"""Deterministic lead summary and next-best-action. Only states facts present in the data."""
from datetime import datetime, timedelta
from typing import Dict, Optional

from .requirement import bhk_text, budget_text

CLOSED = ("won", "lost")
_TIMELINE_PHRASE = {"now": "and wants to move right away", "1_3_months": "within 1-3 months",
                    "3_6_months": "within 3-6 months", "exploring": "but is just looking for now"}
_FIN_PHRASE = {"home_loan": "on a home loan", "own_funds": "with own funds", "undecided": "not sure about financing yet"}
_CLOSING = {"hot": "Likely ready for a site visit.", "warm": "Showing interest, worth a follow-up.",
            "cold": "Still early, keep in touch."}


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def event_counts(events: list, titles: Dict[str, str]) -> dict:
    counts = {"views": 0, "whatsapp": 0, "calls": 0, "shares": 0, "top_listing": None, "top_views": 0}
    per: Dict[str, int] = {}
    for e in events:
        t = e["type"]
        if t == "listing_view":
            counts["views"] += 1
            if e.get("listing_id"):
                per[e["listing_id"]] = per.get(e["listing_id"], 0) + 1
        elif t == "whatsapp_click":
            counts["whatsapp"] += 1
        elif t == "call_click":
            counts["calls"] += 1
        elif t == "share":
            counts["shares"] += 1
    if per:
        lid = max(sorted(per), key=lambda k: per[k])
        counts["top_views"], counts["top_listing"] = per[lid], titles.get(lid)
    return counts


def _times(n: int) -> str:
    return "once" if n == 1 else f"{n} times"


def ai_summary(req: Optional[dict], counts: dict, source: Optional[str], stage: str, temperature: str) -> str:
    sentences = []
    if req:
        bhk = bhk_text(req.get("bhk"))
        s = f"Wants a {bhk}" if bhk else "Looking for a home"
        b = budget_text(req.get("budget_min_inr"), req.get("budget_max_inr"))
        if b:
            s += f" around {b}" if (req.get("budget_min_inr") and req.get("budget_max_inr")) else f" {b}"
        if req.get("localities"):
            s += " in " + _join(req["localities"])
        if req.get("timeline"):
            s += " " + _TIMELINE_PHRASE[req["timeline"]]
        if req.get("financing"):
            s += ", " + _FIN_PHRASE[req["financing"]]
        sentences.append(s + ".")
    else:
        sentences.append("No requirement shared yet.")
    acts = []
    if counts["views"]:
        target = f"the {counts['top_listing']} listing" if counts["top_listing"] else "listings"
        acts.append(f"viewed {target} {_times(counts['top_views'] or counts['views'])}"
                    if counts["top_listing"] else f"viewed listings {_times(counts['views'])}")
    if counts["whatsapp"]:
        acts.append("tapped WhatsApp")
    if counts["calls"]:
        acts.append("tapped call")
    if counts["shares"]:
        acts.append("shared a listing")
    if acts:
        text = _join(acts)
        sentences.append(text[0].upper() + text[1:] + ".")
    if source:
        sentences.append(f"Came in via {source}.")
    if stage == "won":
        sentences.append("Deal closed.")
    elif stage == "lost":
        sentences.append("Marked as lost.")
    else:
        sentences.append(_CLOSING[temperature])
    return " ".join(sentences)


def next_action(contact: dict, temperature: str, req: Optional[dict], now: datetime) -> dict:
    stage = contact["stage"]
    if stage in CLOSED:  # deviation from the contract's rule list: nothing to chase on a closed lead
        return {"type": "follow_up", "reason": "Deal closed" if stage == "won" else "Marked as lost"}
    if stage == "site_visit":
        return {"type": "follow_up", "reason": "Confirm the visit"}
    if temperature == "hot":
        return {"type": "schedule_visit", "reason": "Hot buyer, suggest a site visit"}
    if stage == "new" and contact.get("phone") and now - contact["created_at"] > timedelta(hours=24):
        return {"type": "call", "reason": "New enquiry not contacted yet, respond within a day"}
    if req and req.get("timeline") in ("now", "1_3_months"):
        return {"type": "whatsapp", "reason": "Wants to buy soon, send matching options on WhatsApp"}
    return {"type": "follow_up", "reason": "Keep the conversation going"}
