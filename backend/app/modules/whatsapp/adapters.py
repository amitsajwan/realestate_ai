"""The ONLY place the WhatsApp module touches other modules: chat engine, knowledge, interest links, tracking requirement helpers, contacts
(leads) and notifications. Small functions, so the coupling stays visible and easy to swap. Nothing else in the codebase imports whatsapp.

No edits were needed in chat/engine or knowledge: the engine already works on a plain dict, so WhatsApp pre-fills the buyer's number and
name (we have them from Meta) and stores the lead itself.
"""
import logging
import re
import uuid
from datetime import datetime
from typing import Optional

from app.modules.chat import engine
from app.modules.knowledge.grounding import Ref, facts_for
from app.modules.knowledge.reply import detect_language as _detect
from app.modules.tracking import requirement as rq

log = logging.getLogger(__name__)

# ---- chat engine --------------------------------------------------------------------------------------------------
NAME_OK = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,40}$")


def new_chat_state(phone: str, name: Optional[str]) -> dict:
    """Engine state for a WhatsApp buyer: the number is known and the buyer started the chat, so the engine never asks for it and never makes
    its own lead (`lead_done`); we keep the lead up to date ourselves after every turn."""
    d = engine.new_data()
    d.update(phone=phone, consent_shown=True, lead_done=True)
    if name and NAME_OK.match(name.strip()):
        d["name"] = name.strip().title()[:40]
    return d


async def chat_turn(data: dict, text: str, llm, grounding, finder=None):
    return await engine.turn(data, text, llm, grounding, finder=finder)


def _site_url() -> str:
    import os
    return (os.environ.get("PUBLIC_SITE_URL") or "").strip().rstrip("/")


async def homes_finder(db, agent_id: Optional[str]):
    """The engine's `finder` for a chat away from the website: up to three of the agent's live public homes that fit what the buyer said,
    the same matching and cards as the website chat. None (no homes are shown) without an agent, a public profile or PUBLIC_SITE_URL,
    because a card is only useful with a link the buyer can open."""
    if not agent_id or not _site_url():
        return None
    try:
        from app.modules.chat.service import CARD_MIN_PCT, MAX_LISTINGS_SCANNED, PUBLIC, card
        from app.modules.listings.freshness import is_hidden
        from app.modules.tracking import matching
        profile = await db.get_collection("agent_public_profiles").find_one({"agent_id": agent_id, "is_public": True})
    except Exception as e:  # homes are a help, never a reason to drop a buyer's message
        log.info("homes finder unavailable: %s", type(e).__name__)
        return None
    if not profile or not profile.get("slug"):
        return None
    slug = profile["slug"]

    async def find(req: dict, exclude: Optional[str]) -> list:
        try:
            docs = await db.get_collection("listings").find({"agent_id": agent_id, **PUBLIC}).to_list(MAX_LISTINGS_SCANNED)
            now = datetime.utcnow()
            docs = [d for d in docs if d["_id"] != exclude and not is_hidden(d, now)]
            by_id = {d["_id"]: d for d in docs}
            tx = req.pop("transaction", "sale")
            top = matching.top_matches(req, docs, tx, limit=10)
            return [card(by_id[m["listing_id"]], slug) for m in top if m["match_pct"] >= CARD_MIN_PCT and m["listing_id"] in by_id][:3]
        except Exception as e:
            log.info("homes finder failed: %s", type(e).__name__)
            return []
    return find


def card_lines(cards: list) -> str:
    """Home cards as message text, one line each with its link: '• 2 BHK in Kharadi, 1,100 sq ft, ₹78 Lakh: https://…'. Samples say so."""
    site = _site_url()
    out = []
    for c in cards or []:
        bits = [c.get("title") or "Home"]
        if c.get("carpet_sqft"):
            bits.append(f"{int(c['carpet_sqft']):,} sq ft")
        if c.get("price_text"):
            bits.append(c["price_text"])
        label = " (sample)" if c.get("sample") else ""
        out.append(f"• {', '.join(bits)}{label}: {site}{c.get('url') or ''}")
    return "\n".join(out)


def summary(data: dict) -> str:
    return engine.summary(data).replace("Chat enquiry", "WhatsApp enquiry", 1)


def requirement_fields(data: dict) -> tuple:
    """(fields, sources) in tracking's requirement shape, from what the engine extracted. The buyer typed them, so they are 'stated'."""
    fields, sources = {}, {}
    if data.get("bhk"):
        fields["bhk"], sources["bhk"] = data["bhk"], "stated"
    if data.get("budget_min") is not None or data.get("budget_max") is not None:
        fields["budget_min_inr"], fields["budget_max_inr"], sources["budget"] = data.get("budget_min"), data.get("budget_max"), "stated"
    for k in ("timeline", "financing"):
        if data.get(k):
            fields[k], sources[k] = data[k], "stated"
    if data.get("locality") and data["locality"] != "Other":
        fields["localities"], sources["localities"] = [data["locality"]], "stated"
    return fields, sources


