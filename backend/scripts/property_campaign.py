"""Showcase: one property -> its automatic fact sheet -> a campaign of posts, with a contact sheet and captions.

    cd backend && PYTHONPATH=. python scripts/property_campaign.py --project "Gulmohar City" --locality Ranjangaon \
        --type plot --price 3230000 --sqft 1927 --out property-campaign/gulmohar-city [--llm]

Reads the network (MahaRERA, OpenStreetMap). Writes only into --out, and with --db the fact sheet into `property_facts`. Without --llm the copy is the deterministic path."""
import argparse
import asyncio
import json
from pathlib import Path

from app.modules.creative.samples import contact_sheet
from app.modules.propertyfacts import campaign
from app.modules.propertyfacts.facts import conflicts
from app.modules.propertyfacts.gather import Clients, gather


async def run(a) -> None:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    doc = {"project_name": a.project, "locality": a.locality, "city": a.city, "rera_no": a.rera, "property_type": a.type,
           "transaction": "sale", "price_inr": a.price, "carpet_sqft": a.sqft}
    clients = Clients()
    if a.db:  # read our MahaRERA register first and keep the gathered sheet
        from motor.motor_asyncio import AsyncIOMotorClient

        from app.core.config import settings
        from app.modules.newsroom.store import Store
        from app.modules.propertyfacts.store import FactsStore
        db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
        clients = Clients(register=Store(db), facts_store=FactsStore(db))
    s = await gather({k: v for k, v in doc.items() if v not in (None, "")}, clients)

    lines = [f"# Fact sheet: {a.project}, {a.locality}", ""]
    if s.match:
        lines.append(f"MahaRERA: {s.match.project.regno if s.match.project else 'not matched'} ({s.match.how})\n")
    lines.append("| use | level | fact | value | sources |\n|---|---|---|---|---|")
    for f in s.facts.values():
        lines.append(f"| {'post' if f.usable else 'hold'} | {f.level} | {f.key} | {json.dumps(f.value, ensure_ascii=False)} | "
                     f"{', '.join(f.sources)} |")
    lines += [f"\nIssue: {f.key} = {f.value!r}; others say " + ", ".join(f"{r.value!r} ({r.source})" for r in f.disagree)
              for f in conflicts(s.facts)]
    lines += [f"\nNote: {n}" for n in s.notes]

    llm = None
    if a.llm:
        from app.platform.llm import default_llm
        llm = default_llm()
    dropped: dict = {}
    packs = await campaign.make(s.facts, out / "posts", llm=llm, photo=a.photo or "none", link=a.link, dropped=dropped)
    contact_sheet([p for _, p in packs], out / "contact-sheet.jpg", "instagram")

    lines += ["", f"# Campaign: {len(packs)} posts", ""] + [f"Dropped {k}: {v}" for k, v in dropped.items()]
    for i, (aid, p) in enumerate(packs, 1):
        lines += [f"## Day {i}: {aid} ({p.design.get('layout')}, {len(p.images)} image{'s' if len(p.images) > 1 else ''})",
                  "", p.caption, ""]
    (out / "campaign.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {out / 'contact-sheet.jpg'} and {out / 'campaign.md'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--locality", required=True)
    ap.add_argument("--city", default="Pune")
    ap.add_argument("--rera", default="")
    ap.add_argument("--type", default="apartment")
    ap.add_argument("--price", type=int, default=None, help="asking price in rupees")
    ap.add_argument("--sqft", type=int, default=None, help="carpet area, or plot area for a plot")
    ap.add_argument("--photo", default="", help="a real photo of the property (file path); default: no photo")
    ap.add_argument("--link", default="", help="detail page URL for captions")
    ap.add_argument("--out", default="property-campaign")
    ap.add_argument("--llm", action="store_true", help="write copy with the LLM (falls back to the rule path)")
    ap.add_argument("--db", action="store_true", help="use MongoDB: read the project register first, save the fact sheet")
    asyncio.run(run(ap.parse_args()))


if __name__ == "__main__":
    main()
