"""The platform brand: one source of truth for the name, tagline, sign-off, hashtag and public site.

Avasetu (आवासेतु: aavaas = home + setu = bridge). Colours: navy #102340, gold #F0B13B. Guide: docs/brand/avasetu/README.md.
Pune is the first city; area copy ('homes in Pune', 'Kharadi, Wagholi') is not the brand and stays where it is.
SITE comes from PUBLIC_SITE_URL so the move to a real domain is one setting.
"""
import os
import re
from pathlib import Path
from typing import Optional

NAME = "Avasetu"
NAME_DEVANAGARI = "आवासेतु"
TAGLINE = "Your bridge to the right home"
TAGLINE_HI = "सही घर तक आपका सेतु"
TAGLINE_MR = "योग्य घरापर्यंत तुमचा सेतू"
TEAM = "Avasetu team"
HASHTAG = "#Avasetu"
NAVY = "#102340"
GOLD = "#F0B13B"

DEFAULT_SITE = "https://avasetu.in"
SITE = (os.environ.get("PUBLIC_SITE_URL") or DEFAULT_SITE).rstrip("/")

# Social profiles: the owner renames the Page and the Instagram handle by hand, so the URLs stay settings.
FACEBOOK_URL = os.environ.get("NEXT_PUBLIC_FACEBOOK_URL") or ""
INSTAGRAM_URL = os.environ.get("NEXT_PUBLIC_INSTAGRAM_URL") or ""

# Rendered from docs/brand/avasetu/mark.svg (gold disc, navy roof and bridge) and mark-navy.svg (navy tile, gold strokes).
ASSETS = Path(__file__).resolve().parent.parent / "modules" / "marketing" / "assets"
MARK_PNG = ASSETS / "avasetu-mark.png"
MARK_NAVY_PNG = ASSETS / "avasetu-mark-navy.png"


def site() -> str:
    """PUBLIC_SITE_URL read now (tests and long-running workers may set it after import)."""
    return (os.environ.get("PUBLIC_SITE_URL") or DEFAULT_SITE).rstrip("/")


# our guide pages, by the calendar slug of the posts about them (posts, footers and the chat bots link the same page)
TOPIC_PAGES = (("mhada", "/guides/mhada-pune-lottery"), ("upper-kharadi", "/guides/upper-kharadi"))


def topic_page(slug: str) -> str:
    """The guide page a post is about, by its calendar slug ('upper-kharadi-names-en-20261019' -> https://.../guides/upper-kharadi); ''."""
    for prefix, path in TOPIC_PAGES:
        if (slug or "").startswith(prefix):
            return site() + path
    return ""


def footer(channel: str) -> str:
    """'Avasetu · <site>' for Facebook, 'Avasetu · link in our bio' for Instagram (captions cannot hold links)."""
    return f"{NAME} · link in our bio" if channel == "instagram" else f"{NAME} · {SITE}"


WA_MARK = "\U0001F4AC"   # the speech bubble that starts the WhatsApp line of a caption (calendar.adapters finds it)


def posts_whatsapp_number() -> Optional[str]:
    """The WhatsApp number public posts show, as wa.me digits: WHATSAPP_PUBLIC_NUMBER only (never the website chat's
    NEXT_PUBLIC_WHATSAPP_NUMBER, which may be a test number that answers only allowed phones). None: posts carry only the
    tracked link."""
    d = re.sub(r"\D", "", os.environ.get("WHATSAPP_PUBLIC_NUMBER") or "")
    if re.fullmatch(r"[6-9]\d{9}", d):
        d = "91" + d
    return d if 11 <= len(d) <= 15 else None
