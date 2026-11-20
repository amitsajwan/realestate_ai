"""Reels to our YouTube channel (docs/plan/visibility-base.md step 1): off until set up, each reel once (the publish ledger), a
daily cap for the API quota, and a title and description that name the project, the place and the page."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from app.modules.calendar import adapters
from app.modules.social import distribution
from app.platform import youtube_upload as yt
from app.platform.controls import set_controls

from .fakes import FakeDb

NOW = datetime(2026, 11, 15, 9, 0, tzinfo=timezone.utc)
KEYS = {"YOUTUBE_UPLOAD": "on", "YOUTUBE_CLIENT_ID": "cid", "YOUTUBE_CLIENT_SECRET": "sec-123", "YOUTUBE_REFRESH_TOKEN": "ref-456"}


@pytest.fixture
def set_up(monkeypatch):
    for k, v in KEYS.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("PUBLISH_LEDGER", raising=False)


class YouTubeApi:
    """The token, upload-start and upload calls Google answers; counts uploads and keeps the metadata sent."""

    def __init__(self, fail_upload: bool = False):
        self.uploads, self.meta, self.fail_upload = 0, None, fail_upload

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth2.googleapis.com":
            assert b"refresh_token=ref-456" in request.content
            return httpx.Response(200, json={"access_token": "tok"})
        if request.method == "POST":
            import json
            self.meta = json.loads(request.content)
            return httpx.Response(200, headers={"location": "https://upload.test/session-1"})
        if self.fail_upload:
            return httpx.Response(403, text="quotaExceeded")
        self.uploads += 1
        return httpx.Response(200, json={"id": f"vid{self.uploads}"})


def video(tmp_path: Path) -> Path:
    p = tmp_path / "reel.mp4"
    p.write_bytes(b"\x00" * 64)
    return p


META = yt.VideoMeta(title="Godrej Ivara: 3 BHK from ₹1.2 Cr | Upper Kharadi, Pune", description="https://avasetu.in/projects/godrej-ivara-pune")


async def test_nothing_is_sent_until_the_upload_is_set_up(tmp_path, monkeypatch):
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)
    api = YouTubeApi()
    got = await distribution.youtube_short(FakeDb(), "ivara-1", video(tmp_path), META, now=lambda: NOW, transport=httpx.MockTransport(api))
    assert got is None and api.uploads == 0


async def test_a_reel_is_uploaded_once_whatever_the_retries(set_up, tmp_path):
    db, api = FakeDb(), YouTubeApi()
    t = httpx.MockTransport(api)
    first = await distribution.youtube_short(db, "ivara-1", video(tmp_path), META, now=lambda: NOW, transport=t)
    again = await distribution.youtube_short(db, "ivara-1", video(tmp_path), META, now=lambda: NOW, transport=t)
    assert api.uploads == 1 and first.external_id == again.external_id == "vid1"
    assert first.permalink == "https://www.youtube.com/shorts/vid1"
    assert api.meta["snippet"]["title"].startswith("Godrej Ivara") and api.meta["status"]["privacyStatus"] == "public"
    assert api.meta["snippet"]["categoryId"] == "22"


async def test_uploads_stop_at_the_daily_cap_and_go_again_the_next_day(set_up, tmp_path, monkeypatch):
    monkeypatch.setenv("YOUTUBE_UPLOADS_PER_DAY", "2")
    db, api = FakeDb(), YouTubeApi()
    t = httpx.MockTransport(api)
    for ref in ("a", "b", "c"):
        await distribution.youtube_short(db, ref, video(tmp_path), META, now=lambda: NOW, transport=t)
    assert api.uploads == 2
    tomorrow = NOW + timedelta(days=1)
    assert (await distribution.youtube_short(db, "c", video(tmp_path), META, now=lambda: tomorrow, transport=t)).external_id == "vid3"


async def test_a_pause_stops_uploads_and_a_refusal_is_recorded_without_its_secrets(set_up, tmp_path):
    db = FakeDb()
    await set_controls(db, {"posting_paused": True}, "owner", NOW)
    assert await distribution.youtube_short(db, "p", video(tmp_path), META, now=lambda: NOW,
                                            transport=httpx.MockTransport(YouTubeApi())) is None
    db = FakeDb()
    with pytest.raises(distribution.PublishError):
        await distribution.youtube_short(db, "q", video(tmp_path), META, now=lambda: NOW,
                                         transport=httpx.MockTransport(YouTubeApi(fail_upload=True)))
    row = db.get_collection(distribution.COLLECTION).docs[0]
    assert row["status"] == "failed" and "quotaExceeded" in row["error"] and "ref-456" not in row["error"]


def test_metadata_fits_youtubes_limits():
    m = yt.fit(yt.VideoMeta(title="<b>" + "word " * 40, description="x" * 6000, tags=["Pune"] * 3 + ["t" * 300, "u" * 300]))
    assert len(m.title) <= 100 and "<" not in m.title and m.title.endswith("…")
    assert len(m.description) <= 5000 and m.tags == ["Pune", "t" * 300]


def test_the_video_names_the_project_and_place_and_opens_with_its_page():
    doc = {"_id": "r1", "slug": "ivara-reel-1", "channel": "instagram", "area": "upper_kharadi", "project_name": "Godrej Ivara",
           "page_url": "https://avasetu.in/projects/godrej-ivara-pune",
           "caption": "🏙️ 3 BHK from ₹1.2 Cr, possession Dec 2032\nMahaRERA PR1260002502426, 57% booked.\n"
                      "👉 Interested? Tap the link in our bio and press 'I am interested'.\n"
                      '🔎 Search "Avasetu Upper Kharadi" on Google\nAvasetu · avasetu.in/projects/godrej-ivara-pune · link in our bio'}
    m = adapters.youtube_meta(doc)
    assert m.title == "Godrej Ivara: 3 BHK from ₹1.2 Cr, possession Dec 2032 | Upper Kharadi, Pune"
    assert m.description.startswith("Full details, price sheet and MahaRERA status: https://avasetu.in/projects/godrej-ivara-pune")
    assert "link in our bio" not in m.description and "57% booked" in m.description and "Search \"Avasetu Upper Kharadi\"" in m.description
    assert m.tags[:2] == ["Godrej Ivara", "Upper Kharadi"]


def test_a_listing_reel_opens_with_its_listing_page_taken_from_the_caption():
    head = "Spacious carpet areas\nHomes range 841-1,150 sq ft\n🌐 Website: house-deal.com\n🏠 On Avasetu: avasetu.in/agent/house-deal\n"
    ig = {"_id": "r1", "slug": "campaign-L1-room3_design-ad", "channel": "instagram", "creative": {"project_name": "Unique UNI 89",
          "locality": "Mundhwa"}, "caption": head + "Full details of Mundhwa, with its MahaRERA record: link in bio · "
                                                    "avasetu.in/agent/house-deal/listings/L1"}
    fb = {**ig, "channel": "facebook_page", "caption": head + "Photos and full details: "
                                                              "https://avasetu.in/agent/house-deal/listings/L1?src=fb_room3_design-ad"}
    for doc in (ig, fb):
        m = adapters.youtube_meta(doc)
        assert m.title == "Unique UNI 89: Spacious carpet areas | Mundhwa, Pune"
        assert m.description.startswith("Full details, price sheet and MahaRERA status: https://avasetu.in/agent/house-deal/listings/L1\n")
        assert "link in bio" not in m.description and "src=fb_" not in m.description and "house-deal.com" in m.description


async def test_a_reel_without_its_video_file_is_skipped_quietly(set_up, tmp_path):
    assert await adapters.to_youtube(FakeDb(), {"_id": "r1", "slug": "s", "video": "gone.mp4", "caption": "x"}, tmp_path) is None
