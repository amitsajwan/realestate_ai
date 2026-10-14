"""Our own page for every project in the MahaRERA register (docs/plan/project-pages.md): /projects/<slug>.

Each register record gets a `page_slug` once ("rohan-abhilasha-4-wagholi") and keeps it. The page shows the record's facts with
their source and read date, and a paragraph written by code from those facts only. A page is `indexable` (sitemap, no noindex)
when it has a filed completion date and a promoter or pincode; bookings are optional and finished projects stay in.

Other modules get a project's page with `page_for(db, regno)`; a project the register does not have yet is added through the watch
list first (areastats.watch), and then has its page at once.
"""
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from app.core import brand
from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from .service import _count, _day
from .text import ascii_text, builder_slug, promoter_key, words

SAME_AREA = 6
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _place_word(doc: dict) -> str:
    """The place for a slug: "Ranjangaon", not "Khed taluka" (a taluka name is too broad for an address)."""
    name = doc.get("pune_place_name") or ""
    return "" if name.endswith(" taluka") else name


def in_register(d: dict) -> bool:
    """A record that gets a project page: in one of our areas, on a watch list, or anywhere in Pune district."""
    return d.get("locality") in BY_KEY or bool(d.get("watched_by")) or bool(d.get("pune_place"))


def base_slug(doc: dict) -> str:
    """Name words (at most 8) plus the area, e.g. "rohan-abhilasha-4-wagholi"; the area word is not repeated."""
    picked = words(doc.get("name", ""))[:8] or ["project"]
    area = BY_KEY.get(doc.get("locality") or "")
    tail = words(area.name if area else (_place_word(doc) or "pune"))
    if " ".join(tail) not in " ".join(picked):
        picked += tail
    return "-".join(picked)[:80].strip("-")


async def assign_slug(store: Store, doc: dict) -> str:
    """The record's page slug, given once and stored; a clash gets the registration number's last 5 characters."""
    if doc.get("page_slug"):
        return doc["page_slug"]
    slug = base_slug(doc)
    other = await store.projects.find_one({"page_slug": slug})
    if other and other["_id"] != doc["_id"]:
        slug = f"{slug}-{ascii_text(doc['_id'])[-5:]}"
    await store.set_project(doc["_id"], page_slug=slug)
    return slug


async def assign_all(store: Store, docs: Optional[List[dict]] = None) -> int:
    """Give every record in our areas or on the watch list its page slug (cheap: only the ones without one). Returns how many.

    Also recomputes cluster_id and cluster_primary for all docs: which registrations belong to the same project
    (towers, phases) so the primary page can be identified.  The cluster fields are stored but no redirects are
    added here — that is a separate step once the coordinator has reviewed the cluster report.
    """
    all_docs = docs if docs is not None else await store.all_projects()
    n = 0
    for d in all_docs:
        if not d.get("page_slug") and in_register(d):
            await assign_slug(store, d)
            n += 1
    # Recompute cluster membership across all docs (needs all records together)
    from .clusters import assign_clusters
    await assign_clusters(store, all_docs)
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
    """Our own last change to the page (enrichment or the details read), full ISO datetime; never MahaRERA's dates. The sitemap's lastmod."""
    stamps = [doc.get("enriched_at"), doc.get("page_text_at")]
    if doc.get("details_ok", True):   # a failed details read changed nothing on the page
        stamps.append(doc.get("details_checked_at"))
    # Full datetime (not just date) so IndexNow sees the actual change time within the day
    dts = [v if v.tzinfo else v.replace(tzinfo=timezone.utc) for v in stamps if isinstance(v, datetime)]
    return max(dts).isoformat() if dts else None


# ---- the name buyers use -------------------------------------------------------------------------------------------------
_PHASE = re.compile(r"^(?:[a-z]|[ivx]+)$", re.I)


def _brand_fix(name: str, promoter: Optional[str]) -> tuple:
    """("Gera World of Joy M", "Gera") for "Geras World of Joy M" by Gera Developments; (name, None) otherwise."""
    words = name.split()
    first = words[0] if words else ""
    pwords = promoter_key(promoter).split()
    if len(first) > 2 and first[-1] in "sS" and pwords and ascii_text(first[:-1]) == pwords[0]:
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
    # a page that stands for several towers or phases is named after the project they share, not after one tower (rank-loop R0)
    group = _brand_fix(" ".join((doc.get("group_name") or "").split()), doc.get("promoter"))[0] if doc.get("group_name") else ""
    marketed = " ".join((doc.get("marketed_name_override") or "").split()) or group or fixed
    variants = [marketed, _base(marketed), group, fixed, _base(fixed)]
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


