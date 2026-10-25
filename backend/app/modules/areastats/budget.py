"""What the project enrichment may spend on models, and on which (docs/plan/enrich-lanes.md; owner 2026-10-25: "50 rs per day
is fine" on Gemini).

Two pools:
- Gemini, paid: at most GEMINI_INR_PER_DAY rupees a day (ENRICH_GEMINI_INR_PER_DAY). Every answer's tokens come back through
  platform.llm.USAGE and are priced from PRICES (USD per 1M tokens in and out, by model) at USD_INR; the day is India's.
  RESERVE of it is kept for the work that matters most (a campaign about to post, hot projects, pages Google shows, the
  first areas' prices): the rest of the work may use Gemini only up to the other share.
- the free tiers (platform.llm.free_llm: Groq, GitHub Models, SambaNova, Cloudflare): at most FREE_CALLS_PER_DAY calls
  (ENRICH_FREE_CALLS_PER_DAY), and none while most of them are resting after a 429 or a timeout (`busy`), so chat and the
  newsroom keep room.
An answer is kept in `enrich_answers` under the hash of the exact question (system prompt and the page or facts it was
given): the same question again (a page that did not change, a project whose facts did not change) is answered from there
and costs no call. A question no pool has room for is put off (`deferred`): the caller keeps what it had and the project's
reading waits for room, rather than recording a failure.
Usage per day is in `enrich_llm_usage` ({_id: day, gemini_inr, gemini_calls, free_calls, cached, deferred, tokens_in,
tokens_out, steps.<step>}); `today` is the owner's view of it.
"""
import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.platform import llm as gateway

log = logging.getLogger(__name__)

ANSWERS = "enrich_answers"
USAGE = "enrich_llm_usage"
IST = timezone(timedelta(hours=5, minutes=30))
GEMINI_INR_PER_DAY = 50.0
FREE_CALLS_PER_DAY = 400
USD_INR = 88.0
RESERVE = 0.5                         # share of the Gemini rupees only urgent and premium work may spend
ANSWER_DAYS = 120                     # a kept answer nobody asked for again in this long goes
# USD per 1M tokens (in, out) by model id prefix, list prices on 2026-10-25; Gemini bills its thinking as output. A Gemini model
# not listed is priced at UNKNOWN_GEMINI, high, so the day's cap still holds when an alias moves to a dearer model.
PRICES: Dict[str, Tuple[float, float]] = {
    "gemini-3-flash": (0.50, 3.00),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-flash-lite": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-flash": (0.30, 2.50),
}
UNKNOWN_GEMINI = (1.50, 7.50)
GUESS_TOKENS = (3500, 1900)           # one call's tokens (in, out) before it is made: is there room for it

URGENT, PREMIUM, PLAIN = "urgent", "premium", "plain"
GEMINI, LITE, FREE = "gemini", "lite", "free"


def route(tier: str, step: str) -> List[str]:
    """The pools a question goes to, in turn. A campaign about to post: Gemini for everything. Premium projects (hot, shown by
    Google, the first areas): Gemini for the prices and the page text, where a wrong answer costs most; the free tiers read
    the pages for facts and highlights. The rest: the free tiers first, Gemini Lite when they are spent or resting; prices
    the other way round."""
    if tier == URGENT:
        return [GEMINI, FREE]
    if tier == PREMIUM and step in ("prices", "text"):
        return [GEMINI, FREE]
    if step == "prices":
        return [LITE, FREE]
    return [FREE, LITE]


@dataclass(frozen=True)
class Config:
    gemini_inr: float = GEMINI_INR_PER_DAY
    free_calls: int = FREE_CALLS_PER_DAY
    usd_inr: float = USD_INR
    reserve: float = RESERVE


def load() -> Config:
    def num(var: str, default: float) -> float:
        try:
            return max(0.0, float(os.environ.get(var) or default))
        except ValueError:
            log.warning("budget: %s is not a number, using %s", var, default)
            return default
    return Config(gemini_inr=num("ENRICH_GEMINI_INR_PER_DAY", GEMINI_INR_PER_DAY),
                  free_calls=int(num("ENRICH_FREE_CALLS_PER_DAY", FREE_CALLS_PER_DAY)), usd_inr=num("USD_INR", USD_INR))


