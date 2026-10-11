"""What each listing photo shows (AR-5, first part): a kind and a room per photo, from the same vision provider chain as the
visual review (vision_review: free tier, at most 3 images per request, cached by content hash). Used to order the walkthrough
reel by room and to give each pack card its own photo. Never required: without tags the callers keep rank_photos' order.

    tags = await tag_photos(paths)          # {path: {"kind": "interior", "room": "kitchen"}} for the photos it could tag
    tags = cached_tags(paths)               # the same from the cache only: no network (safe in a request path)
    room_order(paths, tags)                 # the first photo (the hero) stays first, the rest follow a walk through the home

Tagging runs only in background work (the reel worker), never in a request path. A missing key, a rate limit (429), a
timeout or a reply that does not fit the schema leaves those photos untagged; nothing is retried in a loop. Tags are cached
per file hash in memory and as JSON next to the review cache, so a photo is tagged once. AI_PHOTO_TAGS=off (or
AI_VISION_REVIEW=off) turns tagging off: no calls, and cached tags are not used either.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence

from . import vision_review as vr

log = logging.getLogger(__name__)

KINDS = ("exterior", "interior", "view", "amenity", "floor_plan", "document", "other")
ROOMS = ("living", "kitchen", "bedroom", "bath", "balcony", "dining", "lobby", "other")
TAG_TIMEOUT = 12.0       # seconds per request: tagging is a nice-to-have, a slow provider is skipped
MAX_TAGGED = 9           # photos tagged per listing (3 requests at most)
NOT_SHOWN = ("document", "floor_plan")   # never a reel scene or a card background when another photo can take its place

SYSTEM = (
    "You label photos of an Indian property listing for a walkthrough video. For EACH image, in the order given, say what it "
    "shows. kind: exterior (the building or house from outside), interior (a room inside the home), view (the view from a "
    "window or balcony), amenity (a shared facility: pool, gym, garden, clubhouse, play area, parking), floor_plan (a floor "
    "plan or layout drawing), document (a paper, certificate, brochure page or screenshot), other. room (only for interior, "
    "or a balcony): living, kitchen, bedroom, bath, balcony, dining, lobby, other; null otherwise. Judge only what you see. "
    'Reply with ONE JSON object only: {"photos": [{"kind": "...", "room": "..." or null}, ...]} with exactly one item per image.'
)
TAG_VERSION = hashlib.sha256(SYSTEM.encode()).hexdigest()[:8]   # a new prompt is a new set of tags


class TagClient(Protocol):
    model: str

    async def ask(self, images: List[bytes], prompt: str, system: str, max_tokens: int = 600,
                  retry: bool = True) -> Optional[Dict[str, Any]]: ...


def tags_off() -> bool:
    return any((os.environ.get(k) or "on").strip().lower() == "off" for k in ("AI_PHOTO_TAGS", "AI_VISION_REVIEW"))


def default_tag_clients() -> List[TagClient]:
    return [] if tags_off() else list(vr.provider_chain(timeout=TAG_TIMEOUT))


def clean_tag(item: Any) -> Optional[Dict[str, Optional[str]]]:
    """One verified tag: an unknown kind or room becomes 'other'; room is None for a photo that is not of a room."""
    if not isinstance(item, dict):
        return None
    kind = str(item.get("kind") or "").strip().lower().replace(" ", "_").replace("-", "_")
    kind = kind if kind in KINDS else "other"
    room = item.get("room")
    if room is None or str(room).strip().lower() in ("", "null", "none"):
        room = None
    else:
        room = str(room).strip().lower()
        room = {"bathroom": "bath", "toilet": "bath", "living_room": "living", "hall": "living"}.get(room, room)
        room = room if room in ROOMS else "other"
    if kind not in ("interior", "view"):
        room = None
    return {"kind": kind, "room": room}


def clean_reply(data: Optional[Dict[str, Any]], n: int) -> Optional[List[Dict[str, Optional[str]]]]:
    """The reply's tags for `n` images, or None when it does not have exactly one valid item per image (a wrong count could
    put a tag on the wrong photo)."""
    items = (data or {}).get("photos") if isinstance(data, dict) else None
    if not isinstance(items, list) or len(items) != n:
        return None
    out = [clean_tag(i) for i in items]
    return None if any(t is None for t in out) else out  # type: ignore[return-value]


def _key(digest: str) -> str:
    return "tag-" + hashlib.sha256((digest + TAG_VERSION).encode()).hexdigest()[:40]


def _hashes(paths: Sequence[Path]) -> Dict[Path, str]:
    out: Dict[Path, str] = {}
    for p in paths:
        try:
            out[p] = vr.file_hash(p)
        except OSError:
            continue
    return out


def cached_tags(paths: Sequence[Any], cache: Optional[Path] = None) -> Dict[Path, Dict[str, Optional[str]]]:
    """Tags already known for these photos (memory and disk cache only, never the network). {} when tagging is off."""
    if tags_off():
        return {}
    directory = cache if cache is not None else vr.cache_dir()
    out: Dict[Path, Dict[str, Optional[str]]] = {}
    for p, digest in _hashes([Path(x) for x in paths if x and Path(x).is_file()]).items():
        hit = vr._cache_get(_key(digest), directory)
        if hit and hit.get("kind") in KINDS:
            out[p] = {"kind": hit["kind"], "room": hit.get("room")}
    return out


async def tag_photos(paths: Sequence[Any], clients: Optional[Sequence[TagClient]] = None,
                     cache: Optional[Path] = None) -> Dict[Path, Dict[str, Optional[str]]]:
    """Tags for up to MAX_TAGGED photos, from the cache or the vision chain in batches of 3. Never raises. `clients=None` uses
    the configured chain (none when tagging is off); `[]` means cache only. A batch no provider answers well stops the run:
    the remaining photos stay untagged (a rate limit will not lift in the next second)."""
    try:
        paths = [Path(p) for p in paths if p and Path(p).is_file()][:MAX_TAGGED]
        if tags_off() or not paths:
            return {}
        chain = list(default_tag_clients() if clients is None else clients)
        directory = cache if cache is not None else vr.cache_dir()
        hashes = await asyncio.to_thread(_hashes, paths)
        out = cached_tags(list(hashes), directory)
        todo = [p for p in hashes if p not in out]
        for i in range(0, len(todo) if chain else 0, vr.MAX_IMAGES):
            batch = todo[i:i + vr.MAX_IMAGES]
            try:
                images = await asyncio.to_thread(lambda: [vr.jpeg_for_review(p) for p in batch])
            except Exception:
                continue
            prompt = f"{len(images)} photo{'s' if len(images) > 1 else ''} of one listing, in order. Tag each."
            tags = None
            for c in chain:
                try:
                    data = await c.ask(images, prompt, SYSTEM, max_tokens=300, retry=False)
                except Exception:
                    log.info("photo tags via %s raised", getattr(c, "model", "?"), exc_info=True)
                    data = None
                tags = clean_reply(data, len(batch))
                if tags:
                    break
            if not tags:
                break
            for p, t in zip(batch, tags):
                vr._cache_put(_key(hashes[p]), {**t, "tagged_by": getattr(c, "model", None)}, directory)
                out[p] = t
        return out
    except Exception:
        log.info("photo tagging failed", exc_info=True)
        return {}


# ---- using the tags -------------------------------------------------------------------------------------------------
# A walk through the home: the building, the living room, dining, kitchen, bedrooms, bathroom, the balcony and its view, then
# the shared amenities. Photos of other rooms and untagged photos follow; plans and papers come last.
_FLOW_ROOM = {"living": 1, "dining": 2, "kitchen": 3, "bedroom": 4, "bath": 5, "balcony": 6}
_FLOW_KIND = {"exterior": 0, "view": 6, "amenity": 7, "other": 8, "floor_plan": 9, "document": 10}
UNTAGGED = 8


def flow_rank(tag: Optional[Mapping[str, Any]]) -> int:
    if not tag:
        return UNTAGGED
    if tag.get("room") in _FLOW_ROOM:
        return _FLOW_ROOM[tag["room"]]
    if tag.get("room") == "lobby":
        return _FLOW_KIND["amenity"]
    return _FLOW_KIND.get(tag.get("kind") or "", UNTAGGED)


def shown(tag: Optional[Mapping[str, Any]]) -> bool:
    """A photo that can be a reel scene or a card background (not a plan or a paper)."""
    return not tag or tag.get("kind") not in NOT_SHOWN


def room_order(paths: Sequence[Any], tags: Mapping[Path, Mapping[str, Any]]) -> List[Path]:
    """`paths` (best first, the hero at the front) with the hero kept first and the rest in room-flow order; the given order
    breaks ties. Unchanged without tags."""
    paths = [Path(p) for p in paths]
    if not paths or not tags:
        return paths
    rest = sorted(range(1, len(paths)), key=lambda i: (flow_rank(tags.get(paths[i])), i))
    return [paths[0]] + [paths[i] for i in rest]
