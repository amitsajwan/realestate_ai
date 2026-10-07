"""WhatsApp buyer assistant: routing, grounded answers, leads, STOP, the 24-hour window, dry run, notifications, secrets. No network."""
import logging
from datetime import timedelta

import httpx
import pytest

from app.modules.notifications.service import NotificationError, NotificationService
from app.modules.whatsapp import adapters, lang as L
from app.modules.whatsapp.config import load

from .helpers import BUYER, LISTING, NOW, PID, TOKEN, SECRET, GraphRecorder, cfg, later, make, message, say, value

pytestmark = pytest.mark.asyncio


def bot_texts(conv):
    return [m["text"] for m in conv["messages"] if m["role"] == "bot"]


async def conv_of(db, pid=PID, wa=BUYER):
    return await db.get_collection("whatsapp_conversations").find_one({"_id": f"{pid}:{wa}"})


async def add_link(db, code, kind="listing", ref="L1", agent="AGENT2", sample=False, title="2 BHK in Kharadi"):
    await db.get_collection("interest_links").insert_one({"_id": code, "code": code, "kind": kind, "ref": ref, "agent_id": agent,
                                                          "channel": "website", "sample": sample, "title": title})


# ---- config ------------------------------------------------------------------------------------------------------
def test_config_defaults_are_safe_and_secrets_hidden(monkeypatch):
    for k in ("WHATSAPP_ENABLED", "WHATSAPP_DRY_RUN", "WHATSAPP_NUMBER_AGENTS", "WHATSAPP_GRAPH_VERSION"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", TOKEN)
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SECRET)
    c = load()
    assert c.enabled is False and c.dry_run is True and c.graph_version == "v23.0" and c.number_agents == {}
    assert TOKEN not in repr(c) and SECRET not in repr(c)
    monkeypatch.setenv("WHATSAPP_NUMBER_AGENTS", '{"111": "AG1"}')
    monkeypatch.setenv("WHATSAPP_DRY_RUN", "false")
    monkeypatch.setenv("WHATSAPP_GRAPH_VERSION", "v25.0")
    c = load()
    assert c.number_agents == {"111": "AG1"} and c.dry_run is False and c.graph_version == "v25.0"
    monkeypatch.setenv("WHATSAPP_NUMBER_AGENTS", "not json")
    monkeypatch.setenv("WHATSAPP_GRAPH_VERSION", "latest")
    assert load().number_agents == {} and load().graph_version == "v23.0"


# ---- routing ------------------------------------------------------------------------------------------------------
async def test_routes_to_the_owner_when_nothing_names_an_agent():
    svc, db, _, _ = make()
    r = await say(svc, "Hi")
    assert r["agent_id"] == "OWNER" and (await conv_of(db))["routed_by"] == "owner"


async def test_an_agents_own_number_routes_to_him_even_with_an_interest_code():
    svc, db, _, _ = make(cfg(number_agents={PID: "AGENT9"}))
    await add_link(db, "abcd234")
    r = await say(svc, "Hi, I am interested in 2 BHK in Kharadi (ref abcd234)")
    assert r["agent_id"] == "AGENT9"


async def test_an_interest_code_routes_to_the_listing_agent_and_records_the_interest():
    svc, db, _, _ = make()
    await add_link(db, "abcd234")
    r = await say(svc, "Hi, I am interested in 2 BHK in Kharadi (ref abcd234)")
    assert r["agent_id"] == "AGENT2"
    conv = await conv_of(db)
    assert conv["routed_by"] == "interest_code" and conv["context"]["listing_id"] == "L1"
    ev = db.get_collection("interest_events").docs
    assert ev and ev[0]["code"] == "abcd234" and ev[0]["type"] == "interest"
    # the /i/<code> form and 'interested in <code>' work too; an unknown code falls back to the owner
    assert adapters.codes_in("see https://x.test/i/abcd234 please") == ["abcd234"]
    assert adapters.codes_in("interested in abcd234") == ["abcd234"]
    svc2, db2, _, _ = make()
    assert (await say(svc2, "ref zzzz999"))["agent_id"] == "OWNER"


async def test_a_sample_home_code_goes_to_the_owner():
    svc, db, _, _ = make()
    await add_link(db, "smpq234", ref="kharadi-2bhk-ready", agent="AGENT2", sample=True, title="SAMPLE: 2 BHK")
    assert (await say(svc, "I am interested (ref smpq234)"))["agent_id"] == "OWNER"


