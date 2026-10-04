"""Public, read-only news for our own site: `GET /public/news` and `GET /public/news/{id}` (mounted by the integrator, no auth).

Only items the owner approved (status approved, scheduled or published) are returned; drafts, pending, rejected, dropped and failed items
never are. Each item carries our own plain headline, a summary without hashtags, link line or footer, the source name, the original link
(which may be a Google redirect: the site shows it only as 'Read the original at <source>'), the 'as of' date, the card image and the
Facebook / Instagram permalinks when published, and the fixed 'Worth checking' buyer line the captions carry (`buyer_line`, None when
the item has none: education and digest items). No phone numbers, ever.

Addresses: a story's public `id` is a readable slug, `<up to 8 headline words>-<first 6 characters of its stored id>`
(`lohegaon-hospital-opd-awaiting-approval-f5ddee`); digests and roundups keep their own readable ids. The slug is computed, not
stored: the same stored headline and id always give the same slug, so nothing is written on a read and no migration is needed.
The 6 characters make it findable whatever the words say, so `/news/{id}` answers for the slug, for the old stored id (links in
captions already posted) and for any older slug of the same story (its headline was edited): the reply's `id` is always the
current slug, and the site permanently redirects every other address to it."""
import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core import areas as core_areas
from app.core.database import get_database

from . import policy
from . import presentation as pr
from .store import Store

router = APIRouter()
CACHE_SECONDS = 60
SUMMARY_MAX = 700
CHANNEL_NAMES = {"facebook": "facebook", "instagram": "instagram"}
PUBLIC_STATES = ("approved", "scheduled", "published")
SLUG_WORDS = 8
SLUG_CHARS = 60  # the words part, before the id suffix
ID_CHARS = 6
TAIL_WORDS = {"a", "after", "an", "and", "any", "as", "at", "but", "by", "for", "from", "in", "into", "is", "not", "of", "on", "or",
              "than", "the", "to", "with"}  # not last
AREA_WINDOW = 200  # newest public items searched for one area's stories


def get_store() -> Store:
    return Store(get_database())


def _clean(s: str) -> str:
    """One line, no phone-like numbers (links are not touched: they are never part of these fields)."""
    return pr.one_line(pr.URL.sub("", s or ""))


def _iso(d) -> Optional[str]:
    return d.isoformat() if isinstance(d, datetime) else (str(d) if d else None)


def _media(doc: dict) -> Optional[str]:
    import os
    rel = ((doc.get("card") or {}).get("fb"))
    base = (os.environ.get("PUBLIC_MEDIA_BASE_URL") or "").strip().rstrip("/")
    return f"{base}/uploads/{str(rel).lstrip('/')}" if rel and base else None


def _permalinks(doc: dict) -> List[dict]:
    out = []
    for ch, r in ((doc.get("publish") or {}).get("channels") or {}).items():
        if isinstance(r, dict) and r.get("ok") and str(r.get("permalink") or "").startswith("https://") and ch in CHANNEL_NAMES:
            out.append({"channel": ch, "url": r["permalink"]})
    return out


def _is_digest(doc: dict) -> bool:
    return (doc.get("draft") or {}).get("format") == "digest"


def _is_public(doc: Optional[dict]) -> bool:
    return bool(doc) and doc.get("status") in PUBLIC_STATES and bool(doc.get("draft"))


def _area_keys(doc: dict) -> List[str]:
    """The item's areas as app.core.areas keys, in stored order, unknown ones dropped."""
    return [a for a in dict.fromkeys((doc.get("relevance") or {}).get("areas") or []) if a in core_areas.BY_KEY]


def _words(text: str) -> List[str]:
    """Lower-case ascii words: accents folded, digit groups joined ("10,502" -> "10502"), anything else (Devanagari, symbols) gone."""
    t = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.findall(r"[a-z0-9]+", re.sub(r"(?<=\d),(?=\d{3})", "", t.replace("'", "")))


def slug(doc: dict) -> str:
    """The item's public id. Digests keep their stored id. A story: up to 8 words of its headline (at most ~60 characters), then
    the first 6 characters of its stored id; a headline with no ascii words (Hindi or Marathi only) uses its areas and topic."""
    if _is_digest(doc):
        return doc["_id"]
    words, size = [], 0
    for w in _words(_clean(pr.headline(doc))):
        if len(words) == SLUG_WORDS or (words and size + 1 + len(w) > SLUG_CHARS):
            break
        words.append(w)
        size += len(w) + bool(size)
    while len(words) > 1 and words[-1] in TAIL_WORDS:  # "...approved-for-the" reads cut off: end on a word that says something
        words.pop()
    if not words:
        words = [core_areas.BY_KEY[a].slug for a in _area_keys(doc)[:2]] or ["pune"]
        words += _words(pr.pillar_label(doc).replace("Local news", "")) + ["news"]
    return "-".join(words + [str(doc["_id"])[:ID_CHARS].lower()])


