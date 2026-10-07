"""The gentle register refresh behind the area stats: the pincode sweep, relabelling, and details from MahaRERA's project API."""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.modules.areastats import refresh
from app.modules.areastats.service import area_stats
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 4, 6, 0, tzinfo=timezone.utc)
FIX = Path(__file__).parents[1] / "newsroom" / "fixtures" / "sources"
LAST = (FIX / "maharera_pune_last.html").read_text(encoding="utf-8")  # 10 real cards; we set their pincodes per test
EMPTY = "<html><body>Registered Projects Search Record No Records Found</body></html>"
PINS = refresh.pincodes()  # ['411014', '411036', '411045', '411047', '411057', '412207']


def page_of(pincode: str, total: int, name_suffix: str = "") -> str:
    """The fixture page as a pincode listing: every card in `pincode`, the count set to `total`."""
    body = re.sub(r"(<div class=\"greyColor\">Pincode</div>\s*<p>)\d{6}(</p>)", rf"\g<1>{pincode}\g<2>", LAST)
    body = body.replace(">12920<", f">{total}<", 1)
    return body.replace("</strong></h4>", f"{name_suffix}</strong></h4>") if name_suffix else body


def site(pages: dict, calls: list):
    """pages: (pincode, page) -> body; anything else is the flaky empty answer."""
    async def get(url):
        calls.append(url)
        pin = re.search(r"project_location=(\d*)&", url).group(1)
        page = int(re.search(r"[?&]page=(\d+)&", url).group(1))
        return pages.get((pin, page), EMPTY)
    return get


def asked(calls):
    return [(re.search(r"project_location=(\d*)&", u).group(1), int(re.search(r"[?&]page=(\d+)&", u).group(1))) for u in calls]


def test_sweep_covers_every_area_pincode():
    assert PINS == ["411014", "411036", "411045", "411047", "411057", "412207"]


async def test_sweep_reads_pages_in_turn_and_moves_to_the_next_pincode():
    store, calls = Store(FakeDb()), []
    pages = {("411014", 1): page_of("411014", 15), ("411014", 2): page_of("411014", 15), ("411036", 1): page_of("411036", 3)}
    out = await refresh.sweep(store, site(pages, calls), NOW, pages=3)
    assert asked(calls) == [("411014", 1), ("411014", 2), ("411036", 1)]
    assert out["pages"] == 3 and out["new"] == 10 and out["updated"] == 10  # page 2 is the same cards again
    # 411036 is shared with Mundhwa: none of these names says Keshav Nagar, so none is stored for it
    assert {d["locality"] for d in await store.all_projects()} == {"kharadi"}
    mark = await store.get_mark(refresh.MARK)
    assert (mark["pincode"], mark["page"]) == ("411045", 1)


async def test_shared_pincode_keeps_only_named_projects():
    store, calls = Store(FakeDb()), []
    await store.set_mark(refresh.MARK, pincode="411057", page=1, last=0)
    named = page_of("411057", 5).replace("VIKRAM MARQUEE", "VIKRAM MARQUEE WAKAD", 1).replace("Satvam Hills C5", "Hinjewadi Hills", 1)
    await refresh.sweep(store, site({("411057", 1): named}, calls), NOW, pages=1)
    got = {d["name"]: d["locality"] for d in await store.all_projects()}
    assert got == {"VIKRAM MARQUEE WAKAD": "wakad", "Hinjewadi Hills": "hinjawadi"}


async def test_sweep_wraps_round_and_marks_it():
    store, calls = Store(FakeDb()), []
    await store.set_mark(refresh.MARK, pincode="412207", page=2, last=2)
    out = await refresh.sweep(store, site({("412207", 2): page_of("412207", 20)}, calls), NOW, pages=1)
    assert out["round_done"] and (await store.get_mark(refresh.MARK))["round_done_at"] == NOW
    mark = await store.get_mark(refresh.MARK)
    assert (mark["pincode"], mark["page"]) == ("411014", 1)
    assert {d["locality"] for d in await store.all_projects()} == {"wagholi"}


async def test_a_flaky_page_is_asked_again_then_skipped():
    store, calls = Store(FakeDb()), []
    await store.set_mark(refresh.MARK, pincode="411047", page=4, last=20)
    for _ in range(refresh.SKIP_AFTER_MISSES - 1):
        out = await refresh.sweep(store, site({}, calls), NOW, pages=3)
        assert out["pages"] == 1 and out["empty"] == 1  # it stops at once: the site is struggling
        assert (await store.get_mark(refresh.MARK))["page"] == 4
    await refresh.sweep(store, site({}, calls), NOW, pages=3)
    mark = await store.get_mark(refresh.MARK)
    assert (mark["pincode"], mark["page"], mark["misses"]) == ("411047", 5, 0)  # skipped; the next round reads it again