# ---- grounded answers ---------------------------------------------------------------------------------------------
async def test_a_question_about_the_home_is_answered_from_its_facts_only():
    svc, db, _, _ = make()
    await db.get_collection("listings").insert_one(dict(LISTING))
    await add_link(db, "abcd234")
    r = await say(svc, "Hi, I am interested in 2 BHK in Kharadi (ref abcd234). What is the price?")
    assert "₹85 Lakh" in r["reply"]
    r = await say(svc, "Is there a swimming pool?")
    assert "do not have" in r["reply"] and "pool" not in r["reply"].lower().split("do not have")[0]


async def test_a_sample_home_is_labelled_and_only_the_sample_figure_is_given():
    svc, db, _, _ = make()
    await add_link(db, "smpq234", ref="kharadi-2bhk-ready", sample=True, title="SAMPLE: 2 BHK")
    r = await say(svc, "ref smpq234 what is the price?")
    assert "sample price figure" in r["reply"]
    r = await say(svc, "is it available?")
    assert "not available for sale" in r["reply"]


async def test_hindi_buyers_get_hindi_questions_and_notice():
    svc, db, _, _ = make()
    r = await say(svc, "मुझे 2 BHK चाहिए, बजट 80 लाख है")
    # a budget in lakh means buying (chat v2 infers it), so the next question is the area, in Hindi
    assert "आपको कौन सा इलाका सबसे ज़्यादा पसंद है?" in r["reply"] and "किराए पर लेना?" not in r["reply"]
    assert "सूचना:" in r["reply"] and "STOP" in r["reply"]
    assert "Are you looking" not in r["reply"]
    conv = await conv_of(db)
    assert conv["language"] == "hi" and conv["data"]["bhk"] == 2 and conv["data"]["tx"] == "buy"
    r = await say(svc, "Kharadi")  # a short English answer keeps the conversation in Hindi
    assert "आप कब तक शिफ्ट होना चाहते हैं?" in r["reply"]


async def test_hinglish_and_marathi():
    svc, _, _, _ = make()
    r = await say(svc, "mujhe Wagholi mein 3 bhk chahiye")
    assert "Aap ghar kharidna chahte hain ya rent par lena?" in r["reply"]
    svc2, _, _, _ = make()
    r = await say(svc2, "मला खराडीत घर पाहिजे आहे, बजेट किती आहे ते सांगतो")
    assert "तुम्हाला" in r["reply"]


class Translator:
    def __init__(self, text):
        self.text, self.calls = text, 0

    async def json(self, system, user):
        self.calls += 1
        return {"text": self.text} if "Rewrite the TEXT" in system else None


async def test_a_vetted_english_answer_is_translated_only_through_the_checked_translator():
    svc, db, _, _ = make(llm=Translator("हर प्रोजेक्ट का RERA नंबर MahaRERA की वेबसाइट (maharera.maharashtra.gov.in) पर देखें।"))
    await say(svc, "नमस्ते")
    r = await say(svc, "RERA कैसे चेक करें?")
    # the translator's draft lacks the KB answer's names and so is rejected, or accepted when it keeps them; never an invented fact
    assert "RERA" in r["reply"] and "₹" not in r["reply"]


# ---- leads --------------------------------------------------------------------------------------------------------
async def test_the_buyer_becomes_one_lead_with_requirement_consent_and_a_single_notice():
    svc, db, _, _ = make()
    await say(svc, "Hi")
    await say(svc, "I want to buy a 2 BHK in Kharadi under 90 lakh")
    await say(svc, "In 1-3 months")
    leads = db.get_collection("contacts").docs
    assert len(leads) == 1
    lead = leads[0]
    assert lead["agent_id"] == "OWNER" and lead["phone"] == "+919876543210" and lead["source"] == "whatsapp" and lead["name"] == "Priya Sharma"
    assert lead["consent"]["basis"] == "buyer started the WhatsApp chat" and lead["consent"]["given_at"] == NOW
    req = lead["requirement"]
    assert req["bhk"] == 2 and req["budget_max_inr"] == 9_000_000 and req["localities"] == ["Kharadi"] and req["timeline"] == "1_3_months"
    assert "WhatsApp enquiry (buy)" in lead["whatsapp"]["summary"] and "Kharadi" in lead["whatsapp"]["summary"]
    conv = await conv_of(db)
    assert sum("Reply STOP" in t for t in bot_texts(conv)) == 1
    assert not any("mobile number" in t for t in bot_texts(conv))  # never asks for the number we already have
    notes = db.get_collection("notifications").docs
    assert [n["kind"] for n in notes] == ["new_whatsapp_lead"] and notes[0]["agent_id"] == "OWNER" and notes[0]["read"] is False
    assert "9876543210" not in notes[0]["summary"]


