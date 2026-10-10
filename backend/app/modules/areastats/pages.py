"""Our own page for every project in the MahaRERA register (docs/plan/project-pages.md): /projects/<slug>.

Each register record gets a `page_slug` once ("rohan-abhilasha-4-wagholi") and keeps it. The page shows the record's facts with
their source and read date, and a paragraph written by code from those facts only. A page is `indexable` (sitemap, no noindex)
when it has a filed completion date and a promoter or pincode; bookings are optional and finished projects stay in.

Other modules get a project's page with `page_for(db, regno)`; a project the register does not have yet is added through the watch
list first (areastats.watch), and then has its page at once.
"""
import re
import time
import unicodedata
from datetime import date, datetime, timedelta
from typing import List, Optional

from app.core import brand
from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from .service import _count, _day

SAME_AREA = 6
_WORDS = re.compile(r"[a-z0-9]+")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()


def _place_word(doc: dict) -> str:
    """The place for a slug: "Ranjangaon", not "Khed taluka" (a taluka name is too broad for an address)."""
    name = doc.get("pune_place_name") or ""
    return "" if name.endswith(" taluka") else name


def in_register(d: dict) -> bool:
    """A record that gets a project page: in one of our areas, on a watch list, or anywhere in Pune district."""
    return d.get("locality") in BY_KEY or bool(d.get("watched_by")) or bool(d.get("pune_place"))


def base_slug(doc: dict) -> str:
    """Name words (at most 8) plus the area, e.g. "rohan-abhilasha-4-wagholi"; the area word is not repeated."""
    words = _WORDS.findall(_ascii(doc.get("name", "")))[:8] or ["project"]
    area = BY_KEY.get(doc.get("locality") or "")
    tail = _WORDS.findall(_ascii(area.name if area else (_place_word(doc) or "pune")))
    if " ".join(tail) not in " ".join(words):
        words += tail
    return "-".join(words)[:80].strip("-")


async def assign_slug(store: Store, doc: dict) -> str:
    """The record's page slug, given once and stored; a clash gets the registration number's last 5 characters."""
    if doc.get("page_slug"):
        return doc["page_slug"]
    slug = base_slug(doc)
    other = await store.projects.find_one({"page_slug": slug})
    if other and other["_id"] != doc["_id"]:
        slug = f"{slug}-{_ascii(doc['_id'])[-5:]}"
    await store.set_project(doc["_id"], page_slug=slug)
    return slug


async def assign_all(store: Store, docs: Optional[List[dict]] = None) -> int:
    """Give every record in our areas or on the watch list its page slug (cheap: only the ones without one). Returns how many."""
    n = 0
    for d in docs if docs is not None else await store.all_projects():
        if not d.get("page_slug") and in_register(d):
            await assign_slug(store, d)
            n += 1
    return n


def completion_passed(doc: dict, today: Optional[date] = None) -> bool:
    day = _day(doc.get("completion_now"))
    return bool(day) and day < (today or date.today()).isoformat()


OLD_AFTER_DAYS = 365   # a project whose filed completion date passed longer ago than this is finished: page kept, not worked on


def is_old(doc: dict, today: Optional[date] = None) -> bool:
    """Finished: the filed completion date passed more than OLD_AFTER_DAYS ago. Its page stays (search, resale buyers) but it is left
    out of the /projects lists, the crawler's checks and the monthly MahaRERA re-reads."""
    day = _day(doc.get("completion_now"))
    return bool(day) and day < ((today or date.today()) - timedelta(days=OLD_AFTER_DAYS)).isoformat()


def recency(doc: dict) -> int:
    """Day number of the newest date we hold for the project (registered on, or last modified on MahaRERA); 0 when none."""
    days = [d for d in (_day(doc.get("registered_on")), _day(doc.get("last_modified"))) if d]
    return date.fromisoformat(max(days)).toordinal() if days else 0


def booked(doc: dict) -> Optional[int]:
    """Homes booked as MahaRERA shows them; None when unknown. A 0 after the filed completion date means the builder has not
    reported bookings (a finished project with nothing sold is not what that 0 says), so it counts as unknown."""
    b = _count(doc.get("units_booked"))
    return None if b == 0 and completion_passed(doc) else b


def indexable(doc: dict) -> bool:
    """In search when the page has a filed completion date and says who or where (promoter or pincode). Bookings are optional;
    finished projects stay in."""
    return bool(_day(doc.get("completion_now")) and (str(doc.get("promoter") or "").strip() or str(doc.get("pincode") or "").strip()))