# ---- knowledge ----------------------------------------------------------------------------------------------------
def detect_language(text: str) -> str:
    return _detect(text)


async def grounding_for(db, context: Optional[dict], locality: Optional[str]):
    """What the buyer is asking about: the home/post behind the interest code they came from, else the area they named. None when unknown."""
    ctx = context or {}
    try:
        kind, ref = ctx.get("kind"), ctx.get("ref")
        if kind == "listing" and ref:
            if ctx.get("sample"):
                g = await facts_for(Ref.sample(ref), db)
            else:
                doc = await db.get_collection("listings").find_one({"_id": ref, "status": {"$in": ["live", "under_offer"]}})
                g = await facts_for(Ref.listing(ref), db) if doc else None
            if g:
                return g
        if kind == "post" and ref:
            g = await facts_for(Ref.calendar(ref), db)
            if g:
                return g
        if locality and locality != "Other":
            return await facts_for(Ref.area(locality), db)
    except Exception as e:  # knowledge is a help, never a reason to drop a buyer's message
        log.info("whatsapp grounding failed: %s", type(e).__name__)
    return None


async def translate(body: str, lang: str, llm) -> str:
    """A vetted English answer in the buyer's language via the knowledge module's checked translator; English when it cannot."""
    try:
        from app.modules.knowledge.reply import _localise
        text, _ = await _localise(body, lang, "chat", llm)
        return text
    except Exception:
        return body


# ---- interest links -----------------------------------------------------------------------------------------------
CODE = r"([a-hj-km-np-z2-9]{7})"
CODE_PATTERNS = [re.compile(r"/i/" + CODE + r"\b", re.I), re.compile(r"\bref\.?\s*[:#-]?\s*" + CODE + r"\b", re.I),
                 re.compile(r"\binterested in\s+" + CODE + r"\b", re.I)]


def codes_in(text: str) -> list:
    out = []
    for rx in CODE_PATTERNS:
        for m in rx.finditer(text or ""):
            c = m.group(1).lower()
            if c not in out:
                out.append(c)
    return out


async def find_interest_link(db, text: str) -> Optional[dict]:
    links = db.get_collection("interest_links")
    for code in codes_in(text):
        link = await links.find_one({"code": code})
        if link:
            return link
    return None


def interest_target_agent(link: dict, owner_agent_id: str) -> str:
    """Same rule as the interest module: samples and educational pages belong to the platform owner, homes to their agent."""
    if (link.get("sample") or link.get("kind") == "page") and owner_agent_id:
        return owner_agent_id
    return link.get("agent_id") or owner_agent_id


async def record_interest_event(db, code: str, anon_id: str, now: datetime) -> None:
    try:
        from app.modules.interest.store import Store
        await Store(db).add_event(code, "interest", anon_id, now)
    except Exception as e:
        log.info("whatsapp: interest event not stored: %s", type(e).__name__)


async def agent_name(db, agent_id: str):
    """The agent's public name, or None (the caller then says 'the Avasetu team' in the buyer's language)."""
    p = await db.get_collection("agent_public_profiles").find_one({"agent_id": agent_id}) or {}
    return p.get("agent_name") or p.get("display_name") or None


# ---- leads (contacts) ---------------------------------------------------------------------------------------------
CONSENT_BASIS = "buyer started the WhatsApp chat"


