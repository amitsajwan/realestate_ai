"""The public news endpoints: approved items only, our wording, no phone numbers, the source link kept for the site to label."""
from datetime import timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.newsroom import public as pub
from app.modules.newsroom.samples import AS_OF, SAMPLES, make_doc
from app.modules.newsroom.store import Store

from ..fakes import FakeDb


def setup():
    store = Store(FakeDb())
    app = FastAPI()
    app.include_router(pub.router, prefix="/public")
    app.dependency_overrides[pub.get_store] = lambda: store
    return TestClient(app), store


async def put(store, doc, status, **extra):
    await store.items.insert_one({**doc, "status": status, "updated_at": AS_OF + timedelta(minutes=len(store.items.docs)), **extra})


async def test_only_approved_scheduled_and_published_items_are_listed():
    c, store = setup()
    for i, status in enumerate(["approved", "scheduled", "published", "pending_review", "drafted", "rejected", "dropped", "failed", "new"]):
        await put(store, {**SAMPLES[0], "_id": f"it{i}"}, status)
    ids = {r["id"] for r in c.get("/public/news").json()}
    assert ids == {"it0", "it1", "it2"}
    for i in (3, 4, 5, 6, 7, 8):
        assert c.get(f"/public/news/it{i}").status_code == 404
    assert c.get("/public/news/it0").status_code == 200 and c.get("/public/news/missing").status_code == 404


async def test_item_shape_headline_summary_source_and_date():
    c, store = setup()
    await put(store, SAMPLES[0], "published", card={"ig": "news/a-ig.jpg", "fb": "news/a1b2c3d4e5-fb.jpg", "variant": "figure"},
              publish={"platform_id": "1", "channels": {"facebook": {"ok": True, "id": "1", "permalink": "https://www.facebook.com/1"},
                                                          "instagram": {"ok": False, "error": "boom"}}})
    r = c.get("/public/news/a1b2c3d4e5").json()
    assert r["headline"] == "Pune Ring Road: ₹10,502 crore approved for the 32 km eastern stretch"
    assert r["source_name"] == "Times of India" and r["as_of"].startswith("2026-09-29")
    assert r["pillar"] == "infrastructure" and [a["slug"] for a in r["areas"]] == ["kharadi", "wagholi"]
    assert r["what_to_check"].startswith("Read the official notice") and r["disclaimer"].startswith("Approvals and project status change")
    assert r["image_url"] == "https://media.test/uploads/news/a1b2c3d4e5-fb.jpg"
    assert r["permalinks"] == [{"channel": "facebook", "url": "https://www.facebook.com/1"}]  # the failed channel has none
    # the summary is the draft text without the link line, the question, the hashtags and the footer
    assert "http" not in r["summary"] and "#" not in r["summary"] and "?" not in r["summary"] and "PUNE Property" not in r["summary"]
    assert r["summary"].startswith("The eastern stretch of the Pune Ring Road")


async def test_google_redirect_is_flagged_not_hidden():
    c, store = setup()
    await put(store, SAMPLES[0], "approved")
    r = c.get("/public/news/a1b2c3d4e5").json()
    assert r["source_is_redirect"] is True and r["source_url"].startswith("https://news.google.com/")
    await put(store, make_doc("zz", "Direct", ["A fact here is true today."], "infrastructure", ["kharadi"], "Hindustan Times")
              | {"raw": {**SAMPLES[0]["raw"], "id": "zz", "url": "https://www.hindustantimes.com/pune/a"}}, "approved")
    assert c.get("/public/news/zz").json()["source_is_redirect"] is False


async def test_no_phone_numbers_anywhere_in_the_response():
    c, store = setup()
    doc = make_doc("ph1", "Call 98765 43210 for the new Kharadi road", ["Reach the office on 020 2612 3456 for the Kharadi road notice."],
                   "infrastructure", ["kharadi"], "PMC 98220 12345")
    doc["draft"]["text"] = "Road notice. Call +91 98765 43210 now.\n\nWhat to check: ask on 020-2612-3456.\n\nSource: PMC, as of 29 Sep 2026. https://x.test/a\n\n#Pune"
    await put(store, doc, "approved")
    body = c.get("/public/news/ph1").text + c.get("/public/news").text
    for digits in ("98765", "43210", "2612", "3456", "98220"):
        assert digits not in body


async def test_list_is_newest_first_and_limited():
    c, store = setup()
    for i in range(5):
        await put(store, {**SAMPLES[0], "_id": f"n{i}"}, "published")
    ids = [r["id"] for r in c.get("/public/news?limit=3").json()]
    assert ids == ["n4", "n3", "n2"]
    assert c.get("/public/news?limit=0").status_code == 200 and len(c.get("/public/news?limit=999").json()) == 5


async def test_digest_item_lists_its_stories_and_tip():
    from app.modules.newsroom import digest
    c, store = setup()
    dg = digest.sample_digest(SAMPLES)
    await put(store, dg, "approved")
    r = c.get(f"/public/news/{dg['_id']}").json()
    assert r["kind"] == "digest" and r["headline"] == "Kharadi and Wagholi this week" and len(r["items"]) == 5
    assert r["items"][0]["id"] and r["tip"].startswith("Ask for the project") and r["source_url"] is None
