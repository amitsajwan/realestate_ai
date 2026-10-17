"""One target search per project page, and our pages that compete for the same search (docs/plan/rank-loop.md R1, R2).

Daily, inside the seo loop, after Search Console's read (areastats.searchconsole fills `search_demand` with every search that
showed our pages and which pages it showed):

R1  For every project page (a primary; towers answer 301 to it) the target is the search with the most impressions that NAMES
    the project (any of `pages.names` aliases, or `hot.search_name`). It is kept as `seo_target` {phrase, impressions, position,
    source, at}. From it, `search_name` = the target without generic words ("price", "rera", "possession"...), written the way
    people read it ("Venkatesh Vanaya Kharadi"): the page's title and H1 lead with it (pages.view, frontend lib/site/register.ts).
    No search data: no target, and the page keeps its marketed name. `search_name` changes at most once per window, because
    Google needs weeks to settle and churning titles cost rank; each change is logged as a "title" fix in `seo_actions` (the
    page doctor's log) so its effect is measured like any other fix. The window, the log and what an undone title means are
    `seo/actions.py`'s, shared with the doctor: a title a revert put back is never written again.
R2  A search that showed two or more of our pages: pages of one project (same cluster) are already merged by the 301s; any
    other pair is reported on the `seo_conflicts` mark for the owner. Nothing is merged automatically here.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.core.areas import BY_KEY
from app.modules.areastats import hot, searchconsole
from app.modules.areastats.pages import _served, can_host, names
from app.modules.areastats.websearch import mentions
from app.modules.newsroom.store import Store

from .actions import REST_DAYS, blocked, log_fix, stamp

log = logging.getLogger(__name__)

DEMAND = "search_demand"
MARK = "seo_targets"
CONFLICTS = "seo_conflicts"
MAX_NAME = 48
MIN_IMPRESSIONS = 5            # fewer than this in 28 days is noise, not how people search for the page
CONFLICT_KEEP = 50
EVERY = timedelta(hours=24)
HISTORY = 120                  # daily snapshots of the site's numbers kept on the mark
# words that say what a searcher wants, not what the project is called: dropped from the name in the title
GENERIC = {"price", "prices", "rate", "rates", "cost", "rera", "maharera", "possession", "date", "status", "review", "reviews",
           "floor", "plan", "plans", "brochure", "location", "map", "address", "photos", "images", "launch", "new", "project",
           "projects", "flat", "flats", "apartment", "apartments", "for", "sale", "in", "at", "of", "the", "and", "bhk", "1", "2", "3",
           "4", "1bhk", "2bhk", "3bhk", "4bhk", "lakh", "lakhs", "crore", "cr", "details", "number", "builder", "developer", "by",
           "carpet", "area", "sq", "ft", "sqft", "amenities", "construction", "update", "updates", "ready", "move", "resale", "rent",
           "pune"}
KEEP_UPPER = {"bhk", "rera", "pmrda", "pmc", "pcmc", "mhada", "it"}


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def aliases(doc: dict) -> List[str]:
    return [a for a in dict.fromkeys(names(doc)[1] + [hot.search_name(doc.get("name", ""))]) if a]


def own_words(doc: dict) -> set:
    """Words the record itself calls the project by: its names, its area and its builder. A search that adds any other word
    names something else too ("la belle vue vj indilife wakad" is an Airbnb studio inside the tower), not the project."""
    area = BY_KEY.get(doc.get("locality") or "")
    texts = aliases(doc) + [area.name if area else "", *(area.aliases if area else ()), doc.get("pune_place_name") or "",
                            doc.get("promoter") or ""]
    return set(re.findall(r"[a-z0-9']+", " ".join(texts).lower()))


def readable(phrase: str, doc: dict) -> Optional[str]:
    """The target as a name for the title: generic words dropped, each word capitalised; None when the project's name is not in
    it any more (a target like "rera pune" never becomes a title), it carries a word the record does not call the project by,
    or it is too long."""
    words = [w for w in re.findall(r"[a-z0-9']+", (phrase or "").lower()) if w not in GENERIC]
    text = " ".join(w.upper() if w in KEEP_UPPER else w.capitalize() for w in words)
    if not text or len(text) > MAX_NAME or not any(mentions(a, text) for a in aliases(doc)):
        return None
    if set(words) - own_words(doc):
        return None
    return text


def pick(doc: dict, phrases: List[dict]) -> Optional[dict]:
    """The target for a project page from the searches that showed it: most impressions, naming the project."""
    best = None
    for p in phrases:
        if p["impressions"] < MIN_IMPRESSIONS or not any(mentions(a, p["phrase"]) for a in aliases(doc)):
            continue
        if best is None or (p["impressions"], -(p["position"] or 99)) > (best["impressions"], -(best["position"] or 99)):
            best = p
    return best


async def run_once(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    if searchconsole.key() is None and not force:   # the searches come from Search Console
        return None
    last = _aware((await store.get_mark(MARK)).get("at"))
    if not force and last is not None and now - last < EVERY:
        return None
    by_path: Dict[str, List[dict]] = {}
    conflicts = []
    for d in await store.db.get_collection(DEMAND).find({}).to_list(20000):
        g = d.get("gsc") or {}
        row = {"phrase": d.get("phrase") or d["_id"], "impressions": int(g.get("impressions") or 0), "position": g.get("position")}
        pages = list(g.get("pages") or [])
        for path in pages:
            by_path.setdefault(path, []).append(row)
        if len(pages) >= 2 and row["impressions"] >= MIN_IMPRESSIONS:
            conflicts.append({**row, "pages": pages})
    docs = await store.all_projects()
    hosted = {d["_id"] for d in docs if can_host(d)}
    slug_cluster = {d["page_slug"]: d.get("cluster_id") for d in docs if d.get("page_slug")}
    targeted = changed = 0
    for doc in docs:
        if not _served(doc) or doc.get("cluster_primary") in hosted:
            continue
        if doc.get("search_name") and readable(doc["search_name"], doc) is None:
            # a title written before the own-words rule that names something else: the page goes back to its marketed name
            await log_fix(store, doc, "title", now, old=doc["search_name"], new=None, phrase=doc["search_name"],
                          note="names something else: words the record does not call the project by")
            await store.set_project(doc["_id"], search_name=None, search_name_at=now)
            doc = {**doc, "search_name": None}
        best = pick(doc, by_path.get(f"/projects/{doc['page_slug']}", []))
        if best is None:
            continue
        targeted += 1
        await store.set_project(doc["_id"], seo_target={**best, "source": "search_console", "at": now})
        name = readable(best["phrase"], doc)
        if not name or name == doc.get("search_name") or blocked(doc, "title", name):
            continue        # the page already had this title, measured, and put back (seo-review D2)
        since = _aware(doc.get("search_name_at"))
        if since is not None and now - since < timedelta(days=REST_DAYS):
            continue
        await log_fix(store, doc, "title", now, old=doc.get("search_name"), new=name, phrase=best["phrase"])
        await store.set_project(doc["_id"], search_name=name, search_name_at=now)
        await stamp(store, doc["_id"], now, "title")   # the page's one fix for this window, whoever applies the next one
        changed += 1
    # R2: two of our pages for one search; one project's towers are merged already (same cluster)
    report = []
    for c in sorted(conflicts, key=lambda c: -c["impressions"]):
        slugs = [p.split("/projects/", 1)[1] for p in c["pages"] if p.startswith("/projects/")]
        clusters = {slug_cluster.get(s) for s in slugs}
        same = len(slugs) == len(c["pages"]) and len(clusters) == 1 and None not in clusters
        if not same:
            report.append(c)
    await store.set_mark(CONFLICTS, at=now, items=report[:CONFLICT_KEEP], total=len(report))
    # the site's numbers today, kept daily so the owner's Rankings tab and the weekly report show the trend (R9)
    pages = [d for d in docs if _served(d) and d.get("gsc_read_at")]
    snap = {"at": now, "clicks": sum(int(d.get("gsc_clicks") or 0) for d in pages),
            "impressions": sum(int(d.get("gsc_impressions") or 0) for d in pages),
            "page_one": sum(1 for d in pages if d.get("gsc_position") is not None and float(d["gsc_position"]) <= 10),
            "near_page_one": sum(1 for d in pages if searchconsole.near_page_one(d.get("gsc_position"), d.get("gsc_impressions"))),
            "targeted": targeted}
    history = ((await store.get_mark(MARK)).get("history") or [])[-(HISTORY - 1):] + [snap]
    await store.set_mark(MARK, at=now, targeted=targeted, changed=changed, history=history)
    return {"targeted": targeted, "titles_changed": changed, "conflicts": len(report)}
