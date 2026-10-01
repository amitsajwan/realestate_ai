"""Create (or refresh) the fictional demo agent 'Avasetu Demo Homes' at /agent/demo, with the 9 showcase sample homes.

  cd backend && PYTHONPATH=. python scripts/create_demo_agent.py                 # uses MONGODB_URL / DATABASE_NAME like the app
  cd backend && PYTHONPATH=. python scripts/create_demo_agent.py --dry-run       # print what it would do, write nothing

Idempotent: run it again any time. It reuses the same user, profile, image files and listing ids, rewrites them to the
current definition, and restarts the listings' "still available?" clock (live listings hide after 45 days unconfirmed, so
re-run it at least monthly, or from a monthly cron).

What it creates, and what it never does:
- A login user with the placeholder phone +910000000000. That is not a valid Indian mobile (sign-in rejects it), so no OTP,
  SMS or WhatsApp can ever reach anyone; the user is also marked inactive, so no token for it is accepted.
- The public profile, slug 'demo' (a reserved slug, so no real agent can ever be given it), with NO phone number, e-mail or
  RERA number, and branding_data.demo = true: the owner-only flag that makes the site show a DEMO ribbon and note.
  Agents cannot set it (PATCH /join/site ignores it).
- A monogram logo and a banner, drawn with Pillow from the bundled Poppins font and a showcase photo, saved under
  uploads/images/ exactly where the upload route stores files, and referenced as /uploads/images/<file>.
- The 9 showcase sample homes (app/modules/showcase/samples.py) as LIVE listings with their photos, labelled exactly like
  scripts/seed_samples.py: the title starts with "Sample:" and the description opens "SAMPLE LISTING ... not available for sale".
  Sample listings are never shown in the locality pages' real-listing feed.
"""
import argparse
import asyncio
import hashlib
import io
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.listings.schemas import ListingCreate  # noqa: E402
from app.modules.listings.service import compute_fingerprint  # noqa: E402
from app.modules.onboarding import branding as bd  # noqa: E402
from app.modules.onboarding.schemas import SiteUpdate  # noqa: E402
from app.modules.onboarding.service import placeholder_email  # noqa: E402
from app.modules.showcase import samples  # noqa: E402

DEMO_SLUG = "demo"
DEMO_PHONE = "+910000000000"  # not a valid Indian mobile: cannot sign in, cannot receive anything
DEMO_NAME = "Avasetu Demo Homes"
PRESET = "emerald"
BRANDING = {
    "business_name": DEMO_NAME,
    "tagline": "Kharadi and Wagholi homes, explained clearly",
    "about": ("This is a fictional agent created to show what an agent page on Avasetu looks like. "
              "The homes here are labelled samples with stock photos and are not for sale."),
    "preset": PRESET,
    "areas": ["Kharadi", "Upper Kharadi", "Wagholi"],
    "languages": ["English", "Hindi", "Marathi"],
}
LOGO_FILE = "demo-agent-logo.png"
BANNER_FILE = "demo-agent-banner.jpg"
BANNER_PHOTO = "uRUOLhYJF75w.jpg"  # Kharadi exterior (Unsplash, credited in docs/brand/photo-credits.md)
FONT = BACKEND / "app" / "modules" / "marketing" / "fonts" / "Poppins-Bold.ttf"
ID_NAMESPACE = uuid.UUID("6f1c2d8e-5a51-4c1e-9a3e-0d3e5d4a7c11")

FURNISHING = {"Semi-furnished": "semi", "Furnished": "furnished", "Unfurnished": "unfurnished"}


def listing_id(home_slug: str) -> str:
    """Stable id per sample home, so a re-run updates instead of duplicating."""
    return uuid.uuid5(ID_NAMESPACE, "demo-agent/" + home_slug).hex


