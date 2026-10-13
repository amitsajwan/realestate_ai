"""Search Console impressions reach the project records, so enrichment starts with the pages Google shows."""
import base64
import json
from datetime import datetime, timedelta, timezone

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.modules.areastats import pages, searchconsole

from .test_pages import FULL, seeded

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)


def fake_key():
    pem = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    return {"client_email": "sa@x.iam.gserviceaccount.com", "private_key": pem, "token_uri": "https://oauth2.test/token"}


def google(seen):
    def handler(req):
        if req.url.host == "oauth2.test":
            seen.append("token")
            return httpx.Response(200, json={"access_token": "abc"})
        body = json.loads(req.content)
        seen.append(body)
        assert req.headers["Authorization"] == "Bearer abc" and "sc-domain%3Aavasetu.in" in str(req.url)
        if body["dimensions"] == ["query", "page"]:
            return httpx.Response(200, json={"rows": [
                {"keys": ["rohan abhilasha 4 possession date", "https://avasetu.in/projects/rohan-abhilasha-4-wagholi"],
                 "impressions": 30, "clicks": 2, "position": 7.5},
                {"keys": ["Rohan Abhilasha 4 possession date?", "https://avasetu.in/localities/wagholi"], "impressions": 10,
                 "clicks": 0, "position": 11.5},
                {"keys": ["new projects in wagholi", "https://avasetu.in/localities/wagholi"], "impressions": 400, "clicks": 9,
                 "position": 14.0}]})
        return httpx.Response(200, json={"rows": [
            {"keys": ["https://avasetu.in/projects/rohan-abhilasha-4-wagholi"], "impressions": 40, "clicks": 3},
            {"keys": ["https://avasetu.in/localities/wagholi"], "impressions": 500, "clicks": 20}]})
    return httpx.MockTransport(handler)


async def test_does_nothing_without_a_key(monkeypatch):
    monkeypatch.delenv("GSC_SA_KEY_B64", raising=False)
    db, store = await seeded(("P1", "Rohan Abhilasha 4", "wagholi", FULL))
    assert await searchconsole.refresh(store, NOW) is None


async def test_impressions_land_on_project_records_once_a_day(monkeypatch):
    monkeypatch.setenv("GSC_SA_KEY_B64", base64.b64encode(json.dumps(fake_key()).encode()).decode())
    db, store = await seeded(("P1", "Rohan Abhilasha 4", "wagholi", FULL), ("P2", "Other", "wagholi", FULL))
    await pages.assign_all(store)
    seen = []
    out = await searchconsole.refresh(store, NOW, transport=google(seen))
    assert out == {"pages": 2, "projects": 1, "phrases": 2} and seen[0] == "token" and seen[1]["dimensions"] == ["page"]
    p1 = await store.project("P1")
    assert (p1["gsc_impressions"], p1["gsc_clicks"]) == (40, 3) and "gsc_impressions" not in await store.project("P2")
    assert await searchconsole.refresh(store, NOW + timedelta(hours=3), transport=google(seen)) is None   # once a day


async def test_impressions_keep_a_history_and_the_28_days_before(monkeypatch):
    monkeypatch.setenv("GSC_SA_KEY_B64", base64.b64encode(json.dumps(fake_key()).encode()).decode())
    db, store = await seeded(("P1", "Rohan Abhilasha 4", "wagholi", FULL))
    await pages.assign_all(store)
    await store.set_project("P1", gsc_history=[{"at": NOW - timedelta(days=30), "impressions": 10},
                                               {"at": NOW - timedelta(days=1), "impressions": 35}])
    await searchconsole.refresh(store, NOW, transport=google([]))
    p1 = await store.project("P1")
    assert p1["gsc_impressions_prev"] == 10 and p1["gsc_history"][-1] == {"at": NOW, "impressions": 40}


async def test_the_searches_behind_our_pages_become_phrases(monkeypatch):
    from app.modules.areastats import demand
    monkeypatch.setenv("GSC_SA_KEY_B64", base64.b64encode(json.dumps(fake_key()).encode()).decode())
    db, store = await seeded(("P1", "Rohan Abhilasha 4", "wagholi", FULL))
    await searchconsole.refresh(store, NOW, transport=google([]))
    top = await demand.top(store)
    assert [t["phrase"] for t in top] == ["new projects in wagholi", "rohan abhilasha 4 possession date"]
    area, project = top
    assert area["kind"] == "area" and area["area"] == "wagholi" and area["gsc"]["impressions"] == 400
    # the same search on two pages, spelt two ways, is one phrase: impressions add up, position is the impression-weighted mean
    assert project["kind"] == "project" and project["regno"] == "P1" and project["gsc"]["impressions"] == 40
    assert project["gsc"]["position"] == 8.5 and project["gsc"]["pages"] == ["/localities/wagholi", "/projects/rohan-abhilasha-4-wagholi"]
