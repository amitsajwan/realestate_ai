"""Projects we do not have yet, found by number in Google results (areastats.websearch `discovered_projects`), added to the register.

A marketing page often prints the MahaRERA number ("Project RERA Number: PR1260002501386") of a project the register has not
swept yet (Lodha Camelot, Kharadi, 2026-10-12). MahaRERA's public search finds projects by NAME only (its number filter is
ignored), so each step:
1. takes ONE open number (seen most recently first, not tried in the last RETRY_AFTER),
2. makes candidate names from the titles of the results that showed it ("Lodha Camelot Kharadi Pune | Price & Floor Plans" ->
   "Lodha Camelot", "Camelot"), and searches MahaRERA for up to NAMES_PER_STEP names it has not tried for that number,
3. accepts a card ONLY when its registration number is exactly the one we saw: a same-named project with another number is
   never taken, so nothing is ever attached to the wrong project,
4. on a match keeps its MahaRERA id, name and pincode on the discovered record (`status: found`); the watch source
   (`watch_items`, registered in app/wiring.py) then hands it to the register, which reads its details, gives it its area and
   its /projects/<slug> page, and hot projects score it.
When every candidate name was tried, the number itself is searched on Google once: listing sites print the registered name in their
titles and addresses ("ganga-arcadia-c-building-P52100000412"), which is what a person would do, and those names go through step 3.
Still nothing, it stays `open` with the names tried, and a new result gives it new names. `pending()` lists these for the report;
nothing waits for a person, and the exact-number check is why no person is needed. A number that fails `websearch.worth_finding`
(a misprint, another district, 2019 or older) is deleted, not searched.
Gentle: one number per step, PAUSE seconds between MahaRERA searches.
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from app.core.areas import AREAS
from app.modules.newsroom import register
from app.modules.newsroom.sources import maharera as search
from app.modules.newsroom.store import Store

from . import websearch
from .watch import WatchItem
from .websearch import DISCOVERED, SEEN_KEEP

log = logging.getLogger(__name__)

NAMES_PER_STEP = 3
NAME_PAGES = 5                   # MahaRERA result pages read per name: they run oldest first, so a new project of a common name is late
RETRY_AFTER = timedelta(days=1)
PAUSE = 2.0                      # seconds between MahaRERA searches; tests set it to 0
MIN_NAME = 5                     # characters: shorter names match too many projects to be worth a search
SOURCE = "web_discovered"        # the watch source name

_SEGMENT = re.compile(r"\s+[|–—:-]\s+|\s*\|\s*|\s*[–—]\s*")
# words that start the selling part of a title, not the project's name
_NOISE = re.compile(r"\b(price[sd]?|floor ?plans?|brochure|reviews?|possession|rera|maharera|new launch|launch(?:ing|ed)?|official|"
                    r"site|website|by|in|at|near|pune|maharashtra|india|flats?|apartments?|homes?|villas?|plots?|\d+(?:\.\d+)? ?bhk|bhk|"
                    r"project|projects|details?|location|amenities|sale|buy|rent|offers?)\b", re.I)
_AREA_WORDS = sorted({w for a in AREAS for w in (a.name.lower(), *a.aliases)}, key=len, reverse=True)


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def names_from_title(title: str) -> List[str]:
    """Candidate project names from a result title, most specific first."""
    head = _SEGMENT.split((title or "").strip(), maxsplit=1)[0]
    m = _NOISE.search(head)
    head = head[:m.start()] if m else head
    low = head.lower()
    for a in _AREA_WORDS:                                   # "Lodha Camelot Kharadi" -> "Lodha Camelot"
        low = re.sub(rf"(?<![a-z]){re.escape(a)}(?![a-z])", " ", low)
    words = re.findall(r"[a-z0-9]+", low)
    if not words:
        return []
    # full, without the brand, without the last word, the last word alone; never the brand alone ("Lodha" finds too many)
    out = [words, words[1:], words[:-1] if len(words) > 2 else [], words[-1:] if len(words) > 1 else words]
    seen, names = set(), []
    for w in out:
        name = " ".join(w).strip()
        if len(name) >= MIN_NAME and name not in seen:
            seen.add(name)
            names.append(name.title())
    return names


def names_from_link(link: str) -> List[str]:
    """Candidate names from a page's address, which often keeps the wing a title drops. A generic word alone is not a name."""
    slug = urlparse(link or "").path.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"\.\w+$", "", slug).replace("-", " ").replace("_", " ")
    slug = re.sub(r"\b(?:pid )?\d{4,}\b", " ", register.REGNO.sub(" ", slug))
    if len(re.findall(r"[a-zA-Z]{2,}", slug)) < 2:
        return []
    return [n for n in names_from_title(slug) if register.specific_name(n)]


def candidates(doc: dict) -> List[str]:
    """Every candidate name for a discovered number, from all the titles and addresses it was seen in, not yet tried."""
    tried = {t.lower() for t in doc.get("tried_names") or []}
    out: List[str] = []
    for s in doc.get("seen") or []:
        for n in names_from_title(s.get("title", "")) + names_from_link(s.get("link", "")):
            if n.lower() not in tried and n not in out:
                out.append(n)
    return out


