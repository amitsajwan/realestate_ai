"""Explicit showcase publishing. Posts ONE labelled sample home to Instagram (carousel) or the Facebook Page (photo post).

This deliberately does not go through social.service (whose guard refuses to post sample listings as real ones): the images and
captions here always carry the 'Sample listing' label, and the caption is validated before anything is sent. Honours
SOCIAL_DRY_RUN (default on): a dry run renders, validates and returns the would-be post without touching the network.
Media URLs are PUBLIC_MEDIA_BASE_URL + /uploads/showcase/<slug>/<n>.jpg (facebook: facebook.jpg).
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from app.platform.meta_graph.config import SocialConfig, load as load_config
from app.modules.social.distribution import default_publisher
from app.platform.meta_graph.publisher import Post, PublishError, Publisher

from . import captions
from .render import write_home
from .samples import Home, get

UPLOAD_SUBDIR = "showcase"


class ShowcaseError(Exception):
    pass


@dataclass
class ShowcaseResult:
    slug: str
    channel: str                 # 'instagram' | 'facebook_page'
    dry_run: bool
    caption: str
    image_urls: List[str]
    external_id: Optional[str] = None
    permalink: Optional[str] = None


def uploads_dir() -> Path:
    return Path(os.environ.get("UPLOADS_DIR") or "uploads")


def media_path(slug: str, name: str) -> str:
    return f"/uploads/{UPLOAD_SUBDIR}/{slug}/{name}"


def ensure_rendered(h: Home, root: Optional[Path] = None, force: bool = False) -> Path:
    """Render the images for `h` under <uploads>/showcase/<slug>/ if they are not there yet. Returns that folder."""
    root = Path(root) if root else uploads_dir() / UPLOAD_SUBDIR
    folder = root / h.slug
    needed = [folder / f"{i}.jpg" for i in range(1, 6)] + [folder / "facebook.jpg"]
    if force or not all(p.exists() for p in needed):
        write_home(h, root, scenes=False)
    return folder


def _urls(cfg: SocialConfig, slug: str, names: List[str]) -> List[str]:
    base = cfg.media_base_url.rstrip("/")
    return [f"{base}{media_path(slug, n)}" for n in names]


def _publisher(cfg: SocialConfig, publisher: Optional[Publisher]) -> Publisher:
    if publisher is not None:
        return publisher
    return default_publisher(cfg)


async def _publish(slug: str, channel: str, names: List[str], *, cfg: Optional[SocialConfig], publisher: Optional[Publisher], llm,
                   caption: Optional[str], root: Optional[Path]) -> ShowcaseResult:
    h = get(slug)
    cfg = cfg or load_config()
    kind = "instagram" if channel == "instagram" else "facebook"
    ensure_rendered(h, root)
    text = caption if caption is not None else await captions.build_caption(h, kind, llm)
    problems = captions.validate(text, kind)
    if problems:
        raise ShowcaseError("caption refused: " + "; ".join(problems))
    urls = _urls(cfg, slug, names)
    if not cfg.dry_run:
        if not cfg.configured(channel):
            raise ShowcaseError(f"{channel} is not configured (token and id)")
        if not cfg.media_url_ok:
            raise ShowcaseError("PUBLIC_MEDIA_BASE_URL must be a public https address for a real post")
    try:
        res = await _publisher(cfg, publisher).publish(Post(channel=channel, text=text, image_urls=urls))
    except PublishError as e:
        raise ShowcaseError(str(e))
    return ShowcaseResult(slug, channel, cfg.dry_run, text, urls, res.external_id, res.permalink)


async def publish_instagram(slug: str, *, cfg: Optional[SocialConfig] = None, publisher: Optional[Publisher] = None, llm=None,
                            caption: Optional[str] = None, root: Optional[Path] = None) -> ShowcaseResult:
    """Post the 5-slide carousel for `slug` to Instagram."""
    return await _publish(slug, "instagram", [f"{i}.jpg" for i in range(1, 6)], cfg=cfg, publisher=publisher, llm=llm,
                          caption=caption, root=root)


async def publish_facebook(slug: str, *, cfg: Optional[SocialConfig] = None, publisher: Optional[Publisher] = None, llm=None,
                           caption: Optional[str] = None, root: Optional[Path] = None) -> ShowcaseResult:
    """Post the photo card for `slug` to the Facebook Page."""
    return await _publish(slug, "facebook_page", ["facebook.jpg"], cfg=cfg, publisher=publisher, llm=llm, caption=caption, root=root)


async def publish_showcase(slug: str, channel: str, **kw) -> List[ShowcaseResult]:
    """channel: instagram | facebook | both."""
    if channel not in ("instagram", "facebook", "both"):
        raise ShowcaseError("channel must be instagram, facebook or both")
    out = []
    if channel in ("instagram", "both"):
        out.append(await publish_instagram(slug, **kw))
    if channel in ("facebook", "both"):
        out.append(await publish_facebook(slug, **kw))
    return out
