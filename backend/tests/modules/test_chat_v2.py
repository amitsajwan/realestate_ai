"""Chat v2: whole scripted conversations (engine alone, and the service with a fake database, real tracking and real matching), with and
without a (fake) LLM. Each test reads like the conversation a buyer would have; the transcript helpers print it on failure."""
import re
from datetime import datetime

import pytest

from app.modules.chat import engine, phrases
from app.modules.chat.service import ChatService
from app.modules.tracking.service import TrackingService

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio
NOW = datetime(2026, 9, 30, 12, 0, 0)
SID = "session-v2-abcdef123456"
ASKS = {f: phrases.say("ask_" + f) for f in ("tx", "locality", "bhk", "budget", "timeline", "name")}
CONSENT = phrases.say("consent")
PHONE_ASK = re.compile(r"mobile number", re.I)


class FakeLLM:
    def __init__(self, reply=None):
        self.reply, self.calls = reply, 0

    async def json(self, system, user):
        self.calls += 1
        return self.reply


# ---- helpers ------------------------------------------------------------------------------------------------------
async def chat(d, msgs, llm=None, grounding=None, finder=None, whatsapp=False):
    """Plays the buyer's messages through the engine. Returns the transcript [(buyer, Turn)]."""
    out = []
    for m in msgs:
        out.append((m, await engine.turn(d, m, llm, grounding, finder=finder, whatsapp=whatsapp)))
    return out


def bot(transcript):
    return [t.reply for _, t in transcript]


def count(rx_or_text, texts):
    return sum(1 for t in texts if (rx_or_text.search(t) if hasattr(rx_or_text, "search") else rx_or_text in t))


def listing(_id, agent="A1", **over):
    base = {"_id": _id, "agent_id": agent, "status": "live", "visibility": "public", "transaction": "sale", "property_type": "apartment",
            "price_inr": 7_800_000, "city": "Pune", "locality": "Kharadi", "bhk": 2, "carpet_sqft": 780, "title": f"2 BHK in Kharadi {_id}",
            "published_at": NOW, "media": [{"url": f"https://img.test/{_id}.jpg", "kind": "image", "order": 0}]}
    return {**base, **over}


def service(listings=(), llm=None, extra_profiles=()):
    db = FakeDb()
    db.get_collection("agent_public_profiles").docs += [{"slug": "rahul", "is_public": True, "agent_id": "A1"}, *extra_profiles]
    db.get_collection("listings").docs += list(listings)
    return ChatService(db, TrackingService(db, now=lambda: NOW), llm, now=lambda: NOW), db


async def talk(s, msgs, context=None, sid=SID):
    out = []
    for m in msgs:
        out.append((m, await s.message(sid, "rahul", m, context=context)))
    return out


def replies(transcript):
    return [r["reply"] for _, r in transcript]


async def fake_finder(cards):
    async def find(req, exclude):
        find.calls.append((req, exclude))
        return list(cards)
    find.calls = []
    return find


# ---- 1. intent is inferred, known slots are never asked again ---------------------------------------------------------------
@pytest.mark.parametrize("msg,tx", [("2 BHK in Kharadi, budget 80 lakh", "buy"), ("need 3bhk under 1.2 crore", "buy"),
                                    ("2 bhk on rent in Wagholi", "rent"), ("looking for a flat, 25k per month", "rent"),
                                    ("how much deposit for a 1 bhk?", "rent"), ("I want to buy in Baner", "buy")])
async def test_intent_is_inferred_from_budget_and_rent_words(msg, tx):
    d = engine.new_data()
    t = (await chat(d, ["hi", msg]))[-1][1]
    assert d["tx"] == tx and ASKS["tx"] not in t.reply


async def test_a_rent_budget_per_month_is_understood_and_rent_quick_replies_are_offered():
    d = engine.new_data()
    await chat(d, ["hi", "Rent", "Kharadi", "2 BHK"])
    assert d["asked"] == "budget"
    t = (await chat(d, ["20,000-35,000/month"]))[-1][1]
    assert (d["budget_min"], d["budget_max"]) == (20_000, 35_000) and "20,000-35,000/month" in t.reply
    d2 = engine.new_data()
    t = (await chat(d2, ["hi", "rent", "Wagholi", "1 bhk"]))[-1][1]
    assert t.quick == engine.RENT_BUDGET_QUICK


