"""Area photos (docs/plan/area-pictures.md step 4): only live photos reach the guide, each with who took it and when, and a
free-licensed one only with its licence and link. Agents upload; only the owner publishes, hides and orders."""
import io
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.core.auth_backend import current_active_user, get_user_manager
from app.modules.areaphotos import router as ar
from app.modules.areaphotos.service import AreaPhotos, PhotoRefused, check_facts
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 17, 6, 0, tzinfo=timezone.utc)
TODAY = NOW.date()
OWNER = SimpleNamespace(id="OWNER", is_superuser=True)
AGENT = SimpleNamespace(id="agent1", is_superuser=False)
OTHER = SimpleNamespace(id="agent2", is_superuser=False)

OWN = {"caption": "Kharadi bypass road at the EON IT Park signal", "taken_on": "2026-11-10", "credit": "Rohan Kulkarni",
       "kind": "own"}
LICENSED = {"caption": "Ramwadi metro station, Aqua Line", "taken_on": "2024-03-02", "credit": "Jane Doe", "kind": "licensed",
            "licence": "CC BY-SA 4.0", "source_url": "https://commons.wikimedia.org/wiki/File:Ramwadi_metro.jpg"}


def jpeg(w=1200, h=800, color=(90, 120, 160)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (w, h), color).save(out, "JPEG")
    return out.getvalue()


def service(db=None, tmp_path=None) -> AreaPhotos:
    return AreaPhotos(db or FakeDb(), now=lambda: NOW, root=tmp_path)


def client(user, db, tmp_path):
    app = FastAPI()
    app.include_router(ar.router, prefix="/area-photos")
    app.include_router(ar.public_router, prefix="/public")
    app.dependency_overrides[ar.get_service] = lambda: service(db, tmp_path)
    app.dependency_overrides[current_active_user] = lambda: user
    return TestClient(app)


def upload(c, area="kharadi", facts=OWN, body=None, ctype="image/jpeg"):
    return c.post("/area-photos", data={"area": area, **facts}, files={"file": ("p.jpg", body or jpeg(), ctype)})


# ---- the rules -----------------------------------------------------------------------------------------------------------
def test_a_licensed_photo_without_its_licence_or_link_is_refused():
    with pytest.raises(PhotoRefused, match="licence"):
        check_facts({**LICENSED, "licence": ""}, TODAY)
    with pytest.raises(PhotoRefused, match="licence"):
        check_facts({**LICENSED, "licence": "CC BY-NC 4.0"}, TODAY)   # non-commercial is not free for us
    with pytest.raises(PhotoRefused, match="link"):
        check_facts({**LICENSED, "source_url": ""}, TODAY)
    with pytest.raises(PhotoRefused, match="link"):
        check_facts({**LICENSED, "source_url": "http://commons.wikimedia.org/wiki/File:x.jpg"}, TODAY)
    assert check_facts(LICENSED, TODAY)["licence"] == "CC BY-SA 4.0"


def test_an_own_photo_needs_a_caption_a_credit_and_a_past_date_and_carries_no_licence():
    with pytest.raises(PhotoRefused, match="caption"):
        check_facts({**OWN, "caption": "road"}, TODAY)
    with pytest.raises(PhotoRefused, match="caption"):
        check_facts({**OWN, "caption": "x" * 161}, TODAY)
    with pytest.raises(PhotoRefused, match="who took"):
        check_facts({**OWN, "credit": "  "}, TODAY)
    with pytest.raises(PhotoRefused, match="future"):
        check_facts({**OWN, "taken_on": "2026-11-18"}, TODAY)
    with pytest.raises(PhotoRefused, match="date"):
        check_facts({**OWN, "taken_on": "last week"}, TODAY)
    with pytest.raises(PhotoRefused, match="whose photo"):
        check_facts({**OWN, "kind": "ai"}, TODAY)
    clean = check_facts({**OWN, "licence": "CC0", "source_url": "https://x.in/a"}, TODAY)
    assert clean["licence"] is None and clean["source_url"] is None


