"""The knowledge index: everything we publish, cut into short passages and kept in the vector store (knowledge/vectors.py) for the
chat and replies to search.

Sources (read only), each passage {id, kind, title, text, url, area, regno, hash}:
  site     site.ENTRIES: what Avasetu is, buying basics (also always given to the chat whole)
  area     knowledge/areas.py: each area's facts, and each of its FAQ pairs
  topic    calendar/topics/*.json: status and dates, every section, every FAQ pair, in English and Marathi together
  project  the MahaRERA project pages we serve (areastats.pages): the page paragraph with its numbers, each writer section,
           each search FAQ pair and the checked web facts. One passage set per tower group (its primary record).
  post     our published posts and reels (content_calendar), the caption as the post's page shows it
Passages are short on purpose: the meaning model reads about 128 words; BM25 reads all of it.

`loop` (worker role newsroom): every INTERVAL_S builds the passages, embeds only new or changed ones (hash), at most
MAX_PER_CYCLE per cycle so the first fill (~13k projects) runs over several short cycles, and deletes passages whose source is gone.
"""
import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List

from . import site, vectors
from .areas import AREAS

log = logging.getLogger(__name__)

INTERVAL_S = 900
BATCH = 16   # ~4 s of embedder time per batch
MAX_PER_CYCLE = 2500
MAX_TEXT = 1500

# Content's readers, passed in by app/wiring.py (conversations never import content): topics() -> the guide topics by slug
# (calendar.topics.load); caption_text(caption) and caption_title(caption) -> a post's readable text and its title line.
_content: Dict[str, Any] = {"topics": dict, "caption_text": str, "caption_title": str}


def configure(topics: Callable[[], Dict[str, dict]], caption_text: Callable[[str], str], caption_title: Callable[[str], str]) -> None:
    _content.update(topics=topics, caption_text=caption_text, caption_title=caption_title)
PROJECT_FIELDS = {"_id": 1, "regno": 1, "name": 1, "promoter": 1, "pincode": 1, "taluka": 1, "locality": 1, "pune_place": 1,
                  "pune_place_name": 1, "page_slug": 1, "source": 1, "completion_now": 1, "completion_at_registration": 1,
                  "units_total": 1, "units_booked": 1, "details_checked_at": 1, "registered_on": 1, "last_modified": 1,
                  "building_totals": 1, "page_text": 1, "page_sections": 1, "seo_faq": 1, "search_name": 1, "web_facts": 1,
                  "cluster_primary": 1, "group_name": 1, "marketed_name_override": 1, "watched_by": 1}


def _chunk(id: str, kind: str, title: str, text: str, url: str = "", area: str = "", regno: str = "") -> dict:
    text = " ".join((text or "").split())[:MAX_TEXT]
    h = hashlib.sha1(f"{title}\n{text}\n{url}".encode("utf-8")).hexdigest()[:16]
    return {"id": id, "kind": kind, "title": title, "text": text, "url": url, "area": area or "", "regno": regno or "", "hash": h}


def site_chunks() -> Iterable[dict]:
    for e in site.ENTRIES:
        yield _chunk(f"site:{e.id}", "site", "About Avasetu" if e.audience != "buyer" else "Buying a home in Pune", site.text(e))


def area_chunks() -> Iterable[dict]:
    for key, a in AREAS.items():
        facts = [f for f in a.facts if not f.startswith("Check:")]
        checks = [f[len("Check:"):].strip() for f in a.facts if f.startswith("Check:")]
        yield _chunk(f"area:{key}", "area", f"{a.name}, Pune", " ".join(facts), a.page, key)
        if checks:
            yield _chunk(f"area:{key}:check", "area", f"{a.name}: what to check", " ".join(checks), a.page, key)
        for i, (q, ans) in enumerate(a.faq):
            yield _chunk(f"area:{key}:faq{i}", "area", f"{a.name}: {q}", ans, a.page, key)


def _both(v) -> str:
    """A topic text {mr, en} as one passage text: English first, then Marathi (questions come in both)."""
    if isinstance(v, dict):
        return " ".join(x for x in (v.get("en"), v.get("mr")) if x)
    return str(v or "")


