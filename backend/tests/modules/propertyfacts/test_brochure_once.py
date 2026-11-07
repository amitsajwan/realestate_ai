"""One brochure file is understood once, ever, and nothing reaches a page on a near match (docs/plan/brochure-reading.md)."""
from datetime import datetime, timedelta

from app.modules.propertyfacts import brochure as br
from app.modules.propertyfacts import brochure_once as once
from app.modules.propertyfacts import brochure_parse as bp
from app.platform import gemini

from ..fakes import FakeDb

NOW = datetime(2026, 11, 7, 12, 0)
AGENT = "a1"


def reading(numbers=("PM1260002501030",)):
    return {"pages": 2, "image_only_pages": [1, 2], "labels": {"1": {"kind": "floor_plan"}}, "numbers": list(numbers),
            "images": [{"id": "i1", "page": 1, "kind": "floor_plan", "state": "pending", "configs": ["2 BHK"], "label": ""}],
            "facts": [{"key": "carpet_area", "value": "800-835 sq ft", "page": 1, "quote": "x", "label": "Carpet area",
                       "config": "2 BHK", "by": "vision"}]}


class Reader:
    def __init__(self, fail=None):
        self.calls, self.fail = 0, fail

    async def __call__(self, data, folder, ask):
        self.calls += 1
        if self.fail:
            raise self.fail
        return reading()


async def verified(clients, rera, name="", now=None, others=()):
    return {"status": "verified", "rera_no": rera, "note": "ok"}


async def prepare(tmp_path, read, rows=(("l1", AGENT),)):
    db = FakeDb()
    (tmp_path / "documents").mkdir()
    for lid, agent in rows:
        (tmp_path / "documents" / f"{lid}.pdf").write_bytes(b"%PDF-same file")
        await db.get_collection("listings").insert_one({
            "_id": lid, "agent_id": agent, "project_name": "KP Supernova", "rera_no": "PM1260002501030",
            "media": [{"kind": "document", "url": f"https://x/uploads/documents/{lid}.pdf"}]})
    kits = br.Brochures(db, tmp_path, now=lambda: NOW)
    return db, kits, once.BrochureReads(db, tmp_path, kits, now=lambda: NOW + timedelta(minutes=1), read=read)


async def test_the_same_file_on_a_second_listing_costs_no_model_call(tmp_path, monkeypatch):
    read = Reader()
    db, kits, reads = await prepare(tmp_path, read, (("l1", AGENT), ("l2", "a2")))
    monkeypatch.setattr(br, "check_registration", verified)
    assert await reads.sweep() == 2
    assert await reads.run_once() and await reads.run_once()
    assert read.calls == 1
    assert await db.get_collection("brochures").count_documents({"status": "done"}) == 2
    assert (await reads.status("l2"))["status"] == "done"


async def test_a_brochure_seen_before_is_never_queued_again(tmp_path):
    db, kits, reads = await prepare(tmp_path, Reader())
    assert await reads.sweep() == 1
    assert await reads.sweep() == 0


async def test_a_file_that_could_not_be_read_stops_after_three_tries_and_is_never_tried_again(tmp_path):
    read = Reader(fail=once.ReadFailed("no pages"))
    db, kits, reads = await prepare(tmp_path, read)
    await reads.sweep()
    for _ in range(3):
        assert await reads.run_once()
    assert read.calls == 3 and (await reads.status("l1"))["status"] == "failed"
    assert not await reads.run_once()
    await db.get_collection("brochure_jobs").update_one({"_id": "l1:l1.pdf"}, {"$set": {"status": "queued", "tries": 0}})
    await reads.run_once()   # even queued by hand, the stored failure stands
    assert read.calls == 3


async def test_running_out_of_credit_is_not_a_try_and_it_waits(tmp_path):
    db, kits, reads = await prepare(tmp_path, Reader(fail=once.NoCredit("HTTP 402")))
    await reads.sweep()
    await reads.run_once()
    job = await db.get_collection("brochure_jobs").find_one({"_id": "l1:l1.pdf"})
    assert job["status"] == "queued" and job["tries"] == 0 and job["not_before"] > NOW + timedelta(hours=5)
    assert not await reads.run_once()


async def test_a_brochure_that_reaches_the_limit_stops_and_stays_stopped(tmp_path):
    db, kits, reads = await prepare(tmp_path, Reader(fail=once.OverCap()))
    await reads.sweep()
    await reads.run_once()
    state = await reads.status("l1")
    assert state["status"] == "failed" and "₹10" in state["note"]
    assert (await db.get_collection("brochure_reads").find_one({}))["status"] == "over_cap"


async def test_a_spent_day_waits_without_reading(tmp_path):
    read = Reader()
    db, kits, reads = await prepare(tmp_path, read)
    await db.get_collection("enrich_llm_usage").insert_one({"_id": "2026-11-07", "gemini_inr": 999999.0})
    await reads.sweep()
    await reads.run_once()
    assert read.calls == 0 and (await db.get_collection("brochure_jobs").find_one({}))["status"] == "queued"


async def test_a_brochure_for_another_number_never_reaches_the_project_page(tmp_path, monkeypatch):
    db, kits, reads = await prepare(tmp_path, Reader())
    monkeypatch.setattr(br, "check_registration", verified)
    listing = await db.get_collection("listings").find_one({"_id": "l1"})
    kit = await kits.adopt(listing, "sha", "b.pdf", reading(("PM1260002509999",)), b"%PDF")
    assert kit["registration"]["status"] == "unverified" and "this listing is PM1260002501030" in kit["registration"]["note"]


