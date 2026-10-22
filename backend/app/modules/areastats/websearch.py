"""Google search results as a hot-projects signal: which projects Google shows buyers in each area, who markets them, and project
numbers we do not have yet.

Google's own web-search API (Custom Search JSON) is closed to new customers and ends on 2027-01-01, so results come from a paid
results provider through `Search` (today Serper.dev, SERPER_API_KEY; another provider is one function). Without a key nothing runs.

Each day (inside the hot-projects refresh):
1. area searches: what buyers type ("new launch projects in Kharadi Pune"), AREA_PER_DAY of them in turn, so every area and phrase
   comes round every few days;
2. project searches: "<name people use> <area> Pune" for the PROJECT_PER_DAY hottest projects not searched in KEEP_DAYS: the sites
   that rank for it are the ones marketing it (portals, channel partners, the builder);
3. every answer is stored (`web_search_results`, one document per query), and the signal is worked out from the last KEEP_DAYS:
   a project in an area search's top 10 counts (a higher place more), and so does each distinct site marketing it;
4. a MahaRERA number in a result that the register does not have goes to `discovered_projects` with where it was seen, so the
   lookup job can add it (a project like Lodha Camelot reaches us the day marketers start ranking for it).
Marketer sites go on the project record as `web_marketers`: for agents, never on the public page (pages.view lists its fields).
5. target checks (docs/plan/rank-loop.md R8): the target search of a page the page doctor changed 14 or 28 days ago, so the
   owner sees who ranks above us for it (Search Console gives our position, not theirs);
6. the panel (docs/plan/seo-system.md 5.5): PANEL_PER_DAY more target searches, every page's at least once in PANEL_DAYS, most
   seen first, so the MagicBricks scoreboard (seo.scoreboard) counts a fixed set of searches, not whatever was searched.
About 25 searches a day (750 a month). Read-only: it never clicks an ad or visits a result.
"""
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.core.areas import AREAS, BY_KEY
from app.modules.newsroom.register import regnos_in
from app.modules.newsroom.store import Store

from . import hot

log = logging.getLogger(__name__)

RESULTS = "web_search_results"       # {_id: query, kind: "area" | "project", area, regno, at, results: [...]}
DISCOVERED = "discovered_projects"   # {_id: regno, first_seen, last_seen, seen: [{query, title, link}]}
MARK = "web_search"                  # newsroom_status document: where the area searches are in their turn
# one search per way buyers ask for an area (docs/plan/seo-system.md, "Every way buyers search"): the same AREA_PER_DAY budget,
# a longer turn (7 searches x 8 areas, every area's family once in ~9 days)
AREA_QUERIES = ("new launch projects in {area} Pune", "upcoming residential projects in {area} Pune",
                "top residential projects in {area} Pune", "ready to move flats in {area} Pune",
                "flats in {area} Pune", "2 bhk flats in {area} Pune", "property rates in {area} Pune")
AREA_PER_DAY = 6
PROJECT_PER_DAY = 8
TARGET_PER_DAY = 6                   # rank checks: the target search of a page the page doctor changed 14 or 28 days ago
PANEL_PER_DAY = 5                    # the scoreboard's panel: every page's target search once in PANEL_DAYS
PANEL_DAYS = 14
ACTIONS = "seo_actions"              # the page doctor's log (app/modules/seo/doctor.py)
KEEP_DAYS = 7
TOP = 10
KEEP_RESULTS = 40                    # results kept per search: organic, ads, related searches and questions
SEEN_KEEP = 10                       # places a discovered number was seen, kept per number
# sites that are not marketing a project: us, the regulator, encyclopaedias and video/social hosts (counted by their own signals)
NOT_MARKETERS = ("avasetu.in", "maharashtra.gov.in", "wikipedia.org", "youtube.com", "facebook.com", "instagram.com", "x.com",
                 "twitter.com", "linkedin.com", "reddit.com", "quora.com",
                 # travel, health and directory sites: a hotel or a clinic sharing a project's name is not the project (2026-10-22)
                 "ixigo.com", "goibibo.com", "tripadvisor.in", "tripadvisor.com", "makemytrip.com", "booking.com", "agoda.com",
                 "practo.com", "justdial.com", "manipalhospitals.com", "zomato.com", "swiggy.com", "google.com", "indiamart.com",
                 "sulekha.com")