# ---- the service ---------------------------------------------------------------------------------------------------------
async def test_an_upload_waits_as_pending_and_is_kept_sized_without_its_exif(tmp_path):
    svc = service(tmp_path=tmp_path)
    d = await svc.add("kharadi", OWN, jpeg(3000, 2000), "image/jpeg", "agent1")
    assert d["status"] == "pending" and d["area"] == "kharadi" and d["created_by"] == "agent1" and d["created_at"] == NOW
    assert d["image"]["url"] == f"/uploads/area_photos/kharadi/{d['_id']}.webp"
    assert (d["image"]["width"], d["image"]["height"]) == (1600, 1067)
    small = Image.open(tmp_path / "area_photos" / "kharadi" / f"{d['_id']}-small.webp")
    assert max(small.size) == 640 and not small.info.get("exif")


async def test_a_file_that_is_not_a_photo_or_too_small_or_too_large_is_refused(tmp_path):
    svc = service(tmp_path=tmp_path)
    for body, ctype, status in ((jpeg(), "image/gif", 400), (b"not an image", "image/jpeg", 400), (jpeg(600, 400), "image/jpeg", 400),
                                (b"x" * (10 * 1024 * 1024 + 1), "image/jpeg", 413)):
        with pytest.raises(PhotoRefused) as e:
            await svc.add("kharadi", OWN, body, ctype, "agent1")
        assert e.value.status_code == status
    with pytest.raises(PhotoRefused) as e:
        await svc.add("magarpatta", OWN, jpeg(), "image/jpeg", "agent1")
    assert e.value.status_code == 404
    assert not list(tmp_path.rglob("*.webp"))


async def test_only_live_photos_are_public_and_hiding_takes_one_off(tmp_path):
    svc = service(tmp_path=tmp_path)
    a = await svc.add("kharadi", OWN, jpeg(), "image/jpeg", "agent1")
    b = await svc.add("kharadi", LICENSED, jpeg(), "image/jpeg", "agent1")
    await svc.add("wagholi", OWN, jpeg(), "image/jpeg", "agent1")
    assert (await svc.public("kharadi"))["photos"] == []
    await svc.set_status(a["_id"], "live", "OWNER")
    await svc.set_status(b["_id"], "live", "OWNER")
    out = await svc.public("kharadi")
    assert out["area"] == {"key": "kharadi", "name": "Kharadi", "slug": "kharadi"}
    assert [p["id"] for p in out["photos"]] == [b["_id"], a["_id"]]   # the newest upload first until the owner reorders
    lic = out["photos"][0]
    assert lic["credit"] == "Jane Doe" and lic["taken_on"] == "2024-03-02" and lic["licence"] == "CC BY-SA 4.0"
    assert lic["licence_url"] == "https://creativecommons.org/licenses/by-sa/4.0/"
    assert lic["source_url"] == LICENSED["source_url"]
    assert "status" not in lic and "created_by" not in lic
    await svc.set_status(b["_id"], "hidden", "OWNER")
    assert [p["id"] for p in (await svc.public("kharadi"))["photos"]] == [a["_id"]]
    assert await svc.public("magarpatta") is None


async def test_the_owner_orders_an_areas_photos(tmp_path):
    svc = service(tmp_path=tmp_path)
    ids = [(await svc.add("wakad", {**OWN, "caption": f"Wakad photo number {i}"}, jpeg(), "image/jpeg", "agent1"))["_id"]
           for i in range(3)]
    for i in ids:
        await svc.set_status(i, "live", "OWNER")
    assert [p["id"] for p in (await svc.public("wakad"))["photos"]] == ids[::-1]
    await svc.reorder("wakad", [ids[1], ids[0]], "OWNER")
    assert [p["id"] for p in (await svc.public("wakad"))["photos"]] == [ids[1], ids[0], ids[2]]
    with pytest.raises(PhotoRefused):
        await svc.reorder("wakad", [ids[0], "someone-elses"], "OWNER")


