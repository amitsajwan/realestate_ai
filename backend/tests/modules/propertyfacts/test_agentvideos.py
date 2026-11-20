"""The agents' own listing videos copied to our server for video search (propertyfacts/agentvideos.py).

Owner 2026-11-20: "lets get all agents project videos also with us, for video indexing": House Deal's sample-flat videos played
from house-deal.com, so Google credited their site, not our project pages."""
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.modules.propertyfacts import agentvideos as av
from app.modules.propertyfacts import mainvideo, router as facts_router
from app.modules.propertyfacts.router import with_sheet

from ..fakes import FakeDb

NOW = datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc)
REG = "P52100078107"
SITE = "https://www.house-deal.com"
TWO = "https://house-deal.com/wp-content/uploads/2026/09/Medora-2bhk-sample-flat.mp4"
THREE = "https://house-deal.com/wp-content/uploads/2026/09/Medora-3bhk-sample-flat.mp4"


class Probe:
    duration, width, height = 41.6, 720, 1280


class Tools:
    """Downloads and ffmpeg as the pass sees them: what was fetched, and files that fail."""

    def __init__(self, broken=()):
        self.fetched, self.broken = [], set(broken)

    def get(self, url, dest):
        self.fetched.append(url)
        if url in self.broken:
            raise OSError("404")
        Path(dest).write_bytes(b"raw " + url.encode())

    def make(self, src, dest):
        Path(dest).write_bytes(b"h264 " + Path(src).read_bytes())

    @staticmethod
    def frame(video, out):
        Path(out).write_bytes(b"jpg")

    @staticmethod
    def probe(video):
        return Probe()

    async def run(self, db, root, per_turn=5):
        return await av.refresh(db, root, NOW, per_turn=per_turn, get=self.get, make=self.make, frame=self.frame, probe=self.probe)


async def seeded(videos=(TWO, THREE), status="live", public=True, media=()):
    db = FakeDb()
    await db.get_collection("agent_public_profiles").insert_one({"agent_id": "HD", "slug": "house-deal", "is_public": public,
                                                                 "branding_data": {"business_name": "House Deal", "website": SITE}})
    await db.get_collection("listings").insert_one({
        "_id": "L1", "agent_id": "HD", "rera_no": REG, "status": status, "project_name": "Anshul Medora", "price_inr": 9_000_000,
        "updated_at": NOW, "media": list(media),
        "videos": [{"url": u, "label": f"{i + 2} BHK sample flat"} for i, u in enumerate(videos)]})
    return db


def kept_files(root):
    folder = root / mainvideo.KEPT_DIR
    return sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []


async def test_each_website_video_is_kept_once_as_a_phone_friendly_copy_with_a_poster(tmp_path):
    db, tools = await seeded(), Tools()
    out = await tools.run(db, tmp_path)
    assert out == {"kept": 2, "failed": 0, "removed": 0, "waiting": 0} and tools.fetched == [TWO, THREE]
    doc = await db.get_collection(av.COLLECTION).find_one({"_id": f"L1:{av.key_of(TWO)}"})
    assert doc["file"].startswith("av-L1-") and doc["poster"] == doc["file"][:-4] + ".jpg"
    assert (doc["seconds"], doc["width"], doc["height"], doc["order"], doc["label"]) == (42, 720, 1280, 0, "2 BHK sample flat")
    assert (tmp_path / mainvideo.KEPT_DIR / doc["file"]).read_bytes() == b"h264 raw " + TWO.encode()
    assert not [n for n in kept_files(tmp_path) if n.endswith((".src", ".part"))]      # no download left behind
    again = await tools.run(db, tmp_path)
    assert again["kept"] == 0 and tools.fetched == [TWO, THREE]                          # never fetched twice


async def test_only_the_agents_own_site_live_listings_and_shown_agents_are_kept(tmp_path):
    for db in (await seeded(videos=("https://elsewhere.com/a.mp4", "http://house-deal.com/b.mp4", "https://house-deal.com/c.mov")),
               await seeded(status="draft"), await seeded(public=False)):
        tools = Tools()
        assert (await tools.run(db, tmp_path))["kept"] == 0 and tools.fetched == []


