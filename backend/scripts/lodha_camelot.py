"""Create (or refresh) the Lodha Camelot project record as a DRAFT: one marketed project, five MahaRERA registrations.

  cd backend && PYTHONPATH=. python scripts/lodha_camelot.py --dry-run          # validate and print, write nothing
  cd backend && PYTHONPATH=. python scripts/lodha_camelot.py                    # on the official Avasetu page (slug avasetu)
  cd backend && PYTHONPATH=. python scripts/lodha_camelot.py --agent-slug house-deal --no-check

Lodha Camelot (Upper Kharadi, 412207) is on MahaRERA as "Kharadi New Project - Tower N", one registration per tower, promoter
Lodha Developers Limited. The record links the five registrations its brochure lists (agentprojects.groups), so a brochure with
any of these numbers or the name "Lodha Camelot" lands on this project. Towers 5, 6 and 9 have the same promoter, pincode and
naming but are not in the brochure: they are kept as candidates (owner-only) and never shown as part of Camelot until the owner
confirms. The record stays `draft` (not public) until the owner reviews it; this script never sets it live.

Sources:
- Brochure (Nov 2025, labelled "builder"): the registrations and what each holds, address of the site gallery, land, architect,
  landscape and clubhouse designers, the master plan legend (amenities), travel times.
- A channel partner's quote (labelled "agent"): sizes and starting prices.
- MahaRERA public records (labelled "maharera"), read 2026-10-13: each registration's MahaRERA id and filed completion date.
Not included (no source we trust): "~80% open space", "25 m lap pool", rooftop amenities, "3 badminton courts".
"""
import argparse
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.agentprojects.schemas import ProjectIn  # noqa: E402
from app.modules.agentprojects.service import ProjectError, ProjectService  # noqa: E402

SLUG = "lodha-camelot"
READ = "2026-10-13"  # MahaRERA project API, general details of each registration
THREE = "3 BHK, 3 BHK + study"


def _reg(tower, regno, mid, holds, completion):
    return {"regno": regno, "tower": tower, "holds": holds, "maharera_id": mid, "completion": completion,
            "checked_at": READ, "source": "builder"}


def _cand(tower, regno, mid, completion):
    return {"regno": regno, "tower": tower, "maharera_id": mid, "source": "maharera",
            "why": (f"Same promoter (Lodha Developers Limited), pincode 412207 and naming ('Kharadi New Project - {tower}'), "
                    f"MahaRERA completion {completion}; not in the Nov 2025 brochure. Owner to confirm.")}


def _conf(label, bhk, sqft, price):
    return {"label": label, "bhk": bhk, "carpet_sqft": sqft, "price_inr": price, "source": "agent"}


def _near(name, minutes):
    return {"name": name, "minutes": minutes, "source": "builder"}