async def upsert_lead(db, *, agent_id: str, phone: str, wa_id: str, name: Optional[str], data: dict, message: str, now: datetime,
                      phone_number_id: str, interest: Optional[dict] = None) -> tuple:
    """Create or update the buyer's lead. Returns (contact_id, created). Dedupes by (agent, phone) so a buyer who also used the website chat
    stays one lead."""
    contacts = db.get_collection("contacts")
    fields, sources = requirement_fields(data)
    text = summary(data)
    existing = await contacts.find_one({"agent_id": agent_id, "phone": phone})
    if existing:
        wa = {**(existing.get("whatsapp") or {"opted_out": False}), "wa_id": wa_id, "phone_number_id": phone_number_id, "summary": text,
              "last_inbound_at": now}
        changes = {"last_activity_at": now, "last_message": message[:1000], "whatsapp": wa}
        if fields:
            changes["requirement"] = rq.merge(existing.get("requirement"), fields, sources)
        if not (existing.get("consent") or {}).get("given_at"):
            changes["consent"] = {"given_at": now, "purpose": "enquiry follow-up", "basis": CONSENT_BASIS, "channel": "whatsapp"}
        add = {"anon_ids": f"whatsapp:{wa_id}"}
        if (interest or {}).get("code"):   # every post a buyer came through counts for that post (interest report)
            add["interest_codes"] = interest["code"]
            if not existing.get("interest_code"):
                changes["interest_code"] = interest["code"]
        await contacts.update_one({"_id": existing["_id"]}, {"$set": changes, "$addToSet": add})
        return existing["_id"], False
    cid = uuid.uuid4().hex
    await contacts.insert_one({
        "_id": cid, "agent_id": agent_id, "name": (name or data.get("name") or "WhatsApp buyer")[:100], "phone": phone,
        "message": text, "anon_ids": [f"whatsapp:{wa_id}"], "stage": "new", "source": "whatsapp", "utm": {},
        "first_listing_id": (interest or {}).get("listing_id"),
        "consent": {"given_at": now, "purpose": "enquiry follow-up", "basis": CONSENT_BASIS, "channel": "whatsapp"},
        "score_base": 10, "created_at": now, "last_activity_at": now, "last_message": message[:1000], "notes": [],
        "requirement": rq.merge(None, fields, sources) if fields else None,
        "interest_code": (interest or {}).get("code"),
        "interest_codes": [interest["code"]] if (interest or {}).get("code") else [],
        "whatsapp": {"wa_id": wa_id, "phone_number_id": phone_number_id, "summary": text, "opted_out": False, "last_inbound_at": now},
    })
    return cid, True


async def update_lead_summary(db, contact_id: str, data: dict) -> None:
    fields, sources = requirement_fields(data)
    contacts = db.get_collection("contacts")
    doc = await contacts.find_one({"_id": contact_id})
    if not doc:
        return
    changes = {"whatsapp": {**(doc.get("whatsapp") or {}), "summary": summary(data)}}
    if fields:
        changes["requirement"] = rq.merge(doc.get("requirement"), fields, sources)
    await contacts.update_one({"_id": contact_id}, {"$set": changes})


async def mark_lead_opt_out(db, contact_id: Optional[str], opted_out: bool, now: datetime) -> None:
    if not contact_id:
        return
    contacts = db.get_collection("contacts")
    doc = await contacts.find_one({"_id": contact_id})
    if not doc:
        return
    changes = {"whatsapp": {**(doc.get("whatsapp") or {}), "opted_out": opted_out, "opted_out_at": now if opted_out else None}}
    if opted_out and doc.get("consent"):
        changes["consent"] = {**doc["consent"], "withdrawn_at": now}
    elif not opted_out:  # START: the buyer opened the chat again
        changes["consent"] = {**(doc.get("consent") or {}), "given_at": now, "withdrawn_at": None, "basis": CONSENT_BASIS, "channel": "whatsapp"}
    await contacts.update_one({"_id": contact_id}, {"$set": changes})


# ---- notifications ------------------------------------------------------------------------------------------------
async def notify(db, agent_id: str, kind: str, text: str, ref: dict, now: datetime) -> None:
    from app.modules.notifications.service import notify as _notify
    await _notify(db, agent_id, kind, text, ref, now)


# ---- claim your free trial (agents) --------------------------------------------------------------------------------
TRIAL_TEXT = {
    "issued": {
        "en": "Your {brand} free trial is ready. 1 month free, every property, no card.\n\nYour sign-up code: {code}\n"
              "Sign in here: {join} (enter this WhatsApp number and the code).",
        "hi": "आपका {brand} फ्री ट्रायल तैयार है। 1 महीना फ्री, हर प्रॉपर्टी, कोई कार्ड नहीं।\n\nआपका साइन-अप कोड: {code}\n"
              "यहाँ साइन इन करें: {join} (यही WhatsApp नंबर और कोड डालें)।",
        "mr": "तुमचा {brand} फ्री ट्रायल तयार आहे. 1 महिना फ्री, प्रत्येक प्रॉपर्टी, कार्ड नको.\n\nतुमचा साइन-अप कोड: {code}\n"
              "इथे साइन इन करा: {join} (हाच WhatsApp नंबर आणि कोड टाका).",
    },
    "too_soon": {
        "en": "We sent your sign-up code a little while ago; it still works. Sign in here: {join}",
        "hi": "आपका साइन-अप कोड हमने थोड़ी देर पहले भेजा है, वह अभी भी चलेगा। यहाँ साइन इन करें: {join}",
        "mr": "तुमचा साइन-अप कोड थोड्या वेळापूर्वी पाठवला आहे, तो अजून चालेल. इथे साइन इन करा: {join}",
    },
    "full": {
        "en": "Today's free trials are all taken. We have saved your request and will send your code here soon.",
        "hi": "आज के सभी फ्री ट्रायल भर गए हैं। आपकी रिक्वेस्ट सेव है, आपका कोड जल्दी यहीं भेजेंगे।",
        "mr": "आजचे सगळे फ्री ट्रायल भरले आहेत. तुमची विनंती सेव्ह आहे, तुमचा कोड लवकरच इथे पाठवू.",
    },
    "blocked": {
        "en": "This number cannot start a trial. Please reply here if you think this is a mistake.",
        "hi": "इस नंबर से ट्रायल शुरू नहीं हो सकता। अगर यह गलती है तो यहीं जवाब दें।",
        "mr": "या नंबरवरून ट्रायल सुरू होऊ शकत नाही. ही चूक वाटत असेल तर इथेच उत्तर द्या.",
    },
}


