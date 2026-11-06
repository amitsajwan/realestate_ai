"""The owner's weekly SEO note and the pages to ask Google for (docs/plan/seo-system.md section 4 and 5.1).

Once a week (inside the seo loop, app/modules/seo/runner.py) every owner (INSIGHTS_OWNER_IDS, else the calendar's, else the
concierge's) gets one Studio notification (`seo_week`, shown on Home under "Needs you now", opening Insights → Rankings): the
week's numbers beside last week's, and how many pages wait for "Request indexing". Search Console allows that request only by
hand (no API for our page types), so `request_list` picks the pages worth the owner's ~10 clicks a day: sitemap pages Google has
not indexed, in `_rank` order: our areas' place pages, guides and area guides; our area list pages; hot projects in our areas;
builder pages and other areas' hubs; the other project pages (seen on Google first); tiny neighbourhood guides
(/localities/<area>/<community>) last. A hub is ours by the area segment in its place (the one after /projects/area/ or
/localities/), not by any segment, so /localities/lohegaon/viman-nagar is Lohegaon's. Pages since dropped from the sitemap are
still offered (knowing the sitemap needs a network read, which this list does not do), except project pages: one that is not in
search (`pages.searchable`) or is a tower shown on its group's page is left out, since it is noindex or redirects. On 2026-10-31
98 of the first 200 rows were such pages, thin hot projects among them, and a Request indexing on them is a click wasted.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urlparse

from app.core.areas import BY_KEY, BY_SLUG
from app.core.brand import NAME_DEVANAGARI
from app.modules.areastats import launches
from app.modules.areastats.demand import DEMAND
from app.modules.areastats.pages import searchable
from app.modules.insights.collector import owner_ids
from app.modules.newsroom.store import Store
from app.modules.notifications.service import notify
from app.modules.tracking.origin import leads_from_ai

from . import aivisits, coverage, review, scoreboard, targets

MARK = "seo_note"
KIND = "seo_week"
EVERY = timedelta(days=7)
PER_DAY = 10
WAITING = ("Discovered - currently not indexed", "URL is unknown to Google", "Crawled - currently not indexed")


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _rank(path: str, p: dict) -> tuple:
    """Sort key and label for one waiting page; `p` is its register record when it is a project page."""
    segs = [x for x in path.split("/") if x]
    if path.startswith("/projects/area/") and len(segs) >= 3:
        ours, deep = segs[2] in BY_SLUG, len(segs) - 3
        if not ours:
            return (4, len(segs), path), "other area list" if deep else "other area page"
        return ((1, 0, path), "area page") if not deep else ((2, deep, path), "area list")
    if path.startswith("/localities/") and len(segs) >= 2:
        if len(segs) > 2:
            return (6, segs[1] not in BY_SLUG, path), "neighbourhood guide"
        return ((1, 1, path), "area guide") if segs[1] in BY_SLUG else ((4, 2, path), "other area guide")
    if path.startswith("/guides/"):
        return (1, 2, path), "guide"
    if path.startswith("/builders/"):
        return (4, 0, path), "builder page"
    if len(segs) <= 1 and not p:
        return (1, 3, path), "links many pages"
    hot, seen = float(p.get("hot_score") or 0), int(p.get("gsc_impressions") or 0)
    if hot and p.get("locality") in BY_KEY:
        return (3, -hot, -seen, path), "hot project"
    return (5, -seen, p.get("locality") not in BY_KEY, path), "seen on Google" if seen else "project page"


async def request_list(store: Store, n: int = PER_DAY * 7) -> List[dict]:
    """Up to n not-indexed sitemap pages, most worth a Request-indexing first: [{url, state, why}]."""
    docs = await store.db.get_collection(coverage.COLLECTION).find({"state": {"$in": list(WAITING)}}).to_list(None)
    if not docs:
        return []
    by_slug = {d.get("page_slug"): d for d in await store.shared_projects() if d.get("page_slug")}

    def ranked(doc: dict):
        path = urlparse(doc["_id"]).path.rstrip("/") or "/"
        p = (by_slug.get(path.rsplit("/", 1)[-1]) if path.startswith("/projects/") else None) or {}
        return _rank(path, p)

    def offered(doc: dict) -> bool:
        path = urlparse(doc["_id"]).path.rstrip("/")
        if not path.startswith("/projects/") or path.startswith("/projects/area/"):
            return True
        p = by_slug.get(path.rsplit("/", 1)[-1])
        return p is None or (searchable(p) and not p.get("cluster_primary"))

    rows = sorted(((ranked(d), d) for d in docs if offered(d)), key=lambda r: r[0][0])
    return [{"url": d["_id"], "state": d.get("state"), "why": why} for (_, why), d in rows[:n]]


# "Avasetu" however buyers type it (ava setu, avsetu, awasetu, aavasetu, avasethu) or in Devanagari: searches for us by name,
# the sign that people look for the brand and not only for a project (docs/plan/seo-system.md 8b, H5)
BRAND = re.compile(r"\ba{1,2}[vw]a?\s?se(?:t|th)u\b|" + re.escape(NAME_DEVANAGARI), re.I)
BRAND_FRESH = timedelta(days=7)     # a phrase Search Console has not shown this recently is left out (its numbers are old)


async def branded(store: Store, now: datetime) -> dict:
    """{phrases, impressions, clicks, before}: Search Console's 28-day numbers for the searches that name us; `before` is the
    impressions of the 28 days before (None when no phrase has them yet). Reads search_demand (areastats.demand owns it)."""
    out = {"phrases": 0, "impressions": 0, "clicks": 0, "before": None}
    async for d in store.db.get_collection(DEMAND).find({}, {"gsc": 1, "gsc_prev": 1}):
        g = d.get("gsc") or {}
        read = _aware(g.get("read_at"))
        if not BRAND.search(str(d["_id"])) or read is None or now - read > BRAND_FRESH:
            continue
        out["phrases"] += 1
        out["impressions"] += int(g.get("impressions") or 0)
        out["clicks"] += int(g.get("clicks") or 0)
        if isinstance(d.get("gsc_prev"), int):
            out["before"] = (out["before"] or 0) + d["gsc_prev"]
    return out


def brand_line(b: dict) -> str:
    if not b.get("phrases"):
        return "Searches for Avasetu by name, 28 days: none yet."
    change = f" ({'+' if b['impressions'] - b['before'] >= 0 else ''}{b['impressions'] - b['before']:,} on the 28 days before)" \
        if b.get("before") is not None else ""
    return f"Searches for Avasetu by name, 28 days: {b['impressions']:,} impressions{change}, {b['clicks']:,} clicks."


def notes(week_text: str, ai_text: str, brand_text: str, portal_text: str, review_text: str = "", launch_text: str = "") -> List[str]:
    """The week as Studio notifications, each within the notification's length (notifications.service MAX_SUMMARY): the numbers;
    AI search and searches by name; the portal watch when it fired and the sites above us most often; the page check; new launches. One long text was cut off at the AI line before."""
    return [t for t in (week_text, f"{ai_text} {brand_text}".strip(), portal_text, review_text, launch_text) if t]


def portal_line(board: dict) -> str:
    names = scoreboard.format_alert(board.get("format"))
    return (f"Watch: {' and '.join(names)} results now show homes booked or moved dates, the facts only we showed: "
            "Insights → Rankings.") if names else ""


def summary(week: Optional[dict], ago: Optional[dict], cov: dict, board: dict, waiting: int) -> str:
    def num(k: str) -> str:
        v = (week or {}).get(k)
        if v is None:
            return "-"
        p = (ago or {}).get(k)
        return f"{v:,}" + (f" ({'+' if v - p >= 0 else ''}{v - p:,})" if isinstance(p, int) and isinstance(v, int) else "")
    idx = f"{cov.get('indexed', 0):,} of {cov.get('inspected', 0):,} checked" if cov.get("inspected") else "not checked yet"
    # head to head (both on the page) once the board counts it; a search MagicBricks has no page for says little
    if board.get("both"):
        mb = f"{board.get('above_mb_when_shown', 0)} of {board['both']} head to head"
    else:
        mb = f"{board.get('above_mb', 0)} of {board.get('searches', 0)}" if board.get("searches") else "-"
    return (f"SEO week: clicks {num('clicks')}, impressions {num('impressions')}, page one {num('page_one')}; indexed {idx}; "
            f"above MagicBricks {mb}. {waiting} pages to ask Google for, {PER_DAY} a day: Insights → Rankings.")


async def run_once(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    """This week's note to the owners. None when it was sent this week or there is no owner."""
    owners = owner_ids()
    last = _aware((await store.get_mark(MARK)).get("at"))
    if not owners or (not force and last is not None and now - last < EVERY):
        return None
    snaps = (await store.get_mark(targets.MARK)).get("history") or []
    week = snaps[-1] if snaps else None
    ago = next((h for h in reversed(snaps) if week and _aware(week.get("at")) and _aware(h.get("at"))
                and _aware(week["at"]) - _aware(h["at"]) >= timedelta(days=7)), None)
    # the daily check's own summary: pages in the sitemap now. `seo_index` also keeps ~12,000 pages since dropped from it
    cov = await store.get_mark(coverage.MARK)
    waiting = sum(n for state, n in (cov.get("missing_by_state") or {}).items() if state in WAITING)
    leads = await leads_from_ai(store.db.get_collection("contacts"), now - timedelta(days=7))   # read only: tracking owns contacts
    board = await store.get_mark(scoreboard.MARK)
    parts = notes(summary(week, ago, cov, board, waiting), aivisits.week_line(await aivisits.summary(store.db, now, days=7), leads),
                  brand_line(await branded(store, now)), " ".join(t for t in (portal_line(board), scoreboard.leader_line(board)) if t),
                  review.week_line(await review.summary(store, now)),
                  launches.week_line(launches.summary(await store.all_projects(), now)))
    text = " ".join(parts)
    for owner in owners:
        for part in parts:
            await notify(store.db, owner, KIND, part, {"href": "/studio/seo?tab=rankings"}, now=now)
    await store.set_mark(MARK, at=now, text=text)
    return {"owners": len(owners), "waiting": waiting}