async def test_an_existing_website_lead_with_the_same_number_is_updated_not_duplicated():
    svc, db, _, _ = make()
    await db.get_collection("contacts").insert_one({"_id": "C1", "agent_id": "OWNER", "phone": "+919876543210", "name": "Priya", "stage": "contacted",
                                                    "consent": {"given_at": NOW - timedelta(days=3)}, "requirement": None, "anon_ids": ["x"]})
    await say(svc, "I want a 3 BHK in Wagholi")
    leads = db.get_collection("contacts").docs
    assert len(leads) == 1 and leads[0]["stage"] == "contacted" and leads[0]["requirement"]["bhk"] == 3
    assert "whatsapp:" + BUYER in leads[0]["anon_ids"]
    assert db.get_collection("notifications").docs == []


async def test_an_unanswerable_question_notifies_the_agent_once():
    svc, db, _, _ = make()
    await say(svc, "Hi")
    await say(svc, "Which school is nearest to Sky Heights tower B?")
    await say(svc, "And which bank is nearest to Sky Heights tower B?")
    kinds = [n["kind"] for n in db.get_collection("notifications").docs]
    assert kinds.count("whatsapp_needs_you") == 1


# ---- STOP, media, window, dry run --------------------------------------------------------------------------------
async def test_stop_opts_out_confirms_once_then_stays_silent_until_start():
    svc, db, _, _ = make()
    await say(svc, "Hi")
    r = await say(svc, "STOP")
    assert r["status"] == "stopped" and "START" in r["reply"]
    lead = db.get_collection("contacts").docs[0]
    assert lead["whatsapp"]["opted_out"] is True and lead["consent"]["withdrawn_at"] == NOW
    r = await say(svc, "hello?")
    assert r["status"] == "opted_out" and r["reply"] is None and r["send_status"] is None
    r = await say(svc, "START")
    assert r["status"] == "restarted" and r["reply"]
    lead = db.get_collection("contacts").docs[0]
    assert lead["whatsapp"]["opted_out"] is False and lead["consent"]["withdrawn_at"] is None
    assert (await say(svc, "unsubscribe"))["status"] == "stopped"


async def test_media_and_location_get_a_friendly_text_and_reactions_get_nothing():
    svc, _, _, _ = make()
    m = message(mid="wamid.img", mtype="image", extra={"image": {"id": "MEDIA1", "mime_type": "image/jpeg"}})
    assert await svc.claim(m, value([m]))
    r = await svc.handle(m, value([m]))
    assert "only read text" in r["reply"]
    m = message(mid="wamid.loc", mtype="location", extra={"location": {"latitude": 18.55, "longitude": 73.94}})
    await svc.claim(m, value([m]))
    assert "area name" in (await svc.handle(m, value([m])))["reply"]
    m = message(mid="wamid.rx", mtype="reaction", extra={"reaction": {"message_id": "wamid.out1", "emoji": "👍"}})
    await svc.claim(m, value([m]))
    assert (await svc.handle(m, value([m])))["reply"] is None


async def test_dry_run_records_the_reply_and_calls_nothing():
    svc, db, rec, _ = make(cfg(dry_run=True))
    r = await say(svc, "Hi")
    assert r["send_status"] == "dry_run" and rec.requests == []
    out = [m for m in db.get_collection("whatsapp_messages").docs if m["direction"] == "out"]
    assert len(out) == 1 and out[0]["status"] == "dry_run" and out[0]["text"] == r["reply"]


async def test_live_mode_marks_read_and_sends_through_the_messages_endpoint():
    svc, db, rec, _ = make(cfg(dry_run=False))
    r = await say(svc, "Hi", mid="wamid.live1")
    assert r["send_status"] == "sent"
    urls = {str(q.url) for q in rec.requests}
    assert urls == {f"https://graph.facebook.com/v23.0/{PID}/messages"}
    assert all(q.headers["authorization"] == f"Bearer {TOKEN}" for q in rec.requests)
    assert all(TOKEN not in str(q.url) for q in rec.requests)
    reads = [q for q in rec.requests if b'"status": "read"' in q.content or b'"status":"read"' in q.content]
    assert len(reads) == 1
    sends = rec.sends()
    assert len(sends) == 1 and sends[0]["to"] == BUYER and sends[0]["messaging_product"] == "whatsapp" and sends[0]["text"]["body"] == r["reply"]
    out = [m for m in db.get_collection("whatsapp_messages").docs if m["direction"] == "out"]
    assert out[0]["status"] == "sent" and out[0]["_id"].startswith("wamid.out")
    await svc.status_update({"id": out[0]["_id"], "status": "delivered"})
    assert db.get_collection("whatsapp_messages").docs[-1]["delivery"] == "delivered"


