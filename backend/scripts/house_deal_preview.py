"""Create (or refresh) the House Deal preview: the agent's Avasetu site at /agent/house-deal with 5 checked projects.

  cd backend && PYTHONPATH=. python scripts/house_deal_preview.py              # uses MONGODB_URL / DATABASE_NAME like the app
  cd backend && PYTHONPATH=. python scripts/house_deal_preview.py --dry-run    # validate and print, write nothing
  cd backend && PYTHONPATH=. python scripts/house_deal_preview.py --no-check   # skip the MahaRERA re-read

House Deal (house-deal.com, Upper Kharadi) is the first agent we are pitching. Until they agree in writing, the site is a
PREVIEW: branding_data.preview = true makes it unlisted (noindex, not in the sitemap) and labelled as a preview, and no
post goes out under their name. No invite code is issued here; the owner issues one from Studio > Agents after consent.

Sources (2026-10-03):
- house-deal.com project pages: prices, sizes, builder target dates, amenities, land/towers/floors (labelled "agent").
- MahaRERA public records: registration, promoter, completion dates, units booked (re-read by the module, labelled "maharera").
- OpenStreetMap / OSRM: the Rohan Abhilasha township pin and road distances from it (labelled "osm").
- Our own summaries (positioning, who it suits), labelled "avasetu".
Builder photos are NOT used: we have no permission yet. Area photos are Wikimedia Commons (frontend/public/area/CREDITS.md).
"""
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.agentprojects.schemas import ProjectIn  # noqa: E402
from app.modules.agentprojects.service import ProjectError, ProjectService  # noqa: E402
from app.modules.onboarding import branding as bd  # noqa: E402
from app.modules.onboarding.schemas import SiteUpdate  # noqa: E402

SLUG = "house-deal"
PHONE = "+917447212121"  # House Deal's public business number, as on house-deal.com
NAME = "House Deal"
PRIMARY = "#004274"  # House Deal's own blue (house-deal.com)
BRANDING = {
    "business_name": NAME,
    "tagline": "New projects in Kharadi and Wagholi, checked on MahaRERA",
    "about": ("House Deal helps buyers choose new projects in Upper Kharadi, Kharadi and Wagholi, from the office at "
              "RTC Silver, Upper Kharadi. Every project here shows what MahaRERA says today, next to the builder's own plan."),
    "preset": "navy-gold",
    "custom_primary": PRIMARY,
    "areas": ["Upper Kharadi", "Kharadi", "Wagholi", "Mundhwa", "Hadapsar"],
    "languages": ["English", "Hindi", "Marathi"],
}
OFFICE = "1107, RTC Silver, Upper Kharadi, Wagholi, Pune 412207"

AREA_PHOTOS = {
    "skyline": {"url": "/area/kharadi-skyline.jpg", "caption": "Kharadi skyline (area photo, not the project)",
                "credit": "Photo: Akshit 77, CC BY-SA 4.0, Wikimedia Commons"},
    "eon": {"url": "/area/eon-it-park.jpg", "caption": "EON IT Park, Kharadi (area photo, not the project)",
            "credit": "Photo: BhushanWikipedian, CC BY-SA 4.0, Wikimedia Commons"},
    "wtc": {"url": "/area/wtc-kharadi.jpg", "caption": "World Trade Center, Kharadi (area photo, not the project)",
            "credit": "Photo: DesiBoy101, CC BY 4.0, Wikimedia Commons"},
}

AGENT_PROVENANCE = {"configurations": "agent", "possession_target": "agent", "amenities": "agent", "specs": "agent",
                    "address": "agent", "positioning": "avasetu", "who_it_suits": "avasetu", "highlights": "avasetu"}


def _conf(label, bhk, sqft, price):
    return {"label": label, "bhk": bhk, "carpet_sqft": sqft, "price_inr": price, "source": "agent"}


