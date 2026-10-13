"""Can we tell from the logs and `python -m app.worker --check` that the MahaRERA register and the enrichment are working?"""
import logging
from datetime import timedelta

from app.modules.areastats import enrich, refresh

from .test_enrich import GOOD, FakeLLM, gatherer, ready  # noqa: F401 (gatherer: the autouse fake gatherer)
from .test_enrich import NOW as ENRICH_NOW
from .test_pages import FULL
from .test_refresh import EMPTY, NOW, general, seeded


async def _step(store, caplog, fetch=None):
    async def get(url):
        return EMPTY

    async def ok(mid):
        return general(f"PR{mid - 100}")
    with caplog.at_level(logging.INFO, logger=refresh.log.name):
        return await refresh.step(store, get, fetch or ok, NOW)


async def test_a_step_gives_new_projects_their_page(caplog):
    """Regression: step() took `pages` (a count) and so could not reach the pages module; every step failed this part."""
    store = await seeded(*[(f"PR{i}", "wagholi", 100 + i, {"pincode": "412207"}) for i in range(3)])
    out = await _step(store, caplog)
    assert out["pages"] == 3
    assert all([(await store.project(f"PR{i}")).get("page_slug") for i in range(3)])
    assert not [r for r in caplog.records if "pipeline=rera ref=register step=pages outcome=failed" in r.getMessage()]


async def test_each_part_of_a_step_logs_its_outcome(caplog):
    store = await seeded(*[(f"PR{i}", "wagholi", 100 + i, {"pincode": "412207"}) for i in range(3)])

    async def down(mid):
        return None
    await _step(store, caplog, fetch=down)
    lines = {r.getMessage().split("step=")[1].split()[0]: r for r in caplog.records if "pipeline=rera ref=register" in r.getMessage()}
    assert set(lines) == {"sweep", "relabel", "discover", "watch", "details", "pages"}
    assert "outcome=fallback" in lines["sweep"].getMessage() and "empty=1" in lines["sweep"].getMessage()   # MahaRERA's empty page
    assert "outcome=fallback" in lines["details"].getMessage() and "failed=3" in lines["details"].getMessage()
    assert lines["details"].levelno == logging.WARNING


async def test_a_failing_part_is_logged_as_failed_and_the_rest_still_run(caplog, monkeypatch):
    store = await seeded(("PR1", "wagholi", 101, {"pincode": "412207"}))

    async def broken(store):
        raise RuntimeError("db down")
    monkeypatch.setattr(refresh, "relabel", broken)
    out = await _step(store, caplog)
    assert out["relabel"] is None and out["details"] == {"read": 1, "failed": 0}
    assert any("step=relabel outcome=failed" in r.getMessage() and "db down" in r.getMessage() for r in caplog.records)


async def test_status_says_whether_the_register_is_moving():
    store = await seeded(("PR1", "wagholi", 101, {"details_ok": True, "details_checked_at": NOW, "page_slug": "pr1"}),
                         ("PR2", "wagholi", 102, {"details_ok": False, "details_checked_at": NOW}),
                         ("PR3", "wagholi", 103, {}))
    lines = await refresh.status(store, NOW)
    assert lines[0].startswith("WARN rera sweep: never ran")
    assert "3 projects in our areas" in lines[1] and "details ok 1, last read failed 1, never read 1" in lines[1]
    assert lines[2].startswith("WARN rera pages: 1 of 3")
    await store.set_mark(refresh.MARK, pincode="412207", page=4, at=NOW - timedelta(hours=2))
    lines = await refresh.status(store, NOW)
    assert lines[0].startswith("OK   rera sweep: at pincode 412207 page 4, moved 2.0h ago; first round not finished")
    await store.set_mark(refresh.MARK, at=NOW - timedelta(days=3))
    assert (await refresh.status(store, NOW))[0].startswith("WARN")


async def test_an_enrichment_logs_what_it_did_and_why(caplog):
    _, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    doc = await enrich.next_project(store, ENRICH_NOW)
    with caplog.at_level(logging.INFO, logger=enrich.log.name):
        await enrich.enrich_one(store, doc, FakeLLM(GOOD), ENRICH_NOW)
        await enrich.enrich_one(store, doc, None, ENRICH_NOW)
    msgs = [r.getMessage() for r in caplog.records if "pipeline=enrich ref=P1 step=done" in r.getMessage()]
    assert "outcome=ok text=model facts=gathered" in msgs[0]
    assert "outcome=fallback text=code" in msgs[1] and "no LLM key" in msgs[1]
