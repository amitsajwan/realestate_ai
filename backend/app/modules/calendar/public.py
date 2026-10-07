"""Public, read-only view of what the Avasetu Page has already posted: `GET /public/posts` (mounted by the integrator, no auth).
Only rows with status 'published' and a real permalink are ever returned; planned, approved, scheduled, failed and skipped rows never are.
The same item posted on two channels (same slug, published close together) is shown once with both links. No phone numbers, ever.

Every item has a page on our site, `/posts/<slug>`; `GET /public/posts/{slug}` gives one item with its full text.
The slug rule, chosen so that an address never changes once it is out:
- It is made from the title (first line) of the EARLIEST published copy of the item, not of the leading Facebook copy, so a
  Facebook copy published hours after the Instagram one does not rename it. Published captions are never edited by the app
  (only planned rows are), so its words stay put.
- On a clash the item published first keeps the plain words; a later one gets `-<first 6 chars of its earliest row id>`.
  Older items never lose their address to newer ones.
- `<words>-<6 chars>` is ALSO accepted for every item, clash or not, so if an older namesake is ever hidden (and the later item
  then gets the plain words) its old suffixed address still finds it; the reply's `slug` is the one to link to (the page
  redirects). A reel hidden behind a post of the same title leaves its address to that post: same story.
"""
from app.core import areas as pune_areas, brand
import os
import re
import time
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.database import get_database

from .store import Store, aware

router = APIRouter()

CACHE_SECONDS = 60
EXCERPT_MAX = 220
TITLE_MAX = 90
GROUP_DAYS = 3
MAX_LIMIT = 500        # the sitemap asks for every post; the feed is built once a minute whatever the limit
SCAN_ROWS = 10000      # published rows read per build (about 6 a day: years of them)
SLUG_WORDS_MAX = 70    # characters of words in a slug
SUFFIX = 6
CHANNELS = {"facebook_page": "facebook", "facebook": "facebook", "instagram": "instagram"}

_URL = re.compile(r"https?://\S+|www\.\S+")
_TAG = re.compile(r"#\w+")
_PHONE = re.compile(r"(?<!\w)\+?\d[\d\s\-]{8,}\d(?!\w)")
_FOOTER = re.compile(r"^\s*(?:PUNE Property|" + re.escape(brand.NAME) + r")\s*·.*$", re.M)  # old posts carry the pre-rebrand footer
_cache: Dict[str, tuple] = {}


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
    """The caption after its first line (the card already shows that line as the title)."""
    lines = [ln for ln in _clean(caption).splitlines() if ln.strip(" -–—:·•")]
    text = re.sub(r"\s+", " ", " ".join(lines[1:] if len(lines) > 1 else lines)).strip()
    if len(text) <= EXCERPT_MAX:
        return text
    cut = text[:EXCERPT_MAX - 1]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > EXCERPT_MAX * 0.6 else cut).rstrip(" ,;:.-") + "…"


def _own(url: str, site: str) -> str:
    """The URL when it is a page of our own site (not an /i/ interest link), else nothing."""
    bare = url.rstrip(".,;:)")
    return url if bare.startswith(site + "/") and "/i/" not in bare else ""


def _text(caption: str) -> str:
    """The full caption for the post's page: no hashtags, phone numbers or footer; links kept only to our own site, and a
    short label left without its link ('Interested?') goes too."""
    site = brand.site()
    out = []
    for line in _FOOTER.sub("", caption or "").splitlines():
        had = bool(_URL.search(line))
        line = _URL.sub(lambda m: _own(m.group(0), site), line)
        line = re.sub(r"[ \t]+", " ", _PHONE.sub("", _TAG.sub("", line))).strip()
        if had and not _URL.search(line) and len(line.strip(" -–—:·•?")) < 40:
            continue
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def slugify(text: str) -> str:
    """'AMCO Equa, Wagholi: 59.99 L.' -> 'amco-equa-wagholi-59-99-l': lower-case words and hyphens, cut at a word."""
    words = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    if len(words) > SLUG_WORDS_MAX:
        cut = words[:SLUG_WORDS_MAX + 1]
        words = cut[:cut.rfind("-")] if "-" in cut else cut[:SLUG_WORDS_MAX]
    return words.strip("-") or "post"


def _reel_still(video: str) -> Optional[str]:
    """A picture for a reel card: its cover ('x-cover.jpg') or the first carousel slide made beside it ('x-1.jpg')."""
    from .config import uploads_dir
    stem = str(video).lstrip("/")[:-4] if str(video).endswith(".mp4") else ""
    for rel in (f"{stem}-cover.jpg", f"{stem}-1.jpg") if stem else ():
        if (uploads_dir() / rel).is_file():
            return rel
    return None


def _media_urls(doc: dict) -> List[str]:
    """Every slide of the post, as public https URLs (a carousel shows them all, like Instagram)."""
    base = (os.environ.get("PUBLIC_MEDIA_BASE_URL") or "").strip().rstrip("/")
    images = doc.get("images") or ([doc["image_path"]] if doc.get("image_path") else [])
    return [f"{base}/uploads/{str(i).lstrip('/')}" for i in images if i] if base else []


def _site_url(doc: dict) -> Optional[str]:
    """The page on our own site the post points to (the Facebook caption carries it), for the card's main link."""
    site = brand.site()
    for url in _URL.findall(doc.get("caption") or ""):
        url = url.rstrip(".,;:)")
        if url.startswith(site + "/") and "/i/" not in url:
            return url
    return None


