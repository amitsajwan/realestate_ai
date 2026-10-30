"""Passing a lead to an agent (inbox/handover.py, InboxService.pass_lead, followups.auto_passes).

2026-10-26: a Mansha Phase-II form lead (2 BHK, from Google) was passed to House Deal with only a name and a phone, and to the
retired House Deal account. These pin the card, the picker and the automatic pass."""
from datetime import datetime, timedelta

from app.modules.inbox import followups, handover
from app.modules.inbox.service import InboxError, InboxService

from .fakes import FakeDb

NOW = datetime(2026, 10, 26, 4, 0)
OWNER, HD, RETIRED = "OWNER", "HD", "HD-OLD"


class FakeWhatsApp:
    class cfg:
        phone_number_id = "P"
        dry_run = False

    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def send_template(self, conv, name, lang, params, text, now):
        self.sent.append((conv["wa_id"], name, params))
        if self.fail:
            return {"_id": f"m{len(self.sent)}", "status": "failed", "error": "template not approved"}
        return {"_id": f"m{len(self.sent)}", "status": "sent"}


def form_lead(_id="saket", ago=timedelta(minutes=10), **kw):
    """A project-page form lead as the site stores it: the topic in `message`, BHK from the form, the page in first_touch."""
    return {"_id": _id, "agent_id": OWNER, "name": "Saket Patil", "phone": "+918975300001", "stage": "contacted", "channel": "form",
            "message": "About MANSHA PHASE-II (MahaRERA P52100028315)", "source": "google", "utm": {},
            "first_touch": {"landing": "/projects/mansha-phase-ii-wagholi", "referrer": "https://www.google.com/",
                            "enquiry_page": "/projects/mansha-phase-ii-wagholi", "app": None},
            "consent": {"given_at": NOW}, "created_at": NOW - ago, "last_activity_at": NOW - ago, "notes": [],
            "requirement": {"bhk": 2.0, "budget_min_inr": None, "budget_max_inr": None, "timeline": None, "financing": None,
                            "localities": []},
            "auto_followup_at": NOW - ago + timedelta(minutes=2), **kw}


async def setup(*leads):
    db = FakeDb()
    await db.get_collection("projects").insert_one({"_id": "P52100028315", "regno": "P52100028315", "name": "MANSHA PHASE-II",
                                                    "locality": "wagholi", "page_slug": "mansha-phase-ii-wagholi"})
    for p in ({"agent_id": HD, "slug": "house-deal", "phone": "+919921900001", "branding_data": {"business_name": "House Deal"}},
              {"agent_id": RETIRED, "slug": "house-deal-retired-20261003", "phone": "+917447200001", "agent_name": "House Deal"},
              {"agent_id": OWNER, "slug": "avasetu", "phone": "+919767900001"}):
        await db.get_collection("agent_public_profiles").insert_one(p)
    await db.get_collection("users").insert_one({"_id": "u-old", "phone": "+917447200001", "is_active": False})
    for c in leads:
        await db.get_collection("contacts").insert_one(c)
    # the auto follow-up's chat: our template went out, the chat's own state knows nothing (this is what the old text read)
    await db.get_collection("whatsapp_conversations").insert_one({
        "_id": "P:918975300001", "wa_id": "918975300001", "phone_number_id": "P", "agent_id": OWNER, "name": "Saket Patil",
        "lead_id": "saket", "data": {"bhk": None, "locality": None}, "messages": [], "template_sent_at": NOW - timedelta(minutes=8),
        "updated_at": NOW - timedelta(minutes=8)})
    await db.get_collection("whatsapp_messages").insert_one({
        "_id": "w1", "direction": "out", "wa_id": "918975300001", "phone_number_id": "P", "type": "template",
        "text": "Namaste Saket ji, this is Avasetu.", "ts": NOW - timedelta(minutes=8), "status": "sent"})
    return db


async def test_the_card_carries_what_the_lead_record_knows_even_when_the_chat_knows_nothing():
    db = await setup(form_lead())
    h = await InboxService(db, FakeWhatsApp(), now=lambda: NOW).handover_for(OWNER, "saket")
    text = h["card"]["text"]
    for want in ("Name: Saket Patil", "Phone: +91 89753 00001", "Project: Mansha Phase-II, Wagholi (MahaRERA P52100028315)",
                 "Wants: Price sheet and floor plans", "Home: 2 BHK", "Page: https://avasetu.in/projects/mansha-phase-ii-wagholi",
                 "Came from: Google search", "Enquired: 26 Oct, 9:20 am IST", "So far: Avasetu sent them a WhatsApp follow-up; no reply yet"):
        assert want in text, want
    assert h["card"]["missing"] == ["budget", "when they want to buy", "home loan or own funds"]
    assert "Not known yet, please ask: budget, when they want to buy, home loan or own funds" in text
    assert h["areas"] == ["Wagholi"]


