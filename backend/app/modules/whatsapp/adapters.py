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


async def chat_turn(data: dict, text: str, llm, grounding, finder=None, history=None):
    """The website chat's brain (2026-10-18): the LLM leads (chat/agent.py) with the rules engine as its fallback; CHAT_AGENT=off on the
    server goes back to the rules alone, for every channel at once. `history` is the chat so far (role user/bot, text), oldest first."""
    import os
    if os.environ.get("CHAT_AGENT", "on").strip().lower() != "off":
        from app.modules.chat import agent as chat_agent
        return await chat_agent.turn(data, text, llm, grounding, finder=finder, history=history or [], channel="message")
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
        from app.modules.chat.projects import project_cards
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
            cards = [card(by_id[m["listing_id"]], slug) for m in top if m["match_pct"] >= CARD_MIN_PCT and m["listing_id"] in by_id][:3]
            return cards or await project_cards(db, {**req, "transaction": tx})   # no listing fits: our project pages there
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
        if kind in ("post", "calendar") and ref:
            doc = await db.get_collection("content_calendar").find_one({"_id": ref}) or \
                await db.get_collection("content_calendar").find_one({"slug": ref})   # interest links name a post by its slug
            g = await facts_for(Ref.calendar(doc["_id"]), db) if doc else None
            if g:
                return g
            found = await project_for(db, ctx.get("title") or "")   # a campaign post about a project: the project's own facts
            if found:
                g = await project_grounding_for(db, found["ref"])
                if g:
                    return g
        if kind == "project" and ref:
            g = await project_grounding_for(db, ref)
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


# a code typed on its own ("about zy4wad2"): seven code letters with at least one digit, so ordinary words never match
BARE_CODE = re.compile(r"\b(?=[a-hj-km-np-z2-9]*[2-9])" + CODE + r"\b", re.I)


def codes_in(text: str) -> list:
    out = []
    for rx in CODE_PATTERNS + [BARE_CODE]:
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


# ---- where a Messenger / Instagram chat came from, and what we know about it (2026-10-18) ---------------------------
# A DM is answered from what the person was looking at: the post they commented on (our private reply opened the chat), a reel, post
# or story they shared or replied to, the link or ad they opened, a project they name, or one of our guide posts on what they ask.

def _first_line(text: str, limit: int = 90) -> str:
    line = ((text or "").strip().splitlines() or [""])[0].strip()
    return line if len(line) <= limit else line[:limit].rsplit(" ", 1)[0] + "…"


def _calendar_context(doc: dict, how: str) -> dict:
    title = _first_line(doc.get("title") or doc.get("caption") or doc.get("slug") or "our post")
    return {"kind": "calendar", "ref": doc["_id"], "slug": doc.get("slug"), "title": title, "listing_id": None, "sample": False, "code": None,
            "came_from": f"{how} our post “{title}”", "audience": (doc.get("creative") or {}).get("audience") or "buyers"}


def _listing_context(listing_id: str, listing: dict, came_from: str) -> dict:
    return {"kind": "listing", "ref": listing_id, "title": _first_line(listing.get("title") or "our listing"), "listing_id": listing_id,
            "sample": False, "code": None, "came_from": came_from}


async def _post_context(db, ids: list, urls: list, how: str) -> Optional[dict]:
    """A post of ours by its Meta id (a shared reel, a story reply) or its permalink: the calendar row (guides, projects, evergreen posts)
    or the listing it was made from."""
    cal, pubs = db.get_collection("content_calendar"), db.get_collection("publications")
    found = None
    for mid in [str(i) for i in ids if i]:
        found = await cal.find_one({"external_id": mid}) or await pubs.find_one({"external_id": mid})
        if found:
            break
    for url in [u for u in urls if u] if not found else []:
        short = re.search(r"/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)", url)
        if short:
            found = await cal.find_one({"permalink": {"$regex": re.escape(short.group(1))}}) or \
                await pubs.find_one({"permalink": {"$regex": re.escape(short.group(1))}})
            if found:
                break
    if not found:
        return None
    if found.get("listing_id"):  # a publication of a listing
        listing = await db.get_collection("listings").find_one({"_id": found["listing_id"]}) or {}
        return _listing_context(found["listing_id"], listing, f"{how} our post about “{_first_line(listing.get('title') or 'a home')}”")
    if found.get("calendar_id"):
        found = await cal.find_one({"_id": found["calendar_id"]}) or found
    return _calendar_context(found, how)


