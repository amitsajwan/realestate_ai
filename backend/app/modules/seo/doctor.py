"""The page doctor (docs/plan/rank-loop.md R3): once a day, a few project pages get ONE fix each, logged with the page's Search
Console numbers before, and measured again 14 and 28 days later, so we learn which fixes move pages on our site.

Which pages, in order (at most PER_DAY, never one treated in the last REST_DAYS):
  1. just off page one (position 8-20 with 20+ impressions: searchconsole.near_page_one);
  1b. MagicBricks just above us for the page's own search (seo.scoreboard `next`, seo.rival);
  2. a rising search shows the page, but below position 20;
  3. a hot project (hot.HOT_MIN) that Google shows below position 20;
  4. seen (20+ impressions) but never clicked.

The menu (one fix per page per visit, so each result can be put down to one change):
  faq          "People also ask" questions about the project that our facts answer (seo.questions) -> `seo_faq`
  links        the page gets a link slot for LINK_DAYS: first in "Most active projects" on its area page (areastats.hubs)
  refresh      facts older than STALE_DAYS, no web facts yet, Google has not indexed it, or MagicBricks shows a price for its
               search and we have none -> urgent enrichment, which rereads
               MahaRERA and the web and rewrites the page (its sitemap date moves, so Google and IndexNow see it)
  description  seen on page one but not clicked -> a search description from the facts (possession, bookings, registration)
  rival        MagicBricks just above us for the page's own search -> a search description led by the kinds of fact their result
               shows (price, sizes, possession), from our record (seo/rival.py)
(The "title" fix is applied by seo.targets and logged in the same place: seo/actions.py holds the log, the fix window and
what an undone value means, so the two steps cannot work against each other.)

Order of the menu: a fix type with fewer than EXPLORE measured results is tried first (so every type keeps being measured),
then the types with the best median position gain. A title or description change that left its page more than WORSE_BY
positions lower after 28 days is undone automatically (`old` is kept on every action). `results()` is the owner's table.
"""
import logging
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.modules.areastats import enrich, hot, prices, searchconsole
from app.modules.areastats.hubs import active
from app.modules.areastats.pages import _long, _served, booked, can_host, indexable, names
from app.modules.areastats.service import _count, _day
from app.modules.newsroom.store import Store

from . import coverage, questions, rival
from .actions import ACTIONS, FIELD, REST_DAYS, blocked, gain, log_fix, numbers, stamp, undo

log = logging.getLogger(__name__)

MARK = "seo_doctor"
EVERY = timedelta(hours=24)
PER_DAY = 15
LINK_DAYS = 14
STALE_DAYS = 30
EXPLORE = 5                    # measured results a fix type needs before its median decides its place
WORSE_BY = 5.0                 # positions lost after 28 days that undo a title or description change
FIXES = ("faq", "links", "refresh", "description", "rival")
DEMAND = "search_demand"
RIVAL = "MagicBricks just above"   # pick reason: these pages try the rival fix, then refresh (for a price), first


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _pos(d: dict) -> float:
    p = d.get("gsc_position")
    return float(p) if p is not None else 999.0


def _path(d: dict) -> str:
    return f"/projects/{d['page_slug']}"


# ---- measure ----------------------------------------------------------------------------------------------------------------

async def measure(store: Store, now: datetime) -> dict:
    """Fill after14 / after28 on actions old enough, from the page's current Search Console numbers; undo what hurt."""
    coll = store.db.get_collection(ACTIONS)
    filled = undone = 0
    for a in await coll.find({}).to_list(20000):
        at = _aware(a.get("at"))
        if at is None or a.get("reverted") or (a.get("after14") is not None and a.get("after28") is not None):
            continue     # an undone fix is not measured: the numbers on the page are no longer its doing (seo-review D3)
        doc = await store.project(a.get("regno") or "")
        if doc is None:
            continue
        upd = {}
        if a.get("after14") is None and now - at >= timedelta(days=14):
            upd["after14"] = {**numbers(doc), "at": now}
        if a.get("after28") is None and now - at >= timedelta(days=28):
            upd["after28"] = {**numbers(doc), "at": now}
        if not upd:
            continue
        await coll.update_one({"_id": a["_id"]}, {"$set": upd})
        filled += 1
        after = upd.get("after28")
        before = (a.get("before") or {}).get("position")
        if after and a.get("fix") in FIELD and before is not None and after.get("position") is not None \
                and float(after["position"]) - float(before) > WORSE_BY and await undo(store, doc, a, now):
            undone += 1
    return {"measured": filled, "undone": undone}