def page_updated(doc: dict) -> Optional[str]:
    """Our own last change to the page (enrichment or the details read), ISO date; never MahaRERA's dates. The sitemap's lastmod."""
    days = [v.date().isoformat() for v in (doc.get("enriched_at"), doc.get("details_checked_at")) if isinstance(v, datetime)]
    return max(days) if days else None


# ---- the name buyers use -------------------------------------------------------------------------------------------------
_PHASE = re.compile(r"^(?:[a-z]|[ivx]+)$", re.I)


def _brand_fix(name: str, promoter: Optional[str]) -> tuple:
    """("Gera World of Joy M", "Gera") for "Geras World of Joy M" by Gera Developments; (name, None) otherwise."""
    words = name.split()
    first = words[0] if words else ""
    pwords = promoter_key(promoter).split()
    if len(first) > 2 and first[-1] in "sS" and pwords and _ascii(first[:-1]) == pwords[0]:
        return " ".join([first[:-1]] + words[1:]), first[:-1]
    return name, None


def _base(name: str) -> str:
    """Trailing single-letter / roman phase tokens off ("Gera World of Joy M" -> "Gera World of Joy"); two words always kept."""
    words = name.split()
    while len(words) > 2 and _PHASE.match(words[-1]):
        words.pop()
    return " ".join(words)


def names(doc: dict) -> tuple:
    """(marketed_name, aliases): the name buyers google and its variants (base without phase, "Gera's ..." possessive, legal)."""
    legal = " ".join((doc.get("name") or "").split())
    fixed, brand_word = _brand_fix(legal, doc.get("promoter"))
    marketed = " ".join((doc.get("marketed_name_override") or "").split()) or fixed
    variants = [marketed, _base(marketed), fixed, _base(fixed)]
    if brand_word:
        variants += [f"{brand_word}'s" + v[len(brand_word):] for v in (fixed, _base(fixed))]
    variants.append(legal)
    seen, aliases = set(), []
    for v in variants:
        if v and v.lower() not in seen:
            seen.add(v.lower())
            aliases.append(v)
    return marketed, aliases


def _long(day: Optional[str]) -> Optional[str]:
    if not day:
        return None
    y, m, d = day.split("-")
    return f"{int(d)} {_MONTHS[int(m) - 1]} {y}"


def paragraph(doc: dict) -> str:
    """Plain sentences from the record's facts only: no adjectives, no prices, nothing the register does not say."""
    area = BY_KEY.get(doc.get("locality") or "")
    place = doc.get("pune_place_name")
    where = (f"in {area.name}, Pune" if area else f"in {place}, Pune district" if place
             else ("in Pune district" + (f" (pincode {doc['pincode']})" if doc.get("pincode") else "")))
    who = f" by {doc['promoter']}" if doc.get("promoter") else ""
    out = [f"{doc.get('name') or 'This project'} is a project{who} {where}, registered with MahaRERA as {doc.get('regno') or doc['_id']}."]
    now, first = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))
    if now and first and now != first:
        out.append(f"Its filed completion date is {_long(now)}; at registration it was {_long(first)}.")
    elif now:
        out.append(f"Its filed completion date is {_long(now)}.")
    total, sold = _count(doc.get("units_total")), booked(doc)
    read = doc.get("details_checked_at")
    when = f" when we read the record on {_long(read.date().isoformat())}" if isinstance(read, datetime) else ""
    if total and sold is not None and sold <= total:
        out.append(f"{sold} of {total} homes were booked{when}.")
    elif total:
        out.append(f"MahaRERA lists {total} homes; bookings were not reported{when}.")
    if completion_passed(doc):
        out.append("The filed completion date has passed: ask for the occupancy certificate (OC).")
    out.append("Check the MahaRERA record before you book, and ask the builder for the agreement's possession date in writing.")
    return " ".join(out)


_LEGAL = re.compile(r"\b(m s|private|pvt|limited|ltd|llp|the|and|co|company|corporation|corp)\b")


def promoter_key(name: Optional[str]) -> str:
    """'M/s. Rohan Builders Pvt. Ltd.' and 'ROHAN BUILDERS PRIVATE LIMITED' -> 'rohan builders'."""
    words = " ".join(_WORDS.findall(_ascii(name or "")))
    return " ".join(_LEGAL.sub(" ", words).split())


def months_later(doc: dict) -> Optional[int]:
    """Whole months the filed completion date moved later since registration; 0 when it did not; None when unknown."""
    now, first = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))
    if not now or not first:
        return None
    (y1, m1, d1), (y2, m2, d2) = (map(int, first.split("-")), map(int, now.split("-")))
    n = (y2 - y1) * 12 + (m2 - m1) - (1 if d2 < d1 - 3 else 0)
    return max(0, n) if now > first else 0


