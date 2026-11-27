"""MahaRERA agent check (onboarding/verification.py): the owner records what the register says; changing the number undoes it."""
from datetime import datetime

from app.modules.onboarding import verification as v

from .fakes import FakeDb

NOW = datetime(2026, 11, 27, 6, 0)
PAGE = "https://maharera.maharashtra.gov.in/agents/A52100000001"


async def setup(**branding):
    db = FakeDb()
    await db.get_collection("agent_public_profiles").insert_one({"agent_id": "A", "slug": "asha", "agent_name": "Asha",
                                                                 "branding_data": branding})
    return db


async def prof(db):
    return await db.get_collection("agent_public_profiles").find_one({"agent_id": "A"})


async def test_an_agent_is_pending_until_the_owner_verifies_the_number_with_its_register_page():
    db = await setup(rera_agent_no="A52100000001")
    assert v.status_of(await prof(db)) == "pending"
    out = await v.set_status(db, "OWNER", "A", "verified", PAGE, "Name and number match", NOW)
    p = await prof(db)
    assert out["status"] == "verified" and v.is_verified(p)
    assert p["rera_check"] == {"status": "verified", "number": "A52100000001", "by": "OWNER", "at": NOW, "register_url": PAGE,
                               "note": "Name and number match"}
    assert p["branding_data"]["rera_verified_no"] == "A52100000001"   # the public badge; who checked stays private


async def test_verifying_needs_a_number_and_a_maharera_register_page():
    for branding, url, code in (({}, PAGE, 409), ({"rera_agent_no": "A1"}, None, 422),
                                ({"rera_agent_no": "A1"}, "https://example.com/maharera", 422),
                                ({"rera_agent_no": "A1"}, "http://maharera.maharashtra.gov.in/x", 422)):
        db = await setup(**branding)
        try:
            await v.set_status(db, "OWNER", "A", "verified", url, None, NOW)
            assert False, "should be refused"
        except v.VerificationError as e:
            assert e.status_code == code
        assert v.status_of(await prof(db)) == "pending"


def test_the_registers_own_agent_pages_count_as_register_pages():
    # the agent search on maharera.maharashtra.gov.in links each agent to maharerait.maharashtra.gov.in/agent/view/<id>
    assert v.is_register_url("https://maharerait.maharashtra.gov.in/agent/view/281275")
    assert v.is_register_url("https://maharerait.maharashtra.gov.in/agent/view/281275?isOriginal=true")
    assert not v.is_register_url("https://maharerait.maharashtra.gov.in.example.com/agent/view/1")
    assert not v.is_register_url("https://fakemaharerait.maharashtra.gov.in.evil/agent/view/1")


async def test_a_new_number_is_pending_again_and_rejecting_removes_the_badge():
    db = await setup(rera_agent_no="A52100000001")
    await v.set_status(db, "OWNER", "A", "verified", PAGE, None, NOW)
    col = db.get_collection("agent_public_profiles")
    await col.update_one({"agent_id": "A"}, {"$set": {"branding_data.rera_agent_no": "A52100000002"}})
    row = v.view(await prof(db))
    assert row["status"] == "pending" and row["number_changed"] and row["checked_at"] is None
    await v.set_status(db, "OWNER", "A", "rejected", None, "Not on the register", NOW)
    p = await prof(db)
    assert v.status_of(p) == "rejected" and "rera_verified_no" not in p["branding_data"]
    await v.set_status(db, "OWNER", "A", "pending", None, None, NOW)
    assert "rera_check" not in await prof(db)


async def test_the_owner_list_puts_agents_waiting_for_a_check_first():
    db = await setup(rera_agent_no="A52100000001")
    col = db.get_collection("agent_public_profiles")
    await col.insert_one({"agent_id": "B", "slug": "bina", "agent_name": "Bina", "branding_data": {}})
    await col.insert_one({"agent_id": "C", "slug": "chet", "agent_name": "Chet", "branding_data": {"rera_agent_no": "A3"}})
    await v.set_status(db, "OWNER", "C", "verified", PAGE, None, NOW)
    assert [(r["agent_id"], r["status"]) for r in await v.checks(db)] == [("A", "pending"), ("B", "pending"), ("C", "verified")]
