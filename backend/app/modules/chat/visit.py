"""What the visitor read earlier in this visit (owner, 2026-10-29: "the website chat should use the pages this visitor read during this
visit, so it greets and asks the right next question, and the lead card shows what they read").

The pages come from the tracking module's own record of this browser's views (tracking.visits.pages_this_visit), never from a list the
browser sends. Each path is read the way the widget reads it (frontend lib/site/chatContext.ts) and kept only when its subject checks out
against our records: a project page that exists, a place we know, a builder with projects. Agents' pages, Studio, agents' own sites and
anything unknown are left out, so a greeting never names something from a URL alone."""
import logging
import re
from typing import Dict, List, Optional

from app.core import areas, pune_places
from app.modules.areastats import hubs as project_hubs, pages as project_pages
from app.modules.tracking import requirement as rq

log = logging.getLogger(__name__)

MAX_READ = 10          # pages kept per visit (the latest)
MAX_CACHE = 40         # resolved paths kept on the session, so each message looks up only new pages
SLUG = re.compile(r"^[a-z][a-z-]{1,39}$")
SLUG_RX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){0,15}$")
PROJECT = re.compile(r"^[a-z0-9][a-z0-9-]{1,119}$")
LISTS = ("top", "new-launches", "ready-to-move")
LIST_LABEL = {"top": "top list", "new-launches": "new launches", "ready-to-move": "ready to move", "all": "projects"}


def place_name(slug) -> Optional[str]:
    """A Pune place's name from a page's slug ('upper-kharadi' -> 'Upper Kharadi'): one of our areas, else a place of the register's
    list. None for a place we do not know, so a greeting never names a place from the URL alone."""
    s = str(slug or "").strip().lower()
    if not SLUG_RX.match(s):
        return None
    a = areas.get(s)
    if a:
        return a.name
    p = pune_places.BY_SLUG.get(s)
    return p.name if p else None


def _bhk(seg: str) -> Optional[int]:
    m = re.fullmatch(r"([1-4])-bhk", seg or "")
    return int(m.group(1)) if m else None


def read_path(path: str) -> Optional[dict]:
    """A buyer page's kind and slug from its path, as chatContextFromPath reads it; None for every other page (home, news, agents' pages,
    agents' own sites, Studio, unknown)."""
    parts = [p for p in str(path or "").split("?")[0].split("#")[0].split("/") if p]
    if len(parts) < 2:
        return None
    a, b = parts[0], parts[1]
    if a == "projects" and b == "area" and len(parts) >= 3 and SLUG.match(parts[2]):
        rest = parts[3:]
        bhk = next((n for n in map(_bhk, rest) if n), None)
        return {"kind": "list", "slug": parts[2], "list": next((s for s in rest if s in LISTS), "all"), "bhk": bhk}
    if a in ("projects", "check") and len(parts) == 2 and b != "upcoming" and PROJECT.match(b):
        return {"kind": "project", "slug": b}
    if a in ("2-bhk", "3-bhk") and SLUG.match(b):
        return {"kind": "list", "slug": b, "list": "all", "bhk": int(a[0])}
    if a == "price" and len(parts) >= 3 and SLUG.match(parts[2]):
        return {"kind": "list", "slug": parts[2], "list": "all", "bhk": None}
    if a in ("localities", "guides") and SLUG.match(b):
        return {"kind": "area", "slug": b}
    if a == "builders" and PROJECT.match(b):
        return {"kind": "builder", "slug": b}
    return None


def _label(item: dict) -> str:
    """How the lead card and the model's prompt name a page: 'Godrej Ivara', 'Kharadi top list', '2 BHK in Wagholi'."""
    kind = item["kind"]
    if kind == "project":
        return item["name"]
    if kind == "list":
        if item.get("bhk"):
            return f"{rq.bhk_text(item['bhk'])} in {item['area']}"
        return f"{item['area']} {LIST_LABEL.get(item.get('list') or 'all', 'projects')}"
    if kind == "area":
        return f"{item['area']} guide"
    return f"{item['name']} projects"


async def resolve(db, path: str, place_name) -> Optional[dict]:
    """One page as we know it: {kind, path, label, name?, area?, list?, bhk?}, or None when it is not a buyer page or its subject does not
    check out. `place_name` is chat.service.place_name (our areas, then the register's places)."""
    r = read_path(path)
    if r is None:
        return None
    clean = str(path).split("?")[0].split("#")[0]
    item: Optional[dict] = None
    try:
        if r["kind"] == "project":
            p = await project_pages.chat_brief(db, r["slug"])
            if p and p.get("name"):
                item = {"kind": "project", "name": p["name"], "area": p.get("area")}
        elif r["kind"] in ("list", "area"):
            area = place_name(r["slug"])
            if area:
                item = {"kind": r["kind"], "area": area, "list": r.get("list"), "bhk": r.get("bhk")} if r["kind"] == "list" else \
                    {"kind": "area", "area": area}
        elif r["kind"] == "builder":
            b = await project_hubs.chat_builder(db, r["slug"])
            if b and b.get("name"):
                item = {"kind": "builder", "name": b["name"]}
    except Exception as e:   # what they read is a help, never a reason to fail a chat message
        log.info("chat visit page lookup failed: %s", e)
        return None
    if item is None:
        return None
    item = {k: v for k, v in item.items() if v is not None}
    return {**item, "path": clean[:200], "label": _label(item)}


def _key(item: dict) -> tuple:
    return (item["kind"], item.get("name") or "", item.get("area") or "", item.get("list") or "", item.get("bhk") or 0)


async def pages_read(db, paths: List[str], cache: Dict[str, Optional[dict]], place_name) -> List[dict]:
    """The checked pages among `paths` (oldest first), one per subject (its latest reading), at most MAX_READ. `cache` (the session's)
    keeps each path's answer, so a path is looked up once per chat."""
    out: List[dict] = []
    for path in paths[-MAX_READ:]:
        if path not in cache:
            cache[path] = await resolve(db, path, place_name)
        item = cache[path]
        if item:
            out = [x for x in out if _key(x) != _key(item)] + [item]
    while len(cache) > MAX_CACHE:
        cache.pop(next(iter(cache)))
    return out


def trail(items: List[dict]) -> str:
    """'Godrej Ivara → Lodha Camelot → Kharadi top list', for the lead and the session."""
    return " → ".join(i["label"] for i in items)
