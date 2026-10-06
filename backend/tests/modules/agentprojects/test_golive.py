from datetime import date, datetime, timezone

from app.modules.agentprojects.service import ProjectService
from app.modules.calendar import adapters
from app.modules.calendar.store import Store
from scripts import house_deal_golive as gl
from scripts.house_deal_preview import PROJECTS, project_in

from ..fakes import FakeDb
from .test_service import GENERAL

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


async def seeded(tmp_path):
    db = FakeDb()
    await db.get_collection("agent_public_profiles").insert_one(
        {"_id": "HD", "agent_id": "HD", "slug": "house-deal", "is_public": True,
         "branding_data": {"business_name": "House Deal", "preview": True}})
    await db.get_collection("concierge_agents").insert_one({"_id": "HD", "name": "House Deal", "consent": None})

    async def fetch(mid):  # every project answers with its own registration number
        slug = next(s for s, p in PROJECTS.items() if p["maharera_id"] == mid)
        return {**GENERAL, "responseObject": {**GENERAL["responseObject"], "projectRegistartionNo": PROJECTS[slug]["rera_no"]}}

    svc = ProjectService(db, now=lambda: NOW, fetch=fetch)
    for slug in PROJECTS:
        await svc.upsert("HD", slug, project_in(slug))
        await svc.check_maharera("HD", slug)
    return db


async def test_go_live_publishes_the_site_records_consent_and_plans_posts_for_approval(tmp_path):
    db = await seeded(tmp_path)
    logs = []
    out = await gl.go_live(db, tmp_path, "https://avasetu.test", date(2026, 10, 4), NOW, False, logs.append, check=False)
    prof = await db.get_collection("agent_public_profiles").find_one({"slug": "house-deal"})
    assert "preview" not in prof["branding_data"] and prof["branding_data"]["business_name"] == "House Deal"
    consent = (await db.get_collection("concierge_agents").find_one({"_id": "HD"}))["consent"]
    assert consent["given"] is True and "relayed by the owner" in consent["note"]

    rows = await Store(db).all()
    assert out["planned"] == len(rows) == 2 + 2 * len(PROJECTS)
    assert {r["status"] for r in rows} == {"planned"}  # nothing can publish before the owner approves
    assert {r["agent_id"] for r in rows} == {"HD"}
    ig = [r for r in rows if r["channel"] == "instagram" and r["slug"] == "house-deal-goyal-my-home"][0]
    assert len(ig["images"]) == 5 and all((tmp_path / p).is_file() for p in ig["images"])
    assert "Listed by House Deal" in ig["caption"] and "link in our bio" in ig["caption"]
    fb = [r for r in rows if r["channel"] == "facebook_page" and r["slug"] == "house-deal-goyal-my-home"][0]
    assert fb["caption"].endswith("https://avasetu.test/projects/goyal-my-home") and len(fb["images"]) == 1
    first = min(rows, key=lambda r: r["due_at"])
    assert first["slug"] == "house-deal-compare"

    again = await gl.go_live(db, tmp_path, "https://avasetu.test", date(2026, 10, 4), NOW, False, logs.append, check=False)
    assert again["planned"] == 0  # idempotent


async def test_interest_goes_to_the_rows_agent(monkeypatch):
    seen = {}

    async def fake_url(db, **kw):
        seen.update(kw)
        return "https://avasetu.test/i/abc"

    import app.modules.interest.service as interest
    monkeypatch.setattr(interest, "interest_url", fake_url)
    monkeypatch.setenv("INTEREST_OWNER_AGENT_ID", "OWNER")
    out = await adapters.with_interest(FakeDb(), {"channel": "facebook_page", "caption": "Hi", "slug": "s", "agent_id": "HD"})
    assert seen["agent_id"] == "HD" and "https://avasetu.test/i/abc" in out["caption"]
    await adapters.with_interest(FakeDb(), {"channel": "facebook_page", "caption": "Hi", "slug": "s"})
    assert seen["agent_id"] == "OWNER"
