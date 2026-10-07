"""Final captions (what the owner sees and what is sent) and the owner endpoints' preview fields."""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.newsroom import captions
from app.modules.newsroom import presentation as pr
from app.modules.newsroom import router as nr
from app.modules.newsroom.samples import SAMPLES, make_doc
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import CheckResult

from ..fakes import FakeDb
from .helpers import NOW


def test_facebook_caption_has_our_link_never_the_source_link_and_the_footer():
    for d in SAMPLES:
        fb = captions.build(d)["facebook"]
        assert f"Read more: https://site.test/news/{d['_id']}" in fb and "news.google.com" not in fb and fb.endswith("Avasetu · https://site.test")
        assert f"as of {pr.as_of_label(d)}" in fb and "Source: " in fb and len(fb) < 900 and "?" in fb


def test_instagram_caption_has_no_url_a_bio_line_max_eight_hashtags_and_the_footer():
    for d in SAMPLES:
        ig = captions.build(d)["instagram"]
        assert "http" not in ig and "www." not in ig and ".sslip.io" not in ig
        assert "link in our bio" in ig and ig.endswith("Avasetu · link in our bio") and len(ig) < 900
        assert len([w for w in ig.split() if w.startswith("#")]) <= 8


def test_captions_follow_the_brand_voice_and_carry_no_phone_numbers():
    d = make_doc("ph", "Road update", ["The road work starts. Call 98765 43210."], "infrastructure", ["kharadi"], "PMC")
    for text in captions.build(d).values():
        assert "98765" not in text and "43210" not in text
    assert "https://site.test" in captions.build(d)["facebook"]  # the site address is not mistaken for a phone number


def test_a_long_draft_is_trimmed_in_order_and_the_footer_and_link_survive():
    long = make_doc("lg", "Big update", ["Fact one is here. " * 40], "infrastructure", ["kharadi"], "PMC")
    long["draft"]["text"] = ("Sentence number one is quite long and says a lot. " * 30) + "\n\nSource: PMC, as of 29 Sep 2026. https://x.test\n\n#Pune"
    for ch, text in captions.build(long).items():
        assert len(text) < 900 and text.endswith(captions.footer(ch)) and "Read more:" in text


def test_edited_text_flows_into_the_captions():
    d = {**SAMPLES[0], "draft": {**SAMPLES[0]["draft"], "text": "Our own edited line about the ring road. What do you think?"}}
    assert captions.build(d)["facebook"].startswith("Our own edited line about the ring road.")


async def test_verify_runs_the_checker_over_each_final_caption():
    seen = []

    def checker(d, f, r):
        seen.append(d.text)
        return CheckResult(ok="Instagram" not in d.text and "https://" in d.text, problems=["no link"])
    out = await captions.verify(SAMPLES[0], checker)
    assert len(seen) == 2 and out["facebook"] == [] and out["instagram"] == ["no link"]
    assert await captions.verify(SAMPLES[0], None) == {"facebook": [], "instagram": []}


# ---- the owner endpoints --------------------------------------------------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("NEWSROOM_OWNER_IDS", "OWNER")
    store = Store(FakeDb())
    state = {"checker": None}
    app = FastAPI()
    app.include_router(nr.router, prefix="/newsroom")
    app.dependency_overrides[nr.get_store] = lambda: store
    app.dependency_overrides[nr.get_checker] = lambda: state["checker"]
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="OWNER", is_superuser=False)
    return TestClient(app), store, state


async def pending(store, doc=None):
    d = {**(doc or SAMPLES[0]), "status": "pending_review", "created_at": NOW}
    await store.items.insert_one(d)
    return d["_id"]


async def test_queue_shows_card_channels_and_exact_captions(client, monkeypatch):
    c, store, _ = client
    monkeypatch.setenv("META_IG_BUSINESS_ID", "456")
    await pending(store)
    q = c.get("/newsroom/queue").json()[0]
    assert q["card"]["fb"] == "https://media.test/uploads/news/a1b2c3d4e5-fb.jpg" and q["card"]["ig"].endswith("a1b2c3d4e5-ig.jpg")
    assert [x["id"] for x in q["channels"]] == ["facebook", "instagram"]
    assert q["captions"]["facebook"] == captions.build(SAMPLES[0])["facebook"] and "http" not in q["captions"]["instagram"]
    assert q["caption_problems"] == {} and q["dry_run"] is True
    assert (await store.get("a1b2c3d4e5"))["card"]["variant"] == "figure"  # drawn on demand and stored


async def test_instagram_is_not_listed_until_it_is_configured(client):
    c, store, _ = client
    await pending(store)
    q = c.get("/newsroom/queue").json()[0]
    assert [x["id"] for x in q["channels"]] == ["facebook"] and list(q["captions"]) == ["facebook"]


async def test_caption_problems_are_shown_per_channel(client, monkeypatch):
    c, store, state = client
    monkeypatch.setenv("META_IG_BUSINESS_ID", "456")
    state["checker"] = lambda d, f, r: CheckResult(ok="https://" in d.text, problems=["Missing link"])
    await pending(store)
    assert c.get("/newsroom/queue").json()[0]["caption_problems"] == {"instagram": ["Missing link"]}


async def test_preview_endpoint_rebuilds_captions_for_edited_text_without_saving(client, monkeypatch):
    c, store, _ = client
    monkeypatch.setenv("META_IG_BUSINESS_ID", "456")
    id_ = await pending(store)
    r = c.post(f"/newsroom/items/{id_}/preview", json={"text": "A brand new first line. What do you think?"}).json()
    assert r["captions"]["facebook"].startswith("A brand new first line.") and "http" not in r["captions"]["instagram"]
    assert (await store.get(id_))["draft"]["text"] == SAMPLES[0]["draft"]["text"]
    assert c.post("/newsroom/items/nope/preview", json={}).status_code == 404


async def test_preview_is_owner_only_and_pending_only(client):
    c, store, _ = client
    await store.items.insert_one({**SAMPLES[1], "status": "approved", "created_at": NOW})
    assert c.post(f"/newsroom/items/{SAMPLES[1]['_id']}/preview", json={}).status_code == 409