def test_the_form_line_says_what_they_asked_for():
    assert handover.ask_of("About Site visit: GERA ISLAND (MahaRERA P1): Sunday morning") == {
        "want": "A site visit", "topic": "GERA ISLAND (MahaRERA P1)", "said": "Sunday morning"}
    assert handover.ask_of("Floor plans of BREEZA (MahaRERA P2)")["want"] == "Floor plans"
    assert handover.ask_of("About 3 BHK near EON: call after 6")["said"] == "call after 6"


def test_template_parameters_are_five_single_lines_none_empty():
    c = handover.card({"name": "Ravi\nK", "phone": "+919000000001", "requirement": {"bhk": 3, "budget_max_inr": 9000000,
                                                                                   "timeline": "now"}})
    params = handover.template_params(c)
    assert len(params) == 5 and all(p and "\n" not in p for p in params)
    assert params[0] == "Ravi K" and params[2] == "a home in Pune"
    assert params[3] == "3 BHK; budget under 90L; buying now"


async def test_the_picker_leaves_out_retired_accounts_and_a_pass_to_one_is_refused():
    db = await setup(form_lead())
    svc = InboxService(db, FakeWhatsApp(), now=lambda: NOW)
    assert [a["agent_id"] for a in await svc.agents(OWNER)] == [HD]
    try:
        await svc.pass_lead(OWNER, "saket", RETIRED)
        assert False, "a retired account took a buyer"
    except InboxError as e:
        assert e.status_code == 409 and "retired" in str(e)


async def test_a_pass_moves_the_lead_and_its_chat_and_sends_the_card_to_the_agent():
    db = await setup(form_lead())
    wa = FakeWhatsApp()
    r = await InboxService(db, wa, now=lambda: NOW).pass_lead(OWNER, "saket", HD)
    assert r["passed_to"] == "House Deal" and r["whatsapp_status"] == "sent"
    assert wa.sent[0][:2] == ("919921900001", handover.AGENT_TEMPLATE)
    assert wa.sent[0][2][:3] == ["Saket Patil", "+91 89753 00001", "Mansha Phase-II, Wagholi (MahaRERA P52100028315)"]
    lead = await db.get_collection("contacts").find_one({"_id": "saket"})
    assert lead["agent_id"] == HD and lead["passed_to"] == HD and "Mansha Phase-II" in lead["handover"]["text"]
    conv = await db.get_collection("whatsapp_conversations").find_one({"_id": "P:918975300001"})
    assert conv["agent_id"] == HD and conv["routed_by"] == "owner_pass"
    alert = await db.get_collection("notifications").find_one({"agent_id": HD})
    assert alert["kind"] == "buyer_passed" and "Mansha Phase-II" in alert["summary"] and alert["ref"]["lead_id"] == "saket"
    assert "Mansha" in r["whatsapp_url"]
    mine = await InboxService(db, wa, now=lambda: NOW).passed(OWNER)
    assert [(p["name"], p["agent_name"], p["whatsapp_status"]) for p in mine] == [("Saket Patil", "House Deal", "sent")]


async def test_passing_from_the_chat_passes_the_whole_lead_with_its_card():
    db = await setup(form_lead())
    wa = FakeWhatsApp(fail=True)
    svc = InboxService(db, wa, now=lambda: NOW)
    tid = (await svc.for_lead(OWNER, "saket"))[0]["id"]
    r = await svc.pass_to(OWNER, tid, HD)
    assert "Project: Mansha Phase-II" in r["card"]["text"]
    # the template is not approved yet: the pass still happens, the owner keeps the wa.me link and the reason
    assert r["whatsapp_status"] == "failed" and r["whatsapp_error"] == "template not approved" and r["whatsapp_url"]
    assert (await db.get_collection("contacts").find_one({"_id": "saket"}))["agent_id"] == HD


async def test_always_adds_the_area_rule_and_the_next_lead_there_goes_by_itself():
    db = await setup(form_lead())
    svc = InboxService(db, FakeWhatsApp(), now=lambda: NOW)
    r = await svc.pass_lead(OWNER, "saket", HD, always="area")
    assert r["rule_added"]["label"] == "Wagholi"
    assert [(x["agent_name"], x["kind"], x["label"]) for x in await svc.routes(OWNER)] == [("House Deal", "area", "Wagholi")]
    contacts = db.get_collection("contacts")
    await contacts.insert_one(form_lead("next", ago=timedelta(minutes=6), phone="+918975300002", name="Next Buyer"))
    await contacts.insert_one(form_lead("fresh", ago=timedelta(minutes=1), phone="+918975300003"))
    await contacts.insert_one(form_lead("elsewhere", phone="+918975300004", first_touch={"enquiry_page": "/projects/other-baner"}))
    told = []

    async def notify(db_, agent, kind, text, ref, now):
        told.append((agent, kind, text))

    assert await followups.auto_passes(db, svc, OWNER, NOW, notify) == 1
    assert (await contacts.find_one({"_id": "next"}))["agent_id"] == HD
    assert (await contacts.find_one({"_id": "fresh"}))["agent_id"] == OWNER       # the follow-up gets its turn first
    assert (await contacts.find_one({"_id": "elsewhere"}))["agent_id"] == OWNER   # no rule for it
    assert told == [(OWNER, "lead_auto_passed", "Next Buyer went to House Deal by your Wagholi rule. WhatsApp to them sent.")]
    assert (await svc.routes(OWNER))[0]["passed"] == 1
    # once per lead: the next cycle passes the fresh one and nothing twice
    assert await followups.auto_passes(db, svc, OWNER, NOW + timedelta(minutes=5), notify) == 1
    assert len(told) == 2


