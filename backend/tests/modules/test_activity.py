"""Per-listing activity (contract docs/contracts/activity.md section 1)."""
import json
from datetime import datetime, timedelta

import pytest

from app.modules.tracking import activity as act
from app.modules.tracking.service import TrackingError

from .activity_helpers import activity, add_event, add_lead, add_view, ago, make

pytestmark = pytest.mark.asyncio

ZERO_TOTALS = {"views": 0, "unique_visitors": 0, "enquiries": 0, "qualified": 0, "site_visits": 0, "deals": 0,
               "whatsapp_clicks": 0, "call_clicks": 0, "shares": 0}


async def test_empty_state():
    svc, _, _ = await make()
    out = await activity(svc)
    assert out["listing"] == {"id": "L1", "title": "2BHK in Baner", "status": "live", "price_inr": 8_500_000}
    assert out["totals"] == ZERO_TOTALS
    assert out["by_source"] == {} and out["feed"] == [] and out["people"] == []
    assert len(out["daily"]) == 14 and all(d["views"] == 0 and d["enquiries"] == 0 for d in out["daily"])


async def test_other_agents_and_unknown_listings_are_404():
    svc, _, _ = await make()
    for agent, lid in (("A1", "L7"), ("A2", "L1"), ("A1", "NOPE")):
        with pytest.raises(TrackingError) as exc:
            await activity(svc, listing=lid, agent=agent)
        assert exc.value.status_code == 404


async def test_totals_match_performance_rules():
    svc, db, clock = await make()
    for anon in ("anon-1", "anon-1", "anon-2", "anon-3"):
        await add_view(db, clock, "L1", anon)
    await add_view(db, clock, "L2", "anon-1")                  # another listing
    await add_view(db, clock, "L1", "anon-9", agent="A2")      # another agent
    await add_lead(db, clock, "c1", first_listing="L1", source="whatsapp", base=40)   # qualified (hot)
    await add_lead(db, clock, "c2", first_listing="L1", stage="site_visit")
    await add_lead(db, clock, "c3", first_listing="L1", stage="won")
    await add_lead(db, clock, "c4", first_listing="L2")
    await add_lead(db, clock, "c5", first_listing="L1", agent="A2")
    # a deal attributed to L1 although the lead first asked about L2
    await add_lead(db, clock, "c6", first_listing="L2", stage="won")
    db.get_collection("contacts").docs[-1]["outcome"] = {"result": "won", "deal_price_inr": 8_000_000, "listing_id": "L1"}
    perf = {i["listing_id"]: i for i in (await svc.performance("A1"))["items"]}["L1"]
    totals = (await activity(svc))["totals"]
    for key in ("views", "unique_visitors", "enquiries", "qualified", "site_visits", "deals"):
        assert totals[key] == perf[key], key
    assert (totals["views"], totals["unique_visitors"], totals["enquiries"], totals["deals"]) == (4, 3, 3, 1)


async def test_click_and_share_totals_ignore_other_listings_agents_and_page_views():
    svc, db, clock = await make()
    for t in ("whatsapp_click", "whatsapp_click", "call_click", "share", "share", "share"):
        await add_event(db, clock, t)
    await add_event(db, clock, "whatsapp_click", listing="L2")
    await add_event(db, clock, "call_click", agent="A2")
    await add_event(db, clock, "page_view")
    t = (await activity(svc))["totals"]
    assert (t["whatsapp_clicks"], t["call_clicks"], t["shares"], t["views"]) == (2, 1, 3, 0)


async def test_by_source_counts_views_and_enquiries():
    svc, db, clock = await make()
    await add_event(db, clock, "listing_view", source="instagram")
    await add_event(db, clock, "listing_view", source="instagram", anon="anon-2")
    await add_event(db, clock, "listing_view", source=None, anon="anon-3")
    await add_lead(db, clock, "c1", first_listing="L1", source="whatsapp")
    await add_lead(db, clock, "c2", first_listing="L1", source="instagram")
    await add_lead(db, clock, "c3", first_listing="L1", source=None)
    assert (await activity(svc))["by_source"] == {
        "instagram": {"views": 2, "enquiries": 1},
        "direct": {"views": 1, "enquiries": 1},
        "whatsapp": {"views": 0, "enquiries": 1}}


