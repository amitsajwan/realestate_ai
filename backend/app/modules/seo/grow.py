"""The site grows its own list pages (docs/plan/area-intent-pages.md section 11): weekly, inside the seo loop.

discover -> parse -> gate -> create (capped) -> tell (the sitemap lists live pages, IndexNow sends them):
1. discover: Google's autocomplete for one buyer search per focus area (Serper, AUTOCOMPLETE_PER_WEEK calls) goes into
   `search_demand` with the phrases Search Console, related searches and "People also ask" already put there;
2. parse: every phrase becomes a facet by fixed rules (seo.phrases); phrases about BHK or budget attach to the existing pages,
   words we cannot answer go on the data gaps list, words we do not know on the unknown words list;
3. gate: a facet becomes a page only when people search for it (DEMAND_IMPRESSIONS in 28 days, or DEMAND_SOURCES places show
   it; the first three intents of every place are the seed and count as searched), at least facets.MIN_PROJECTS projects match,
   its projects overlap under MAX_OVERLAP with every live page of the same place, and it fits the week's budget;
4. create: `seo_pages` {_id: facet key, path, place, intent, kind, status, source, phrases, demand, regnos, count, gate,
   created_at, live_at, checked_at}. Status: candidate (waiting, `gate` says why) -> live; the owner can hold (noindex now)
   or say never (never made again). A candidate is checked again every round, so a page appears the week its data allows.
Budget: WEEKLY new live pages, WEEKLY_MORE once RAISE_AT of the pages made 14+ days ago are indexed (seo.coverage). The focus
areas' seeds go live without counting against it. SEO_GROW_ENABLED=0 stops new pages; live pages keep working.
Never writes text with a model, never removes a page (retiring with a 301 is the next step in the plan).
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import httpx

from app.modules.areastats import demand, websearch
from app.modules.areastats.hubs import _primaries, builders
from app.modules.areastats.pages import cluster_stamps, cluster_updated
from app.modules.newsroom.store import Store

from . import facets, phrases
from .facets import FOCUS, Facet

log = logging.getLogger(__name__)

PAGES = "seo_pages"
MARK = "seo_grow"
EVERY = timedelta(days=7)
DEMAND_IMPRESSIONS = 10
DEMAND_SOURCES = 2                   # distinct places that show a search: search_console, related, question, autocomplete
MAX_OVERLAP = 0.7
WEEKLY, WEEKLY_MORE = 10, 20
RAISE_AT = 0.7
RAISE_AFTER = timedelta(days=14)
KEEP_LISTS = 60
AUTOCOMPLETE_PER_WEEK = 8
AUTOCOMPLETE_SEEDS = ("new projects in {area}", "flats in {area}")
SOURCES = ("search_console", "related", "question", "autocomplete")
STATUSES = ("candidate", "live", "held", "never")


def enabled() -> bool:
    return (os.environ.get("SEO_GROW_ENABLED") or "1").strip().lower() not in ("0", "false", "off", "no")


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


# ---- 1. discover ---------------------------------------------------------------------------------------------------------------

async def autocomplete(q: str, key: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> List[str]:
    """Google's suggestions for a search as people start typing it, for India in English (Serper /autocomplete)."""
    async with httpx.AsyncClient(timeout=20, transport=transport) as c:
        r = await c.post("https://google.serper.dev/autocomplete", json={"q": q, "gl": "in", "hl": "en"}, headers={"X-API-KEY": key})
        r.raise_for_status()
        body = r.json()
    return [str(s.get("value") or "").strip() for s in body.get("suggestions") or [] if s.get("value")]


async def discover(store: Store, now: datetime, docs: List[dict], week: int,
                   transport: Optional[httpx.AsyncBaseTransport] = None) -> int:
    """This week's autocomplete searches (one seed per focus area, the seeds taking turns by week) into search_demand."""
    key = (os.environ.get("SERPER_API_KEY") or "").strip()
    if not key:
        return 0
    from app.core.areas import AREAS
    seed, n = AUTOCOMPLETE_SEEDS[week % len(AUTOCOMPLETE_SEEDS)], 0
    for a in AREAS[:AUTOCOMPLETE_PER_WEEK]:
        try:
            got = await autocomplete(seed.format(area=a.name.lower()), key, transport)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 402, 403, 429):
                log.warning("grow: autocomplete refused (%s), stopping for this week", e.response.status_code)
                break
            continue
        except Exception:
            log.exception("grow: autocomplete failed for %s", a.name)
            continue
        for s in got:
            await demand._upsert(store, s, now, docs, "autocomplete", {})
            n += 1
    return n