async def test_an_agent_edits_only_his_own_photo_while_it_waits(tmp_path):
    svc = service(tmp_path=tmp_path)
    d = await svc.add("baner", OWN, jpeg(), "image/jpeg", "agent1")
    assert (await svc.edit(d["_id"], {"caption": "Baner road near Balewadi High Street"}, "agent1", False))["caption"] \
        == "Baner road near Balewadi High Street"
    with pytest.raises(PhotoRefused) as e:
        await svc.edit(d["_id"], {"credit": "Me"}, "agent2", False)
    assert e.value.status_code == 403
    await svc.set_status(d["_id"], "live", "OWNER")
    with pytest.raises(PhotoRefused):
        await svc.edit(d["_id"], {"credit": "Me"}, "agent1", False)
    assert (await svc.edit(d["_id"], {"credit": "Avasetu team"}, "OWNER", True))["status"] == "live"
    with pytest.raises(PhotoRefused, match="licence"):
        await svc.edit(d["_id"], {"kind": "licensed"}, "OWNER", True)


async def test_uploads_per_person_per_day_are_capped(tmp_path):
    db = FakeDb()
    for i in range(40):
        await db.area_photos.insert_one({"_id": f"p{i}", "area": "lohegaon", "created_by": "agent1",
                                         "created_at": NOW - timedelta(hours=1), "order": i})
    with pytest.raises(PhotoRefused) as e:
        await service(db, tmp_path).add("kharadi", OWN, jpeg(), "image/jpeg", "agent1")
    assert e.value.status_code == 429
    assert (await service(db, tmp_path).add("kharadi", OWN, jpeg(), "image/jpeg", "agent2"))["status"] == "pending"


# ---- the routes ----------------------------------------------------------------------------------------------------------
def test_an_agent_uploads_but_cannot_publish_hide_or_reorder(tmp_path):
    db = FakeDb()
    c = client(AGENT, db, tmp_path)
    r = upload(c)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "pending" and body["mine"] and body["can_edit"] and body["url"].startswith("/uploads/area_photos/")
    pid = body["id"]
    assert c.post(f"/area-photos/{pid}/publish").status_code == 403
    assert c.post(f"/area-photos/{pid}/hide").status_code == 403
    assert c.put("/area-photos/order", json={"area": "kharadi", "ids": [pid]}).status_code == 403
    listed = c.get("/area-photos", params={"area": "kharadi"}).json()
    assert listed["can_publish"] is False and [i["id"] for i in listed["items"]] == [pid]
    assert c.get("/public/areas/kharadi/photos").json()["photos"] == []


def test_the_owner_publishes_and_the_public_route_shows_it_with_its_credit(tmp_path):
    db = FakeDb()
    pid = upload(client(AGENT, db, tmp_path), facts=LICENSED).json()["id"]
    owner = client(OWNER, db, tmp_path)
    assert owner.get("/area-photos", params={"area": "kharadi"}).json()["can_publish"] is True
    r = owner.post(f"/area-photos/{pid}/publish")
    assert r.status_code == 200 and r.json()["status"] == "live"
    pub = owner.get("/public/areas/kharadi/photos")
    assert pub.status_code == 200 and pub.headers["cache-control"] == "public, max-age=300"
    [p] = pub.json()["photos"]
    assert {k: p[k] for k in ("caption", "credit", "taken_on", "kind", "licence", "source_url")} == {
        k: LICENSED[k] for k in ("caption", "credit", "taken_on", "kind", "licence", "source_url")}
    assert owner.post(f"/area-photos/{pid}/hide").json()["status"] == "hidden"
    assert owner.get("/public/areas/kharadi/photos").json()["photos"] == []
    assert owner.get("/public/areas/nowhere/photos").status_code == 404


