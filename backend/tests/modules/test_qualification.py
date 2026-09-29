"""Service-level tests: enquiry capture, lead detail, drafts, follow-ups, /today."""
from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote, urlparse

import pytest

from app.modules.tracking.schemas import DraftIn, StageUpdate
from app.modules.tracking.service import TrackingError

from .qual_helpers import BROWSER, ev, inquiry, lead_id, make

pytestmark = pytest.mark.asyncio

MSG = "2bhk under 90 lakh, need it next month, home loan"


# ---------- enquiry capture ----------

async def test_old_body_still_works_and_defaults_from_listing():
    svc, db, _ = await make()
    assert await svc.capture_inquiry(inquiry()) == {"received": True, "new_lead": True}
    d = await svc.lead_detail("A1", await lead_id(svc))
    assert d["requirement"] == {"bhk": 2.0, "budget_min_inr": None, "budget_max_inr": None, "timeline": None,
                                "financing": None, "localities": ["Baner"], "source": "inferred"}
    assert d["requirement_line"] == "2 BHK · Baner"


async def test_no_listing_no_message_means_no_requirement():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(listing_id=None))
    d = await svc.lead_detail("A1", await lead_id(svc))
    assert d["requirement"] is None and d["requirement_line"] is None
    assert d["matches"] == []
    assert "No requirement shared yet." in d["ai_summary"]


async def test_inferred_from_message():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(message=MSG))
    r = (await svc.lead_detail("A1", await lead_id(svc)))["requirement"]
    assert (r["bhk"], r["budget_min_inr"], r["budget_max_inr"]) == (2, None, 9_000_000)
    assert r["timeline"] == "1_3_months" and r["financing"] == "home_loan"
    assert r["localities"] == ["Baner"] and r["source"] == "inferred"


async def test_stated_beats_inferred_and_marks_mixed():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(message=MSG, bhk=3, budget_min_inr=8_000_000, budget_max_inr=9_500_000,
                                      timeline="now"))
    r = (await svc.lead_detail("A1", await lead_id(svc)))["requirement"]
    assert r["bhk"] == 3 and (r["budget_min_inr"], r["budget_max_inr"]) == (8_000_000, 9_500_000)
    assert r["timeline"] == "now" and r["financing"] == "home_loan"  # financing still inferred
    assert r["source"] == "mixed"


async def test_all_stated_source():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(listing_id=None, bhk=2, budget_max_inr=5_000_000, budget_min_inr=0,
                                      timeline="exploring", financing="undecided"))
    assert (await svc.lead_detail("A1", await lead_id(svc)))["requirement"]["source"] == "stated"


async def test_reenquiry_merges_stated_beats_inferred_newer_stated_wins():
    svc, _, clock = await make()
    await svc.capture_inquiry(inquiry(bhk=3))
    clock.advance(days=1)
    res = await svc.capture_inquiry(inquiry(anon_id="anon-visitor-2", message="really want 2 bhk, home loan",
                                            budget_max_inr=9_000_000))
    assert res["new_lead"] is False
    r = (await svc.lead_detail("A1", await lead_id(svc)))["requirement"]
    assert r["bhk"] == 3  # inferred 2 does not beat stated 3
    assert r["financing"] == "home_loan" and r["budget_max_inr"] == 9_000_000
    clock.advance(days=1)
    await svc.capture_inquiry(inquiry(anon_id="anon-visitor-2", bhk=2, budget_max_inr=8_500_000))
    r = (await svc.lead_detail("A1", await lead_id(svc)))["requirement"]
    assert r["bhk"] == 2 and r["budget_max_inr"] == 8_500_000  # newer stated wins
    await svc.capture_inquiry(inquiry(anon_id="anon-visitor-2", message="budget 60 lakh"))
    assert (await svc.lead_detail("A1", await lead_id(svc)))["requirement"]["budget_max_inr"] == 8_500_000


