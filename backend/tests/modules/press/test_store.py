from datetime import datetime, timedelta, timezone

from app.modules.press.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)


async def test_save_and_read_a_story():
    store = Store(FakeDb())
    facts = [{"text": "x", "area": None, "topic": "registrations", "source": "s", "as_of": "2026-11-17"}]
    await store.save_story("2026-11", facts, facts, NOW)
    assert (await store.story("2026-11"))["facts"] == facts
    assert (await store.latest_story())["month"] == "2026-11"
    await store.save_story("2026-11", facts + facts, facts, NOW)  # upsert, not a duplicate
    assert len((await store.story("2026-11"))["facts"]) == 2


async def test_the_same_journalist_is_not_pitched_twice_in_a_month():
    store = Store(FakeDb())
    j = {"outlet": "Hindustan Times", "title": "t", "url": "https://hindustantimes.com/a", "date": "", "name": None,
         "email": None, "contact_page": None}
    draft = {"subject": "s", "body": "b", "origin": "template"}
    first = await store.save_pitch("2026-11", j, draft, NOW)
    again = await store.save_pitch("2026-11", j, draft, NOW)
    assert first["_id"] == again["_id"]
    assert len(await store.pitches_for("2026-11")) == 1


async def test_pitches_older_than_the_ttl_are_pruned():
    store = Store(FakeDb())
    old = {"outlet": "A", "title": "t1", "url": "https://hindustantimes.com/old", "date": "", "name": None, "email": None,
          "contact_page": None}
    fresh = {"outlet": "A", "title": "t2", "url": "https://hindustantimes.com/fresh", "date": "", "name": None, "email": None,
            "contact_page": None}
    draft = {"subject": "s", "body": "b", "origin": "template"}
    await store.save_pitch("2025-11", old, draft, NOW - timedelta(days=380))
    await store.save_pitch("2026-11", fresh, draft, NOW)
    pruned = await store.prune_old(NOW, 365)
    assert pruned == 1
    urls = [p["article"]["url"] for p in await store.pitches_for()]
    assert urls == ["https://hindustantimes.com/fresh"]


async def test_summary_counts_sent_replied_and_links_won():
    store = Store(FakeDb())
    j1 = {"outlet": "A", "title": "t1", "url": "https://hindustantimes.com/1", "date": "", "name": None, "email": None,
         "contact_page": None}
    j2 = {"outlet": "A", "title": "t2", "url": "https://hindustantimes.com/2", "date": "", "name": None, "email": None,
         "contact_page": None}
    draft = {"subject": "s", "body": "b", "origin": "template"}
    p1 = await store.save_pitch("2026-11", j1, draft, NOW)
    p2 = await store.save_pitch("2026-11", j2, draft, NOW)
    await store.update_pitch(p1["_id"], status="sent", replied=True, link_won_url="https://hindustantimes.com/story")
    await store.update_pitch(p2["_id"], status="skipped")
    assert await store.summary() == {"sent": 1, "replied": 1, "links_won": 1}