def test_the_upload_route_refuses_a_licensed_photo_without_a_link_and_an_unknown_area(tmp_path):
    c = client(AGENT, FakeDb(), tmp_path)
    r = upload(c, facts={**LICENSED, "source_url": ""})
    assert r.status_code == 422 and "link" in r.json()["detail"]
    assert upload(c, area="nowhere").status_code == 404
    assert c.get("/area-photos", params={"area": "nowhere"}).status_code == 404
    assert upload(c, ctype="application/pdf").status_code == 400


def test_signed_out_callers_get_nothing(tmp_path):
    app = FastAPI()
    app.include_router(ar.router, prefix="/area-photos")
    app.dependency_overrides[get_user_manager] = lambda: SimpleNamespace()   # no token: never asked about a user
    c = TestClient(app)
    assert c.get("/area-photos", params={"area": "kharadi"}).status_code == 401
    assert c.post("/area-photos/x/publish").status_code == 401


# ---- the photo scout's suggestions: owner-only publish, refuse and publish-all --------------------------------------------
async def _suggestion(db, tmp_path, pid="s1", area="kharadi"):
    svc = AreaPhotos(db, now=lambda: NOW, root=tmp_path)
    pic = {"url": f"/uploads/area_photos/{area}/{pid}.webp", "small_url": f"/uploads/area_photos/{area}/{pid}-small.webp",
          "width": 1600, "height": 1067}
    return await svc.add_suggestion(area, pic, LICENSED, commons_pageid=42, ai={"score": 4, "shows": ["main_road"],
                                   "reason": "Shows Kharadi's main road; taken March 2024; CC BY-SA 4.0."}, now=NOW)


async def test_an_agent_sees_suggestions_read_only(tmp_path):
    db = FakeDb()
    await _suggestion(db, tmp_path)
    c = client(AGENT, db, tmp_path)
    r = c.get("/area-photos", params={"area": "kharadi"})
    [item] = r.json()["items"]
    assert item["status"] == "suggested" and item["origin"] == "scout" and item["ai"]["score"] == 4
    assert c.post(f"/area-photos/{item['id']}/publish").status_code == 403
    assert c.post(f"/area-photos/{item['id']}/refuse").status_code == 403
    assert c.post("/area-photos/publish-all", json={"area": "kharadi"}).status_code == 403


async def test_the_owner_publishes_a_suggestion_and_the_guide_shows_it(tmp_path):
    db = FakeDb()
    doc = await _suggestion(db, tmp_path)
    owner = client(OWNER, db, tmp_path)
    r = owner.post(f"/area-photos/{doc['_id']}/publish")
    assert r.status_code == 200 and r.json()["status"] == "live"
    [p] = owner.get("/public/areas/kharadi/photos").json()["photos"]
    assert p["credit"] == LICENSED["credit"]


async def test_the_owner_refuses_a_suggestion_and_it_stays_off_the_guide(tmp_path):
    db = FakeDb()
    doc = await _suggestion(db, tmp_path)
    owner = client(OWNER, db, tmp_path)
    r = owner.post(f"/area-photos/{doc['_id']}/refuse")
    assert r.status_code == 200 and r.json()["status"] == "refused"
    assert owner.get("/public/areas/kharadi/photos").json()["photos"] == []


async def test_publish_all_suggested_publishes_every_one_for_the_area_only(tmp_path):
    db = FakeDb()
    for i in range(3):
        await _suggestion(db, tmp_path, pid=f"s{i}")
    await _suggestion(db, tmp_path, pid="other-area", area="wagholi")
    owner = client(OWNER, db, tmp_path)
    r = owner.post("/area-photos/publish-all", json={"area": "kharadi"})
    assert r.status_code == 200
    assert {i["status"] for i in r.json()["items"]} == {"live"}
    kharadi_live = owner.get("/public/areas/kharadi/photos").json()["photos"]
    assert len(kharadi_live) == 3
    assert owner.get("/public/areas/wagholi/photos").json()["photos"] == []
