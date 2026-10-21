"""Search demand: what people search around our areas and projects, and where our site ranks for it.

One list of search phrases (`search_demand`, one document per phrase), filled from:
- Search Console (`from_gsc`, daily with the page counts): the real searches that showed our pages, with impressions, clicks
  and position, and the impressions of the 28 days before, so a phrase whose searches are growing is `rising`;
- Google results (`from_results`, daily after the hot-projects searches): the related searches and "People also ask" questions
  Google shows with our own searches (free with them), and our site's place for every search we run (`rank`, with history).
Each phrase is placed once by the rules: `project` (it names a register project the way people write it: `regno`), `area` (it
names one of our areas) or `topic` (stamp duty, RERA rules, home loans...). Read only: nothing here changes a page. The page
work (answers on project and area pages, topic drafts) reads `top()`.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse

from app.core import brand
from app.core.areas import in_search as named_in
from app.modules.newsroom.store import Store

from . import hot
from .websearch import PHRASE_TYPES, mentions, site

DEMAND = "search_demand"
HISTORY = 60                    # dated readings kept per phrase (Search Console impressions, our rank)
SEEN_IN = 10                    # searches a related phrase was seen with, kept per phrase
PREV_DAYS = 28                  # Search Console reads the last 28 days: compare with the reading 28 days older
RISING_MIN = 10                 # impressions in 28 days before a phrase can count as rising
RISING_RATIO = 1.5              # this many times the 28 days before
NEW_DAYS = 7                    # a phrase first seen this recently, with RISING_MIN impressions, counts as rising
MAX_LEN = 120


def normalize(q: str) -> str:
    """The phrase as a key: lower case, single spaces, no trailing punctuation."""
    return re.sub(r"\s+", " ", (q or "").strip().lower()).rstrip("?.!,;: ")[:MAX_LEN]


def our_host() -> str:
    host = (urlparse(brand.site()).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def classify(phrase: str, projects: List[dict]) -> dict:
    """{kind, area, regno} by the rules: a register project named the way people write it, else one of our areas, else a topic."""
    areas = named_in(phrase)
    area = areas[0].key if areas else None
    for d in projects:
        name = hot.search_name(d.get("name", ""))
        if name and mentions(name, phrase):
            return {"kind": "project", "area": d.get("locality") or area, "regno": d.get("regno") or d["_id"]}
    return {"kind": "area" if area else "topic", "area": area, "regno": None}


def _previous(hist: list, now: datetime, key: str) -> Optional[int]:
    old = [h for h in hist if isinstance(h.get("at"), datetime) and now - _aware(h["at"]) >= timedelta(days=PREV_DAYS)]
    return int(old[-1].get(key) or 0) if old else None


async def _upsert(store: Store, phrase: str, now: datetime, projects: List[dict], source: str, fields: dict,
                  history: Optional[dict] = None, seen_in: Optional[str] = None) -> dict:
    coll = store.db.get_collection(DEMAND)
    key = normalize(phrase)
    if not key:
        return {}
    doc = await coll.find_one({"_id": key})
    new = doc is None
    doc = doc or {"_id": key, "phrase": key, "first_seen": now, "sources": [], "seen_in": [], **classify(key, projects)}
    doc["last_seen"] = now
    if source not in doc["sources"]:
        doc["sources"] = sorted(set(doc["sources"]) | {source})
    if seen_in and seen_in not in doc["seen_in"]:
        doc["seen_in"] = (doc["seen_in"] + [seen_in])[-SEEN_IN:]
    doc.update(fields)
    for name, reading in (history or {}).items():
        hist = list(doc.get(name) or [])
        if hist and isinstance(hist[-1].get("at"), datetime) and _aware(hist[-1]["at"]).date() == now.date():
            hist[-1] = {"at": now, **reading}                 # one reading a day
        else:
            hist.append({"at": now, **reading})
        doc[name] = hist[-HISTORY:]
    if new:
        await coll.insert_one(doc)
    else:
        await coll.update_one({"_id": key}, {"$set": {k: v for k, v in doc.items() if k != "_id"}})
    return doc


async def from_gsc(store: Store, rows: List[dict], now: datetime, projects: Optional[List[dict]] = None) -> int:
    """Search Console rows [{query, page, impressions, clicks, position}] (last 28 days) into phrases. Returns how many."""
    projects = projects if projects is not None else await store.all_projects()
    by: Dict[str, dict] = {}
    for r in rows:
        key = normalize(r.get("query", ""))
        if not key:
            continue
        a = by.setdefault(key, {"impressions": 0, "clicks": 0, "pos_sum": 0.0, "pages": set()})
        imp = int(r.get("impressions") or 0)
        a["impressions"] += imp
        a["clicks"] += int(r.get("clicks") or 0)
        a["pos_sum"] += float(r.get("position") or 0) * max(imp, 1)
        if r.get("page"):
            a["pages"].add(urlparse(r["page"]).path.rstrip("/") or "/")
    for key, a in by.items():
        imp = a["impressions"]
        pos = round(a["pos_sum"] / max(imp, 1), 1) if a["pos_sum"] else None
        doc = await _upsert(store, key, now, projects, "search_console",
                            {"gsc": {"impressions": imp, "clicks": a["clicks"], "position": pos, "pages": sorted(a["pages"])[:10],
                                     "read_at": now}},
                            history={"gsc_history": {"impressions": imp, "position": pos}})
        prev = _previous(doc.get("gsc_history") or [], now, "impressions")
        await store.db.get_collection(DEMAND).update_one({"_id": key}, {"$set": {"gsc_prev": prev, "rising": is_rising(doc, prev, now)}})
    return len(by)


def is_rising(doc: dict, prev: Optional[int], now: datetime) -> bool:
    imp = int((doc.get("gsc") or {}).get("impressions") or 0)
    if imp < RISING_MIN:
        return False
    if prev is not None:
        return imp >= RISING_RATIO * max(prev, 1)
    first = doc.get("first_seen")
    return isinstance(first, datetime) and now - _aware(first) <= timedelta(days=NEW_DAYS)


def rank_of(results: List[dict], host: str) -> Optional[int]:
    """Our site's place among a search's organic results (1 = first), or None when it is not in them."""
    for r in results:
        if r.get("type", "organic") == "organic" and not r.get("ad") and int(r.get("position") or 0) > 0:
            s = site(r.get("link", ""))
            if s == host or s.endswith("." + host):
                return int(r["position"])
    return None


async def from_results(store: Store, docs: List[dict], now: datetime, projects: Optional[List[dict]] = None) -> dict:
    """Google results (web_search_results documents) into phrases: our rank for each search run today, and the related
    searches and questions shown with every search. Returns counts."""
    projects = projects if projects is not None else await store.all_projects()
    host, ranked, phrases = our_host(), 0, 0
    for doc in docs:
        results = doc.get("results") or []
        if isinstance(doc.get("at"), datetime) and _aware(doc["at"]).date() == now.date():
            pos = rank_of(results, host)
            await _upsert(store, doc["_id"], now, projects, "searched", {"rank": {"position": pos, "at": now}},
                          history={"rank_history": {"position": pos}})
            ranked += 1
        for r in results:
            if r.get("type") in PHRASE_TYPES and r.get("title"):
                await _upsert(store, r["title"], now, projects, r["type"], {}, seen_in=doc["_id"])
                phrases += 1
    return {"ranked": ranked, "phrases": phrases}


async def top(store: Store, kind: Optional[str] = None, area: Optional[str] = None, rising_only: bool = False,
              limit: int = 20) -> List[dict]:
    """The phrases most worth answering: by Search Console impressions, then by how many sources show them."""
    docs = await store.db.get_collection(DEMAND).find({}).to_list(20000)
    docs = [d for d in docs if (kind is None or d.get("kind") == kind) and (area is None or d.get("area") == area)
            and (not rising_only or d.get("rising"))]
    docs.sort(key=lambda d: (-int((d.get("gsc") or {}).get("impressions") or 0), -len(d.get("sources") or []), d["_id"]))
    return [{k: d.get(k) for k in ("phrase", "kind", "area", "regno", "sources", "gsc", "gsc_prev", "rising", "rank", "seen_in")}
            for d in docs[:limit]]