def link_context(link: dict, how: str) -> dict:
    title = (link.get("title") or "")[:140]
    return {"kind": link.get("kind"), "ref": link.get("ref"), "sample": bool(link.get("sample")), "code": link.get("code"), "title": title,
            "listing_id": link.get("ref") if link.get("kind") == "listing" and not link.get("sample") else None,
            "came_from": f"{how} “{title}”" if title else how}


async def dm_origin(db, platform: str, sender: str, refs: Optional[dict]) -> Optional[dict]:
    """Where this person came from, best evidence first: the link or ad they opened (its ref is an interest code), the post they shared or
    replied to, the comment that made us message them. None when the chat simply started."""
    refs = refs or {}
    try:
        ref = str(refs.get("ref") or "").strip().lower()
        if ref:
            link = await db.get_collection("interest_links").find_one({"code": ref})
            if link:
                return link_context(link, "opened our link for")
        ctx = await _post_context(db, refs.get("media_ids") or [], refs.get("urls") or [],
                                  "replied to" if refs.get("reply_to_story") else "shared")
        if ctx:
            return ctx
        c = await db.get_collection("engage_comments").find_one({"dm_recipient": sender}, sort=[("processed_at", -1)])
        if c:
            said = (c.get("text") or "")[:160]
            if c.get("calendar_id"):
                doc = await db.get_collection("content_calendar").find_one({"_id": c["calendar_id"]})
                if doc:
                    out = _calendar_context(doc, "commented on")
                    out["came_from"] += f": “{said}”"
                    return out
            if c.get("listing_id"):
                listing = await db.get_collection("listings").find_one({"_id": c["listing_id"]}) or {}
                return _listing_context(c["listing_id"], listing,
                                        f"commented on our post about “{_first_line(listing.get('title') or 'a home')}”: “{said}”")
            return {"kind": None, "ref": None, "title": "", "listing_id": None, "sample": False, "code": None,
                    "came_from": f"commented on one of our {platform} posts: “{said}”"}
    except Exception as e:  # where they came from is a help, never a reason to drop the message
        log.info("dm origin failed: %s", type(e).__name__)
    return None


# words that say nothing about a topic, in the languages people write to us in
_STOP = set("""what when where which this that have with from your about there their will would could should please tell know want need
 does into they them then than also just only very more some much many like here kasa kashi kase kuthe kiti kadhi aahe ahet aahet madhe
 sathi karaycha karayche kitna kitni kahan kaise hain hoga milega chahiye mujhe aapka hamara kripya batao bataiye home homes pune
 the and for you are can how why who not but all any our has had was its yes kya hai hum aap yeh woh kar karu kaa kee mein par aur
 ahe aah kay ani aani tar mala tula ghar new kasa kase kashi karyach karycha karaych""".split()) | {"आहे", "का", "कसा", "कशी", "करायचा", "मध्ये", "आणि", "है", "क्या", "में", "और", "की", "के", "का"}
_WORDS = re.compile(r"[a-z][a-z0-9]{2,}|[ऀ-ॿ]{2,}", re.I)


# the same idea in the words people type: 'arj kasa karaycha' asks how to apply
_SAME = {"arj": "apply", "arji": "apply", "arja": "apply", "arz": "apply", "aavedan": "apply", "avedan": "apply", "अर्ज": "apply",
         "आवेदन": "apply", "application": "apply", "kagadpatre": "documents", "kagadpatra": "documents", "कागदपत्रे": "documents",
         "दस्तावेज": "documents", "tarikh": "date", "tarikha": "date", "तारीख": "date", "उत्पन्न": "income", "utpanna": "income",
         "aay": "income", "आय": "income", "sodat": "lottery", "सोडत": "lottery", "लॉटरी": "lottery", "म्हाडा": "mhada"}