def _served(d: dict) -> bool:
    return bool(d.get("page_slug")) and in_register(d)


def track_record(doc: dict, docs: List[dict]) -> Optional[dict]:
    """The promoter's projects in our register: how many, how many moved their completion date later and by how much."""
    key = promoter_key(doc.get("promoter"))
    if not key:
        return None
    mine = [d for d in docs if promoter_key(d.get("promoter")) == key]
    moved = [m for m in (months_later(d) for d in mine) if m]
    mine.sort(key=lambda d: (_day(d.get("completion_now")) or "9999", d.get("name", "")))
    return {"name": doc.get("promoter"), "count": len(mine), "with_dates": sum(1 for d in mine if months_later(d) is not None),
            "moved_later": len(moved), "avg_months_later": round(sum(moved) / len(moved)) if moved else None,
            "projects": [{"name": d.get("name", ""), "regno": d.get("regno") or d["_id"], "slug": d["page_slug"] if _served(d) else None,
                          "completion_now": _day(d.get("completion_now")), "months_later": months_later(d),
                          "this": d["_id"] == doc["_id"]} for d in mine[:30]]}


def details(doc: dict) -> dict:
    """The 'Project details' grid: MahaRERA's buildings totals and the record's own numbers (None where unknown)."""
    t = doc.get("building_totals") or {}
    total, sold = _count(doc.get("units_total")), booked(doc)
    return {"towers": t.get("towers"), "max_floors": t.get("max_floors"),
            "units_total": total or t.get("units_total"), "units_residential": t.get("units_residential"),
            "units_other": t.get("units_other"),
            "booked_pct": round(100 * sold / total) if total and sold is not None and sold <= total else None,
            "registered_on": _day(doc.get("registered_on")), "completion_moved_months": months_later(doc)}


CHECK_LABELS = {"maharera_general": "MahaRERA record", "buildings": "Buildings and wings", "places": "Location",
                "text": "Description"}


def checks(doc: dict) -> List[dict]:
    """What the enrichment checked for this page, step by step: {key, label, ok, at, note}; empty before the first round."""
    steps = (doc.get("enrichment") or {}).get("steps") or {}
    out = []
    for key, label in CHECK_LABELS.items():
        st = steps.get(key)
        if not st:
            continue
        note = st.get("checked") or ""
        if key == "text":
            note = "written from the gathered facts; every number checked against them" if st.get("ok") else "kept our own paragraph"
        at = st.get("at")
        out.append({"key": key, "label": label, "ok": bool(st.get("ok")),
                    "at": at.date().isoformat() if isinstance(at, datetime) else None, "note": note[:160]})
    return out


def checked_count(doc: dict) -> Optional[int]:
    """How many of the enrichment checks passed (0 to 4); None before the crawler's first round on this project."""
    steps = (doc.get("enrichment") or {}).get("steps")
    if not steps:
        return None
    return sum(1 for k in CHECK_LABELS if (steps.get(k) or {}).get("ok"))


def view(doc: dict, same_area: List[dict], docs: Optional[List[dict]] = None) -> dict:
    area = BY_KEY.get(doc.get("locality") or "")
    read = doc.get("details_checked_at")
    geo = doc.get("geo") or {}
    checked = ((doc.get("enrichment") or {}).get("steps") or {}).get("places") or {}
    return {
        "details": details(doc),
        "buildings": [{k: b.get(k) for k in ("name", "wing", "floors", "units_residential", "units_other", "units_total")}
                      for b in doc.get("buildings") or []],
        # a position only when the check put it near the pincode's centre
        "map": {"lat": geo["lat"], "lon": geo["lon"]} if geo.get("lat") is not None and checked.get("ok") else None,
        "map_from": geo.get("located_from") if geo.get("lat") is not None and checked.get("ok") else None,
        "checks": checks(doc), "text_checked": bool(doc.get("page_text")),
        "builder": track_record(doc, docs) if docs is not None else None,
        "place": doc.get("place_locality") or None, "taluka": doc.get("taluka") or None,
        "slug": doc.get("page_slug"), "name": doc.get("name", ""), "regno": doc.get("regno") or doc["_id"],
        "promoter": doc.get("promoter") or None, "pincode": doc.get("pincode") or None,
        "area": {"key": area.key, "slug": area.slug, "name": area.name} if area else None,
        "pune_place": {"key": doc["pune_place"], "name": doc.get("pune_place_name")} if doc.get("pune_place") else None,
        "completion_now": _day(doc.get("completion_now")), "completion_at_registration": _day(doc.get("completion_at_registration")),
        "units_total": _count(doc.get("units_total")), "units_booked": booked(doc), "completion_passed": completion_passed(doc),
        "details_read_at": read.date().isoformat() if isinstance(read, datetime) and doc.get("details_ok") else None,
        "listed_or_updated": _day(doc.get("last_modified")), "maharera_url": doc.get("source_url") or None,
        # the enriched text (model-written from gathered facts, checked) when there is one, else the code-written paragraph
        "paragraph": doc.get("page_text") or paragraph(doc), "indexable": indexable(doc),
        "marketed_name": names(doc)[0], "aliases": names(doc)[1], "page_updated": page_updated(doc),
        "same_promoter": same_promoter(doc, docs) if docs is not None else [],
        "enriched_at": doc["enriched_at"].date().isoformat() if isinstance(doc.get("enriched_at"), datetime) else None,
        "same_area": [{"name": s.get("name", ""), "slug": s["page_slug"], "completion_now": _day(s.get("completion_now"))} for s in same_area],
        "source": "MahaRERA public records",
    }


