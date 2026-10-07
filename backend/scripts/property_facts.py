"""Gather a property's facts from every automatic source and print the sheet (docs/CONTENT_PLATFORM.md PF track).

    cd backend && PYTHONPATH=. python scripts/property_facts.py --project "Gulmohar City" --locality Ranjangaon --type plot

Reads the network (MahaRERA, OpenStreetMap); writes nothing."""
import argparse
import asyncio

from app.modules.propertyfacts.facts import conflicts
from app.modules.propertyfacts.gather import Clients, gather


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="")
    ap.add_argument("--locality", required=True)
    ap.add_argument("--city", default="Pune")
    ap.add_argument("--rera", default="")
    ap.add_argument("--type", default="", help="property type, as on a listing (plot, apartment, ...)")
    ap.add_argument("--price", type=int, default=None, help="asking price in rupees")
    a = ap.parse_args()
    doc = {"project_name": a.project, "locality": a.locality, "city": a.city, "rera_no": a.rera, "property_type": a.type,
           "price_inr": a.price}
    s = asyncio.run(gather(doc, Clients()))
    if s.match:
        print(f"MahaRERA match: {s.match.project.regno if s.match.project else 'none'} ({s.match.how})")
    for f in s.facts.values():
        mark = "post" if f.usable else "hold"
        print(f"  [{mark}] {f.level:<12} {f.key:<28} {f.value!r:<40} {', '.join(f.sources)}")
    for f in conflicts(s.facts):
        print(f"  ISSUE {f.key}: {f.value!r} vs " + ", ".join(f"{r.value!r} ({r.source})" for r in f.disagree))
    for n in s.notes:
        print("  note:", n)


if __name__ == "__main__":
    main()