def _topic_words(text: str) -> set:
    return {_SAME.get(w.lower(), w.lower()) for w in _WORDS.findall(text or "")} - _STOP


async def guide_for(db, text: str, earlier: str = "", exclude=()) -> Optional[dict]:
    """One of our own guide posts (MHADA, how-to reels: rows with a reply sheet) on what the person asks, by the words they share with it;
    the post's title words count double. None when nothing clearly fits."""
    asked = _topic_words(f"{text} {earlier}")
    if not asked:
        return None
    best, best_score = None, 0
    for doc in await db.get_collection("content_calendar").find({"reply_facts": {"$exists": True, "$ne": []}}).to_list(300):
        title = _topic_words(f"{doc.get('title') or ''} {(doc.get('slug') or '').replace('-', ' ')} {_first_line(doc.get('caption') or '', 200)}")
        body = _topic_words(" ".join(list(doc.get("reply_facts") or []) + [f"{x.get('q', '')} {x.get('a', '')}" for x in doc.get("reply_faq") or []]))
        score = 0 if doc["_id"] in exclude or doc.get("slug") in exclude else 2 * len(asked & title) + len(asked & body)
        newer = best is not None and str(doc.get("due_at") or "") > str(best.get("due_at") or "")
        if score > best_score or (score == best_score and score and newer):
            best, best_score = doc, score
    if best is None or best_score < 3:
        return None
    return _calendar_context(best, "asked about the topic of")


async def project_for(db, text: str) -> Optional[dict]:
    """A builder project one of our agents sells (agent_projects), named in the message: 'Lodha Camelot possession date?'."""
    low = (text or "").lower()
    best = None
    for p in await db.get_collection("agent_projects").find({}).to_list(500):
        name = (p.get("name") or "").lower().strip()
        words = [w for w in re.findall(r"[a-z0-9]+", name) if len(w) >= 5]  # 'camelot', 'abhilasha': the distinctive word is enough
        if name and (name in low or any(re.search(rf"\b{re.escape(w)}\b", low) for w in words[-1:])):
            if best is None or len(name) > len(best.get("name") or ""):
                best = p
    if not best:
        return None
    return {"kind": "project", "ref": best["_id"], "title": best.get("name"), "listing_id": None, "sample": False, "code": None,
            "came_from": f"asked about the project “{best.get('name')}”", "agent_id": best.get("agent_id")}


async def project_grounding_for(db, project_id: str):
    from app.modules.agentprojects.service import public_view
    from app.modules.knowledge.grounding import project_grounding
    proj = await db.get_collection("agent_projects").find_one({"_id": project_id})
    if not proj:
        return None
    prof = await db.get_collection("agent_public_profiles").find_one({"agent_id": proj.get("agent_id")}) or {}
    name = (prof.get("branding_data") or {}).get("business_name") or prof.get("agent_name") or "the agent"
    site = _site_url()
    page = f"{site}/agent/{prof['slug']}/projects/{proj['slug']}" if site and prof.get("slug") and proj.get("slug") else ""
    return project_grounding(public_view(proj), name, page)


def agents_grounding():
    """What we tell an agent about our service: the vetted 'about us' answers that are not for buyers only (knowledge/site.py)."""
    from app.modules.knowledge import site
    from app.modules.knowledge.grounding import Grounding
    g = Grounding(subject="our service for real estate agents", kind="post")
    g.facts = [e.answer for e in site.ENTRIES if getattr(e, "audience", "") != "buyer"]
    g.general = []
    return g


async def listing_state(db, listing_id: str) -> Optional[dict]:
    """The listing behind a link or post, for the chat: what it is (from our record) and whether it is still for sale or rent."""
    doc = await db.get_collection("listings").find_one({"_id": listing_id})
    if not doc:
        return {"live": False}
    return {"live": doc.get("status") in ("live", "under_offer"), "tx": "rent" if doc.get("transaction") == "rent" else "buy",
            "locality": doc.get("locality"), "bhk": doc.get("bhk")}


