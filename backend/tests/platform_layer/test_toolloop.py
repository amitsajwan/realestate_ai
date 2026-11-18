"""The thinking loop (platform/toolloop.py): the model picks its lookups, the loop keeps the limits and never breaks."""
import asyncio
import json

import httpx

from app.platform import llm, toolloop
from app.platform.toolloop import Tool, run_tools


def tool_call(id_, name, **args):
    return {"id": id_, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


class ScriptedLLM:
    """Answers each step with the next scripted message and keeps what it was sent."""

    def __init__(self, *script):
        self.script = list(script)
        self.sent = []

    async def step(self, messages, tools=None, json_mode=False, effort=None, timeout=None):
        self.sent.append({"messages": [dict(m) for m in messages], "tools": tools, "json_mode": json_mode})
        return self.script.pop(0) if self.script else None


def project_facts_tool(seen):
    async def run(slug):
        seen.append(slug)
        return {"slug": slug, "possession": "2027-12", "price_range": "68-74 L"}
    return Tool("project_facts", "Facts of one project", {"type": "object", "properties": {"slug": {"type": "string"}}}, run)


async def test_the_model_looks_things_up_then_answers_from_them():
    seen = []
    model = ScriptedLLM(
        {"content": "", "tool_calls": [tool_call("c1", "project_facts", slug="fiore-2a")], "reasoning": "need the possession date"},
        {"content": '{"possession": "2027-12", "flag": "after his move-in"}'},
    )
    out = await run_tools(model, "sys", "lead", [project_facts_tool(seen)])
    assert out.outcome == "done" and out.answer == {"possession": "2027-12", "flag": "after his move-in"}
    assert seen == ["fiore-2a"] and out.rounds == 2 and out.reasoning == ["need the possession date"]
    tool_msg = model.sent[1]["messages"][-1]
    assert tool_msg["role"] == "tool" and tool_msg["tool_call_id"] == "c1" and "2027-12" in tool_msg["content"]
    assert "2027-12" in out.results_text()


async def test_the_next_round_gets_only_standard_fields_so_another_provider_can_take_it():
    model = ScriptedLLM({"content": None, "reasoning": "x", "tool_calls": [tool_call("c1", "project_facts", slug="a")]},
                        {"content": "{}"})
    await run_tools(model, "s", "u", [project_facts_tool([])])
    assistant = model.sent[1]["messages"][2]
    assert set(assistant) == {"role", "content", "tool_calls"} and assistant["content"] == ""


async def test_a_failing_unknown_or_garbled_tool_call_is_told_to_the_model_not_raised():
    async def broken(**_):
        raise RuntimeError("db down")
    bad_args = {"id": "c3", "type": "function", "function": {"name": "project_facts", "arguments": "{not json"}}
    model = ScriptedLLM(
        {"tool_calls": [tool_call("c1", "broken"), tool_call("c2", "nope"), bad_args]},
        {"content": '{"ok": false}'},
    )
    out = await run_tools(model, "s", "u", [Tool("broken", "d", {"type": "object"}, broken), project_facts_tool([])])
    assert out.answer == {"ok": False}
    assert [c.ok for c in out.calls] == [False, False, False]
    errors = [json.loads(m["content"])["error"] for m in model.sent[1]["messages"] if m["role"] == "tool"]
    assert "failed" in errors[0] and "no tool named 'nope'" in errors[1] and "JSON" in errors[2]


async def test_a_slow_tool_times_out_and_the_loop_goes_on(monkeypatch):
    monkeypatch.setattr(toolloop, "TOOL_TIMEOUT_S", 0.01)

    async def slow():
        await asyncio.sleep(1)
    model = ScriptedLLM({"tool_calls": [tool_call("c1", "slow")]}, {"content": '{"a": 1}'})
    out = await run_tools(model, "s", "u", [Tool("slow", "d", {"type": "object"}, slow)])
    assert out.answer == {"a": 1} and out.calls[0].preview == "timed out"


async def test_out_of_rounds_the_model_must_answer_without_tools():
    seen = []
    looping = [{"tool_calls": [tool_call(f"c{i}", "project_facts", slug=str(i))]} for i in range(3)]
    model = ScriptedLLM(*looping, {"content": '{"answer": "partial"}'})
    out = await run_tools(model, "s", "u", [project_facts_tool(seen)], max_rounds=3)
    assert out.outcome == "forced" and out.answer == {"answer": "partial"} and seen == ["0", "1", "2"]
    last = model.sent[-1]
    assert last["tools"] is None and last["json_mode"] and last["messages"][-1]["content"] == toolloop.FINAL_ASK


async def test_the_call_cap_cuts_a_round_that_asks_for_too_much():
    seen = []
    model = ScriptedLLM({"tool_calls": [tool_call(f"c{i}", "project_facts", slug=str(i)) for i in range(20)]},
                        {"content": '{"n": 4}'})
    out = await run_tools(model, "s", "u", [project_facts_tool(seen)], max_calls=4)
    assert len(seen) == 4 and len(out.calls) == 4 and out.outcome == "forced"


async def test_out_of_time_it_stops_looking():
    t = {"now": 0.0}

    class Slow(ScriptedLLM):
        async def step(self, *a, **kw):
            t["now"] += 50
            return await super().step(*a, **kw)
    model = Slow({"tool_calls": [tool_call("c1", "project_facts", slug="a")]},
                 {"tool_calls": [tool_call("c2", "project_facts", slug="b")]}, {"content": '{"late": true}'})
    out = await run_tools(model, "s", "u", [project_facts_tool([])], budget=90, clock=lambda: t["now"])
    assert out.rounds == 2 and out.outcome == "forced" and out.answer == {"late": True}


async def test_a_prose_answer_gets_one_json_retry_and_then_the_caller_falls_back():
    model = ScriptedLLM({"content": "He wants a 2 BHK."}, {"content": '```json\n{"bhk": 2}\n```'})
    out = await run_tools(model, "s", "u", [])
    assert out.answer == {"bhk": 2} and model.sent[1]["messages"][-2]["content"] == "He wants a 2 BHK."
    model = ScriptedLLM({"content": "prose"}, {"content": "still prose"})
    assert (await run_tools(model, "s", "u", [])).answer is None


async def test_no_model_or_a_model_down_means_no_answer():
    assert (await run_tools(None, "s", "u", [])).outcome == "failed"
    out = await run_tools(ScriptedLLM(), "s", "u", [project_facts_tool([])])
    assert out.answer is None and out.outcome == "failed"


async def test_groq_step_sends_tools_and_effort_and_returns_the_message():
    sent = {}

    def handler(request):
        sent.clear()
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "", "tool_calls": [tool_call("c1", "t")]}}]})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    g = llm.GroqLLM("key", model="m", client=client, url="https://x.test/v1/chat/completions", health=llm.ModelHealth())
    msg = await g.step([{"role": "user", "content": "hi"}], tools=[{"type": "function"}], effort="high")
    assert msg["tool_calls"][0]["id"] == "c1"
    assert sent["tools"] == [{"type": "function"}] and sent["reasoning_effort"] == "high" and "response_format" not in sent
    await g.step([{"role": "user", "content": "hi"}], json_mode=True)
    assert sent["response_format"] == {"type": "json_object"} and "tools" not in sent and "reasoning_effort" not in sent


async def test_groq_step_is_none_on_a_provider_error():
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    g = llm.GroqLLM("key", model="m", client=client, url="https://x.test/v1/chat/completions", health=llm.ModelHealth())
    assert await g.step([{"role": "user", "content": "hi"}]) is None


async def test_fallback_step_moves_to_the_next_provider():
    class Down:
        async def step(self, *a, **kw):
            return None
    up = ScriptedLLM({"content": "{}"})
    f = llm.FallbackLLM([Down(), up])
    assert await f.step([{"role": "user", "content": "x"}]) == {"content": "{}"}
