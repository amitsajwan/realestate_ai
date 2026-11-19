"""New pages go into search a few a day, the richest first (areastats.entry)."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import entry, pages

from .test_pages import FULL, seeded

NOW = datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc)          # 11:30 in India
TEXT = "Few homes left: Few homes are left to book here."
PRICED = {**FULL, "page_text": TEXT, "prices": {"rows": [{"bhk": "2 BHK"}]}}
RICH = {**PRICED, "web_facts": {"facts": [{"k": "towers", "v": "3"}]}, "profile": {"highlights": ["Clubhouse"]}}
WAIT = {"wait": True, "at": NOW - timedelta(hours=2)}


def _waiting(n: int, extra: dict = PRICED):
    return [(f"W{i}", f"Waiting {i}", "wagholi", {**extra, "search_state": WAIT}) for i in range(n)]


async def _in_search(store) -> set:
    return {d["_id"] async for d in store.projects.find({"search_state.in": True})}


async def test_no_more_than_the_days_number_go_in():
    db, store = await seeded(*_waiting(entry.ENTRIES_PER_DAY + 5))
    out = await entry.admit(store, NOW)
    assert len(out["let_in"]) == entry.ENTRIES_PER_DAY and out["waiting"] == 5
    out = await entry.admit(store, NOW + timedelta(hours=3))    # later the same day: no room left
    assert out["let_in"] == [] and out["waiting"] == 5


async def test_pages_let_in_earlier_today_use_up_the_room():
    today = [(f"T{i}", f"Today {i}", "wagholi", {**PRICED, "search_state": {"in": True, "at": NOW - timedelta(hours=4)}})
             for i in range(entry.ENTRIES_PER_DAY - 2)]
    yesterday = [("Y", "Yesterday", "wagholi", {**PRICED, "search_state": {"in": True, "at": NOW - timedelta(hours=12)}})]   # 23:30 IST
    db, store = await seeded(*today, *yesterday, *_waiting(5))
    out = await entry.admit(store, NOW)
    assert len(out["let_in"]) == 2 and out["today"] == entry.ENTRIES_PER_DAY


async def test_the_next_india_day_lets_more_in():
    db, store = await seeded(*_waiting(entry.ENTRIES_PER_DAY + 5))
    await entry.admit(store, NOW)
    out = await entry.admit(store, NOW + timedelta(days=1))
    assert len(out["let_in"]) == 5 and out["waiting"] == 0


async def test_the_richest_waiting_pages_go_first():
    db, store = await seeded(*_waiting(entry.ENTRIES_PER_DAY), ("R", "Rich", "wagholi", {**RICH, "search_state": WAIT}))
    out = await entry.admit(store, NOW)
    assert "R" in out["let_in"] and out["let_in"][0] == "R"
    assert entry.facts_held(RICH) == 3 and entry.facts_held(PRICED) == 1


async def test_a_waiting_page_no_longer_ready_stays_out_and_keeps_waiting():
    db, store = await seeded(("G", "Gone thin", "wagholi", {**PRICED, "prices": {"rows": []}, "search_state": WAIT}))
    out = await entry.admit(store, NOW)
    assert out["let_in"] == [] and not pages.searchable(await store.project("G"), NOW)
    assert (await store.project("G"))["search_state"] == WAIT


async def test_a_page_made_ready_outside_a_round_joins_the_list():
    db, store = await seeded(("N", "New", "wagholi", PRICED), ("X", "No text", "wagholi", {**FULL}))
    out = await entry.admit(store, NOW)
    assert out["joined"] == 1 and out["let_in"] == ["N"]
    assert "search_state" not in await store.project("X")


async def test_pages_already_in_search_are_never_touched():
    held = {"in": True, "at": NOW - timedelta(days=3)}
    db, store = await seeded(("I", "In", "wagholi", {**PRICED, "search_state": held}), *_waiting(1))
    await entry.admit(store, NOW)
    assert (await store.project("I"))["search_state"] == held and await _in_search(store) == {"I", "W0"}


async def test_the_list_is_looked_at_every_ten_minutes():
    db, store = await seeded(*_waiting(1))
    assert await entry.admit(store, NOW, last=NOW - timedelta(minutes=5)) is None
    assert await entry.admit(store, NOW, last=NOW - entry.EVERY) is not None
