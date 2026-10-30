"""Bring House Deal's own projects from house-deal.com onto Avasetu: more photos for their listings, and the projects they list
there that Avasetu does not have yet.

  cd backend && PYTHONPATH=. python scripts/house_deal_sync.py --dry-run    # what it would do, nothing written or downloaded
  cd backend && PYTHONPATH=. python scripts/house_deal_sync.py              # in the backend container on the VM

Owner 2026-10-30: "if we have a project from house-deal, same one, and pictures are missing, add from there", and bring their
plots and villas. Idempotent; run it again whenever their site changes.

Photos: a listing with fewer than MAX_PHOTOS (the listing schema's limit, a hosting cost) gets the project page's own pictures
from house-deal.com, saved as uploads/images/hd-<slug>-NN.jpg (1,920 px wide at most). A picture already on the listing is
skipped (an 8x8 average hash, so a re-saved copy counts as the same), and so is the site's chrome: any image on more than one
of their pages (their promo banner, the calendar and area icons, a Lodha banner pasted on the VTP pages).

New listings: only the pages in NEW (checked by hand on 2026-10-30), live under House Deal, from their price table, with the
locality MahaRERA files them under (their site says Upper Kharadi for VTP's Manjari projects). Gulmohar City's plots are
published as House Deal shows them (owner 2026-10-30: "just publish as is done by house deal").
"""
import argparse
import asyncio
import hashlib
import io
import re
import sys
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

SLUG = "house-deal"
SITE = "https://house-deal.com"
UA = {"User-Agent": "Mozilla/5.0 (Avasetu; House Deal listings)"}
MAX_PHOTOS = 10
WIDTH = 1920
NEW = {   # page -> what it is (checked by hand); the rest of a new listing comes from the page
    "vtp-aurelia-kharadi": "apartment", "vtp-dolce-vita": "apartment", "vtp-altamira": "apartment",
    "yashoda-east-rise": "apartment", "vtp-never-before": "villa", "gulmohar-city": "plot",
}
CHROME = re.compile(r"logo|agent-|avatar|icon|favicon|placeholder|calender|calendar|/area\.|banner-img|-banner\.", re.I)


def price_of(text: str) -> Optional[int]:
    """'93 L' -> 9300000, '1.02 Cr' -> 10200000."""
    m = re.match(r"\s*([\d.]+)\s*(cr|crore|l|lac|lakh)", text or "", re.I)
    if not m:
        return None
    return int(round(float(m.group(1)) * (1e7 if m.group(2).lower().startswith("cr") else 1e5)))


def read_page(html: str) -> Dict:
    body = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", "", html, flags=re.S)
    text = re.sub(r"(\|\s*)+", "| ", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", body)))
    title = re.search(r"<title>([^<]+)</title>", html)
    rera = re.search(r"RERA No\s*\|?\s*([A-Z]{1,3}\d{8,16})", text)
    area = re.search(r"Area:\s*\|?\s*([^|]{2,40})", text)
    rows = []
    for kind, price, sqft in re.findall(r"\|\s*(\d(?:\.\d)?\s*BHK|Plot|Villa|Agriculture)\s*\|\s*₹\s*([\d.]+\s*(?:Cr|L|Lac|Lakh))\s*\|\s*([\d,]+)\s*sqft", text, re.I):
        bhk = re.match(r"(\d(?:\.\d)?)", kind)
        rows.append({"bhk": float(bhk.group(1)) if bhk else None, "carpet_sqft": int(sqft.replace(",", "")), "price_inr": price_of(price)})
    imgs: List[str] = []
    for m in re.findall(r"https://house-deal\.com/wp-content/uploads/[^\"'\s)]+?\.(?:jpe?g|png|webp)", html):
        base = re.sub(r"-\d{2,4}x\d{2,4}(?=\.\w+$)", "", m)
        if not CHROME.search(base) and base not in imgs:
            imgs.append(base)
    return {"name": (title.group(1).split(" - ")[0].strip() if title else ""), "rera": rera.group(1) if rera else None,
            "area": area.group(1).strip() if area else None, "rows": rows, "imgs": imgs}


def ahash(data: bytes) -> int:
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("L").resize((8, 8))
    px = list(im.getdata())
    avg = sum(px) / 64
    return sum(1 << i for i, p in enumerate(px) if p > avg)


def same(a: int, b: int) -> bool:
    return bin(a ^ b).count("1") <= 6


def jpeg(data: bytes) -> Tuple[bytes, int, int]:
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    if im.width > WIDTH:
        im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "JPEG", quality=85, optimize=True, progressive=True)
    return out.getvalue(), im.width, im.height


