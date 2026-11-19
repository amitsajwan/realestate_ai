"""Page-by-page audit: every page Google knows of ours, what it earns and what to do with it. Read-only.

The 12-month publishing blueprint (docs/plan/publishing-blueprint.md) asks for this before anything new is written: which pages
already get clicks, which are seen but rank poorly, which are indexed and never shown, which are not indexed, and the search each
page is found for. The loops already hold every piece (Search Console per page, URL Inspection per page in `seo_index`); this puts
them side by side, one row per page, with one bucket and one action each, so the owner's next hours go to pages that already earn.

Actions never say "delete": a real page is not dropped to make numbers look better (seo-system.md section 9). A page that repeats
another is merged with a 301 to the one that earns; a thin one is improved or kept out of search until it holds a fact.
"""
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from app.modules.areastats import searchconsole
from app.modules.newsroom.store import Store

from . import actions, coverage

log = logging.getLogger(__name__)

SEEN = 20                 # impressions in 28 days before a page's rank or CTR is worth reading (searchconsole.NEAR_MIN_IMPRESSIONS)
CTR_SEEN = 100            # impressions before a low click rate on page one is more than chance
CTR_LOW = 0.01            # under 1% of impressions clicked while averaging page one: the title or description is not chosen
TREND = 0.3               # a 30% move in impressions against the 28 days before is rising or falling

# Bucket order is the order the owner works in: protect what earns, then what is closest to earning.
BUCKETS = ("low_ctr", "earning", "near_page_one", "seen_far", "too_few", "outside_sitemap", "indexed_silent",
           "not_indexed", "unchecked")

KINDS = (  # first match wins; the six content pillars of the blueprint map onto these
    ("/projects/area/", "area"), ("/projects/", "project"), ("/localities/", "locality"), ("/builders/", "builder"),
    ("/guides/", "guide"), ("/news/track/", "tracker"), ("/news/", "news"), ("/insights/", "insights"),
    ("/pune-maharera-tracker", "research"), ("/posts/", "post"), ("/agent/", "agent"), ("/2-bhk/", "listing"),
    ("/1-bhk/", "listing"), ("/3-bhk/", "listing"), ("/4-bhk/", "listing"), ("/price/", "listing"),
)

HUBS = {"/projects", "/localities", "/builders", "/news", "/insights", "/guides"}


def kind_of(path: str) -> str:
    """Which section of the site a path belongs to."""
    if path in ("", "/"):
        return "home"
    if path in HUBS:
        return "hub"
    for prefix, kind in KINDS:
        if path == prefix or path.startswith(prefix):
            return kind
    return "other"


def path_of(url: str) -> str:
    return urlparse(url).path.rstrip("/") or "/"


def trend(now_imp: int, before_imp: Optional[int]) -> str:
    if not before_imp:
        return "new" if now_imp else ""
    change = (now_imp - before_imp) / before_imp
    return "rising" if change >= TREND else "falling" if change <= -TREND else "steady"


def bucket(c: dict, index: Optional[dict], now: datetime) -> Tuple[str, str]:
    """(bucket, action) for one page from its 28-day counts and its last URL Inspection (None when never inspected)."""
    imp, clicks, pos = int(c.get("impressions") or 0), int(c.get("clicks") or 0), c.get("position")
    listed = bool(index.get(coverage.LISTED, True)) if index else None
    if imp >= CTR_SEEN and pos is not None and pos <= 10 and clicks / imp < CTR_LOW:
        when = f" once the title hold ends ({actions.HOLD_UNTIL:%d %b %Y})" if actions.on_hold(now) else ""
        return "low_ctr", f"On page one but rarely chosen: a title and description that answer the top search{when}"
    if clicks:
        return "earning", "Earns clicks: keep it steady, change it only through the doctor's measured fix"
    if searchconsole.near_page_one(pos, imp):
        return "near_page_one", "Just off page one: the doctor's queue; add the fact the top search asks for"
    if imp >= SEEN:
        return "seen_far", "Shown for searches it does not answer well: compare the page with its top search"
    if imp:
        return "too_few", "Shown a little: too few impressions to call, leave it"
    if listed is False:
        return "outside_sitemap", "Out of the sitemap: check it is noindex or 301s to the page that replaced it"
    if index is None:
        return "unchecked", "Not inspected yet: the daily index check reaches it"
    if index.get("verdict") == "PASS":
        return "indexed_silent", ("Indexed, never shown: merge (301) into the page that earns for the same search, "
                                  "or give it a fact nobody else has")
    state = index.get("state") or "Unknown"
    if state.startswith("Crawled"):
        return "not_indexed", f"{state}: Google read it and passed; add facts of its own or keep it out of search"
    if state.startswith("Discovered"):
        return "not_indexed", f"{state}: not read yet; Request indexing and link it from a page that earns"
    return "not_indexed", f"{state}: read the URL Inspection report for this page"


def top_queries(rows: Iterable[dict]) -> Dict[str, Tuple[str, int]]:
    """{path: (search, impressions)}: the search that shows each page most (the blueprint's keyword-to-URL map)."""
    best: Dict[str, Tuple[str, int]] = {}
    for r in rows:
        p, q, n = path_of(r.get("page") or ""), r.get("query") or "", int(r.get("impressions") or 0)
        if q and n > best.get(p, ("", -1))[1]:
            best[p] = (q, n)
    return best


