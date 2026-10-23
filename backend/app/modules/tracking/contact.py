"""Contact status of a lead: has anyone on our side reached them, and who is waiting for whom (owner, 2026-10-23: two form leads sat
unanswered for 10 hours and 3 days and nothing in Studio said so).

Worked out from what is already stored, never typed in:
  whatsapp_conversations  by lead_id, or by the lead's mobile on our number (read only; owned by the whatsapp module)
  dm_conversations        by lead_id (Messenger / Instagram)
  chat_sessions           by the number the visitor gave in the website chat
  contacts.calls          calls a person logged on the lead ("Answered" / "No answer")

States, from the latest thing that happened:
  not_contacted  nothing sent, no call, still New (at = when the lead came in)
  waiting_you    their message is the last one: nobody answered it (bot held back, or a person has to)
  no_reply       we wrote (bot, person or follow-up template) and they never wrote back
  no_answer      the last thing is a call nobody picked up
  in_touch       they wrote and the last word is ours (by = bot or you), or a call was answered
  contacted      moved past New by hand, with nothing here to show how
  closed         won or lost
"""
import re
from datetime import datetime
from typing import Dict, List, Optional

from .summary import CLOSED

THEM = {"user", "in"}
MAX = 1000
PERSON = {"agent", "human", "person"}


def wa_digits(phone) -> Optional[str]:
    """'+91 98765 43210' -> '919876543210'; None unless it is an Indian mobile (same rule as the inbox)."""
    d = re.sub(r"\D", "", str(phone or ""))
    if len(d) == 10 and d[0] in "6789":
        d = "91" + d
    return d if len(d) == 12 and d.startswith("91") and d[2] in "6789" else None


def _who(m: dict) -> str:
    role = m.get("role") or ""
    if role in THEM:
        return "them"
    return "you" if role in PERSON or m.get("sent_by") in ("owner", "agent", "person") else "bot"


def _touches(convs: List[dict], calls: List[dict]) -> List[dict]:
    out = [{"who": _who(m), "at": m["ts"], "channel": c["channel"]}
           for c in convs for m in (c["doc"].get("messages") or []) if isinstance(m.get("ts"), datetime)]
    out += [{"who": "call", "at": k["ts"], "answered": k.get("outcome") == "answered", "channel": "call"}
            for k in calls if isinstance(k.get("ts"), datetime)]
    return sorted(out, key=lambda t: t["at"])


def state_of(contact: dict, convs: List[dict]) -> dict:
    stage = contact.get("stage") or "new"
    if stage in CLOSED:
        return {"state": "closed", "at": None, "by": None, "channel": None}
    touches = _touches(convs, contact.get("calls") or [])
    if not touches:
        if stage == "new":
            return {"state": "not_contacted", "at": contact.get("created_at"), "by": None, "channel": None}
        return {"state": "contacted", "at": contact.get("contacted_at"), "by": "you", "channel": None}
    last = touches[-1]
    if last["who"] == "them":
        return {"state": "waiting_you", "at": last["at"], "by": "them", "channel": last["channel"]}
    if last["who"] == "call":
        return {"state": "in_touch" if last["answered"] else "no_answer", "at": last["at"], "by": "you", "channel": "call"}
    heard = any(t["who"] == "them" or (t["who"] == "call" and t["answered"]) for t in touches)
    return {"state": "in_touch" if heard else "no_reply", "at": last["at"], "by": last["who"], "channel": last["channel"]}


async def conversations_by_lead(db, contacts: List[dict]) -> Dict[str, List[dict]]:
    """{lead id: [{channel, doc}]} for the given leads, three reads in all (the leads list asks for up to 200 at once)."""
    ids = [c["_id"] for c in contacts]
    digits = {wa_digits(c.get("phone")): c["_id"] for c in contacts if wa_digits(c.get("phone"))}
    phones = {c["phone"]: c["_id"] for c in contacts if c.get("phone")}
    agents = list({c["agent_id"] for c in contacts})
    out: Dict[str, List[dict]] = {i: [] for i in ids}
    if not ids:
        return out
    col = db.get_collection
    wa = await col("whatsapp_conversations").find({"lead_id": {"$in": ids}}, {"messages": 1, "lead_id": 1, "wa_id": 1}).to_list(MAX)
    seen = {d["_id"] for d in wa}
    wa += [d for d in await col("whatsapp_conversations").find({"wa_id": {"$in": list(digits)}}, {"messages": 1, "lead_id": 1, "wa_id": 1}).to_list(MAX)
           if d["_id"] not in seen]
    for d in wa:
        lid = d.get("lead_id") if d.get("lead_id") in out else digits.get(d.get("wa_id"))
        if lid in out:
            out[lid].append({"channel": "whatsapp", "doc": d})
    for d in await col("dm_conversations").find({"lead_id": {"$in": ids}}, {"messages": 1, "lead_id": 1, "platform": 1}).to_list(MAX):
        out[d["lead_id"]].append({"channel": d.get("platform") or "messenger", "doc": d})
    if phones:
        profs = await col("agent_public_profiles").find({"agent_id": {"$in": agents}}, {"slug": 1}).to_list(MAX)
        slugs = [p["slug"] for p in profs if p.get("slug")]
        for d in await col("chat_sessions").find({"agent_slug": {"$in": slugs}, "data.phone": {"$in": list(phones)}},
                                                 {"messages": 1, "data.phone": 1}).to_list(MAX):
            lid = phones.get((d.get("data") or {}).get("phone"))
            if lid in out:
                out[lid].append({"channel": "website", "doc": d})
    return out