PROJECTS: Dict[str, dict] = {
    "amco-equa": dict(
        order=1, name="AMCO Equa", builder="AMCO Landmark Realty", promoter="AMCO LANDMARK REALTY",
        locality="Wagholi", address="BAIF Road, Wagholi, Pune 412207", pincode="412207",
        rera_no="P52100032093", maharera_id=30763,
        scope_note="This registration (EQUA) is one of three for Equa on MahaRERA: Wing C and Wings D and E are registered separately.",
        configurations=[_conf("2 BHK", 2, 549, 5999000), _conf("2 BHK large", 2, 635, 6949000), _conf("3 BHK", 3, 784, 8549000)],
        possession_target="2027-03",
        positioning="The lowest starting price of the five, and the nearest MahaRERA completion date.",
        who_it_suits=["First home under ₹70 lakh", "Buyers who want to move in around 2027",
                      "A compact 3 BHK under ₹90 lakh"],
        highlights=["Off BAIF Road, Wagholi", "Most homes in this registration are already booked"],
        amenities=["Clubhouse", "Gym", "Swimming pool", "Multipurpose hall", "Landscaped garden", "Children's play area",
                   "Mini theatre", "Party hall", "Yoga deck", "Senior citizen area", "Co-working space", "Ganesh temple"],
        specs={"Land": "2.5 acres", "Towers": "5", "Floors": "G + 13"},
        maps_query="Equa AMCO Landmark BAIF Road Wagholi Pune",
        media=[AREA_PHOTOS["skyline"]],
        issues=[
            {"field": "status", "theirs": "Ready to move", "found": "MahaRERA completion date is 30 Apr 2027 (31 Dec 2026 at registration); the building is not complete yet"},
            {"field": "possession", "theirs": "RERA possession Dec 2027", "found": "MahaRERA shows 30 Apr 2027"},
        ],
    ),
    "anshul-medora": dict(
        order=2, name="Anshul Medora", builder="Anshul Group", promoter="ANSHUL BHOSALE REALTY LLP",
        locality="Wagholi", address="Ivy Estate Road, behind Tata Croma, off Pune–Nagar Highway, Wagholi, Pune 412207",
        pincode="412207", rera_no="P52100079331", maharera_id=54278,
        scope_note="This registration is ANSHUL MEDORA C BUILDING (90 homes). Ask which building a home is in before booking.",
        configurations=[_conf("2 BHK", 2, 698, 6600000), _conf("3 BHK", 3, 936, 8600000)],
        possession_target="2028-12",
        positioning="A 3 BHK under ₹90 lakh on Ivy Estate Road, off Nagar Road.",
        who_it_suits=["Families who need a 3 BHK under ₹90 lakh", "Buyers comfortable with a 2030 completion date"],
        highlights=["Ivy Estate Road, behind Tata Croma", "Builder targets Dec 2028; MahaRERA date is later"],
        amenities=["Clubhouse", "Swimming pool", "Kids' pool", "Party lawn", "Open gym", "Senior citizen plaza",
                   "Children's play area", "Yoga deck", "Mini theatre", "Sports club", "Garden", "Ganesh temple",
                   "Co-working space"],
        specs={"Land": "3 acres", "Towers": "3", "Floors": "G + P + 19"},
        maps_query="Anshul Medora Ivy Estate Road Wagholi Pune",
        media=[AREA_PHOTOS["skyline"]],
        issues=[
            {"field": "possession", "theirs": "RERA possession Apr 2030", "found": "MahaRERA now shows 30 Aug 2030 (30 Apr 2030 at registration)"},
            {"field": "scope", "theirs": "3 towers, 3 acres", "found": "RERA no. P52100079331 is ANSHUL MEDORA C BUILDING only (90 homes)"},
            {"field": "url", "theirs": "house-deal.com/property/anushul-medora/", "found": "The page address misspells Anshul ('anushul')"},
        ],
    ),
    "rohan-abhilasha": dict(
        order=3, name="Rohan Abhilasha 4", builder="Rohan Builders", promoter="Rohan Housing Pvt Ltd",
        locality="Wagholi", address="Lohegaon–Wagholi Road, Wagholi, Pune 412207", pincode="412207",
        rera_no="P52100080076", maharera_id=55189,
        scope_note="This registration is Rohan Abhilasha 4 Phase 1 (416 homes), a new phase of the larger Rohan Abhilasha township.",
        configurations=[_conf("2 BHK", 2, 688, 7400000), _conf("2 BHK large", 2, 783, 8300000), _conf("3 BHK", 3, 1012, 10600000)],
        possession_target="2028-06",
        positioning="A new phase of the Rohan Abhilasha township, with the earlier buildings next door to visit.",
        who_it_suits=["Buyers who want to visit the builder's earlier buildings before booking", "IT professionals working in Kharadi",
                      "Families comparing 2 BHK sizes"],
        highlights=["Earlier Rohan Abhilasha buildings stand in the same township", "About 9.5 km by road to EON IT Park"],
        amenities=["Swimming pool", "Gym", "Clubhouse", "Children's play area", "Garden", "Sports facilities",
                   "Mini theatre", "Party hall", "Yoga deck", "Senior citizen area", "Co-working space", "Ganesh temple"],
        specs={"Township land": "7.6 acres", "Township towers": "11", "Floors": "2B + G + 12"},
        provenance={"nearby": "osm"},
        nearby=[{"name": "EON IT Park", "km": 9.5, "source": "osm"},
                {"name": "World Trade Center, Kharadi", "km": 8.9, "source": "osm"},
                {"name": "Pune Airport", "km": 11.0, "source": "osm"},
                {"name": "Phoenix Marketcity, Viman Nagar", "km": 11.0, "source": "osm"}],
        place={"lat": 18.59403, "lon": 73.9684, "source": "osm", "note": "Rohan Abhilasha township on OpenStreetMap"},
        maps_query="Rohan Abhilasha Wagholi Pune",
        media=[AREA_PHOTOS["eon"]],
        issues=[
            {"field": "possession", "theirs": "RERA possession Jun 2029", "found": "MahaRERA now shows 30 Oct 2029 (30 Jun 2029 at registration)"},
            {"field": "scope", "theirs": "7.6 acres, 11 towers, RERA P52100080076", "found": "P52100080076 is Abhilasha 4 Phase 1 only: 416 homes; the acreage and tower count describe the whole township"},
            {"field": "location", "theirs": "Near EON IT Park, World Trade Center", "found": "About 9.5 km by road to EON IT Park and 8.9 km to WTC (OpenStreetMap route)", "source": "osm"},
        ],
    ),
    "triaa-kosmic-kourtyard": dict(
        order=4, name="Triaa Kosmic Kourtyard", builder="Triaa Lifespaces", promoter="Triaa Lifespaces LLP",
        locality="Wagholi", address="Awhalwadi Road, Kalubai Nagar, Wagholi, Pune 412207", pincode="412207",
        rera_no="P52100055341", maharera_id=43848,
        scope_note="This registration is KOSMIC KOURTYARD PHASE 2. Phase 1 is registered separately (P52100032462).",
        configurations=[_conf("2 BHK", 2, 765, 7689000), _conf("3 BHK", 3, 951, 9800000), _conf("3 BHK large", 3, 1007, 10400000)],
        possession_target="2028-12",
        positioning="Mid-budget 2 and 3 BHK homes on Awhalwadi Road, with most of Phase 2 already booked.",
        who_it_suits=["2 BHK buyers with a budget near ₹80 lakh", "3 BHK buyers under ₹1.05 crore"],
        highlights=["Awhalwadi Road, Wagholi", "Phase 1 (MahaRERA date Dec 2025) is on the same site: ask to visit it"],
        amenities=["Children's play area", "Clubhouse", "Co-working space", "Ganesh temple", "Garden", "Gym",
                   "Mini theatre", "Party hall", "Senior citizen area", "Sports club", "Swimming pool", "Yoga deck"],
        specs={"Land": "4.5 acres", "Towers": "6", "Floors": "G + 14 (with podium levels)"},
        maps_query="Kosmic Kourtyard Triaa Awhalwadi Road Wagholi Pune",
        media=[AREA_PHOTOS["skyline"]],
        issues=[
            {"field": "possession", "theirs": "RERA possession Dec 2028", "found": "MahaRERA now shows 30 Apr 2029 (31 Dec 2028 at registration)"},
            {"field": "brochure", "theirs": "Kosmik_E-Brochure_V2_copy (1)", "found": "The brochure link on the page does not open; the file name also misspells Kosmic"},
        ],
    ),
    "goyal-my-home": dict(
        order=5, name="Goyal My Home, Upper Kharadi", builder="Goyal Properties", promoter="GODIVA PROMOTERS LLP",
        locality="Upper Kharadi",
        address="Nagar Road, next to Decathlon Kharadi, Upper Kharadi, Wagholi, Pune 412207", pincode="412207",
        rera_no="P52100078796", maharera_id=53311,
        scope_note="Registered on MahaRERA as MY HOME UPPER KHARADI, one tower of 143 homes.",
        configurations=[_conf("2 BHK", 2, 941, 9700000), _conf("2 BHK large", 2, 949, 10000000), _conf("3 BHK", 3, 1205, 12500000)],
        possession_target="2028-03",
        positioning="One tower of 143 homes on Nagar Road, next to Decathlon Kharadi.",
        who_it_suits=["Buyers who want Upper Kharadi rather than inner Wagholi", "Large 2 BHK buyers near ₹1 crore",
                      "A single-tower community"],
        highlights=["Next to Decathlon Kharadi, on Nagar Road", "One tower, 143 homes"],
        amenities=["Clubhouse", "Two swimming pools", "Library", "Yoga deck", "Multipurpose hall", "Indoor games",
                   "Music room", "Children's play area", "Party lawn", "Work-from-home zone", "Garden", "Gym",
                   "Ganesh temple", "Sports club"],
        specs={"Land": "1 acre", "Towers": "1", "Floors": "G + 3P + 12"},
        maps_query="My Home Upper Kharadi Goyal Decathlon Kharadi Pune",
        media=[AREA_PHOTOS["wtc"]],
        issues=[
            {"field": "possession", "theirs": "RERA possession Dec 2028", "found": "MahaRERA now shows 30 Apr 2029 (31 Dec 2028 at registration)"},
            {"field": "configurations", "theirs": "3 BHK 890 sqft ₹97.99 L and 3 BHK 906 sqft ₹98.99 L",
             "found": "These 3 BHKs are smaller than the 2 BHKs (941 and 949 sqft). Held back from the page until House Deal confirms", "source": "avasetu"},
        ],
    ),
}


