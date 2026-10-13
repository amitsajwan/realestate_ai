"""Google index coverage: a daily batch of sitemap pages through URL Inspection, never-checked first, summarised for Admin."""
import base64
import json
from datetime import datetime, timedelta, timezone

import httpx

from app.modules.newsroom.store import Store
from app.modules.seo import coverage, runner

from ..areastats.test_searchconsole import fake_key
from ..fakes import FakeDb

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
URLS = ["https://avasetu.in/", "https://avasetu.in/localities/wagholi", "https://avasetu.in/projects/a", "https://avasetu.in/news/n1"]
STATES = {"/": ("PASS", "Submitted and indexed"), "/localities/wagholi": ("PASS", "Submitted and indexed"),
          "/projects/a": ("NEUTRAL", "Crawled - currently not indexed"), "/news/n1": ("NEUTRAL", "Discovered - currently not indexed")}


def google(seen, urls=URLS, quota_after=None):
    xml = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>"

    def handler(req):
        if req.url.path == "/sitemap.xml":
            return httpx.Response(200, text=xml)
        if req.url.host == "oauth2.test":
            return httpx.Response(200, json={"access_token": "abc"})
        body = json.loads(req.content)
        assert req.headers["Authorization"] == "Bearer abc" and body["siteUrl"] == "sc-domain:avasetu.in"
        if quota_after is not None and len(seen) >= quota_after:
            return httpx.Response(429)
        seen.append(body["inspectionUrl"])
        verdict, state = STATES[httpx.URL(body["inspectionUrl"]).path]
        return httpx.Response(200, json={"inspectionResult": {"indexStatusResult": {"verdict": verdict, "coverageState": state}}})
    return httpx.MockTransport(handler)


def configured(monkeypatch):
    monkeypatch.setenv("GSC_SA_KEY_B64", base64.b64encode(json.dumps(fake_key()).encode()).decode())
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://avasetu.in")
    monkeypatch.delenv("INDEXNOW_SITEMAP_URL", raising=False)
    monkeypatch.delenv("GSC_SITE", raising=False)
    return Store(FakeDb())


async def test_does_nothing_without_search_console(monkeypatch):
    monkeypatch.delenv("GSC_SA_KEY_B64", raising=False)
    assert await coverage.run_once(Store(FakeDb()), NOW) is None


async def test_inspects_the_sitemap_and_says_why_pages_are_not_indexed(monkeypatch):
    store, seen = configured(monkeypatch), []
    assert await coverage.run_once(store, NOW, google(seen)) == {"checked": 4, "indexed": 2, "inspected": 4, "sitemap": 4}
    mark = await store.get_mark(coverage.MARK)
    assert mark["missing_by_state"] == {"Crawled - currently not indexed": 1, "Discovered - currently not indexed": 1}
    assert [m["url"] for m in mark["not_indexed"]] == ["https://avasetu.in/news/n1", "https://avasetu.in/projects/a"]
    assert await coverage.run_once(store, NOW + timedelta(hours=3), google(seen)) is None   # once a day


async def test_a_daily_batch_takes_never_checked_pages_first_then_the_oldest(monkeypatch):
    store, seen = configured(monkeypatch), []
    monkeypatch.setattr(coverage, "PER_DAY", 3)
    await coverage.run_once(store, NOW, google(seen))
    assert seen == URLS[:3]
    seen.clear()
    await coverage.run_once(store, NOW + timedelta(days=1), google(seen))
    assert seen == [URLS[3], URLS[0], URLS[1]]


async def test_the_quota_stops_the_batch_but_keeps_what_was_read(monkeypatch):
    store, seen = configured(monkeypatch), []
    out = await coverage.run_once(store, NOW, google(seen, quota_after=2))
    assert out == {"checked": 2, "indexed": 2, "inspected": 2, "sitemap": 4}


async def test_pages_dropped_from_the_sitemap_are_not_counted(monkeypatch):
    store, seen = configured(monkeypatch), []
    await coverage.run_once(store, NOW, google(seen))
    out = await coverage.run_once(store, NOW + timedelta(days=1), google(seen, urls=URLS[:2]))
    assert (out["inspected"], out["indexed"], out["sitemap"]) == (2, 2, 2)


async def test_the_loop_runs_both_steps_and_one_failing_does_not_stop_the_other(monkeypatch):
    calls = []

    async def boom(store, now):
        calls.append("indexnow")
        raise RuntimeError("down")

    async def fine(store, now):
        calls.append("coverage")
        return {"checked": 1}
    monkeypatch.setattr(runner.indexnow, "run_once", boom)
    monkeypatch.setattr(runner.coverage, "run_once", fine)
    assert await runner.round_once(Store(FakeDb()), NOW) == {"indexnow": {"error": "RuntimeError"}, "coverage": {"checked": 1}}
    assert calls == ["indexnow", "coverage"]
