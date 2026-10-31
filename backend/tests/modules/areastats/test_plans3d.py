"""3D floor plans from checked plans (app/modules/areastats/plans3d.py)."""
import io
from datetime import datetime, timezone

from PIL import Image

from app.modules.areastats import plans3d

NOW = datetime(2026, 10, 31, 9, 0, tzinfo=timezone.utc)

# what Gemini read from Lodha Camelot's "3-BED WITH STUDY | UNIT 1" plan on lodhagroup.com (2026-10-31)
CAMELOT = {"unit_plan": True, "title": "3-BED WITH STUDY | UNIT 1", "rooms": [
    {"name": "FOYER", "printed_sqft": 45, "legend_dims": "5'0\" X 9'2\""},
    {"name": "LIVING/DINING", "printed_sqft": 342, "legend_dims": "22'0\" X 15'9\""},
    {"name": "DECK", "printed_sqft": 151, "legend_dims": "21'8\" X 7'0\""},
    {"name": "KITCHEN", "printed_sqft": 142, "legend_dims": "8'6\" X 12'7\""},
    {"name": "UTILITY", "printed_sqft": None, "legend_dims": "5'0\" X 7'0\""},
    {"name": "MASTER BEDROOM", "printed_sqft": 289, "legend_dims": "11'0\" X 17'9\" + 6'9\" X 5'5\" + 2'9\" X 2'0\""},
    {"name": "BEDROOM-02", "printed_sqft": 133, "legend_dims": "10'6\" X 12'0\" + 3'9\" X 2'0\""},
    {"name": "BEDROOM-03", "printed_sqft": 212, "legend_dims": "10'6\" X 15'9\" + 4'6\" X 2'0\""}]}


def png() -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (40, 30), "white").save(out, "PNG")
    return out.getvalue()


def test_a_legend_size_becomes_square_feet():
    assert plans3d.dims_sqft("10'6\" X 12'0\" + 3'9\" X 2'0\"") == 133.5
    assert plans3d.dims_sqft("5'0\" X 7'0\"") == 35.0
    assert plans3d.dims_sqft("") is None


def test_a_plan_whose_numbers_agree_passes_with_its_room_sizes():
    ok, why, rooms = plans3d.check(CAMELOT)
    assert ok, why
    assert {"name": "UTILITY", "sqft": 35, "dims": "5'0\" X 7'0\""} in rooms   # no size printed: the legend's area
    assert next(r for r in rooms if r["name"] == "BEDROOM-02")["sqft"] == 133


def misread(name, sqft):
    return {**CAMELOT, "rooms": [dict(r, printed_sqft=sqft) if r["name"] == name else r for r in CAMELOT["rooms"]]}


def test_a_size_far_off_its_legend_fails_the_whole_plan():
    ok, why, _ = plans3d.check(misread("MASTER BEDROOM", 829))   # 289 read as 829
    assert not ok and "MASTER BEDROOM" in why


def test_two_readings_that_differ_fail_the_plan():
    # the free model read Bedroom 2 as 153 sq ft where 133 is printed: inside the legend's range, so only a second reading shows it
    assert plans3d.check(misread("BEDROOM-02", 153))[0]
    ok, why = plans3d.same_reading(CAMELOT, misread("BEDROOM-02", 153))
    assert not ok and "BEDROOM02" in why
    assert plans3d.same_reading(CAMELOT, CAMELOT)[0]
    spaced = {**CAMELOT, "rooms": [dict(r, name=r["name"].replace("-", " -")) for r in CAMELOT["rooms"]]}
    assert plans3d.same_reading(CAMELOT, spaced)[0]   # one reading wrote "BEDROOM -02" (Camelot, 2026-10-31)
    worded = {**CAMELOT, "rooms": [dict(r, printed_sqft=f"{r['printed_sqft']} SQ.FT.") if r["printed_sqft"] else r for r in CAMELOT["rooms"]]}
    assert plans3d.same_reading(CAMELOT, worded)[0]   # the other wrote "45 SQ.FT."


def test_master_plans_and_wrong_bedroom_counts_are_not_drawn():
    assert plans3d.check({"unit_plan": False, "rooms": []})[0] is False
    assert plans3d.check({**CAMELOT, "title": "2 BHK | UNIT 4"})[0] is False


def test_a_drawing_with_a_missing_room_or_another_layout_is_refused():
    assert plans3d.verified({"missing": [], "extra": [], "same_layout": True})[0]
    assert not plans3d.verified({"missing": ["STUDY"], "extra": [], "same_layout": True})[0]
    assert not plans3d.verified({"missing": [], "extra": [], "same_layout": False})[0]
    assert not plans3d.verified({"missing": [], "extra": [], "same_layout": True, "sizes": ["207 SQ.FT."]})[0]   # a wrong size drawn in
    assert not plans3d.verified({"missing": [], "extra": [], "same_layout": True, "misspelled": ["STAFF SOON"]})[0]


async def test_a_project_gets_drawings_only_of_its_unit_plans_that_pass(tmp_path):
    (tmp_path / "project_media" / "p1").mkdir(parents=True)
    for f in ("a.webp", "m.webp"):
        (tmp_path / "project_media" / "p1" / f).write_bytes(png())
    doc = {"_id": "P1", "regno": "P1", "profile": {"plans": [
        {"path": "project_media/p1/a.webp", "alt": "Camelot 3 BHK with study floor plan", "site": "lodhagroup.com", "source": "builder"},
        {"path": "project_media/p1/m.webp", "alt": "Camelot master plan", "site": "lodhagroup.com", "source": "builder"}]}}
    asks = []

    async def read(images, prompt, models=None):
        asks.append(len(images))
        return CAMELOT if len(images) == 1 else {"missing": [], "extra": [], "same_layout": True}

    async def draw(image, prompt):
        return png()
    out = (await plans3d.make(doc, NOW, read=read, draw=draw, uploads=tmp_path))["plans_3d"]
    assert asks == [1, 1, 2]                   # read twice, checked once; the master plan is never read or drawn
    [item] = out["items"]
    assert item["label"] == "3 BHK with study" and item["source"]["site"] == "lodhagroup.com"
    assert (tmp_path / item["path"]).is_file()
    assert plans3d.public(out)["items"][0]["url"].startswith("/uploads/project_media/p1-3d/")


async def test_a_plan_drawn_before_is_kept_not_drawn_again(tmp_path):
    (tmp_path / "project_media" / "p1").mkdir(parents=True)
    (tmp_path / "project_media" / "p1" / "a.webp").write_bytes(png())
    old = {"path": "project_media/p1-3d/x.webp", "label": "3 BHK", "rooms": [], "source": {"path": "project_media/p1/a.webp"}}
    doc = {"_id": "P1", "regno": "P1", "plans_3d": {"items": [old]},
           "profile": {"plans": [{"path": "project_media/p1/a.webp", "alt": "3 BHK floor plan"}]}}

    async def never(*a, **k):
        raise AssertionError("no model call for a kept drawing")
    out = (await plans3d.make(doc, NOW, read=never, draw=never, uploads=tmp_path))["plans_3d"]
    assert out["items"] == [old] and out["tried"][0]["why"] == "kept"