async def test_reenquiry_fills_gaps_from_newer_inferred_only():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(message="under 90 lakh"))
    await svc.capture_inquiry(inquiry(message="under 80 lakh, asap"))
    r = (await svc.lead_detail("A1", await lead_id(svc)))["requirement"]
    assert r["budget_max_inr"] == 8_000_000 and r["timeline"] == "now"  # newer inferred replaced older inferred


async def test_listing_of_another_agent_gives_no_defaults():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(listing_id="L7"))  # belongs to A2
    assert (await svc.lead_detail("A1", await lead_id(svc)))["requirement"] is None


async def test_list_items_have_requirement_line():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(message="2bhk 80-90L in 3 months"))
    line = (await svc.list_leads("A1"))[0]["requirement_line"]
    assert line == "2 BHK · 80L-90L · Baner · 1-3 months"


# ---------- matches ----------

async def test_matches_are_owner_scoped_live_only_sorted():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(bhk=2, budget_min_inr=8_000_000, budget_max_inr=9_000_000))
    m = (await svc.lead_detail("A1", await lead_id(svc)))["matches"]
    ids = [x["listing_id"] for x in m]
    assert ids == ["L1", "L4", "L3"]  # L2 (Wakad, 70L) < 40%, L5 draft, L6 rent, L7 other agent
    assert [x["match_pct"] for x in m] == [100, 100, 45]
    assert m[0]["title"] == "2BHK in Baner" and m[0]["price_inr"] == 8_500_000 and m[0]["locality"] == "Baner"
    assert any("within budget" in r for r in m[0]["reasons"])
    assert "L7" not in ids


async def test_matches_rent_intent_from_message_without_listing():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(listing_id=None, message="2bhk for rent in Baner under 40000"))
    d = await svc.lead_detail("A1", await lead_id(svc))
    assert [x["listing_id"] for x in d["matches"]] == ["L6"] or d["matches"] == []


# ---------- summary & next action ----------

async def test_ai_summary_uses_only_real_facts():
    svc, _, clock = await make()
    for _ in range(3):
        await svc.track_event(ev("listing_view"), BROWSER)
        clock.advance(minutes=1)
    await svc.track_event(ev("whatsapp_click"), BROWSER)
    await svc.capture_inquiry(inquiry(message=MSG))
    s = (await svc.lead_detail("A1", await lead_id(svc)))["ai_summary"]
    assert s == ("Wants a 2 BHK under 90L in Baner within 1-3 months, on a home loan. "
                 "Viewed the 2BHK in Baner listing 3 times and tapped WhatsApp. Came in via whatsapp. "
                 "Likely ready for a site visit.")


async def test_ai_summary_range_and_closed():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(listing_id=None, bhk=2, budget_min_inr=8_000_000, budget_max_inr=9_000_000,
                                      timeline="exploring", source=None))
    lid = await lead_id(svc)
    s = (await svc.lead_detail("A1", lid))["ai_summary"]
    assert s.startswith("Wants a 2 BHK around 80L-90L but is just looking for now.")
    assert "Came in via" not in s and s.endswith("Showing interest, worth a follow-up.")
    out = await svc.update_stage("A1", lid, StageUpdate(stage="won"))
    assert out["ai_summary"].endswith("Deal closed.")


async def test_next_action_rules_in_order():
    svc, _, clock = await make()
    await svc.capture_inquiry(inquiry(listing_id=None))
    lid = await lead_id(svc)
    assert (await svc.lead_detail("A1", lid))["next_action"]["type"] == "follow_up"  # warm, fresh, no timeline
    await svc.capture_inquiry(inquiry(listing_id=None, phone="9123456780", anon_id="anon-visitor-2", timeline="now"))
    assert (await svc.lead_detail("A1", await lead_id(svc, idx=1)))["next_action"]["type"] == "whatsapp"
    clock.advance(hours=25)
    na = (await svc.lead_detail("A1", lid))["next_action"]
    assert na["type"] == "call" and "respond within a day" in na["reason"]  # beats timeline rule
    await svc.track_event(ev("whatsapp_click"), BROWSER)
    await svc.track_event(ev("call_click"), BROWSER)
    d = await svc.lead_detail("A1", lid)
    assert d["temperature"] == "hot" and d["next_action"]["type"] == "schedule_visit"
    d = await svc.update_stage("A1", lid, StageUpdate(stage="site_visit"))
    assert d["next_action"] == {"type": "follow_up", "reason": "Confirm the visit"}  # beats hot
    d = await svc.update_stage("A1", lid, StageUpdate(stage="lost"))
    assert d["next_action"]["type"] == "follow_up" and "lost" in d["next_action"]["reason"]


