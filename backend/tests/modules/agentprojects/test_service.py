from datetime import datetime

import pytest
from pydantic import ValidationError

from app.modules.agentprojects import maharera
from app.modules.agentprojects.schemas import ProjectIn
from app.modules.agentprojects.service import ProjectError, ProjectService

from ..fakes import FakeDb

NOW = datetime(2026, 10, 3, 9, 0)

# The real answer for MY HOME UPPER KHARADI (2026-10-03), trimmed to the fields we read.
GENERAL = {"message": "SUCCESS", "status": "1", "responseObject": {
    "projectId": 53311, "projectName": "MY HOME UPPER KHARADI", "projectRegistartionNo": "P52100078796",
    "projectTypeName": "Residential / Group Housing", "projectProposeComplitionDate": "2029-04-30",
    "originalProjectProposeCompletionDate": "2028-12-31", "reraRegistrationDate": "2025-01-13",
    "totalNumberOfSoldUnits": 102, "totalNumberOfUnits": 143, "revisedDate": "2029-04-30"}}


def project(**kw) -> ProjectIn:
    base = dict(name="Goyal My Home", builder="Goyal Properties", promoter="GODIVA PROMOTERS LLP",
                locality="Upper Kharadi", rera_no="P52100078796", maharera_id=53311, status="live",
                configurations=[{"label": "2 BHK", "bhk": 2, "carpet_sqft": 941, "price_inr": 9700000},
                                {"label": "3 BHK", "bhk": 3, "carpet_sqft": 1205, "price_inr": 12500000}],
                issues=[{"field": "possession", "theirs": "RERA possession Dec 2028",
                         "found": "MahaRERA now shows 30 Apr 2029"}])
    base.update(kw)
    return ProjectIn(**base)


def make(answer=GENERAL):
    db = FakeDb()
    calls = []

    async def fetch(mid):
        calls.append(mid)
        return answer

    svc = ProjectService(db, now=lambda: NOW, fetch=fetch)
    return svc, db, calls


async def add_profile(db, slug="house-deal", public=True):
    await db.get_collection("agent_public_profiles").insert_one({"_id": "A1", "agent_id": "A1", "slug": slug,
                                                                 "is_public": public})


async def test_upsert_derives_price_per_sqft_and_range():
    svc, db, _ = make()
    out = await svc.upsert("A1", "goyal-my-home", project())
    assert [c.price_per_sqft for c in out.configurations] == [10308, 10373]
    assert (out.price_min, out.price_max, out.bhk_options) == (9700000, 12500000, [2.0, 3.0])
    assert out.rera is None and out.issues[0].status == "open"
    again = await svc.upsert("A1", "goyal-my-home", project(positioning="Upper Kharadi, next to Decathlon"))
    assert again.id == out.id and len(db.get_collection("agent_projects").docs) == 1


async def test_check_reads_maharera_and_keeps_it_across_edits():
    svc, db, calls = make()
    await svc.upsert("A1", "goyal-my-home", project())
    out = await svc.check_maharera("A1", "goyal-my-home")
    assert calls == [53311]
    r = out.rera
    assert (r.completion_at_registration, r.completion_now, r.units_booked, r.units_total) == ("2028-12-31", "2029-04-30", 102, 143)
    assert r.promoter == "GODIVA PROMOTERS LLP" and r.checked_at == "2026-10-03"
    assert r.url == "https://maharerait.maharashtra.gov.in/public/project/view/53311"
    assert out.booked_pct == 71 and out.completion_moved_months == 4
    kept = await svc.upsert("A1", "goyal-my-home", project(positioning="x"))
    assert kept.rera.completion_now == "2029-04-30"
    dropped = await svc.upsert("A1", "goyal-my-home", project(rera_no="P52100055341", maharera_id=43848))
    assert dropped.rera is None


async def test_check_refuses_a_different_registration_and_silence():
    svc, _, _ = make({**GENERAL, "responseObject": {**GENERAL["responseObject"], "projectRegistartionNo": "P52100000001"}})
    await svc.upsert("A1", "p", project())
    with pytest.raises(ProjectError) as e:
        await svc.check_maharera("A1", "p")
    assert e.value.status_code == 422 and "not P52100078796" in str(e.value)
    svc, _, _ = make(None)
    await svc.upsert("A1", "p", project())
    with pytest.raises(ProjectError) as e:
        await svc.check_maharera("A1", "p")
    assert e.value.status_code == 503
    svc, _, _ = make()
    await svc.upsert("A1", "p", project(maharera_id=None))
    with pytest.raises(ProjectError) as e:
        await svc.check_maharera("A1", "p")
    assert e.value.status_code == 422


async def test_public_reads_only_live_projects_of_public_agents_and_never_issues():
    svc, db, _ = make()
    await add_profile(db)
    await svc.upsert("A1", "goyal-my-home", project(order=2))
    await svc.upsert("A1", "draft-one", project(status="draft"))
    await svc.upsert("A1", "kosmic", project(order=1, name="Kosmic Kourtyard"))
    items = await svc.public_list("house-deal")
    assert [p.slug for p in items] == ["kosmic", "goyal-my-home"]
    assert "issues" not in items[0].model_dump() and "agent_id" not in items[0].model_dump()
    assert (await svc.public_get("house-deal", "kosmic")).name == "Kosmic Kourtyard"
    for slug, p in (("house-deal", "draft-one"), ("house-deal", "nope"), ("someone-else", "kosmic")):
        with pytest.raises(ProjectError):
            await svc.public_get(slug, p)


async def test_hidden_agent_profile_hides_projects():
    svc, db, _ = make()
    await add_profile(db, public=False)
    await svc.upsert("A1", "kosmic", project())
    with pytest.raises(ProjectError) as e:
        await svc.public_list("house-deal")
    assert e.value.status_code == 404


def test_input_rules():
    with pytest.raises(ValidationError):
        project(rera_no="HZ-33")
    with pytest.raises(ValidationError):
        project(possession_target="March 2028")
    with pytest.raises(ValidationError):
        project(unknown="x")
    assert project(rera_no=" p52100078796 ").rera_no == "P52100078796"
    assert project(rera_no="PR1261012601574").rera_no == "PR1261012601574"


def test_parse_general_handles_missing_and_wrong_answers():
    with pytest.raises(maharera.MahaReraError):
        maharera.parse_general({"status": "0"}, "P52100078796", 1)
    r = maharera.parse_general(GENERAL, "p52100078796", 53311)
    assert r["registered_on"] == "2025-01-13" and r["name"] == "MY HOME UPPER KHARADI"
