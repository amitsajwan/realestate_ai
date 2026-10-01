"""The standard footer of every Avasetu post: the website for Facebook, 'link in our bio' for Instagram (captions cannot hold links).
`with_footer` is pure and idempotent. The integrator applies it where captions are built; nothing here touches stored captions."""
from app.core import brand
import re

SITE_URL = brand.SITE
FACEBOOK_FOOTER = brand.footer("facebook")
INSTAGRAM_FOOTER = brand.footer("instagram")
# footers of drafts written before the rebrand; replaced by the current footer, never kept twice
_LEGACY_FOOTER = re.compile(r"^[ \t]*PUNE Property[ \t]*·.*$", re.M)
FACEBOOK_MAX = 900     # strictly under
INSTAGRAM_MAX = 2000   # strictly under
MAX_HASHTAGS = 10

_TAG = re.compile(r"#\w+")


def footer_for(channel: str) -> str:
    return INSTAGRAM_FOOTER if channel == "instagram" else FACEBOOK_FOOTER


def _limit(channel: str) -> int:
    return INSTAGRAM_MAX if channel == "instagram" else FACEBOOK_MAX


def _trim_hashtags(text: str) -> str:
    seen = 0

    def keep(m: "re.Match") -> str:
        nonlocal seen
        seen += 1
        return m.group(0) if seen <= MAX_HASHTAGS else ""

    return re.sub(r"[ \t]+\n", "\n", _TAG.sub(keep, text)).rstrip()


def _cut(body: str, room: int) -> str:
    if len(body) <= room:
        return body
    cut = body[:max(room - 1, 0)]
    nl = cut.rfind("\n")
    sp = cut.rfind(" ")
    at = nl if nl > room * 0.6 else sp if sp > room * 0.6 else -1
    return (cut[:at] if at > 0 else cut).rstrip() + "…"


def with_footer(caption: str, channel: str) -> str:
    """Caption + footer, once. At most 10 hashtags; Facebook stays under 900 characters and Instagram under 2000 (the body is trimmed, never the footer)."""
    foot = footer_for(channel)
    body = _LEGACY_FOOTER.sub("", caption or "").strip()
    if foot in body:
        body = body.replace(foot, "").rstrip(" \n·")
    body = _trim_hashtags(body)
    tags = _TAG.findall(body)
    # keep the trailing hashtag block (if any) intact when trimming the prose
    block = ""
    m = re.search(r"(\n[ \t]*(?:#\w+[ \t]*)+)$", body)
    if m and len(tags) <= MAX_HASHTAGS:
        block, body = m.group(1).rstrip(), body[:m.start()].rstrip()
    room = _limit(channel) - 1 - len(foot) - len(block) - 2
    body = _cut(body, room)
    text = (body + block).strip()
    return f"{text}\n\n{foot}" if text else foot