def audit(now_counts: Dict[str, dict], before_counts: Dict[str, dict], queries: Iterable[dict], index_docs: Iterable[dict],
          now: datetime) -> List[dict]:
    """One row per page Google showed or the index check knows, the buckets in BUCKETS order, most seen first inside each."""
    index = {path_of(d["_id"]): d for d in index_docs}
    counts = {(p or "/"): c for p, c in now_counts.items()}
    before = {(p or "/"): c for p, c in before_counts.items()}
    best = top_queries(queries)
    out = []
    for path in sorted(set(counts) | set(index)):
        c, doc = counts.get(path) or {}, index.get(path)
        if not c and doc is not None and doc.get(coverage.LISTED) is False and doc.get("verdict") != "PASS":
            continue   # taken out, never indexed and not shown: nothing for anyone to do
        name, action = bucket(c, doc, now)
        imp, clicks = int(c.get("impressions") or 0), int(c.get("clicks") or 0)
        q, qn = best.get(path, ("", 0))
        out.append({"path": path, "kind": kind_of(path), "bucket": name, "action": action, "clicks": clicks, "impressions": imp,
                    "ctr": round(clicks / imp, 3) if imp else None, "position": c.get("position"),
                    "impressions_before": int((before.get(path) or {}).get("impressions") or 0),
                    "trend": trend(imp, int((before.get(path) or {}).get("impressions") or 0)),
                    "index_state": (doc or {}).get("state") or "", "in_sitemap": (doc or {}).get(coverage.LISTED),
                    "top_search": q, "top_search_impressions": qn})
    order = {b: i for i, b in enumerate(BUCKETS)}
    out.sort(key=lambda r: (order[r["bucket"]], -r["impressions"], -r["clicks"], r["path"]))
    return out


def summary(rows: List[dict], top: int = 20) -> dict:
    """Counts per bucket and per kind, and the most seen pages (the blueprint's week-one "top 20 pages by impressions")."""
    by_kind: Dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_kind[r["kind"]][r["bucket"]] += 1
        by_kind[r["kind"]]["clicks"] += r["clicks"]
        by_kind[r["kind"]]["impressions"] += r["impressions"]
    return {"pages": len(rows), "by_bucket": {b: sum(1 for r in rows if r["bucket"] == b) for b in BUCKETS},
            "by_kind": {k: dict(v) for k, v in sorted(by_kind.items(), key=lambda kv: -kv[1]["impressions"])},
            "top": sorted(rows, key=lambda r: (-r["impressions"], r["path"]))[:top]}


async def read(store: Store, now: datetime, transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[List[dict]]:
    """Search Console's last 28 days and the 28 before, its searches per page, and the stored index checks, audited.
    None without the Search Console key."""
    sa = searchconsole.key()
    if sa is None:
        return None
    today = now.date()
    days = searchconsole.DAYS
    now_counts = await searchconsole.page_counts(sa, today, transport)
    before_counts = await searchconsole.page_counts(sa, today, transport, first=2 * days + 2, last=days + 3)
    queries = await searchconsole.query_rows(sa, today, transport)
    docs = await store.db.get_collection(coverage.COLLECTION).find({}).to_list(None)
    return audit(now_counts, before_counts, queries, docs, now)


MARK = "page_audit"              # newsroom_status document: the last audit, so opening Studio does not call Google every time
KEEP = timedelta(hours=24)       # Search Console's numbers move once a day
LABELS = {
    "low_ctr": "Page one, rarely clicked", "earning": "Earning clicks", "near_page_one": "Just off page one",
    "seen_far": "Seen, ranked far", "too_few": "Shown a little", "outside_sitemap": "Out of the sitemap",
    "indexed_silent": "Indexed, never shown", "not_indexed": "Not indexed", "unchecked": "Not checked yet",
}


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


async def view(store: Store, now: datetime, fresh: bool = False,
               transport: Optional[httpx.AsyncBaseTransport] = None) -> dict:
    """Studio → SEO → Audit: the last audit while it is under KEEP old, else a new one (fresh=True always reads again).
    When Google cannot be read, the last stored audit is shown with the error, never an empty screen."""
    mark = await store.get_mark(MARK)
    at, rows, error = _aware(mark.get("at")), mark.get("rows"), None
    if fresh or rows is None or at is None or now - at >= KEEP:
        try:
            got = await read(store, now, transport)
        except Exception as e:   # Search Console down or the key refused: keep what we have
            log.exception("pageaudit: reading Search Console failed")
            got, error = None, f"Could not read Search Console: {type(e).__name__}"
        if got is not None:
            rows, at = got, now
            await store.set_mark(MARK, at=now, rows=rows)
        elif error is None and rows is None:
            return {"configured": False, "at": None, "error": None, "buckets": [], "rows": [], "pages": 0, "by_kind": {}}
    rows = rows or []
    s = summary(rows)
    return {"configured": True, "at": at.isoformat() if at else None, "error": error, "pages": s["pages"],
            "buckets": [{"key": b, "label": LABELS[b], "pages": s["by_bucket"][b]} for b in BUCKETS],
            "by_kind": s["by_kind"], "rows": rows}