def words(name: str) -> str:
    """A project's name for matching: lower case, no builder suffixes or spelling noise ("Unique Youtophia Phase 3" = "unique youtopia")."""
    w = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower().replace("youtophia", "youtopia").replace("rytham", "rhythm"))
    w = re.sub(r"\b(?:phase|ph|wing|tower|towers|pune|kharadi|wagholi|by|the|\d+)\b", " ", w)
    return " ".join(w.split())


def slug_of(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50]


def money(n: int) -> str:
    return f"{n / 1e7:.2f}".rstrip("0").rstrip(".") + " Cr" if n >= 1e7 else f"{n / 1e5:.2f}".rstrip("0").rstrip(".") + " L"


async def fetch(http: httpx.AsyncClient, url: str) -> Optional[httpx.Response]:
    for attempt in range(4):
        try:
            r = await http.get(url)
            if r.status_code == 200:
                return r
        except httpx.HTTPError:
            pass
        await asyncio.sleep(3 * (attempt + 1))
    return None


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--uploads", default="uploads")
    a = ap.parse_args()

    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import settings
    from app.modules.areastats.pages import page_for
    from app.modules.listings.schemas import ListingCreate
    from app.modules.listings.service import compute_fingerprint

    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    prof = await db.agent_public_profiles.find_one({"slug": SLUG})
    images = Path(a.uploads) / "images"

    async def project_of(regno: Optional[str]) -> Optional[dict]:
        return await page_for(db, regno) if regno else None

    pages: Dict[str, Dict] = {}
    async with httpx.AsyncClient(headers=UA, timeout=60, follow_redirects=True) as http:
        sm = await fetch(http, SITE + "/property-sitemap.xml")
        for url in re.findall(r"<loc>([^<]+)</loc>", sm.text if sm else ""):
            key = url.rstrip("/").rsplit("/", 1)[-1]
            if key == "property":
                continue
            r = await fetch(http, url)
            if r is not None:
                pages[key] = {**read_page(r.text), "page": url}
            await asyncio.sleep(1.0)
        # the site's chrome: an image on more than one page belongs to no project
        seen = Counter(i for p in pages.values() for i in p["imgs"])
        for p in pages.values():
            p["imgs"] = [i for i in p["imgs"] if seen[i] == 1]

        listings = await db.listings.find({"agent_id": prof["agent_id"], "status": {"$in": ["live", "under_offer"]}}).to_list(500)
        by_project: Dict[str, dict] = {}
        for l in listings:
            pg = await project_of((l.get("rera_no") or "").upper())
            for k in filter(None, [pg and pg["slug"], (l.get("rera_no") or "").upper()]):
                by_project.setdefault(k, l)

        # their page and our listing sometimes carry different towers' numbers (Lodha Camelot, Kohinoor Kaleido): the name decides
        by_name = {words(l.get("project_name") or ""): l for l in listings if words(l.get("project_name") or "")}
        now = datetime.utcnow()
        topped = created = 0
        for key, p in pages.items():
            pg = await project_of(p["rera"])
            l = by_project.get(pg["slug"] if pg else "") or by_project.get(p["rera"] or "") or by_name.get(words(p["name"]))
            if l is None and key not in NEW:
                if p["rera"] or p["rows"]:
                    print(f"-  {key}: not on Avasetu and not in NEW (left alone)")
                continue
            if l is None:   # a new listing from their page
                rows = [r for r in p["rows"] if r["price_inr"]]
                first = min(rows, key=lambda r: r["price_inr"]) if rows else None
                place = (pg or {}).get("slug", "")
                locality = (await db.projects.find_one({"page_slug": place}, {"pune_place_name": 1}) or {}).get("pune_place_name") if place else None
                locality = locality or p["area"] or "Pune"
                kind = NEW[key]
                what = (f"{int(first['bhk'])} BHK and up from {money(first['price_inr'])}" if first and first["bhk"]
                        else f"plots of {first['carpet_sqft']:,} sq ft from {money(first['price_inr'])}" if first and kind == "plot"
                        else "Villas, price on request")
                offered = [f"{r['bhk']:g} BHK of {r['carpet_sqft']:,} sq ft carpet at Rs {money(r['price_inr'])}" if r["bhk"]
                           else f"{r['carpet_sqft']:,} sq ft plot at Rs {money(r['price_inr'])}" for r in rows]
                body = {
                    "visibility": "public", "transaction": "sale", "property_type": kind, "listing_scope": "layout",
                    "title": f"{p['name']}, {locality}: {what}"[:120], "city": "Pune", "locality": locality, "project_name": p["name"],
                    "rera_no": p["rera"], "bhk": first["bhk"] if first else None, "carpet_sqft": first["carpet_sqft"] if first else None,
                    "price_inr": first["price_inr"] if first else None,
                    "configurations": [r for r in rows if r["bhk"]] if len([r for r in rows if r["bhk"]]) > 1 else None,
                    "description": {"en": (f"{p['name']} in {locality}, Pune" + (f", MahaRERA {p['rera']}" if p["rera"] else "") + ". "
                                           + ("On offer: " + "; ".join(offered) + "." if rows else "Ask House Deal for prices and a site visit."))},
                }
                doc = ListingCreate(**body).model_dump()
                lid = uuid.uuid4().hex
                doc.update({"_id": lid, "id": lid, "agent_id": prof["agent_id"], "status": "live", "media": [], "created_at": now,
                            "updated_at": now, "published_at": now, "freshness_confirmed_at": now, "imported_from": p["page"]})
                doc["fingerprint"] = compute_fingerprint(doc)
                print(f"+  new listing: {doc['title']}  ({len(rows)} price rows)")
                if not a.dry_run:
                    await db.listings.insert_one(doc)
                l = doc
                created += 1
            # photos up to MAX_PHOTOS, never one it already has
            media = list(l.get("media") or [])
            room = MAX_PHOTOS - len(media)
            if room <= 0 or not p["imgs"]:
                continue
            have = []
            for m in media:
                f = images / str(m.get("url", "")).rsplit("/", 1)[-1]
                if f.is_file():
                    try:
                        have.append(ahash(f.read_bytes()))
                    except Exception:
                        pass
            name = slug_of(l.get("project_name") or p["name"])
            added = []
            for src in p["imgs"]:
                if len(added) >= room:
                    break
                r = await fetch(http, src)
                if r is None or len(r.content) < 20_000:   # thumbnails and icons
                    continue
                try:
                    h = ahash(r.content)
                    data, w, _ = jpeg(r.content)
                except Exception:
                    continue
                if any(same(h, x) for x in have) or w < 600:
                    continue
                have.append(h)
                n = len(media) + len(added) + 1
                fname = f"hd-{name}-{n:02d}-{hashlib.sha1(src.encode()).hexdigest()[:6]}.jpg"
                if not a.dry_run:
                    images.mkdir(parents=True, exist_ok=True)
                    (images / fname).write_bytes(data)
                # Only the fields the listing's Media model takes: a stray key or a quality with no score breaks every read.
                added.append({"url": f"/uploads/images/{fname}", "kind": "image", "order": len(media) + len(added)})
                await asyncio.sleep(0.5)
            if added:
                print(f"   {l.get('title', '')[:50]}: {len(media)} -> {len(media) + len(added)} photos")
                if not a.dry_run:
                    await db.listings.update_one({"_id": l["_id"]}, {"$set": {"media": media + added, "updated_at": now}})
                topped += 1
    print(f"{'would create' if a.dry_run else 'created'} {created} listings; {'would add' if a.dry_run else 'added'} photos to {topped}")


if __name__ == "__main__":
    asyncio.run(_main())