async def claim_trial(db, phone: str, lang: str, now: Optional[datetime] = None) -> tuple:
    """An agent sent TRIAL: issue (or re-issue) his sign-up code and say how to use it. Never a lead: he is not a buyer.
    Returns (reply, claim status)."""
    from app.core import brand
    from app.core.config import settings
    from app.modules.onboarding.invites import InviteService
    from app.modules.onboarding.trial import TrialService
    clock = (lambda: now) if now is not None else datetime.utcnow
    claim = await TrialService(db, InviteService(db, settings.jwt_secret_key, now=clock), now=clock).claim(phone, "whatsapp")
    lang = lang if lang in ("en", "hi", "mr") else "en"
    join = f"{settings.public_site_url.rstrip('/')}/join?phone={phone[3:]}"
    return TRIAL_TEXT[claim.status if claim.status in TRIAL_TEXT else "issued"][lang].format(
        brand=brand.NAME, code=claim.code or "", join=join), claim.status


# An agent writing to our number after his trial (or any agent with an account): a person on our team answers him, the bot only says so
AGENT_TEXT = {
    "en": "Hi {name}, thanks for writing. Our team reads every message here and will reply soon.\nTo add a property now: {studio}",
    "hi": "नमस्ते {name}, मैसेज के लिए धन्यवाद। हमारी टीम यहाँ हर मैसेज पढ़ती है और जल्दी जवाब देगी।\nअभी प्रॉपर्टी जोड़ने के लिए: {studio}",
    "mr": "नमस्कार {name}, मेसेजसाठी धन्यवाद. आमची टीम इथे प्रत्येक मेसेज वाचते आणि लवकरच उत्तर देईल.\nआता प्रॉपर्टी जोडण्यासाठी: {studio}",
}
AGENT_TEXT_NOT_SIGNED_IN = {
    "en": "Hi, thanks for writing. Our team will reply here soon.\nYour sign-up code is in the message above. Sign in here: {join}",
    "hi": "नमस्ते, मैसेज के लिए धन्यवाद। हमारी टीम जल्दी यहीं जवाब देगी।\nआपका साइन-अप कोड ऊपर वाले मैसेज में है। यहाँ साइन इन करें: {join}",
    "mr": "नमस्कार, मेसेजसाठी धन्यवाद. आमची टीम लवकरच इथे उत्तर देईल.\nतुमचा साइन-अप कोड वरच्या मेसेजमध्ये आहे. इथे साइन इन करा: {join}",
}


async def agent_for_phone(db, phone: str, exclude: str = "") -> Optional[dict]:
    """The agent behind this WhatsApp number: an account with this phone, or a live sign-up code sent to it. None for a buyer.
    `exclude` (the owner's own account) stays a buyer, so the owner can still try the buyer chat from his phone."""
    user = await db.get_collection("users").find_one({"phone": phone})
    if user and str(user["_id"]) == exclude:
        return None
    inv = await db.get_collection("invites").find_one({"_id": phone})
    if not user and not (inv and not inv.get("revoked")):
        return None
    name = " ".join(p for p in ((user or {}).get("first_name"), (user or {}).get("last_name")) if p).strip()
    return {"user_id": str(user["_id"]) if user else None, "name": name or None, "signed_up": bool(user)}


def agent_ack(agent: dict, phone: str, lang: str) -> str:
    from app.core.config import settings
    site = settings.public_site_url.rstrip("/")
    lang = lang if lang in ("en", "hi", "mr") else "en"
    if not agent.get("signed_up"):
        return AGENT_TEXT_NOT_SIGNED_IN[lang].format(join=f"{site}/join?phone={phone[3:]}")
    first = (agent.get("name") or "").split(" ")[0]
    return AGENT_TEXT[lang].format(name=first, studio=f"{site}/studio/listings/new").replace(" ,", ",")  # no name: "Hi, thanks"


