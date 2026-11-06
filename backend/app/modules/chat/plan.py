"""The East Pune home plan as the chat sees it (docs/plan/chat-reach.md, docs/plan/home-plan.md).

The plan's answers live in its address (frontend lib/site/homeplan.ts), so the chat reads them from this browser's own page views: it
never asks again what the buyer just answered, and it offers the plan only to a buyer who has not done one. BUDGETS and WORK mirror the
frontend's; tests/modules/test_chat_plan.py keeps them equal. No model is asked here."""
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlsplit

from app.core import pune_places

from .phrases import quick

PAGE = "/home-plan"
# (key, how it reads, lowest, highest): frontend lib/site/finder.ts BUDGETS
BUDGETS: Tuple[Tuple[str, str, int, Optional[int]], ...] = (
    ("under-75l", "Under ₹75 L", 0, 7_500_000), ("75l-1cr", "₹75 L – 1 Cr", 7_500_000, 10_000_000),
    ("1-1.5cr", "₹1 – 1.5 Cr", 10_000_000, 15_000_000), ("1.5-2.5cr", "₹1.5 – 2.5 Cr", 15_000_000, 25_000_000),
    ("above-2.5cr", "₹2.5 Cr +", 25_000_000, None))
# key: (how it reads, inside East Pune, the area it stands for until they name another): frontend lib/site/homeplan.ts WORK
WORK = {"kharadi": ("Kharadi", True, "Kharadi"), "magarpatta": ("Magarpatta, Hadapsar", True, None),
        "airport": ("Viman Nagar, Airport", True, None), "home": ("home", True, None),
        "west": ("Hinjawadi, Baner, Wakad", False, "Hinjawadi"), "elsewhere": ("elsewhere in Pune", False, None)}
SIZES = ("1", "2", "3", "4")
EAST = {p.name.lower() for p in pune_places.PLACES if p.zone == pune_places.Z_EAST}


def read(path: Optional[str]) -> Optional[dict]:
    """A plan's address as the chat's history item, or None when it is not a complete plan (work, budget and size are what make one)."""
    url = urlsplit(path or "")
    q = parse_qs(url.query)
    one = lambda k: (q.get(k) or [""])[0].strip().lower()   # noqa: E731
    work, budget, bhk = one("work"), one("budget"), one("bhk")
    band = next((b for b in BUDGETS if b[0] == budget), None)
    if not url.path.startswith(PAGE + "/result") or work not in WORK or band is None or bhk not in SIZES:
        return None
    want = f"{bhk}+ BHK" if bhk == "4" else f"{bhk} BHK"
    want = f"{want}, {band[1]}"
    return {"kind": "plan", "path": str(path)[:200], "want": want, "work": work, "budget": budget, "bhk": int(bhk), "east": WORK[work][1],
            "label": f"Home plan: {want}, works in {WORK[work][0]}" if work != "home" else f"Home plan: {want}, works from home"}


def latest(paths: List[str]) -> Optional[dict]:
    """The newest complete plan among `paths` (oldest first)."""
    return next((p for p in map(read, reversed(paths)) if p), None)


def prefill(d: dict) -> None:
    """Their plan's size, budget and area stand for theirs until they say others, so the chat skips those questions."""
    p = d.get("plan")
    if not p:
        return
    declined = d.get("declined") or []
    if not d.get("bhk") and "bhk" not in declined:
        d["bhk"], d["bhk_src"] = p["bhk"], "history"
    band = next((b for b in BUDGETS if b[0] == p["budget"]), None)
    if band and d.get("budget_min") is None and d.get("budget_max") is None and "budget" not in declined:
        d["budget_min"], d["budget_max"] = band[2] or None, band[3]
    area = WORK[p["work"]][2]
    if area and not d.get("locality") and "locality" not in declined:
        d["locality"], d["locality_src"] = area, "history"


def east(locality: Optional[str]) -> bool:
    return (locality or "").strip().lower() in EAST


def can_offer(d: dict, channel: str) -> bool:
    """Once per chat, to a buyer with no plan yet, in or not yet tied to East Pune (the plan's only side of the city). On the website only
    on our own pages: an agent's site keeps its buyers. WhatsApp and DMs are ours."""
    if d.get("plan") or d.get("plan_offered") or d.get("handed_off") or d.get("audience") == "agent":
        return False
    if channel == "web" and (d.get("audience") != "buyer" or (d.get("page") or {}).get("site") != "house"):
        return False
    return not d.get("locality") or east(d["locality"])


def link(d: dict, lang: str, site: str = "") -> dict:
    """The plan's questions, with what the chat already knows ticked, as {label, url}."""
    q = {}
    bhk = d.get("bhk")
    if isinstance(bhk, (int, float)) and bhk >= 1:
        q["bhk"] = "4" if bhk >= 4 else str(int(bhk))
    top, low = d.get("budget_max"), d.get("budget_min")
    if isinstance(top, (int, float)) and top > 0:
        q["budget"] = next(b[0] for b in BUDGETS if b[3] is None or top <= b[3])
    elif isinstance(low, (int, float)) and low > 0:
        q["budget"] = next(b[0] for b in BUDGETS if b[3] is None or low < b[3])
    return {"label": quick("try_plan", lang), "url": f"{site}{PAGE}" + (f"?{urlencode(q)}" if q else "")}