# query -> [{"title", "link", "snippet", "position", "ad": bool, "type"}]: type "organic" or "ad" (results), "related" (Google's
# related searches: the title is the search) or "question" ("People also ask": the title is the question)
Search = Callable[[str], Awaitable[List[dict]]]
PHRASE_TYPES = ("related", "question")


def serper(key: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> Search:
    """Google results for India in English through Serper.dev (POST google.serper.dev/search, X-API-KEY header)."""
    async def search(q: str) -> List[dict]:
        async with httpx.AsyncClient(timeout=20, transport=transport) as c:
            r = await c.post("https://google.serper.dev/search", json={"q": q, "gl": "in", "hl": "en", "num": TOP},
                             headers={"X-API-KEY": key})
            r.raise_for_status()
            body = r.json()
        out = [{"title": str(i.get("title") or ""), "link": str(i.get("link") or ""), "snippet": str(i.get("snippet") or ""),
                "position": int(i.get("position") or n + 1), "ad": False, "type": "organic"}
               for n, i in enumerate(body.get("organic") or [])]
        out += [{"title": str(i.get("title") or ""), "link": str(i.get("link") or ""), "snippet": str(i.get("snippet") or ""),
                 "position": 0, "ad": True, "type": "ad"} for i in body.get("ads") or []]
        # what else people search: free with the same search (areastats.demand keeps them)
        out += [{"title": str(i.get("query") or ""), "link": "", "snippet": "", "position": 0, "ad": False, "type": "related"}
                for i in body.get("relatedSearches") or [] if i.get("query")]
        out += [{"title": str(i.get("question") or ""), "link": str(i.get("link") or ""), "snippet": str(i.get("snippet") or ""),
                 "position": 0, "ad": False, "type": "question"} for i in body.get("peopleAlsoAsk") or [] if i.get("question")]
        return out
    return search


def provider() -> Optional[Search]:
    key = (os.environ.get("SERPER_API_KEY") or "").strip()
    return serper(key) if key else None


def site(link: str) -> str:
    host = (urlparse(link).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def marketer(link: str) -> bool:
    s = site(link)
    return bool(s) and not any(s == n or s.endswith("." + n) for n in NOT_MARKETERS)


def mentions(name: str, text: str) -> bool:
    """The name people use for the project, as whole words, in a result's title or snippet."""
    words = re.findall(r"[a-z0-9]+", (name or "").lower())
    return bool(words) and re.search(r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(map(re.escape, words)) + r"(?![a-z0-9])",
                                     (text or "").lower()) is not None


def area_queries() -> List[dict]:
    return [{"q": t.format(area=a.name), "area": a.key} for t in AREA_QUERIES for a in AREAS]


def project_query(d: dict) -> Optional[str]:
    name, area = hot.search_name(d.get("name", "")), BY_KEY.get(d.get("locality") or "")
    return f"{name} {area.name if area else ''} Pune".replace("  ", " ") if name else None


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


async def target_checks(store: Store, now: datetime, taken: set) -> List[dict]:
    """Up to TARGET_PER_DAY searches: target phrases of pages changed by the page doctor 14 or 28 days ago, not searched lately."""
    coll, out = store.db.get_collection(RESULTS), []
    actions = [a for a in await store.db.get_collection(ACTIONS).find({}).to_list(20000) if a.get("phrase")]
    actions.sort(key=lambda a: _aware(a["at"]) if isinstance(a.get("at"), datetime) else now)
    for a in actions:
        if len(out) >= TARGET_PER_DAY:
            break
        q = a.get("phrase")
        age = (now - _aware(a["at"])).days if isinstance(a.get("at"), datetime) else -1
        if not q or q in taken or age not in (14, 15, 28, 29):
            continue
        old = await coll.find_one({"_id": q})
        if old and isinstance(old.get("at"), datetime) and now - _aware(old["at"]) < timedelta(days=10):
            continue
        taken.add(q)
        out.append({"q": q, "kind": "target", "area": None, "regno": a.get("regno")})
    return out + await panel_checks(store, now, taken)


async def panel_checks(store: Store, now: datetime, taken: set) -> List[dict]:
    """Up to PANEL_PER_DAY target searches (seo.targets `seo_target`) not searched in PANEL_DAYS, the most seen pages first."""
    coll, out = store.db.get_collection(RESULTS), []
    docs = await store.db.get_collection("projects").find({"seo_target": {"$exists": True}}).to_list(None)
    docs.sort(key=lambda d: -int((d.get("seo_target") or {}).get("impressions") or 0))
    for d in docs:
        if len(out) >= PANEL_PER_DAY:
            break
        q = (d.get("seo_target") or {}).get("phrase")
        if not q or q in taken:
            continue
        old = await coll.find_one({"_id": q})
        if old and isinstance(old.get("at"), datetime) and now - _aware(old["at"]) < timedelta(days=PANEL_DAYS):
            continue
        taken.add(q)
        out.append({"q": q, "kind": "target", "area": d.get("locality"), "regno": d.get("regno") or d["_id"]})
    return out


async def run_searches(store: Store, projects: List[dict], now: datetime, search: Search) -> dict:
    """Today's searches: the next AREA_PER_DAY area searches in turn, then the hottest projects not searched lately."""
    coll = store.db.get_collection(RESULTS)
    todo = area_queries()
    start = int((await store.get_mark(MARK)).get("next") or 0) % len(todo)
    batch = [{**todo[(start + i) % len(todo)], "kind": "area"} for i in range(min(AREA_PER_DAY, len(todo)))]
    fresh = now - timedelta(days=KEEP_DAYS)
    for d in projects:
        if sum(1 for b in batch if b["kind"] == "project") >= PROJECT_PER_DAY:
            break
        q = project_query(d)
        if q is None:
            continue
        old = await coll.find_one({"_id": q})
        if old and isinstance(old.get("at"), datetime) and _aware(old["at"]) > fresh:
            continue
        batch.append({"q": q, "kind": "project", "area": d.get("locality"), "regno": d.get("regno") or d["_id"]})
    batch += await target_checks(store, now, {b["q"] for b in batch})
    done, failed, handled = 0, 0, 0
    for b in batch:
        try:
            results = await search(b["q"])
        except httpx.HTTPStatusError as e:
            failed += 1
            if e.response.status_code in (401, 402, 403, 429):   # key refused or credit spent: the rest would fail the same way
                log.warning("websearch: provider refused (%s), stopping for today", e.response.status_code)
                break                                             # not handled: this search is asked again tomorrow
            handled += 1
            continue
        except Exception:
            failed += 1
            handled += 1
            log.exception("websearch: search failed: %s", b["q"])
            continue
        doc = {"kind": b["kind"], "area": b.get("area"), "regno": b.get("regno"), "at": now, "results": results[:KEEP_RESULTS]}
        if await coll.find_one({"_id": b["q"]}):
            await coll.update_one({"_id": b["q"]}, {"$set": doc})
        else:
            await coll.insert_one({"_id": b["q"], **doc})
        done += 1
        handled += 1
    areas_done = sum(1 for b in batch[:handled] if b["kind"] == "area")
    await store.set_mark(MARK, next=(start + areas_done) % len(todo), at=now)
    return {"searched": done, "failed": failed}


async def discover(store: Store, docs: List[dict], now: datetime) -> int:
    """MahaRERA numbers in recent results that the register does not have: kept with where they were seen. Returns how many new."""
    known = {d.get("regno") or d["_id"] for d in await store.all_projects()}
    coll, new = store.db.get_collection(DISCOVERED), 0
    for doc in docs:
        for r in doc.get("results") or []:
            for regno in regnos_in(f"{r.get('title', '')} {r.get('snippet', '')}"):
                if regno in known:
                    continue
                seen = {"query": doc["_id"], "title": r.get("title", "")[:160], "link": r.get("link", ""), "at": now}
                old = await coll.find_one({"_id": regno})
                if old is None:
                    await coll.insert_one({"_id": regno, "first_seen": now, "last_seen": now, "seen": [seen]})
                    new += 1
                elif not any(s.get("link") == seen["link"] for s in old.get("seen") or []):
                    await coll.update_one({"_id": regno}, {"$set": {"last_seen": now,
                                                                    "seen": ((old.get("seen") or []) + [seen])[-SEEN_KEEP:]}})
    return new


def score(projects: List[dict], docs: List[dict]) -> Dict[str, dict]:
    """{regno: signal} from stored results: places in area searches' top 10, and the distinct sites marketing the project."""
    out: Dict[str, dict] = {}
    for d in projects:
        regno, name = d.get("regno") or d["_id"], hot.search_name(d.get("name", ""))
        if not name:
            continue
        places, sites, ads = [], set(), set()
        for doc in docs:
            for r in doc.get("results") or []:
                if r.get("type") in PHRASE_TYPES:          # searches and questions, not pages: areastats.demand reads them
                    continue
                text = f"{r.get('title', '')} {r.get('snippet', '')}"
                if doc.get("kind") == "area" and doc.get("area") == d.get("locality") and not r.get("ad") \
                        and 0 < int(r.get("position") or 0) <= TOP and mentions(name, text):
                    places.append((int(r["position"]), doc["_id"]))
                if mentions(name, text) and marketer(r.get("link", "")):
                    sites.add(site(r["link"]))
                    if r.get("ad"):
                        ads.add(site(r["link"]))
        if not places and not sites:
            continue
        value = sum(1 + (TOP - p) / TOP for p, _ in places) + len(sites) / 2 + len(ads)
        bits = []
        if places:
            best = min(places)
            bits.append(f"in Google's top {TOP} for {len(places)} buyer searches in its area (best: #{best[0]} for '{best[1]}')")
        if sites:
            bits.append(f"{len(sites)} sites market it" + (f", {len(ads)} with Google ads" if ads else "") +
                        ": " + ", ".join(sorted(sites)[:6]))
        out[regno] = {"value": round(value, 2), "evidence": "; ".join(bits), "source": "Google search results",
                      "marketers": sorted(sites), "advertisers": sorted(ads)}
    return out


def signal(search: Optional[Search] = None) -> hot.Signal:
    """The hot-projects signal ("google"): runs today's searches, keeps discoveries and marketers, scores from the last KEEP_DAYS."""
    async def fn(store: Store, projects: List[dict], now: datetime) -> Dict[str, dict]:
        s = search or provider()
        if s is None:
            return {}
        ran = await run_searches(store, projects, now, s)
        since = now - timedelta(days=KEEP_DAYS)
        docs = [d for d in await store.db.get_collection(RESULTS).find({}).to_list(2000)
                if isinstance(d.get("at"), datetime) and _aware(d["at"]) >= since]
        found = await discover(store, docs, now)
        out = score(projects, docs)
        for regno, sig in out.items():
            await store.set_project(regno, web_marketers=sig.pop("marketers"), web_advertisers=sig.pop("advertisers"), web_read_at=now)
        try:   # our own rank for each search, and the related searches and questions Google showed (areastats.demand)
            from . import demand
            await demand.from_results(store, docs, now)
        except Exception:
            log.exception("websearch: keeping the search phrases failed")
        log.info("websearch: %s, %d new project numbers, %d projects seen", ran, found, len(out))
        return out
    return fn


async def discovered(store: Store, limit: int = 50) -> List[dict]:
    """Project numbers seen in Google results that the register lacks, most recently seen first: for the lookup job and admins."""
    docs = await store.db.get_collection(DISCOVERED).find({}).to_list(2000)
    docs.sort(key=lambda d: _aware(d["last_seen"]) if isinstance(d.get("last_seen"), datetime) else datetime.min.replace(tzinfo=timezone.utc),
              reverse=True)
    return [{"regno": d["_id"], "first_seen": d.get("first_seen"), "last_seen": d.get("last_seen"), "seen": d.get("seen") or []}
            for d in docs[:limit]]