PROJECT = dict(
    name="Lodha Camelot", builder="Lodha", promoter="Lodha Developers Limited",
    locality="Upper Kharadi", address="Upper Kharadi Main Rd, Pune 412207", pincode="412207",
    rera_no="PR1260002501386", maharera_id=59459,  # Tower 1, the primary registration (MahaRERA checks read this one)
    registrations=[
        _reg("Tower 1", "PR1260002501386", 59459, THREE, "2030-07-31"),
        _reg("Tower 2", "PR1260002501413", 59681, THREE, "2030-07-31"),
        _reg("Tower 3", "PR1260002501399", 60478, THREE, "2030-07-31"),
        _reg("Tower 4", "PR1260002501398", 60479, THREE, "2030-07-31"),
        _reg("Tower 11", "PR1260002501449", 60480, "4 BHK + study + staff room", "2031-03-30"),
    ],
    candidates=[
        _cand("Tower 5", "PR1260002502039", 61744, "2030-09-30"),
        _cand("Tower 6", "PR1260002602176", 67557, "2031-03-31"),
        _cand("Tower 9", "PR1260002602168", 67561, "2031-09-30"),
    ],
    scope_note="Registered on MahaRERA as five towers (Tower 1, 2, 3, 4 and 11), each its own registration. Ask which tower a home is in.",
    configurations=[
        _conf("3 BHK (1250–1270 sq ft)", 3, 1250, 22400000),
        _conf("3 BHK + study", 3, 1511, 27700000),
        _conf("4 BHK + study + staff room", 4, 2244, 40500000),  # Tower 11
    ],
    amenities=[
        "Swimming pool with jacuzzi", "Kids' pool", "Meditation lawn", "Temple", "Reflexology path", "Senior citizens corner",
        "Outdoor kids play area", "Open lawn", "Pet park",
        "Clubhouse on 2 levels", "Clubhouse lounge", "Indoor badminton / half basketball court", "Gymnasium", "Indoor games",
        "Activity rooms", "Banquet halls", "Cafe lounge", "Kids club",
        "Elevated sports arena", "Multipurpose courts (5-a-side football turf cum pickleball)", "Padel courts", "Playing lawn",
        "Jogging track", "Cricket pitch central sports lawn", "Amphitheatre",
    ],
    specs={"Land": "10-acre estate", "Architect": "Hafeez Contractor", "Landscape": "SHMA",
           "Clubhouse interiors": "Studio HBA"},
    provenance={"configurations": "agent", "amenities": "builder", "specs": "builder", "address": "builder",
                "scope_note": "builder", "nearby": "builder"},
    nearby=[
        _near("Pune–Ahmednagar Highway", 3), _near("Pune Airport", 20), _near("Pune Outer Ring Road", 20),
        _near("EON IT Park", 5), _near("World Trade Center", 10), _near("Solitaire Business Hub", 15),
        _near("Citigroup", 5), _near("Infosys", 5), _near("Podar International School", 1), _near("EuroSchool", 5),
        _near("Orchids International", 10), _near("Phoenix Marketcity", 14), _near("Amanora Mall", 18),
        _near("Seasons Mall", 20), _near("Manipal Hospital Kharadi", 15), _near("Poonawalla Memorial Hospital", 25),
    ],
    maps_query="Lodha Camelot Upper Kharadi Pune",
    order=50,
)


def project_in() -> ProjectIn:
    return ProjectIn(**PROJECT, status="draft")


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--agent-slug", default="avasetu", help="whose page holds the record (default: the official Avasetu page)")
    ap.add_argument("--no-check", action="store_true", help="do not re-read Tower 1 on MahaRERA")
    a = ap.parse_args()
    p = project_in()
    if a.dry_run:
        print(f"{SLUG}: {p.name} ({p.builder}; {p.promoter}), {p.locality}, status {p.status}")
        for r in p.registrations:
            print(f"  member    {r.tower:9} {r.regno} id {r.maharera_id}  {r.holds}  completion {r.completion} ({r.source})")
        for c in p.candidates:
            print(f"  candidate {c.tower:9} {c.regno} id {c.maharera_id}  (not part of Camelot until the owner confirms)")
        print(f"  {len(p.configurations)} configurations, {len(p.amenities)} amenities, {len(p.nearby)} nearby, specs {p.specs}")
        print(f"would upsert agent_projects ({a.agent_slug}, {SLUG}) as DRAFT")
        return
    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import settings

    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    prof = await db.get_collection("agent_public_profiles").find_one({"slug": a.agent_slug})
    if not prof or not prof.get("agent_id"):
        raise SystemExit(f"no agent page with slug {a.agent_slug!r}")
    svc = ProjectService(db)
    existing = await svc.col.find_one({"agent_id": prof["agent_id"], "slug": SLUG})
    if existing and existing.get("status") == "live":
        raise SystemExit(f"{SLUG} is already live on /agent/{a.agent_slug}; not overwriting a reviewed record")
    out = await svc.upsert(prof["agent_id"], SLUG, p)
    if not a.no_check:
        try:
            out = await svc.check_maharera(prof["agent_id"], SLUG)
        except ProjectError as e:
            print(f"MahaRERA check failed ({e}); keeping the last reading")
    r = out.rera
    print(f"done: {SLUG} on /agent/{a.agent_slug} as {out.status}, {len(out.registrations)} registrations, "
          f"{len(out.candidates)} candidates; " + (f"Tower 1 MahaRERA completion {r.completion_now}" if r else "no MahaRERA reading"))


if __name__ == "__main__":
    asyncio.run(_main())
