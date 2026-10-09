"""Follow-up after a reply is sent (docs/RADAR.md §6, v4): a small checkpointed state machine per lead, stored on the signal as
`followup` = {state, due_at, history}. Each step waits in Mongo (days apart, surviving restarts), and every message it suggests
waits for a person to send it: nothing is posted.

    waiting --(their reply under our comment)--> replied: answer drafted for the operator
    waiting --(clicked our link)---------------> clicked: hand to the agent (warm)
    waiting --(48h, nothing)-------------------> nudge: one gentle second reply suggested, then waiting_2
    waiting_2 --(5 more days, nothing)---------> closed
    replied / clicked --(operator marks done)--> closed

The graph has five states and two timers, so it is plain code over Mongo rather than a LangGraph dependency; the shape is the
same (state, checkpoint, human-approved edges)."""
import logging
from datetime import timedelta
from typing import Dict, Optional

from app.platform.youtube import YouTubeError

from . import store
from .models import Intent

log = logging.getLogger(__name__)

NUDGE_AFTER_H = 48
CLOSE_AFTER_H = 24 * 5
OPEN = ("waiting", "waiting_2")
ACTION = ("replied", "clicked", "nudge")   # states shown in the follow-up queue


def start(now) -> dict:
    return {"state": "waiting", "due_at": now + timedelta(hours=NUDGE_AFTER_H), "history": [{"state": "waiting", "at": now}]}


def _move(f: dict, state: str, now, due_h: Optional[float] = None, **extra) -> dict:
    hist = list(f.get("history") or []) + [{"state": state, "at": now}]
    return {**f, **extra, "state": state, "due_at": (now + timedelta(hours=due_h)) if due_h else None, "history": hist[-12:]}


async def _their_reply(sig: dict) -> Optional[str]:
    """The asker's newest reply under the comment we answered (YouTube only; 1 quota unit)."""
    if sig.get("source") != "youtube":
        return None
    from .sources.youtube import thread_replies
    try:
        replies = await thread_replies(sig["external_id"])
    except YouTubeError as e:
        log.info("radar: follow-up read failed: %s", e)
        return None
    mine = [r for r in replies if sig.get("author_id") and r["author_id"] == sig.get("author_id")]
    sent_at = (sig.get("labelled_at") or store.now()).isoformat()[:19]
    newer = [r for r in mine if (r.get("at") or "")[:19] > sent_at]
    return newer[-1]["text"] if newer else None


async def _answer(db, sig: dict, text: str, llm) -> str:
    from . import draft as drafting
    from .score import find_matches
    from .verify import find_project
    intent = Intent.model_validate(sig.get("intent") or {})
    project = await find_project(db, intent, sig.get("context", ""), text)
    matches = await find_matches(db, intent)
    out = await drafting.compose(text, intent, matches, sig.get("link") or "", project, llm)
    return out.text


NUDGE = {"en": "Hi again! Did the MahaRERA record help? Happy to answer anything else here.",
         "hinglish": "Hi! MahaRERA record dekh paaye? Aur kuch poochna ho toh yahan pooch lo.",
         "hi": "Hi! MahaRERA record dekh paaye? Aur kuch poochna ho toh yahan pooch lo.",
         "mr": "नमस्कार! MahaRERA रेकॉर्ड पाहिला का? अजून काही विचारायचे असल्यास इथे विचारा."}


async def step(db, llm, limit: int = 100) -> Dict[str, int]:
    """Advance every follow-up whose timer is due."""
    counts = {"replied": 0, "clicked": 0, "nudge": 0, "closed": 0, "waiting": 0}
    now = store.now()
    coll = db.get_collection(store.SIGNALS)
    for sig in await coll.find({"followup.state": {"$in": list(OPEN)}, "followup.due_at": {"$lte": now}}).to_list(limit):
        f = sig["followup"]
        if sig.get("clicks"):
            f = _move(f, "clicked", now)
        else:
            text = await _their_reply(sig)
            if text:
                f = _move(f, "replied", now, their_reply=text, draft=await _answer(db, sig, text, llm))
            elif f["state"] == "waiting":
                lang = ((sig.get("intent") or {}).get("language")) or "en"
                f = _move(f, "nudge", now, draft=NUDGE.get(lang, NUDGE["en"]))
            else:
                f = _move(f, "closed", now)
        await coll.update_one({"_id": sig["_id"]}, {"$set": {"followup": f}})
        counts[f["state"]] = counts.get(f["state"], 0) + 1
    return counts


async def done(db, sid, action: str) -> Optional[dict]:
    """The operator acted on a follow-up: sent the nudge (wait again), sent the answer, handed over, or closed it."""
    sig = await db.get_collection(store.SIGNALS).find_one({"_id": sid})
    if not sig or not sig.get("followup"):
        return None
    now, f = store.now(), sig["followup"]
    if action == "sent" and f["state"] == "nudge":
        f = _move(f, "waiting_2", now, CLOSE_AFTER_H)
    elif action == "sent" and f["state"] == "replied":
        f = _move(f, "waiting_2", now, NUDGE_AFTER_H)
    else:
        f = _move(f, "closed", now, reason=action)
    await db.get_collection(store.SIGNALS).update_one({"_id": sid}, {"$set": {"followup": f}})
    return f
