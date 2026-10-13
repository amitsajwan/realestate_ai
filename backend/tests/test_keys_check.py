"""scripts/keys_check.py: every key checked against a (fake) service; refused, unreachable and empty keys are told apart."""
import base64
import json

import httpx

from scripts import keys_check as kc


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def set_env(monkeypatch, **values):
    for name, _, _ in kc.CHECKS:
        monkeypatch.delenv(name, raising=False)
    for v in ("AI_LLM_BASE_URL", "AI_LLM_FALLBACK_BASE_URL", "AI_STT_BASE_URL", "AI_VISION_BASE_URL", "AI_VISION_FALLBACK_BASE_URL",
              "META_PAGE_ID", "WHATSAPP_PHONE_NUMBER_ID"):
        monkeypatch.delenv(v, raising=False)
    for k, v in values.items():
        monkeypatch.setenv(k, v)


def rows_by_name(rows):
    return {r[0]: r for r in rows}


def test_accepted_refused_empty_and_unreachable_keys(monkeypatch):
    set_env(monkeypatch, SERPER_API_KEY="serper-good-1111", YOUTUBE_API_KEY="yt-bad-2222", GEMINI_API_KEY="gem-3333",
            AI_LLM_API_KEY="or-key-4444", AI_LLM_BASE_URL="https://openrouter.ai/api/v1")
    seen = []

    def handler(req):
        seen.append(req)
        if req.url.host == "google.serper.dev":
            assert req.headers["X-API-KEY"] == "serper-good-1111"
            return httpx.Response(200, json={"organic": []})
        if "youtube" in req.url.path:
            return httpx.Response(400, json={"error": {"message": "API key not valid. Please pass a valid API key."}})
        if req.url.host == "generativelanguage.googleapis.com":
            raise httpx.ConnectError("no route")
        if req.url.host == "openrouter.ai":
            assert req.url.path == "/api/v1/key" and req.headers["Authorization"] == "Bearer or-key-4444"   # not the public model list
            return httpx.Response(200, json={"data": {}})
        raise AssertionError(f"unexpected call {req.url}")
    rows = rows_by_name(kc.run(client(handler)))
    assert rows["SERPER_API_KEY"][2:4] == ("OK", "...1111")
    assert rows["YOUTUBE_API_KEY"][2] == "FAILED" and "API key not valid" in rows["YOUTUBE_API_KEY"][4]
    assert rows["GEMINI_API_KEY"][2] == "FAILED" and "could not reach" in rows["GEMINI_API_KEY"][4]
    assert rows["AI_LLM_API_KEY"][2] == "OK"
    assert rows["GOOGLE_TTS_API_KEY"][2] == "EMPTY" and rows["META_PAGE_ACCESS_TOKEN"][2] == "EMPTY"
    assert not any("serper-good-1111" in str(r) or "yt-bad-2222" in str(r) for r in rows.values())   # values never printed


def test_groq_style_keys_list_models_at_the_base_the_app_uses(monkeypatch):
    set_env(monkeypatch, GROQ_API_KEY="g-1", AI_VISION_API_KEY="v-2", AI_LLM_BASE_URL="https://llm.example/v1",
            AI_LLM_FALLBACK_API_KEY="f-3")
    asked = []

    def handler(req):
        asked.append(str(req.url))
        return httpx.Response(200, json={"data": []})
    rows = rows_by_name(kc.run(client(handler)))
    assert "https://api.groq.com/openai/v1/models" in asked          # GROQ_API_KEY: always Groq
    assert "https://llm.example/v1/models" in asked                  # vision falls back to AI_LLM_BASE_URL, like the app
    assert rows["AI_LLM_FALLBACK_API_KEY"][2] == "SKIP"              # no fallback base URL: nothing to check against


def test_meta_token_must_belong_to_our_page(monkeypatch):
    set_env(monkeypatch, META_PAGE_ACCESS_TOKEN="tok-9999", META_PAGE_ID="111")
    rows = rows_by_name(kc.run(client(lambda req: httpx.Response(200, json={"id": "222", "name": "Someone Else"}))))
    assert rows["META_PAGE_ACCESS_TOKEN"][2] == "FAILED" and "not META_PAGE_ID 111" in rows["META_PAGE_ACCESS_TOKEN"][4]
    rows = rows_by_name(kc.run(client(lambda req: httpx.Response(200, json={"id": "111", "name": "Avasetu"}))))
    assert rows["META_PAGE_ACCESS_TOKEN"][2:] == ("OK", "...9999", "page: Avasetu")


def test_search_console_key_must_be_a_service_account_file(monkeypatch):
    set_env(monkeypatch, GSC_SA_KEY_B64=base64.b64encode(json.dumps({"type": "service_account"}).encode()).decode())
    assert rows_by_name(kc.run(client(lambda r: httpx.Response(200))))["GSC_SA_KEY_B64"][2:5:2] == ("FAILED", "the file has no client_email / private_key / token_uri")
    set_env(monkeypatch, GSC_SA_KEY_B64="not base64 at all!")
    assert rows_by_name(kc.run(client(lambda r: httpx.Response(200))))["GSC_SA_KEY_B64"][2] == "FAILED"


def test_exit_code_is_1_only_when_a_key_failed(monkeypatch):
    set_env(monkeypatch)
    monkeypatch.setattr(kc, "TIMEOUT", 1)
    assert kc.main() == 0                                            # all empty: nothing failed