def _image_url(doc: dict) -> Optional[str]:
    base = (os.environ.get("PUBLIC_MEDIA_BASE_URL") or "").strip().rstrip("/")
    images = doc.get("images") or ([doc["image_path"]] if doc.get("image_path") else [])
    if not images and doc.get("video"):
        still = _reel_still(doc["video"])
        images = [still] if still else []
    if not base or not images:
        return None
    return f"{base}/uploads/{str(images[0]).lstrip('/')}"


def _channel(doc: dict) -> Optional[str]:
    return CHANNELS.get(doc.get("channel", ""))


def _when(doc: dict):
    return aware(doc.get("published_at") or doc.get("updated_at") or doc["due_at"])


def _view(doc: dict) -> dict:
    from .reach import area, audience
    ch = _channel(doc)
    a = area(doc)
    return {"id": doc["_id"], "kind": doc.get("kind", "post"), "channel": ch, "channels": [ch],
            "title": _title(doc.get("caption", "")), "excerpt": _excerpt(doc.get("caption", "")),
            "image_url": _image_url(doc), "images": _media_urls(doc), "site_url": _site_url(doc),
            "permalink": doc["permalink"], "links": [{"channel": ch, "url": doc["permalink"]}],
            "published_at": _when(doc), "sample": doc.get("kind") == "showcase", "area": a.key if a else None,
            "audience": audience(doc), "_slug": doc.get("slug"), "_text": _text(doc.get("caption", "")),
            "_first": (_when(doc), str(doc["_id"]), _title(doc.get("caption", "")))}


def _merge(into: dict, other: dict) -> None:
    if other["channel"] not in into["channels"]:
        into["channels"].append(other["channel"])
        into["links"].append(other["links"][0])
    if not into["image_url"]:
        into["image_url"] = other["image_url"]
    if len(other["images"]) > len(into["images"]):  # Instagram carries every slide, Facebook only the cover
        into["images"] = other["images"]
    if not into["site_url"]:
        into["site_url"] = other["site_url"]
    if not into["area"]:
        into["area"] = other["area"]
    into["_first"] = min(into["_first"], other["_first"])  # the earliest copy names the post (slug rule above)
    if into["channel"] != "facebook" and other["channel"] == "facebook":  # the Facebook text and link lead
        for k in ("channel", "title", "excerpt", "permalink", "_text"):
            into[k] = other[k]
        into["id"] = other["id"]
        if other["area"]:
            into["area"] = other["area"]


def _name(items: List[dict]) -> Dict[str, dict]:
    """Give every item its `slug` (rule in the module docstring) and return every address that finds it: the slugs and the
    always-valid `<words>-<6 chars>` forms."""
    index: Dict[str, dict] = {}
    for o in sorted(items, key=lambda o: o["_first"][:2]):
        _, first_id, first_title = o["_first"]
        words = slugify(first_title)
        long = f"{words}-{first_id[:SUFFIX].lower()}"
        slug, n = (words if words not in index else long), SUFFIX
        while slug in index:  # two ids sharing 6 chars under one title: practically never, but never a duplicate
            n += 2
            slug = f"{words}-{first_id[:n].lower()}"
        o["slug"] = slug
        index[slug] = o
        index.setdefault(long, o)
    return index


def _all(docs: List[dict]) -> Tuple[List[dict], Dict[str, dict]]:
    """Every visible item, newest first and named, plus the address index (items keep their full text under `_text`)."""
    # hidden_from_feed: posts taken down from Facebook/Instagram (old Page, retired tests); kept as history, never shown
    rows = [d for d in docs if d.get("status") == "published" and d.get("permalink") and _channel(d) and not d.get("hidden_from_feed")]
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
    # a reel with the same title as a post is the same story told twice: show the post (it has the slides) once
    posts = {o["title"] for o in out if o["kind"] != "reel"}
    out = [o for o in out if not (o["kind"] == "reel" and o["title"] in posts)]
    for o in out:
        o.pop("_slug", None)
        o["links"].sort(key=lambda link: link["channel"] != "facebook")
    index = _name(out)
    for o in out:
        o.pop("_first", None)
    return out, index


def _public(item: dict) -> dict:
    return {k: v for k, v in item.items() if not k.startswith("_")}


def _filter(items: List[dict], area: Optional[str]) -> List[dict]:
    return items if area is None else [o for o in items if o["area"] == area]


def build(docs: List[dict], limit: int, area: Optional[str] = None) -> List[dict]:
    """The feed: newest first; `area` (an area key) keeps only that area's posts."""
    return [_public(o) for o in _filter(_all(docs)[0], area)[:limit]]


async def _built(store: Store) -> Tuple[List[dict], Dict[str, dict]]:
    """One build of everything a minute, shared by the feed (any limit or area) and the post pages."""
    hit = _cache.get("all")
    if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
        return hit[1]
    rows = await store.items.find({"status": "published"}).sort("due_at", -1).limit(SCAN_ROWS).to_list(SCAN_ROWS)
    built = _all(rows)
    _cache["all"] = (time.monotonic(), built)
    return built


@router.get("/posts")
async def public_posts(response: Response, limit: int = 12, area: Optional[str] = None,
                       store: Store = Depends(get_store)) -> List[dict]:
    limit = max(1, min(limit, MAX_LIMIT))
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    items, _ = await _built(store)
    if area is not None:  # an area key (its page slug works too); an unknown one gives an empty list
        known = pune_areas.get(area)
        area = known.key if known else "-"
    return [_public(o) for o in _filter(items, area)[:limit]]


@router.get("/posts/{slug}")
async def public_post(slug: str, response: Response, store: Store = Depends(get_store)) -> dict:
    _, index = await _built(store)
    item = index.get((slug or "").strip().lower())
    if not item:
        raise HTTPException(status_code=404, detail="Post not found")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return {**_public(item), "text": item["_text"]}
