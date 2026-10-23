"""The hot projects banner on every public page (docs/plan/hot-projects.md, "Spotlight"): a short rolling strip of project links.

The owner picks the projects in Studio (Admin > Hot projects banner): each with an optional area (shown only on that area's
pages and first there, else everywhere), an optional short note ("Tower C launched") and an optional end date. With `auto` on,
the strip is filled up to MAX from the hottest projects (hot_score >= HOT_MIN), so it is never empty while there are hot ones.

Only project pages that are live and indexable are ever shown: the strip is internal links into pages Google may index, never a
link to a 404 or a noindex page. Each entry carries the owner's note, else one sourced fact (hubs.fact_line); never a score.

- get_config(db) / set_config(db, body, by, now): the owner's settings (one document);
- public(db, area, now): the strip for one page: [{slug, name, area, area_slug, regnos, note, fact, source, picked}]. `regnos` are
  the registrations the page stands for (its towers too), so the site can link an agent-listed project's own page directly
  instead of through its 301.

The owner may also pick an upcoming project MahaRERA has not registered yet (upcoming.py), as slug "upcoming/<slug>": its page is
/projects/upcoming/<slug>, noindex, and its fact says it is not registered. Never filled in by `auto`.
"""
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from . import hot, upcoming
from .hubs import _primaries, fact_line, link_name
from .pages import indexable, is_old

COLLECTION = "site_settings"
DOC_ID = "spotlight"
MAX = 6                 # entries in the strip
MAX_PICKS = 20          # projects the owner can pick
NOTE_MAX = 60           # characters of a note: one short line in the strip


class SpotlightError(ValueError):
    """A setting the owner cannot save (unknown project, unknown area, bad date); the message is shown in Studio."""


def area_key(area: Optional[str]) -> Optional[str]:
    """An area key from a key or a slug; None for none or one we do not cover."""
    if not area:
        return None
    a = BY_KEY.get(area) or next((x for x in BY_KEY.values() if x.slug == area), None)
    return a.key if a else None


async def get_config(db) -> Dict:
    doc = await db.get_collection(COLLECTION).find_one({"_id": DOC_ID}) or {}
    return {"auto": bool(doc.get("auto", True)), "items": doc.get("items") or [],
            "updated_at": doc.get("updated_at"), "updated_by": doc.get("updated_by")}


def _until(v) -> Optional[str]:
    if not v:
        return None
    try:
        return date.fromisoformat(str(v)[:10]).isoformat()
    except ValueError:
        raise SpotlightError(f"End date {v!r} is not a date (YYYY-MM-DD)")


async def set_config(db, body: Dict, by: str, now: datetime) -> Dict:
    """Replace the owner's settings. Every picked project must have a live page; an area must be one we cover."""
    items = body.get("items") or []
    if len(items) > MAX_PICKS:
        raise SpotlightError(f"Pick at most {MAX_PICKS} projects")
    pages = {d["page_slug"]: d for d in _primaries(await Store(db).shared_projects()) if d.get("page_slug")}
    clean, seen = [], set()
    for it in items:
        slug = str(it.get("slug") or "").strip().strip("/").removeprefix("projects/")
        if not slug or slug in seen:
            continue
        if slug.startswith(upcoming.PREFIX):
            if not await upcoming.get(db, slug.removeprefix(upcoming.PREFIX)):
                raise SpotlightError(f"No upcoming project page /projects/{slug}")
        elif slug not in pages:
            raise SpotlightError(f"No project page /projects/{slug}")
        elif not indexable(pages[slug]):
            raise SpotlightError(f"/projects/{slug} is not in search yet (no filed completion date or promoter): it cannot be shown")
        area = it.get("area") or None
        if area and area_key(area) is None:
            raise SpotlightError(f"We do not cover the area {area!r}")
        clean.append({"slug": slug, "area": area_key(area), "note": str(it.get("note") or "").strip()[:NOTE_MAX],
                      "until": _until(it.get("until"))})
        seen.add(slug)
    fields = {"auto": bool(body.get("auto", True)), "items": clean, "updated_at": now, "updated_by": by}
    col = db.get_collection(COLLECTION)
    if await col.find_one({"_id": DOC_ID}):
        await col.update_one({"_id": DOC_ID}, {"$set": fields})
    else:
        await col.insert_one({"_id": DOC_ID, **fields})
    return await get_config(db)


def _entry(d: dict, now: datetime, regnos: List[str], note: str = "", picked: bool = False) -> dict:
    a = BY_KEY.get(d.get("locality") or "")
    return {"slug": d["page_slug"], "name": link_name(d), "area": a.name if a else None, "area_slug": a.slug if a else None,
            "regnos": regnos, "note": note or None, **fact_line(d, now), "picked": picked}


def _upcoming_entry(slug: str, u: dict, note: str) -> dict:
    return {"slug": slug, "name": u["name"], "area": u["area_name"], "area_slug": u["area_slug"], "regnos": [],
            "note": note or u.get("note") or None, "fact": "coming soon, not yet registered with MahaRERA", "source": "builder",
            "picked": True}


async def public(db, area: Optional[str] = None, now: Optional[datetime] = None, limit: int = MAX) -> List[dict]:
    """The strip for a page: on an area's pages that area's picks first, then picks for everywhere, then (auto) hot projects of
    the area, then hot projects anywhere. Expired, unknown, old and noindex projects are left out."""
    now = now or datetime.now(timezone.utc)
    key = area_key(area)
    cfg = await get_config(db)
    every = await Store(db).shared_projects()
    docs = {d["page_slug"]: d for d in _primaries(every) if d.get("page_slug") and indexable(d) and not is_old(d)}
    regnos: Dict[str, List[str]] = {}
    for d in every:
        if d.get("cluster_primary"):
            regnos.setdefault(d["cluster_primary"], []).append(d.get("regno") or d["_id"])
    for u in await upcoming.live(db):
        docs[upcoming.PREFIX + u["slug"]] = {"upcoming": u}
    own = lambda d: [d.get("regno") or d["_id"], *regnos.get(d["_id"], [])]  # noqa: E731
    today = now.date().isoformat()
    live = [it for it in cfg["items"] if it["slug"] in docs and not (it.get("until") and it["until"] < today)]
    picks = [it for it in live if key and it.get("area") == key] + [it for it in live if not it.get("area")]
    out, seen = [], set()
    for it in picks:
        if it["slug"] not in seen:
            d = docs[it["slug"]]
            out.append(_upcoming_entry(it["slug"], d["upcoming"], it.get("note") or "") if "upcoming" in d
                       else _entry(d, now, own(d), it.get("note") or "", picked=True))
            seen.add(it["slug"])
    if cfg["auto"] and len(out) < limit:
        hot_docs = sorted((d for d in docs.values() if "upcoming" not in d and (d.get("hot_score") or 0) >= hot.HOT_MIN and d["page_slug"] not in seen),
                          key=lambda d: (not (key and d.get("locality") == key), -(d.get("hot_score") or 0), d.get("name", "")))
        out += [_entry(d, now, own(d)) for d in hot_docs[:limit - len(out)]]
    return out[:limit]
