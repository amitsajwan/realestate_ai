"""IndexNow gets every page once, then only the pages changed since the last send; nothing without a key."""
import json
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.newsroom.store import Store
from app.modules.seo import indexnow
from app.modules.seo.router import public_router

from ..fakes import FakeDb

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
KEY = "a1b2c3d4e5f6a7b8"


def sitemap(*entries):
    rows = "".join(f"<url><loc>{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>" for u, d in entries)
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>'


def engines(xml, sent, status=200):
    def handler(req):
        if req.url.path == "/sitemap.xml":
            return httpx.Response(200, text=xml)
        assert str(req.url) == indexnow.ENDPOINT
        sent.append(json.loads(req.content))
        return httpx.Response(status)
    return httpx.MockTransport(handler)


def configured(monkeypatch):
    monkeypatch.setenv("INDEXNOW_KEY", KEY)
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://avasetu.in/")
    monkeypatch.delenv("INDEXNOW_SITEMAP_URL", raising=False)
    return Store(FakeDb())


XML = sitemap(("https://avasetu.in/", None),
              ("https://avasetu.in/news/n1", "2026-10-12T08:30:00.000Z"),
              ("https://avasetu.in/projects/old", "2026-09-01T00:00:00.000Z"),
              ("https://other.example/x", "2026-10-12T08:30:00.000Z"))


async def test_does_nothing_without_a_key(monkeypatch):
    monkeypatch.delenv("INDEXNOW_KEY", raising=False)
    assert await indexnow.run_once(Store(FakeDb()), NOW) is None


async def test_a_malformed_key_counts_as_off(monkeypatch):
    monkeypatch.setenv("INDEXNOW_KEY", "has spaces!")
    assert indexnow.key() is None


async def test_first_round_sends_every_page_of_ours_then_only_changed_ones(monkeypatch):
    store, sent = configured(monkeypatch), []
    assert await indexnow.run_once(store, NOW, engines(XML, sent)) == {"sent": 3, "status": 200}
    assert sent[0] == {"host": "avasetu.in", "key": KEY, "keyLocation": "https://avasetu.in/indexnow-key.txt",
                       "urlList": ["https://avasetu.in/", "https://avasetu.in/news/n1", "https://avasetu.in/projects/old"]}
    later = sitemap(("https://avasetu.in/", None), ("https://avasetu.in/news/n1", "2026-10-12T08:30:00.000Z"),
                    ("https://avasetu.in/news/n2", "2026-10-12T09:40:00+00:00"), ("https://avasetu.in/projects/old", "2026-09-01"))
    assert await indexnow.run_once(store, NOW + timedelta(minutes=30), engines(later, sent)) == {"sent": 2, "status": 200}
    assert sent[1]["urlList"] == ["https://avasetu.in/news/n1", "https://avasetu.in/news/n2"]   # n1 is inside the hour of slack


async def test_nothing_changed_sends_nothing(monkeypatch):
    store, sent = configured(monkeypatch), []
    await indexnow.run_once(store, NOW, engines(XML, sent))
    await indexnow.run_once(store, NOW + timedelta(minutes=30), engines(XML, sent))   # n1 once more: inside the slack
    assert await indexnow.run_once(store, NOW + timedelta(days=1), engines(XML, sent)) == {"sent": 0, "status": 200}
    assert len(sent) == 2


async def test_a_refused_send_is_tried_again_with_the_same_pages(monkeypatch):
    store, sent = configured(monkeypatch), []
    assert await indexnow.run_once(store, NOW, engines(XML, sent, status=403)) == {"sent": 0, "status": 403}
    assert await indexnow.run_once(store, NOW + timedelta(minutes=30), engines(XML, sent)) == {"sent": 3, "status": 200}


def test_the_key_is_served_as_text_only_when_set(monkeypatch):
    app = FastAPI()
    app.include_router(public_router, prefix="/api/v1/public")
    client = TestClient(app)
    monkeypatch.delenv("INDEXNOW_KEY", raising=False)
    assert client.get("/api/v1/public/indexnow-key").status_code == 404
    monkeypatch.setenv("INDEXNOW_KEY", KEY)
    r = client.get("/api/v1/public/indexnow-key")
    assert r.status_code == 200 and r.text == KEY and r.headers["content-type"].startswith("text/plain")
