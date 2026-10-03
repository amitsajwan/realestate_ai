"""T1.3 'New on MahaRERA': one click turns the register's last 30 days into a carousel and a Facebook post, queued for review."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.newsroom import captions, cards, codec, roundup
from app.modules.newsroom import adapters
from app.modules.newsroom import router as nr
from app.modules.newsroom.stages.check import check
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 3, 6, 0, tzinfo=timezone.utc)  # 11:30 IST


def proj(n, name, locality="kharadi", last_modified="2026-09-24", pincode="411014"):
    return {"_id": f"PR12600026016{n:02d}", "regno": f"PR12600026016{n:02d}", "name": name, "promoter": "", "locality": locality,
            "pincode": pincode, "last_modified": last_modified, "source": "MahaRERA",
            "source_url": f"https://maharerait.maharashtra.gov.in/public/project/view/{n}", "news": []}


PROJECTS = [
    proj(1, "SHANTISHIKHAR", last_modified="2026-09-27"),
    proj(2, "Belmont Skyone", "wagholi", "2026-09-24", "412207"),
    proj(3, "The Element", "upper_kharadi", "2026-10-01"),
    proj(4, "VENKATESH VANAYA - WING – N (MHADA)- PHASE - 8", last_modified="2026-09-03"),  # 30 days before 3 Oct IST: in
    proj(5, "NEOWORLD", "wagholi", "2026-09-02", "412207"),  # 31 days: out
    proj(6, "Mantra Kharadi Phase 3", last_modified=""),  # no date: never claimed as recent
]


def test_pick_last_30_days_newest_first():
    assert [p["name"] for p in roundup.pick(PROJECTS, NOW)] == [
        "The Element", "SHANTISHIKHAR", "Belmont Skyone", "VENKATESH VANAYA - WING – N (MHADA)- PHASE - 8"]


def test_nothing_in_window_gives_none():
    assert roundup.compose([PROJECTS[4], PROJECTS[5]], NOW, "x") is None


def test_text_states_facts_only_and_passes_the_check():
    doc = roundup.compose(PROJECTS, NOW, "maharera-x")
    text = doc["draft"]["text"]
    assert text.startswith("4 projects in Kharadi and Wagholi were listed or updated on MahaRERA in the last 30 days.")
    for p in roundup.pick(PROJECTS, NOW):
        assert p["name"] in text and p["_id"] in text
    assert "last updated 1 Oct 2026" in text and "Source: MahaRERA, as of 3 Oct 2026." in text
    assert "NEOWORLD" not in text and "Mantra" not in text
    low = text.lower()
    for word in ("new launch", "newly", "launched", "just registered", "best", "price"):
        assert word not in low
    res = check(codec.draft(doc), codec.facts(doc), codec.raw_item(doc))
    assert res.ok, res.problems
    assert doc["status"] == "pending_review" and doc["relevance"]["pillar"] == "new_supply"
    assert doc["relevance"]["areas"] == ["upper_kharadi", "kharadi", "wagholi"]


def test_captions_link_to_the_area_pages():
    doc = roundup.compose(PROJECTS, NOW, "maharera-x")
    out = captions.build(doc)
    assert "https://site.test/localities" in out["facebook"] and "#MahaRERA" in out["facebook"]
    assert "link in our bio" in out["instagram"] and "https://" not in out["instagram"].split("#")[0].replace("https://site.test", "")


def test_carousel_cover_projects_check_closing():
    doc = roundup.compose(PROJECTS, NOW, "maharera-x")
    ig = cards.digest_slides(doc["digest"], "ig")
    fb = cards.digest_slides(doc["digest"], "fb")
    assert len(ig) == 1 + 4 + 2 and len(fb) == 1
    assert doc["digest"]["title"] == "Listed or updated on MahaRERA"
    assert doc["digest"]["cover_line"] == "4 projects, with their registration numbers"


def test_more_than_eight_projects_show_eight_slides_and_list_all():
    many = [proj(10 + i, f"Tower Group {chr(65 + i)} Residency", last_modified=f"2026-09-{10 + i:02d}") for i in range(11)]
    doc = roundup.compose(many, NOW, "maharera-x")
    assert len(doc["digest"]["items"]) == roundup.MAX_SLIDES
    assert doc["digest"]["cover_line"].endswith("(first 7 here)")
    assert all(p["name"] in doc["draft"]["text"] for p in many)
    assert len(cards.digest_slides(doc["digest"], "ig")) == 10  # Instagram's limit


async def seeded():
    store = Store(FakeDb())
    for p in PROJECTS:
        await store.projects.insert_one(dict(p))
    return store


async def test_build_queues_one_roundup_and_a_second_click_returns_it():
    store = await seeded()
    first = await roundup.build(store, NOW)
    assert first["created"] and (await store.get(first["doc"]["_id"]))["status"] == "pending_review"
    again = await roundup.build(store, NOW + timedelta(minutes=1))
    assert not again["created"] and again["doc"]["_id"] == first["doc"]["_id"]
    await store.move(first["doc"]["_id"], "rejected", "owner said no")
    third = await roundup.build(store, NOW + timedelta(minutes=2))
    assert third["created"] and third["doc"]["_id"] != first["doc"]["_id"]


async def test_build_with_nothing_to_post():
    with pytest.raises(roundup.NothingToPost):
        await roundup.build(Store(FakeDb()), NOW)


async def test_build_refuses_text_that_fails_the_check():
    store = await seeded()

    def strict(d, f, r):
        return SimpleNamespace(ok=False, problems=["nope"])
    with pytest.raises(ValueError):
        await roundup.build(store, NOW, checker=strict)
    assert await store.items.count_documents({}) == 0


# --- the one-click endpoint ---------------------------------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("NEWSROOM_OWNER_IDS", "OWNER")
    drawn = []

    async def fake_cards(doc):
        drawn.append(doc["_id"])
        return {"ig": [f"news/{doc['_id']}-ig-{i}.jpg" for i in range(1, 8)], "fb": f"news/{doc['_id']}-fb.jpg", "variant": "digest"}
    monkeypatch.setattr(adapters, "card_stage", fake_cards)
    store = Store(FakeDb())
    app = FastAPI()
    app.include_router(nr.router, prefix="/newsroom")
    app.dependency_overrides[nr.get_store] = lambda: store
    app.dependency_overrides[nr.get_checker] = lambda: check
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="OWNER", is_superuser=False)
    return TestClient(app), store, drawn


async def test_endpoint_makes_carousel_and_post_for_review(client):
    c, store, drawn = client
    assert c.post("/newsroom/maharera-roundup").status_code == 404  # empty register
    for p in PROJECTS:
        await store.projects.insert_one(dict(p))
    r = c.post("/newsroom/maharera-roundup")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] is True and body["projects"] >= 1 and drawn == [body["id"]]
    q = c.get("/newsroom/queue").json()
    item = next(i for i in q if i["id"] == body["id"])
    assert len(item["card"]["slides"]) == 7 and item["captions"]["facebook"]
    assert c.post("/newsroom/maharera-roundup").json() == {**body, "created": False}


def test_link_follows_the_site_address(monkeypatch):
    doc = roundup.compose(PROJECTS, NOW, "maharera-x")
    assert doc["digest"]["link"] == "/localities"
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://new.test")
    assert "Read more: https://new.test/localities" in captions.build(doc)["facebook"]


async def test_captions_pass_the_check_with_our_own_name_in_the_footer():
    doc = roundup.compose(PROJECTS, NOW, "maharera-x")
    assert await captions.verify(doc, check) == {"facebook": [], "instagram": []}
