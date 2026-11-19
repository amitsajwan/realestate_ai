"""The page-by-page audit: one bucket and one action per page, from Search Console's counts and the stored index checks."""
import base64
import json
from datetime import datetime, timedelta, timezone

import httpx

from app.modules.newsroom.store import Store
from app.modules.seo import coverage, pageaudit

from ..areastats.test_searchconsole import fake_key
from ..fakes import FakeDb

NOW = datetime(2026, 11, 19, 9, 0, tzinfo=timezone.utc)
AFTER_HOLD = datetime(2026, 12, 20, 9, 0, tzinfo=timezone.utc)
SITE = "https://avasetu.in"


def doc(path, verdict="PASS", state="Submitted and indexed", listed=True):
    return {"_id": SITE + path, "verdict": verdict, "state": state, coverage.LISTED: listed}


def by_path(rows):
    return {r["path"]: r for r in rows}


def test_each_path_belongs_to_one_section_of_the_site():
    assert pageaudit.kind_of("/") == "home"
    assert pageaudit.kind_of("/projects/godrej-ivara") == "project"
    assert pageaudit.kind_of("/projects/area/kharadi/top") == "area"
    assert pageaudit.kind_of("/projects") == "hub"
    assert pageaudit.kind_of("/localities/wagholi") == "locality"
    assert pageaudit.kind_of("/news/track/purandar-airport") == "tracker"
    assert pageaudit.kind_of("/news/abc") == "news"
    assert pageaudit.kind_of("/pune-maharera-tracker") == "research"
    assert pageaudit.kind_of("/price/50-75-lakh/wagholi") == "listing"
    assert pageaudit.kind_of("/about") == "other"


def test_a_page_with_clicks_is_kept_steady_and_listed_before_quiet_pages():
    rows = pageaudit.audit({"/projects/a": {"impressions": 400, "clicks": 12, "position": 6.2}},
                           {"/projects/a": {"impressions": 200}}, [], [doc("/projects/a"), doc("/projects/b")], NOW)
    assert [r["path"] for r in rows] == ["/projects/a", "/projects/b"]
    a = rows[0]
    assert a["bucket"] == "earning" and a["trend"] == "rising" and a["ctr"] == 0.03 and "steady" in a["action"]


def test_page_one_with_almost_no_clicks_waits_for_the_title_hold():
    counts = {"/projects/area/wagholi": {"impressions": 900, "clicks": 3, "position": 7.0}}
    held = by_path(pageaudit.audit(counts, {}, [], [], NOW))["/projects/area/wagholi"]
    assert held["bucket"] == "low_ctr" and "title hold ends (15 Dec 2026)" in held["action"]
    later = by_path(pageaudit.audit(counts, {}, [], [], AFTER_HOLD))["/projects/area/wagholi"]
    assert later["bucket"] == "low_ctr" and "hold" not in later["action"]


def test_seen_pages_are_split_by_how_far_they_rank():
    counts = {"/projects/near": {"impressions": 50, "clicks": 0, "position": 12.0},
              "/projects/far": {"impressions": 80, "clicks": 0, "position": 38.0},
              "/projects/few": {"impressions": 5, "clicks": 0, "position": 40.0}}
    rows = by_path(pageaudit.audit(counts, {}, [], [], NOW))
    assert rows["/projects/near"]["bucket"] == "near_page_one"
    assert rows["/projects/far"]["bucket"] == "seen_far"
    assert rows["/projects/few"]["bucket"] == "too_few"


def test_index_state_says_what_to_do_with_a_page_never_shown():
    docs = [doc("/builders/x"), doc("/projects/thin", "NEUTRAL", "Crawled - currently not indexed"),
            doc("/projects/new", "NEUTRAL", "Discovered - currently not indexed"),
            doc("/projects/gone", listed=False)]
    rows = by_path(pageaudit.audit({}, {}, [], docs, NOW))
    assert rows["/builders/x"]["bucket"] == "indexed_silent" and "301" in rows["/builders/x"]["action"]
    assert rows["/projects/thin"]["bucket"] == "not_indexed" and "facts of its own" in rows["/projects/thin"]["action"]
    assert rows["/projects/new"]["bucket"] == "not_indexed" and "Request indexing" in rows["/projects/new"]["action"]
    assert rows["/projects/gone"]["bucket"] == "outside_sitemap"


