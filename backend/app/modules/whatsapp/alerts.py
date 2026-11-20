"""New-project alerts on WhatsApp (owner, 2026-11-19: leads that do not depend on Google). A buyer sends "ALERT Kharadi 2BHK" and, each
week, gets the projects newly registered on MahaRERA in that place, from our own number.

  sign up   ALERT <place> [<n> BHK]: the place is read the way buyers spell it (pune_places.in_search); no place -> ask for one
  stop      ALERT OFF (or STOP, which silences everything): the alert is dropped
  weekly    `send_due`: a chat whose alert was last looked at WEEK ago gets the projects registered in its place since then, ones it was
            never sent, newest first. Nothing new -> nothing sent (an empty week is not a message). Inside the 24-hour window a plain
            message (free); outside it the approved marketing template TEMPLATE, which the buyer opted into by sending ALERT.

State lives on the chat (whatsapp_conversations, this module's collection): conv["alert"] = {place, name, bhk, at, checked_at, sent}.
The register is read through `configure(new_projects=...)` (app.wiring), since the register sits with the content modules.
"""
import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, List, Optional

from app.core import pune_places
from app.core.database import get_database
from app.platform.heartbeats import heartbeat

from . import adapters, lang as L

log = logging.getLogger(__name__)

INTERVAL_S = 3600
WEEK = timedelta(days=7)
SEND_HOURS_IST = range(10, 20)        # nobody gets a project alert at night
IST = timedelta(hours=5, minutes=30)
MAX_PROJECTS = 5
MAX_CHATS = 500
TEMPLATE = "new_launch_alert_v1"     # MARKETING: "New projects registered in {{1}} this week: {{2}}. See them all: {{3}} ..."

ASKED = re.compile(r"^\W*(?:alerts?|new\s+launch(?:es)?\s+alerts?|अलर्ट)\b", re.I)
OFF = re.compile(r"\b(?:off|stop|band|बंद|नको|cancel)\b", re.I)
BHK = re.compile(r"\b([1-5])\s*(?:\.5\s*)?bhk\b|\b([1-5])\s*(?:bed|room)", re.I)

# (db, place key, since) -> the register's new projects there: [{regno, name, builder, homes, slug, registered_on}], newest first
NewProjects = Callable[[Any, str, datetime], Awaitable[List[dict]]]
_deps: dict = {"new_projects": None}


def configure(new_projects: Optional[NewProjects] = None) -> None:
    _deps["new_projects"] = new_projects


def enabled() -> bool:
    """Signing up always works; the weekly send is switched on with WHATSAPP_ALERTS (each one outside the window is a paid template)."""
    return os.getenv("WHATSAPP_ALERTS", "").strip().lower() in ("1", "true", "yes", "on")


