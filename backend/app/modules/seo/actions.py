"""One page, one fix, measured: the log both SEO steps write and the undo rules both of them read.

`seo_actions` is the audit trail the owner's Rankings tab shows and the page doctor learns from. `targets` applies the title
fix and `doctor` the faq / links / refresh / description ones, so the rules that keep the two steps from working against
each other live here rather than in either of them (docs/plan/seo-review.md D2, D3, D6):

  - **one fix per page per REST_DAYS, whoever applied it** — `stamp` writes the window, so a title from `targets` and a
    description from `doctor` on the same page cannot both be scored against one position reading;
  - **a value that was measured and undone is never applied again** — `undo` keeps the rejected value in a `<field>_no` list
    on the record, and `blocked` is what each step checks before writing;
  - **an undone action is not measured** — `doctor.measure` skips it, so the results table only holds fixes still standing.
"""
from datetime import datetime
from typing import Optional

from app.modules.newsroom.store import Store

ACTIONS = "seo_actions"
REST_DAYS = 28                   # a page gets one fix per window, so a position move can be put down to one change
FIELD = {"title": "search_name", "description": "seo_description"}   # the fix types that write a value we can put back


def numbers(doc: dict) -> dict:
    """The page's Search Console numbers now, the before/after pair every action is measured on."""
    return {"position": doc.get("gsc_position"), "impressions": int(doc.get("gsc_impressions") or 0),
            "clicks": int(doc.get("gsc_clicks") or 0)}


def blocked(doc: dict, fix: str, value) -> bool:
    """True when this exact value was already applied to this page, measured and undone."""
    return value is not None and value in (doc.get(FIELD[fix] + "_no") or [])


def gain(action: dict) -> Optional[float]:
    """Positions gained (positive = moved up) from before to the latest reading; None until one exists or without positions."""
    after = action.get("after28") or action.get("after14")
    b = (action.get("before") or {}).get("position")
    if not after or b is None or after.get("position") is None:
        return None
    return round(float(b) - float(after["position"]), 1)


async def log_fix(store: Store, doc: dict, fix: str, now: datetime, old=None, new=None, phrase: Optional[str] = None,
                  note: str = "") -> None:
    """One line in the log: what changed on which page, and the page's Search Console numbers before it."""
    await store.db.get_collection(ACTIONS).insert_one({
        "path": f"/projects/{doc.get('page_slug')}", "regno": doc.get("regno") or doc["_id"], "fix": fix, "at": now,
        "phrase": phrase or (doc.get("seo_target") or {}).get("phrase"), "before": numbers(doc), "old": old, "new": new,
        "note": note, "after14": None, "after28": None, "reverted": False})


async def stamp(store: Store, doc_id: str, now: datetime, fix: Optional[str] = None) -> None:
    """Open the page's new fix window. Every step that changes a page calls this, including the ones that change nothing."""
    await store.set_project(doc_id, page_fix_at=now, page_fix=fix)


async def undo(store: Store, doc: dict, action: dict, now: datetime) -> bool:
    """Put a page back the way it was before `action`, and make sure the same value is not tried again.

    Only when the field still holds what that action wrote: if anything changed the page since, the old value is no longer
    this action's to restore. False when there was nothing to undo."""
    field = FIELD.get(action.get("fix") or "")
    if not field or doc.get(field) != action.get("new"):
        return False
    refused = [v for v in dict.fromkeys([*(doc.get(field + "_no") or []), action.get("new")]) if v]
    updates = {field: action.get("old"), field + "_no": refused, "page_fix_at": now, "page_fix": None}
    if field == "search_name":
        # the title's own hold, restarted: targets may write another title only after the window again
        updates["search_name_at"] = now
    await store.set_project(doc["_id"], **updates)
    await store.db.get_collection(ACTIONS).update_one({"_id": action["_id"]}, {"$set": {"reverted": True, "reverted_at": now}})
    return True