async def test_next_action_contacted_lead_not_called():
    svc, _, clock = await make()
    await svc.capture_inquiry(inquiry(listing_id=None))
    lid = await lead_id(svc)
    await svc.update_stage("A1", lid, StageUpdate(stage="contacted"))
    clock.advance(hours=30)
    assert (await svc.lead_detail("A1", lid))["next_action"]["type"] == "follow_up"


# ---------- follow-up scheduling ----------

async def test_contacted_sets_due_in_two_days_and_overdue_later():
    svc, _, clock = await make()
    await svc.capture_inquiry(inquiry())
    lid = await lead_id(svc)
    assert (await svc.lead_detail("A1", lid))["follow_up"] == {"due_at": None, "overdue": False}
    d = await svc.update_stage("A1", lid, StageUpdate(stage="contacted"))
    assert d["follow_up"] == {"due_at": clock() + timedelta(days=2), "overdue": False}
    clock.advance(days=2, minutes=1)
    assert (await svc.lead_detail("A1", lid))["follow_up"]["overdue"] is True
    d = await svc.update_stage("A1", lid, StageUpdate(note="spoke, call back"))  # note does not reschedule
    assert d["follow_up"]["overdue"] is True
    d = await svc.update_stage("A1", lid, StageUpdate(stage="won"))
    assert d["follow_up"]["overdue"] is False  # closed leads are never overdue


async def test_explicit_follow_up_at_wins_and_can_be_set_without_stage():
    svc, _, clock = await make()
    await svc.capture_inquiry(inquiry())
    lid = await lead_id(svc)
    when = clock() + timedelta(days=5)
    d = await svc.update_stage("A1", lid, StageUpdate(stage="contacted", follow_up_at=when))
    assert d["follow_up"]["due_at"] == when
    when2 = clock() + timedelta(days=1)
    d = await svc.update_stage("A1", lid, StageUpdate(follow_up_at=when2))
    assert d["follow_up"]["due_at"] == when2 and d["stage"] == "contacted"


async def test_stage_update_needs_something():
    with pytest.raises(ValueError):
        StageUpdate()


# ---------- drafts ----------

async def _hot_lead(svc, clock):
    await svc.capture_inquiry(inquiry(bhk=2, budget_min_inr=8_000_000, budget_max_inr=9_000_000, timeline="now"))
    return await lead_id(svc)


async def test_draft_uses_real_facts_and_wa_url():
    svc, db, clock = await make()
    await db.get_collection("listings").insert_one(
        {"_id": "L8", "id": "L8", "agent_id": "A1", "status": "live", "transaction": "sale", "property_type": "apartment",
         "title": "Sunny 2BHK Baner Road", "price_inr": 8_200_000, "city": "Pune", "locality": "Baner", "bhk": 2})
    lid = await _hot_lead(svc, clock)
    clock.advance(days=2)
    out = await svc.followup_draft("A1", lid)
    msg = out["message"]
    assert out["language"] == "en"
    assert msg.startswith("Hi Amit,") and "2BHK in Baner" in msg
    assert "80L-90L" in msg and "2 BHK" in msg
    assert "Sunny 2BHK Baner Road" in msg and "82L" in msg  # a different matching listing, real price
    assert "site visit" in msg  # timeline now
    assert "No reply for 2 days" in out["based_on"] and "Budget 80L-90L" in out["based_on"]
    assert "New listing in Baner within budget" in out["based_on"]
    u = urlparse(out["whatsapp_url"])
    assert u.netloc == "wa.me" and u.path == "/919876543210"
    assert unquote(parse_qs(u.query)["text"][0]) == msg
    assert " " not in out["whatsapp_url"] and "\n" not in out["whatsapp_url"]


