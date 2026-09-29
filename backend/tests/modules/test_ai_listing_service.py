import asyncio

import pytest

from app.modules.ai_listing.extract_numbers import parse_areas, parse_price
from app.modules.ai_listing import llm as llm_mod
from app.modules.ai_listing.llm import GroqLLM
from app.modules.ai_listing.service import AIListingService, AudioInput, TranscriberUnavailable
from app.modules.ai_listing.text_norm import normalise

pytestmark = pytest.mark.asyncio


class FakeLLM:
    def __init__(self, extract=None, translate=None, boom=False, hang=False):
        self._extract, self._translate, self.boom, self.hang = extract, translate, boom, hang
        self.extract_calls = self.translate_calls = 0

    async def extract(self, text, city_hint=None):
        self.extract_calls += 1
        if self.boom:
            raise RuntimeError("network down")
        if self.hang:
            await asyncio.sleep(60)
        return self._extract

    async def translate(self, facts, description_en):
        self.translate_calls += 1
        if self.boom:
            raise RuntimeError("network down")
        return self._translate


class FakeTranscriber:
    def __init__(self, text="2 bhk in baner 85 lakh"):
        self.text, self.calls = text, []

    async def transcribe(self, data, filename, content_type, language=None):
        self.calls.append((len(data), filename, content_type, language))
        return self.text


TEXT = "2 BHK in Baner, 1100 sq ft carpet, 85 lakh, for sale"


@pytest.mark.parametrize("text,expected", [
    ("85 lakh", 8_500_000), ("85 L", 8_500_000), ("85 lac", 8_500_000), ("1.25 Cr", 12_500_000),
    ("1.2 crore", 12_000_000), ("Rs 85,00,000", 8_500_000), ("₹85,00,000/-", 8_500_000), ("25k", 25_000),
    ("25,000/month", 25_000), ("1 cr 25 lakh", 12_500_000), ("Rs. 1,20,000 per month", 120_000),
])
def test_price_formats(text, expected):
    assert parse_price(normalise(text))[0] == expected


def test_price_ignores_deposit_and_rate():
    assert parse_price("deposit 2 lakh, rent 30k")[0] == 30_000
    assert parse_price("rs 8500 per sq ft, 1.2 cr")[0] == 12_000_000


def test_devanagari_numerals_and_words():
    assert parse_price(normalise("८५ लाख"))[0] == 8_500_000
    assert parse_price(normalise("पचासी लाख"))[0] == 8_500_000
    assert parse_price(normalise("१.२५ करोड"))[0] == 12_500_000
    assert parse_areas(normalise("१२०० वर्ग फूट")) == {"carpet": (1200, 0.6)}


async def test_deterministic_only_when_no_llm():
    res = await AIListingService().from_text(TEXT, image_count=2)
    assert res.draft["price_inr"] == 8_500_000 and res.draft["locality"] == "Baner"
    assert res.draft["title"] == "2 BHK for sale in Baner, Pune - 85 L"
    assert list(res.draft["description"]) == ["en"]
    assert res.missing == []
    assert res.confidence["price_inr"] == 0.95 and res.confidence["locality"] == 0.8


async def test_description_only_states_extracted_facts():
    res = await AIListingService().from_text("2 BHK Baner 85 lakh sale")
    en = res.draft["description"]["en"]
    for banned in ("gym", "parking", "pool", "furnished", "possession", "RERA"):
        assert banned.lower() not in en.lower()
    assert "85,00,000" in en and "Baner" in en


async def test_llm_fills_gaps_but_deterministic_wins():
    llm = FakeLLM(extract={"price_inr": 9_900_000, "bhk": 3, "locality": "Balewadi", "city": "Pune",
                           "project_name": "Sky Towers", "furnishing": "semi", "amenities": ["Gym", "Unicorn stable"],
                           "transaction": "sale", "property_type": "apartment"},
                  translate={"hi": "हिंदी विवरण", "mr": "मराठी वर्णन"})
    res = await AIListingService(llm=llm).from_text("2 BHK in Baner 85 lakh")
    d = res.draft
    assert d["price_inr"] == 8_500_000 and d["bhk"] == 2 and d["locality"] == "Baner"  # regex/gazetteer win
    assert d["project_name"] == "Sky Towers" and res.confidence["project_name"] == 0.6   # LLM fills gap
    assert d["furnishing"] == "semi" and 0.5 <= res.confidence["furnishing"] <= 0.7
    assert d["amenities"] == ["Gym"]  # unknown amenity dropped, never invented
    assert d["description"]["hi"] == "हिंदी विवरण" and d["description"]["mr"] == "मराठी वर्णन"
    assert llm.extract_calls == 1 and llm.translate_calls == 1


