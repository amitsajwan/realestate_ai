"""Render House Deal's pitch content: one Instagram carousel per project, one comparison carousel, captions, contact sheets.

  cd backend && PYTHONPATH=. python scripts/house_deal_content.py [--out uploads/agentprojects/house-deal]

Reads the projects scripts/house_deal_preview.py stored (with their MahaRERA readings). Writes files only: nothing is queued
or posted. These are DRAFTS for the pitch; House Deal approves before anything goes out under their name.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.agentprojects import cards  # noqa: E402
from app.modules.agentprojects.service import ProjectService  # noqa: E402
from scripts.house_deal_preview import NAME, PHONE, PRIMARY, SLUG  # noqa: E402

AGENT = {"name": NAME, "phone_display": f"{PHONE[3:8]} {PHONE[8:]}", "primary": PRIMARY}


def render(projects: list, out: Path) -> dict:
    made = {"projects": {}, "compare": None}
    for p in projects:
        files = cards.save_all(cards.project_carousel(p, AGENT), out, p["slug"])
        (out / f"{p['slug']}.txt").write_text(cards.caption(p, AGENT), encoding="utf-8")
        made["projects"][p["slug"]] = [f.name for f in files]
        cards.contact_sheet(files, out / f"{p['slug']}-sheet.jpg")
    files = cards.save_all(cards.compare_carousel(projects, AGENT, cards.area_label(projects)), out, "compare")
    made["compare"] = [f.name for f in files]
    cards.contact_sheet(files, out / "compare-sheet.jpg", cols=4)
    (out / "index.json").write_text(json.dumps(made, indent=2), encoding="utf-8")
    return made


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=f"uploads/agentprojects/{SLUG}")
    a = ap.parse_args()
    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import settings
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    profile = await db.get_collection("agent_public_profiles").find_one({"slug": SLUG})
    if not profile:
        raise SystemExit(f"/agent/{SLUG} does not exist: run scripts/house_deal_preview.py first")
    projects = [p.model_dump(mode="json") for p in await ProjectService(db).list_for_owner(profile["agent_id"])]
    made = render(projects, Path(a.out))
    print(f"wrote {sum(len(v) for v in made['projects'].values()) + len(made['compare'])} slides to {a.out}")


if __name__ == "__main__":
    asyncio.run(_main())
