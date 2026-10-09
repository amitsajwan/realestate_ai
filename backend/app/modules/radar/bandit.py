"""Watch budget (docs/RADAR.md §6): Thompson sampling over watches. Each watch is an arm; a check is a pull; a check that finds at
least one lead worth showing is a win. For each watch draw θ ~ Beta(1 + wins + 2·converted, 1 + checks − wins) and spend this
cycle's quota on the highest draws. Proven arms get most of the quota, new arms (Beta(1,1)) still get tried, and arms that keep
finding nothing fade out on their own; after RETIRE_AFTER empty checks a watch is switched off to save quota."""
import random
from typing import List, Optional

from . import store

RETIRE_AFTER = 20


def theta(w: dict, rng: Optional[random.Random] = None) -> float:
    rng = rng or random
    wins = int(w.get("hits") or 0) + 2 * int(w.get("converted") or 0)
    checks = int(w.get("checks") or 0)
    return rng.betavariate(1 + wins, 1 + max(0, checks - int(w.get("hits") or 0)))


def pick(watches: List[dict], n: int, rng: Optional[random.Random] = None) -> List[dict]:
    """The n watches to check this cycle, best draw first."""
    scored = sorted(((theta(w, rng), i) for i, w in enumerate(watches)), reverse=True)
    return [watches[i] for _, i in scored[:n]]


def mean(w: dict) -> float:
    wins = int(w.get("hits") or 0) + 2 * int(w.get("converted") or 0)
    checks = int(w.get("checks") or 0)
    return (1 + wins) / (2 + wins + max(0, checks - int(w.get("hits") or 0)))


async def pulled(db, wid) -> None:
    """A check happened; retire the watch if it never found anything."""
    w = await db.get_collection(store.WATCHES).find_one_and_update({"_id": wid}, {"$inc": {"checks": 1}}, return_document=True)
    if w and w.get("origin") != "manual" and int(w.get("checks") or 0) >= RETIRE_AFTER and not int(w.get("hits") or 0):
        await db.get_collection(store.WATCHES).update_one({"_id": wid}, {"$set": {"active": False, "retired": "no leads"}})


async def won(db, wid, field: str = "hits") -> None:
    """A signal from this watch was shown (hits) or converted; credit the watch and the query that found it."""
    if not wid:
        return
    w = await db.get_collection(store.WATCHES).find_one_and_update({"_id": wid}, {"$inc": {field: 1}}, return_document=True)
    parent = (w or {}).get("parent_id")
    if parent:
        await db.get_collection(store.WATCHES).update_one({"_id": parent}, {"$inc": {field: 1}})
