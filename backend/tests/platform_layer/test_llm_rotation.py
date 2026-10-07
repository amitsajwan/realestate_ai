"""Round-robin over providers, and models that are retired (404) or rate-limited (429) are rested instead of asked again."""
import httpx

from app.platform import llm


class Clock:
    t = 1000.0

    def __call__(self):
        return self.t


def test_retired_and_busy_models_rest_then_come_back():
    clock = Clock()
    h = llm.ModelHealth(clock)
    h.note("u", "old:free", httpx.Response(404))
    h.note("u", "busy", httpx.Response(429, headers={"retry-after": "30"}))
    assert h.usable("u", ["old:free", "busy", "good"]) == ["good"]
    assert h.usable("u", ["old:free", "busy"]) == ["old:free", "busy"]       # all resting: still try rather than nothing
    assert h.resting("u", ["old:free", "busy"]) and not h.resting("u", ["good"])
    clock.t += 31
    assert h.usable("u", ["old:free", "busy"]) == ["busy"]                   # the 429 rest is over, the 404 is not


class Provider:
    def __init__(self, name, calls, answer=True, resting=False):
        self.name, self.calls, self.answer, self._resting = name, calls, answer, resting

    def resting(self):
        return self._resting

    async def json(self, system, user):
        self.calls.append(self.name)
        return {"by": self.name} if self.answer else None


async def test_calls_take_turns_and_a_resting_provider_goes_last():
    calls = []
    f = llm.FallbackLLM([Provider("groq", calls), Provider("openrouter", calls)])
    got = [(await f.json("s", "u"))["by"] for _ in range(4)]
    assert sorted(got) == ["groq", "groq", "openrouter", "openrouter"]      # spread over both, not all on the first
    calls.clear()
    f = llm.FallbackLLM([Provider("groq", calls, resting=True), Provider("openrouter", calls, answer=False)])
    assert (await f.json("s", "u"))["by"] == "groq" and calls == ["openrouter", "groq"]