async def test_plans_are_on_the_page_until_the_agent_drops_them_but_facts_wait_for_a_tick(tmp_path, monkeypatch):
    db, kits, reads = await prepare(tmp_path, Reader())
    monkeypatch.setattr(br, "check_registration", verified)
    listing = await db.get_collection("listings").find_one({"_id": "l1"})
    kit = await kits.adopt(listing, "sha", "b.pdf", reading(), b"%PDF")
    assert kit["images"][0]["state"] == "pending" and kit["registration"]["status"] == "verified"
    assert br.confirmed(kit) == []


async def test_two_reads_of_a_number_must_agree(monkeypatch):
    monkeypatch.setattr(once, "page_jpeg", lambda *a: b"x")
    said = iter([{"box": [100, 100, 200, 400]}, {"number": "PM1260002501030"}, {"number": "P51260002501030"}])

    async def ask(images, prompt):
        return next(said)
    assert await once.read_number(b"", 1, ask) == ""


async def test_two_agreeing_reads_give_the_number(monkeypatch):
    monkeypatch.setattr(once, "page_jpeg", lambda *a: b"x")
    said = iter([{"box": [100, 100, 200, 400]}, {"number": "PM1260002501030"}, {"number": "PM1260002501030"}])

    async def ask(images, prompt):
        return next(said)
    assert await once.read_number(b"", 1, ask) == "PM1260002501030"


def test_an_area_row_whose_metres_and_feet_disagree_is_dropped():
    rows = once.checked_rows({"rows": [{"units": "301", "type": "3 BHK", "sqm": "104.98", "sqft": "1130"},
                                       {"units": "302", "type": "2 BHK", "sqm": "75.25", "sqft": "910"}]})
    assert [r["sqft"] for r in rows] == [1130.0]


def test_a_joined_flat_with_no_printed_area_is_never_a_home_type():
    facts = once.carpet_facts([], [{"title": "2 BHK UNIT PLAN", "carpet_area": "800-835 SQ. FT.", "unit_label": "F-08", "page": 16},
                                   {"title": "4 BHK UNIT PLAN", "carpet_area": None, "unit_label": "F-08+09", "page": 17}], {})
    assert [(f.config, f.value) for f in facts] == [("2 BHK", "800-835 SQ. FT.")]


def test_the_table_outranks_a_plans_heading_and_gives_a_range():
    rows = [{"type": "2 BHK", "sqft": 800.0}, {"type": "2 BHK", "sqft": 835.0}]
    facts = once.carpet_facts(rows, [{"title": "2 BHK", "carpet_area": "800 sq ft", "unit_label": "F-1", "page": 2}], {"2 BHK": 18})
    assert [(f.value, f.page) for f in facts] == [("800-835 sq ft", 18)]


async def test_a_page_the_model_cannot_read_is_skipped_but_a_money_refusal_stops_the_read(monkeypatch):
    async def slow(*a, **k):
        raise gemini.GeminiError("gemini-3 unreachable (ReadTimeout)")
    monkeypatch.setattr(gemini, "read_counted", slow)
    assert await once.asker(once.Cost())([b"x"], "p") is None

    async def broke(*a, **k):
        raise gemini.GeminiError("gemini-3 HTTP 402: no credit")
    monkeypatch.setattr(gemini, "read_counted", broke)
    try:
        await once.asker(once.Cost())([b"x"], "p")
        assert False, "a read went on with no credit"
    except once.NoCredit:
        pass


async def test_the_read_stops_at_the_limit_before_the_next_call():
    try:
        await once.asker(once.Cost(inr=once.CAP_INR))([b"x"], "p")
        assert False, "a call past the limit"
    except once.OverCap:
        pass


def test_a_page_gives_only_facts_the_kit_knows():
    facts = once.page_facts({"builder": "Kanifnath Realtors", "amenities": ["Gym", "Pool"], "towers": 2}, 3)
    assert {f.key for f in facts} == {"promoter", "amenities", "towers"} and all(f.key in bp.LABELS for f in facts)


def test_a_key_with_one_answer_keeps_the_fullest_and_a_slogan_is_no_address():
    facts = once.best_of_each([bp.Candidate("promoter", "KP", 1, "KP"), bp.Candidate("promoter", "Kanifnath Realtors", 7, "x"),
                               bp.Candidate("address", "@NIBM ANNEXE", 1, "x"), bp.Candidate("amenities", ["Gym"], 8, "x")])
    assert [(f.key, f.value) for f in facts] == [("promoter", "Kanifnath Realtors"), ("amenities", ["Gym"])]


def test_grouped_specifications_read_as_plain_text():
    [spec] = once.page_facts({"specifications": [{"category": "WINDOWS", "details": ["3 Track Sliding Window."]}]}, 21)
    assert spec.value == ["WINDOWS: 3 Track Sliding Window."]


async def test_a_brochure_with_no_number_read_stays_off_the_page_even_on_a_registered_listing(tmp_path):
    db, kits, reads = await prepare(tmp_path, Reader())
    listing = await db.get_collection("listings").find_one({"_id": "l1"})
    kit = await kits.adopt(listing, "sha", "b.pdf", reading(()), b"%PDF")
    assert kit["registration"]["status"] == "unknown" and not kit["registration"]["rera_no"]


async def test_gemini_may_name_the_box_either_way(monkeypatch):
    monkeypatch.setattr(once, "page_jpeg", lambda *a: b"x")
    said = iter([{"box_2d": [165, 859, 179, 961]}, {"number": "PC1260002501550"}, {"number": "PC1260002501550"}])

    async def ask(images, prompt):
        return next(said)
    assert await once.read_number(b"", 1, ask) == "PC1260002501550"


def test_a_table_heading_is_not_a_project_name():
    facts = once.best_of_each([bp.Candidate("project_name", "Area Statement", 1, "x")])
    assert facts == []