async def test_draft_without_facts_is_still_polite():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(listing_id=None))
    out = await svc.followup_draft("A1", await lead_id(svc))
    assert out["message"].startswith("Hi Amit, thanks for reaching out.")
    assert out["based_on"] == []


async def test_draft_languages_and_fallback():
    svc, _, clock = await make()
    lid = await _hot_lead(svc, clock)
    hi = await svc.followup_draft("A1", lid, DraftIn(language="hi"))
    assert hi["language"] == "hi" and "नमस्ते Amit" in hi["message"] and "80L-90L" in hi["message"]
    mr = await svc.followup_draft("A1", lid, DraftIn(language="mr"))
    assert mr["language"] == "mr" and "नमस्कार Amit" in mr["message"]
    from app.modules.tracking.followup import build_draft
    fb = build_draft({"name": "A", "stage": "new", "last_activity_at": clock()}, None, None, None, "fr", clock())
    assert fb["language"] == "en"


async def test_llm_polish_cannot_change_facts():
    async def good(msg, lang):
        return "Namaste! " + msg

    async def bad(msg, lang):
        return "Hi Amit, are you still interested? Budget 50L."  # drops title/budget facts

    async def boom(msg, lang):
        raise RuntimeError("llm down")

    svc, _, clock = await make(polish=good)
    lid = await _hot_lead(svc, clock)
    assert (await svc.followup_draft("A1", lid))["message"].startswith("Namaste! Hi Amit,")
    for fn in (bad, boom):
        svc.polish = fn
        plain = (await svc.followup_draft("A1", lid))["message"]
        assert plain.startswith("Hi Amit,") and "80L-90L" in plain


# ---------- /today ----------

async def _today_fixture():
    svc, db, clock = await make()
    # 1: hot, fresh, uncontacted
    await svc.capture_inquiry(inquiry(bhk=2, budget_min_inr=8_000_000, budget_max_inr=9_000_000))
    await svc.track_event(ev("whatsapp_click"), BROWSER)
    # 2: warm, contacted, follow-up due today
    await svc.capture_inquiry(inquiry(name="Sita Rao", phone="9123456780", anon_id="anon-visitor-2", listing_id=None))
    # 3: contacted, follow-up tomorrow
    await svc.capture_inquiry(inquiry(name="Ravi Nair", phone="9123456781", anon_id="anon-visitor-3", listing_id=None))
    # 4: site visit
    await svc.capture_inquiry(inquiry(name="Meena Iyer", phone="9123456782", anon_id="anon-visitor-4", listing_id=None))
    # 5: other agent's lead
    await svc.capture_inquiry(inquiry(agent_slug="priya", name="Other", phone="9123456783", anon_id="anon-visitor-5",
                                      listing_id="L7"))
    ids = {l["name"]: l["id"] for l in await svc.list_leads("A1")}
    await svc.update_stage("A1", ids["Sita Rao"], StageUpdate(stage="contacted", follow_up_at=clock() + timedelta(hours=3)))
    await svc.update_stage("A1", ids["Ravi Nair"], StageUpdate(stage="contacted", follow_up_at=clock() + timedelta(days=1)))
    await svc.update_stage("A1", ids["Meena Iyer"], StageUpdate(stage="site_visit"))
    return svc, db, clock, ids


async def test_today_counts_and_lists():
    svc, _, clock, ids = await _today_fixture()
    t = await svc.today("A1")
    assert t["counts"] == {"new_enquiries_24h": 4, "hot": 1, "site_visits": 1, "follow_ups_due": 1, "uncontacted": 1}
    assert [h["name"] for h in t["hot_buyers"]] == ["Amit Kumar"]
    hb = t["hot_buyers"][0]
    assert hb["requirement_line"] == "2 BHK · 80L-90L · Baner" and hb["temperature"] == "hot"
    assert hb["top_match"] == {"title": "2BHK in Baner", "match_pct": 100}
    assert [f["name"] for f in t["follow_ups"]] == ["Sita Rao"]
    assert t["follow_ups"][0]["overdue"] is False and t["follow_ups"][0]["reason"] == "Follow-up due today"
    assert t["headline"] == "1 buyer hasn't been contacted today."


