"""What to review for a calendar item, a news item or a listing's marketing cards: the image files and the text context.

The builders are shared by the on-demand endpoint and the post-render warm-up hooks so both produce the same cache key.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

CARD_ORDER = ("cover", "facts", "amenities", "cta", "status")


def uploads_root() -> Path:
    return Path(os.environ.get("UPLOAD_DIRECTORY", "uploads"))


def safe_file(rel: Any, root: Optional[Path] = None) -> Optional[Path]:
    """A file under the uploads root for 'x/y.jpg' or '/uploads/x/y.jpg'; None for anything outside it or missing."""
    if not isinstance(rel, str) or not rel.strip():
        return None
    rel = rel.strip()
    if rel.startswith("/uploads/"):
        rel = rel[len("/uploads/"):]
    if rel.startswith("/") or ".." in rel.replace("\\", "/").split("/"):
        return None
    base = (root or uploads_root()).resolve()
    p = (base / rel).resolve()
    try:
        p.relative_to(base)
    except ValueError:
        return None
    return p if p.is_file() else None


def calendar_target(doc: Dict[str, Any], root: Optional[Path] = None) -> Tuple[List[Path], Dict[str, Any]]:
    images = list(doc.get("images") or ([doc["image_path"]] if doc.get("image_path") else []))
    paths = [p for p in (safe_file(i, root) for i in images) if p]
    hook = (doc.get("creative") or {}).get("hook") or ""
    return paths, {"kind": doc.get("kind", "post"), "headline": hook, "caption": doc.get("caption") or ""}


def news_target(doc: Dict[str, Any], root: Optional[Path] = None) -> Tuple[List[Path], Dict[str, Any]]:
    card = doc.get("card") or {}
    rels: List[str] = []
    ig = card.get("ig")
    rels += ig if isinstance(ig, list) else [ig] if ig else []
    if card.get("fb") and card.get("fb") not in rels:
        rels.append(card["fb"])
    paths = [p for p in (safe_file(r, root) for r in rels) if p]
    draft = doc.get("draft") or {}
    return paths, {"kind": "news", "headline": draft.get("title") or (doc.get("raw") or {}).get("title") or "",
                   "caption": draft.get("text") or ""}


def listing_target(pack: Dict[str, Any], listing: Dict[str, Any], root: Optional[Path] = None) -> Tuple[List[Path], Dict[str, Any]]:
    imgs = pack.get("images") or {}
    paths = [p for p in (safe_file((imgs.get(k) or {}).get("path"), root) for k in CARD_ORDER if k in imgs) if p]
    return paths, {"kind": "listing", "headline": pack.get("headline") or listing.get("title") or "",
                   "caption": (pack.get("instagram") or {}).get("caption") or ""}


def warm(paths: List[Path], context: Dict[str, Any]) -> None:
    """Fire-and-forget: review now so the Approve screen's chip is instant later. Only when an AI provider is configured
    (the rule review is cheap enough to run on demand). Never raises."""
    try:
        from .vision_review import default_clients, review
        if not paths or not default_clients():
            return
        loop = asyncio.get_running_loop()
        task = loop.create_task(review(paths, context))
        task.add_done_callback(lambda t: t.exception() and log.info("quality warm-up failed: %s", t.exception()))
    except Exception:
        return