def price_of(model: str) -> Tuple[float, float]:
    best = ""
    for prefix in PRICES:
        if model.startswith(prefix) and len(prefix) > len(best):
            best = prefix
    return PRICES[best] if best else UNKNOWN_GEMINI


def cost_inr(model: str, tokens_in: int, tokens_out: int, usd_inr: float) -> float:
    p_in, p_out = price_of(model)
    return (tokens_in * p_in + tokens_out * p_out) / 1_000_000 * usd_inr


def day_of(now: datetime) -> str:
    """India's date: the day's rupees start again at midnight IST."""
    now = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return now.astimezone(IST).date().isoformat()


def question_key(system: str, user: str) -> str:
    return hashlib.sha256(f"{system}\n\x00\n{user}".encode("utf-8")).hexdigest()


def busy(llm) -> bool:
    """More than half the text providers are resting after a 429 or a timeout (platform.llm.ModelHealth): work that can wait
    does, so the free tiers keep room for chat and content."""
    providers = getattr(llm, "providers", None) or ([llm] if llm is not None else [])
    resting = sum(1 for p in providers if getattr(p, "resting", lambda: False)())
    return bool(providers) and resting * 2 > len(providers)


class Reader:
    """The enrichment's model for one turn of the loop: answers from `enrich_answers` when the question was asked before, else
    from the pools `route` names, while the day's budget has room. `ask(tier, step)` gives the client a step uses."""

    budgeted = True

    def __init__(self, db, now: datetime, free=None, gemini=None, lite=None, cfg: Optional[Config] = None):
        self.db, self.now, self.cfg = db, now, cfg or load()
        self.clients = {FREE: free, GEMINI: gemini, LITE: lite}
        self.day = day_of(now)
        self.gemini_inr = 0.0
        self.gemini_calls = 0
        self.free_calls = 0
        self.deferred = 0

    async def start(self) -> "Reader":
        doc = await self.db.get_collection(USAGE).find_one({"_id": self.day}) or {}
        self.gemini_inr = float(doc.get("gemini_inr") or 0.0)
        self.gemini_calls = int(doc.get("gemini_calls") or 0)
        self.free_calls = int(doc.get("free_calls") or 0)
        return self

    def ask(self, tier: str, step: str) -> "Ask":
        return Ask(self, tier, step)

    # ---- room -----------------------------------------------------------------------------------------------------------
    def allowed(self, pool: str, tier: str) -> bool:
        client = self.clients.get(pool)
        if client is None:
            return False
        if pool == FREE:
            return self.free_calls < self.cfg.free_calls and not busy(client)
        cap = self.cfg.gemini_inr * (1.0 if tier in (URGENT, PREMIUM) else max(0.0, 1.0 - self.cfg.reserve))
        model = gateway.model_order(getattr(client, "model", "") or "")
        guess = cost_inr(model[0] if model else "", *GUESS_TOKENS, self.cfg.usd_inr)
        if self.gemini_calls:   # today's calls cost more than the guess: the next one likely does too
            guess = max(guess, self.gemini_inr / self.gemini_calls)
        return self.gemini_inr + guess <= cap

    def can_read(self, tier: str) -> bool:
        """Room for a project's reading round: some pool for the page reads and some pool for the page text."""
        return all(any(self.allowed(p, tier) for p in route(tier, s)) for s in ("web", "text"))

    # ---- asking ---------------------------------------------------------------------------------------------------------
    async def json(self, tier: str, step: str, system: str, user: str, temperature: float = 0) -> Optional[dict]:
        key = question_key(system, user)
        answers = self.db.get_collection(ANSWERS)
        kept = await answers.find_one({"_id": key})
        if kept is not None and isinstance(kept.get("answer"), dict):
            await answers.update_one({"_id": key}, {"$set": {"used_at": self.now}})
            await self._count({"cached": 1, f"steps.{step}.cached": 1})
            return kept["answer"]
        tried = False
        for pool in route(tier, step):
            if not self.allowed(pool, tier):
                continue
            tried = True
            out = await self._call(pool, step, system, user, temperature)
            if isinstance(out, dict):
                await answers.update_one({"_id": key}, {"$set": {"answer": out, "step": step, "at": self.now, "used_at": self.now}},
                                         upsert=True)
                return out
        if not tried:   # no pool has room today: put off, not failed
            self.deferred += 1
            await self._count({"deferred": 1, f"steps.{step}.deferred": 1})
        return None

    async def forget(self, system: str, user: str) -> None:
        """A kept answer the caller refused (a page text that failed its checks): the next round asks again."""
        await self.db.get_collection(ANSWERS).delete_one({"_id": question_key(system, user)})

    async def _call(self, pool: str, step: str, system: str, user: str, temperature: float) -> Any:
        client = self.clients[pool]
        seen: List[dict] = []
        token = gateway.USAGE.set(seen.append)
        try:
            out = await (client.json(system, user, temperature=temperature) if temperature else client.json(system, user))
        except Exception:
            log.exception("budget: %s call failed", pool)
            out = None
        finally:
            gateway.USAGE.reset(token)
        tokens_in = sum(u["prompt_tokens"] for u in seen)
        tokens_out = sum(u["output_tokens"] for u in seen)
        inc: Dict[str, Any] = {"tokens_in": tokens_in, "tokens_out": tokens_out, f"steps.{step}.calls": 1}
        if pool == FREE:
            self.free_calls += 1
            inc["free_calls"] = 1
        else:
            if seen:
                inr = sum(cost_inr(u["model"], u["prompt_tokens"], u["output_tokens"], self.cfg.usd_inr) for u in seen)
            else:   # no usage reported (an error before the answer, a provider that does not say): charge the guess
                model = gateway.model_order(getattr(client, "model", "") or "")
                inr = cost_inr(model[0] if model else "", *GUESS_TOKENS, self.cfg.usd_inr)
            self.gemini_inr += inr
            self.gemini_calls += 1
            inc.update({"gemini_inr": round(inr, 4), "gemini_calls": 1, f"steps.{step}.gemini_inr": round(inr, 4)})
        await self._count(inc)
        return out

    async def _count(self, inc: Dict[str, Any]) -> None:
        await self.db.get_collection(USAGE).update_one({"_id": self.day}, {"$inc": inc, "$set": {"at": self.now}}, upsert=True)


