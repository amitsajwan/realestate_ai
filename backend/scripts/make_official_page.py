"""Turn the owner's agent page into the official Avasetu page (run once on the server):
  docker compose exec -T -e PYTHONPATH=. backend python scripts/make_official_page.py
Slug amit-sajwan -> avasetu (the website redirects the old address), shown name 'Avasetu Homes', Avasetu logo, navy-gold preset."""
import asyncio
import os
import shutil
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

from app.core import brand
from app.core.config import settings

OLD, NEW = "amit-sajwan", "avasetu"


async def main():
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    col = db["agent_public_profiles"]
    prof = await col.find_one({"slug": OLD}) or await col.find_one({"slug": NEW})
    if not prof:
        raise SystemExit("owner profile not found")
    clash = await col.find_one({"slug": NEW, "_id": {"$ne": prof["_id"]}})
    if clash:
        raise SystemExit("slug 'avasetu' is already used by another profile")
    up = Path(os.environ.get("UPLOAD_DIRECTORY", "uploads")) / "images"
    up.mkdir(parents=True, exist_ok=True)
    src = Path("app/modules/marketing/assets/avasetu-mark.png")
    shutil.copyfile(src, up / "avasetu-official-logo.png")
    b = dict(prof.get("branding_data") or {})
    b.update({
        "business_name": "Avasetu Homes",
        "tagline": brand.TAGLINE,
        "about": "The official Avasetu page: homes, guides and trusted local agents in Pune. Homes marked Sample are illustrations only.",
        "logo": "/uploads/images/avasetu-official-logo.png",
        "preset": "navy-gold",
        "areas": ["Kharadi", "Upper Kharadi", "Wagholi"],
        "languages": ["English", "Hindi", "Marathi"],
    })
    await col.update_one({"_id": prof["_id"]}, {"$set": {
        "slug": NEW, "agent_name": "Avasetu Homes", "bio": b["about"], "branding_data": b,
        "site_config.hero.headline": "Avasetu Homes", "site_config.hero.subheadline": brand.TAGLINE,
        "previous_slugs": sorted(set((prof.get("previous_slugs") or []) + [OLD])),
    }})
    print(f"official page ready: /agent/{NEW} (was /agent/{OLD})")


asyncio.run(main())
