"""Project check in a chat (docs/plan/project-check.md): Messenger, Instagram and WhatsApp, inside the shared ChatBrain.

  start   the "Check my project" button, a short "status" / "RERA status" message, or a MahaRERA number -> ask for the name
  search  one clear match -> the card; several -> up to 3 to pick from ("reply 1, 2 or 3"); none -> say so, ask again once
  card    what the possession date did (areastats/check.py), homes booked, the /check/<slug> link, then one ask: bought or planning?
  stage   1 bought -> what to do now; 2 planning -> the chat carries the project and goes on as the buyer conversation (lead, agent)

State lives on the chat as conv["check"] = {step: ask | pick | stage, options, regno, slug, name, misses, at}. Any message the step
does not expect leaves the flow (None: the brain answers as usual). Never a word the register does not hold.
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional

from . import adapters, lang as L

EXPIRE = timedelta(minutes=30)
MAX_MISSES = 2
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

REGNO = re.compile(r"\bP[A-Z]?\d{9,13}\b", re.I)
START = re.compile(r"check\s+(?:my\s+)?project|\b(?:project|rera|maharera|possession)?\s*status\b|स्टेटस|स्थिती तपासा", re.I)
NOT_PROJECT = re.compile(r"mhada|lottery|application|म्हाडा|लॉटरी|अर्ज|order|payment|loan", re.I)
FILLER = re.compile(r"\b(?:check|my|the|of|for|project|projects|maharera|rera|status|possession|please|pls|plz|what|whats|is|kya|hai|"
                    r"batao|bataiye|ka|ki|ke|sathi|chi|cha|che)\b|'s\b|स्टेटस|स्थिती तपासा|[🔍?!.,:;-]", re.I)
BOUGHT = re.compile(r"^\s*1\b|\b(bought|booked|purchased|owner|liya|ghetla|ghetle)\b|खरीद|घेतल|बुक", re.I)
PLANNING = re.compile(r"^\s*2\b|\b(plan|planning|thinking|want to buy|looking)\b|सोच|विचार|लेना है|घ्याय", re.I)

ASK = {
    "en": "Send the project name or its MahaRERA number (P52…), and I will check its status on MahaRERA.",
    "hi": "प्रोजेक्ट का नाम या उसका MahaRERA नंबर (P52…) भेजें, मैं MahaRERA पर उसका स्टेटस देखकर बताता हूँ।",
    "hinglish": "Project ka naam ya uska MahaRERA number (P52…) bhejein, main MahaRERA par uska status check karke batata hoon.",
    "mr": "प्रोजेक्टचे नाव किंवा त्याचा MahaRERA नंबर (P52…) पाठवा, मी MahaRERA वर त्याचा स्टेटस तपासून सांगतो.",
    "mr_latn": "Projectche naav kiva tyacha MahaRERA number (P52…) pathva, mi MahaRERA var tyacha status tapasun sangto.",
}
NONE = {
    "en": "I could not find “{q}” in our MahaRERA register for Pune district. Try another spelling, or the MahaRERA number (P52…) from your agreement.",
    "hi": "पुणे ज़िले के हमारे MahaRERA रजिस्टर में “{q}” नहीं मिला। दूसरी स्पेलिंग आज़माएँ, या अपने एग्रीमेंट से MahaRERA नंबर (P52…) भेजें।",
    "hinglish": "Pune district ke hamare MahaRERA register mein “{q}” nahi mila. Doosri spelling try karein, ya apne agreement se MahaRERA number (P52…) bhejein.",
    "mr": "पुणे जिल्ह्याच्या आमच्या MahaRERA रजिस्टरमध्ये “{q}” सापडले नाही. दुसरे स्पेलिंग वापरून पाहा, किंवा तुमच्या करारातील MahaRERA नंबर (P52…) पाठवा.",
    "mr_latn": "Pune jilhyachya aamchya MahaRERA register madhe “{q}” sapadle nahi. Dusre spelling vaparun paha, kiva tumchya kararatil MahaRERA number (P52…) pathva.",
}
PICK = {
    "en": "Which one is yours? Reply 1, 2 or 3:",
    "hi": "आपका कौन सा है? 1, 2 या 3 लिखें:",
    "hinglish": "Aapka kaun sa hai? 1, 2 ya 3 likhein:",
    "mr": "तुमचा कोणता? 1, 2 किंवा 3 लिहा:",
    "mr_latn": "Tumcha konta? 1, 2 kiva 3 liha:",
}
VERDICT = {
    "passed": {
        "en": "Possession date has passed: {now}. Ask the builder for the occupancy certificate (OC).",
        "hi": "पज़ेशन की तारीख निकल चुकी है: {now}। बिल्डर से ऑक्यूपेंसी सर्टिफिकेट (OC) माँगें।",
        "hinglish": "Possession date nikal chuki hai: {now}. Builder se occupancy certificate (OC) maangein.",
        "mr": "पझेशनची तारीख उलटून गेली आहे: {now}. बिल्डरकडे ऑक्युपन्सी सर्टिफिकेट (OC) मागा.",
        "mr_latn": "Possession chi tarikh ulatun geli aahe: {now}. Builder kade occupancy certificate (OC) maga.",
    },
    "moved": {
        "en": "Possession date moved later by {m} months: now {now}, it was {first} at registration.",
        "hi": "पज़ेशन की तारीख {m} महीने आगे खिसकी है: अब {now}, रजिस्ट्रेशन के समय {first} थी।",
        "hinglish": "Possession date {m} mahine aage khiski hai: ab {now}, registration ke time {first} thi.",
        "mr": "पझेशनची तारीख {m} महिने पुढे गेली आहे: आता {now}, नोंदणीच्या वेळी {first} होती.",
        "mr_latn": "Possession chi tarikh {m} mahine pudhe geli aahe: aata {now}, nondanichya veli {first} hoti.",
    },
    "unchanged": {
        "en": "Possession date unchanged since registration: {now}.",
        "hi": "रजिस्ट्रेशन से अब तक पज़ेशन की तारीख नहीं बदली: {now}।",
        "hinglish": "Registration se ab tak possession date nahi badli: {now}.",
        "mr": "नोंदणीपासून पझेशनची तारीख बदललेली नाही: {now}.",
        "mr_latn": "Nondanipasun possession chi tarikh badalleli nahi: {now}.",
    },
    "dated": {
        "en": "Possession date on MahaRERA: {now}.",
        "hi": "MahaRERA पर पज़ेशन की तारीख: {now}।",
        "hinglish": "MahaRERA par possession date: {now}.",
        "mr": "MahaRERA वर पझेशनची तारीख: {now}.",
        "mr_latn": "MahaRERA var possession chi tarikh: {now}.",
    },
    "no_date": {
        "en": "MahaRERA shows no possession date for it yet.",
        "hi": "MahaRERA पर अभी इसकी पज़ेशन की तारीख नहीं दिखती।",
        "hinglish": "MahaRERA par abhi iski possession date nahi dikhti.",
        "mr": "MahaRERA वर अजून याची पझेशनची तारीख दिसत नाही.",
        "mr_latn": "MahaRERA var ajun yachi possession chi tarikh disat nahi.",
    },
}
BOOKED = {
    "en": "{b} of {t} homes booked.",
    "hi": "{t} में से {b} घर बुक हो चुके हैं।",
    "hinglish": "{t} mein se {b} ghar book ho chuke hain.",
    "mr": "{t} पैकी {b} घरे बुक झाली आहेत.",
    "mr_latn": "{t} paiki {b} ghare book jhali aahet.",
}
SOURCE = {
    "en": "From MahaRERA public records{read}.",
    "hi": "MahaRERA के सार्वजनिक रिकॉर्ड से{read}।",
    "hinglish": "MahaRERA ke public record se{read}.",
    "mr": "MahaRERA च्या सार्वजनिक नोंदींमधून{read}.",
    "mr_latn": "MahaRERA chya public records madhun{read}.",
}
READ = {"en": ", read {d}", "hi": ", {d} को पढ़ा", "hinglish": ", {d} ko padha", "mr": ", {d} रोजी वाचले", "mr_latn": ", {d} roji vachle"}
STAGE = {
    "en": "Reply 1 if you have bought here, 2 if you are planning to buy.",
    "hi": "यहाँ घर ले चुके हैं तो 1 लिखें, लेने का सोच रहे हैं तो 2।",
    "hinglish": "Yahan ghar le chuke hain to 1 likhein, lene ka soch rahe hain to 2.",
    "mr": "इथे घर घेतले असेल तर 1 लिहा, घेण्याचा विचार करत असाल तर 2.",
    "mr_latn": "Ithe ghar ghetle asel tar 1 liha, ghenyacha vichar karat asal tar 2.",
}
BOUGHT_TEXT = {
    "en": "Keep your agreement's possession date handy. If possession comes later than that date, RERA (section 18) lets you claim interest for every month of delay, or a refund; complaints go to MahaRERA. Send STATUS any time to check again.",
    "hi": "अपने एग्रीमेंट में लिखी पज़ेशन की तारीख संभाल कर रखें। अगर पज़ेशन उस तारीख के बाद मिले, तो RERA (धारा 18) के तहत आप हर महीने की देरी का ब्याज या रिफंड माँग सकते हैं; शिकायत MahaRERA पर होती है। दोबारा देखने के लिए कभी भी STATUS लिखें।",
    "hinglish": "Apne agreement mein likhi possession date sambhal kar rakhein. Agar possession us date ke baad mile, to RERA (section 18) ke tahat aap har mahine ki deri ka interest ya refund maang sakte hain; complaint MahaRERA par hoti hai. Dobara check karne ke liye kabhi bhi STATUS likhein.",
    "mr": "तुमच्या करारातील पझेशनची तारीख जपून ठेवा. पझेशन त्या तारखेनंतर मिळाले, तर RERA (कलम 18) नुसार तुम्ही प्रत्येक महिन्याच्या उशिराचे व्याज किंवा परतावा मागू शकता; तक्रार MahaRERA कडे होते. पुन्हा तपासण्यासाठी कधीही STATUS लिहा.",
    "mr_latn": "Tumchya kararatil possession chi tarikh japun theva. Possession tya tarkhenantar milale, tar RERA (kalam 18) nusar tumhi pratyek mahinyachya ushirache vyaj kiva partava magu shakta; takrar MahaRERA kade hote. Punha tapasnyasathi kadhihi STATUS liha.",
}
PLANNING_TEXT = {
    "en": "Good. Before you book, look at the homes booked and the builder's other projects on the link above. Would you like an agent to share prices and arrange a site visit at {name}?",
    "hi": "ठीक है। बुक करने से पहले ऊपर के लिंक पर बुक हुए घर और बिल्डर के दूसरे प्रोजेक्ट देख लें। क्या आप चाहेंगे कि एजेंट आपको {name} की कीमतें बताएँ और साइट विज़िट करवाएँ?",
    "hinglish": "Theek hai. Book karne se pehle upar ke link par booked ghar aur builder ke doosre projects dekh lein. Kya aap chahenge ki agent aapko {name} ke prices bataye aur site visit karwaye?",
    "mr": "छान. बुक करण्यापूर्वी वरच्या लिंकवर बुक झालेली घरे आणि बिल्डरचे इतर प्रोजेक्ट पाहा. एजंटने तुम्हाला {name} च्या किमती सांगाव्यात आणि साइट व्हिजिट करून द्यावी, असे हवे आहे का?",
    "mr_latn": "Chhan. Book karnyapurvi varchya link var book jhaleli ghare ani builder che itar project paha. Agent ne tumhala {name} chya kimati sangavyat ani site visit karun dyavi, ase have aahe ka?",
}


def starts(text: str) -> bool:
    """A message that asks for a project's status: the button, "status", "RERA status", "check my project", or a MahaRERA number."""
    t = (text or "").strip()
    if REGNO.search(t):
        return True
    return len(t.split()) <= 7 and bool(START.search(t)) and not NOT_PROJECT.search(t)


