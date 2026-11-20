"""The campaign's main video kept for the listing's page (propertyfacts/mainvideo.py), offered on the page and served with ranges.

2026-11-20: the owner wants the marketing video on our page, stored by us (not a YouTube or Facebook embed); the drawn reels
are deleted two days after drawing (admin.video_cleanup), and our /uploads mount answers no byte ranges, which phones need."""
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.modules.admin.video_cleanup import old_videos
from app.modules.propertyfacts import mainvideo, router as facts_router
from app.modules.propertyfacts.router import with_sheet

from ..fakes import FakeDb

NOW = datetime(2026, 11, 20, 9, 0)
REG = "P52100078107"


def drawn(root: Path, rel: str, data: bytes = b"0123456789" * 10) -> str:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return "/uploads/" + rel


def poster(video: Path, out: Path) -> None:
    out.write_bytes(b"jpg")


def run_with(*reels, lid="L1", rid="run12345abc"):
    return {"_id": rid, "listing_id": lid, "reels": list(reels)}


def test_the_agents_own_video_stands_for_the_campaign_then_a_walkthrough_then_the_ad_reel():
    ad = {"kind": "ad", "angle": "room2_homes", "video": "/uploads/a.mp4"}
    walk = {"kind": "walkthrough", "status": "done", "video": "/uploads/w.mp4"}
    own = {"kind": "video", "status": "done", "video": "/uploads/v.mp4"}
    assert mainvideo.choose(run_with(ad, walk, own)) is own
    assert mainvideo.choose(run_with(ad, walk)) is walk
    assert mainvideo.choose(run_with(ad, {**walk, "status": "queued"})) is ad
    assert mainvideo.choose(run_with({"kind": "ad", "video": None})) is None


def test_the_main_video_is_copied_out_of_the_cleanups_reach_with_a_poster_and_one_copy_a_listing(tmp_path):
    first = drawn(tmp_path, "campaigns/L1/run1/reels/ad-room2_homes.mp4")
    kept = mainvideo.keep(tmp_path, run_with({"kind": "ad", "angle": "room2_homes", "video": first, "caption": "Homes at UNI 89\nmore"}),
                          NOW, frame=poster, seconds=lambda p: 24)
    video = tmp_path / mainvideo.KEPT_DIR / kept["file"]
    assert video.read_bytes() == (tmp_path / first[len("/uploads/"):]).read_bytes()
    assert kept["poster"] == video.with_suffix(".jpg").name and kept["seconds"] == 24 and kept["headline"] == "Homes at UNI 89"
    assert kept["file"].startswith("L1-") and kept["kept_at"] == NOW
    # two days on, the cleanup deletes the drawn reel but never the kept copy
    later = datetime.fromtimestamp(video.stat().st_mtime) + timedelta(days=3)
    assert [p.name for p in old_videos(tmp_path, later)] == ["ad-room2_homes.mp4"]
    # a voiced remake is a new file: a new name, and the listing's older copy goes
    voiced = drawn(tmp_path, "campaigns/L1/run1/reels/ad-room2_homes-en-female.mp4", b"voiced")
    again = mainvideo.keep(tmp_path, run_with({"kind": "ad", "video": voiced}), NOW, frame=poster, seconds=lambda p: 25)
    assert again["file"] != kept["file"]
    assert sorted(p.name for p in (tmp_path / mainvideo.KEPT_DIR).iterdir()) == sorted([again["file"], again["poster"]])


def test_no_reel_or_a_reel_already_deleted_keeps_nothing(tmp_path):
    assert mainvideo.keep(tmp_path, run_with(), NOW, frame=poster) is None
    assert mainvideo.keep(tmp_path, run_with({"kind": "ad", "video": "/uploads/campaigns/gone.mp4"}), NOW, frame=poster) is None


def test_a_poster_that_cannot_be_drawn_leaves_the_video_playable(tmp_path):
    def broken(video, out):
        raise RuntimeError("no ffmpeg")
    kept = mainvideo.keep(tmp_path, run_with({"kind": "ad", "video": drawn(tmp_path, "campaigns/L1/r/a.mp4")}), NOW, frame=broken,
                          seconds=lambda p: None)
    assert kept["file"] and kept["poster"] is None
    assert mainvideo.public(kept) == {"url": "/api/v1/public/listing-video/" + kept["file"], "poster": None, "seconds": None,
                                      "headline": "", "uploaded_at": "2026-11-20"}


def test_byte_ranges_are_read_as_phones_send_them():
    assert mainvideo.byte_range("bytes=0-1", 100) == (0, 1)
    assert mainvideo.byte_range("bytes=0-", 100) == (0, 99)
    assert mainvideo.byte_range("bytes=90-500", 100) == (90, 99)
    assert mainvideo.byte_range("bytes=-10", 100) == (90, 99)
    assert mainvideo.byte_range("bytes=200-", 100) is None
    assert mainvideo.byte_range("bytes=0-1,5-6", 100) is None
    assert mainvideo.byte_range(None, 100) is None