def test_a_page_taken_out_and_never_indexed_is_left_off_the_audit():
    rows = pageaudit.audit({}, {}, [], [doc("/posts/p", "NEUTRAL", "Discovered - currently not indexed", listed=False)], NOW)
    assert rows == []


def test_no_action_tells_the_owner_to_delete_a_page():
    counts = {f"/projects/p{i}": {"impressions": i * 10, "clicks": i % 2, "position": float(i * 5)} for i in range(12)}
    docs = [doc("/projects/q"), doc("/projects/r", "NEUTRAL", "Crawled - currently not indexed"), doc("/projects/s", listed=False)]
    for r in pageaudit.audit(counts, {}, [], docs, NOW):
        assert "delete" not in r["action"].lower() and "remove" not in r["action"].lower()


def test_each_page_names_the_search_that_shows_it_most():
    queries = [{"query": "godrej ivara", "page": SITE + "/projects/godrej-ivara", "impressions": 40},
               {"query": "godrej ivara price", "page": SITE + "/projects/godrej-ivara", "impressions": 90},
               {"query": "flats in kharadi", "page": SITE + "/projects/area/kharadi/", "impressions": 7}]
    counts = {"/projects/godrej-ivara": {"impressions": 130, "clicks": 4, "position": 5.0},
              "/projects/area/kharadi": {"impressions": 7, "clicks": 0, "position": 30.0}}
    rows = by_path(pageaudit.audit(counts, {}, queries, [], NOW))
    assert (rows["/projects/godrej-ivara"]["top_search"], rows["/projects/godrej-ivara"]["top_search_impressions"]) == ("godrej ivara price", 90)
    assert rows["/projects/area/kharadi"]["top_search"] == "flats in kharadi"


def test_summary_counts_buckets_and_kinds_and_lists_the_most_seen():
    counts = {"/projects/a": {"impressions": 300, "clicks": 9, "position": 4.0},
              "/localities/kharadi": {"impressions": 60, "clicks": 0, "position": 25.0}}
    s = pageaudit.summary(pageaudit.audit(counts, {}, [], [doc("/builders/x")], NOW), top=2)
    assert s["pages"] == 3 and s["by_bucket"]["earning"] == 1 and s["by_bucket"]["seen_far"] == 1
    assert s["by_kind"]["project"]["clicks"] == 9 and list(s["by_kind"])[0] == "project"
    assert [r["path"] for r in s["top"]] == ["/projects/a", "/localities/kharadi"]


async def test_read_joins_search_console_with_the_stored_index_checks(monkeypatch):
    monkeypatch.setenv("GSC_SA_KEY_B64", base64.b64encode(json.dumps(fake_key()).encode()).decode())
    monkeypatch.delenv("GSC_SITE", raising=False)
    bodies = []

    def handler(req):
        if req.url.host == "oauth2.test":
            return httpx.Response(200, json={"access_token": "abc"})
        body = json.loads(req.content)
        bodies.append(body)
        if body["dimensions"] == ["query", "page"]:
            return httpx.Response(200, json={"rows": [{"keys": ["kharadi flats", SITE + "/projects/area/kharadi"], "impressions": 30}]})
        older = body["startDate"] < "2026-10-01"
        return httpx.Response(200, json={"rows": [{"keys": [SITE + "/projects/area/kharadi"], "impressions": 10 if older else 30,
                                                   "clicks": 0 if older else 2, "position": 9.0}]})

    db = FakeDb()
    await db.get_collection(coverage.COLLECTION).insert_one(doc("/builders/x"))
    rows = by_path(await pageaudit.read(Store(db), NOW, httpx.MockTransport(handler)))
    k = rows["/projects/area/kharadi"]
    assert (k["bucket"], k["impressions_before"], k["trend"], k["top_search"]) == ("earning", 10, "rising", "kharadi flats")
    assert rows["/builders/x"]["bucket"] == "indexed_silent"
    assert sorted(b["startDate"] for b in bodies if b["dimensions"] == ["page"]) == ["2026-09-22", "2026-10-20"]