def project_in(slug: str, status: str = "live") -> ProjectIn:
    d = dict(PROJECTS[slug])
    d["provenance"] = {**AGENT_PROVENANCE, **d.get("provenance", {})}
    d["media"] = [{**m, "artist_impression": False} for m in d.get("media", [])]
    return ProjectIn(**d, status=status)


async def ensure_agent(db, users, now: Callable[[], datetime], log: Callable[[str], None]) -> str:
    """The House Deal login user, public profile (preview) and concierge record. No invite code is issued."""
    profiles = db.get_collection("agent_public_profiles")
    concierge = db.get_collection("concierge_agents")
    user = await users.get_by_phone(PHONE) or await users.create(PHONE)
    uid = str(user.id)
    existing = await profiles.find_one({"slug": SLUG})
    if existing and existing.get("user_id") != uid:
        raise SystemExit(f"slug '{SLUG}' belongs to another user ({existing.get('user_id')}); not touching it")
    clean = SiteUpdate(**BRANDING)
    colors = bd.theme_for(clean.preset, clean.custom_primary)
    prev = (existing or {}).get("branding_data") or {}
    branding = {**prev, "business_name": clean.business_name, "tagline": clean.tagline, "about": clean.about,
                "preset": clean.preset, "custom_primary": clean.custom_primary, "areas": clean.areas,
                "languages": clean.languages, "colors": colors, "preview": True}
    t = now()
    fields = {
        "agent_name": NAME, "slug": SLUG, "bio": clean.about, "phone": PHONE, "office_address": OFFICE,
        "specialties": ["New projects", "Upper Kharadi", "Wagholi"], "languages": clean.languages,
        "is_active": True, "is_public": True, "branding_data": branding,
        "site_config": {"theme": colors, "hero": {"headline": NAME, "subheadline": clean.tagline},
                        "sections": ["about", "projects", "contact"], "languages": clean.languages, "city": "Pune"},
        "updated_at": t,
    }
    if existing:
        await profiles.update_one({"_id": existing["_id"]}, {"$set": fields})
        log("profile updated: /agent/" + SLUG)
    else:
        await profiles.insert_one({"_id": uid, "id": uid, "user_id": uid, "agent_id": uid, "photo": "", "email": "",
                                   "experience": "", "view_count": 0, "contact_count": 0, "created_at": t, **fields})
        log("profile created: /agent/" + SLUG)
    if not await concierge.find_one({"_id": uid}):
        await concierge.insert_one({"_id": uid, "phone": PHONE, "name": NAME, "label": "House Deal, Upper Kharadi (preview)",
                                    "created_by": "script:house_deal_preview", "created_at": t, "consent": None})
        log("concierge record created (no invite issued)")
    return uid


