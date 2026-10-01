"""The platform brand: one source of truth for the name, tagline, sign-off, hashtag and public site.

Avasetu (आवासेतु: aavaas = home + setu = bridge). Colours: navy #102340, gold #F0B13B. Guide: docs/brand/avasetu/README.md.
Pune is the first city; area copy ('homes in Pune', 'Kharadi, Wagholi') is not the brand and stays where it is.
SITE comes from PUBLIC_SITE_URL so the move to a real domain is one setting.
"""
import os
from pathlib import Path

NAME = "Avasetu"
NAME_DEVANAGARI = "आवासेतु"
TAGLINE = "Your bridge to the right home"
TAGLINE_HI = "सही घर तक आपका सेतु"
TAGLINE_MR = "योग्य घरापर्यंत तुमचा सेतू"
TEAM = "Avasetu team"
HASHTAG = "#Avasetu"
NAVY = "#102340"
GOLD = "#F0B13B"

DEFAULT_SITE = "https://34-180-39-243.sslip.io"
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


def footer(channel: str) -> str:
    """'Avasetu · <site>' for Facebook, 'Avasetu · link in our bio' for Instagram (captions cannot hold links)."""
    return f"{NAME} · link in our bio" if channel == "instagram" else f"{NAME} · {SITE}"