async def test_daily_is_14_india_dates_oldest_first_zero_filled():
    svc, db, clock = await make()
    await add_event(db, clock, "listing_view", ts=ago(clock, days=2))
    await add_event(db, clock, "listing_view", ts=ago(clock, days=2), anon="anon-2")
    await add_lead(db, clock, "c1", first_listing="L1", last_activity_days_ago=5)
    daily = (await activity(svc))["daily"]
    assert [d["date"] for d in daily] == [(datetime(2026, 1, 1) - timedelta(days=13 - i)).date().isoformat()
                                          for i in range(14)]
    by_date = {d["date"]: d for d in daily}
    assert by_date["2025-12-30"] == {"date": "2025-12-30", "views": 2, "enquiries": 0}
    assert by_date["2025-12-27"]["enquiries"] == 1
    assert sum(d["views"] for d in daily) == 2 and daily[-1] == {"date": "2026-01-01", "views": 0, "enquiries": 0}


async def test_daily_uses_ist_day_boundaries():
    svc, db, clock = await make()  # now = 2026-01-01 12:00 UTC = 17:30 IST
    ev = lambda ts, a: add_event(db, clock, "listing_view", anon=a, ts=ts)
    await ev(datetime(2025, 12, 31, 18, 29, 59), "a1")  # 23:59:59 IST on Dec 31
    await ev(datetime(2025, 12, 31, 18, 30, 0), "a2")   # 00:00:00 IST on Jan 1
    await ev(datetime(2025, 12, 18, 18, 29, 59), "a3")  # Dec 18 23:59:59 IST: before the 14-day window
    await ev(datetime(2025, 12, 18, 18, 30, 0), "a4")   # Dec 19 00:00 IST: first day of the window
    by_date = {d["date"]: d["views"] for d in (await activity(svc))["daily"]}
    assert by_date["2025-12-31"] == 1 and by_date["2026-01-01"] == 1 and by_date["2025-12-19"] == 1
    assert "2025-12-18" not in by_date and sum(by_date.values()) == 3
    # near IST midnight the current India date has already rolled over
    clock.t = datetime(2026, 1, 1, 18, 30, 0)
    daily = (await activity(svc))["daily"]
    assert daily[-1]["date"] == "2026-01-02" and daily[0]["date"] == "2025-12-20"


async def test_enquiry_day_uses_ist_date():
    svc, db, clock = await make()
    await add_lead(db, clock, "c1", first_listing="L1")
    db.get_collection("contacts").docs[-1]["created_at"] = datetime(2025, 12, 31, 19, 0, 0)  # Jan 1, 00:30 IST
    assert {d["date"]: d["enquiries"] for d in (await activity(svc))["daily"]}["2026-01-01"] == 1


async def test_feed_newest_first_with_privacy_safe_labels_and_text():
    svc, db, clock = await make()
    base = datetime(2025, 12, 31, 10, 0, 0)
    await add_event(db, clock, "listing_view", anon="secret-anon-A", source="instagram", ts=base)
    await add_event(db, clock, "listing_view", anon="secret-anon-B", source="instagram", ts=base + timedelta(minutes=1))
    await add_event(db, clock, "listing_view", anon="secret-anon-A", source="direct", ts=base + timedelta(minutes=2))
    await add_event(db, clock, "whatsapp_click", anon="secret-anon-B", source="whatsapp", ts=base + timedelta(minutes=3))
    await add_event(db, clock, "call_click", anon="secret-anon-C", ts=base + timedelta(minutes=4))
    await add_event(db, clock, "share", anon="secret-anon-C", ts=base + timedelta(minutes=5))
    out = await activity(svc)
    feed = out["feed"]
    assert [f["type"] for f in feed] == ["share", "call_click", "whatsapp_click", "view", "view", "view"]
    assert [f["text"] for f in feed] == [
        "Visitor 3 shared this listing", "Visitor 3 tapped Call", "Visitor 2 tapped WhatsApp",
        "Visitor 1 viewed this", "Visitor 2 viewed this from Instagram", "Visitor 1 viewed this from Instagram"]
    assert feed[0]["who"] == {"kind": "visitor", "label": "Visitor 3"}
    assert feed[-1]["source"] == "instagram" and feed[0]["source"] is None
    blob = json.dumps(out, default=str)
    assert "secret-anon" not in blob and "anon_id" not in blob and "user_agent" not in blob and "ip" not in feed[0]