async def test_the_live_test_conversation_never_asks_buy_or_rent_again_and_never_restarts_after_the_lead():
    """The conversation from the live test: budget first, name, number, then more questions."""
    d = engine.new_data(localise=True)
    find = await fake_finder([{"id": "L2", "title": "2 BHK in Kharadi", "sample": False}])
    tr = await chat(d, ["hi", "I need a 2 BHK in Kharadi, budget 80 lakh", "In 1-3 months", "Rahul", "9822012345",
                        "is there a gym?", "what about loans?", "thanks"], finder=find)
    texts = bot(tr)
    assert count(ASKS["tx"], texts) == 1          # only in the very first greeting
    assert count(ASKS["tx"], texts[1:]) == 0
    assert d["tx"] == "buy" and tr[4][1].lead and tr[4][1].lead["name"] == "Rahul"
    after = texts[5:]
    assert not any(q in t for t in after for q in ASKS.values()) and count(PHONE_ASK, after) == 0


async def test_each_question_is_asked_at_most_twice_and_known_slots_never():
    d = engine.new_data()
    tr = await chat(d, ["hi", "buy", "hmm", "not sure", "ok whatever", "fine"])
    texts = bot(tr)
    assert count(ASKS["locality"], texts) <= 2
    for f in ("tx",):
        assert count(ASKS[f], texts[2:]) == 0


# ---- 2. the name ----------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text,asked,name", [("I am Rahul", None, "Rahul"), ("mera naam Rahul hai", None, "Rahul"), ("maza nav Rahul", None, "Rahul"),
                                             ("Hi, I'm Priya Sharma and I need a 2 BHK", None, "Priya Sharma"), ("rahul", "name", "Rahul"),
                                             ("Rahul here", "name", "Rahul"), ("My name is amit sajwan", None, "Amit Sajwan"),
                                             ("I am looking for a flat", None, None), ("I'm interested in Kharadi", None, None),
                                             ("I am from Mumbai", None, None), ("2 bhk", "name", None), ("not now", "name", None),
                                             ("what is the price?", "name", None), ("this is urgent", None, None)])
def test_names_are_caught_when_offered_or_asked_and_nothing_else_is_taken_for_a_name(text, asked, name):
    assert engine._name_in(text, asked) == name


async def test_the_name_is_stored_put_on_the_lead_and_used_at_most_twice():
    s, db = service([listing("L2")])
    tr = await talk(s, ["hi", "Hi, I am Rahul. I want to buy a 2 BHK in Kharadi under 90 lakh", "In 1-3 months", "9822012345", "ok", "what is RERA?",
                        "show me homes", "thanks"])
    texts = replies(tr)
    assert texts[1].startswith("Thanks, Rahul.")
    assert sum(t.count("Rahul") for t in texts) == 2  # 'Thanks, Rahul.' and 'Thank you, Rahul!'
    assert db.get_collection("chat_sessions").docs[0]["data"]["name"] == "Rahul"
    lead = db.get_collection("contacts").docs[0]
    assert lead["name"] == "Rahul" and lead["phone"] == "+919822012345"


async def test_a_name_given_after_the_number_replaces_the_placeholder_on_the_lead():
    s, db = service()
    await talk(s, ["hi", "call me on 9822012345", "yes", "I am Rahul"])
    assert db.get_collection("contacts").docs[0]["name"] == "Rahul"


# ---- 3. the number: at most twice, consent once, 'Not now' respected ------------------------------------------------------------
async def test_the_number_is_asked_at_most_twice_and_the_consent_sentence_shown_once():
    d = engine.new_data()
    msgs = ["hi", "Which school is nearest to Sky Heights?", "and which hospital is nearest to Sky Heights?", "what about the nearest mall to Sky Heights?",
            "buy", "Kharadi", "2 bhk", "80 lakh", "soon", "Rahul", "ok", "what is carpet area?", "fine", "hmm", "ok"]
    texts = bot(await chat(d, msgs))
    assert count(PHONE_ASK, texts) <= 2 and count(CONSENT, texts) == 1
    first = next(i for i, t in enumerate(texts) if PHONE_ASK.search(t))
    assert CONSENT in texts[first]  # the consent sentence sits next to the first ask
    assert first >= 1 and "do not want to guess" in texts[first]  # asked after we gave something (an honest hand-off)