def trial_url() -> str:
    return f"{_site_url()}/trial" if _site_url() else ""


def brand_name() -> str:
    from app.core import brand
    return brand.NAME


async def listing_agent(db, listing_id: str) -> Optional[str]:
    doc = await db.get_collection("listings").find_one({"_id": listing_id})
    return (doc or {}).get("agent_id")


async def grounded_answer(text: str, grounding, llm):
    """The comment assistant's checked answer (knowledge/reply.py) for a 1:1 chat: facts only, in the person's language, and plainly what is
    not known."""
    from app.modules.knowledge.reply import answer
    return await answer(text, grounding, "chat", llm)


FACTS_REPLY = """You answer someone who wrote to {brand} on Facebook Messenger or Instagram. Use ONLY the FACTS (about {subject}); the
CONVERSATION tells you what short questions refer to. Answer exactly what they asked, like a helpful local advisor: 1 to 4 short sentences,
in {lang}. If the FACTS do not answer it, return "reply": "" (never guess, never answer from general knowledge). No links, phone numbers,
or any number, date, name or promise that the FACTS do not contain; we do not give loans or arrange services the FACTS do not describe.
Return ONE JSON object: {{"reply": "..."}}"""


def _facts_text(grounding) -> str:
    lines = [f"- {f}" for f in list(grounding.facts) + list(getattr(grounding, "area_facts", []) or [])]
    lines += [f"- Q: {x.get('q')} A: {x.get('a')}" for x in list(grounding.faq or []) + list(getattr(grounding, "area_faq", []) or [])]
    return "\n".join(lines)


async def facts_reply(text: str, grounding, lang: str, llm, history: str = "") -> Optional[str]:
    """A DM question answered by the model from one post's (or project's, or our agent service's) facts only, with the conversation for
    meaning, and checked like every reply (no number, name or link the facts do not contain). None when the facts do not answer it."""
    if llm is None or not hasattr(llm, "json") or grounding is None:
        return None
    from app.modules.knowledge.reply import LANG_NAME, valid_text
    facts = _facts_text(grounding)
    if not facts:
        return None
    try:
        raw = await llm.json(FACTS_REPLY.format(brand=brand_name(), subject=grounding.subject, lang=LANG_NAME.get(lang, "English")),
                             f"FACTS:\n{facts}\n\nCONVERSATION:\n{history or '(first message)'}\n\nTHEY ASK NOW:\n{(text or '')[:500]}")
    except Exception as e:
        log.info("facts reply failed: %s", type(e).__name__)
        return None
    reply = " ".join(str((raw or {}).get("reply") or "").split()) if isinstance(raw, dict) else ""
    # the person's own words count as a source in a 1:1 chat ('income 7 lakh' may be said back), as on the website chat
    source = f"{facts} {grounding.subject} {brand_name()} {text}"
    if lang in ("hinglish", "mr_latn"):
        source += " " + " ".join(re.findall(r"[A-Za-z][A-Za-z']+", reply))
    if len(reply) < 12 or reply.strip(" .\"'").lower() in ("reply", "answer", "none", "null", "n/a"):
        return None   # the model sometimes returns the field name or a placeholder instead of an answer
    if not valid_text(reply, source, "chat", 700):
        return None
    return reply


async def prefill_from_title(data: dict, title: str) -> None:
    """A listing that is gone still says what they wanted ('2 BHK for sale in Kharadi'): the chat starts from that, not from 'buy or rent?'."""
    from app.modules.chat import engine as _engine
    work = dict(data)
    try:
        _engine.extract(work, title or "")
    except Exception:
        return
    for k in ("tx", "locality", "bhk", "budget_min", "budget_max"):
        if work.get(k) and not data.get(k):
            data[k] = work[k]
    if data.get("locality"):
        data.setdefault("locality_src", "listing")
    if data.get("bhk"):
        data.setdefault("bhk_src", "listing")
    if "for sale" in (title or "").lower() and not data.get("tx"):
        data["tx"] = "buy"
