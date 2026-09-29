"""GET /inbox/today: the agent's daily snapshot. Owner scoped (only this agent's contacts and listings)."""
from datetime import datetime, timedelta

from . import requirement as reqmod, scoring
from .summary import CLOSED

MAX_HOT, MAX_FOLLOW_UPS = 5, 10


def _headline(uncontacted: int, due: int, hot: int) -> str:
    if uncontacted:
        return (f"{uncontacted} buyer{' hasn' if uncontacted == 1 else 's haven'}'t been contacted today.")
    if due:
        return f"{due} follow-up{' is' if due == 1 else 's are'} due today."
    if hot:
        return f"{hot} hot buyer{'' if hot == 1 else 's'} to talk to today."
    return "You're all caught up."


IST = timedelta(hours=5, minutes=30)


def end_of_ist_day(now_utc: datetime) -> datetime:
    """End of the agent's current day (India time) as a naive UTC datetime; stored times are naive UTC."""
    ist = now_utc + IST
    return ist.replace(hour=23, minute=59, second=59, microsecond=999999) - IST


async def build_today(svc, agent_id: str) -> dict:
    now = svc.now()
    end_of_day = end_of_ist_day(now)
    contacts = await svc.contacts.find({"agent_id": agent_id}).to_list(2000)
    listings = await svc._agent_listings(agent_id)
    rows = []
    for c in contacts:
        value = scoring.score(c.get("score_base", 0), c["last_activity_at"], now)
        rows.append((c, value, scoring.temperature(value)))
    open_rows = [r for r in rows if r[0]["stage"] not in CLOSED]

    hot_rows = sorted((r for r in open_rows if r[2] == "hot"), key=lambda r: -r[1])
    hot_buyers = []
    for c, value, temp in hot_rows[:MAX_HOT]:
        req = reqmod.public(c.get("requirement"))
        top = svc._matches(c, req, listings)
        hot_buyers.append({
            "id": c["_id"], "name": c["name"], "phone": c["phone"], "score": value, "temperature": temp,
            "requirement_line": reqmod.requirement_line(req),
            "top_match": {"title": top[0]["title"], "match_pct": top[0]["match_pct"]} if top else None})

    due_rows = sorted((r for r in open_rows if r[0].get("follow_up_due_at") and r[0]["follow_up_due_at"] <= end_of_day),
                      key=lambda r: r[0]["follow_up_due_at"])
    follow_ups = []
    for c, _, _ in due_rows[:MAX_FOLLOW_UPS]:
        due = c["follow_up_due_at"]
        overdue = due < now
        days = (now - due).days
        reason = ("Follow-up overdue" + (f" by {days} day{'s' if days != 1 else ''}" if days >= 1 else "")
                  if overdue else "Follow-up due today")
        follow_ups.append({"id": c["_id"], "name": c["name"], "phone": c["phone"], "due_at": due,
                           "overdue": overdue, "reason": reason})

    counts = {
        "new_enquiries_24h": sum(1 for c, _, _ in rows if c["created_at"] >= now - timedelta(hours=24)),
        "hot": len(hot_rows),
        "site_visits": sum(1 for c, _, _ in rows if c["stage"] == "site_visit"),
        "follow_ups_due": len(due_rows),
        "uncontacted": sum(1 for c, _, _ in rows if c["stage"] == "new"),
    }
    return {"counts": counts, "hot_buyers": hot_buyers, "follow_ups": follow_ups,
            "headline": _headline(counts["uncontacted"], counts["follow_ups_due"], counts["hot"])}
