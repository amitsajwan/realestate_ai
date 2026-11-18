"""The thinking loop: a model that plans, looks things up with tools, reads what came back and decides when it is done
(docs/plan/buyer-mind.md step 1). Everything else we run is a fixed pipeline where our code picks the steps; here the model
picks them, so the loop is where the limits live.

    result = await run_tools(llm, system, user, tools, pipeline="buyermind", ref=lead_id)
    result.answer   # the model's final JSON object, or None
    result.calls    # every tool call: name, arguments, ok, a short preview of what came back

One round: the model gets the conversation and the tool list; it either asks for tools (all of that round's calls run together,
since every tool given here must only read) or writes its answer. A tool that raises, a tool that does not exist and arguments
that are not JSON are told to the model as an error, so it can try another way; they never stop the loop. When the rounds or the
time run out, the model is asked once more, with no tools, for its answer from what it has. Anything else (no model, a provider
down, an answer that is not a JSON object) ends with `answer=None` and the caller falls back to its rules, as every AI path here
does. The loop knows nothing of the business: callers bring the prompt, the tools and the checks on the answer.
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from app.platform import trace
from app.platform.llm import _json_text

log = logging.getLogger(__name__)

MAX_ROUNDS = 6          # rounds of tool calls before the model must answer with what it has
MAX_CALLS = 12          # tool calls in all: a model that asks for twenty lookups in one round gets the first twelve
BUDGET_S = 90.0         # the whole loop, model turns and tools; the deep mind runs in the background, never in a chat turn
TOOL_TIMEOUT_S = 15.0   # one tool call
RESULT_CHARS = 6000     # what one tool result may add to the conversation (tokens cost money and dilute attention)
PREVIEW_CHARS = 200     # what the trace keeps of a result

FINAL_ASK = ("You have no more lookups. Answer now from what you have, as the one JSON object your instructions describe. "
             "Say plainly what you could not find.")


@dataclass
class Tool:
    """One read-only lookup the model may call. `parameters` is a JSON Schema object; `run` gets the arguments as keywords and
    returns anything JSON can carry."""
    name: str
    description: str
    parameters: dict[str, Any]
    run: Callable[..., Awaitable[Any]]

    def spec(self) -> dict[str, Any]:
        return {"type": "function", "function": {"name": self.name, "description": self.description, "parameters": self.parameters}}


@dataclass
class Call:
    name: str
    arguments: dict[str, Any]
    ok: bool
    preview: str


@dataclass
class Result:
    answer: Optional[dict[str, Any]]
    calls: list[Call] = field(default_factory=list)
    rounds: int = 0
    outcome: str = "failed"       # done | forced (out of rounds or time, answered anyway) | failed
    reasoning: list[str] = field(default_factory=list)   # what the model thought each round, where the provider sends it

    def results_text(self) -> str:
        """Every tool result's preview in one string, for a caller's check that a figure in the answer came from a lookup."""
        return "\n".join(c.preview for c in self.calls if c.ok)


def _clip(value: Any, limit: int) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[:limit] + " …(cut)"


def _parse_answer(content: Optional[str]) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(_json_text(content or ""))
    except (ValueError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def _assistant_turn(msg: dict[str, Any]) -> dict[str, Any]:
    """The assistant's message as it goes back into the conversation: only the standard fields, since a provider may reject
    another's extras (Groq's `reasoning`) when the next round goes elsewhere."""
    turn: dict[str, Any] = {"role": "assistant", "content": msg.get("content") or ""}
    if msg.get("tool_calls"):
        turn["tool_calls"] = [{"id": c.get("id"), "type": "function",
                               "function": {"name": (c.get("function") or {}).get("name"),
                                            "arguments": (c.get("function") or {}).get("arguments") or "{}"}}
                              for c in msg["tool_calls"]]
    return turn


async def _run_call(call: dict[str, Any], tools: dict[str, Tool], timeout: float) -> tuple[Call, str]:
    fn = call.get("function") or {}
    name = fn.get("name") or ""
    try:
        args = json.loads(fn.get("arguments") or "{}")
        if not isinstance(args, dict):
            raise ValueError("arguments are not an object")
    except (ValueError, TypeError) as e:
        return Call(name, {}, False, f"bad arguments: {e}"), json.dumps({"error": f"arguments were not a JSON object: {e}"})
    tool = tools.get(name)
    if tool is None:
        return Call(name, args, False, "no such tool"), json.dumps({"error": f"no tool named {name!r}; use one of {sorted(tools)}"})
    try:
        value = await asyncio.wait_for(tool.run(**args), timeout=timeout)
    except asyncio.TimeoutError:
        return Call(name, args, False, "timed out"), json.dumps({"error": "this lookup timed out; try another way or answer without it"})
    except Exception as e:   # a tool's failure is the model's information, not the loop's end
        log.info("tool %s failed: %s", name, type(e).__name__)
        return Call(name, args, False, f"failed: {type(e).__name__}"), json.dumps({"error": f"this lookup failed ({type(e).__name__})"})
    text = _clip(value, RESULT_CHARS)
    return Call(name, args, True, _clip(value, PREVIEW_CHARS)), text


async def run_tools(llm: Any, system: str, user: str, tools: list[Tool], *, pipeline: str = "toolloop", ref: Any = None,
                    max_rounds: int = MAX_ROUNDS, max_calls: int = MAX_CALLS, budget: float = BUDGET_S,
                    effort: Optional[str] = "medium", clock: Callable[[], float] = time.monotonic) -> Result:
    """Let the model think with `tools` until it answers with one JSON object (see the module docstring)."""
    result = Result(answer=None)
    if llm is None or not hasattr(llm, "step"):
        trace.event(log, pipeline, ref, "think", trace.SKIPPED, reason="no model")
        return result
    by_name = {t.name: t for t in tools}
    specs = [t.spec() for t in tools]
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    start = clock()

    def left() -> float:
        return budget - (clock() - start)

    while result.rounds < max_rounds and len(result.calls) < max_calls and left() > 1.0:
        result.rounds += 1
        msg = await llm.step(messages, tools=specs or None, effort=effort, timeout=left())
        if not msg:
            trace.event(log, pipeline, ref, "think", trace.FAILED, round=result.rounds, reason="no answer from any model")
            return result
        if msg.get("reasoning"):
            result.reasoning.append(_clip(msg["reasoning"], 2000))
        asked = list(msg.get("tool_calls") or [])[: max(0, max_calls - len(result.calls))]
        if not asked:
            result.answer = _parse_answer(msg.get("content"))
            if result.answer is None:
                messages.append(_assistant_turn(msg))
                break   # it answered in prose: one more try below, in JSON mode
            result.outcome = "done"
            trace.event(log, pipeline, ref, "think", trace.OK, rounds=result.rounds, calls=len(result.calls))
            return result
        msg = {**msg, "tool_calls": asked}
        messages.append(_assistant_turn(msg))
        done = await asyncio.gather(*(_run_call(c, by_name, min(TOOL_TIMEOUT_S, max(left(), 1.0))) for c in asked))
        for call, (record, text) in zip(asked, done):
            result.calls.append(record)
            messages.append({"role": "tool", "tool_call_id": call.get("id"), "content": text})
            trace.event(log, pipeline, ref, f"tool:{record.name}", trace.OK if record.ok else trace.FALLBACK,
                        round=result.rounds, reason=None if record.ok else record.preview)

    # Out of rounds, calls or time, or the answer was not JSON: one last turn, no tools, JSON only.
    messages.append({"role": "user", "content": FINAL_ASK})
    msg = await llm.step(messages, tools=None, json_mode=True, effort=effort, timeout=max(left(), 10.0))
    result.answer = _parse_answer((msg or {}).get("content"))
    result.outcome = "forced" if result.answer is not None else "failed"
    trace.event(log, pipeline, ref, "think", trace.FALLBACK if result.answer is not None else trace.FAILED,
                rounds=result.rounds, calls=len(result.calls), reason="answered without more lookups")
    return result