def trial_claims_on() -> bool:
    from app.modules.onboarding.trial import enabled
    return enabled()


# ---- Messenger / Instagram DM leads -------------------------------------------------------------------------------
DM_LABEL = {"messenger": "Messenger", "instagram": "Instagram"}
DM_SOURCE = {"messenger": "facebook", "instagram": "instagram"}


async def find_dm_lead(db, platform: str, sender: str) -> Optional[dict]:
    """The lead this DM sender already has: one the comment assistant made when it messaged them after a comment (`dm.id`), or one an
    earlier DM made."""
    contacts = db.get_collection("contacts")
    return await contacts.find_one({"dm.id": sender}) or await contacts.find_one({"anon_ids": f"{platform}_dm:{sender}"})


async def upsert_dm_lead(db, *, agent_id: str, platform: str, sender: str, data: dict, message: str, now: datetime,
                         interest: Optional[dict] = None) -> tuple:
    """Create or update the DM buyer's lead. Returns (contact_id, created). No number until the buyer shares one (the chat engine asks, with
    the consent line); a shared number joins an existing lead with that number for the agent rather than making a second one."""
    contacts = db.get_collection("contacts")
    fields, sources = requirement_fields(data)
    text = summary(data).replace("WhatsApp enquiry", f"{DM_LABEL[platform]} enquiry", 1)
    phone = (data.get("phone") or "").strip()
    consent = {"given_at": now, "purpose": "enquiry follow-up", "basis": f"shared their number in a {DM_LABEL[platform]} chat",
               "channel": platform}
    existing = await find_dm_lead(db, platform, sender)
    if phone and not (existing and existing.get("phone")):
        same = await contacts.find_one({"agent_id": agent_id, "phone": phone})
        if same and (not existing or same["_id"] != existing["_id"]):
            if existing and not existing.get("phone") and hasattr(contacts, "delete_one"):
                await contacts.delete_one({"_id": existing["_id"]})  # the number-less placeholder joins the lead that has the number
            existing = same
    dm = {"channel": DM_SOURCE[platform], "id": sender, "platform": platform, "summary": text, "last_inbound_at": now}
    if existing:
        changes = {"last_activity_at": now, "last_message": message[:1000], "dm": {**(existing.get("dm") or {}), **dm}}
        if fields:
            changes["requirement"] = rq.merge(existing.get("requirement"), fields, sources)
        if phone and not existing.get("phone"):
            changes.update(phone=phone, score_base=max(int(existing.get("score_base") or 0), 25))
            if not (existing.get("consent") or {}).get("given_at"):
                changes["consent"] = consent
        if data.get("name") and (existing.get("name") or "") in ("", f"{DM_LABEL[platform]} buyer"):
            changes["name"] = data["name"][:100]  # the buyer told us their name after the lead was made
        await contacts.update_one({"_id": existing["_id"]}, {"$set": changes, "$addToSet": {"anon_ids": f"{platform}_dm:{sender}"}})
        return existing["_id"], False
    cid = uuid.uuid4().hex
    await contacts.insert_one({
        "_id": cid, "agent_id": agent_id, "name": (data.get("name") or f"{DM_LABEL[platform]} buyer")[:100], "phone": phone,
        "message": text, "anon_ids": [f"{platform}_dm:{sender}"], "stage": "new", "source": DM_SOURCE[platform], "utm": {},
        "first_listing_id": (interest or {}).get("listing_id"), "consent": consent if phone else None,
        "score_base": 25 if phone else 10, "created_at": now, "last_activity_at": now, "last_message": message[:1000], "notes": [],
        "requirement": rq.merge(None, fields, sources) if fields else None, "interest_code": (interest or {}).get("code"), "dm": dm,
    })
    return cid, True


async def mark_dm_opt_out(db, contact_id: Optional[str], opted_out: bool, now: datetime) -> None:
    if not contact_id:
        return
    contacts = db.get_collection("contacts")
    doc = await contacts.find_one({"_id": contact_id})
    if not doc:
        return
    changes = {"dm": {**(doc.get("dm") or {}), "opted_out": opted_out, "opted_out_at": now if opted_out else None}}
    if opted_out and doc.get("consent"):
        changes["consent"] = {**doc["consent"], "withdrawn_at": now}
    await contacts.update_one({"_id": contact_id}, {"$set": changes})
