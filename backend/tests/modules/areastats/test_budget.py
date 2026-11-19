"""The enrichment's model spend: answers kept by question, Gemini metered in rupees per India's day, the free tiers counted,
premium work first to Gemini, and a question put off (not failed) when no pool has room."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import budget
from app.platform import llm as gateway

from ..fakes import FakeDb

NOW = datetime(2026, 10, 25, 6, 0, tzinfo=timezone.utc)    # 11:30 in India
CFG = budget.Config(gemini_inr=50.0, free_calls=3, usd_inr=88.0, reserve=0.5)


class Model:
    """A provider: answers, and reports its tokens like platform.llm.GroqLLM does."""

    def __init__(self, name, model="", tokens=(3000, 1500), answer=True, resting=False):
        self.name, self.model, self.tokens, self.answer, self._resting, self.calls = name, model, tokens, answer, resting, 0

    def resting(self):
        return self._resting

    async def json(self, system, user, temperature=0):
        self.calls += 1
        hook = gateway.USAGE.get()
        if hook and self.model:
            hook({"url": "u", "model": self.model, "prompt_tokens": self.tokens[0], "output_tokens": self.tokens[1]})
        return {"by": self.name} if self.answer else None


def models():
    return (Model("free"), Model("gemini", "gemini-3-flash-preview"), Model("lite", "gemini-flash-lite-latest"))


async def reader(db, free, gemini, lite, now=NOW, cfg=CFG):
    return await budget.Reader(db, now, free=free, gemini=gemini, lite=lite, cfg=cfg).start()


def test_gemini_is_priced_from_its_tokens_with_unknown_models_priced_high():
    assert round(budget.cost_inr("gemini-3-flash-preview", 1_000_000, 0, 88.0), 2) == 44.0
    assert round(budget.cost_inr("gemini-3-flash-preview", 3300, 1600, 88.0), 2) == 0.57
    assert budget.price_of("gemini-flash-lite-latest") == budget.PRICES["gemini-flash-lite"]
    assert budget.price_of("gemini-9-ultra") == budget.UNKNOWN_GEMINI


def test_the_day_is_indias():
    assert budget.day_of(datetime(2026, 10, 24, 18, 29, tzinfo=timezone.utc)) == "2026-10-24"
    assert budget.day_of(datetime(2026, 10, 24, 18, 31, tzinfo=timezone.utc)) == "2026-10-25"


def test_premium_prices_and_text_go_to_gemini_first_the_rest_to_the_free_tiers():
    assert budget.route(budget.URGENT, "web") == [budget.GEMINI, budget.FREE]
    assert budget.route(budget.PREMIUM, "prices") == [budget.GEMINI, budget.FREE]
    assert budget.route(budget.PREMIUM, "web") == [budget.FREE, budget.LITE]
    assert budget.route(budget.PLAIN, "text") == [budget.FREE, budget.LITE]
    assert budget.route(budget.PLAIN, "prices") == [budget.LITE, budget.FREE]


def test_judging_a_picture_goes_to_gemini_never_the_free_tiers_which_do_not_take_images():
    assert budget.route(budget.PLAIN, "area_picture") == [budget.LITE, budget.GEMINI]
    assert budget.route(budget.URGENT, "area_picture") == [budget.GEMINI, budget.FREE]  # urgent still wins as ever


async def test_the_same_question_again_costs_no_call():
    db = FakeDb()
    free, gemini, lite = models()
    r = await reader(db, free, gemini, lite)
    assert await r.ask(budget.PLAIN, "web").json("sys", "page A") == {"by": "free"}
    assert await r.ask(budget.PLAIN, "web").json("sys", "page A") == {"by": "free"}
    assert free.calls == 1
    assert await r.ask(budget.PLAIN, "web").json("sys v2", "page A") == {"by": "free"}   # a new prompt asks again
    assert free.calls == 2
    usage = await budget.today(db, NOW, CFG)
    assert usage["free_calls"] == 2 and usage["cached"] == 1 and usage["steps"]["web"]["calls"] == 2


async def test_a_refused_answer_is_forgotten_and_asked_again():
    db = FakeDb()
    free, gemini, lite = models()
    r = await reader(db, free, gemini, lite)
    ask = r.ask(budget.PLAIN, "text")
    await ask.json("sys", "facts")
    await ask.forget("sys", "facts")
    await ask.json("sys", "facts")
    assert free.calls == 2


async def test_gemini_stops_at_the_days_rupees_and_plain_work_only_spends_the_unreserved_half():
    db = FakeDb()
    free, gemini, lite = Model("free", resting=True), Model("gemini", "gemini-3-flash-preview", tokens=(200_000, 50_000)), \
        Model("lite", "gemini-flash-lite-latest", tokens=(200_000, 50_000))
    r = await reader(db, free, gemini, lite)
    # ~Rs 22 a premium call: two fit under Rs 50, the third would not
    for i in range(3):
        await r.ask(budget.PREMIUM, "text").json("sys", f"facts {i}")
    assert gemini.calls == 2 and r.deferred == 1
    usage = await budget.today(db, NOW, CFG)
    assert 40 < usage["gemini_inr"] <= 50 and usage["gemini_calls"] == 2 and usage["deferred"] == 1
    # plain work may not touch Gemini past half of Rs 50, and the free tiers are resting: put off
    assert await r.ask(budget.PLAIN, "web").json("sys", "page") is None and lite.calls == 0 and r.deferred == 2
    # the next Indian day starts again, from what is stored
    tomorrow = await reader(db, free, gemini, lite, now=NOW + timedelta(days=1))
    assert tomorrow.gemini_inr == 0 and tomorrow.can_read(budget.PREMIUM)
    again = await reader(db, free, gemini, lite)
    assert again.gemini_inr > 40 and not again.can_read(budget.PLAIN)


async def test_the_free_tiers_stop_at_their_daily_calls_then_plain_work_falls_to_gemini_lite():
    db = FakeDb()
    free, gemini, lite = models()
    r = await reader(db, free, gemini, lite)
    for i in range(4):
        await r.ask(budget.PLAIN, "web").json("sys", f"page {i}")
    assert free.calls == 3 and lite.calls == 1 and gemini.calls == 0


async def test_no_room_anywhere_puts_the_question_off_and_a_failed_answer_is_not_kept():
    db = FakeDb()
    r = await reader(db, Model("free", answer=False), None, None)
    assert await r.ask(budget.PLAIN, "web").json("sys", "page") is None and r.deferred == 0   # asked, no answer: a failure
    assert await db.get_collection(budget.ANSWERS).count_documents({}) == 0
    r = await reader(db, None, None, None)
    assert await r.ask(budget.PLAIN, "web").json("sys", "page") is None and r.deferred == 1   # nothing to ask: put off
    assert not r.can_read(budget.URGENT)


async def test_answers_nobody_asked_for_in_a_long_while_are_pruned():
    db = FakeDb()
    answers = db.get_collection(budget.ANSWERS)
    await answers.insert_one({"_id": "old", "answer": {}, "used_at": NOW - timedelta(days=budget.ANSWER_DAYS + 1)})
    await answers.insert_one({"_id": "new", "answer": {}, "used_at": NOW - timedelta(days=3)})
    assert await budget.prune(db, NOW) == 1
    assert [d["_id"] for d in answers.docs] == ["new"]


def test_the_caps_come_from_the_environment(monkeypatch):
    monkeypatch.delenv("ENRICH_GEMINI_INR_PER_DAY", raising=False)
    assert budget.load().gemini_inr == 50.0
    monkeypatch.setenv("ENRICH_GEMINI_INR_PER_DAY", "20")
    monkeypatch.setenv("ENRICH_FREE_CALLS_PER_DAY", "250")
    cfg = budget.load()
    assert cfg.gemini_inr == 20.0 and cfg.free_calls == 250


async def test_a_paid_model_refusing_every_call_counts_as_no_room_for_an_hour():
    # 2026-11-19: Google refused every Gemini call (monthly spending cap); once the free tiers' day was spent each read paid
    # Serper for its searches and got nothing
    db = FakeDb()
    free, gemini, lite = Model("free"), Model("gemini", "gemini-3-flash-preview"), Model("lite", "gemini-flash-lite-latest", answer=False)
    r = await reader(db, free, gemini, lite, cfg=budget.Config(gemini_inr=50.0, free_calls=0, usd_inr=88.0, reserve=0.5))
    for i in range(budget.REFUSED_AFTER):
        assert await r.json(budget.PLAIN, "web", "s", f"q{i}") is None
    assert lite.calls == budget.REFUSED_AFTER
    assert not r.can_read(budget.PLAIN)                      # the read waits instead of searching for nothing
    again = await reader(db, free, gemini, lite, cfg=budget.Config(gemini_inr=50.0, free_calls=0, usd_inr=88.0, reserve=0.5))
    assert again.refusing(budget.LITE)                       # kept on the day's record: the next round knows too
    later = await reader(db, free, gemini, lite, now=NOW + budget.REFUSED_REST, cfg=budget.Config(gemini_inr=50.0, free_calls=0, usd_inr=88.0, reserve=0.5))
    assert not later.refusing(budget.LITE)                   # asked again after the rest


async def test_an_answer_ends_a_paid_models_run_of_refusals():
    db = FakeDb()
    lite = Model("lite", "gemini-flash-lite-latest", answer=False)
    r = await reader(db, Model("free"), Model("gemini", "gemini-3-flash-preview"), lite,
                     cfg=budget.Config(gemini_inr=50.0, free_calls=0, usd_inr=88.0, reserve=0.5))
    for i in range(budget.REFUSED_AFTER - 1):
        await r.json(budget.PLAIN, "web", "s", f"q{i}")
    lite.answer = True
    assert await r.json(budget.PLAIN, "web", "s", "ok") == {"by": "lite"}
    assert r.pools[budget.LITE]["streak"] == 0 and not r.refusing(budget.LITE)
