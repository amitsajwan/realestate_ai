"""What an answer cost reaches whoever asked for it (USAGE), and the paid Gemini client stays apart from the free tiers."""
import httpx

from app.platform import llm


def _answer(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": '{"ok": true}'}}],
                                     "usage": {"prompt_tokens": 1200, "completion_tokens": 300, "total_tokens": 2100}})


async def test_each_answer_reports_its_tokens_with_thinking_counted_as_output():
    seen = []
    client = httpx.AsyncClient(transport=httpx.MockTransport(_answer))
    g = llm.GroqLLM("key", model="gemini-3-flash-preview", url=llm.GEMINI_OPENAI_URL, client=client, health=llm.ModelHealth())
    token = llm.USAGE.set(seen.append)
    try:
        assert await g.json("s", "u") == {"ok": True}
    finally:
        llm.USAGE.reset(token)
    assert seen == [{"url": llm.GEMINI_OPENAI_URL, "model": "gemini-3-flash-preview", "prompt_tokens": 1200, "output_tokens": 900}]
    assert await g.json("s", "u") == {"ok": True}   # nobody listening: nothing reported, the answer still comes
    assert len(seen) == 1


def test_gemini_is_its_own_client_and_left_out_of_the_free_tiers(monkeypatch):
    for var in ("AI_LLM_API_KEY", "GROQ_API_KEY", "GROQ_API_KEYS", "AI_LLM_FALLBACK_API_KEY", "GITHUB_MODELS_TOKEN",
                "SAMBANOVA_API_KEY", "CLOUDFLARE_API_TOKEN", "AI_OPENROUTER_TEXT", "AI_GEMINI_LITE_MODEL", "AI_CRITICAL_MODEL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(llm, "groq_api_key", lambda: None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert llm.gemini_llm() is None and llm.free_llm() is None
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("SAMBANOVA_API_KEY", "s")
    assert llm.gemini_llm().model == llm.GEMINI_CRITICAL_MODEL
    assert llm.gemini_llm(lite=True).model == llm.GEMINI_LITE_MODEL
    free = llm.free_llm()
    assert free.url != llm.GEMINI_OPENAI_URL and "sambanova" in free.url