async def test_llm_garbage_values_are_sanitised():
    llm = FakeLLM(extract={"price_inr": "lots", "bhk": 99, "transaction": "barter", "carpet_sqft": -5, "floor": "x"})
    res = await AIListingService(llm=llm).from_text("hello there")
    assert res.draft == {}


@pytest.mark.parametrize("kw", [dict(boom=True), dict(hang=True), dict(extract=None), dict(extract=["not", "a", "dict"])])
async def test_llm_failure_falls_back_silently(monkeypatch, kw):
    import app.modules.ai_listing.service as svc
    monkeypatch.setattr(svc, "LLM_TIMEOUT", -0.4)  # makes the guard timeout ~0.1s for the hang case
    res = await AIListingService(llm=FakeLLM(**kw)).from_text(TEXT)
    assert res.draft["price_inr"] == 8_500_000
    assert list(res.draft["description"]) == ["en"]


async def test_llm_only_extraction_when_regex_finds_nothing():
    llm = FakeLLM(extract={"price_inr": 6_000_000, "locality": "Sadashiv Peth", "city": "Pune", "bhk": 2})
    res = await AIListingService(llm=llm).from_text("sundar ghar milega")
    assert res.draft["locality"] == "Sadashiv Peth" and res.confidence["price_inr"] == 0.6


async def test_groq_llm_returns_none_on_http_error():
    import httpx

    def handler(request):
        return httpx.Response(500, json={"error": "x"})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await GroqLLM("k", client=client).extract("2 bhk") is None


async def test_groq_llm_parses_json_mode_reply():
    import httpx, json

    def handler(request):
        body = json.loads(request.content)
        assert body["response_format"] == {"type": "json_object"} and body["model"] == llm_mod.LLM_MODEL
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"bhk": 2}'}}]})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await GroqLLM("k", client=client).extract("2 bhk") == {"bhk": 2}


async def test_gemini_transcriber_sends_inline_audio_and_key_header_not_url():
    import base64
    import httpx
    import json
    from app.modules.ai_listing.llm import GeminiTranscriber

    seen = {}

    def handler(request):
        seen["url"], seen["key"], seen["body"] = str(request.url), request.headers.get("x-goog-api-key"), json.loads(request.content)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": " 2 bhk upper kharadi 85 lakh "}]}}]})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    out = await GeminiTranscriber("SECRETKEY", model="gemini-x", client=client).transcribe(b"abc", "n.webm", "audio/webm;codecs=opus", "hi")
    assert out == "2 bhk upper kharadi 85 lakh"
    assert seen["url"].endswith("/models/gemini-x:generateContent") and "SECRETKEY" not in seen["url"] and seen["key"] == "SECRETKEY"
    inline = seen["body"]["contents"][0]["parts"][1]["inline_data"]
    assert inline["mime_type"] == "audio/webm" and base64.b64decode(inline["data"]) == b"abc"


async def test_gemini_transcriber_error_is_a_clean_transcription_error():
    import httpx
    from app.modules.ai_listing.llm import GeminiTranscriber, TranscriptionError

    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(429, json={"error": "quota"})))
    with pytest.raises(TranscriptionError) as e:
        await GeminiTranscriber("SECRETKEY", client=client).transcribe(b"abc", "n.webm", "audio/webm")
    assert "SECRETKEY" not in str(e.value)


async def test_gemini_transcriber_retries_once_when_the_model_is_busy():
    import httpx
    from app.modules.ai_listing.llm import GeminiTranscriber

    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503, json={"error": "unavailable"})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await GeminiTranscriber("k", client=client).transcribe(b"a", "n.webm", "audio/webm") == "ok" and len(calls) == 2


@pytest.mark.parametrize("reply", ["NO_SPEECH", " no_speech. ", "[NO_SPEECH]"])
async def test_gemini_silence_marker_becomes_empty_transcript(reply):
    import httpx
    from app.modules.ai_listing.llm import GeminiTranscriber

    client = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": reply}]}}]})))
    assert await GeminiTranscriber("k", client=client).transcribe(b"a", "n.webm", "audio/webm") == ""