class Ask:
    """The client one step of one project uses: `json(system, user)` like any LLM, through the Reader's cache and budget."""

    budgeted = True

    def __init__(self, reader: Reader, tier: str, step: str):
        self.reader, self.tier, self.step = reader, tier, step

    async def json(self, system: str, user: str, temperature: float = 0) -> Optional[dict]:
        return await self.reader.json(self.tier, self.step, system, user, temperature)

    async def forget(self, system: str, user: str) -> None:
        await self.reader.forget(system, user)

    @property
    def deferred(self) -> int:
        return self.reader.deferred


async def reader(db, now: datetime, cfg: Optional[Config] = None) -> Optional[Reader]:
    """Today's Reader over the configured providers, or None when no model key is set at all."""
    free, gemini, lite = gateway.free_llm(), gateway.gemini_llm(), gateway.gemini_llm(lite=True)
    if free is None and gemini is None:
        return None
    return await Reader(db, now, free=free, gemini=gemini, lite=lite, cfg=cfg).start()


async def prune(db, now: datetime) -> int:
    """Kept answers nobody asked for in ANSWER_DAYS (a page that changed, a project dropped) go."""
    res = await db.get_collection(ANSWERS).delete_many({"used_at": {"$lt": now - timedelta(days=ANSWER_DAYS)}})
    return int(getattr(res, "deleted_count", 0) or 0)


async def today(db, now: datetime, cfg: Optional[Config] = None) -> dict:
    """The owner's view of today's spend against the caps."""
    cfg = cfg or load()
    doc = await db.get_collection(USAGE).find_one({"_id": day_of(now)}) or {}
    return {"day": day_of(now), "gemini_inr": round(float(doc.get("gemini_inr") or 0.0), 2), "gemini_inr_cap": cfg.gemini_inr,
            "gemini_calls": int(doc.get("gemini_calls") or 0), "free_calls": int(doc.get("free_calls") or 0),
            "free_calls_cap": cfg.free_calls, "cached": int(doc.get("cached") or 0), "deferred": int(doc.get("deferred") or 0),
            "steps": doc.get("steps") or {}}