def _month(day: Optional[str]) -> str:
    if not day:
        return ""
    y, m, _ = day.split("-")
    return f"{_MONTHS[int(m) - 1]} {y}"


def _day(day: Optional[str]) -> str:
    if not day:
        return ""
    y, m, d = day.split("-")
    return f"{int(d)} {_MONTHS[int(m) - 1]} {y}"


def card_text(s: dict, lang: str, site: str) -> str:
    """The check as a message: name, what the date did, bookings, source, the link, then the one ask."""
    head = s["name"] + (f" ({s['place']})" if s.get("place") else "")
    lines = [f"{head}\nMahaRERA {s['regno']}",
             L.pick(VERDICT[s["state"]], lang, now=_month(s.get("completion_now")), first=_month(s.get("completion_at_registration")),
                    m=s.get("months_later") or 0)]
    if s.get("total") and s.get("booked") is not None and s["booked"] <= s["total"]:
        lines.append(L.pick(BOOKED, lang, b=f"{s['booked']:,}", t=f"{s['total']:,}"))
    read = L.pick(READ, lang, d=_day(s["read_at"])) if s.get("read_at") else ""
    lines.append(L.pick(SOURCE, lang, read=read))
    if site:
        lines.append(f"{site}/check/{s['slug']}?r={s['regno']}")
    return "\n".join(lines) + "\n\n" + L.pick(STAGE, lang)