async def test_a_video_uploaded_in_studio_is_kept_from_our_own_disk(tmp_path):
    (tmp_path / "videos").mkdir()
    (tmp_path / "videos" / "cee5.mp4").write_bytes(b"walk")
    db = await seeded(videos=(), media=[{"kind": "video", "url": "http://avasetu.in/uploads/videos/cee5.mp4", "order": 4},
                                        {"kind": "video", "url": "http://avasetu.in/uploads/videos/../../etc.mp4"}])
    tools = Tools()
    assert (await tools.run(db, tmp_path))["kept"] == 1 and tools.fetched == []
    doc = await db.get_collection(av.COLLECTION).find_one({})
    assert (tmp_path / mainvideo.KEPT_DIR / doc["file"]).read_bytes() == b"h264 walk"


async def test_a_few_a_turn_and_a_broken_file_is_tried_three_times_then_left(tmp_path):
    db, tools = await seeded(), Tools(broken={TWO})
    assert await tools.run(db, tmp_path, per_turn=1) == {"kept": 0, "failed": 1, "removed": 0, "waiting": 1}
    for _ in range(4):
        await tools.run(db, tmp_path, per_turn=1)
    assert tools.fetched.count(TWO) == av.TRIES and tools.fetched.count(THREE) == 1
    assert (await db.get_collection(av.COLLECTION).find_one({"_id": f"L1:{av.key_of(TWO)}"}))["error"] == "OSError"


async def test_a_video_the_listing_dropped_or_a_listing_gone_loses_its_copy(tmp_path):
    db, tools = await seeded(), Tools()
    await tools.run(db, tmp_path)
    await db.get_collection("listings").update_one({"_id": "L1"}, {"$set": {"videos": [{"url": THREE, "label": "3 BHK"}]}})
    out = await tools.run(db, tmp_path)
    assert out["removed"] == 1 and len(kept_files(tmp_path)) == 2
    assert (await db.get_collection(av.COLLECTION).find_one({"_id": f"L1:{av.key_of(THREE)}"}))["order"] == 0
    await db.get_collection("listings").update_one({"_id": "L1"}, {"$set": {"status": "sold"}})
    assert (await tools.run(db, tmp_path))["removed"] == 1 and kept_files(tmp_path) == []


async def test_keeping_the_campaign_video_never_removes_the_agents_copies(tmp_path):
    db, tools = await seeded(), Tools()
    await tools.run(db, tmp_path)
    reel = tmp_path / "campaigns" / "L1" / "r" / "a.mp4"
    reel.parent.mkdir(parents=True)
    reel.write_bytes(b"ad")
    mainvideo.keep(tmp_path, {"listing_id": "L1", "reels": [{"kind": "ad", "video": "/uploads/campaigns/L1/r/a.mp4"}]}, NOW,
                   frame=Tools.frame, seconds=lambda p: 20)
    assert len([n for n in kept_files(tmp_path) if n.startswith("av-")]) == 4


async def test_the_page_offer_and_the_video_list_carry_the_kept_copies(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_directory", str(tmp_path))

    async def page_for(db, regno):
        return {"slug": "anshul-medora-wagholi", "indexable": True}
    monkeypatch.setattr(facts_router, "page_for", page_for)
    db, tools = await seeded(), Tools()
    await tools.run(db, tmp_path)
    offer = (await with_sheet(db, {"maharera": {"rera_no": REG}, "offer": {"price_inr": 1}}, "L1"))["offer"]
    assert [v["label"] for v in offer["agent_videos"]] == ["2 BHK sample flat", "3 BHK sample flat"]
    first = offer["agent_videos"][0]
    assert first["url"].startswith("/api/v1/public/listing-video/av-L1-") and first["poster"].endswith(".jpg")
    assert (first["key"], first["seconds"], first["uploaded_at"]) == (av.key_of(TWO), 42, "2026-11-20")
    assert [v["url"] for v in offer["videos"]] == [TWO, THREE]          # the website addresses stay as they were
    out = await facts_router.project_videos(db)
    assert [(o["slug"], o["video"], len(o["agent_videos"])) for o in out] == [("anshul-medora-wagholi", None, 2)]
