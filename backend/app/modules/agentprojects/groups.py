"""Marketed project groups: one marketed name sold under several MahaRERA registrations.

Builders register a big project tower by tower under working names: Lodha Camelot (Upper Kharadi) is "Kharadi New Project -
Tower 1", "- Tower 2"... on MahaRERA, and nothing on MahaRERA says these are one project. A project record (agent_projects)
with `registrations` is that link: its `rera_no` is the primary registration, `registrations` every one the project is sold
under (each with its source, e.g. the builder's brochure), `candidates` look-alikes nobody has confirmed (never members).

`Groups(db).resolve(regno, name)` finds the group for a member registration number or for the marketed name ("Lodha Camelot",
"Camelot Kharadi", "Lodha Camelot Tower 11"). It reads draft records too: matching a brochure is internal, nothing is published
from here. Candidates never match."""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .schemas import REGNO

COLLECTION = "agent_projects"
MAX_GROUPS = 500
# words that say where or by whom, not which project: dropped before names are compared (the builder's and locality's words too)
_PLAIN = {"the", "by", "at", "in", "pune", "project", "projects", "new", "phase", "residences", "homes", "tower", "towers",
          "wing", "building"}
_TOWER = re.compile(r"\b(?:tower|wing|building)\s*-?\s*([a-z]?\d{1,3}[a-z]?)\b")


def _words(s: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (s or "").lower())


def members(doc: dict) -> List[str]:
    """The registration numbers a project is sold under (just rera_no for a one-registration record)."""
    regs = [r["regno"] for r in doc.get("registrations") or [] if r.get("regno")]
    return regs or ([doc["rera_no"]] if doc.get("rera_no") else [])


def _who_where(doc: dict) -> set:
    return set(_words(doc.get("builder", ""))) | set(_words(doc.get("locality", "")))


def _core(name: str, doc: dict) -> List[str]:
    drop = _PLAIN | _who_where(doc)
    return [w for w in _words(_TOWER.sub(" ", (name or "").lower())) if w not in drop and not w.isdigit()]


def names_group(doc: dict, name: str) -> bool:
    """True when `name` is the project's marketed name, or its distinctive words plus the builder or the place ("Camelot
    Kharadi" for Lodha Camelot). The distinctive words alone ("Camelot") are not enough: another builder may use them."""
    q = _words(name)
    if not q:
        return False
    if q == _words(doc.get("name", "")):
        return True
    core_q, core_n = _core(name, doc), _core(doc.get("name", ""), doc)
    return bool(core_n) and core_q == core_n and bool(set(q) & _who_where(doc))


def tower_in(doc: dict, name: str) -> Optional[dict]:
    """The registration whose tower label the name says ("Lodha Camelot Tower 11" -> Tower 11's), else None."""
    m = _TOWER.search((name or "").lower())
    if not m:
        return None
    def label(r):
        t = _TOWER.search((r.get("tower") or "").lower())
        return t.group(1) if t else None
    hits = [r for r in doc.get("registrations") or [] if label(r) == m.group(1)]
    return hits[0] if len(hits) == 1 else None


def view(doc: dict, regno: str = "") -> Dict[str, Any]:
    """What a caller needs: the group, the member that matched (if any) and its siblings. No candidates."""
    regs = [dict(r) for r in doc.get("registrations") or []]
    hit = next((r for r in regs if r.get("regno") == regno), None)
    return {
        "name": doc.get("name", ""), "builder": doc.get("builder", ""), "promoter": doc.get("promoter", ""),
        "locality": doc.get("locality", ""), "pincode": doc.get("pincode", ""), "address": doc.get("address", ""),
        "agent_id": doc.get("agent_id"), "slug": doc.get("slug"), "status": doc.get("status", "draft"),
        "primary": doc.get("rera_no"), "regno": hit["regno"] if hit else "", "tower": hit.get("tower", "") if hit else "",
        "registrations": regs, "siblings": [r for r in regs if r is not hit],
    }


def _best(docs: List[dict]) -> dict:
    """Several agents may hold the same project: a live record first, then the most recently updated."""
    def key(d):
        u = d.get("updated_at")
        return (d.get("status") == "live", u.isoformat() if isinstance(u, datetime) else str(u or ""))
    return max(docs, key=key)


class Groups:
    def __init__(self, db):
        self.col = db.get_collection(COLLECTION)

    async def by_regno(self, regno: str) -> Optional[Dict[str, Any]]:
        r = (regno or "").strip().upper()
        if not REGNO.match(r):
            return None
        docs = await self.col.find({"registrations.regno": r}).to_list(50)
        return view(_best(docs), r) if docs else None

    async def by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """The group the name means; None when none does, or when two different groups would (never guess)."""
        if not _words(name):
            return None
        docs = await self.col.find({"registrations.0": {"$exists": True}}).to_list(MAX_GROUPS)
        hits = [d for d in docs if names_group(d, name)]
        if not hits or len({frozenset(members(d)) for d in hits}) != 1:
            return None
        best = _best(hits)
        t = tower_in(best, name)
        return view(best, t["regno"] if t else "")

    async def resolve(self, regno: str = "", name: str = "") -> Optional[Dict[str, Any]]:
        """By a member registration number first, else by the marketed name."""
        return (await self.by_regno(regno) if regno else None) or (await self.by_name(name) if name else None)


async def public_group(db, regno: str) -> Optional[Dict[str, Any]]:
    """For a public page about one registration: the marketed project it is sold as, when that project is LIVE on a public
    agent page and has more than one registration. {name, tower, towers, path}; None otherwise (drafts never leak).
    `path` is Avasetu's shared page (/projects/<slug>) when the catalog carries the project (an indexable agent and a
    MahaRERA reading), else the agent's own project page."""
    from .service import indexable  # service imports maharera and schemas; kept local so this module stays light

    g = await Groups(db).by_regno(regno)
    if not g or g["status"] != "live" or len(g["registrations"]) < 2 or not g.get("slug"):
        return None
    profile = await db.get_collection("agent_public_profiles").find_one({"agent_id": g["agent_id"], "is_public": True})
    if not profile or not profile.get("slug"):
        return None
    doc = await db.get_collection(COLLECTION).find_one({"agent_id": g["agent_id"], "slug": g["slug"]}, {"rera": 1})
    shared = indexable(profile) and bool((doc or {}).get("rera"))
    path = f"/projects/{g['slug']}" if shared else f"/agent/{profile['slug']}/projects/{g['slug']}"
    return {"name": g["name"], "tower": g["tower"], "towers": len(g["registrations"]), "path": path}
