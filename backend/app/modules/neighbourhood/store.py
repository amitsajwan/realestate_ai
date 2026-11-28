"""The module's collections and the only code that writes them (ARCHITECTURE §5 rule 2)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

AREA_RESEARCH = "area_research"          # _id "<kind>|<place>": {kind, place, data, sources, computed_at, tried_at, ok, note}
SCHOOLS = "schools"                      # _id "<board>|<affiliation>": one school from an official board list
WORK_HUB_RESEARCH = "work_hub_research"  # _id hub slug: {data, sources, computed_at}
CITY = "_city"                           # the place of a researcher that works once for all of Pune


class Store:
    def __init__(self, db):
        self.db = db
        self.research = db.get_collection(AREA_RESEARCH)
        self.schools = db.get_collection(SCHOOLS)
        self.hubs = db.get_collection(WORK_HUB_RESEARCH)

    async def put(self, kind: str, place: str, data: Any, sources: List[dict], now: datetime, ok: bool = True,
                  note: str = "") -> None:
        """One researcher's result for one place. A failed run (ok=False) keeps the last good data and only notes the failure."""
        _id = f"{kind}|{place}"
        fields = {"kind": kind, "place": place, "tried_at": now, "ok": ok, "note": note}
        if ok:
            fields.update({"data": data, "sources": sources, "computed_at": now})
        await self.research.update_one({"_id": _id}, {"$set": fields}, upsert=True)

    async def get(self, kind: str, place: str) -> Optional[dict]:
        return await self.research.find_one({"_id": f"{kind}|{place}"})

    async def for_place(self, place: str) -> Dict[str, dict]:
        """{kind: document} of every researcher's stored result for one place, the city-wide ones included (a place's own
        result wins over the city's)."""
        out: Dict[str, dict] = {}
        async for d in self.research.find({"place": {"$in": [place, CITY]}}):
            if d.get("data") is None:
                continue
            if d["place"] == CITY:
                out.setdefault(d["kind"], d)
            else:
                out[d["kind"]] = d
        return out

    async def tried(self, kind: str) -> Dict[str, datetime]:
        """{place: last tried} for one researcher, so the loop can pick what is due."""
        out: Dict[str, datetime] = {}
        async for d in self.research.find({"kind": kind}, {"place": 1, "tried_at": 1}):
            if d.get("tried_at"):
                out[d["place"]] = d["tried_at"]
        return out

    async def put_school(self, doc: dict) -> None:
        await self.schools.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)

    async def schools_in(self, query: dict) -> List[dict]:
        return [d async for d in self.schools.find(query)]

    async def put_hub(self, slug: str, data: Any, sources: List[dict], now: datetime) -> None:
        await self.hubs.update_one({"_id": slug}, {"$set": {"data": data, "sources": sources, "computed_at": now}}, upsert=True)

    async def hub(self, slug: str) -> Optional[dict]:
        return await self.hubs.find_one({"_id": slug})
