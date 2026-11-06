"""What a buyer told us on the website goes with them to WhatsApp (owner, 2026-11-06: "chat means WhatsApp also, and context should be
kept"; docs/plan/chat-reach.md). A WhatsApp conversation used to start empty, so a buyer who had given their size and budget was asked again.

Two ways across:
  the chat's own link   "Continue on WhatsApp" fills in "(chat <ref>)", which names the website session
  their number          anyone else who writes: the lead with that number, its requirement and the pages its browsers read

Only what the buyer told us or read goes across, and it fills only what the WhatsApp chat does not know yet: what they say there wins.
Read only here: chat_sessions is this module's, contacts and events are read through tracking's query functions."""
import re
import uuid
from typing import List, Optional

from app.modules.tracking import visits

from . import plan, visit

REF = re.compile(r"\(chat\s+([a-f0-9]{8})\)", re.I)
MAX_READ = 6
MAX_QUESTIONS = 3


def new_ref() -> str:
    return uuid.uuid4().hex[:8]


def ref_in(text: Optional[str]) -> Optional[str]:
    m = REF.search(text or "")
    return m.group(1).lower() if m else None


def without_ref(text: str) -> str:
    return " ".join(REF.sub(" ", text or "").split())


def from_session(data: dict) -> dict:
    """What the website chat knows, as carried over. `read` outlives the visit (chat.service keeps the latest visit's reading)."""
    read = data.get("read") or []
    project = next((i["name"] for i in reversed(read) if i.get("kind") == "project" and i.get("name")), None)
    keep = {k: data.get(k) for k in ("locality", "bhk", "tx", "timeline", "budget_min", "budget_max", "name")}
    return {**keep, "lang": data.get("lang"), "plan": data.get("plan"), "project": project,
            "read": [i["label"] for i in read if i.get("label")][-MAX_READ:], "questions": list(data.get("questions") or [])[-MAX_QUESTIONS:]}


async def session_by_ref(db, ref: str) -> Optional[dict]:
    s = await db.get_collection("chat_sessions").find_one({"wa_ref": ref})
    return from_session(s.get("data") or {}) if s else None


async def from_lead(db, phone: str) -> Optional[dict]:
    """What the lead with this number holds: the requirement, and the pages read by the browsers on it. None when no such lead."""
    if not phone:   # DMs have no number; a lead with no number is not them
        return None
    leads = await db.get_collection("contacts").find({"phone": phone}).sort("last_activity_at", -1).limit(1).to_list(1)
    if not leads:
        return None
    lead = leads[0]
    req = lead.get("requirement") or {}
    areas: List[str] = req.get("localities") or []
    browsers = [a for a in lead.get("anon_ids") or [] if not a.startswith(("whatsapp:", "chat-", "ip-"))]
    paths = await visits.recent_pages(db, lead.get("agent_id"), browsers)
    labels = [i["label"] for i in lead.get("pages_read") or [] if i.get("label")]
    items: List[dict] = []
    if paths:
        items = await visit.pages_read(db, paths, {}, visit.place_name)
        labels = labels or [i["label"] for i in items]
    return {"locality": areas[0] if areas else None, "bhk": req.get("bhk"), "timeline": req.get("timeline"),
            "budget_min": req.get("budget_min_inr"), "budget_max": req.get("budget_max_inr"), "plan": plan.latest(paths),
            "project": next((i["name"] for i in reversed(items) if i.get("kind") == "project"), None),
            "read": labels[-MAX_READ:], "questions": []}


def apply(d: dict, c: Optional[dict]) -> None:
    """Fill what this chat does not know yet; mark the chat as read either way, so it is looked up once."""
    d["carried"] = True
    if not c:
        return
    for f in ("locality", "bhk"):
        if c.get(f) and not d.get(f):
            d[f], d[f + "_src"] = c[f], "web"
    for f in ("tx", "timeline", "name"):
        if c.get(f) and not d.get(f):
            d[f] = c[f]
    if d.get("budget_min") is None and d.get("budget_max") is None:
        d["budget_min"], d["budget_max"] = c.get("budget_min"), c.get("budget_max")
    if c.get("plan") and not d.get("plan"):
        d["plan"] = c["plan"]
    d["carried_read"], d["carried_questions"] = c.get("read") or [], c.get("questions") or []
    if d.get("plan") and d["plan"]["label"] not in d["carried_read"]:
        d["carried_read"] = d["carried_read"] + [d["plan"]["label"]]