# ---- 2. parse ------------------------------------------------------------------------------------------------------------------

def _impressions(d: dict) -> int:
    return int((d.get("gsc") or {}).get("impressions") or 0)


def collect(rows: List[dict], names: Dict[str, str]) -> dict:
    """search_demand rows -> {facets: {key: {facet, phrases, impressions, sources}}, existing, unknown, gaps}."""
    out: dict = {"facets": {}, "existing": {}, "unknown": {}, "gaps": {}}
    for d in rows:
        if d.get("kind") == "project":
            continue
        phrase = d.get("phrase") or d["_id"]
        p = phrases.parse(phrase, names)
        imp, src = _impressions(d), set(d.get("sources") or []) & set(SOURCES)
        for w in p["unanswerable"]:
            g = out["gaps"].setdefault(w, {"word": w, "impressions": 0, "phrases": []})
            g["impressions"] += imp
            g["phrases"] = (g["phrases"] + [phrase])[:5]
        if p["existing"]:
            e = out["existing"].setdefault(p["existing"], {"path": p["existing"], "impressions": 0, "phrases": []})
            e["impressions"] += imp
            e["phrases"] = (e["phrases"] + [phrase])[:5]
            continue
        if p["place"] and p["unknown"]:
            for w in p["unknown"]:
                u = out["unknown"].setdefault(w, {"word": w, "impressions": 0, "phrases": []})
                u["impressions"] += imp
                u["phrases"] = (u["phrases"] + [phrase])[:5]
        f = p["facet"]
        if f is None:
            continue
        c = out["facets"].setdefault(f.key, {"facet": f, "phrases": [], "impressions": 0, "sources": set()})
        c["phrases"].append(phrase)
        c["impressions"] += imp
        c["sources"] |= src
    return out


# ---- 3. gate -------------------------------------------------------------------------------------------------------------------

def overlap(a: List[str], b: List[str]) -> float:
    """Share of a's projects that b lists too."""
    return len(set(a) & set(b)) / len(a) if a else 0.0


def gate(cand: dict, regnos: List[str], live: List[dict]) -> dict:
    """{ok, demand, supply, distinct, overlaps_with}: every rule except the budget."""
    seed = cand.get("source") == "seed"
    dem = seed or cand["impressions"] >= DEMAND_IMPRESSIONS or len(cand["sources"]) >= DEMAND_SOURCES
    sup = len(regnos) >= facets.MIN_PROJECTS
    worst, with_ = 0.0, None
    for p in live:
        if p["_id"] == cand["facet"].key or p.get("place") != cand["facet"].place:
            continue
        other = facets.from_key(p["_id"])
        if other is not None and other.bhk != cand["facet"].bhk:
            continue   # "2 bhk flats in X" is its own search, with prices the other lists do not show
        o = overlap(regnos, p.get("regnos") or [])
        if o > worst:
            worst, with_ = o, p["_id"]
    dis = worst < MAX_OVERLAP
    return {"ok": dem and sup and dis, "demand": dem, "supply": sup, "distinct": dis, "overlap": round(worst, 2),
            "overlaps_with": with_ if not dis else None, "projects": len(regnos)}


async def budget(store: Store, now: datetime) -> int:
    """WEEKLY, or WEEKLY_MORE once RAISE_AT of the pages made RAISE_AFTER ago or earlier are indexed."""
    old = [p for p in await store.db.get_collection(PAGES).find({"status": "live"}).to_list(None)
           if p.get("source") != "seed" and (t := _aware(p.get("live_at"))) and now - t >= RAISE_AFTER]
    if not old:
        return WEEKLY
    from .indexnow import site
    seen = {d["_id"]: d.get("verdict") for d in await store.db.get_collection("seo_index").find(
        {"_id": {"$in": [site() + p["path"] for p in old]}}).to_list(None)}
    if not seen:
        return WEEKLY
    passed = sum(1 for v in seen.values() if v == "PASS")
    return WEEKLY_MORE if passed / len(seen) >= RAISE_AT else WEEKLY


# ---- the round -------------------------------------------------------------------------------------------------------------------