SAME_PROMOTER = 8


def same_promoter(doc: dict, docs: List[dict]) -> List[dict]:
    """Up to 8 other pages by the same promoter, active (not finished) first: {name, marketed_name, slug, completion_now}."""
    key = promoter_key(doc.get("promoter"))
    if not key:
        return []
    mine = [d for d in docs if d["_id"] != doc["_id"] and _served(d) and promoter_key(d.get("promoter")) == key]
    mine.sort(key=lambda d: (is_old(d), d.get("name", "")))
    return [{"name": d.get("name", ""), "marketed_name": names(d)[0], "slug": d["page_slug"],
             "completion_now": _day(d.get("completion_now"))} for d in mine[:SAME_PROMOTER]]


def _similar(doc: dict, docs: List[dict]) -> List[dict]:
    """Other indexable projects in the same area, the closest completion year first."""
    key = "locality" if doc.get("locality") else "pune_place" if doc.get("pune_place") else None
    if key is None:
        return []
    year = int((_day(doc.get("completion_now")) or "0")[:4] or 0)
    others = [d for d in docs if d["_id"] != doc["_id"] and d.get(key) == doc[key] and d.get("page_slug") and indexable(d)]
    others.sort(key=lambda d: (abs(int(_day(d.get("completion_now"))[:4]) - year) if year else 0, d.get("name", "")))
    return others[:SAME_AREA]


async def project_page(db, slug: str) -> Optional[dict]:
    store = Store(db)
    doc = await store.projects.find_one({"page_slug": slug})
    if doc is None or not in_register(doc):
        return None
    docs = await store.all_projects()   # about a thousand records: the same-area list and the builder's track record
    key = "locality" if doc.get("locality") else "pune_place"
    peers = [d for d in docs if doc.get(key) and d.get(key) == doc[key]]
    return view(doc, _similar(doc, peers), docs)


async def page_for(db, regno: str) -> Optional[dict]:
    """{slug, path, url, indexable} for a project in the register (in our areas or watched); None when it is not there."""
    store = Store(db)
    doc = await store.project((regno or "").strip().upper())
    if doc is None or not in_register(doc):
        return None
    slug = await assign_slug(store, doc)
    return {"slug": slug, "path": f"/projects/{slug}", "url": f"{brand.SITE}/projects/{slug}", "indexable": indexable(doc)}


async def listing(db, area: Optional[str] = None, only_indexable: bool = True, limit: int = 2000,
                  place: Optional[str] = None) -> List[dict]:
    """Pages for the sitemap, area pages and search: {slug, regno, name, area, place, place_name, promoter, completion_now,
    checked, active, indexable}, newest listed first. `area` is one of our covered areas; `place` any Pune place (key or slug)."""
    store = Store(db)
    docs = [d for d in await store.all_projects() if d.get("page_slug") and in_register(d)]
    if area:
        key = (BY_KEY.get(area) or next((a for a in BY_KEY.values() if a.slug == area), None))
        docs = [d for d in docs if key and d.get("locality") == key.key]
    if place:
        want = place.strip().lower().replace("-", "_")
        docs = [d for d in docs if d.get("pune_place") == want]
    if only_indexable:
        docs = [d for d in docs if indexable(d)]
    docs.sort(key=lambda d: (_day(d.get("last_modified")) or "", d.get("name", "")), reverse=True)
    return [{"slug": d["page_slug"], "regno": d.get("regno") or d["_id"], "name": d.get("name", ""), "marketed_name": names(d)[0],
             "area": d.get("locality"), "units_total": _count(d.get("units_total")), "units_booked": booked(d),
             "place": d.get("pune_place"), "place_name": d.get("pune_place_name"),
             "promoter": d.get("promoter") or None, "completion_now": _day(d.get("completion_now")),
             "checked": checked_count(d), "checks_total": len(CHECK_LABELS), "active": not is_old(d),
             "listed_or_updated": _day(d.get("last_modified")),
             "page_updated": page_updated(d),   # our own last change (the sitemap's lastmod), never MahaRERA's dates
             "indexable": indexable(d)} for d in docs[:limit]]


