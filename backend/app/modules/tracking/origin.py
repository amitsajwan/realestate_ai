"""Where a visitor came from: the page they landed on, the outside site that sent them, and a source name for it."""
from typing import Optional
from urllib.parse import urlparse

MAX_LEN = 300

# host fragment -> source name (checked in order; the first match wins)
REFERRER_SOURCES = (
    ("google.", "google"), ("bing.", "bing"), ("duckduckgo.", "duckduckgo"), ("yahoo.", "yahoo"),
    ("instagram.", "instagram"), ("facebook.", "facebook"), ("fb.", "facebook"), ("fb.me", "facebook"),
    ("whatsapp.", "whatsapp"), ("wa.me", "whatsapp"), ("youtube.", "youtube"), ("youtu.be", "youtube"),
    ("t.co", "twitter"), ("twitter.", "twitter"), ("x.com", "twitter"), ("linkedin.", "linkedin"),
    ("reddit.", "reddit"), ("chatgpt.", "chatgpt"), ("openai.", "chatgpt"), ("perplexity.", "perplexity"),
)


def clip(value: Optional[str]) -> Optional[str]:
    """Trim and cut to MAX_LEN; empty becomes None. Never rejects: a long URL must not lose the visit."""
    v = (value or "").strip()
    return v[:MAX_LEN] or None


def referrer_source(referrer: Optional[str]) -> Optional[str]:
    """'https://www.google.com/' -> 'google'; an unknown site -> its host; nothing -> None."""
    if not referrer:
        return None
    host = (urlparse(referrer).hostname or "").lower()
    if not host:
        return None
    labels = host.split(".")
    for frag, name in REFERRER_SOURCES:
        # "google." matches any google.* host (www.google.co.in); "wa.me" matches that domain and its subdomains
        if frag.endswith(".") and frag[:-1] in labels[:-1]:
            return name
        if not frag.endswith(".") and (host == frag or host.endswith("." + frag)):
            return name
    return host[4:] if host.startswith("www.") else host


def touch_fields(e) -> dict:
    """The page fields stored on every event."""
    return {"path": e.path, "landing": e.landing, "referrer": e.referrer}


def first_touch(events: list, enquiry) -> dict:
    """Where this lead first came from: the earliest event that knows its landing page, else the enquiry itself."""
    first = next((ev for ev in sorted(events, key=lambda d: d["ts"]) if ev.get("landing") or ev.get("referrer")), None)
    src = first if first else {"landing": enquiry.landing, "referrer": enquiry.referrer}
    return {"landing": src.get("landing"), "referrer": src.get("referrer"), "enquiry_page": enquiry.path}