ASK_PLACE = {
    "en": "Which area should I watch? Send it like this: ALERT Kharadi 2BHK",
    "hi": "किस एरिया के नए प्रोजेक्ट भेजूँ? ऐसे लिखें: ALERT Kharadi 2BHK",
    "hinglish": "Kis area ke naye projects bhejun? Aise likhein: ALERT Kharadi 2BHK",
    "mr": "कोणत्या एरियाचे नवीन प्रोजेक्ट पाठवू? असे लिहा: ALERT Kharadi 2BHK",
    "mr_latn": "Konatya area che navin projects pathvu? Ase liha: ALERT Kharadi 2BHK",
}
DONE = {
    "en": "Done. Each week I will send you the new projects registered on MahaRERA in {place}{bhk}. Nothing new, no message. "
          "Reply ALERT OFF to stop.\nWhat is open there now: {link}",
    "hi": "हो गया। हर हफ्ते {place}{bhk} में MahaRERA पर रजिस्टर हुए नए प्रोजेक्ट मैं आपको भेजूँगा। कुछ नया नहीं, तो मैसेज नहीं। "
          "बंद करने के लिए ALERT OFF लिखें।\nअभी वहाँ क्या उपलब्ध है: {link}",
    "hinglish": "Ho gaya. Har hafte {place}{bhk} mein MahaRERA par register hue naye projects main aapko bhejunga. Kuch naya nahi, "
                "to message nahi. Band karne ke liye ALERT OFF likhein.\nAbhi wahan kya available hai: {link}",
    "mr": "झाले. दर आठवड्याला {place}{bhk} मध्ये MahaRERA वर नोंदलेले नवीन प्रोजेक्ट मी तुम्हाला पाठवेन. नवीन काही नसेल तर मेसेज नाही. "
          "बंद करण्यासाठी ALERT OFF लिहा.\nआत्ता तिथे काय उपलब्ध आहे: {link}",
    "mr_latn": "Jhale. Dar athavdyala {place}{bhk} madhe MahaRERA var nondlele navin projects mi tumhala pathven. Navin kahi nasel tar "
               "message nahi. Band karnyasathi ALERT OFF liha.\nAatta tithe kay available aahe: {link}",
}
BHK_PART = {"en": " ({bhk} BHK noted)", "hi": " ({bhk} BHK नोट किया)", "hinglish": " ({bhk} BHK note kiya)", "mr": " ({bhk} BHK नोंदवले)",
            "mr_latn": " ({bhk} BHK nondavle)"}
STOPPED = {
    "en": "Alert stopped. Send ALERT with an area any time to start again.",
    "hi": "अलर्ट बंद। फिर शुरू करने के लिए कभी भी ALERT और एरिया लिखें।",
    "hinglish": "Alert band. Phir shuru karne ke liye kabhi bhi ALERT aur area likhein.",
    "mr": "अलर्ट बंद. पुन्हा सुरू करण्यासाठी कधीही ALERT आणि एरिया लिहा.",
    "mr_latn": "Alert band. Punha suru karnyasathi kadhihi ALERT ani area liha.",
}
WEEKLY = {   # inside the 24-hour window: a plain message, one project a line
    "en": "New on MahaRERA in {place} this week:\n{lines}\nAll of {place}: {link}\nReply with a project's name to know more, or ALERT OFF to stop.",
    "hi": "इस हफ्ते {place} में MahaRERA पर नए:\n{lines}\nपूरा {place}: {link}\nज़्यादा जानने के लिए प्रोजेक्ट का नाम लिखें, या बंद करने के लिए ALERT OFF।",
    "hinglish": "Is hafte {place} mein MahaRERA par naye:\n{lines}\nPoora {place}: {link}\nZyada jaanne ke liye project ka naam likhein, ya band karne ke liye ALERT OFF.",
    "mr": "या आठवड्यात {place} मध्ये MahaRERA वर नवीन:\n{lines}\nसंपूर्ण {place}: {link}\nअधिक माहितीसाठी प्रोजेक्टचे नाव लिहा, किंवा बंद करण्यासाठी ALERT OFF.",
    "mr_latn": "Ya athavdyat {place} madhe MahaRERA var navin:\n{lines}\nSampurna {place}: {link}\nAdhik mahitisathi project che nav liha, kiva band karnyasathi ALERT OFF.",
}


def asked(text: str) -> bool:
    return bool(ASKED.match(text or ""))


def _link(key: str, bhk: Optional[int]) -> str:
    slug = key.replace("_", "-")
    return f"{adapters.site_url()}/projects/area/{slug}" + (f"/{bhk}-bhk" if bhk else "")