async def test_no_rules_means_no_automatic_pass():
    db = await setup(form_lead())
    assert await followups.auto_passes(db, InboxService(db, FakeWhatsApp(), now=lambda: NOW), OWNER, NOW) == 0
    assert (await db.get_collection("contacts").find_one({"_id": "saket"}))["agent_id"] == OWNER


async def test_the_owner_still_opens_a_lead_he_passed_read_only():
    from app.modules.tracking.service import TrackingError, TrackingService
    db = await setup(form_lead())
    await InboxService(db, FakeWhatsApp(), now=lambda: NOW).pass_lead(OWNER, "saket", HD)
    tracking = TrackingService(db, now=lambda: NOW)
    mine = await tracking.lead_detail(OWNER, "saket")
    assert mine["passed_to"] == "House Deal" and "Mansha Phase-II" in mine["handover"]["text"]
    theirs = await tracking.lead_detail(HD, "saket")
    assert theirs["passed_to"] is None and theirs["handover"]
    assert [t["channel"] for t in await InboxService(db, FakeWhatsApp(), now=lambda: NOW).for_lead(OWNER, "saket")] == ["whatsapp"]
    try:
        await tracking.lead_detail("SOMEONE", "saket")
        assert False, "a stranger opened the lead"
    except TrackingError as e:
        assert e.status_code == 404


async def test_an_enquiry_on_the_agents_own_site_goes_to_their_office_whatsapp_once():
    # 2026-10-30: House Deal's own-page enquiries only reached their Studio; the owner wants them on WhatsApp through Avasetu,
    # to the office line, which is also the phone of their retired login and so lives in office_phone
    own = form_lead("own", agent_id=HD, name="Ravi Kale", ago=timedelta(minutes=3))
    old = form_lead("old", agent_id=HD, ago=timedelta(hours=3))                      # from before the step went live
    passed = form_lead("passed", agent_id=HD, passed_at=NOW, passed_by=OWNER)         # a pass already sent its card
    mine = form_lead("mine", ago=timedelta(minutes=3))                                # the owner's own lead
    db = await setup(own, old, passed, mine)
    await db.get_collection("agent_public_profiles").update_one(
        {"agent_id": HD}, {"$set": {"branding_data": {"business_name": "House Deal", "office_phone": "+917447200001"}}})
    wa, told = FakeWhatsApp(), []
    svc = InboxService(db, wa, now=lambda: NOW)

    async def notify(db_, agent, kind, text, ref, now):
        told.append((agent, kind, text))

    assert await followups.agent_site_enquiries(db, svc, OWNER, NOW, notify) == 1
    assert [(to, name, params[:2]) for to, name, params in wa.sent] == [("917447200001", "agent_site_enquiry_v1", ["House Deal", "Ravi Kale"])]
    lead = await db.get_collection("contacts").find_one({"_id": "own"})
    assert lead["agent_wa_status"] == "sent" and lead["agent_id"] == HD
    assert await followups.agent_site_enquiries(db, svc, OWNER, NOW + timedelta(minutes=5), notify) == 0
    assert len(wa.sent) == 1
    # the owner follows it: one alert, a row in Leads > Passed, and the lead opens read only
    assert told == [(OWNER, "agent_site_enquiry", "Ravi Kale enquired on House Deal's site. WhatsApp to them sent.")]
    row = next(r for r in await svc.passed(OWNER) if r["lead_id"] == "own")
    assert row["by"] == "site" and row["agent_name"] == "House Deal" and "Name: Ravi Kale" in row["text"]
    assert row["whatsapp_url"].startswith("https://wa.me/917447200001?text=")
    from app.modules.tracking.service import TrackingService
    assert (await TrackingService(db, now=lambda: NOW).lead_detail(OWNER, "own"))["name"] == "Ravi Kale"


async def test_until_meta_approves_the_site_enquiry_template_the_pass_template_goes_instead():
    db = await setup(form_lead("own", agent_id=HD, name="Ravi Kale", ago=timedelta(minutes=3)))

    class NotApprovedYet(FakeWhatsApp):
        async def send_template(self, conv, name, lang, params, text, now):
            self.sent.append((conv["wa_id"], name, params))
            ok = name != "agent_site_enquiry_v1"
            return {"_id": "m", "status": "sent" if ok else "failed", "error": None if ok else "template not approved"}

    wa = NotApprovedYet()
    r = await InboxService(db, wa, now=lambda: NOW).tell_agent_of_lead(await db.get_collection("contacts").find_one({"_id": "own"}))
    assert [name for _, name, _ in wa.sent] == ["agent_site_enquiry_v1", "lead_passed_v1"]
    assert r["whatsapp_status"] == "sent" and r["agent_name"] == "House Deal"