async def test_relabel_moves_411047_from_wagholi_to_lohegaon():
    store = Store(FakeDb())
    base = {"pincode": "411047", "locality": "wagholi", "locality_from": "pincode", "news": []}
    await store.projects.insert_one({**base, "_id": "P1", "name": "Belmont Skyone"})
    await store.projects.insert_one({**base, "_id": "P2", "name": "Solitaire Business Hub Viman Nagar Phase 1"})
    await store.projects.insert_one({**base, "_id": "P3", "name": "Kharadi Pune P1", "pincode": "412207"})
    assert await refresh.relabel(store) == 2
    got = {d["_id"]: (d["locality"], d["locality_from"]) for d in await store.all_projects()}
    assert got == {"P1": ("lohegaon", "pincode"), "P2": (None, "not in our areas"), "P3": ("wagholi", "pincode")}
    assert await refresh.relabel(store) == 0
    assert (await area_stats(store.db, "lohegaon", NOW.date()))["projects"] == 1
    assert (await area_stats(store.db, "wagholi", NOW.date()))["projects"] == 1


def general(regno, units=120, sold=70):
    return {"status": "1", "responseObject": {
        "projectRegistartionNo": regno, "projectName": "X", "projectTypeName": "Residential / Group Housing",
        "reraRegistrationDate": "2026-09-01", "originalProjectProposeCompletionDate": "2029-06-30",
        "projectProposeComplitionDate": "2029-12-31", "totalNumberOfUnits": units, "totalNumberOfSoldUnits": sold}}


async def seeded(*specs):
    store = Store(FakeDb())
    for regno, locality, mid, extra in specs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": regno, "locality": locality, "news": [],
                                         "source_url": f"https://maharerait.maharashtra.gov.in/public/project/view/{mid}" if mid else
                                         "https://www.maharera.maharashtra.gov.in/projects-search-result?regno=" + regno, **extra})
    return store


async def test_details_fill_completion_and_homes_never_read_first():
    store = await seeded(("PR1", "wagholi", 11, {"details_checked_at": NOW - timedelta(days=40), "details_ok": True}),
                         ("PR2", "wagholi", 12, {}),
                         ("PR3", None, 13, {}),  # not in our areas: never read
                         ("PR4", "baner", 14, {"details_checked_at": NOW - timedelta(days=3), "details_ok": True}))  # fresh
    asked_ids = []

    async def fetch(mid):
        asked_ids.append(mid)
        return general({11: "PR1", 12: "PR2"}[mid])

    out = await refresh.details(store, fetch, NOW, limit=5)
    assert asked_ids == [12, 11] and out == {"read": 2, "failed": 0}
    p2 = await store.project("PR2")
    assert (p2["completion_now"], p2["completion_at_registration"], p2["units_total"], p2["units_booked"]) == \
        ("2029-12-31", "2029-06-30", 120, 70)
    assert p2["details_ok"] and p2["details_checked_at"] == NOW and p2["name"] == "PR2"  # the register's name is kept
    assert "completion_now" not in await store.project("PR3")
    assert await refresh.details(store, fetch, NOW + timedelta(hours=3)) == {"read": 0, "failed": 0}  # nothing due


async def test_details_limit_and_failures_retry_next_day():
    store = await seeded(("PR1", "wagholi", 11, {}), ("PR2", "wagholi", 12, {}), ("PR3", "wagholi", None, {}))

    async def fetch(mid):
        return None if mid == 11 else general("SOMEONE-ELSE")  # down, and a different registration

    out = await refresh.details(store, fetch, NOW, limit=2)
    assert out == {"read": 0, "failed": 2}
    out = await refresh.details(store, fetch, NOW, limit=5)
    assert out == {"read": 0, "failed": 1}  # PR3 (no project id in its link); the other two wait a day
    assert all(d["details_ok"] is False for d in await store.all_projects())
    assert (await refresh.details(store, fetch, NOW + timedelta(days=1), limit=5))["failed"] == 3


async def test_step_runs_all_parts_and_survives_a_broken_one():
    store, calls = Store(FakeDb()), []
    await store.projects.insert_one({"_id": "P1", "name": "Belmont Skyone", "pincode": "411047", "locality": "wagholi", "news": []})

    async def fetch(mid):
        raise RuntimeError("boom")

    out = await refresh.step(store, site({("411014", 1): page_of("411014", 10)}, calls), fetch, NOW, pages=1, limit=5)
    assert out["sweep"]["new"] == 10 and out["relabel"] == 1 and out["details"] is None
    assert (await store.project("P1"))["locality"] == "lohegaon"
