"""Post clearly labelled SAMPLE listings to the Facebook Page, as illustrations of how a listing looks on Avasetu.

  python scripts/post_samples.py preview                  show what would be posted (no network writes)
  python scripts/post_samples.py post [--only N ...]      publish (default: one per area)

This is a deliberate, explicit exception to the server rule that sample listings cannot be posted through the normal approve-and-consent flow.
Every post starts with a SAMPLE LISTING line and the card carries a SAMPLE LISTING chip. Nothing is stored in `publications`.
Run on the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/post_samples.py post
"""
import argparse
import asyncio
from dataclasses import replace
from pathlib import Path

from app.core import database as dbmod
from app.core.config import settings
from app.modules.marketing.service import MarketingService
from app.modules.social.config import load
from app.modules.social.graph import GraphPublisher
from app.modules.social.publisher import Post
from app.modules.social.service import build_payload

AGENT_SLUG = "avasetu"
PICKS = [("Kharadi", 3), ("Upper Kharadi", 2), ("Wagholi", 2)]


async def main(mode: str) -> None:
    await dbmod.init_database()
    db = dbmod.get_database()
    profile = await db.get_collection("agent_public_profiles").find_one({"slug": AGENT_SLUG})
    listings = await db.get_collection("listings").find({"agent_id": profile["agent_id"], "status": "live"}).to_list(100)
    cfg = replace(load(), dry_run=False)
    svc = MarketingService(db, Path(settings.upload_directory), settings.public_site_url)
    pub = GraphPublisher(cfg)
    for locality, bhk in PICKS:
        pick = next((l for l in listings if (l.get("title") or "").startswith("Sample:") and l.get("locality") == locality and l.get("bhk") == bhk), None)
        if not pick:
            print(f"no sample listing for {bhk} BHK {locality}")
            continue
        await svc.generate(profile["agent_id"], pick["_id"], "en", settings.public_site_url + "/")
        pack = await db.get_collection("marketing_packs").find_one({"_id": pick["_id"]})
        payload = build_payload(pack, "facebook_page", cfg.media_base_url)
        assert payload["text"].startswith("SAMPLE LISTING"), "refusing to post a sample without its label"
        print(f"--- {pick['title']} | image: {payload['image_urls'][:1]}\n{payload['text'][:220]}...")
        if mode == "post":
            res = await pub.publish(Post("facebook_page", payload["text"], payload["image_urls"], payload["link"]))
            print("POSTED:", res.permalink or res.external_id)
            await asyncio.sleep(3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preview", "post"])
    asyncio.run(main(ap.parse_args().mode))