# ---- images ------------------------------------------------------------------------------------------------
def _hex(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def draw_logo(size: int = 512) -> bytes:
    """'AD' monogram: gold letters on the emerald preset, a thin gold ring inside a rounded square."""
    from PIL import Image, ImageDraw, ImageFont

    p = bd.PRESETS[PRESET]
    scale = 4  # draw big, then downsample for smooth edges
    s = size * scale
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.22), fill=_hex(p["primary"]))
    inset = int(s * 0.075)
    d.rounded_rectangle((inset, inset, s - 1 - inset, s - 1 - inset), radius=int(s * 0.17), outline=_hex(p["accent"]), width=int(s * 0.018))
    font = ImageFont.truetype(str(FONT), int(s * 0.40))
    box = d.textbbox((0, 0), "AD", font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((s - w) / 2 - box[0], (s - h) / 2 - box[1]), "AD", font=font, fill=_hex(p["accent"]))
    im = im.resize((size, size), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return out.getvalue()


def draw_banner(photo: Path, width: int = 1600, height: int = 600) -> bytes:
    """A showcase photo, cover-cropped, with an emerald gradient from the left so text on top stays readable."""
    from PIL import Image, ImageOps

    p = bd.PRESETS[PRESET]
    with Image.open(photo) as src:
        im = ImageOps.fit(ImageOps.exif_transpose(src).convert("RGB"), (width, height), Image.LANCZOS, centering=(0.5, 0.4))
    shade = Image.new("RGB", (width, height), _hex(p["secondary"]))
    mask = Image.linear_gradient("L").rotate(-90).resize((width, height))  # 255 at the left -> 0 at the right
    mask = mask.point(lambda v: int(40 + v * 0.62))
    im = Image.composite(shade, im, mask)
    out = io.BytesIO()
    im.save(out, "JPEG", quality=84, optimize=True, progressive=True)
    return out.getvalue()


def _write_if_changed(path: Path, data: bytes) -> bool:
    if path.is_file() and hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(data).digest():
        return False
    path.write_bytes(data)
    return True


# ---- listings ------------------------------------------------------------------------------------------------
def listing_body(home: "samples.Home", media: list) -> dict:
    """The seed_samples.py body (same "Sample:" title and SAMPLE LISTING description) for one showcase home, validated."""
    from scripts.seed_samples import body

    b = body(dict(
        locality=home.locality, bhk=home.bhk, carpet_sqft=home.carpet_sqft, price_inr=home.price_inr, floor=home.floor,
        total_floors=home.total_floors, furnishing=FURNISHING.get(home.furnishing, "unfurnished"),
        possession="ready" if home.ready else home.possession,
        amenities=[samples.ICON_LABELS[a] for a in home.amenities],
    ))
    if not home.ready:
        b["title"] += " (under construction)"
    b["media"] = media
    return ListingCreate(**b).model_dump()


async def create_demo_agent(db, users, uploads_dir: Path, now: Callable[[], datetime] = datetime.utcnow,
                            log: Callable[[str], None] = print) -> dict:
    """Create or refresh the demo agent. `users` is a UserStore (get_by_phone/create) with an optional deactivate(user)."""
    profiles = db.get_collection("agent_public_profiles")
    listings = db.get_collection("listings")
    images = Path(uploads_dir) / "images"
    images.mkdir(parents=True, exist_ok=True)

    # 1. user (placeholder phone, inactive)
    user = await users.get_by_phone(DEMO_PHONE)
    if user is None:
        user = await users.create(DEMO_PHONE)
        log(f"user created: {user.id}")
    if hasattr(users, "deactivate"):
        await users.deactivate(user)
    uid = str(user.id)

    existing = await profiles.find_one({"slug": DEMO_SLUG})
    if existing and existing.get("user_id") != uid:
        raise SystemExit(f"slug '{DEMO_SLUG}' belongs to another user ({existing.get('user_id')}); not touching it")

    # 2. images, under uploads/images like the upload route
    for name, data in ((LOGO_FILE, draw_logo()), (BANNER_FILE, draw_banner(samples.PHOTO_DIR / BANNER_PHOTO))):
        if _write_if_changed(images / name, data):
            log(f"wrote uploads/images/{name}")

    # 3. profile: brand fields go through the same validators agents' input does; demo is set here only
    clean = SiteUpdate(**BRANDING, logo=f"/uploads/images/{LOGO_FILE}", banner=f"/uploads/images/{BANNER_FILE}")
    colors = bd.theme_for(PRESET, None)
    branding = {
        "business_name": clean.business_name, "tagline": clean.tagline, "about": clean.about, "preset": clean.preset,
        "areas": clean.areas, "languages": clean.languages, "logo": clean.logo, "banner": clean.banner,
        "colors": colors, "demo": True,
    }
    t = now()
    fields = {
        "agent_name": DEMO_NAME, "slug": DEMO_SLUG, "bio": clean.about, "photo": "", "phone": "", "email": "",
        "office_address": "Pune", "specialties": ["Sample homes"], "experience": "", "languages": clean.languages,
        "is_active": True, "is_public": True, "branding_data": branding,
        "site_config": {"theme": colors, "hero": {"headline": DEMO_NAME, "subheadline": clean.tagline},
                        "sections": ["about", "listings", "contact"], "languages": clean.languages, "city": "Pune"},
        "updated_at": t,
    }
    if existing:
        await profiles.update_one({"_id": existing["_id"]}, {"$set": fields})
        log("profile updated: /agent/" + DEMO_SLUG)
    else:
        await profiles.insert_one({"_id": uid, "id": uid, "user_id": uid, "agent_id": uid, "view_count": 0,
                                   "contact_count": 0, "created_at": t, **fields})
        log("profile created: /agent/" + DEMO_SLUG)
    if hasattr(users, "mark_onboarded"):
        await users.mark_onboarded(user, DEMO_NAME)

    # 4. the 9 showcase homes as live, labelled sample listings with their photos
    created = updated = 0
    for home in samples.HOMES:
        lid = listing_id(home.slug)
        media = []
        for i, photo in enumerate(home.photos):
            name = f"demo-{home.slug}-{i + 1}.jpg"
            if not (images / name).is_file():
                from scripts.seed_samples import jpeg_bytes
                (images / name).write_bytes(jpeg_bytes(photo.path))
            media.append({"url": f"/uploads/images/{name}", "kind": "image", "order": i})
        doc = listing_body(home, media)
        doc.update({"status": "live", "agent_id": uid, "sample_key": home.slug, "updated_at": t, "published_at": t,
                    "freshness_confirmed_at": t, "fingerprint": compute_fingerprint(doc)})
        if await listings.find_one({"_id": lid}):
            await listings.update_one({"_id": lid}, {"$set": doc})
            updated += 1
        else:
            await listings.insert_one({"_id": lid, "id": lid, "created_at": t, **doc})
            created += 1
    log(f"sample listings: {created} created, {updated} refreshed")
    return {"user_id": uid, "slug": DEMO_SLUG, "listings": [listing_id(h.slug) for h in samples.HOMES],
            "created": created, "updated": updated}


class DemoUserStore:
    """Beanie users for the demo: the existing phone-login helper (BeanieUserStore) plus deactivate()."""

    def __init__(self):
        from app.modules.onboarding.service import BeanieUserStore
        self.inner = BeanieUserStore()

    async def get_by_phone(self, phone):
        return await self.inner.get_by_phone(phone)

    async def create(self, phone):
        user = await self.inner.create(phone)
        assert user.email == placeholder_email(phone)
        return user

    async def deactivate(self, user):
        if getattr(user, "is_active", False):
            user.is_active = False
            user.updated_at = datetime.utcnow()
            await user.save()

    async def mark_onboarded(self, user, name):
        await self.inner.mark_onboarded(user, name)


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uploads", default="uploads", help="uploads folder (default: ./uploads, the upload route's folder)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        print(f"would create/refresh /agent/{DEMO_SLUG} ({DEMO_NAME}), {len(samples.HOMES)} sample listings, "
              f"images in {Path(a.uploads) / 'images'}")
        for h in samples.HOMES:
            print("  ", listing_id(h.slug), listing_body(h, [])["title"])
        return
    from beanie import init_beanie
    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import settings
    from app.models.user import User

    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    await init_beanie(database=db, document_models=[User])
    out = await create_demo_agent(db, DemoUserStore(), Path(a.uploads))
    print(f"done: /agent/{out['slug']} (user {out['user_id']})")


if __name__ == "__main__":
    asyncio.run(_main())