async def test_not_now_stops_the_asking_for_five_turns_and_it_comes_back_only_once():
    d = engine.new_data()
    find = await fake_finder([{"id": "L2", "title": "2 BHK", "sample": False}])
    tr = await chat(d, ["hi", "buy 2 bhk in Kharadi under 90 lakh", "soon", "Rahul"], finder=find)
    assert PHONE_ASK.search(tr[-1][1].reply) and CONSENT in tr[-1][1].reply and tr[-1][1].quick == ["Not now"]
    tr = await chat(d, ["Not now", "what is RERA?", "is metro running?", "how about loans?", "ok", "fine", "ok"], finder=find)
    texts = bot(tr)
    assert texts[0] == "No problem. Is there anything else I can help you with?"
    assert count(PHONE_ASK, texts[:6]) == 0   # 'Not now' and five turns of peace after it
    assert count(PHONE_ASK, texts[6:]) == 1 and CONSENT not in texts[6]  # one short, polite second ask
    texts = bot(await chat(d, ["Not now", "ok", "ok", "ok", "ok", "ok", "ok", "ok"], finder=find))
    assert count(PHONE_ASK, texts) == 0  # never a third time


async def test_hinglish_not_now_is_understood():
    d = engine.new_data(localise=True)
    await chat(d, ["hi", "Rahul"])
    d["asked"] = "phone"
    t = (await chat(d, ["abhi nahi"]))[-1][1]
    assert d["phone_snooze_until"] > d["turn_no"] and not PHONE_ASK.search(t.reply)


async def test_a_volunteered_number_is_masked_in_the_confirmation_and_needs_a_yes():
    d = engine.new_data()
    t = (await chat(d, ["hi", "my number is 98220 12345"]))[-1][1]
    assert "2345" in t.reply and "98220" not in t.reply and "9822012345" not in t.reply and "Reply YES" in t.reply and CONSENT in t.reply
    assert t.lead is None and (await chat(d, ["yes"]))[-1][1].lead["phone"] == "+919822012345"


# ---- 4. homes ---------------------------------------------------------------------------------------------------------------
async def test_matching_homes_are_shown_as_cards_from_this_agent_only_with_samples_labelled():
    homes = [listing("L2", price_inr=7_500_000), listing("L3", price_inr=8_200_000, title="Sample: 2 BHK apartment for sale in Kharadi, Pune"),
             listing("L4", price_inr=8_800_000), listing("L5", price_inr=7_900_000),
             listing("X1", agent="OTHER", price_inr=7_600_000), listing("D1", status="draft"), listing("R1", transaction="rent", price_inr=30_000),
             listing("V1", visibility="private"), listing("B1", bhk=4, price_inr=7_700_000), listing("W1", locality="Wagholi", bhk=1, price_inr=2_000_000)]
    s, _ = service(homes)
    tr = await talk(s, ["hi", "I want to buy a 2 BHK in Kharadi, budget 70 lakh to 90 lakh"])
    r = tr[-1][1]
    ids = [c["id"] for c in r["cards"]]
    assert 1 <= len(ids) <= 3 and set(ids) <= {"L2", "L3", "L4", "L5"}
    assert "Here are 3 homes" in r["reply"]
    c = r["cards"][0]
    assert set(c) >= {"title", "locality", "bhk", "carpet_sqft", "price_text", "sample", "url", "image_url"}
    assert c["url"] == f"/agent/rahul/listings/{c['id']}" and c["image_url"].startswith("https://img.test/")
    for c in r["cards"]:
        if c["id"] == "L3":
            assert c["sample"] is True and c["price_text"] is None and not c["title"].lower().startswith("sample")
        else:
            assert c["sample"] is False and c["price_text"].startswith("₹")
    if any(c["sample"] for c in r["cards"]):
        assert "Homes marked Sample are illustrations, not for sale." in r["reply"]
    assert "available" not in r["reply"].lower().replace("not for sale", "")