async def test_visitor_numbers_are_stable_regardless_of_feed_limit():
    svc, db, clock = await make()
    base = datetime(2025, 12, 31, 10, 0, 0)
    for i, anon in enumerate(("a-first", "a-second", "a-third")):
        await add_event(db, clock, "listing_view", anon=anon, ts=base + timedelta(minutes=i))
    full = (await activity(svc))["feed"]
    short = (await activity(svc, limit=1))["feed"]
    assert full[0]["who"]["label"] == "Visitor 3" and short == full[:1]


async def test_visitor_who_became_a_lead_shows_the_lead_name():
    svc, db, clock = await make()
    await add_lead(db, clock, "c1", name="Priya Sharma", first_listing="L1")
    db.get_collection("contacts").docs[-1]["anon_ids"] = ["anon-priya"]
    base = datetime(2025, 12, 31, 10, 0, 0)
    await add_event(db, clock, "listing_view", anon="anon-priya", source="whatsapp", ts=base)             # via anon_ids
    await add_event(db, clock, "whatsapp_click", anon="anon-other", contact_id="c1", ts=base + timedelta(minutes=1))
    await add_event(db, clock, "inquiry", anon="anon-priya", ts=base + timedelta(minutes=2))
    await add_event(db, clock, "listing_view", anon="anon-stranger", ts=base + timedelta(minutes=3))
    feed = (await activity(svc))["feed"]
    assert [f["text"] for f in feed] == [
        "Visitor 1 viewed this", "Priya Sharma sent an enquiry", "Priya Sharma tapped WhatsApp",
        "Priya Sharma viewed this from WhatsApp"]
    assert feed[1]["type"] == "enquiry" and feed[1]["who"] == {"kind": "lead", "label": "Priya Sharma", "lead_id": "c1"}


async def test_feed_limit_and_cap():
    svc, db, clock = await make()
    for i in range(7):
        await add_event(db, clock, "listing_view", anon=f"anon-{i}", ts=datetime(2025, 12, 31, 10, i))
    assert len((await activity(svc, limit=3))["feed"]) == 3
    assert len((await activity(svc, limit=500))["feed"]) == 7  # clamped to the 100 max, only 7 exist


async def test_event_cap_keeps_newest_events(monkeypatch):
    svc, db, clock = await make()
    monkeypatch.setattr(act, "MAX_EVENTS", 4)
    for i in range(10):
        await add_event(db, clock, "listing_view", anon=f"anon-{i}", ts=datetime(2025, 12, 31, 10, i))
    out = await activity(svc)
    assert out["totals"]["views"] == 4
    assert out["feed"][0]["ts"] == datetime(2025, 12, 31, 10, 9)


async def test_people_ranked_hottest_first_and_scoped_to_this_listing():
    svc, db, clock = await make()
    await add_lead(db, clock, "cold", name="Cold Enquirer", first_listing="L1", base=0)
    await add_lead(db, clock, "hot", name="Hot Enquirer", first_listing="L1", base=50, bhk=2, lo=5_000_000, hi=9_000_000)
    await add_lead(db, clock, "viewer", name="Only Viewer", first_listing="L2", base=20)   # interacted, no enquiry here
    await add_lead(db, clock, "stranger", name="Stranger", first_listing="L2", base=90)    # unrelated
    await add_lead(db, clock, "other-agent", name="Other Agent Lead", first_listing="L1", agent="A2", base=99)
    await add_event(db, clock, "listing_view", anon="anon-v", contact_id="viewer")
    people = (await activity(svc))["people"]
    assert [p["lead_id"] for p in people] == ["hot", "viewer", "cold"]
    assert [p["temperature"] for p in people] == ["hot", "warm", "cold"]
    assert people[0]["name"] == "Hot Enquirer" and people[0]["score"] == 50
    assert people[0]["requirement_line"] and set(people[0]) == {
        "lead_id", "name", "temperature", "score", "requirement_line", "last_activity_at"}


async def test_people_capped_at_ten():
    svc, db, clock = await make()
    for i in range(13):
        await add_lead(db, clock, f"c{i:02d}", name=f"Lead {i}", first_listing="L1", base=i)
    people = (await activity(svc))["people"]
    assert len(people) == 10 and people[0]["lead_id"] == "c12"


async def test_activity_does_not_change_other_reads():
    svc, db, clock = await make()
    await add_view(db, clock, "L1", "anon-1")
    before = await svc.performance("A1")
    await activity(svc)
    assert await svc.performance("A1") == before
