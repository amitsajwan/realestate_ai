"""The monthly run: story then pitches then pruning, and never any send code path (CLAUDE.md rule 6)."""
import sys
from datetime import datetime, timedelta, timezone

from app.modules.press.config import Config
from app.modules.press.service import monthly_run
from app.modules.press.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)


async def seeded_db():
    db = FakeDb()
    await db.get_collection("projects").insert_one(
        {"_id": "PR1260002600001", "regno": "PR1260002600001", "name": "Project 1", "locality": "kharadi",
         "registered_on": "2026-11-02", "units_total": 100, "units_booked": 40})
    return db


async def fake_search(q):
    return [{"title": "Kharadi housing story", "link": "https://hindustantimes.com/kharadi", "snippet": "", "date": ""}]


async def fake_fetch(url):
    return None


async def test_monthly_run_stores_a_story_and_one_pitch_per_journalist():
    db = await seeded_db()
    out = await monthly_run(db, NOW, cfg=Config(contact_email="hello@avasetu.in"), search=fake_search, fetch=fake_fetch, llm=None)
    assert out["pitches"] == 1
    pitches = await Store(db).pitches_for("2026-11")
    assert len(pitches) == 1 and pitches[0]["status"] == "draft" and pitches[0]["origin"] == "template"
    story = await Store(db).story("2026-11")
    assert story is not None and story["headline_facts"]


async def test_monthly_run_never_imports_any_mail_or_smtp_module():
    """Nothing here can send: no smtplib, no email client, ever imported by the press package."""
    before = set(sys.modules)
    db = await seeded_db()
    await monthly_run(db, NOW, cfg=Config(), search=fake_search, fetch=fake_fetch, llm=None)
    after = set(sys.modules) - before
    assert not any(m.startswith(("smtplib", "email.mime", "imaplib", "poplib")) for m in after)
    import app.modules.press as press_pkg
    import inspect
    import os
    src_dir = os.path.dirname(inspect.getfile(press_pkg))
    for fname in os.listdir(src_dir):
        if fname.endswith(".py"):
            text = open(os.path.join(src_dir, fname)).read()
            assert "smtplib" not in text and "sendmail" not in text.lower()


async def test_no_headline_facts_means_no_journalist_search():
    called = {"search": False}

    async def must_not_be_called(q):
        called["search"] = True
        return []
    out = await monthly_run(FakeDb(), NOW, cfg=Config(), search=must_not_be_called, fetch=fake_fetch, llm=None)
    assert out["pitches"] == 0 and called["search"] is False


async def test_pitches_from_an_earlier_month_are_pruned_after_a_year():
    db = await seeded_db()
    store = Store(db)
    old_j = {"outlet": "A", "title": "old", "url": "https://hindustantimes.com/old", "date": "", "name": None,
             "email": None, "contact_page": None}
    await store.save_pitch("2025-10", old_j, {"subject": "s", "body": "b", "origin": "template"}, NOW - timedelta(days=380))
    await monthly_run(db, NOW, cfg=Config(pitch_ttl_days=365), search=fake_search, fetch=fake_fetch, llm=None)
    remaining = await store.pitches_for()
    assert not any(p["article"]["url"] == "https://hindustantimes.com/old" for p in remaining)