async def test_no_reply_outside_the_24_hour_window():
    svc, db, rec, _ = make(cfg(dry_run=False))
    r = await say(svc, "Hi", ts=NOW - timedelta(hours=25))  # a webhook delivered (or retried) more than a day late
    assert r["send_status"] == "refused" and rec.sends() == []
    out = [m for m in db.get_collection("whatsapp_messages").docs if m["direction"] == "out"][0]
    assert "24-hour" in out["error"]
    assert svc.in_window({"last_inbound_at": NOW - timedelta(hours=23)}, NOW) and not svc.in_window({"last_inbound_at": None}, NOW)


async def test_an_old_message_does_not_reopen_the_window_but_a_new_one_does():
    svc, db, rec, clock = make(cfg(dry_run=False))
    await say(svc, "Hi")
    later(clock, hours=30)
    r = await say(svc, "2 bhk", ts=NOW)  # delayed copy of an old message
    assert r["send_status"] == "refused"
    r = await say(svc, "3 bhk")  # sent now
    assert r["send_status"] == "sent"


async def test_tokens_never_reach_logs_or_stored_errors(caplog):
    caplog.set_level(logging.DEBUG)
    rec = GraphRecorder(fail={"error": {"message": f"Invalid OAuth access token {TOKEN} (access_token={TOKEN})", "code": 190}}, status=401)
    svc, db, _, _ = make(cfg(dry_run=False), recorder=rec)
    r = await say(svc, "Hi")
    assert r["send_status"] == "failed"
    out = [m for m in db.get_collection("whatsapp_messages").docs if m["direction"] == "out"][0]
    assert "190" in out["error"] and TOKEN not in out["error"]
    assert TOKEN not in caplog.text and SECRET not in caplog.text
    rec2 = GraphRecorder(raise_exc=httpx.ConnectError(f"boom {TOKEN}"))
    svc2, db2, _, _ = make(cfg(dry_run=False), recorder=rec2)
    await say(svc2, "Hi")
    out2 = [m for m in db2.get_collection("whatsapp_messages").docs if m["direction"] == "out"][0]
    assert out2["status"] == "failed" and TOKEN not in out2["error"] and TOKEN not in caplog.text


async def test_claim_is_idempotent():
    svc, db, _, _ = make()
    m = message("Hi", mid="wamid.same")
    assert await svc.claim(m, value([m])) is True
    assert await svc.claim(m, value([m])) is False
    assert await svc.claim({"from": BUYER}, value([])) is False


async def test_studio_conversations_are_agent_scoped_and_mask_the_number():
    svc, db, _, _ = make()
    await say(svc, "Hi")
    await say(svc, "I want a 2 BHK in Kharadi")
    mine = await svc.conversations("OWNER")
    assert len(mine) == 1 and await svc.conversations("SOMEONE_ELSE") == []
    c = mine[0]
    assert c["channel"] == "whatsapp" and c["name"] == "Priya Sharma" and "9876543210" not in c["phone"] and c["phone"].endswith("10")
    assert "Kharadi" in c["summary"] and c["lead_id"] and c["window_open"] is True
    assert [m["role"] for m in c["messages"]] == ["user", "bot", "user", "bot"]


async def test_the_conversation_keeps_only_the_last_20_messages():
    svc, db, _, _ = make()
    for i in range(14):
        await say(svc, f"what is carpet area {i}?")
    assert len((await conv_of(db))["messages"]) == 20


# ---- notifications ------------------------------------------------------------------------------------------------
async def test_notifications_are_agent_scoped_and_can_be_marked_read():
    svc, db, _, _ = make()
    await say(svc, "Hi")
    ns = NotificationService(db, now=lambda: NOW)
    res = await ns.list("OWNER")
    assert res["unread"] == 1 and res["items"][0]["kind"] == "new_whatsapp_lead"
    assert (await ns.list("OTHER")) == {"items": [], "unread": 0}
    nid = res["items"][0]["id"]
    with pytest.raises(NotificationError):
        await ns.mark_read("OTHER", nid)
    assert (await ns.mark_read("OWNER", nid))["read"] is True
    assert (await ns.list("OWNER"))["unread"] == 0
    assert (await ns.list("OWNER", unread_only=True))["items"] == []


def test_language_helpers():
    assert L.sticky("hi", "en", "Buy") == "hi"
    assert L.sticky("hi", "en", "I would like to buy a flat") == "en"
    text, left = L.localise_fixed("Got it: buy. Which area are you most interested in?", "mr")
    assert text.startswith("ठीक आहे: buy.") and "तुम्हाला कोणता भाग" in text and not left
    _, left = L.localise_fixed("Every project above the RERA limits must be registered. Which area are you most interested in?", "hi")
    assert left
