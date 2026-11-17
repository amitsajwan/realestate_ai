"""The area photo records (collection `area_photos`) and the rules a photo must pass before it is kept or shown.

A record: {_id, area (app/core/areas.py key), image {url, small_url, width, height}, caption, taken_on "YYYY-MM-DD", credit,
kind own|licensed, licence (licensed only), source_url (licensed only), status pending|live|hidden, order, created_by,
created_at, updated_by, updated_at}. The public list is the live ones by `order` (a new upload goes first), each with its credit.
"""
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from app.core import areas
from app.platform import media

log = logging.getLogger(__name__)

COLLECTION = "area_photos"
FOLDER = "area_photos"
KINDS = ("own", "licensed")
STATUSES = ("pending", "live", "hidden")
# the free licences a photo may carry, with the deed a page links to; anything else (NC, ND, "all rights reserved") is refused
LICENCES: Dict[str, str] = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
}
CAPTION_MIN, CAPTION_MAX = 8, 160
CREDIT_MAX = 80
SOURCE_MAX = 500
MIN_SIDE = 800                 # long side: a smaller photo looks broken across a page
OLDEST = date(2000, 1, 1)      # a photo older than this shows a place that is gone
PUBLIC_MAX = 12                # the page shows 8; a few spare for when one is hidden
PER_AREA_MAX = 60
DAILY_UPLOADS = 40             # per person: a whole area's round in one afternoon, with room to retry
IST = timezone(timedelta(hours=5, minutes=30))


class PhotoRefused(Exception):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def _text(v: Any) -> str:
    return " ".join(str(v or "").split())


def _https(url: str) -> bool:
    try:
        p = urlparse(url)
    except ValueError:
        return False
    return p.scheme == "https" and bool(p.hostname) and "." in (p.hostname or "") and " " not in url


def check_facts(raw: Dict[str, Any], today: date) -> Dict[str, Any]:
    """The written part of a photo, cleaned; PhotoRefused (422) saying what to fix when something is missing or wrong."""
    caption, credit = _text(raw.get("caption")), _text(raw.get("credit"))
    if not CAPTION_MIN <= len(caption) <= CAPTION_MAX:
        raise PhotoRefused(f"Write a caption of {CAPTION_MIN} to {CAPTION_MAX} letters: what the photo shows and where.")
    if not credit or len(credit) > CREDIT_MAX:
        raise PhotoRefused(f"Say who took the photo (up to {CREDIT_MAX} letters).")
    try:
        taken = date.fromisoformat(str(raw.get("taken_on") or "").strip())
    except ValueError:
        raise PhotoRefused("Give the date the photo was taken.")
    if taken > today:
        raise PhotoRefused("The date taken cannot be in the future.")
    if taken < OLDEST:
        raise PhotoRefused(f"Photos taken before {OLDEST.year} show a place that has changed too much.")
    kind = str(raw.get("kind") or "").strip()
    if kind not in KINDS:
        raise PhotoRefused("Say whose photo it is: our own, or free-licensed.")
    licence = source = None
    if kind == "licensed":
        licence = str(raw.get("licence") or "").strip()
        if licence not in LICENCES:
            raise PhotoRefused(f"A free-licensed photo needs its licence: one of {', '.join(LICENCES)}.")
        source = str(raw.get("source_url") or "").strip()
        if not source or len(source) > SOURCE_MAX or not _https(source):
            raise PhotoRefused("A free-licensed photo needs the https link to the page it came from.")
    return {"caption": caption, "credit": credit, "taken_on": taken.isoformat(), "kind": kind, "licence": licence,
            "source_url": source}


def _order_key(d: dict):
    return (d.get("order") or 0, -(d["created_at"].timestamp() if isinstance(d.get("created_at"), datetime) else 0))


def view(d: dict) -> Dict[str, Any]:
    """What Studio shows of a record."""
    img = d.get("image") or {}
    return {"id": d["_id"], "area": d["area"], "url": img.get("url"), "small_url": img.get("small_url"),
            "width": img.get("width"), "height": img.get("height"), "caption": d["caption"], "taken_on": d["taken_on"],
            "credit": d["credit"], "kind": d["kind"], "licence": d.get("licence"),
            "licence_url": LICENCES.get(d.get("licence") or ""), "source_url": d.get("source_url"), "status": d["status"],
            "order": d.get("order") or 0, "created_by": d.get("created_by"),
            "created_at": d["created_at"].isoformat() if isinstance(d.get("created_at"), datetime) else d.get("created_at")}


def public_view(d: dict) -> Dict[str, Any]:
    v = view(d)
    return {k: v[k] for k in ("id", "url", "small_url", "width", "height", "caption", "taken_on", "credit", "kind", "licence",
                              "licence_url", "source_url")}