async def test_only_samples_are_never_presented_as_available():
    s, _ = service([listing("S1", title="Sample: 2 BHK in Kharadi", sample_key="k1"), listing("S2", title="Sample: 2 BHK flat", price_inr=8_000_000)])
    r = (await talk(s, ["hi", "2 bhk in Kharadi, 80 lakh"]))[-1][1]
    assert r["cards"] and all(c["sample"] and c["price_text"] is None for c in r["cards"])
    assert "illustrations, not for sale" in r["reply"] and "Here are" not in r["reply"]


async def test_no_match_is_said_honestly_and_the_agent_is_offered():
    s, _ = service([listing("W1", locality="Wagholi", bhk=1, price_inr=2_000_000)])
    r = (await talk(s, ["hi", "I want a 3 BHK in Kharadi under 2 crore"]))[-1][1]
    assert r["cards"] == [] and "could not find a listed home" in r["reply"] and "our team can look for you" in r["reply"]
    assert PHONE_ASK.search(r["reply"]) and CONSENT in r["reply"]  # a natural moment: offer the agent's help
    assert "₹" not in r["reply"]


async def test_homes_are_not_shown_twice_for_the_same_requirement_but_again_when_asked_or_changed():
    find = await fake_finder([{"id": "L2", "title": "2 BHK", "sample": False}])
    d = engine.new_data()
    tr = await chat(d, ["hi", "buy 2 bhk in Kharadi under 90 lakh", "soon", "show me more homes", "actually 3 bhk"], finder=find)
    assert [bool(t.cards) for _, t in tr] == [False, True, False, True, True]
    assert find.calls[0][0] == {"bhk": 2, "budget_min_inr": None, "budget_max_inr": 9_000_000, "localities": ["Kharadi"], "transaction": "sale"}


async def test_on_a_platform_page_about_a_demo_home_the_cards_come_from_the_demo_agent():
    demo = {"slug": "demo", "is_public": True, "agent_id": "DEMO"}
    homes = [listing("DM1", agent="DEMO", title="Sample: 2 BHK in Kharadi", bhk=2), listing("DM2", agent="DEMO", title="Sample: 2 BHK in Kharadi B", price_inr=8_100_000),
             listing("L2", agent="A1")]
    s, _ = service(homes, extra_profiles=[demo])
    tr = await talk(s, ["hi", "Similar homes"], context={"listing_id": "DM1"})
    r = tr[-1][1]
    assert [c["id"] for c in r["cards"]] == ["DM2"] and r["cards"][0]["url"] == "/agent/demo/listings/DM2" and r["cards"][0]["sample"]


# ---- 5. the agent is alerted --------------------------------------------------------------------------------------------------
async def test_a_chat_lead_and_an_unanswerable_question_each_alert_the_agent_once_without_the_number():
    s, db = service([listing("L2")])
    await talk(s, ["hi", "Which school is nearest to Sky Heights tower B?", "and the nearest bank to Sky Heights tower B?"])
    notes = db.get_collection("notifications").docs
    assert [n["kind"] for n in notes] == ["chat_needs_you"] and notes[0]["agent_id"] == "A1" and "school" in notes[0]["summary"]
    await talk(s, ["I am Rahul, 2 bhk in Kharadi under 90 lakh", "9822012345"])
    notes = db.get_collection("notifications").docs
    assert [n["kind"] for n in notes] == ["chat_needs_you", "new_chat_lead"]
    lead_note = notes[1]
    assert lead_note["summary"].startswith("Rahul shared their number in the website chat.") and "Kharadi" in lead_note["summary"]
    assert "9822012345" not in str(notes) and "98220" not in str(notes)
    assert lead_note["ref"]["lead_id"] == db.get_collection("contacts").docs[0]["_id"] and lead_note["read"] is False


