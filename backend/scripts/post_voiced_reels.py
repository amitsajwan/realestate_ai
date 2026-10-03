"""Publish the voiced sample reels (made by make_voiced_reels.py) to Instagram and the Facebook Page.
  docker compose exec -T -e PYTHONPATH=. backend python scripts/post_voiced_reels.py [--dry-run]
Hindi home + Hindi tip go to both channels; the English home goes to Facebook only (no duplicate home on Instagram)."""
import asyncio
import os
import sys
from dataclasses import replace
from pathlib import Path

from app.core import brand
from app.modules.social import reel_publish as publish
from app.platform.meta_graph.config import load

UP = Path(os.environ.get("UPLOAD_DIRECTORY", "uploads"))
SITE = brand.SITE
TAGS_HOME = "#Kharadi #PuneRealEstate #2BHK #PuneHomes " + brand.HASHTAG + " #HindiReels"
TAGS_TIP = "#PuneRealEstate #HomeBuyingTips #SiteVisit #Kharadi #Wagholi " + brand.HASHTAG

HOME_HI = ("Kharadi mein 2BHK? \U0001F3E1 Dekhiye asal mein kya milta hai.\n\n"
           "780 sq ft carpet · Floor 7 of 22 · Ready to move\nParking, gym, lift, security, power backup\n\n"
           "Yeh ek SAMPLE HOME hai (illustrative, not for sale). Aapke liye asli ghar ke liye 'I am interested' dabaiye.")
TIP_HI = ("Flat book karne se pehle ye 3 sawaal zaroor poochhiye \U0001F4A7⚡\n\n"
          "1️⃣ Paani kahan se aata hai: municipal, tanker ya borewell?\n2️⃣ Building mein storage kitna hai?\n"
          "3️⃣ Power backup sirf lift ka hai ya aapke flat ka bhi?\n\nSave karein aur follow karein \U0001F4BE")
HOME_EN = ("2BHK in Kharadi: what do you actually get? \U0001F3E1\n\n780 sq ft carpet · Floor 7 of 22 · Ready to move\n"
           "Parking, gym, lift, security, power backup\n\nThis is a SAMPLE HOME (illustrative, not for sale). Tell us what you want and we will find a real one.")

JOBS = [
    ("voiced-kharadi-2bhk-hi.mp4", "instagram", f"{HOME_HI}\n\nLink in our bio \U0001F446\n\n{TAGS_HOME}"),
    ("voiced-kharadi-2bhk-hi.mp4", "facebook_page", f"{HOME_HI}\n\n\U0001F449 {SITE}/go\n\n{TAGS_HOME}"),
    ("voiced-tip-water-power-hi.mp4", "instagram", f"{TIP_HI}\n\n{TAGS_TIP}"),
    ("voiced-tip-water-power-hi.mp4", "facebook_page", f"{TIP_HI}\n\nMore buyer guides: {SITE}/insights\n\n{TAGS_TIP}"),
    ("voiced-kharadi-2bhk-en.mp4", "facebook_page", f"{HOME_EN}\n\n\U0001F449 {SITE}/go\n\n#Kharadi #PuneRealEstate {brand.HASHTAG}"),
]


async def main(dry: bool) -> None:
    cfg = replace(load(), dry_run=dry)
    for name, channel, caption in JOBS:
        src = UP / "reels" / name
        try:
            staged = publish.stage(src, UP)
            url = publish.public_url(cfg, staged)
            res = await publish.publish_reel(channel, url, caption, cfg=cfg, file_path=src if channel == "facebook_page" else None)
            print(f"POSTED {name} -> {channel}: {res.permalink or res.external_id}")
        except Exception as e:
            print(f"FAILED {name} -> {channel}: {e}")
        await asyncio.sleep(5)


asyncio.run(main("--dry-run" in sys.argv))
