"""Drawn reel videos leave the uploads volume two days after they were made, unless a calendar row is still to post them."""
import asyncio
import os
from datetime import datetime, timedelta

from app.modules.admin import video_cleanup
from app.modules.calendar.config import COLLECTION

from ..fakes import FakeDb

NOW = datetime(2026, 10, 23, 12, 0, 0)


def _file(root, rel, age: timedelta):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x" * 10)
    t = (NOW - age).timestamp()
    os.utime(p, (t, t))
    return p


def test_videos_older_than_two_days_are_deleted_and_sources_and_open_rows_are_kept(tmp_path):
    old = timedelta(days=3)
    posted = _file(tmp_path, "reels/a.mp4", old)
    run = _file(tmp_path, "campaigns/agent1/run1/reel.mp4", old)
    fresh = _file(tmp_path, "calendar/reels/new.mp4", timedelta(hours=30))
    waiting = _file(tmp_path, "calendar/reels/tomorrow.mp4", old)
    walkthrough = _file(tmp_path, "videos/agent-upload.mp4", old)
    cover = _file(tmp_path, "reels/a-cover.jpg", old)
    db = FakeDb()
    asyncio.run(db.get_collection(COLLECTION).insert_one(
        {"_id": "r1", "slug": "s", "status": "approved", "video": "calendar/reels/tomorrow.mp4", "due_at": NOW}))
    asyncio.run(db.get_collection(COLLECTION).insert_one(
        {"_id": "r2", "slug": "p", "status": "published", "video": "reels/a.mp4", "due_at": NOW}))

    res = asyncio.run(video_cleanup.cycle(db, NOW, tmp_path))

    assert res["removed"] == 2
    assert not posted.exists() and not run.exists()
    assert fresh.exists() and waiting.exists() and walkthrough.exists() and cover.exists()
