"""Projects the register keeps fresh although they are outside our 8 areas (a project we market in Ranjangaon, say).

A watched project gets its MahaRERA details (completion dates, homes booked) refreshed like an in-area one, but it never counts
in the area stats or the news roundups: its `locality` stays what the rules say (None outside our areas). It carries
`watched_by`, the names of the sources that want it.

Nobody has to keep the list by hand:
- a source: any module registers `add_source(name, fn)` at startup (app/wiring.py); `fn()` returns the projects it cares about
  now (for example every builder project an agent has added). Each refresh step asks every source again, so a project the
  source no longer returns stops being watched by it. Adding a kind of project to watch is one `add_source` line.
- one project: `await watch(store, WatchItem(...), "script")`, from a script or a test.
A project is known by its registration number; MahaRERA's internal id is needed only when the register does not have the
project yet (the details come from MahaRERA's project API, which is keyed by that id).
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable, Dict, Iterable, Optional

from app.modules.newsroom.sources.maharera import DETAIL
from app.modules.newsroom.store import Store

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class WatchItem:
    regno: str                          # MahaRERA registration number, e.g. P52100076768
    maharera_id: Optional[int] = None   # MahaRERA's internal id (public/project/view/<id>); needed for a project new to us
    name: str = ""
    pincode: str = ""


Source = Callable[[], Awaitable[Iterable[WatchItem]]]
_SOURCES: Dict[str, Source] = {}


def add_source(name: str, fn: Source) -> None:
    """Register (or replace) a source of projects to watch. Safe to call again with the same name."""
    _SOURCES[name] = fn


def sources() -> Dict[str, Source]:
    return dict(_SOURCES)


async def watch(store: Store, item: WatchItem, source: str, now: datetime) -> bool:
    """Make sure the register has the project and `source` is among its watchers. False when it cannot be watched
    (unknown to the register and no MahaRERA id to read it by)."""
    regno = (item.regno or "").strip().upper()
    if not regno:
        return False
    doc = await store.project(regno)
    if doc is None:
        if not item.maharera_id:
            return False
        await store.record_projects([{
            "regno": regno, "name": item.name or regno, "pincode": item.pincode, "locality": None,
            "locality_from": "watched, not in our areas", "source": "MahaRERA", "source_url": f"{DETAIL}{int(item.maharera_id)}",
            "checked_at": now,
        }])
        doc = {"watched_by": []}
    by = set(doc.get("watched_by") or [])
    if source not in by:
        await store.set_project(regno, watched_by=sorted(by | {source}))
    return True


async def sync(store: Store, now: datetime) -> dict:
    """Ask every source for its projects: add new ones, and drop the source from projects it no longer returns. A source that
    fails is skipped this time (its projects stay watched), so one broken source never empties the list."""
    out = {"watched": 0, "dropped": 0, "skipped": 0, "failed_sources": []}
    for name, fn in sources().items():
        try:
            items = list(await fn())
        except Exception:
            log.exception("areastats: watch source %s failed", name)
            out["failed_sources"].append(name)
            continue
        wanted = set()
        for item in items:
            if await watch(store, item, name, now):
                wanted.add(item.regno.strip().upper())
                out["watched"] += 1
            else:
                out["skipped"] += 1
        for doc in await store.all_projects():
            by = doc.get("watched_by") or []
            if name in by and doc["_id"] not in wanted:
                await store.set_project(doc["_id"], watched_by=[s for s in by if s != name])
                out["dropped"] += 1
    return out


def is_watched(doc: dict) -> bool:
    return bool(doc.get("watched_by"))