def _options_text(hits: List[dict], lang: str) -> str:
    rows = [f"{i}. {h.get('marketed_name') or h['name']}" + (f", {h['place_name']}" if h.get("place_name") else "")
            + (f" ({h['promoter']})" if h.get("promoter") else "") for i, h in enumerate(hits, 1)]
    return L.pick(PICK, lang) + "\n" + "\n".join(rows)


async def _search(db, q: str) -> List[dict]:
    from app.modules.areastats import pages
    return await pages.search(db, q, limit=3)


async def _status(db, regno: str) -> Optional[dict]:
    from app.modules.areastats import check
    return await check.status(db, regno)


async def _show(db, conv: dict, regno: str, lang: str, now: datetime) -> Optional[str]:
    s = await _status(db, regno)
    if s is None:
        return None
    conv["check"] = {"step": "stage", "regno": s["regno"], "slug": s["slug"], "name": s["name"], "at": now}
    conv.setdefault("checked", [])
    conv["checked"] = ([s["regno"]] + [r for r in conv["checked"] if r != s["regno"]])[:5]
    return card_text(s, lang, adapters._site_url())


async def _find(db, conv: dict, q: str, lang: str, now: datetime) -> str:
    hits = await _search(db, q)
    regno = REGNO.search(q)
    if hits and (len(hits) == 1 or regno or hits[0].get("regno", "").upper() == q.strip().upper()):
        shown = await _show(db, conv, hits[0]["regno"], lang, now)
        if shown:
            return shown
    if hits:
        conv["check"] = {"step": "pick", "options": [h["regno"] for h in hits], "at": now}
        return _options_text(hits, lang)
    misses = int((conv.get("check") or {}).get("misses") or 0) + 1
    conv["check"] = {"step": "ask", "misses": misses, "at": now} if misses < MAX_MISSES else None
    return L.pick(NONE, lang, q=q.strip()[:60])


