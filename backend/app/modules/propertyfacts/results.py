"""What happened to a campaign's posts after "Send to calendar": each calendar row's state (waiting, approved, posted) and the
leads from it (clicks on and "I am interested" taps of the post's interest link, keyed by slug and channel; calendar.adapters.with_interest).
Read only: nothing here changes the calendar or the counts."""
from typing import Dict, List

from app.modules.calendar.store import Store as CalendarStore, aware
from app.modules.interest.store import Store as InterestStore

from .schedule import slug_for

STATE = {"planned": "waiting", "approved": "approved", "scheduled": "approved", "published": "posted",
         "failed": "failed", "skipped": "skipped", "removed": "removed"}


async def results(db, run: dict) -> List[Dict]:
    """One entry per calendar row of the run, in campaign order:
    {angle, kind, channel, state, due_at, posted_at, permalink, clicks, interests}."""
    cal, links = CalendarStore(db), InterestStore(db)
    out: List[Dict] = []
    for c in run.get("calendar") or []:
        row = await cal.get(c.get("row_id") or "")
        if not row:
            continue
        channel = "instagram" if row["channel"] == "instagram" else "facebook"
        link = await links.find_link("post", row.get("slug") or slug_for(run["listing_id"], c["angle"]), channel)
        clicks = await links.count(link["code"], "click") if link else 0
        interests = await links.count(link["code"], "interest") if link else 0
        out.append({"angle": c["angle"], "kind": row.get("kind", "post"), "channel": row["channel"],
                    "state": STATE.get(row["status"], row["status"]), "due_at": aware(row.get("due_at")),
                    "posted_at": aware(row.get("published_at")), "permalink": row.get("permalink"),
                    "clicks": clicks, "interests": interests})
    return out
