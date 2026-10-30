"""Attach House Deal's sample-flat videos from house-deal.com to their listings on Avasetu (played from house-deal.com, not copied).

  cd backend && PYTHONPATH=. python scripts/house_deal_videos.py --dry-run    # print the matches, write nothing
  cd backend && PYTHONPATH=. python scripts/house_deal_videos.py              # in the backend container on the VM

Idempotent: run it again whenever house-deal.com adds videos. It reads every page in house-deal.com/property-sitemap.xml, takes
the page's MahaRERA number and its <video> files, and matches a page to a live House Deal listing when both numbers lead to the
same project page in our register (their site and their listing sometimes use different towers' numbers: Lodha Camelot,
Kohinoor Kaleido), or failing that the same number. It sets `videos` = [{url, label}] on the listing; the project page shows
them under the pictures (propertyfacts.router.listing_videos keeps only https .mp4 files on the agent's website). The label
comes from the file name ("Godrej-Ivara-3bhk-Sample-flat-.mp4" -> "3 BHK sample flat"): the tabs on their pages are often wrong.
Owner 2026-10-30: "yes we can play directly from house deal".
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import httpx

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

SLUG = "house-deal"
SITEMAP = "https://house-deal.com/property-sitemap.xml"
UA = {"User-Agent": "Mozilla/5.0 (Avasetu; House Deal listings)"}


def label_of(url: str) -> str:
    name = url.rsplit("/", 1)[-1].lower()
    m = re.search(r"(\d(?:\.\d)?)\s*[-_ ]?\s*bhk", name)
    if m:
        return f"{m.group(1)} BHK sample flat"
    if "walkthrough" in name or "walk-through" in name:
        return "Walkthrough"
    return "Sample flat" if "sample" in name else "Project video"


def read_page(html: str) -> Dict:
    text = re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S))
    rera = re.search(r"RERA No\s*([A-Z]{1,3}\d{8,16})", text)
    urls: List[str] = []
    for block in re.findall(r"<video[^>]*>.*?</video>", html, re.S):
        for u in re.findall(r'src="(https://(?:www\.)?house-deal\.com/[^"]+\.mp4)"', block):
            if u not in urls:
                urls.append(u)
    return {"rera": rera.group(1) if rera else None, "videos": [{"url": u, "label": label_of(u)} for u in urls]}


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import settings
    from app.modules.areastats.pages import page_for

    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    prof = await db.agent_public_profiles.find_one({"slug": SLUG})
    if not prof:
        raise SystemExit(f"no profile {SLUG}")

    async def project_of(regno: Optional[str]) -> Optional[str]:
        page = await page_for(db, regno) if regno else None
        return page["slug"] if page else None

    pages: Dict[str, Dict] = {}    # key (project slug or regno) -> page
    async with httpx.AsyncClient(headers=UA, timeout=40, follow_redirects=True) as http:
        sm = (await http.get(SITEMAP)).text
        for url in re.findall(r"<loc>([^<]+)</loc>", sm):
            if url.rstrip("/").endswith("/property"):
                continue
            page = {**read_page((await http.get(url)).text), "page": url}
            if not page["rera"] or not page["videos"]:
                continue
            pages[page["rera"]] = page
            slug = await project_of(page["rera"])
            if slug:
                pages.setdefault(slug, page)
            await asyncio.sleep(0.3)

    done = 0
    async for l in db.listings.find({"agent_id": prof["agent_id"], "status": {"$in": ["live", "under_offer"]}}):
        regno = (l.get("rera_no") or "").strip().upper()
        page = pages.get(await project_of(regno) or "") or pages.get(regno)
        if not page:
            print(f"-  {l.get('title', '')[:50]} ({regno}): no video page")
            continue
        print(f"{len(page['videos'])}  {l.get('title', '')[:50]} <- {page['page']}  {[v['label'] for v in page['videos']]}")
        if not a.dry_run:
            await db.listings.update_one({"_id": l["_id"]}, {"$set": {"videos": page["videos"]}})
        done += 1
    print(f"{'would set' if a.dry_run else 'set'} videos on {done} listings")


if __name__ == "__main__":
    asyncio.run(_main())