async def run_once(store: Store, now: datetime, force: bool = False,
                   transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[dict]:
    mark = await store.get_mark(MARK)
    last = _aware(mark.get("at"))
    if not force and last is not None and now - last < EVERY:
        return None
    coll = store.db.get_collection(PAGES)
    docs = await store.all_projects()
    if not docs:
        return None   # no register yet: nothing to list, nothing due
    week = int(mark.get("week") or 0)
    found = await discover(store, now, docs, week, transport)
    names = phrases.builder_names(await builders(store.db, only_indexable=False))
    got = collect(await store.db.get_collection(demand.DEMAND).find({}).to_list(20000), names)

    # candidates: the seed intents of every place, then every facet a search asked for
    cands: Dict[str, dict] = {}
    for f in facets.seeds(docs):
        cands[f.key] = {"facet": f, "phrases": [], "impressions": 0, "sources": set(), "source": "seed"}
    for k, c in got["facets"].items():
        if c["facet"].is_place_page:
            continue
        if k in cands:
            cands[k].update(phrases=c["phrases"], impressions=c["impressions"], sources=c["sources"])
        else:
            cands[k] = {**c, "source": "search"}

    pages = {p["_id"]: p for p in await coll.find({}).to_list(None)}
    by_place: Dict[str, List[dict]] = {}
    for d in _primaries(docs):
        if d.get("pune_place"):
            by_place.setdefault(d["pune_place"], []).append(d)
    live = [p for p in pages.values() if p.get("status") == "live"]
    # live pages first: their project lists move with the register, and the overlap rule reads them
    for p in live:
        f = facets.from_key(p["_id"])
        if f is None:
            continue
        r = facets.regnos(f, by_place.get(f.place, []), now)
        c = cands.get(p["_id"]) or {}
        await coll.update_one({"_id": p["_id"]}, {"$set": {
            "regnos": r, "count": len(r), "checked_at": now,
            "phrases": sorted(set(p.get("phrases") or []) | set(c.get("phrases") or []))[:20],
            "demand": {"impressions": c.get("impressions", 0), "sources": sorted(c.get("sources") or [])}}})
        p["regnos"] = r

    allowed = await budget(store, now) if enabled() else 0
    made = made_focus = waiting = attached = 0
    # focus-area seeds, then the most searched, then the places with the most to list (never the alphabet: the first round
    # gave its 10 slots to Airport Road, Akurdi, Ambegaon, Aundh and Baramati)
    size = {k: len(facets.members(c["facet"], by_place.get(c["facet"].place, []), now)) for k, c in cands.items()}
    order = sorted(cands.values(), key=lambda c: (c["source"] != "seed" or c["facet"].place not in FOCUS,
                                                 -c["impressions"], -len(c["sources"]), -size[c["facet"].key],
                                                 c["source"] != "seed", c["facet"].key))
    for c in order:
        f: Facet = c["facet"]
        old = pages.get(f.key)
        if old and old.get("status") in ("live", "held", "never"):
            continue
        r = facets.regnos(f, by_place.get(f.place, []), now)
        g = gate(c, r, live)
        focus_seed = c["source"] == "seed" and f.place in FOCUS
        if c["source"] == "seed" and not r and old is None:
            continue   # a place's seed with nothing to list yet: not worth a record until it has a project
        status = "candidate"
        if g["ok"] and enabled() and (focus_seed or made < allowed):
            status = "live"
            if focus_seed:
                made_focus += 1
            else:
                made += 1
        elif not g["distinct"] and g["overlaps_with"] and c["phrases"]:
            # the same projects as a live page: its searches belong to that page
            await coll.update_one({"_id": g["overlaps_with"]}, {"$addToSet": {"phrases": {"$each": c["phrases"][:10]}}})
            attached += 1
        if status == "candidate":
            waiting += 1
        doc = {"path": f.path, "place": f.place, "intent": f.intent, "kind": f.kind, "status": status, "source": c["source"],
               "phrases": sorted(set(c["phrases"]))[:20], "regnos": r, "count": len(r), "gate": g, "checked_at": now,
               "demand": {"impressions": c["impressions"], "sources": sorted(c["sources"])}}
        if status == "live":
            doc["live_at"] = now
            live.append({"_id": f.key, **doc})
        if old is None:
            await coll.insert_one({"_id": f.key, "created_at": now, **doc})
        else:
            await coll.update_one({"_id": f.key}, {"$set": doc})

    top = lambda d: sorted(d.values(), key=lambda x: -x["impressions"])[:KEEP_LISTS]  # noqa: E731
    await store.set_mark(MARK, at=now, week=week + 1, made=made + made_focus, waiting=waiting, attached=attached,
                         autocomplete=found, budget=allowed, unknown=top(got["unknown"]), gaps=top(got["gaps"]),
                         existing=top(got["existing"]))
    return {"made": made + made_focus, "waiting": waiting, "attached": attached, "autocomplete": found, "budget": allowed}


# ---- reading it: the public list, the owner tab, hold and never -----------------------------------------------------------------

async def live_pages(db, now: Optional[datetime] = None) -> List[dict]:
    """Live facet pages for the sitemap and links: [{key, path, place, intent, label, count, indexable, page_updated}].
    Counted from the register now, so a page that fell under facets.MIN_PROJECTS is noindex and left out of the sitemap."""
    now = now or datetime.now(timezone.utc)
    rows = await db.get_collection(PAGES).find({"status": "live"}).to_list(None)
    if not rows:
        return []
    docs = await Store(db).shared_projects()   # read-only here: the one copy the public pages share
    stamps = cluster_stamps(docs)
    by_place: Dict[str, List[dict]] = {}
    for d in _primaries(docs):
        if d.get("pune_place"):
            by_place.setdefault(d["pune_place"], []).append(d)
    out = []
    for p in rows:
        f = facets.from_key(p["_id"])
        if f is None:
            continue
        listed = [d for d, _ in facets.members(f, by_place.get(f.place, []), now)]
        stamp = [u for u in (cluster_updated(d, docs, stamps) for d in listed[:facets.MAX_ROWS]) if u]
        live_at = _aware(p.get("live_at"))
        if live_at:
            stamp.append(live_at.isoformat())   # a new page is news to search engines even when its projects are not
        label = facets.LABEL[f.intent] if not f.possession else (
            f"Possession {f.possession}" if f.intent == "all" else f"{facets.LABEL[f.intent]}, possession {f.possession}")
        if f.bhk:
            label = f"{f.bhk} BHK flats" if f.intent == "all" and not f.possession else f"{label}, {f.bhk} BHK"
        out.append({"key": f.key, "path": f.path, "place": f.place, "place_slug": facets.place_slug(f.place), "intent": f.intent,
                    "possession": f.possession, "builder": f.builder, "bhk": f.bhk, "label": label, "count": len(listed),
                    "indexable": len(listed) >= facets.MIN_PROJECTS, "page_updated": max(stamp) if stamp else None})
    out.sort(key=lambda r: (r["place"], facets.INTENTS.index(r["intent"]), r["bhk"] or 0, r["possession"] or 0, r["builder"] or ""))
    return out


async def status(db, key: str) -> Optional[str]:
    p = await db.get_collection(PAGES).find_one({"_id": key})
    return p.get("status") if p else None


def _iso(d) -> Optional[str]:
    d = _aware(d)
    return d.isoformat() if d else None


async def owner_view(store: Store) -> dict:
    """Studio -> Insights -> Pages: the last round, live pages, pages waiting and why, unknown words and data gaps."""
    mark = await store.get_mark(MARK)
    rows = await store.db.get_collection(PAGES).find({}).to_list(None)
    def item(p: dict) -> dict:
        return {"key": p["_id"], "path": p.get("path"), "status": p.get("status"), "source": p.get("source"), "kind": p.get("kind"),
                "count": p.get("count"), "phrases": (p.get("phrases") or [])[:5], "demand": p.get("demand") or {},
                "gate": p.get("gate") or {}, "created_at": _iso(p.get("created_at")), "live_at": _iso(p.get("live_at"))}
    live = sorted((item(p) for p in rows if p.get("status") in ("live", "held")), key=lambda r: r["live_at"] or "", reverse=True)
    waiting = sorted((item(p) for p in rows if p.get("status") == "candidate" and (p.get("gate") or {}).get("demand")),
                     key=lambda r: (-(r["demand"].get("impressions") or 0), -(r["count"] or 0)))[:KEEP_LISTS]
    never = [item(p) for p in rows if p.get("status") == "never"]
    return {"at": _iso(mark.get("at")), "enabled": enabled(),
            "last": {k: mark.get(k) for k in ("made", "waiting", "attached", "autocomplete", "budget")},
            "counts": {s: sum(1 for p in rows if p.get("status") == s) for s in STATUSES},
            "live": live, "waiting": waiting, "never": never,
            "unknown": mark.get("unknown") or [], "gaps": mark.get("gaps") or [], "existing": mark.get("existing") or []}


async def set_status(store: Store, key: str, to: str) -> bool:
    """The owner's buttons: hold (noindex now, out of the sitemap), never (never made again), or back to live."""
    if to not in ("live", "held", "never"):
        return False
    coll = store.db.get_collection(PAGES)
    p = await coll.find_one({"_id": key})
    if p is None:
        return False
    fields = {"status": to, "status_by_owner_at": datetime.now(timezone.utc)}
    if to == "live" and not p.get("live_at"):
        fields["live_at"] = fields["status_by_owner_at"]
    await coll.update_one({"_id": key}, {"$set": fields})
    return True
