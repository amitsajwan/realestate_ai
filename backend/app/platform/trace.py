"""One log line per step of a pipeline, in one shape, so a run can be followed (and its failures found) with grep.

    pipeline=reel ref=3f2a… step=voice outcome=fallback reason="API key not valid" lang=hi

  pipeline  reel | marketing | publish | startup
  ref       the job, run or post id: `grep "ref=<id>"` shows that run's whole story
  step      the stage inside the pipeline (start, script, voice, render, facts, posts, reels, done...)
  outcome   ok        the step did what it should
            fallback  it worked, but with less (rules script for the LLM's, music only for voice + music...)
            skipped   it did not run, on purpose or for a missing setting
            failed    it did not work; the user sees an error

ok is logged at INFO, fallback and skipped at WARNING, failed at ERROR. Values are one line, quoted when they have spaces,
and cut at 300 characters. Never pass a secret: the callers pass messages that are already redacted."""
import logging
from typing import Any

OK, FALLBACK, SKIPPED, FAILED = "ok", "fallback", "skipped", "failed"
_LEVELS = {OK: logging.INFO, FALLBACK: logging.WARNING, SKIPPED: logging.WARNING, FAILED: logging.ERROR}
MAX_VALUE = 300


def _value(v: Any) -> str:
    if isinstance(v, float):
        v = f"{v:.1f}"
    s = " ".join(str(v).split())[:MAX_VALUE]
    return f'"{s}"' if (not s or any(c in s for c in ' "=')) else s


def line(pipeline: str, ref: Any, step: str, outcome: str, **detail: Any) -> str:
    parts = [f"pipeline={pipeline}", f"ref={_value(ref or '-')}", f"step={step}", f"outcome={outcome}"]
    parts += [f"{k}={_value(v)}" for k, v in detail.items() if v is not None]
    return " ".join(parts)


def event(log: logging.Logger, pipeline: str, ref: Any, step: str, outcome: str, exc_info: bool = False, **detail: Any) -> None:
    """Log one step's outcome (see the module docstring)."""
    log.log(_LEVELS.get(outcome, logging.INFO), line(pipeline, ref, step, outcome, **detail), exc_info=exc_info, stacklevel=2)