async def offer_db(tmp_path, kept):
    db = FakeDb()
    await db.get_collection("agent_public_profiles").insert_one({"agent_id": "HD", "slug": "house-deal", "is_public": True,
                                                                 "branding_data": {"business_name": "House Deal"}})
    await db.get_collection("listings").insert_one({"_id": "L1", "agent_id": "HD", "rera_no": REG, "status": "live",
                                                    "price_inr": 12_000_000, "updated_at": NOW, "media": []})
    await db.get_collection("marketing_runs").insert_one({"_id": "old", "listing_id": "L1", "created_at": datetime(2026, 11, 1)})
    await db.get_collection("marketing_runs").insert_one({"_id": "new", "listing_id": "L1", "created_at": NOW, "main_video": kept})
    return db


async def test_the_project_page_offer_carries_the_kept_video_while_its_file_is_there(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_directory", str(tmp_path))
    kept = mainvideo.keep(tmp_path, run_with({"kind": "ad", "video": drawn(tmp_path, "campaigns/L1/r/a.mp4")}), NOW, frame=poster,
                          seconds=lambda p: 20)
    db = await offer_db(tmp_path, kept)
    facts = {"maharera": {"rera_no": REG}, "offer": {"price_inr": 1}}
    video = (await with_sheet(db, facts, "L1"))["offer"]["main_video"]
    assert video["url"].endswith(kept["file"]) and video["poster"].endswith(".jpg") and video["seconds"] == 20
    (tmp_path / mainvideo.KEPT_DIR / kept["file"]).unlink()
    assert "main_video" not in (await with_sheet(db, facts, "L1"))["offer"]


def test_the_kept_video_is_served_with_byte_ranges_and_odd_names_are_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_directory", str(tmp_path))
    kept = mainvideo.keep(tmp_path, run_with({"kind": "ad", "video": drawn(tmp_path, "campaigns/L1/r/a.mp4", bytes(range(200)))}),
                          NOW, frame=poster, seconds=lambda p: 20)
    app = FastAPI()
    app.include_router(facts_router.public_router, prefix="/api/v1/public")
    client = TestClient(app)
    url = mainvideo.public(kept)["url"]
    part = client.get(url, headers={"Range": "bytes=10-19"})
    assert part.status_code == 206 and part.content == bytes(range(10, 20))
    assert part.headers["content-range"] == "bytes 10-19/200" and part.headers["content-type"] == "video/mp4"
    whole = client.get(url)
    assert whole.status_code == 200 and len(whole.content) == 200 and whole.headers["accept-ranges"] == "bytes"
    assert "immutable" in whole.headers["cache-control"]
    assert client.get(mainvideo.public(kept)["poster"]).content == b"jpg"
    assert client.get("/api/v1/public/listing-video/..%2F..%2Fsecret.mp4").status_code == 404
    assert client.get("/api/v1/public/listing-video/nothing.mp4").status_code == 404


async def test_the_video_list_has_one_video_a_project_page_only_live_listings_and_pages_in_search(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_directory", str(tmp_path))
    pages = {"P1": {"slug": "uni-89", "indexable": True}, "P2": {"slug": "hidden", "indexable": False}}

    async def page_for(db, regno):
        return pages.get(regno)
    monkeypatch.setattr(facts_router, "page_for", page_for)
    db = FakeDb()
    for lid, regno, status in (("A", "P1", "live"), ("B", "P1", "live"), ("C", "P2", "live"), ("D", "P1", "draft"), ("E", "P1", "live")):
        await db.get_collection("listings").insert_one({"_id": lid, "rera_no": regno, "status": status, "project_name": f"Project {lid}"})
    for i, lid in enumerate(("A", "B", "C", "D", "E")):
        kept = mainvideo.keep(tmp_path, run_with({"kind": "ad", "video": drawn(tmp_path, f"campaigns/{lid}/r/a.mp4")}, lid=lid), NOW,
                              frame=poster, seconds=lambda p: 20)
        await db.get_collection("marketing_runs").insert_one({"_id": f"r{lid}", "listing_id": lid, "main_video": kept,
                                                              "created_at": datetime(2026, 11, 20, i)})
    (tmp_path / mainvideo.KEPT_DIR / (await db.get_collection("marketing_runs").find_one({"_id": "rE"}))["main_video"]["file"]).unlink()
    out = await facts_router.project_videos(db)
    # E's file is gone, D is a draft, C's page is not in search: B is the newest video of uni-89, and A's page is already taken
    assert [(o["slug"], o["name"]) for o in out] == [("uni-89", "Project B")]
    assert out[0]["video"]["url"].startswith("/api/v1/public/listing-video/B-")