async def _ask_google(coll, doc: dict, ask: websearch.Search, now: datetime) -> Optional[dict]:
    """Searches the number once and keeps the pages that print it. None when the search failed: asked again after RETRY_AFTER."""
    regno, query = doc["_id"], f'"{doc["_id"]}"'
    try:
        results = await ask(query)
    except Exception as e:
        log.info("discover: Google search of %s failed (%s)", regno, type(e).__name__)
        await coll.update_one({"_id": regno}, {"$set": {"last_try": now}})
        return None
    old = doc.get("seen") or []
    links = {s.get("link") for s in old}
    new = [{"query": query, "title": r.get("title", "")[:160], "link": r["link"], "at": now} for r in results
           if r.get("link") and r["link"] not in links
           and regno.lower() in f"{r.get('title', '')} {r.get('snippet', '')} {r['link']}".lower()]
    seen = (old + new)[-SEEN_KEEP:]
    await coll.update_one({"_id": regno}, {"$set": {"seen": seen, "google_at": now}})
    return {**doc, "seen": seen, "google_at": now}


async def _find_card(get: search.Fetcher, name: str, regno: str) -> Tuple[bool, Optional[search.MahaReraProject]]:
    """(the site answered, the card carrying exactly this number) over the name's result pages."""
    for page in range(1, NAME_PAGES + 1):
        if page > 1:
            await asyncio.sleep(PAUSE)
        cards = await search.search_by_name(get, name, page=page)
        if cards is None:
            return False, None
        hit = next((c for c in cards if c.regno.upper() == regno.upper()), None)
        if hit or len(cards) < search.PAGE_SIZE:
            return True, hit
    return True, None


async def resolve(store: Store, get: search.Fetcher, now: datetime, ask: Optional[websearch.Search] = None) -> dict:
    """One step: try to find one open number on MahaRERA. Returns what happened, for the refresh step's log."""
    ask = ask or websearch.provider()
    coll = store.db.get_collection(DISCOVERED)
    known = {d.get("regno") or d["_id"] for d in await store.all_projects()}
    docs = await coll.find({}).to_list(2000)
    open_docs = []
    for d in docs:
        if d.get("status") == "found" or d["_id"] in known:
            continue
        if not websearch.worth_finding(d["_id"]):
            await coll.delete_one({"_id": d["_id"]})
            continue
        last = d.get("last_try")
        if isinstance(last, datetime) and now - _aware(last) < RETRY_AFTER:
            continue
        if candidates(d) or (ask and not d.get("google_at")):
            open_docs.append(d)
    if not open_docs:
        return {"tried": None}
    open_docs.sort(key=lambda d: _aware(d["last_seen"]) if isinstance(d.get("last_seen"), datetime) else now, reverse=True)
    doc, regno = open_docs[0], open_docs[0]["_id"]
    if not candidates(doc):
        doc = await _ask_google(coll, doc, ask, now)
        if doc is None:
            return {"tried": regno, "found": None, "names": []}
    tried = list(doc.get("tried_names") or [])
    for i, name in enumerate(candidates(doc)[:NAMES_PER_STEP]):
        if i:
            await asyncio.sleep(PAUSE)
        answered, hit = await _find_card(get, name, regno)
        if not answered:                                    # the site did not answer: not tried, ask again next time
            break
        tried.append(name)
        if hit:
            await coll.update_one({"_id": regno}, {"$set": {
                "status": "found", "found_at": now, "found_by": name, "name": hit.name, "pincode": hit.pincode,
                "maharera_id": register.maharera_id(hit.url), "source_url": hit.url, "tried_names": tried, "last_try": now}})
            log.info("discover: %s is %s (MahaRERA, searched as %r)", regno, hit.name, name)
            return {"tried": regno, "found": hit.name}
    await coll.update_one({"_id": regno}, {"$set": {"status": "open", "tried_names": tried, "last_try": now}})
    return {"tried": regno, "found": None, "names": tried[-NAMES_PER_STEP:]}


async def watch_items(db) -> List[WatchItem]:
    """The watch source: every discovered number found on MahaRERA (with its id), for the register."""
    docs = await db.get_collection(DISCOVERED).find({"status": "found"}).to_list(2000)
    return [WatchItem(d["_id"], d.get("maharera_id"), d.get("name") or "", d.get("pincode") or "")
            for d in docs if d.get("maharera_id")]


async def pending(store: Store, limit: int = 50) -> List[dict]:
    """Numbers seen in Google results that no candidate name found on MahaRERA (every name tried), for the report."""
    known = {d.get("regno") or d["_id"] for d in await store.all_projects()}
    docs = [d for d in await store.db.get_collection(DISCOVERED).find({}).to_list(2000)
            if d.get("status") != "found" and d["_id"] not in known and websearch.worth_finding(d["_id"])
            and d.get("tried_names") and not candidates(d)]
    return [{"regno": d["_id"], "tried_names": d.get("tried_names"), "seen": (d.get("seen") or [])[-3:]} for d in docs[:limit]]
