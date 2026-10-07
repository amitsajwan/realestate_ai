"""The register's watch list (projects outside our areas kept fresh) and the automatic catch-up of the refresh step."""
from datetime import timedelta

from app.modules.areastats import refresh, watch
from app.modules.areastats.watch import WatchItem
from app.modules.newsroom.store import Store

from ..fakes import FakeDb
from .test_refresh import NOW, general, seeded

GULMOHAR = WatchItem("P52100076768", 46398, "Gulmohar City", "412209")   # Ranjangaon: outside our 8 areas


def source(*items):
    async def fn():
        return list(items)
    return fn


async def test_a_source_adds_a_project_outside_our_areas_and_its_details_are_kept_fresh():
    store = Store(FakeDb())
    watch.add_source("agent_projects", source(GULMOHAR))
    out = await watch.sync(store, NOW)
    assert out["watched"] == 1
    doc = await store.project("P52100076768")
    assert doc["locality"] is None and doc["watched_by"] == ["agent_projects"] and doc["source_url"].endswith("/46398")

    asked = []

    async def fetch(mid):
        asked.append(mid)
        return general("P52100076768")

    assert await refresh.details(store, fetch, NOW, limit=5) == {"read": 1, "failed": 0} and asked == [46398]
    assert (await store.project("P52100076768"))["completion_now"] == "2029-12-31"
    await refresh.relabel(store)  # the rules still say: not ours
    assert (await store.project("P52100076768"))["locality"] is None


async def test_a_watched_project_never_counts_in_area_stats():
    store = await seeded(("PR1", "wagholi", 11, {}))
    watch.add_source("agent_projects", source(WatchItem("PR9", 99, "Far Away", "412209")))
    await watch.sync(store, NOW)
    assert [d["_id"] for d in await store.projects_in(["wagholi"])] == ["PR1"]   # what the area stats read
    assert (await store.project("PR9"))["locality"] is None


async def test_an_in_area_project_a_source_watches_keeps_its_area():
    store = await seeded(("PR1", "wagholi", 11, {}))
    watch.add_source("agent_projects", source(WatchItem("PR1")))   # already known: no MahaRERA id needed
    await watch.sync(store, NOW)
    doc = await store.project("PR1")
    assert doc["locality"] == "wagholi" and doc["watched_by"] == ["agent_projects"]


async def test_a_dropped_project_stops_being_watched_and_a_broken_source_changes_nothing():
    store = Store(FakeDb())
    watch.add_source("agent_projects", source(GULMOHAR))
    watch.add_source("property_facts", source(GULMOHAR))
    await watch.sync(store, NOW)
    assert (await store.project(GULMOHAR.regno))["watched_by"] == ["agent_projects", "property_facts"]

    watch.add_source("agent_projects", source())          # the agent removed the project
    async def broken():
        raise RuntimeError("db down")
    watch.add_source("property_facts", broken)           # this source fails this time
    out = await watch.sync(store, NOW)
    assert out["dropped"] == 1 and out["failed_sources"] == ["property_facts"]
    assert (await store.project(GULMOHAR.regno))["watched_by"] == ["property_facts"]


async def test_an_unknown_project_without_a_maharera_id_is_skipped():
    store = Store(FakeDb())
    watch.add_source("x", source(WatchItem("P99999999999")))
    assert (await watch.sync(store, NOW))["skipped"] == 1 and await store.project("P99999999999") is None


async def test_step_catches_up_while_behind_then_goes_back_to_gentle():
    store = await seeded(*[(f"PR{i}", "wagholi", 100 + i, {"pincode": "412207"}) for i in range(30)])
    reads = []

    async def fetch(mid):
        reads.append(mid)
        return general(f"PR{mid - 100}")

    async def get(url):
        return "<html>No Records Found</html>"

    out = await refresh.step(store, get, fetch, NOW)        # first round not done, 30 waiting: catch up
    assert out["mode"] == "catch-up" and out["details"]["read"] == 30 and out["sweep"]["pages"] == 1  # empty page: stops early

    await store.set_mark(refresh.MARK, round_done_at=NOW)
    out = await refresh.step(store, get, fetch, NOW + timedelta(hours=3))
    assert out["mode"] == "steady" and out["details"] == {"read": 0, "failed": 0}
    assert refresh.CATCHUP_DETAILS > refresh.DETAILS_PER_STEP and refresh.CATCHUP_PAGES > refresh.SWEEP_PAGES


async def test_explicit_sizes_are_kept_for_the_backfill_script():
    store = await seeded(*[(f"PR{i}", "wagholi", 100 + i, {"pincode": "412207"}) for i in range(5)])

    async def fetch(mid):
        return general(f"PR{mid - 100}")

    async def get(url):
        return "<html>No Records Found</html>"

    out = await refresh.step(store, get, fetch, NOW, pages=1, limit=2)
    assert out["mode"] == "steady" and out["details"]["read"] == 2