async def seed_projects(svc: ProjectService, agent_id: str, check: bool, log: Callable[[str], None]) -> list:
    out = []
    for slug in PROJECTS:
        p = await svc.upsert(agent_id, slug, project_in(slug))
        if check:
            try:
                p = await svc.check_maharera(agent_id, slug)
            except ProjectError as e:
                log(f"  {slug}: MahaRERA check failed ({e}); keeping the last reading")
        r = p.rera
        log(f"  {slug}: {p.rera_no} " + (f"MahaRERA {r.completion_at_registration} -> {r.completion_now}, "
                                         f"{r.units_booked}/{r.units_total} booked" if r else "no MahaRERA reading"))
        out.append(p)
    return out


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-check", action="store_true", help="do not re-read MahaRERA")
    a = ap.parse_args()
    if a.dry_run:
        for slug in PROJECTS:
            p = project_in(slug)
            print(f"{slug}: {p.name} {p.rera_no} ({len(p.configurations)} configurations, {len(p.issues)} issues)")
        print(f"would create/refresh /agent/{SLUG} as a PREVIEW, phone {PHONE[:5]}***")
        return
    from beanie import init_beanie
    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import settings
    from app.models.user import User
    from app.modules.onboarding.service import BeanieUserStore

    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    await init_beanie(database=db, document_models=[User])
    uid = await ensure_agent(db, BeanieUserStore(), datetime.utcnow, print)
    await seed_projects(ProjectService(db), uid, not a.no_check, print)
    print(f"done: /agent/{SLUG} (user {uid}), preview only")


if __name__ == "__main__":
    asyncio.run(_main())