async def test_today_overdue_ordering_and_caught_up():
    svc, _, clock, ids = await _today_fixture()
    clock.advance(days=3)
    await svc.update_stage("A1", ids["Amit Kumar"], StageUpdate(stage="lost"))
    t = await svc.today("A1")
    assert [f["name"] for f in t["follow_ups"]] == ["Sita Rao", "Ravi Nair"]  # oldest due first
    assert all(f["overdue"] for f in t["follow_ups"])
    assert t["follow_ups"][0]["reason"] == "Follow-up overdue by 2 days"
    assert t["counts"]["follow_ups_due"] == 2 and t["counts"]["uncontacted"] == 0
    assert t["counts"]["new_enquiries_24h"] == 0 and t["counts"]["hot"] == 0
    assert t["headline"] == "2 follow-ups are due today."
    for n in ("Sita Rao", "Ravi Nair"):
        await svc.update_stage("A1", ids[n], StageUpdate(stage="won"))
    t = await svc.today("A1")
    assert t["headline"] == "You're all caught up." and t["follow_ups"] == []


async def test_today_caps_and_hot_ordering():
    svc, _, clock = await make()
    for n in range(7):
        await svc.capture_inquiry(inquiry(name=f"Buyer {n}", phone=f"91234567{n:02d}", anon_id=f"anon-visitor-{n}"))
        for _ in range(n + 1):
            await svc.track_event(ev("whatsapp_click", anon=f"anon-visitor-{n}"), BROWSER)
    t = await svc.today("A1")
    assert len(t["hot_buyers"]) == 5 and t["counts"]["hot"] == 7
    scores = [h["score"] for h in t["hot_buyers"]]
    assert scores == sorted(scores, reverse=True) and t["hot_buyers"][0]["name"] == "Buyer 6"
    for l in await svc.list_leads("A1"):
        await svc.update_stage("A1", l["id"], StageUpdate(stage="contacted", follow_up_at=clock() - timedelta(hours=1)))
    t = await svc.today("A1")
    assert len(t["follow_ups"]) == 7 and t["counts"]["follow_ups_due"] == 7
    for n in range(7, 13):
        await svc.capture_inquiry(inquiry(name=f"Extra {n}", phone=f"91234567{n:02d}", anon_id=f"anon-visitor-{n}"))
    for l in await svc.list_leads("A1"):
        await svc.update_stage("A1", l["id"], StageUpdate(stage="contacted", follow_up_at=clock() - timedelta(hours=1)))
    t = await svc.today("A1")
    assert len(t["follow_ups"]) == 10 and t["counts"]["follow_ups_due"] == 13


async def test_today_headline_hot_and_empty():
    svc, _, _ = await make()
    assert (await svc.today("A1"))["headline"] == "You're all caught up."
    assert (await svc.today("A1"))["counts"]["new_enquiries_24h"] == 0


# ---------- owner isolation ----------

async def test_owner_isolation_for_all_new_reads_and_writes():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry())
    lid = await lead_id(svc)
    with pytest.raises(TrackingError) as e:
        await svc.followup_draft("A2", lid)
    assert e.value.status_code == 404
    with pytest.raises(TrackingError):
        await svc.update_stage("A2", lid, StageUpdate(follow_up_at=datetime(2030, 1, 1)))
    t = await svc.today("A2")
    assert t["counts"] == {"new_enquiries_24h": 0, "hot": 0, "site_visits": 0, "follow_ups_due": 0, "uncontacted": 0}
    assert (await svc.lead_detail("A1", lid))["follow_up"]["due_at"] is None
