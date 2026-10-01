"""Public, read-only news for our own site: `GET /public/news` and `GET /public/news/{id}` (mounted by the integrator, no auth).

Only items the owner approved (status approved, scheduled or published) are returned; drafts, pending, rejected, dropped and failed items
never are. Each item carries our own plain headline, a summary without hashtags, link line or footer, the source name, the original link
(which may be a Google redirect: the site shows it only as 'Read the original at <source>'), the 'as of' date, the card image and the
Facebook / Instagram permalinks when published. No phone numbers, ever."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.database import get_database

from . import policy
from . import presentation as pr
from .store import Store

router = APIRouter()
CACHE_SECONDS = 60
SUMMARY_MAX = 700
CHANNEL_NAMES = {"facebook": "facebook", "instagram": "instagram"}


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


def view(doc: dict, full: bool = True) -> dict:
    """The public shape of one item (`full` adds the long parts the detail page needs)."""
    d = doc.get("draft") or {}
    parts = pr.split_text(d.get("text", ""))
    digest = doc.get("digest")
    raw = doc.get("raw") or {}
    url = raw.get("url") or d.get("link") or ""
    is_digest = d.get("format") == "digest"
    out = {
        "id": doc["_id"], "kind": "digest" if is_digest else "story",
        "headline": _clean(pr.headline(doc)), "summary": _clean(parts.summary)[:SUMMARY_MAX],
        "pillar": pr.pillar(doc), "pillar_label": pr.pillar_label(doc),
        "areas": [{"slug": pr.AREA_SLUGS[a], "name": pr.AREA_NAMES[a]} for a in pr.areas(doc)],
        "source_name": _clean(pr.source_name(doc)),
        "source_url": url if str(url).startswith("http") and not is_digest else None,
        "source_is_redirect": pr.is_google_redirect(url),
        "as_of": _iso(pr.as_of(doc)), "image_url": _media(doc), "permalinks": _permalinks(doc),
        "published_at": _iso(doc.get("published_at") or doc.get("updated_at")),
    }
    if full:
        out.update({"our_view": _clean(parts.our_view), "what_to_check": _clean(parts.what_to_check), "disclaimer": policy.DISCLAIMER})
        if is_digest and digest:
            out["items"] = [{"id": i["id"], "headline": _clean(i.get("headline", "")), "source_name": _clean(i.get("source", "")),
                             "line": _clean(i.get("line", ""))} for i in digest.get("items", [])]
            out["tip"] = _clean(digest.get("tip", ""))
    return out


@router.get("/news")
async def public_news(response: Response, limit: int = 20, store: Store = Depends(get_store)) -> List[dict]:
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return [view(d, full=False) for d in await store.public(max(1, min(limit, 50)))]


@router.get("/news/{item_id}")
async def public_news_item(item_id: str, response: Response, store: Store = Depends(get_store)) -> dict:
    doc = await store.get(item_id)
    if not doc or doc.get("status") not in ("approved", "scheduled", "published") or not doc.get("draft"):
        raise HTTPException(404, "Not found")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return view(doc)