# ---- search by the names buyers type -------------------------------------------------------------------------------------
SEARCH_TTL = 60
_search_cache: dict = {}


def _norm(text: Optional[str]) -> str:
    return " ".join(_WORDS.findall(_ascii(text or "")))


def clear_search_cache() -> None:
    _search_cache.clear()


async def _search_rows(db) -> List[dict]:
    hit = _search_cache.get(id(db))
    if hit and hit[0] > time.monotonic():
        return hit[1]
    rows = []
    for d in await Store(db).all_projects():
        if not _served(d):
            continue
        marketed, aliases = names(d)
        regno = d.get("regno") or d["_id"]
        rows.append({"out": {"slug": d["page_slug"], "name": d.get("name", ""), "marketed_name": marketed, "regno": regno,
                             "promoter": d.get("promoter") or None,
                             "area": d.get("locality") if d.get("locality") in BY_KEY else None,
                             "place_name": d.get("pune_place_name"), "completion_now": _day(d.get("completion_now")),
                             "units_total": _count(d.get("units_total")), "units_booked": booked(d),
                             "checked": checked_count(d), "checks_total": len(CHECK_LABELS), "active": not is_old(d)},
                     "regno": _norm(regno).replace(" ", ""),
                     "names": [n for n in dict.fromkeys(_norm(x) for x in [d.get("name"), marketed, *aliases]) if n],
                     "hay": " ".join(_norm(x) for x in [d.get("name"), marketed, *aliases, d.get("promoter"),
                                                        d.get("pune_place_name"), regno])})
    _search_cache[id(db)] = (time.monotonic() + SEARCH_TTL, rows)
    return rows


def _score(row: dict, q: str) -> int:
    flat = q.replace(" ", "")
    if flat == row["regno"]:
        return 100
    if flat in row["regno"]:
        return 80
    if any(n.startswith(q) for n in row["names"]):
        return 60
    if q in row["hay"]:
        return 50
    return 30 if all(w in row["hay"] for w in q.split()) else 0


async def search(db, q: str, limit: int = 20) -> List[dict]:
    """Projects matching what a buyer typed (registration number, name, marketed name, alias, promoter, place), best first."""
    qn = _norm(q)
    if len(qn.replace(" ", "")) < 2:
        return []
    scored = [(s, r) for r in await _search_rows(db) if (s := _score(r, qn))]
    scored.sort(key=lambda x: (-x[0], not x[1]["out"]["active"], x[1]["out"]["marketed_name"].lower()))
    return [r["out"] for _, r in scored[:limit]]


async def places(db) -> List[dict]:
    """Pune places with at least one project page, with counts, in the zone order of app/core/pune_places.py; talukas last."""
    from app.core import pune_places
    counts: dict = {}
    for d in await Store(db).all_projects():
        if d.get("page_slug") and d.get("pune_place"):
            c = counts.setdefault(d["pune_place"], {"name": d.get("pune_place_name") or d["pune_place"], "projects": 0, "indexable": 0})
            c["projects"] += 1
            c["indexable"] += 1 if indexable(d) else 0
    zones = list(dict.fromkeys(p.zone for p in pune_places.PLACES))
    out = []
    for p in pune_places.PLACES:
        if p.key in counts:
            out.append({"key": p.key, "slug": p.slug, "name": p.name, "zone": p.zone, **{k: counts[p.key][k] for k in ("projects", "indexable")}})
    for key, c in sorted(counts.items()):
        if key not in pune_places.BY_KEY:
            out.append({"key": key, "slug": key.replace("_", "-"), "name": c["name"], "zone": pune_places.Z_OUT,
                        "projects": c["projects"], "indexable": c["indexable"]})
    order = {z: i for i, z in enumerate(zones)}
    return sorted(out, key=lambda r: order.get(r["zone"], 99))
