from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.ai_listing import router as r
from app.modules.ai_listing.llm import TranscriptionError


class FakeTranscriber:
    def __init__(self, text="3 bhk Wakad 1.25 cr sale", fail=False):
        self.text, self.fail, self.calls = text, fail, 0

    async def transcribe(self, data, filename, content_type, language=None):
        self.calls += 1
        if self.fail:
            raise TranscriptionError("transcription failed (HTTPStatusError)")
        return self.text


def make_client(transcriber=None, llm=None):
    app = FastAPI()
    app.include_router(r.router, prefix="/api/v1/listings")
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="u1")
    app.dependency_overrides[r.get_llm] = lambda: llm
    app.dependency_overrides[r.get_transcriber] = lambda: transcriber
    return TestClient(app)


URL = "/api/v1/listings/ai/draft"


def test_requires_auth():
    route = next(x for x in r.router.routes if x.path == "/ai/draft")
    assert current_active_user in [d.call for d in route.dependant.dependencies]


def test_text_draft_matches_contract():
    res = make_client().post(URL, data={"text": "2 BHK in Baner, 1100 sq ft carpet, 85 lakh, for sale", "image_count": "2"})
    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"draft", "confidence", "missing", "transcript", "warnings"}
    assert body["draft"]["price_inr"] == 8_500_000 and body["draft"]["city"] == "Pune"
    assert body["missing"] == [] and body["transcript"] is None
    assert body["confidence"]["price_inr"] == 0.95


def test_no_input_returns_empty_draft_not_500():
    res = make_client().post(URL, data={})
    assert res.status_code == 200 and res.json()["draft"] == {} and "price_inr" in res.json()["missing"]
    assert "media" not in res.json()["missing"]  # photos are optional


def test_city_hint_and_garbage():
    res = make_client().post(URL, data={"text": "@@## ???", "city_hint": "Mumbai"})
    assert res.status_code == 200 and res.json()["draft"]["city"] == "Mumbai"


def test_negative_image_count_clamped():
    res = make_client().post(URL, data={"text": "2 bhk baner 85 lakh sale", "image_count": "-4"})
    assert res.status_code == 200 and "media" not in res.json()["missing"]


def test_text_too_long():
    assert make_client().post(URL, data={"text": "a" * 7000}).status_code == 413


def test_audio_transcribed():
    tr = FakeTranscriber()
    res = make_client(tr).post(URL, files={"audio": ("note.webm", b"1234", "audio/webm;codecs=opus")})
    assert res.status_code == 200
    body = res.json()
    assert body["transcript"] == "3 bhk Wakad 1.25 cr sale" and body["draft"]["bhk"] == 3
    assert body["draft"]["price_inr"] == 12_500_000 and tr.calls == 1


def test_audio_without_key_gives_503_but_text_still_works():
    c = make_client(transcriber=None)
    res = c.post(URL, files={"audio": ("n.webm", b"1234", "audio/webm")})
    assert res.status_code == 503 and "text" in res.json()["detail"]
    assert c.post(URL, data={"text": "2 bhk baner 85 lakh"}).status_code == 200


def test_oversize_audio_rejected(monkeypatch):
    monkeypatch.setattr(r, "MAX_AUDIO_BYTES", 2048)  # keeps the test fast; production limit is 10 MB
    tr = FakeTranscriber()
    big = b"0" * 4096
    res = make_client(tr).post(URL, files={"audio": ("n.wav", big, "audio/wav")})
    assert res.status_code == 413 and tr.calls == 0


def test_bad_audio_type_rejected():
    tr = FakeTranscriber()
    res = make_client(tr).post(URL, files={"audio": ("evil.exe", b"MZ", "application/x-msdownload")})
    assert res.status_code == 415 and tr.calls == 0


def test_empty_audio_rejected():
    assert make_client(FakeTranscriber()).post(URL, files={"audio": ("n.mp3", b"", "audio/mpeg")}).status_code == 400


@pytest.mark.parametrize("name,ctype", [("a.webm", "audio/webm"), ("a.ogg", "audio/ogg"), ("a.mp3", "audio/mpeg"),
                                        ("a.m4a", "audio/x-m4a"), ("a.wav", "audio/wav"), ("a.m4a", "application/octet-stream")])
def test_allowed_audio_types(name, ctype):
    assert make_client(FakeTranscriber()).post(URL, files={"audio": (name, b"abc", ctype)}).status_code == 200


def test_transcription_failure_is_502():
    res = make_client(FakeTranscriber(fail=True)).post(URL, files={"audio": ("n.webm", b"abc", "audio/webm")})
    assert res.status_code == 502