async def test_read_does_nothing_without_search_console(monkeypatch):
    monkeypatch.delenv("GSC_SA_KEY_B64", raising=False)
    assert await pageaudit.read(Store(FakeDb()), NOW) is None


def search_console(calls, fail=False):
    def handler(req):
        if req.url.host == "oauth2.test":
            return httpx.Response(200, json={"access_token": "abc"})
        calls.append(1)
        if fail:
            return httpx.Response(503)
        body = json.loads(req.content)
        if body["dimensions"] == ["query", "page"]:
            return httpx.Response(200, json={"rows": []})
        return httpx.Response(200, json={"rows": [{"keys": [SITE + "/projects/a"], "impressions": 300, "clicks": 9, "position": 4.0}]})
    return httpx.MockTransport(handler)


def keyed(monkeypatch):
    monkeypatch.setenv("GSC_SA_KEY_B64", base64.b64encode(json.dumps(fake_key()).encode()).decode())
    monkeypatch.delenv("GSC_SITE", raising=False)


async def test_studio_reads_google_once_a_day_unless_asked_for_a_fresh_audit(monkeypatch):
    keyed(monkeypatch)
    store, calls = Store(FakeDb()), []
    first = await pageaudit.view(store, NOW, transport=search_console(calls))
    assert first["configured"] and first["pages"] == 1 and first["at"] == NOW.isoformat() and len(calls) == 3
    assert {b["key"]: b["pages"] for b in first["buckets"]}["earning"] == 1 and first["buckets"][1]["label"] == "Earning clicks"
    again = await pageaudit.view(store, NOW + timedelta(hours=5), transport=search_console(calls))
    assert again["at"] == NOW.isoformat() and len(calls) == 3
    fresh = await pageaudit.view(store, NOW + timedelta(hours=5), fresh=True, transport=search_console(calls))
    assert fresh["at"] == (NOW + timedelta(hours=5)).isoformat() and len(calls) == 6
    await pageaudit.view(store, NOW + timedelta(hours=30), transport=search_console(calls))
    assert len(calls) == 9


async def test_a_failed_read_keeps_the_last_audit_and_says_why(monkeypatch):
    keyed(monkeypatch)
    store = Store(FakeDb())
    await pageaudit.view(store, NOW, transport=search_console([]))
    out = await pageaudit.view(store, NOW, fresh=True, transport=search_console([], fail=True))
    assert out["pages"] == 1 and out["at"] == NOW.isoformat() and "Could not read Search Console" in out["error"]


async def test_without_the_key_studio_is_told_the_audit_is_not_set_up(monkeypatch):
    monkeypatch.delenv("GSC_SA_KEY_B64", raising=False)
    out = await pageaudit.view(Store(FakeDb()), NOW)
    assert out["configured"] is False and out["rows"] == []


async def test_the_audit_endpoint_is_owner_only(monkeypatch):
    from types import SimpleNamespace

    from app.core.auth_backend import current_active_user

    from ..newsroom.test_router import setup
    monkeypatch.delenv("GSC_SA_KEY_B64", raising=False)
    monkeypatch.setenv("NEWSROOM_OWNER_IDS", "OWNER")
    c, _ = setup()
    assert c.get("/newsroom/insights/audit").json()["configured"] is False
    c.app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="SOMEONE", is_superuser=False)
    assert c.get("/newsroom/insights/audit").status_code == 403