async def results(store: Store) -> List[dict]:
    """Per fix type: tried, measured, median positions gained, share improved, clicks before/after (the owner's table)."""
    rows: Dict[str, dict] = {}
    for a in await store.db.get_collection(ACTIONS).find({}).to_list(20000):
        r = rows.setdefault(a.get("fix") or "?", {"fix": a.get("fix") or "?", "tried": 0, "gains": [], "reverted": 0,
                                                  "clicks_before": 0, "clicks_after": 0})
        r["tried"] += 1
        r["reverted"] += 1 if a.get("reverted") else 0
        g = gain(a)
        if g is not None:
            r["gains"].append(g)
            r["clicks_before"] += int((a.get("before") or {}).get("clicks") or 0)
            r["clicks_after"] += int((a.get("after28") or a.get("after14") or {}).get("clicks") or 0)
    out = []
    for r in rows.values():
        gs = r.pop("gains")
        out.append({**r, "measured": len(gs), "median_gain": statistics.median(gs) if gs else None,
                    "improved_pct": round(100 * sum(1 for g in gs if g > 0) / len(gs)) if gs else None})
    out.sort(key=lambda r: (r["median_gain"] is None, -(r["median_gain"] or 0)))
    return out


def order(table: List[dict]) -> List[str]:
    """The menu in the order to try: under-measured types first (explore), then by median gain."""
    by = {r["fix"]: r for r in table}
    def key(fix: str):
        r = by.get(fix) or {"measured": 0, "median_gain": None}
        return (r["measured"] >= EXPLORE, -(r["median_gain"] or 0))
    return sorted(FIXES, key=key)


# ---- pick ---------------------------------------------------------------------------------------------------------------

async def pick(store: Store, docs: List[dict], now: datetime, limit: int = PER_DAY, rivals: Optional[Dict[str, dict]] = None) -> List[tuple]:
    """[(doc, reason)] for today, in priority order."""
    hosted = {d["_id"] for d in docs if can_host(d)}
    pages = [d for d in docs if _served(d) and d.get("cluster_primary") not in hosted and indexable(d)
             and not ((t := _aware(d.get("page_fix_at"))) and now - t < timedelta(days=REST_DAYS))]
    by_path = {_path(d): d for d in pages}
    rising = set()
    for p in await store.db.get_collection(DEMAND).find({"rising": True}).to_list(5000):
        for path in (p.get("gsc") or {}).get("pages") or []:
            if path in by_path and _pos(by_path[path]) > 20:
                rising.add(path)
    seen_min = searchconsole.NEAR_MIN_IMPRESSIONS
    groups = [
        ("near page one", [d for d in pages if searchconsole.near_page_one(d.get("gsc_position"), d.get("gsc_impressions"))]),
        (RIVAL, [d for d in pages if (d.get("regno") or d["_id"]) in (rivals or {})]),
        ("rising search", [by_path[p] for p in rising]),
        ("hot, below 20", [d for d in pages if (d.get("hot_score") or 0) >= hot.HOT_MIN and int(d.get("gsc_impressions") or 0) > 0
                           and _pos(d) > 20]),
        ("seen, not clicked", [d for d in pages if int(d.get("gsc_impressions") or 0) >= seen_min and not d.get("gsc_clicks")]),
    ]
    out, taken = [], set()
    for reason, group in groups:
        group.sort(key=lambda d: -int(d.get("gsc_impressions") or 0))
        for d in group:
            if d["_id"] not in taken:
                taken.add(d["_id"])
                out.append((d, reason))
    return out[:limit]


# ---- diagnose and fix ---------------------------------------------------------------------------------------------------

def description(doc: dict) -> Optional[str]:
    """A search description from the record's facts only (what a searcher wants to know before clicking)."""
    shown = doc.get("search_name") or names(doc)[0]
    bits = []
    if _day(doc.get("completion_now")):
        bits.append(f"possession filed for {_long(_day(doc['completion_now']))}")
    total, sold = _count(doc.get("units_total")), booked(doc)
    if total and sold is not None and sold <= total:
        bits.append(f"{sold} of {total} homes booked")
    if doc.get("promoter"):
        bits.append(f"by {doc['promoter']}")
    if not bits:
        return None
    text = f"{shown}: " + ", ".join(bits) + f". MahaRERA {doc.get('regno') or doc['_id']}. Checked facts, map and buyer questions."
    return text[:160]