def can_host(d: dict) -> bool:
    """A record a cluster's other registrations may point at: it has a page we serve AND search may list it.

    Every reader of R0 asks this one question, so a tower never gives its page up to a record that is not in the sitemap:
    `listing`, `hubs`, `seo.targets` and `seo.doctor` all stand a member aside only behind a primary that passes this, and
    `primary_of` follows the member's 301 only to one that still does. `clusters._primary_for` ranks on it too, so when any
    tower of the project has a page search may list, that is the one that hosts the others (docs/plan/seo-review.md D1)."""
    return _served(d) and indexable(d)


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
        "builder_slug": builder_slug(doc.get("promoter")) or None,
        "area": {"key": area.key, "slug": area.slug, "name": area.name} if area else None,
        "pune_place": {"key": doc["pune_place"], "name": doc.get("pune_place_name")} if doc.get("pune_place") else None,
        "completion_now": _day(doc.get("completion_now")), "completion_at_registration": _day(doc.get("completion_at_registration")),
        "units_total": _count(doc.get("units_total")), "units_booked": booked(doc), "completion_passed": completion_passed(doc),
        "details_read_at": read.date().isoformat() if isinstance(read, datetime) and doc.get("details_ok") else None,
        "listed_or_updated": _day(doc.get("last_modified")), "maharera_url": doc.get("source_url") or None,
        # the enriched text (model-written from gathered facts, checked) when there is one, else the code-written paragraph
        "paragraph": doc.get("page_text") or paragraph(doc), "indexable": indexable(doc),
        "marketed_name": names(doc)[0], "aliases": names(doc)[1], "page_updated": page_updated(doc),
        # how people search for the page (seo.targets, rank-loop R1): leads the title and H1; the legal name stays in the body
        "search_name": doc.get("search_name") or None,
        # "People also ask" questions answered from our facts (seo.questions, R4), each with its source and its topic:
        # the topic is what lets the page drop its own question on a topic a real one already covers
        "faq": [{k: f.get(k) for k in ("q", "a", "source", "topic")} for f in doc.get("seo_faq") or []],
        # a search description from facts, written by the page doctor when the page was seen but not clicked (R3)
        "search_description": doc.get("seo_description") or None,
        "same_promoter": same_promoter(doc, docs) if docs is not None else [],
        "enriched_at": doc["enriched_at"].date().isoformat() if isinstance(doc.get("enriched_at"), datetime) else None,
        # links into other pages say how people search for them (rank-loop R5): search_name, else the marketed name
        "same_area": [{"name": s.get("search_name") or names(s)[0], "slug": s["page_slug"], "completion_now": _day(s.get("completion_now"))}
                      for s in same_area],
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
    return [{"name": d.get("name", ""), "marketed_name": names(d)[0], "search_name": d.get("search_name") or None, "slug": d["page_slug"],
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


def web_public(web: Optional[dict]) -> Optional[dict]:
    """What a project page shows of `web_facts` (areastats.webfacts): the published facts with their sources and the read date;
    never the sites that disagree."""
    if not web or not web.get("facts"):
        return None
    at = web.get("at")
    return {"read_at": at.date().isoformat() if isinstance(at, datetime) else None,
            "facts": [{k: f[k] for k in ("key", "label", "text", "official", "sources")} for f in web["facts"]]}


def group_primary(doc: dict, docs: List[dict]) -> dict:
    """The record a tower group's shared facts are kept on (the doc itself when it is alone or the primary)."""
    want = doc.get("cluster_primary")
    return next((d for d in docs if d["_id"] == want), doc) if want else doc


async def web_facts_for(db, regno: str) -> Optional[dict]:
    """The published web facts for a registration (its tower group's), or None."""
    store = Store(db)
    doc = await store.project((regno or "").strip().upper())
    if doc is None:
        return None
    if doc.get("cluster_primary"):
        doc = await store.project(doc["cluster_primary"]) or doc
    return web_public(doc.get("web_facts"))


def primary_of(doc: dict, docs: List[dict]) -> dict:
    """The page a registration is shown on: its cluster's primary when that one is a page search may list (tower and phase
    pages answer 301 to it, docs/plan/rank-loop.md R0), else its own."""
    want = doc.get("cluster_primary")
    if not want:
        return doc
    p = next((d for d in docs if d["_id"] == want), None)
    return p if p is not None and can_host(p) else doc


def towers(doc: dict, docs: List[dict]) -> List[dict]:
    """Every registration of the project a primary page stands for (towers, phases), its own first: MahaRERA facts each."""
    cid = doc.get("cluster_id")
    if not cid:
        return []
    mine = [d for d in docs if d.get("cluster_id") == cid]
    if len(mine) < 2:
        return []
    mine.sort(key=lambda d: (d["_id"] != doc["_id"], _day(d.get("completion_now")) or "9999", d.get("name", "")))
    return [{"regno": d.get("regno") or d["_id"], "name": d.get("name", ""), "completion_now": _day(d.get("completion_now")),
             "completion_at_registration": _day(d.get("completion_at_registration")), "units_total": _count(d.get("units_total")),
             "units_booked": booked(d), "registered_on": _day(d.get("registered_on")), "maharera_url": d.get("source_url") or None}
            for d in mine]


def cluster_stamps(docs: List[dict]) -> dict:
    """{cluster_id: the newest page_updated of its members}, in one pass (lists call cluster_updated thousands of times)."""
    out: dict = {}
    for d in docs:
        cid = d.get("cluster_id")
        s = page_updated(d) if cid else None
        if s and (cid not in out or s > out[cid]):
            out[cid] = s
    return out


def cluster_updated(doc: dict, docs: List[dict], stamps: Optional[dict] = None) -> Optional[str]:
    """A page's own last change; for a primary, the newest of its members' (a tower read changes the merged page too).
    Pass `stamps` (cluster_stamps) when calling it for many pages."""
    cid = doc.get("cluster_id")
    if not cid:
        return page_updated(doc)
    return (stamps if stamps is not None else cluster_stamps(docs)).get(cid) or page_updated(doc)


async def project_page(db, slug: str) -> Optional[dict]:
    """The page for a slug. A tower's slug gets its project's primary page, whose own slug the frontend redirects to (301)."""
    store = Store(db)
    doc = await store.projects.find_one({"page_slug": slug})
    if doc is None or not in_register(doc):
        return None
    docs = await store.all_projects()   # about a thousand records: the same-area list and the builder's track record
    doc = primary_of(doc, docs)
    key = "locality" if doc.get("locality") else "pune_place"
    peers = [d for d in docs if doc.get(key) and d.get(key) == doc[key] and not d.get("cluster_primary")]
    out = view(doc, _similar(doc, peers), docs)
    out["towers"] = towers(doc, docs)
    out["page_updated"] = cluster_updated(doc, docs)
    out["web_facts"] = web_public(group_primary(doc, docs).get("web_facts"))
    try:   # the neighbourhood guide nearest the project (rank-loop R5): a link both ways
        from .hubs import near_guide
        out["near_guide"] = await near_guide(db, doc)
    except Exception:
        out["near_guide"] = None
    # one tower of a project marketed under several registrations (Lodha Camelot): name it and link the whole project, only
    # when that project is live on a public page (agentprojects.groups.public_group; drafts never show)
    from app.modules.agentprojects.groups import public_group
    out["group"] = await public_group(db, out["regno"])
    return out


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
    every = await store.all_projects()
    served = {d["_id"] for d in every if can_host(d)}
    # a tower or phase whose project has a page search may list is not a page of its own (it answers 301 to it)
    docs = [d for d in every if _served(d) and d.get("cluster_primary") not in served]
    if area:
        key = (BY_KEY.get(area) or next((a for a in BY_KEY.values() if a.slug == area), None))
        docs = [d for d in docs if key and d.get("locality") == key.key]
    if place:
        want = place.strip().lower().replace("-", "_")
        docs = [d for d in docs if d.get("pune_place") == want]
    if only_indexable:
        docs = [d for d in docs if indexable(d)]
    docs.sort(key=lambda d: (_day(d.get("last_modified")) or "", d.get("name", "")), reverse=True)
    stamps = cluster_stamps(every)
    return [{"slug": d["page_slug"], "regno": d.get("regno") or d["_id"], "name": d.get("name", ""), "marketed_name": names(d)[0],
             "search_name": d.get("search_name") or None,
             "area": d.get("locality"), "units_total": _count(d.get("units_total")), "units_booked": booked(d),
             "place": d.get("pune_place"), "place_name": d.get("pune_place_name"),
             "promoter": d.get("promoter") or None, "completion_now": _day(d.get("completion_now")),
             "checked": checked_count(d), "checks_total": len(CHECK_LABELS), "active": not is_old(d),
             "listed_or_updated": _day(d.get("last_modified")),
             "page_updated": cluster_updated(d, every, stamps),   # our own last change (the sitemap's lastmod; a primary: its newest tower), never MahaRERA's dates
             "indexable": indexable(d)} for d in docs[:limit]]


# ---- search by the names buyers type -------------------------------------------------------------------------------------
SEARCH_TTL = 60
_search_cache: dict = {}


def _norm(text: Optional[str]) -> str:
    return " ".join(words(text))


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
