"""Fill House Deal's About, team and footer details on /agent/house-deal from what house-deal.com publishes.

  cd backend && PYTHONPATH=. python scripts/house_deal_about.py              # in the backend container on the VM
  cd backend && PYTHONPATH=. python scripts/house_deal_about.py --dry-run    # print what it would set, write nothing

Idempotent: run it again any time. It downloads the three team photos and House Deal's own hero banner (the "Welcome to House
Deal" RTC Silver picture, a wide copy and a tall one for phones) from house-deal.com, saves them as JPEGs under
uploads/images/hd-*.jpg (where the upload route keeps files), and sets only the keys below on the profile;
everything else in branding_data stays. office_phone is the office line +91 74472 12121 (owner, 2026-10-30): the site shows it
(show_phone prints it while the site-wide call buttons stay off) and enquiries go to it on WhatsApp from our number. The
profile phone stays +919921993099, Sharad's login: 7447212121 is the phone of their retired login, so as the profile phone it
would mark House Deal as retired.
Taken from house-deal.com on 2026-10-30; the owner confirmed the team. The RERA agent number is shown as stated by House Deal.
"""
import argparse
import asyncio
import io
import sys
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

SLUG = "house-deal"
SRC = "https://house-deal.com/wp-content/uploads/"
IMAGES = {
    "hd-team-mohini.jpg": SRC + "2016/02/agent-mohini.png",
    "hd-team-sarika.jpg": SRC + "2026/08/agent-tejasgree.png",  # their file name; the site shows it as Sarika Kotwal
    "hd-team-omkar.jpg": SRC + "2026/08/agent-omkar.png",
}
SIZE = 480
# their hero slideshow (house-deal.com home page, 2026-10-30): the East Pune / RTC Silver slide. The words are part of the picture,
# so the site shows it whole (banner_words). The phone copy loses its bottom 105 px, where the picture generator's sparkle sits.
BANNERS = {
    "hd-banner.jpg": (SRC + "2026/10/House-Deal_-Pune-Metro-Cityscape.png", 0),
    "hd-banner-phone.jpg": (SRC + "2026/10/house-deal-mobile-view.png", 105),
}

ABOUT = (
    "House Deal is a property advisory office at RTC Silver, Upper Kharadi. We help buyers choose new projects in Upper "
    "Kharadi, Kharadi and Wagholi, from the first shortlist to the day you get the keys.\n\n"
    "We work with the builders of the projects we list, take you on site visits, and help with the home loan and the "
    "paperwork. Every project on this page shows what MahaRERA says today, next to the builder's own plan."
)
TEAM = [
    {"name": "Mohini Bharate", "role": "Team Lead", "photo": "/uploads/images/hd-team-mohini.jpg",
     "about": "Leads the sales team and is your first contact for any project."},
    {"name": "Sarika Kotwal", "role": "Pre-sales Executive", "photo": "/uploads/images/hd-team-sarika.jpg",
     "about": "Understands what you need and lines up the right projects and site visits."},
    {"name": "Omkar Palekar", "role": "Pre-sales Executive", "photo": "/uploads/images/hd-team-omkar.jpg",
     "about": "Understands what you need and lines up the right projects and site visits."},
]
SETS = {
    "email": "housedealofficial@gmail.com",
    "bio": ABOUT,
    "branding_data.about": ABOUT,
    "branding_data.rera_agent_no": "A031262502865",
    "branding_data.tagline": "Your Dream Home, Our Best Deal",
    "branding_data.banner": "/uploads/images/hd-banner.jpg",
    "branding_data.banner_mobile": "/uploads/images/hd-banner-phone.jpg",
    "branding_data.banner_words": True,
    "branding_data.banner_alt": (
        "Welcome to House Deal. Your dream home, our best deal. Premium properties in East Pune: better connectivity, "
        "growing opportunities, a brighter future. The House Deal office at RTC Silver, by the Pune Metro."
    ),
    "branding_data.services": [
        "Shortlist projects for your budget", "Site visits with our team", "Home loan help",
        "Agreement and registration paperwork", "Advice for investors", "MahaRERA check on every project",
    ],
    "branding_data.areas": ["Upper Kharadi", "Kharadi", "Wagholi", "Mundhwa", "Hadapsar", "Keshav Nagar"],
    "branding_data.team": TEAM,
    "branding_data.show_phone": True,
    "branding_data.office_phone": "+917447212121",
    "branding_data.website": "https://house-deal.com",
    "branding_data.social": {
        "instagram": "housedeal_official",
        "facebook": "https://www.facebook.com/people/House-Deal/61581766839967/",
        "youtube": "https://www.youtube.com/@HouseDealOfficial",
        "linkedin": "https://www.linkedin.com/company/housedeal",
        "x": "https://x.com/HouseDealPune",
    },
}


def square_jpeg(data: bytes) -> bytes:
    """Centre-crop to a square from the top (faces sit high in these portraits) and shrink to SIZE px."""
    from PIL import Image

    im = Image.open(io.BytesIO(data)).convert("RGB")
    side = min(im.size)
    left = (im.width - side) // 2
    im = im.crop((left, 0, left + side, side)).resize((SIZE, SIZE), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "JPEG", quality=85, optimize=True)
    return out.getvalue()


def banner_jpeg(data: bytes, cut_bottom: int) -> bytes:
    """The banner at full size as a JPEG, less `cut_bottom` px off the bottom edge."""
    from PIL import Image

    im = Image.open(io.BytesIO(data)).convert("RGB")
    if cut_bottom:
        im = im.crop((0, 0, im.width, im.height - cut_bottom))
    out = io.BytesIO()
    im.save(out, "JPEG", quality=84, optimize=True, progressive=True)
    return out.getvalue()


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uploads", default="uploads", help="uploads folder (default: ./uploads, the upload route's folder)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        for k, v in SETS.items():
            print(f"{k} = {v!r}")
        for name, url in IMAGES.items():
            print(f"{url} -> {Path(a.uploads) / 'images' / name}")
        for name, (url, _) in BANNERS.items():
            print(f"{url} -> {Path(a.uploads) / 'images' / name}")
        return

    images = Path(a.uploads) / "images"
    images.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as http:
        for name, url in IMAGES.items():
            r = await http.get(url)
            r.raise_for_status()
            (images / name).write_bytes(square_jpeg(r.content))
            print(f"wrote {images / name}")
        for name, (url, cut) in BANNERS.items():
            r = await http.get(url)
            r.raise_for_status()
            (images / name).write_bytes(banner_jpeg(r.content, cut))
            print(f"wrote {images / name}")

    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import settings

    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    res = await db.agent_public_profiles.update_one({"slug": SLUG}, {"$set": SETS})
    if not res.matched_count:
        raise SystemExit(f"no profile with slug {SLUG}")
    print(f"updated /agent/{SLUG} (modified={res.modified_count})")


if __name__ == "__main__":
    asyncio.run(_main())
