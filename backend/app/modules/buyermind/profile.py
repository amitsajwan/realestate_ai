"""The buyer profile: what we know of one buyer, what it suggests and what we still do not know (docs/plan/buyer-mind.md step 2).

Two halves, kept apart on purpose:
  said     facts the buyer gave or did (form answers, what they wrote, pages read), straight from the lead's handover card
           (inbox/handover.py), so the profile never says more than the lead record does;
  implied  what the deep mind read into it ("family: asked about schools twice"), each a short sentence from its last brief,
           shown to the agent as a reading, never sent to the buyer as a fact.
`unknown` starts as the card's missing facts and the mind may add to it ("which tower").

Pure: the caller reads the card and the brief; the service stores the result in `buyer_profiles` (_id = the lead id).
"""
from datetime import datetime
from typing import Any, Optional

# lines of the card that are about the buyer; the phone stays out of the profile (and so out of every prompt)
SAID_LINES = ("Name", "Project", "Wants", "Home", "Budget", "Buying when", "Paying by", "Areas", "They wrote", "Came from",
              "Enquired", "Pages seen", "So far", "Notes")
MAX_IMPLIED = 6
MAX_LINE = 240


def _lines(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    out = []
    for x in items:
        s = " ".join(str(x).split())[:MAX_LINE] if isinstance(x, (str, int, float)) else ""
        if s and s not in out:
            out.append(s)
    return out


def rows(card: dict) -> dict[str, str]:
    """The card's lines ({label, value}, inbox/handover.py) that are about the buyer, by label; never the phone."""
    out = {}
    for line in card.get("lines") or []:
        label, value = (line.get("label"), line.get("value")) if isinstance(line, dict) else (tuple(line) + (None, None))[:2]
        if label in SAID_LINES and value:
            out[label] = " ".join(str(value).split())[:MAX_LINE * 2]
    return out


def build(lead_id: str, agent_id: str, card: dict, brief: Optional[dict], now: datetime) -> dict:
    """The profile from the lead's card and, when there is one, the mind's last brief."""
    said = rows(card)
    brief = brief or {}
    unknown = list(dict.fromkeys(_lines(card.get("missing")) + _lines(brief.get("unknown"))))
    return {"_id": lead_id, "agent_id": agent_id, "said": said, "implied": _lines(brief.get("implied"))[:MAX_IMPLIED],
            "unknown": unknown, "buyer": brief.get("buyer") or None, "temperature": brief.get("temperature") or None,
            "updated_at": now}


def prompt_text(card: dict) -> str:
    """The card as the model reads it: every buyer line, never the phone."""
    missing = _lines(card.get("missing"))
    text = "\n".join(f"{k}: {v}" for k, v in rows(card).items())
    return text + (f"\nNot known yet: {', '.join(missing)}" if missing else "")
