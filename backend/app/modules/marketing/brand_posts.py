"""Starter posts for the PUNE Property Page: useful, honest content (no fake listings) rendered in the same card style.

Facts stated here are general and stable (RERA registration, carpet area definitions). Nothing claims verification, reviews,
prices or properties that do not exist.
"""
from typing import Dict, List, Tuple

from PIL import Image

from .images import GOLD, MARGIN, PITCH, SOFT, SQUARE, WHITE, DARK_INK, Card, _chip, _stamp_logo, brand_background, load_font

SITE = "https://34-180-39-243.sslip.io"
TAGS = "#PunePropertyHub #PuneRealEstate #PuneProperty #HomeBuyingTips"

POSTS: List[Dict] = [
    {
        "slug": "welcome", "kicker": "WELCOME", "title": "Homes in Pune, shared clearly",
        "points": ["Price, area, possession and RERA in one place", "Simple, honest listings from local agents", "Follow this page: listings are coming"],
        "caption": (
            "\U0001F3E1 Welcome to PUNE Property\n\n"
            "We are building a simple way to find and share homes in Pune: clear price, area, possession and RERA details, "
            "posted by local agents.\n\n"
            "\U0001F4CD Follow this page for new listings and buying tips.\n"
            f"\U0001F517 {SITE}\n\n{TAGS}"),
    },
    {
        "slug": "five-checks", "kicker": "BUYING TIP", "title": "5 checks before you buy a flat in Pune",
        "points": ["RERA registration of the project", "Carpet area, not just built-up", "Title and approvals: ask a lawyer",
                   "Possession date and builder's past projects", "Full cost: stamp duty, registration, maintenance"],
        "caption": (
            "\U0001F3E1 5 checks before you buy a flat in Pune\n\n"
            "1️⃣ RERA registration of the project\n"
            "2️⃣ Carpet area, not just built-up\n"
            "3️⃣ Title and approvals: get a lawyer to check them\n"
            "4️⃣ Possession date and the builder's past projects\n"
            "5️⃣ The full cost: stamp duty, registration and maintenance, not just the price\n\n"
            "\U0001F4AC Save this for your next site visit.\n\n" + TAGS),
    },
    {
        "slug": "rera", "kicker": "KNOW YOUR RIGHTS", "title": "Check RERA before you pay a booking amount",
        "points": ["Every project above the RERA limit must be registered", "Look up the project number on the MahaRERA website",
                   "Compare the possession date with what you are told", "No RERA number in the ad? Ask for it"],
        "caption": (
            "\U0001F4CB Check RERA before you pay a booking amount\n\n"
            "▪ Projects above the RERA limits must be registered\n"
            "▪ Look up the project number on the MahaRERA website\n"
            "▪ Compare the possession date there with what you are told\n"
            "▪ No RERA number in the ad? Ask for it\n\n"
            "Every listing on PUNE Property shows the RERA number when the agent provides it.\n\n" + TAGS),
    },
    {
        "slug": "carpet-area", "kicker": "EXPLAINED", "title": "Carpet vs built-up vs super built-up",
        "points": ["Carpet: the floor area you actually use, wall to wall", "Built-up: carpet plus walls and balcony",
                   "Super built-up: built-up plus your share of common areas", "Compare flats by price per sq ft of carpet area"],
        "caption": (
            "\U0001F4D0 Carpet vs built-up vs super built-up\n\n"
            "▪ Carpet: the floor area you actually use, wall to wall\n"
            "▪ Built-up: carpet plus walls and balcony\n"
            "▪ Super built-up: built-up plus your share of common areas\n\n"
            "\U0001F4A1 Tip: compare flats by price per sq ft of CARPET area, so you compare like with like.\n\n" + TAGS),
    },
    {
        "slug": "agents", "kicker": "FOR PUNE AGENTS", "title": "Property agent in Pune? Join our pilot",
        "points": ["Your own website in minutes", "Ready-made posts for Facebook, Instagram and WhatsApp", "Buyers tracked in one simple inbox",
                   "Invite-only pilot, free to start"],
        "caption": (
            "\U0001F91D Property agent in Pune? Join our pilot\n\n"
            "✅ Your own website in minutes\n"
            "✅ Ready-made posts for Facebook, Instagram and WhatsApp\n"
            "✅ Buyers tracked in one simple inbox\n\n"
            "The pilot is invite-only and free to start. Request an invite:\n"
            f"\U0001F517 {SITE}/request-invite\n\n" + TAGS),
    },
    {
        "slug": "kharadi-choose", "kicker": "KHARADI - UPPER KHARADI - WAGHOLI", "title": "Which one suits you? Start with your commute",
        "points": ["Kharadi: closest to the big office campuses", "Upper Kharadi: newer projects, a short hop from Kharadi",
                   "Wagholi: often more space for the budget, longer commute", "Test it: travel to your office at 9 am on a weekday"],
        "caption": (
            "\U0001F4CD Kharadi, Upper Kharadi or Wagholi?\n\n"
            "\u25AA Kharadi: closest to the big office campuses\n"
            "\u25AA Upper Kharadi: newer projects, a short hop from Kharadi\n"
            "\u25AA Wagholi: often more space for the budget, but a longer commute\n\n"
            "\U0001F697 The real test: travel from the flat to your office at 9 am and 6:30 pm on a weekday.\n\n"
            f"\U0001F4D6 Read the full guide: {SITE}/insights/kharadi-upper-kharadi-wagholi\n\n"
            "#Kharadi #UpperKharadi #Wagholi " + TAGS),
    },
    {
        "slug": "kharadi-metro", "kicker": "METRO", "title": "Metro near Kharadi and Wagholi: approved is not running",
        "points": ["Ramwadi to Wagholi (Corridor 2B) is approved", "Kharadi to Khadakwasla (Line 4) is approved",
                   "Approved lines take years to build", "Do not pay extra for a metro that is not running yet"],
        "caption": (
            "\U0001F687 Metro near Kharadi and Wagholi: approved is not the same as running\n\n"
            "\u2705 Ramwadi to Wagholi/Vitthalwadi (Corridor 2B): approved by the Union Cabinet\n"
            "\u2705 Kharadi to Khadakwasla (Line 4): approved by the Union Cabinet\n\n"
            "\u26A0\uFE0F Approved lines take years to build. Do not pay extra today for a metro that is not yet running, and check the latest "
            "status on the official Maha-Metro website.\n\n"
            f"\U0001F4D6 Sources and details: {SITE}/insights/metro-kharadi-wagholi-approved-not-running\n\n"
            "#PuneMetro #Kharadi #Wagholi " + TAGS),
    },
    {
        "slug": "kharadi-site-visit", "kicker": "SITE VISIT CHECKLIST", "title": "Visiting a flat in Upper Kharadi or Wagholi? Check these 6",
        "points": ["Go at 9 am and again at 6:30 pm on a weekday", "Ask where the water comes from", "Ask what the power backup covers",
                   "Look at the road outside, ideally after rain", "Ask about parking and maintenance charges",
                   "Visit a finished project by the same builder"],
        "caption": (
            "\U0001F4CB Site visit checklist for Upper Kharadi and Wagholi\n\n"
            "1\uFE0F\u20E3 Go at 9 am and again at 6:30 pm on a weekday\n"
            "2\uFE0F\u20E3 Ask where the water comes from\n"
            "3\uFE0F\u20E3 Ask what the power backup covers\n"
            "4\uFE0F\u20E3 Look at the road outside, ideally after rain\n"
            "5\uFE0F\u20E3 Ask about parking and maintenance charges\n"
            "6\uFE0F\u20E3 Visit a finished project by the same builder\n\n"
            f"\U0001F4D6 The full checklist: {SITE}/insights/site-visit-checklist-upper-kharadi-wagholi\n\n"
            "#UpperKharadi #Wagholi #SiteVisit " + TAGS),
    },
]


