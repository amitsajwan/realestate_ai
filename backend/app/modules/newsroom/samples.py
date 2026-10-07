"""Realistic sample items for design review and tests: `python -m app.modules.newsroom.samples <out_dir>` renders the cards, the digest
carousel and a contact sheet. The items are illustrations written for review (not live news) and are never stored or published."""
from app.core import brand
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from . import presentation as pr

AS_OF = datetime(2026, 9, 29, 6, 30, tzinfo=timezone.utc)


def make_doc(id: str, title: str, facts: List[str], pillar: str, areas: List[str], source: str, text: Optional[str] = None,
             question: Optional[str] = None, status: str = "pending_review") -> dict:
    where = " or ".join(pr.AREA_NAMES[a] for a in areas[:2]) or "Pune"
    what = " ".join(f if f.endswith(".") else f + "." for f in facts[:2])
    body = text or "\n\n".join([
        what, f"What to check: Read the official notice for the latest status before you decide.",
        f"Source: {source}, as of {AS_OF.day} Sep {AS_OF.year}. https://news.google.com/rss/articles/CBMi{id}",
        question or f"Does this change how you look at homes in {where}? Tell us in the comments.", "#Pune " + brand.HASHTAG])
    return {"_id": id, "status": status, "created_at": AS_OF, "updated_at": AS_OF, "published_at": AS_OF,
            "raw": {"id": id, "source": source, "url": f"https://news.google.com/rss/articles/CBMi{id}", "title": title + " | " + source,
                    "text": " ".join(facts), "published_at": AS_OF, "fetched_at": AS_OF},
            "relevance": {"keep": True, "pillar": pillar, "areas": areas, "reason": "sample"},
            "facts": {"facts": [{"text": f, "quote": f} for f in facts], "as_of": AS_OF},
            "draft": {"format": "post", "text": body, "title": title, "link": f"https://news.google.com/rss/articles/CBMi{id}", "source_names": [source]},
            "check": {"ok": True, "problems": []}}


SAMPLES: List[dict] = [
    make_doc("a1b2c3d4e5", "Pune Ring Road: ₹10,502 crore approved for the 32 km eastern stretch",
             ["The eastern stretch of the Pune Ring Road is 32 km long.", "₹10,502 crore has been approved for this stretch."],
             "infrastructure", ["kharadi", "wagholi"], "Times of India"),
    make_doc("b2c3d4e5f6", "PMC starts land acquisition for Kharadi roads, ₹27.14 crore deposited",
             ["PMC has deposited ₹27.14 crore to acquire land for road widening in Kharadi.", "Land acquisition for the Kharadi roads has started."],
             "infrastructure", ["kharadi"], "Hindustan Times"),
    make_doc("c3d4e5f6a7", "Metro corridor 2B Ramwadi to Wagholi approved, not running yet",
             ["Metro corridor 2B from Ramwadi to Wagholi has been approved.", "The line is not running yet and no opening date is given."],
             "infrastructure", ["wagholi", "kharadi"], "The Indian Express"),
    make_doc("d4e5f6a7b8", "Three Kharadi projects listed or updated on MahaRERA",
             ["Three residential projects in Kharadi were listed or updated on MahaRERA in the last seven days.", "Each listing carries its own registration number."],
             "new_supply", ["kharadi"], "MahaRERA"),
    make_doc("e5f6a7b8c9", "RBI keeps the repo rate at 5.5 percent, home-loan rates stay put",
             ["The RBI kept the repo rate unchanged at 5.5 percent.", "Banks linked to the repo rate are not expected to change home-loan rates today."],
             "rules_money", ["kharadi", "wagholi"], "ET Realty"),
    make_doc("f6a7b8c9d0", "New traffic signals planned at three Kharadi IT park junctions",
             ["PMC plans new traffic signals at three junctions near the Kharadi IT park.", "Work is expected to be tendered first."],
             "locality_life", ["kharadi"], "Punekar News"),
    make_doc("a7b8c9d0e1", "Wagholi water supply line upgrade is planned after tenders",
             ["PMC plans to upgrade the water supply line serving Wagholi.", "The work will start only after tenders are completed."],
             "locality_life", ["wagholi"], "The Hindu"),
    make_doc("b8c9d0e1f2", "Check the RERA number before you pay any token amount",
             ["Every registered project has a MahaRERA registration number.", "The MahaRERA website lets buyers look up the number for free."],
             "education", ["kharadi", "upper_kharadi", "wagholi"], "MahaRERA"),
]


def render_all(out: Path) -> List[Path]:
    from PIL import Image, ImageDraw
    from . import cards, digest
    out.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for d in SAMPLES:
        for k, p in cards.render_item(d, out).items():
            if k in ("ig", "fb"):
                paths.append(out / p)
    dg = digest.sample_digest(SAMPLES)
    paths += [out / p for p in cards.render_digest(dg, out)["ig"]]
    paths.append(out / cards.render_digest(dg, out)["fb"])
    ig = [p for p in paths if p.name.endswith("-ig.jpg") and "digest" not in p.name]
    sheet = Image.new("RGB", (4 * 360 + 50, 2 * 450 + 30), (236, 232, 222))
    for i, p in enumerate(ig[:8]):
        with Image.open(p) as im:
            sheet.paste(im.convert("RGB").resize((360, 450)), (10 + (i % 4) * 370, 10 + (i // 4) * 460))
    sheet.save(out / "contact-news.jpg", quality=82)
    return paths


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "news-samples")
    for p in render_all(target):
        print(p)