def _tables(section: dict) -> List[dict]:
    """A section's fact tables: one `table`, or several under `tables` (a page splits averages from project figures)."""
    return ([section["table"]] if section.get("table") else []) + list(section.get("tables") or [])


def _rows(table: dict) -> str:
    return " ".join("; ".join(f"{c}: {v}" for c, v in zip(table.get("columns", []), r["cells"])) + "."
                    for r in table.get("rows", []))


def _unbold(text: str) -> str:
    """The page bolds an item's lead-in with **...**; a chat reply quoting it should not show the asterisks."""
    return text.replace("**", "")


def topic_chunks() -> Iterable[dict]:
    for slug, t in _content["topics"]().items():
        title, url = t["title"].get("en", slug), f"/guides/{slug}"
        dates = "; ".join(f"{d['label'].get('en')}: {d['value'].get('en')}" for d in t.get("dates", []))
        dates_mr = "; ".join(f"{d['label'].get('mr')}: {d['value'].get('mr')}" for d in t.get("dates", []))
        yield _chunk(f"topic:{slug}:status", "topic", title,
                     f"{_both(t.get('summary'))} {_both(t.get('status_line'))} Key dates: {dates}. {dates_mr}. "
                     f"Checked on {t.get('checked_on')}.", url)
        for s in t.get("sections", []):
            items = s.get("items") or {}
            tables = " ".join(f"{_both(tb.get('title'))} {_rows(tb)} {_both(tb.get('note'))}" for tb in _tables(s))
            text = (f"{_both(s.get('text'))} {tables} {' '.join(items.get('en', []))} "
                    f"{s['heading'].get('mr', '')}: {' '.join(items.get('mr', []))}")
            yield _chunk(f"topic:{slug}:{s['id']}", "topic", f"{title}: {s['heading'].get('en')}", _unbold(text), url)
        for i, f in enumerate(t.get("faq", [])):
            yield _chunk(f"topic:{slug}:faq{i}", "topic", f"{title}: {f['q'].get('en')}",
                         f"{f['a'].get('en')} {f['q'].get('mr', '')} {f['a'].get('mr', '')}", url)
        if t.get("results"):
            yield _chunk(f"topic:{slug}:results", "topic", f"{title}: {_both(t['results'].get('heading'))}",
                         _both(t["results"].get("text")), url)
        if t.get("warning"):
            yield _chunk(f"topic:{slug}:warning", "topic", f"{title}: warning", _both(t["warning"]), url)


def _details(doc: dict) -> str:
    from app.modules.areastats import pages
    d = pages.details(doc)
    bits = []
    if d.get("towers"):
        bits.append(f"{d['towers']} towers/wings" + (f", up to {d['max_floors']} floors" if d.get("max_floors") else ""))
    if d.get("completion_moved_months"):
        bits.append(f"completion date moved {d['completion_moved_months']} months later since registration")
    if d.get("registered_on"):
        bits.append(f"registered on {d['registered_on']}")
    return ("Project details: " + "; ".join(bits) + ".") if bits else ""


def project_chunks(doc: dict) -> List[dict]:
    from app.core.areas import BY_KEY
    from app.modules.areastats import pages
    regno = doc.get("regno") or doc["_id"]
    area = BY_KEY.get(doc.get("locality") or "")
    where = area.name if area else (doc.get("pune_place_name") or doc.get("taluka") or "Pune district")
    name = doc.get("search_name") or doc.get("group_name") or pages.names(doc)[0] or doc.get("name") or regno
    title, url, akey = f"{name}, {where} (MahaRERA {regno})", f"/projects/{doc['page_slug']}", (area.key if area else doc.get("pune_place") or "")
    first = " ".join(x for x in (doc.get("page_text") or pages.paragraph(doc), _details(doc)) if x)
    out = [_chunk(f"project:{regno}", "project", title, first, url, akey, regno)]
    if doc.get("page_text"):
        for i, s in enumerate(doc.get("page_sections") or []):
            if s.get("text"):
                out.append(_chunk(f"project:{regno}:s{i}", "project", f"{title}: {s.get('heading') or ''}", s["text"], url, akey, regno))
    for i, f in enumerate(doc.get("seo_faq") or []):
        if f.get("q") and f.get("a"):
            out.append(_chunk(f"project:{regno}:faq{i}", "project", f"{title}: {f['q']}", f["a"], url, akey, regno))
    web = pages.web_public(doc.get("web_facts"))
    if web:
        facts = " ".join(f"{f.get('label') or f.get('key')}: {f.get('text')}." for f in web["facts"] if f.get("text"))
        if facts:
            out.append(_chunk(f"project:{regno}:web", "project", f"{title}: facts from builder and portal sites",
                              f"{facts} (read {web.get('read_at')})", url, akey, regno))
    return out