async def applicable(store: Store, doc: dict, docs: List[dict], now: datetime, slotted: set, index_state: Optional[str],
                     rivalry: Optional[dict] = None) -> Dict[str, dict]:
    """{fix: details} for every fix on the menu this page needs today."""
    out: Dict[str, dict] = {}
    if rivalry:
        text = rival.description(doc, rivalry["wants"], now)
        if text and text != doc.get("seo_description") and not blocked(doc, "rival", text):
            out["rival"] = {"new": text, "note": f'"{rivalry["query"]}": MagicBricks #{rivalry["magicbricks"]}, us '
                            + (f'#{rivalry["ours"]}' if rivalry.get("ours") else "not top 10")}
    faq = questions.answers(doc, docs, await questions.questions_for(store.db, doc))
    have = {f.get("topic") for f in doc.get("seo_faq") or []}
    if faq and {f["topic"] for f in faq} - have:
        out["faq"] = {"new": faq}
    if not _aware(doc.get("seo_link_slot_until")) or _aware(doc["seo_link_slot_until"]) <= now:
        if _path(doc) not in slotted:
            out["links"] = {}
    enriched = _aware(doc.get("enriched_at"))
    stale = enriched is None or now - enriched > timedelta(days=STALE_DAYS) or not (doc.get("web_facts") or {}).get("facts")
    no_price = bool(rivalry and "price" in rivalry["wants"] and not prices.public(doc.get("prices"), now))
    if no_price:   # MagicBricks shows a price for this search and our page has none: read the builder's and portals' pages again
        out["refresh"] = {"note": "MagicBricks shows a price, our page has none"}
    elif stale or (index_state and index_state != "PASS"):
        out["refresh"] = {"note": "not indexed: " + index_state if index_state and index_state != "PASS" else "facts older than "
                          f"{STALE_DAYS} days or no web facts"}
    if 0 < _pos(doc) <= 10 and int(doc.get("gsc_impressions") or 0) >= searchconsole.NEAR_MIN_IMPRESSIONS and not doc.get("gsc_clicks"):
        text = description(doc)
        if text and text != doc.get("seo_description") and not blocked(doc, "description", text):
            out["description"] = {"new": text}
    return out


async def treat(store: Store, doc: dict, fix: str, info: dict, now: datetime, reason: str) -> None:
    note = f"{reason}; {info.get('note', '')}".strip("; ")
    if fix == "faq":
        await log_fix(store, doc, "faq", now, old=doc.get("seo_faq"), new=info["new"], note=note)
        await store.set_project(doc["_id"], seo_faq=info["new"], seo_faq_at=now)
    elif fix == "links":
        until = now + timedelta(days=LINK_DAYS)
        await log_fix(store, doc, "links", now, new=until.isoformat(), note=note)
        await store.set_project(doc["_id"], seo_link_slot_until=until)
    elif fix == "refresh":
        await log_fix(store, doc, "refresh", now, note=note)
        await enrich.enrich_now(store.db, doc.get("regno") or doc["_id"], by="doctor")
    elif fix in ("description", "rival"):
        await log_fix(store, doc, fix, now, old=doc.get("seo_description"), new=info["new"], note=note)
        await store.set_project(doc["_id"], seo_description=info["new"])
    await stamp(store, doc["_id"], now, fix)


async def _index_states(store: Store) -> Dict[str, str]:
    """{path: "PASS" or Search Console's coverage state} from the daily coverage read."""
    out = {}
    for d in await store.db.get_collection(coverage.COLLECTION).find({}).to_list(None):
        path = "/" + d["_id"].split("://", 1)[-1].split("/", 1)[-1] if "://" in d["_id"] else d["_id"]
        out[path.rstrip("/")] = "PASS" if d.get("verdict") == "PASS" else (d.get("state") or "Unknown")
    return out


async def run_once(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    """Today's round: measure old fixes, then treat up to PER_DAY pages. None when done today. Needs Search Console data."""
    if searchconsole.key() is None and not force:
        return None
    last = _aware((await store.get_mark(MARK)).get("at"))
    if not force and last is not None and now - last < EVERY:
        return None
    measured = await measure(store, now)
    docs = await store.all_projects()
    menu = order(await results(store))
    states = await _index_states(store)
    rivals = await rival.targets(store)
    treated, by_fix, slotted_areas = [], {}, {}
    for doc, reason in await pick(store, docs, now, rivals=rivals):
        area = doc.get("locality")
        if area and area not in slotted_areas:   # pages already in the area's "Most active" list do not need a slot
            slotted_areas[area] = {f"/projects/{r['slug']}" for r in await active(store.db, area=area, now=now)}
        fixes = await applicable(store, doc, docs, now, slotted_areas.get(area, set()), states.get(_path(doc)),
                                 rivals.get(doc.get("regno") or doc["_id"]))
        here = menu if reason != RIVAL else ["rival", "refresh"] + [f for f in menu if f not in ("rival", "refresh")]
        fix = next((f for f in here if f in fixes), None)
        if fix is None:
            await stamp(store, doc["_id"], now)
            continue
        await treat(store, doc, fix, fixes[fix], now, reason)
        treated.append({"path": _path(doc), "fix": fix, "reason": reason})
        by_fix[fix] = by_fix.get(fix, 0) + 1
    await store.set_mark(MARK, at=now, treated=treated, menu=menu)
    return {"treated": len(treated), **{f"fix_{k}": v for k, v in by_fix.items()}, **measured}


async def revert(store: Store, path: str, now: Optional[datetime] = None) -> int:
    """Undo the title and description changes still standing on a page (the owner's button). Returns how many."""
    now = now or datetime.now(timezone.utc)
    n = 0
    for a in await store.db.get_collection(ACTIONS).find({"path": path, "reverted": False,
                                                           "fix": {"$in": list(FIELD)}}).to_list(100):
        doc = await store.project(a.get("regno") or "")
        if doc is not None and await undo(store, doc, a, now):
            n += 1
    return n