async def test_the_studio_badge_counts_chat_alerts_too():
    from app.modules.notifications.service import KINDS, NotificationService
    s, db = service()
    await talk(s, ["hi", "Which school is nearest to Sky Heights tower B?"])
    assert {"new_chat_lead", "chat_needs_you"} <= set(KINDS)
    assert (await NotificationService(db).list("A1", unread_only=True))["unread"] == 1


# ---- 6. the greeting knows the page -------------------------------------------------------------------------------------------
async def test_a_listing_page_greeting_opens_with_that_home():
    s, _ = service([listing("L1", carpet_sqft=780)])
    r = (await talk(s, ["hi"], context={"listing_id": "L1"}))[0][1]
    assert r["reply"] == "Asking about the 2 BHK in Kharadi, 780 sq ft? I can tell you about it or find similar homes."
    assert r["quick_replies"] == ["Tell me about it", "Similar homes"]


async def test_a_sample_listing_greeting_says_it_is_a_sample_and_tell_me_about_it_uses_its_facts():
    s, _ = service([listing("L1", title="Sample: 2 BHK in Kharadi")])
    tr = await talk(s, ["hi", "Tell me about it"], context={"listing_id": "L1"})
    assert tr[0][1]["reply"].startswith("Asking about the sample 2 BHK in Kharadi, 780 sq ft? It is an illustration, not for sale.")
    assert "sample home shown for illustration, not available for sale" in tr[1][1]["reply"] and "780 sq ft" in tr[1][1]["reply"]
    assert ASKS["locality"] not in tr[1][1]["reply"] and ASKS["bhk"] not in tr[1][1]["reply"]  # the page already says which area and size


async def test_a_locality_page_greeting_is_about_that_area_and_the_general_greeting_elsewhere():
    s, _ = service()
    r = (await talk(s, ["hi"], context={"locality": "upper-kharadi"}))[0][1]
    assert r["reply"].startswith("Looking at homes in Upper Kharadi?") and ASKS["tx"] in r["reply"] and ASKS["locality"] not in r["reply"]
    r = (await talk(s, ["hi"], sid="session-v2-other-0001"))[0][1]
    assert r["reply"].startswith("Hi! I am the Avasetu assistant.") and len(r["reply"]) < 200


# ---- 7. Continue on WhatsApp only when the number is configured ----------------------------------------------------------------
async def test_continue_on_whatsapp_is_offered_only_when_the_platform_number_is_set(monkeypatch):
    monkeypatch.delenv("WHATSAPP_PUBLIC_NUMBER", raising=False)
    monkeypatch.delenv("NEXT_PUBLIC_WHATSAPP_NUMBER", raising=False)
    s, db = service([listing("L1"), listing("L2", price_inr=8_000_000)])
    tr = await talk(s, ["hi", "Similar homes", "Which school is nearest to Sky Heights tower B?"], context={"listing_id": "L1"})
    assert all(phrases.WHATSAPP not in r["quick_replies"] and r["whatsapp_url"] is None for _, r in tr)

    monkeypatch.setenv("NEXT_PUBLIC_WHATSAPP_NUMBER", "98765 43210")
    await db.get_collection("interest_links").insert_one({"_id": "abcd234", "code": "abcd234", "kind": "listing", "ref": "L1", "channel": "whatsapp"})
    s2, _ = service([listing("L1"), listing("L2", price_inr=8_000_000)])
    s2.db.get_collection("interest_links").docs.append({"_id": "abcd234", "code": "abcd234", "kind": "listing", "ref": "L1", "channel": "whatsapp"})
    r = (await talk(s2, ["hi"], context={"listing_id": "L1"}, sid="session-v2-wa-000001"))[0][1]
    assert r["quick_replies"][-1] == "Continue on WhatsApp"
    assert r["whatsapp_url"].startswith("https://wa.me/919876543210?text=") and "ref%20abcd234" in r["whatsapp_url"]
    r = (await talk(s2, ["call me on 9822012345", "yes"], context={"listing_id": "L1"}, sid="session-v2-wa-000001"))[-1][1]
    assert r["lead_created"] and "Continue on WhatsApp" in r["quick_replies"] and "9822012345" not in (r["whatsapp_url"] or "")