async def project_all(db) -> List[dict]:
    from app.modules.areastats import pages
    out = []
    async for d in db.projects.find({"page_slug": {"$nin": [None, ""]}}, PROJECT_FIELDS):
        if not pages.can_host(d):
            continue
        if d.get("cluster_primary") and d["cluster_primary"] != d["_id"]:
            continue   # a tower of a group: its page redirects to the group's primary, which carries the shared facts
        out.extend(project_chunks(d))
    return out


async def post_chunks(db) -> List[dict]:
    _text, _title = _content["caption_text"], _content["caption_title"]
    out = []
    cur = db.content_calendar.find({"status": "published", "hidden_from_feed": {"$ne": True}, "caption": {"$nin": [None, ""]}},
                                   {"caption": 1, "permalink": 1, "tags.area": 1, "kind": 1})
    async for d in cur:
        text = _text(d.get("caption") or "")
        if len(text) < 40 or d.get("kind") == "showcase":
            continue   # a showcase is a SAMPLE home: never knowledge about a real one
        out.append(_chunk(f"post:{d['_id']}", "post", _title(d.get("caption") or ""), text, d.get("permalink") or "",
                          ((d.get("tags") or {}).get("area") or "").replace("unknown", "")))
    return out


async def build(db) -> List[dict]:
    chunks = [*site_chunks(), *area_chunks(), *topic_chunks()]
    chunks += await post_chunks(db)
    chunks += await project_all(db)
    seen: Dict[str, dict] = {}
    same = set()   # one passage per wording: a post published on Facebook and Instagram is one caption
    for c in chunks:
        key = (c["title"], c["text"])
        if c["text"] and key not in same:
            same.add(key)
            seen[c["id"]] = c
    return list(seen.values())


async def refresh(db) -> dict:
    """One cycle: embed what is new or changed (up to MAX_PER_CYCLE), delete what is gone. Returns counts."""
    await vectors.ensure_collection()
    chunks = await build(db)
    have = await vectors.stored()
    todo = [c for c in chunks if have.get(c["id"]) != c["hash"]]
    # our own words first (site, areas, topics), then posts, then projects: the small sources are searchable within one cycle
    order = {"site": 0, "topic": 1, "area": 2, "post": 3, "project": 4}
    todo.sort(key=lambda c: order.get(c["kind"], 9))
    done = 0
    for i in range(0, min(len(todo), MAX_PER_CYCLE), BATCH):
        await vectors.upsert(todo[i:i + BATCH])
        done += len(todo[i:i + BATCH])
    gone = sorted(set(have) - {c["id"] for c in chunks})
    for i in range(0, len(gone), 500):
        await vectors.delete(gone[i:i + 500])
    return {"passages": len(chunks), "embedded": done, "waiting": len(todo) - done, "deleted": len(gone)}


async def loop() -> None:
    """Worker loop (app/worker.py, role newsroom). Off when QDRANT_URL / EMBEDDER_URL are not set."""
    from app.core.database import get_database
    from app.platform.heartbeats import heartbeat

    log.info("knowledge index: loop started (%s)", "on" if vectors.enabled() else "off: QDRANT_URL or EMBEDDER_URL not set")
    while True:
        started = datetime.now()
        try:
            async with heartbeat("knowledge_index", get_database, on=vectors.enabled()):
                if vectors.enabled():
                    counts = await refresh(get_database())
                    if counts["embedded"] or counts["deleted"]:
                        log.info("knowledge index: %s in %ss", counts, (datetime.now() - started).seconds)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("knowledge index: cycle failed")
        await asyncio.sleep(INTERVAL_S)
