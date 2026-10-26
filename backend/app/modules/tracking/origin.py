"""Where a visitor came from: the page they landed on, the outside site that sent them, and a source name for it."""
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse

MAX_LEN = 300

# AI assistants (docs/plan/seo-system.md 8a, step 3): referring host (or a parent domain of it), the name shown, the source key.
# Checked before the search engines below: gemini.google.com is Gemini, not Google search. seo.aivisits counts AI visits by
# the same list, so a lead and a visit from one assistant always carry the same name.
AI_REFERRERS = (
    ("chatgpt.com", "ChatGPT", "chatgpt"), ("chat.openai.com", "ChatGPT", "chatgpt"), ("perplexity.ai", "Perplexity", "perplexity"),
    ("copilot.microsoft.com", "Copilot", "copilot"), ("gemini.google.com", "Gemini", "gemini"), ("bard.google.com", "Gemini", "gemini"),
    ("claude.ai", "Claude", "claude"), ("you.com", "You.com", "you"), ("phind.com", "Phind", "phind"), ("meta.ai", "Meta AI", "meta_ai"),
    ("grok.com", "Grok", "grok"), ("chat.deepseek.com", "DeepSeek", "deepseek"),
)
# utm_source values assistants add to their links (ChatGPT adds utm_source=chatgpt.com) -> source key
AI_UTM = {"chatgpt.com": "chatgpt", "chatgpt": "chatgpt", "openai": "chatgpt", "perplexity": "perplexity", "perplexity.ai": "perplexity",
          "copilot": "copilot", "copilot.com": "copilot", "gemini": "gemini", "claude": "claude", "claude.ai": "claude"}
AI_NAMES = {key: name for _, name, key in AI_REFERRERS}
AI_SOURCES = frozenset(AI_NAMES)

# host fragment -> source name (checked in order; the first match wins)
REFERRER_SOURCES = (
    ("google.", "google"), ("bing.", "bing"), ("duckduckgo.", "duckduckgo"), ("yahoo.", "yahoo"),
    ("instagram.", "instagram"), ("facebook.", "facebook"), ("fb.", "facebook"), ("fb.me", "facebook"),
    ("whatsapp.", "whatsapp"), ("wa.me", "whatsapp"), ("youtube.", "youtube"), ("youtu.be", "youtube"),
    ("t.co", "twitter"), ("twitter.", "twitter"), ("x.com", "twitter"), ("linkedin.", "linkedin"),
    ("reddit.", "reddit"), ("chatgpt.", "chatgpt"), ("openai.", "chatgpt"), ("perplexity.", "perplexity"),
)


# in-app browsers name their app in the user agent; their links usually arrive with no referrer (2026-10-21: a hot lead showed only
# "direct" and nobody could tell Instagram from Facebook). Instagram first: its Android agent can also carry FB markers.
IN_APP = (("instagram", "instagram"), ("fban", "facebook"), ("fbav", "facebook"), ("fb_iab", "facebook"), ("fbios", "facebook"),
          ("messenger", "facebook"), ("linkedinapp", "linkedin"), ("snapchat", "snapchat"))


def app_of(user_agent: Optional[str]) -> Optional[str]:
    """The app whose built-in browser opened the page (instagram, facebook, ...), from the user agent; None for a normal browser."""
    ua = (user_agent or "").lower()
    return next((name for mark, name in IN_APP if mark in ua), None)


def clip(value: Optional[str]) -> Optional[str]:
    """Trim and cut to MAX_LEN; empty becomes None. Never rejects: a long URL must not lose the visit."""
    v = (value or "").strip()
    return v[:MAX_LEN] or None


def ai_host(host: str) -> Optional[str]:
    """The AI assistant a referring host belongs to ('gemini.google.com' -> 'gemini'), else None."""
    host = (host or "").lower()
    return next((key for h, _, key in AI_REFERRERS if host == h or host.endswith("." + h)), None)


def ai_utm(utm: Optional[Dict[str, str]]) -> Optional[str]:
    """The AI assistant a link's utm_source names ({'utm_source': 'chatgpt.com'} -> 'chatgpt'), else None."""
    return AI_UTM.get(str((utm or {}).get("utm_source") or "").strip().lower())


def referrer_source(referrer: Optional[str]) -> Optional[str]:
    """'https://www.google.com/' -> 'google'; an AI assistant -> its key ('gemini'); an unknown site -> its host; nothing -> None."""
    if not referrer:
        return None
    host = (urlparse(referrer).hostname or "").lower()
    if not host:
        return None
    ai = ai_host(host)
    if ai:
        return ai
    labels = host.split(".")
    for frag, name in REFERRER_SOURCES:
        # "google." matches any google.* host (www.google.co.in); "wa.me" matches that domain and its subdomains
        if frag.endswith(".") and frag[:-1] in labels[:-1]:
            return name
        if not frag.endswith(".") and (host == frag or host.endswith("." + frag)):
            return name
    return host[4:] if host.startswith("www.") else host


def source_key(source: Optional[str], referrer: Optional[str], utm: Optional[Dict[str, str]] = None) -> str:
    """One name to group by: a tagged link (src=) wins, then an AI assistant's utm_source (its app often sends no referrer), then
    the referring site, else 'direct' (typed, bookmarked, or an app that hides it)."""
    return (source or ai_utm(utm) or referrer_source(referrer) or "direct").lower()


async def leads_from_ai(contacts, since: datetime) -> Dict[str, int]:
    """{assistant name: leads} created since `since` that came from an AI answer, for the owner's weekly SEO note."""
    out: Dict[str, int] = {}
    async for c in contacts.find({"created_at": {"$gte": since}}, {"source": 1, "utm": 1, "first_touch": 1}):
        key = source_key(c.get("source"), (c.get("first_touch") or {}).get("referrer"), c.get("utm"))
        if key in AI_SOURCES:
            out[AI_NAMES[key]] = out.get(AI_NAMES[key], 0) + 1
    return out


def channel_of(c: dict) -> str:
    """How a lead reached us: form | chat | whatsapp | dm | comment | post_link. Stored on new leads; worked out for older ones."""
    if c.get("channel"):
        return c["channel"]
    anon = c.get("anon_ids") or []
    if c.get("interest_code"):
        return "post_link"
    if any(a.startswith("whatsapp:") for a in anon):
        return "whatsapp"
    if any("_dm:" in a for a in anon):
        return "dm"
    if c.get("source") == "chat" or any(a.startswith("chat-") for a in anon):
        return "chat"
    if (c.get("source") or "").endswith("_comment") and any(a.startswith(("facebook:", "instagram:")) for a in anon):
        return "comment"
    return "form"


def touch_fields(e) -> dict:
    """The page fields stored on every event."""
    return {"path": e.path, "landing": e.landing, "referrer": e.referrer}


def first_touch(events: list, enquiry) -> dict:
    """Where this lead first came from: the earliest event that knows its landing page, else the enquiry itself."""
    first = next((ev for ev in sorted(events, key=lambda d: d["ts"]) if ev.get("landing") or ev.get("referrer")), None)
    src = first if first else {"landing": enquiry.landing, "referrer": enquiry.referrer}
    return {"landing": src.get("landing"), "referrer": src.get("referrer"), "enquiry_page": enquiry.path}