async def test_whatsapp_prefill_names_the_requirement_when_there_is_no_listing(monkeypatch):
    monkeypatch.setenv("WHATSAPP_PUBLIC_NUMBER", "+91 98765 43210")
    s, _ = service([listing("L2")])
    r = (await talk(s, ["hi", "2 bhk in Kharadi, 80 lakh"]))[-1][1]
    assert "Continue on WhatsApp" in r["quick_replies"]
    assert "2%20BHK%2C%20Kharadi%2C%20under%2080L" in r["whatsapp_url"]


# ---- 8. language stays consistent ---------------------------------------------------------------------------------------------
ENGLISH_TEMPLATES = [phrases.P[k]["en"] for k in ("ask_tx", "ask_locality", "ask_bhk", "ask_budget", "ask_timeline", "ask_name", "ask_phone", "ask_phone_again",
                                               "consent", "no_match", "anything_else", "dont_guess", "thanks_name", "not_now_ok")] + ["Here are", "Got it:"]


async def test_a_hinglish_buyer_gets_hinglish_fixed_phrases_and_no_english_templates():
    d = engine.new_data(localise=True)
    tr = await chat(d, ["hi", "mujhe Kharadi mein 2 bhk chahiye, budget 80 lakh hai", "abhi 2 mahine mein", "mera naam Rahul hai", "abhi nahi",
                        "Kharadi mein school kitna door hai?"], finder=await fake_finder([]))
    texts = bot(tr)[1:]
    assert d["lang"] == "hinglish" and d["tx"] == "buy"
    for t in texts:
        for en in ENGLISH_TEMPLATES:
            assert en.format(n=3, name="Rahul") not in t, (en, t)
    joined = " ".join(texts)
    assert "Abhi is requirement se milta koi listed ghar nahi mila" in joined and "Shukriya, Rahul." in joined
    assert phrases.say("consent", "hinglish") in joined and "Koi baat nahi." in joined


async def test_hindi_and_marathi_buyers_get_their_language():
    d = engine.new_data(localise=True)
    t = (await chat(d, ["नमस्ते", "मुझे 2 BHK चाहिए"]))[-1][1]
    assert phrases.say("ask_tx", "hi") in t.reply and "Are you" not in t.reply
    d2 = engine.new_data(localise=True)
    t = (await chat(d2, ["hi", "mala Wagholi madhye ghar pahije aahe"]))[-1][1]
    assert d2["lang"] == "mr_latn" and phrases.say("ask_tx", "mr_latn") in t.reply


async def test_short_english_answers_keep_the_buyers_language_and_whatsapp_state_stays_english():
    d = engine.new_data(localise=True)
    await chat(d, ["hi", "mujhe ghar chahiye"])
    t = (await chat(d, ["Buy"]))[-1][1]
    assert d["lang"] == "hinglish" and phrases.say("ask_locality", "hinglish") in t.reply
    wa = engine.new_data()  # WhatsApp: the engine speaks English, the WhatsApp module translates
    t = (await chat(wa, ["hi", "mujhe ghar chahiye"]))[-1][1]
    assert ASKS["tx"] in t.reply


# ---- with the fake LLM: same rules -----------------------------------------------------------------------------------------------
async def test_with_an_llm_the_rules_hold_and_unsafe_drafts_never_reach_the_buyer():
    bad = FakeLLM({"answerable": True, "answer": "It costs ₹90 lakh, call 9876543210."})
    s, db = service([listing("L2")], llm=bad)
    tr = await talk(s, ["hi", "Does the builder give a loan payment plan on Ganga Heights?", "buy 2 bhk Kharadi 80 lakh", "soon", "I am Rahul",
                        "9822012345", "thanks"])
    texts = replies(tr)
    assert not any("9876543210" in t for t in texts) and count(CONSENT, texts) == 1 and count(PHONE_ASK, texts) <= 2
    assert count(ASKS["tx"], texts[2:]) == 0 and tr[5][1]["lead_created"] and any(r["cards"] for _, r in tr)
