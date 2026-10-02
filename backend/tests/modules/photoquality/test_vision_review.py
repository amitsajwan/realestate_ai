"""The visual review: fake vision clients only (no network), fallbacks, caching, the provider chain and the request shape."""
import json

import cv2
import httpx
import pytest

from app.modules.photoquality import vision_review as vr
from app.modules.photoquality.analysis import load_bgr

from .test_analysis_enhance import ROOM, darken


class FakeVision:
    def __init__(self, *replies, model="fake-vision"):
        self.replies, self.model, self.calls = list(replies), model, []

    async def review(self, images, prompt):
        self.calls.append((len(images), prompt))
        r = self.replies.pop(0) if self.replies else None
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture(autouse=True)
def clean_cache():
    vr._MEM.clear()
    yield
    vr._MEM.clear()


@pytest.fixture
def card(tmp_path):
    p = tmp_path / "card.jpg"
    cv2.imwrite(str(p), load_bgr(ROOM))
    return p


async def test_ai_review_is_used_and_cached(card, tmp_path):
    fake = FakeVision({"score": 90, "verdict": "good", "notes": []})
    ctx = {"caption": "3 BHK in Baner", "headline": "Morning light"}
    res = await vr.review([card], ctx, clients=[fake], cache=tmp_path / "c")
    assert res["source"] == "ai" and res["verdict"] == "good" and res["ai_available"] and res["model"] == "fake-vision"
    assert 85 <= res["score"] <= 95
    assert "3 BHK in Baner" in fake.calls[0][1]
    again = await vr.review([card], ctx, clients=[fake], cache=tmp_path / "c")
    assert again["cached"] and len(fake.calls) == 1
    vr._MEM.clear()   # the file cache survives a restart
    assert (await vr.review([card], ctx, clients=[fake], cache=tmp_path / "c"))["cached"]
    # a different caption is a different review
    await vr.review([card], {"caption": "other"}, clients=[fake], cache=tmp_path / "c")
    assert len(fake.calls) == 2


async def test_failover_to_second_client_then_rules(card):
    bad = FakeVision(RuntimeError("down"), model="a")
    ok = FakeVision({"score": 40, "verdict": "redo", "notes": ["Text cut at the bottom", 7, "x" * 500]}, model="b")
    res = await vr.review([card], {}, clients=[bad, ok])
    assert res["model"] == "b" and res["verdict"] == "redo"
    assert res["notes"][0] == "Text cut at the bottom" and all(len(n) <= 140 for n in res["notes"])


async def test_unusable_reply_falls_back_to_rules_and_is_not_cached(card):
    fake = FakeVision({"verdict": "great"}, "nonsense", None)
    res = await vr.review([card], {}, clients=[fake])
    assert res["source"] == "rules" and not res["ai_available"] and vr.UNAVAILABLE in res["notes"]
    res2 = await vr.review([card], {}, clients=[FakeVision({"score": 80, "verdict": "good"})])
    assert res2["source"] == "ai"


async def test_rules_only_uses_photo_analysis_and_critic(tmp_path):
    p = tmp_path / "dark.jpg"
    cv2.imwrite(str(p), darken(load_bgr(ROOM)))
    critic = {"ok": False, "problems": [{"rule": "truncated", "message": "cover#1: 'Wakad' does not fit", "severity": "error"},
                                        {"rule": "orphan", "message": "x", "severity": "warn"}]}
    res = await vr.review([p], {"critic": critic}, clients=[])
    assert res["source"] == "rules" and res["score"] < 75 and res["verdict"] in ("fix", "redo")
    assert any("too dark" in n for n in res["notes"]) and any("does not fit" in n for n in res["notes"])
    assert vr.summary(res).startswith(f"Quality {res['score']} · Check: ")


async def test_no_images():
    res = await vr.review(["missing.jpg"], {}, clients=[])
    assert res["notes"] == ["No image to review yet"]


def test_parse_reply_and_summary():
    assert vr.parse_reply('<think>{"score": 1}</think>```json\n{"score": 82, "verdict": "good", "notes": []}\n```')["score"] == 82
    assert vr.parse_reply("no json") is None
    assert vr.clean_ai({"score": "140", "verdict": "meh"}) == {"score": 100, "verdict": "good", "notes": []}
    assert vr.summary({"score": 82, "verdict": "good", "notes": []}) == "Quality 82/100 · Good"
    assert vr.summary({"score": 54, "verdict": "fix", "notes": ["text cut at the bottom"]}) == "Quality 54 · Check: text cut at the bottom"


def test_provider_chain_from_env(monkeypatch):
    for k in ("AI_VISION_API_KEY", "AI_LLM_API_KEY", "GROQ_API_KEY", "AI_VISION_MODEL", "AI_VISION_FALLBACK_MODEL", "AI_VISION_REVIEW",
              "AI_VISION_FALLBACK_API_KEY", "AI_LLM_FALLBACK_API_KEY", "AI_VISION_FALLBACK_BASE_URL", "AI_LLM_FALLBACK_BASE_URL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr("app.modules.ai_listing.llm.groq_api_key", lambda: None)
    assert vr.default_clients() == []
    monkeypatch.setenv("AI_LLM_API_KEY", "k")
    monkeypatch.setattr("app.modules.ai_listing.llm.groq_api_key", lambda: "k")
    chain = vr.default_clients()
    assert [c.model for c in chain] == [vr.DEFAULT_VISION_MODEL] and chain[0].url.startswith("https://api.groq.com/")
    monkeypatch.setenv("AI_VISION_FALLBACK_MODEL", "some/vision:free")
    monkeypatch.setenv("AI_LLM_FALLBACK_API_KEY", "or")
    monkeypatch.setenv("AI_LLM_FALLBACK_BASE_URL", "https://openrouter.ai/api/v1")
    chain = vr.default_clients()
    assert [c.model for c in chain] == [vr.DEFAULT_VISION_MODEL, "some/vision:free"]
    assert chain[1].url == "https://openrouter.ai/api/v1/chat/completions"
    monkeypatch.setenv("AI_VISION_REVIEW", "off")
    assert vr.default_clients() == []


async def test_openai_vision_request_shape(card):
    seen = {}

    def handler(request: httpx.Request):
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"score": 77, "verdict": "good", "notes": ["clean"]}'}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = vr.OpenAIVision("key", "qwen/qwen3.8-27b", "https://api.groq.com/openai/v1", client=http)
        res = await vr.review([card, card, card, card], {"caption": "c"}, clients=[client])
    parts = seen["body"]["messages"][1]["content"]
    assert seen["auth"] == "Bearer key" and seen["body"]["model"] == "qwen/qwen3.8-27b"
    assert parts[0]["type"] == "text" and sum(p["type"] == "image_url" for p in parts) == 3
    assert parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert "Do NOT invent" in seen["body"]["messages"][0]["content"]
    assert res["source"] == "ai" and res["notes"] == ["clean"]

    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(429))) as http:
        res = await vr.review([card], {"caption": "z"}, clients=[vr.OpenAIVision("k", "m", "https://x", client=http)])
    assert res["source"] == "rules"