async def test_silent_recording_never_invents_a_listing():
    import httpx
    from app.modules.ai_listing.llm import GeminiTranscriber

    client = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "NO_SPEECH"}]}}]})))
    res = await AIListingService(transcriber=GeminiTranscriber("k", client=client)).create_draft(
        audio=AudioInput(b"a", "n.webm", "audio/webm"))
    assert res.draft == {} and res.transcript == "" and any("No speech" in w for w in res.warnings)


async def test_text_llm_retries_once_when_busy():
    import httpx

    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503, json={"error": "busy"})
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"bhk": 3}'}}]})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await GroqLLM("k", client=client).extract("3 bhk") == {"bhk": 3} and len(calls) == 2


def test_provider_switch(monkeypatch):
    from app.modules.ai_listing.llm import GeminiTranscriber, GroqTranscriber, default_transcriber

    for k in ("AI_STT_PROVIDER", "AI_STT_API_KEY", "GEMINI_API_KEY", "AI_LLM_API_KEY", "GROQ_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("AI_LLM_API_KEY", "g")
    assert isinstance(default_transcriber(), GroqTranscriber)
    monkeypatch.setenv("AI_STT_PROVIDER", "gemini")
    assert default_transcriber() is None  # provider chosen but no key: voice is reported as unavailable, text still works
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    assert isinstance(default_transcriber(), GeminiTranscriber)


async def test_missing_and_media():
    res = await AIListingService().from_text("2 BHK 85 lakh", image_count=0)
    assert set(res.missing) == {"city", "locality"}
    res = await AIListingService().from_text("2 BHK Baner 85 lakh sale", image_count=3)
    assert res.missing == []


async def test_empty_text_lists_all_required():
    res = await AIListingService().from_text("")
    assert res.draft == {}
    assert set(res.missing) == {"title", "transaction", "property_type", "price_inr", "city", "locality",
                                "description.en"}


async def test_warnings():
    w = (await AIListingService().from_text("2 BHK Baner 20 lakh 1000 sq ft carpet sale")).warnings
    assert any("low for Baner" in x for x in w)
    w = (await AIListingService().from_text("2 BHK Baner 5 crore 1000 sq ft carpet sale")).warnings
    assert any("high for Baner" in x for x in w)
    w = (await AIListingService().from_text("2 BHK Baner 90 lakh carpet 1400 sba 1200")).warnings
    assert any("Carpet area is larger" in x for x in w)
    w = (await AIListingService().from_text("5 BHK Baner 3 crore 400 sq ft carpet")).warnings
    assert any("implausible" in x for x in w)
    w = (await AIListingService().from_text("2 BHK 85 lakh")).warnings
    assert any("City not found" in x for x in w)


async def test_city_hint_used_when_missing():
    res = await AIListingService().from_text("2 BHK 85 lakh", city_hint="pune")
    assert res.draft["city"] == "Pune" and res.confidence["city"] == 0.6
    assert "city" not in res.missing


async def test_transcript_path_with_fake_transcriber():
    tr = FakeTranscriber()
    audio = AudioInput(b"\x00" * 10, "note.webm", "audio/webm", "hi")
    res = await AIListingService(transcriber=tr).create_draft(text=None, audio=audio, image_count=1)
    assert res.transcript == "2 bhk in baner 85 lakh"
    assert res.draft["locality"] == "Baner" and res.draft["price_inr"] == 8_500_000
    assert tr.calls == [(10, "note.webm", "audio/webm", "hi")]


async def test_typed_text_and_transcript_are_combined():
    tr = FakeTranscriber("85 lakh")
    audio = AudioInput(b"x", "n.ogg", "audio/ogg")
    res = await AIListingService(transcriber=tr).create_draft(text="3 bhk Wakad for sale", audio=audio)
    assert res.draft["bhk"] == 3 and res.draft["price_inr"] == 8_500_000 and res.transcript == "85 lakh"


async def test_audio_without_transcriber_raises():
    with pytest.raises(TranscriberUnavailable):
        await AIListingService().create_draft(text="x", audio=AudioInput(b"x", "n.webm", "audio/webm"))


async def test_silent_audio_warns():
    res = await AIListingService(transcriber=FakeTranscriber("")).create_draft(
        audio=AudioInput(b"x", "n.webm", "audio/webm"))
    assert res.transcript == "" and any("No speech" in w for w in res.warnings)
