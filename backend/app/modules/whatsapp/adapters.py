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


async def chat_turn(data: dict, text: str, llm, grounding):
    return await engine.turn(data, text, llm, grounding)


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
    """The agent's public name, or None (the caller then says 'the PUNE Property team' in the buyer's language)."""
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
        await contacts.update_one({"_id": existing["_id"]}, {"$set": changes, "$addToSet": {"anon_ids": f"whatsapp:{wa_id}"}})
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