async def _carry(db, conv: dict, c: dict, stage: str) -> None:
    """The chat carries the project they checked, so the lead says it. Planning to buy in a project one of our agents sells: that agent's
    chat, answered from the project's facts; anything else: the register project as the lead's interest."""
    did = "is planning to buy there" if stage == "planning" else "has bought a home there"
    came_from = f"checked the MahaRERA status of “{c.get('name')}” and {did}"
    proj = await db.get_collection("agent_projects").find_one({"rera_no": c.get("regno")}) if stage == "planning" else None
    if proj:
        conv["context"] = {"kind": "project", "ref": proj["_id"], "title": proj.get("name") or c.get("name"), "listing_id": None,
                           "sample": False, "code": None, "agent_id": proj.get("agent_id"), "came_from": came_from}
        if proj.get("agent_id") and conv.get("routed_by") in (None, "owner"):
            conv["agent_id"], conv["routed_by"] = proj["agent_id"], "check"
    else:
        conv["context"] = {"kind": "register", "ref": c.get("regno"), "slug": c.get("slug"), "title": c.get("name"), "stage": stage,
                           "came_from": came_from}


async def turn(db, conv: dict, text: str, lang: str, now: Optional[datetime] = None) -> Optional[str]:
    """The check's reply to this message, or None when the message is not part of a check (the brain answers it)."""
    now = now or datetime.utcnow()
    t = (text or "").strip()
    c = conv.get("check") or {}
    if c and (not isinstance(c.get("at"), datetime) or now - c["at"] > EXPIRE):
        conv["check"], c = None, {}
    step = c.get("step")
    if step == "stage":
        stage = "planning" if PLANNING.search(t) else "bought" if BOUGHT.search(t) else None
        if stage:
            conv["check"] = None
            conv["check_stage"] = {"stage": stage, "regno": c.get("regno"), "at": now}
            await _carry(db, conv, c, stage)
            return L.pick(PLANNING_TEXT, lang, name=c.get("name") or "") if stage == "planning" else L.pick(BOUGHT_TEXT, lang)
        conv["check"], step = None, None   # something else: a new check, or the brain answers it
    elif step == "pick":
        m = re.fullmatch(r"\s*([1-3])\s*[.)]?\s*", t)
        options = c.get("options") or []
        if m and int(m.group(1)) <= len(options):
            return await _show(db, conv, options[int(m.group(1)) - 1], lang, now)
        if not starts(t) and 2 <= len(t) and len(t.split()) <= 8:
            return await _find(db, conv, t, lang, now)   # another name
        conv["check"], step = None, None
    elif step == "ask":
        if not starts(t) and 2 <= len(t) and len(t.split()) <= 8:
            return await _find(db, conv, t, lang, now)
        conv["check"], step = None, None
    if not starts(t):
        return None
    regno = REGNO.search(t)
    if regno:
        return await _find(db, conv, regno.group(0).upper(), lang, now)
    named = " ".join(FILLER.sub(" ", t).split())
    if len(named) >= 3:   # "status of Gera World of Joy": the name is already there
        return await _find(db, conv, named, lang, now)
    conv["check"] = {"step": "ask", "at": now}
    return L.pick(ASK, lang)
