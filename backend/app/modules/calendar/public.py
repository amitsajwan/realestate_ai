"""Public, read-only view of what the Avasetu Page has already posted: `GET /public/posts` (mounted by the integrator, no auth).
Only rows with status 'published' and a real permalink are ever returned; planned, approved, scheduled, failed and skipped rows never are.
The same item posted on two channels (same slug, published close together) is shown once with both links. No phone numbers, ever."""
from app.core import brand
import os
import re
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Response

from app.core.database import get_database

from .store import Store, aware

router = APIRouter()

CACHE_SECONDS = 60
EXCERPT_MAX = 220
TITLE_MAX = 90
GROUP_DAYS = 3
CHANNELS = {"facebook_page": "facebook", "facebook": "facebook", "instagram": "instagram"}

_URL = re.compile(r"https?://\S+|www\.\S+")
_TAG = re.compile(r"#\w+")
_PHONE = re.compile(r"(?<!\w)\+?\d[\d\s\-]{8,}\d(?!\w)")
_FOOTER = re.compile(r"^\s*(?:PUNE Property|" + re.escape(brand.NAME) + r")\s*·.*$", re.M)  # old posts carry the pre-rebrand footer
_cache: Dict[int, tuple] = {}


def get_store() -> Store:
    return Store(get_database())


def clear_cache() -> None:
    _cache.clear()


def _clean(text: str) -> str:
    text = _FOOTER.sub("", text or "")
    return _PHONE.sub("", _TAG.sub("", _URL.sub("", text)))


def _title(caption: str) -> str:
    for line in _clean(caption).splitlines():
        line = re.sub(r"\s+", " ", line).strip(" -–—:·•")
        if line:
            return line if len(line) <= TITLE_MAX else line[:TITLE_MAX - 1].rstrip() + "…"
    return brand.NAME


def _excerpt(caption: str) -> str:
    text = re.sub(r"\s+", " ", _clean(caption)).strip()
    if len(text) <= EXCERPT_MAX:
        return text
    cut = text[:EXCERPT_MAX - 1]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > EXCERPT_MAX * 0.6 else cut).rstrip(" ,;:.-") + "…"


def _image_url(doc: dict) -> Optional[str]:
    base = (os.environ.get("PUBLIC_MEDIA_BASE_URL") or "").strip().rstrip("/")
    images = doc.get("images") or ([doc["image_path"]] if doc.get("image_path") else [])
    if not base or not images:
        return None
    return f"{base}/uploads/{str(images[0]).lstrip('/')}"


def _channel(doc: dict) -> Optional[str]:
    return CHANNELS.get(doc.get("channel", ""))


def _when(doc: dict):
    return aware(doc.get("published_at") or doc.get("updated_at") or doc["due_at"])


def _view(doc: dict) -> dict:
    ch = _channel(doc)
    return {"id": doc["_id"], "kind": doc.get("kind", "post"), "channel": ch, "channels": [ch],
            "title": _title(doc.get("caption", "")), "excerpt": _excerpt(doc.get("caption", "")),
            "image_url": _image_url(doc), "permalink": doc["permalink"], "links": [{"channel": ch, "url": doc["permalink"]}],
            "published_at": _when(doc), "sample": doc.get("kind") == "showcase", "_slug": doc.get("slug")}


def _merge(into: dict, other: dict) -> None:
    if other["channel"] not in into["channels"]:
        into["channels"].append(other["channel"])
        into["links"].append(other["links"][0])
    if not into["image_url"]:
        into["image_url"] = other["image_url"]
    if into["channel"] != "facebook" and other["channel"] == "facebook":  # the Facebook text and link lead
        for k in ("channel", "title", "excerpt", "permalink"):
            into[k] = other[k]
        into["id"] = other["id"]


def build(docs: List[dict], limit: int) -> List[dict]:
    rows = [d for d in docs if d.get("status") == "published" and d.get("permalink") and _channel(d)]
    rows.sort(key=_when, reverse=True)
    out: List[dict] = []
    for d in rows:
        v = _view(d)
        twin = next((o for o in out if o["_slug"] and o["_slug"] == v["_slug"] and o["kind"] == v["kind"]
                     and abs((o["published_at"] - v["published_at"]).days) <= GROUP_DAYS), None)
        if twin:
            _merge(twin, v)
        else:
            out.append(v)
    for o in out:
        o.pop("_slug", None)
        o["links"].sort(key=lambda link: link["channel"] != "facebook")
    return out[:limit]


@router.get("/posts")
async def public_posts(response: Response, limit: int = 12, store: Store = Depends(get_store)) -> List[dict]:
    limit = max(1, min(limit, 50))
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    hit = _cache.get(limit)
    if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
        return hit[1]
    posts = build(await store.listing("published", 2000), limit)
    _cache[limit] = (time.monotonic(), posts)
    return posts