class AreaPhotos:
    def __init__(self, db, now: Optional[Callable[[], datetime]] = None, root: Path = media.UPLOADS):
        self.db, self.root = db, root
        self.now = now or (lambda: datetime.now(timezone.utc))

    @property
    def col(self):
        return self.db.get_collection(COLLECTION)

    def _today(self) -> date:
        return self.now().astimezone(IST).date()

    @staticmethod
    def area(key_or_slug: str) -> areas.Area:
        a = areas.get(key_or_slug or "")
        if a is None:
            raise PhotoRefused("We do not cover that area.", 404)
        return a

    async def _get(self, pid: str) -> dict:
        d = await self.col.find_one({"_id": pid})
        if d is None:
            raise PhotoRefused("Photo not found.", 404)
        return d

    async def list_area(self, key_or_slug: str) -> List[dict]:
        """Every photo of an area, any status, in the page's order."""
        a = self.area(key_or_slug)
        docs = await self.col.find({"area": a.key}).to_list(PER_AREA_MAX * 2)
        return sorted(docs, key=_order_key)

    async def add(self, key_or_slug: str, facts: Dict[str, Any], body: bytes, content_type: str, user_id: str) -> dict:
        """Keep one uploaded photo as pending. The image is checked and saved before the record, and removed again when the
        record cannot be written."""
        a = self.area(key_or_slug)
        clean = check_facts(facts, self._today())
        if content_type not in media.PHOTO_TYPES:
            raise PhotoRefused("Please choose a photo (JPEG, PNG or WebP).", 400)
        if not body:
            raise PhotoRefused("The file is empty.", 400)
        if len(body) > media.MAX_PHOTO_BYTES:
            raise PhotoRefused(f"This photo is too large. Keep it under {media.MAX_PHOTO_BYTES // (1024 * 1024)} MB.", 413)
        now = self.now()
        if await self.col.count_documents({"created_by": user_id, "created_at": {"$gte": now - timedelta(days=1)}}) >= DAILY_UPLOADS:
            raise PhotoRefused(f"That is {DAILY_UPLOADS} photos today. Please send the rest tomorrow.", 429)
        if await self.col.count_documents({"area": a.key}) >= PER_AREA_MAX:
            raise PhotoRefused(f"{a.name} already has {PER_AREA_MAX} photos. Ask the owner to clear some first.", 409)
        pid = uuid.uuid4().hex
        folder = f"{FOLDER}/{a.key}"
        try:
            image = media.keep_photo(body, folder, pid, min_side=MIN_SIDE, root=self.root)
        except media.PhotoError as e:
            if str(e) == "too small":
                raise PhotoRefused(f"This photo is too small. Send one at least {MIN_SIDE} pixels wide.", 400)
            raise PhotoRefused("We could not read this photo. Try another file.", 400)
        first = await self.col.find_one({"area": a.key}, sort=[("order", 1)])
        doc = {"_id": pid, "area": a.key, "image": image, **clean, "status": "pending",
               "order": ((first or {}).get("order") or 0) - 1 if first else 0,
               "created_by": user_id, "created_at": now, "updated_by": user_id, "updated_at": now}
        try:
            await self.col.insert_one(doc)
        except Exception:
            media.drop_photo(folder, pid, root=self.root)
            raise
        log.info("area photo %s added for %s by %s", pid, a.key, user_id)
        return doc

    async def edit(self, pid: str, changes: Dict[str, Any], user_id: str, admin: bool) -> dict:
        """Change the written part. The owner may change any photo; an agent only his own while it waits."""
        d = await self._get(pid)
        if not admin and (d.get("created_by") != user_id or d["status"] != "pending"):
            raise PhotoRefused("Only the owner can change a photo once it is published, or someone else's.", 403)
        merged = {k: d.get(k) for k in ("caption", "credit", "taken_on", "kind", "licence", "source_url")}
        merged.update({k: v for k, v in changes.items() if v is not None})
        clean = check_facts(merged, self._today())
        await self.col.update_one({"_id": pid}, {"$set": {**clean, "updated_by": user_id, "updated_at": self.now()}})
        return await self._get(pid)

    async def set_status(self, pid: str, status: str, user_id: str) -> dict:
        """Publish (live) or hide. The caller checks that the user is the owner."""
        if status not in ("live", "hidden"):
            raise PhotoRefused("Unknown status.")
        d = await self._get(pid)
        if status == "live":
            check_facts(d, self._today())   # an old record that would not pass today's rules is not published as it is
        await self.col.update_one({"_id": pid}, {"$set": {"status": status, "updated_by": user_id, "updated_at": self.now()}})
        log.info("area photo %s %s by %s", pid, status, user_id)
        return await self._get(pid)

    async def reorder(self, key_or_slug: str, ids: List[str], user_id: str) -> List[dict]:
        """Put an area's photos in this order; photos not named keep their order after the named ones."""
        a = self.area(key_or_slug)
        docs = await self.list_area(a.key)
        known = {d["_id"] for d in docs}
        if len(set(ids)) != len(ids) or any(i not in known for i in ids):
            raise PhotoRefused(f"Those photos are not all {a.name}'s.")
        rest = [d["_id"] for d in docs if d["_id"] not in set(ids)]
        now = self.now()
        for i, pid in enumerate(list(ids) + rest):
            await self.col.update_one({"_id": pid}, {"$set": {"order": i, "updated_by": user_id, "updated_at": now}})
        return await self.list_area(a.key)

    async def public(self, slug: str) -> Optional[Dict[str, Any]]:
        """The live photos of an area for its guide, with every credit field; None for an area we do not cover."""
        a = areas.BY_SLUG.get(slug or "")
        if a is None:
            return None
        docs = await self.col.find({"area": a.key, "status": "live"}).to_list(PER_AREA_MAX)
        live = sorted(docs, key=_order_key)[:PUBLIC_MAX]
        return {"area": {"key": a.key, "name": a.name, "slug": a.slug}, "photos": [public_view(d) for d in live]}
