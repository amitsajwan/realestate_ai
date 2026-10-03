"""What the owner sees before tapping Approve: the rendered card, the channels the item will go to, and the exact final captions, each
already run through the check stage. Pure except for reading the social settings; used by the owner router."""
import os
from typing import Callable, Dict, List, Optional

from app.platform.meta_graph import config as social_config

from . import captions


def media_url(rel: str) -> str:
    """Public address of a file under uploads/ (absolute when PUBLIC_MEDIA_BASE_URL is set, else a path on the API host)."""
    base = (os.environ.get("PUBLIC_MEDIA_BASE_URL") or "").strip().rstrip("/")
    return f"{base}/uploads/{str(rel).lstrip('/')}"


def card_view(card: Optional[dict]) -> Optional[dict]:
    if not card or not card.get("fb"):
        return None
    ig = card.get("ig")
    slides = [media_url(p) for p in (ig if isinstance(ig, list) else [ig] if ig else [])]
    return {"fb": media_url(card["fb"]), "ig": slides[0] if slides else None, "slides": slides, "variant": card.get("variant")}


def channels() -> List[dict]:
    """The channels an approved item will be published to, with what each needs. Instagram only when META_IG_BUSINESS_ID is set."""
    cfg = social_config.load()
    out = [{"id": "facebook", "label": "Facebook Page", "post": "photo post with our link"}]
    if cfg.ig_id:
        out.append({"id": "instagram", "label": "Instagram", "post": "image post, link in bio"})
    return out


async def build(doc: dict, checker: Optional[Callable]) -> Dict[str, object]:
    texts = captions.build(doc) if doc.get("draft") else {}
    live = [c["id"] for c in channels()]
    problems = await captions.verify(doc, checker) if texts else {}
    return {"captions": {k: v for k, v in texts.items() if k in live},
            "caption_problems": {k: v for k, v in problems.items() if k in live and v},
            "channels": channels(), "card": card_view(doc.get("card")), "dry_run": social_config.load().dry_run}