def render_brand_post(kicker: str, title: str, points: List[str]) -> Card:
    """A 1080x1080 card: kicker chip, bold title, numbered/ticked points, brand footer. All text stays in the safe margins."""
    size = SQUARE
    c = Card(size, brand_background(size, "pune-property", floor=1.0, tall=0.2))
    _, y = _chip(c, kicker, c.left, c.top)
    y += 34
    y = c.block(title, y, 68, WHITE, 3, 42, weight="bold") + 26
    footer_h = 110
    avail = c.bottom - footer_h - y
    for sz in (40, 36, 32, 28):
        need = sum(c.height_of(p, sz, 2, 24, x=c.left + 64, weight="medium") + 20 for p in points)
        if need <= avail:
            break
    for i, p in enumerate(points):
        cy = y + int(sz * PITCH) // 2 + 4
        c.draw.ellipse((c.left, cy - 21, c.left + 42, cy + 21), fill=GOLD)
        c.draw.text((c.left + 21, cy), str(i + 1), font=load_font(26, "bold"), fill=DARK_INK, anchor="mm")
        y = c.block(p, y, sz, WHITE, 2, 24, x=c.left + 64, weight="medium") + 20
    _stamp_logo(c, c.left, c.bottom - 88, 88)
    c.block("PUNE Property", c.bottom - 88, 34, GOLD, 1, 20, x=c.left + 108, weight="semibold")
    c.block("Find. Compare. Decide.", c.bottom - 88 + int(34 * PITCH), 26, SOFT, 1, 18, x=c.left + 108, weight="medium")
    return c
