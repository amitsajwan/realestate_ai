"""Lead follow-ups loop (app/modules/inbox/followups.py): auto template to fresh form leads, one alert per wait."""
from datetime import datetime, timedelta

from app.modules.inbox import followups
from app.modules.inbox.service import InboxService

from .fakes import FakeDb

NOW = datetime(2026, 10, 23, 10, 0)


class FakeWhatsApp:
    class cfg:
        phone_number_id = "P"
        dry_run = False

    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def send_template(self, conv, name, lang, params, text, now):
        if self.fail:
            return {"_id": f"m{len(self.sent)}", "status": "failed", "error": "boom"}
        self.sent.append(conv["wa_id"])
        return {"_id": f"m{len(self.sent)}", "status": "sent"}


def lead(_id, phone="+919730369091", ago=timedelta(minutes=10), **kw):
    return {"_id": _id, "agent_id": "A", "name": _id.title(), "phone": phone, "stage": "new", "channel": "form", "consent": {"given_at": NOW},
            "score_base": 25, "created_at": NOW - ago, "last_activity_at": NOW - ago, "notes": [], **kw}


async def setup(*leads):
    db = FakeDb()
    for i in range(5):
        await db.get_collection("whatsapp_messages").insert_one({"_id": f"m{i}"})
    for c in leads:
        await db.get_collection("contacts").insert_one(c)
    return db


async def test_auto_followup_goes_once_to_fresh_uncontacted_form_leads_only():
    db = await setup(lead("rahul"), lead("tooold", phone="+919000000001", ago=timedelta(days=2)),
                     lead("justnow", phone="+919000000002", ago=timedelta(seconds=30)),
                     lead("chat", phone="+919000000003", channel="chat"), lead("nophone", phone="+1555"),
                     lead("other", phone="+919000000004", agent_id="B"))
    wa = FakeWhatsApp()
    inbox = InboxService(db, wa, now=lambda: NOW)
    assert await followups.auto_followups(db, inbox, "A", NOW) == 1
    assert wa.sent == ["919730369091"]
    rahul = await db.get_collection("contacts").find_one({"_id": "rahul"})
    assert rahul["stage"] == "contacted" and rahul["auto_followup_at"] == NOW
    # 5 minutes on: the 30-second-old lead is due now; Rahul is never messaged twice
    assert await followups.auto_followups(db, inbox, "A", NOW + timedelta(minutes=5)) == 1
    assert wa.sent == ["919730369091", "919000000002"]


async def test_a_failed_send_is_kept_on_the_lead_and_not_retried():
    db = await setup(lead("rahul"))
    wa = FakeWhatsApp(fail=True)
    inbox = InboxService(db, wa, now=lambda: NOW)
    assert await followups.auto_followups(db, inbox, "A", NOW) == 0
    c = await db.get_collection("contacts").find_one({"_id": "rahul"})
    assert "boom" in c["auto_followup_error"]
    assert await followups.auto_followups(db, inbox, "A", NOW) == 0


async def test_waiting_alert_once_per_wait_and_again_when_they_write_again():
    db = await setup(lead("veebha", ago=timedelta(hours=3)), lead("fresh", phone="+919000000002", ago=timedelta(hours=1)),
                     lead("won", phone="+919000000003", ago=timedelta(hours=5), stage="won"))
    told = []

    async def notify(db_, agent, kind, text, ref, now):
        told.append((agent, kind, ref["lead_id"], text))

    assert await followups.waiting_alerts(db, NOW, notify) == 1
    assert told[0][:3] == ("A", "lead_waiting", "veebha") and "nobody has contacted" in told[0][3]
    assert await followups.waiting_alerts(db, NOW + timedelta(minutes=5), notify) == 0
    # a person answered, then they wrote again and waited 2+ hours: a new wait, told again
    convs = db.get_collection("whatsapp_conversations")
    await convs.insert_one({"_id": "P:919730369091", "wa_id": "919730369091", "lead_id": "veebha", "messages": [
        {"role": "agent", "sent_by": "person", "text": "Hi", "ts": NOW},
        {"role": "user", "text": "When can I visit?", "ts": NOW + timedelta(minutes=10)}]})
    assert await followups.waiting_alerts(db, NOW + timedelta(hours=3), notify) == 2   # Veebha again, and 'fresh' is now 4 h old
    again = [t for t in told[1:] if t[2] == "veebha"]
    assert len(again) == 1 and "replied" in again[0][3]


class Templates(FakeWhatsApp):
    """Records which template went with which parameters; `refuse` names templates Meta has not approved yet."""

    def __init__(self, refuse=()):
        super().__init__()
        self.refuse, self.names = refuse, []

    async def send_template(self, conv, name, lang, params, text, now):
        self.names.append((name, params, text))
        if name in self.refuse:
            return {"_id": f"m{len(self.names)}", "status": "failed", "error": "template not approved"}
        return {"_id": f"m{len(self.names)}", "status": "sent"}


ARRCADE = {"slug": "96-arrcade-kharadi", "name": "96 Arrcade", "area": "Kharadi", "regno": "P52100078739"}


def subhash():
    return lead("subhash", name="Subhash Girase", message="About Site visit: 96 Arrcade (MahaRERA P52100078739)",
                requirement={"bhk": 2, "localities": []}, first_touch={"landing": "/projects/area/kharadi/2-bhk?utm_source=chatgpt.com",
                                                                       "enquiry_page": "/projects/96-arrcade-kharadi"})


async def project_inbox(db, wa):
    inbox = InboxService(db, wa, now=lambda: NOW)

    async def project_of(c):
        return ARRCADE if (c.get("first_touch") or {}).get("enquiry_page") == "/projects/96-arrcade-kharadi" else None

    inbox.project_of = project_of
    return inbox


async def test_a_project_page_enquiry_gets_the_project_and_what_they_asked_for_not_which_part_of_pune():
    db = await setup(subhash())
    wa = Templates()
    assert await followups.auto_followups(db, await project_inbox(db, wa), "A", NOW) == 1
    [(name, params, text)] = wa.names
    assert name == "project_enquiry_v1" and params == ["Subhash", "96 Arrcade, Kharadi", "a site visit"]
    assert "part of Pune" not in text
    conv = await db.get_collection("whatsapp_conversations").find_one({"_id": "P:919730369091"})
    assert conv["messages"][-1]["text"] == text


async def test_until_meta_approves_the_project_template_the_old_one_goes_with_the_area():
    db = await setup(subhash())
    wa = Templates(refuse=("project_enquiry_v1",))
    assert await followups.auto_followups(db, await project_inbox(db, wa), "A", NOW) == 1
    assert [n for n, _, _ in wa.names] == ["project_enquiry_v1", "enquiry_followup_v1"]
    assert wa.names[1][1] == ["Subhash", "2 BHK home", "Kharadi"]


async def test_an_enquiry_off_a_project_page_keeps_the_general_follow_up():
    db = await setup(lead("rahul", message="Call me", first_touch={"enquiry_page": "/agent/avasetu"}))
    wa = Templates()
    assert await followups.auto_followups(db, await project_inbox(db, wa), "A", NOW) == 1
    assert [(n, p) for n, p, _ in wa.names] == [("enquiry_followup_v1", ["Rahul", "home", "your enquiry on our website"])]
