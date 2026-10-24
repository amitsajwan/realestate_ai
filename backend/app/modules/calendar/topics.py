"""Topic pages: one public page per subject our guide reels keep coming back to (first: the MHADA Pune lottery, whose Marathi
reels got most of our views in October 2026). The MHADA page is information only: no sign-up, no selling (owner 2026-10-18:
"this is information to public, they will never buy our flats"). Buyer topics such as Upper Kharadi may end a section with a
`cta` banner that opens our chat.

A topic is a file in topics/<slug>.json: status line, key dates, sections, results, FAQ, official links and sources, each text
as {"mr": ..., "en": ...}. A section may carry fact tables (`table`, or several titled ones under `tables`) whose rows can link
to our project page (`href`) and carry an availability `tag` (resale: 95%+ booked, open: under 30%, limited: in between); an
item's lead-in can be bolded with **...**. Edit the file when a date changes and the page follows; `checked_on` says when it
was last true.
Its updates are the reels already posted about it: published calendar rows whose slug starts with one of `row_prefixes`, or
whose creative names the topic (a guide JSON with "topic": "<slug>"), shown the way the posts feed shows them.

    GET /public/topics            the live topics (sitemap, links)
    GET /public/topics/{slug}     one topic with its updates, newest first
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from . import public
from .store import Store

router = APIRouter()

TOPICS = Path(__file__).resolve().parent / "topics"
CACHE_SECONDS = 60
MAX_UPDATES = 30
_cache: Dict[str, tuple] = {}


def load(folder: Path = TOPICS) -> Dict[str, dict]:
    out = {}
    for f in sorted(folder.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        out[data["slug"]] = data
    return out


def _belongs(doc: dict, topic: dict) -> bool:
    if (doc.get("creative") or {}).get("topic") == topic["slug"]:
        return True
    return any((doc.get("slug") or "").startswith(p) for p in topic.get("row_prefixes", []))


def updates(topic: dict, rows: List[dict], items: List[dict]) -> List[dict]:
    """The feed items (public.build's view) whose published rows belong to the topic, newest first."""
    links = {d.get("permalink") for d in rows if _belongs(d, topic) and d.get("permalink")}
    picked = [o for o in items if any(link["url"] in links for link in o["links"])]
    return [public._public(o) for o in picked[:MAX_UPDATES]]


def summary(topic: dict) -> dict:
    return {"slug": topic["slug"], "title": topic["title"], "summary": topic["summary"], "status": topic.get("status"),
            "checked_on": topic.get("checked_on"), "lang": topic.get("lang", "en")}


async def _rows(store: Store) -> List[dict]:
    hit = _cache.get("rows")
    if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
        return hit[1]
    rows = await store.items.find({"status": "published"}, {"slug": 1, "permalink": 1, "creative.topic": 1}) \
        .sort("due_at", -1).limit(public.SCAN_ROWS).to_list(public.SCAN_ROWS)
    _cache["rows"] = (time.monotonic(), rows)
    return rows


@router.get("/topics")
async def public_topics(response: Response) -> List[dict]:
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return [summary(t) for t in load().values()]


@router.get("/topics/{slug}")
async def public_topic(slug: str, response: Response, store: Store = Depends(public.get_store)) -> dict:
    topic: Optional[dict] = load().get((slug or "").strip().lower())
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    items, _ = await public._built(store)
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    body = {k: v for k, v in topic.items() if k != "row_prefixes"}
    return {**body, "updates": updates(topic, await _rows(store), items)}
