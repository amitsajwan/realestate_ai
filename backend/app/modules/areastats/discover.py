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
A number whose every candidate name was tried stays `open` with the names tried: a new result title gives it new names and it is
tried again; `pending()` lists the ones nobody could find (the builder registered another name), for a person to resolve.
Gentle: one number per step, PAUSE seconds between MahaRERA searches.
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List

from app.core.areas import AREAS
from app.modules.newsroom import register
from app.modules.newsroom.sources import maharera as search
from app.modules.newsroom.store import Store

from .watch import WatchItem
from .websearch import DISCOVERED

log = logging.getLogger(__name__)

NAMES_PER_STEP = 3
RETRY_AFTER = timedelta(days=1)
PAUSE = 2.0                      # seconds between MahaRERA searches; tests set it to 0
MIN_NAME = 5                     # characters: shorter names match too many projects to be worth a search
SOURCE = "web_discovered"        # the watch source name
IGNORED = "ignored"              # the owner said this number is not ours to add (Studio → Insights → Found on Google)

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


def candidates(doc: dict) -> List[str]:
    """Every candidate name for a discovered number, from all the titles it was seen in, not yet tried."""
    tried = {t.lower() for t in doc.get("tried_names") or []}
    out: List[str] = [n for n in doc.get("owner_names") or [] if n.lower() not in tried]   # the owner's names go first
    for s in doc.get("seen") or []:
        for n in names_from_title(s.get("title", "")):
            if n.lower() not in tried and n not in out:
                out.append(n)
    return out


async def resolve(store: Store, get: search.Fetcher, now: datetime) -> dict:
    """One step: try to find one open number on MahaRERA. Returns what happened, for the refresh step's log."""
    coll = store.db.get_collection(DISCOVERED)
    known = {d.get("regno") or d["_id"] for d in await store.all_projects()}
    docs = await coll.find({}).to_list(2000)
    open_docs = []
    for d in docs:
        if d.get("status") in ("found", IGNORED) or d["_id"] in known:
            continue
        last = d.get("last_try")
        if isinstance(last, datetime) and now - _aware(last) < RETRY_AFTER:
            continue
        if candidates(d):
            open_docs.append(d)
    if not open_docs:
        return {"tried": None}
    open_docs.sort(key=lambda d: _aware(d["last_seen"]) if isinstance(d.get("last_seen"), datetime) else now, reverse=True)
    doc, regno = open_docs[0], open_docs[0]["_id"]
    tried = list(doc.get("tried_names") or [])
    for i, name in enumerate(candidates(doc)[:NAMES_PER_STEP]):
        if i:
            await asyncio.sleep(PAUSE)
        cards = await search.search_by_name(get, name)
        if cards is None:                                   # the site did not answer: not tried, ask again next time
            break
        tried.append(name)
        hit = next((c for c in cards if c.regno.upper() == regno.upper()), None)
        if hit:
            await coll.update_one({"_id": regno}, {"$set": {
                "status": "found", "found_at": now, "found_by": name, "name": hit.name, "pincode": hit.pincode,
                "maharera_id": register.maharera_id(hit.url), "source_url": hit.url, "tried_names": tried, "last_try": now}})
            log.info("discover: %s is %s (MahaRERA, searched as %r)", regno, hit.name, name)
            return {"tried": regno, "found": hit.name}
    await coll.update_one({"_id": regno}, {"$set": {"status": "open", "tried_names": tried, "last_try": now}})
    return {"tried": regno, "found": None, "names": tried[-NAMES_PER_STEP:]}


async def ignore(store: Store, regno: str, now: datetime) -> bool:
    """The owner's "Ignore": never searched again. False when the number is unknown."""
    r = await store.db.get_collection(DISCOVERED).update_one({"_id": regno}, {"$set": {"status": IGNORED, "ignored_at": now}})
    return r.matched_count > 0


async def search_as(store: Store, regno: str, name: str) -> bool:
    """The owner's name for a number nobody could find (the builder registered another name): tried first, on the next step."""
    name = " ".join((name or "").split())[:80]
    if len(name) < MIN_NAME:
        return False
    coll = store.db.get_collection(DISCOVERED)
    doc = await coll.find_one({"_id": regno})
    if doc is None:
        return False
    names = [n for n in doc.get("owner_names") or [] if n.lower() != name.lower()] + [name]
    tried = [t for t in doc.get("tried_names") or [] if t.lower() != name.lower()]
    await coll.update_one({"_id": regno}, {"$set": {"owner_names": names, "tried_names": tried, "status": "open", "last_try": None}})
    return True


async def watch_items(db) -> List[WatchItem]:
    """The watch source: every discovered number found on MahaRERA (with its id), for the register."""
    docs = await db.get_collection(DISCOVERED).find({"status": "found"}).to_list(2000)
    return [WatchItem(d["_id"], d.get("maharera_id"), d.get("name") or "", d.get("pincode") or "")
            for d in docs if d.get("maharera_id")]


async def pending(store: Store, limit: int = 50) -> List[dict]:
    """Numbers seen in Google results that no candidate name found on MahaRERA (every name tried): for a person to resolve."""
    known = {d.get("regno") or d["_id"] for d in await store.all_projects()}
    docs = [d for d in await store.db.get_collection(DISCOVERED).find({}).to_list(2000)
            if d.get("status") not in ("found", IGNORED) and d["_id"] not in known and d.get("tried_names") and not candidates(d)]
    return [{"regno": d["_id"], "tried_names": d.get("tried_names"), "seen": (d.get("seen") or [])[-3:]} for d in docs[:limit]]
