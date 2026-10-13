"""The standard footer of every Avasetu post: the website for Facebook, 'link in our bio' for Instagram (captions cannot hold links).
`with_footer` is pure and idempotent. The integrator applies it where captions are built; nothing here touches stored captions."""
import hashlib
import re
from typing import Optional

from app.core import brand
from app.platform.text import IG_MAX_HASHTAGS

SITE_URL = brand.SITE
FACEBOOK_FOOTER = brand.footer("facebook")
INSTAGRAM_FOOTER = brand.footer("instagram")
# footers of drafts written before the rebrand; replaced by the current footer, never kept twice
_LEGACY_FOOTER = re.compile(r"^[ \t]*PUNE Property[ \t]*·.*$", re.M)
FACEBOOK_MAX = 900     # strictly under
INSTAGRAM_MAX = 2000   # strictly under
MAX_HASHTAGS = 10        # Facebook
IG_MAX_TAGS = IG_MAX_HASHTAGS  # Instagram allows 5

_TAG = re.compile(r"#\w+")
# likers and sharers cannot be messaged through the API; the caption asks them to comment (the engage worker answers comments) and follow
# each part is left out when the caption already asks for that action (a post that says 'Comment PRICE' keeps its one comment ask)
ASK_PARTS = ((re.compile(r"\bcomment", re.I), "💬 Comment INFO for the details."),
             (re.compile(r"\bshare\b", re.I), "📤 Share with a friend who needs this."),
             (re.compile(r"\bfollow\b", re.I), "➕ Follow for daily Pune property updates."))


# Buyer posts ask ONE thing (2026-10-11, docs/plan/reach-captions.md): three asks on every post read as engagement bait, which Meta
# demotes, and bury the post's own action. A send is the strongest reach signal we can ask for; about 1 post in 4 (stable by key)
# asks for a comment instead, so the comment assistant keeps working and the two can be compared.
SEND_ASK = {"en": "📤 Send this to someone looking for a home in {place}.",
            "mr": "📤 {place} मध्ये घर शोधणाऱ्या व्यक्तीला हे पाठवा.",
            "hi": "📤 {place} में घर ढूँढ रहे किसी व्यक्ति को यह भेजें."}
COMMENT_ASK = {"en": "💬 Comment INFO for the details.", "mr": "💬 माहितीसाठी INFO कमेंट करा.", "hi": "💬 जानकारी के लिए INFO कमेंट करें."}
COMMENT_EVERY = 4
_OWN_ASK = re.compile(r"\b(comment|share|send)\b|कमेंट|पाठवा|भेजें|शेअर|शेयर", re.I)
_ACTION_LINE = re.compile(r"^\s*(👉|💬\s*WhatsApp)", re.M)   # the interest link and the WhatsApp line are actions, not asks


def ask_for(body: str, key: Optional[str] = None, place: str = "", language: str = "en") -> str:
    """The engagement ask. Without `key` (recruitment posts): the old asks, each left out when the caption already makes it.
    With `key` (buyer posts): at most one, none when the caption already asks for a comment, share or send."""
    if key is None:
        return " ".join(line for has, line in ASK_PARTS if not has.search(body or ""))
    own = "\n".join(ln for ln in (body or "").splitlines() if not _ACTION_LINE.match(ln))
    if _OWN_ASK.search(own):
        return ""
    lang = language if language in SEND_ASK else "en"
    if int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % COMMENT_EVERY == 0:
        return COMMENT_ASK[lang]
    return SEND_ASK[lang].format(place=(place or "Pune").strip())


def footer_for(channel: str) -> str:
    return INSTAGRAM_FOOTER if channel == "instagram" else FACEBOOK_FOOTER


def _limit(channel: str) -> int:
    return INSTAGRAM_MAX if channel == "instagram" else FACEBOOK_MAX


def _max_tags(channel: str) -> int:
    return IG_MAX_TAGS if channel == "instagram" else MAX_HASHTAGS


def _trim_hashtags(text: str, limit: int = MAX_HASHTAGS) -> str:
    seen = 0

    def keep(m: "re.Match") -> str:
        nonlocal seen
        seen += 1
        return m.group(0) if seen <= limit else ""

    return re.sub(r"[ \t]+\n", "\n", _TAG.sub(keep, text)).rstrip()


def _cut(body: str, room: int) -> str:
    if len(body) <= room:
        return body
    cut = body[:max(room - 1, 0)]
    nl = cut.rfind("\n")
    sp = cut.rfind(" ")
    at = nl if nl > room * 0.6 else sp if sp > room * 0.6 else -1
    return (cut[:at] if at > 0 else cut).rstrip() + "…"


def with_footer(caption: str, channel: str, key: Optional[str] = None, place: str = "", language: str = "en") -> str:
    """Caption + engagement ask + footer, once. At most 10 hashtags (5 on Instagram); Facebook stays under 900 characters and Instagram under 2000 (the body is trimmed, never the footer)."""
    foot = footer_for(channel)
    body = _LEGACY_FOOTER.sub("", caption or "").strip()
    if foot in body:
        body = body.replace(foot, "").rstrip(" \n·")
    body = _trim_hashtags(body, _max_tags(channel))
    tags = _TAG.findall(body)
    # keep the trailing hashtag block (if any) intact when trimming the prose
    block = ""
    m = re.search(r"(\n[ \t]*(?:#\w+[ \t]*)+)$", body)
    if m and len(tags) <= _max_tags(channel):
        block, body = m.group(1).rstrip(), body[:m.start()].rstrip()
    ask = ask_for(body, key, place, language) if body else ""
    ask = "\n\n" + ask if ask else ""
    room = _limit(channel) - 1 - len(foot) - len(block) - len(ask) - 2
    body = _cut(body, room)
    text = (body + ask + block).strip()
    return f"{text}\n\n{foot}" if text else foot