def view(doc: dict, full: bool = True, item_ids: Optional[Dict[str, str]] = None) -> dict:
    """The public shape of one item (`full` adds the long parts the detail page needs). `item_ids` maps a digest's story ids to
    their public slugs; a digest entry without one (a MahaRERA project in a roundup, a story no longer public) is not `linked`."""
    d = doc.get("draft") or {}
    parts = pr.split_text(d.get("text", ""))
    digest = doc.get("digest")
    raw = doc.get("raw") or {}
    url = raw.get("url") or d.get("link") or ""
    is_digest = d.get("format") == "digest"
    out = {
        "id": slug(doc), "kind": "digest" if is_digest else "story",
        "headline": _clean(pr.headline(doc)), "summary": _clean(parts.summary)[:SUMMARY_MAX],
        "pillar": pr.pillar(doc), "pillar_label": pr.pillar_label(doc),
        "areas": [{"key": a, "slug": core_areas.BY_KEY[a].slug, "name": core_areas.BY_KEY[a].name} for a in _area_keys(doc)],
        "source_name": _clean(pr.source_name(doc)),
        "source_url": url if str(url).startswith("http") and not is_digest else None,
        "source_is_redirect": pr.is_google_redirect(url),
        "as_of": _iso(pr.as_of(doc)), "image_url": _media(doc), "permalinks": _permalinks(doc),
        "published_at": _iso(doc.get("published_at") or doc.get("updated_at")),
        # the same fixed line the captions carry (presentation.buyer_line over policy.BUYER_LINES), never generated
        "buyer_line": _clean(pr.buyer_line(doc)) or None,
    }
    if full:
        out.update({"our_view": _clean(parts.our_view), "what_to_check": _clean(parts.what_to_check), "disclaimer": policy.DISCLAIMER})
        if is_digest and digest:
            ids = item_ids or {}
            out["items"] = [{"id": ids.get(i["id"], i["id"]), "linked": i["id"] in ids, "headline": _clean(i.get("headline", "")),
                             "source_name": _clean(i.get("source", "")), "line": _clean(i.get("line", ""))} for i in digest.get("items", [])]
            out["tip"] = _clean(digest.get("tip", ""))
    return out


async def find(store: Store, item_id: str) -> Optional[dict]:
    """The public item at this address: its stored id (old links), else a slug, matched by its last part, the first 6
    characters of the stored id (the story whose current slug is exactly this address wins when two share those characters)."""
    doc = await store.get(item_id)
    if _is_public(doc):
        return doc
    head, _, tail = item_id.rpartition("-")
    if not head or not tail or len(tail) > ID_CHARS:
        return None
    # ids that start with `tail` sort together from `tail` onwards: one short index range, no regex
    near = await store.items.find({"_id": {"$gte": tail}}).sort("_id", 1).limit(50).to_list(50)
    found = [d for d in near if str(d["_id"])[:ID_CHARS].lower() == tail and _is_public(d) and not _is_digest(d)]
    return next((d for d in found if slug(d) == item_id), found[0] if found else None)


async def _story_ids(store: Store, doc: dict) -> Dict[str, str]:
    """A digest's story ids that are public stories, mapped to their slugs."""
    out = {}
    for i in ((doc.get("digest") or {}).get("items") or [])[:20]:
        story = await store.get(str(i.get("id", "")))
        if _is_public(story) and not _is_digest(story):
            out[i["id"]] = slug(story)
    return out


@router.get("/news")
async def public_news(response: Response, limit: int = 20, area: Optional[str] = None, store: Store = Depends(get_store)) -> List[dict]:
    """The newest public items; `area=<key>` (an app.core.areas key, or its page slug) keeps the items about that area: an unknown key gives [],
    the weekly digest (it spans every area) is left out, a MahaRERA roundup naming the area is kept."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    limit = max(1, min(limit, 50))
    if area is None:
        return [view(d, full=False) for d in await store.public(limit)]
    found = core_areas.get(area)  # the key; a page slug ("upper-kharadi") is taken too
    if not found:
        return []
    key = found.key
    docs = [d for d in await store.public(AREA_WINDOW)
            if key in _area_keys(d) and not (_is_digest(d) and not (d.get("digest") or {}).get("kind"))]
    return [view(d, full=False) for d in docs[:limit]]


@router.get("/news/{item_id}")
async def public_news_item(item_id: str, response: Response, store: Store = Depends(get_store)) -> dict:
    """One item by its slug or by any older address of it; the reply's `id` is the address to show (and redirect to)."""
    doc = await find(store, item_id)
    if not doc:
        raise HTTPException(404, "Not found")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return view(doc, item_ids=await _story_ids(store, doc) if _is_digest(doc) else None)