def turn(conv: dict, text: str, lang: str, now: datetime) -> str:
    """The reply to an ALERT message, and the chat's alert set or dropped."""
    rest = ASKED.sub(" ", text or "", count=1)
    if OFF.search(rest):
        conv["alert"] = None
        return L.pick(STOPPED, lang)
    m = BHK.search(rest)
    bhk = int(m.group(1) or m.group(2)) if m else None
    found = pune_places.in_search(BHK.sub(" ", rest))
    if not found:
        return L.pick(ASK_PLACE, lang)
    place = found[0]
    old = conv.get("alert") or {}
    conv["alert"] = {"place": place.key, "name": place.name, "bhk": bhk, "at": now, "checked_at": now,
                     "sent": (old.get("sent") or []) if old.get("place") == place.key else []}
    data = conv.setdefault("data", {})
    data.setdefault("questions", []).append(f"Wants new-project alerts for {place.name}" + (f", {bhk} BHK" if bhk else ""))
    return L.pick(DONE, lang, place=place.name, bhk=L.pick(BHK_PART, lang, bhk=bhk) if bhk else "", link=_link(place.key, bhk))


def project_line(p: dict) -> str:
    who = f" by {p['builder']}" if p.get("builder") else ""
    homes = f", {p['homes']} homes" if p.get("homes") else ""
    return f"{p['name']}{who}{homes}"


def _send_hour(now: datetime) -> bool:
    return (now + IST).hour in SEND_HOURS_IST


async def send_due(db, svc, now: datetime) -> int:
    """Send each due alert its new projects. Returns how many messages went out (or were recorded in dry run)."""
    new_projects = _deps["new_projects"]
    if new_projects is None or not _send_hour(now):
        return 0
    convs = db.get_collection("whatsapp_conversations")
    due = await convs.find({"alert.place": {"$exists": True}, "alert.checked_at": {"$lte": now - WEEK},
                            "opted_out": {"$ne": True}}).to_list(MAX_CHATS)
    sent = 0
    for conv in due:
        a = conv["alert"]
        try:
            # checked first: a crash or a refusal never sends the same week twice
            await convs.update_one({"_id": conv["_id"]}, {"$set": {"alert.checked_at": now}})
            fresh = [p for p in await new_projects(db, a["place"], a["checked_at"] - timedelta(days=1))
                     if p["regno"] not in (a.get("sent") or [])][:MAX_PROJECTS]
            if not fresh:
                continue
            link = _link(a["place"], a.get("bhk"))
            lang = conv.get("language") or "en"
            if svc.in_window(conv, now):
                text = L.pick(WEEKLY, lang, place=a["name"], lines="\n".join(f"• {project_line(p)}" for p in fresh), link=link)
                rec = await svc._send(conv, text, now)
            else:
                names = "; ".join(project_line(p) for p in fresh)
                text = (f"New projects registered in {a['name']} this week: {names}. See them all: {link} "
                        f"(You asked for these alerts. Reply ALERT OFF to stop.)")
                rec = await svc.send_template(conv, TEMPLATE, "en", [a["name"], names, link], text, now)
            msgs = (conv.get("messages") or []) + [{"role": "bot", "sent_by": "alert", "text": text, "ts": now, "status": rec["status"]}]
            changes = {"messages": msgs[-20:], "updated_at": now, "alert.last_status": rec["status"]}
            if rec["status"] in ("sent", "dry_run"):
                changes["alert.sent"] = ((a.get("sent") or []) + [p["regno"] for p in fresh])[-200:]
                changes["alert.last_sent_at"] = now
                sent += 1
            await convs.update_one({"_id": conv["_id"]}, {"$set": changes})
        except Exception as e:   # one chat's failure never stops the others
            log.warning("whatsapp alert for %s failed: %s", conv["_id"][-4:], type(e).__name__)
    return sent


async def loop() -> None:
    from . import config, router   # as jobs.py: the router builds the service, and the service reads this module
    while True:
        if enabled():
            try:
                async with heartbeat("whatsapp_alerts", get_database):
                    n = await send_due(get_database(), router.build_service(config.load()), datetime.utcnow())
                    if n:
                        log.info("whatsapp alerts: %d sent", n)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("whatsapp alerts cycle failed")
        await asyncio.sleep(INTERVAL_S)
