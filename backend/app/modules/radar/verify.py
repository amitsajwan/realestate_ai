"""Verify before you buy: find the MahaRERA project a comment is about and say what its record shows (docs/RADAR.md §5).
Only numbers the register holds are used: the filed completion date, how far it moved since registration, homes booked.
No verdicts ("safe", "risky"): the buyer reads the record and decides."""
import re
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from .models import Intent

STOP = {"pune", "the", "by", "at", "in", "phase", "ph", "project", "projects", "homes", "flats", "flat", "plots", "plot",
        "new", "launch", "review", "bhk", "2bhk", "3bhk", "1bhk", "and", "&", "-", "|", "luxury", "luxurious", "sample"}
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


@dataclass
class Project:
    name: str
    regno: str
    path: str
    line: str           # what the record shows, one sentence


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())


def _tokens(s: str) -> List[str]:
    return [t for t in _norm(s).split() if t not in STOP and len(t) > 1]


def best_match(names: List[str], text: str) -> Optional[int]:
    """Index of the project whose distinctive name words all appear in the text; the longest such name wins
    ("Kolte Patil Life Republic" beats "Life"). Single-word names must be at least 6 letters to count."""
    words = set(_tokens(text))
    best, best_len = None, 0
    for i, n in enumerate(names):
        toks = _tokens(n)
        if not toks or (len(toks) == 1 and len(toks[0]) < 6):
            continue
        if all(t in words for t in toks) and len(toks) > best_len:
            best, best_len = i, len(toks)
    return best


def _month(iso: Optional[str]) -> Optional[str]:
    try:
        d = date.fromisoformat((iso or "")[:10])
    except ValueError:
        return None
    return f"{MONTHS[d.month - 1]} {d.year}"


def record_line(page: dict) -> str:
    parts = [f"MahaRERA {page.get('regno')}"]
    now, first = _month(page.get("completion_now")), _month(page.get("completion_at_registration"))
    if now:
        parts.append(f"completion filed for {now}" + (f" (it was {first} at registration)" if first and first != now else ""))
    total, booked = page.get("units_total"), page.get("units_booked")
    if total and booked and booked <= total:  # 0 usually means the builder has not updated the figure, not that none sold
        parts.append(f"{booked} of {total} units booked")
    return ", ".join(parts)


async def find_project(db, intent: Intent, context: str, text: str) -> Optional[Project]:
    from app.modules.areastats.pages import listing, project_page
    rows = await listing(db, only_indexable=False)
    if not rows:
        return None
    names = [r["name"] for r in rows]
    i = None
    if intent.project:
        i = best_match(names, intent.project)
    if i is None:
        i = best_match(names, f"{text} {context}")
    if i is None:
        return None
    page = await project_page(db, rows[i]["slug"]) or {}
    return Project(rows[i]["name"], rows[i]["regno"], f"/projects/{rows[i]['slug']}", record_line({**rows[i], **page}))
