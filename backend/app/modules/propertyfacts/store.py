"""The only file that touches Mongo for property facts. Collection `property_facts`: one document per property, the latest
gathered sheet with every fact's sources and when each was read, so a campaign (or a later one) can reuse it and show where
each number came from. Uses only find_one (by _id or alias)/update_one with $set so the in-memory test fakes work."""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .facts import Fact, Reading

COLLECTION = "property_facts"


def key_of(doc: Dict[str, Any], rera_no: str = "") -> str:
    """The MahaRERA number when known (one project, one sheet), else project + locality."""
    if rera_no:
        return rera_no.upper()
    words = re.findall(r"[a-z0-9]+", f"{doc.get('project_name') or ''} {doc.get('locality') or ''}".lower())
    return "-".join(words) or "unknown"


def _fact(f: Fact) -> dict:
    def r(x):
        return {"source": x.source, "url": x.url, "value": x.value, "fetched_at": x.fetched_at}
    return {"value": f.value, "level": f.level, "usable": f.usable, "readings": [r(x) for x in f.readings],
            "disagree": [r(x) for x in f.disagree]}


def _maharera_id(sheet: Any) -> Optional[int]:
    f = sheet.facts.get("maharera_url")
    m = re.search(r"/view/(\d+)", str(f.value)) if f and f.usable else None
    return int(m.group(1)) if m else None


def facts_of(doc: Optional[dict]) -> Dict[str, Fact]:
    """A kept sheet's facts as Fact objects again (to rebuild a campaign brief later)."""
    out: Dict[str, Fact] = {}
    for f in (doc or {}).get("facts") or []:
        rs = [Reading(f["key"], r.get("value"), r.get("source", ""), r.get("url", ""), r.get("fetched_at")) for r in f.get("readings") or []]
        ds = [Reading(f["key"], r.get("value"), r.get("source", ""), r.get("url", ""), r.get("fetched_at")) for r in f.get("disagree") or []]
        out[f["key"]] = Fact(f["key"], f.get("value"), f.get("level", "single"), rs, ds)
    return out


class FactsStore:
    def __init__(self, db):
        self.col = db.get_collection(COLLECTION)

    async def save(self, sheet: Any, doc: Dict[str, Any], now: datetime) -> str:
        """Upsert the sheet; returns its key. Fact keys contain dots ("nearby.hospital"), so facts are stored as a list."""
        rera = sheet.facts["rera_no"].value if "rera_no" in sheet.facts and sheet.facts["rera_no"].usable else ""
        key = key_of(doc, rera)
        body = {
            "project_name": doc.get("project_name"), "locality": doc.get("locality"), "listing_id": doc.get("id") or doc.get("_id"),
            "facts": [{"key": k, **_fact(f)} for k, f in sheet.facts.items()],
            "notes": list(sheet.notes), "match": sheet.match.how if sheet.match else "", "gathered_at": now,
            "alias": key_of(doc),  # project + locality, so a listing without the RERA number still finds this sheet
            "rera_no": rera or None, "maharera_id": _maharera_id(sheet),  # for the register's watch list (areastats.watch)
        }
        await self.col.update_one({"_id": key}, {"$set": body}, upsert=True)
        return key

    async def get(self, key: str) -> Optional[dict]:
        return await self.col.find_one({"_id": key})

    async def watched(self, limit: int = 2000) -> List[dict]:
        """Every kept sheet with a MahaRERA number: {rera_no, maharera_id, project_name}."""
        return await self.col.find({"rera_no": {"$ne": None}}, {"rera_no": 1, "maharera_id": 1, "project_name": 1}).to_list(limit)

    async def find(self, rera: str = "", project: str = "", locality: str = "") -> Optional[dict]:
        """By MahaRERA number, else by project + locality (the key or the alias of a sheet kept under its number)."""
        if rera:
            doc = await self.get(key_of({}, rera))
            if doc:
                return doc
        if project:
            k = key_of({"project_name": project, "locality": locality})
            return await self.get(k) or await self.col.find_one({"alias": k})
        return None
