"""Plans, maps and renders from the builder's brochure (docs/MARKETING_ARCHITECTURE_REVIEW.md §5.1 step 6, S4): pages whose
text says what picture they hold are kept as large images, the agent says "use" or "don't use", a used floor plan carries a
post with its configuration and carpet area, and a render is only ever shown labelled "Artist's impression"."""
from PIL import Image

from app.modules.creative import art_director, copywriter, strategist
from app.modules.creative.layouts import render_layout
from app.modules.creative.guards import problems_in
from app.modules.propertyfacts import brochure, campaign, jobs
from app.modules.propertyfacts import brochure_parse as bp
from app.modules.propertyfacts.facts import Reading, sheet

from .pdfs import GULMOHAR, text_pdf
from .test_brochure import api, make

COVER = ["Gulmohar Heights", "Artist's impression"]
PLAN = ["TYPICAL FLOOR PLAN", "2 BHK", "Living 10'0\" x 14'0\"", "Kitchen 8'0\" x 9'0\"", "Bedroom 10'0\" x 11'0\""]
MASTER = ["MASTER PLAN", "1. Entrance gate  2. Clubhouse  3. Swimming pool"]
MAP = ["LOCATION MAP", "Map not to scale"]
LEGAL = ["Disclaimer: all images are artist's impression. This is not an offer or a contract.",
         "The promoter may change the plans as approved by the authorities."]
BROCHURE_PAGES = [COVER, GULMOHAR[1], PLAN, MASTER, MAP, LEGAL, None]


# ---- which pages hold pictures --------------------------------------------------------------------------------------------
def test_page_text_says_what_picture_it_holds():
    kind = lambda lines: bp.image_kind("\n".join(lines))  # noqa: E731
    assert kind(PLAN) == "floor_plan" and kind(["Unit Plan", "3 BHK"]) == "floor_plan"
    assert kind(["2 BHK", "M.Bed 11'0\" x 12'0\"", "Kitchen 8'0\" x 9'0\"", "Toilet"]) == "floor_plan"   # no heading
    assert kind(MASTER) == "master_plan" and kind(["Site layout"]) == "master_plan" and kind(["Layout"]) == "master_plan"
    assert kind(MAP) == "location_map" and kind(["Route map"]) == "location_map"
    assert kind(COVER) == "render" and kind(["Artistic impression of the clubhouse"]) == "render"
    assert kind(["3D view of tower A"]) == "render"
    assert kind(LEGAL) == "" and kind(GULMOHAR[4]) == ""        # a disclaimer saying "artist's impression" is not a render
    assert kind(GULMOHAR[1]) == "" and kind(["Floor plan"] + ["word " * 300]) == ""   # amenities; a text-heavy page
    assert bp.plan_configs("2 BHK and 3 BHK | 1 RK") == ["2 BHK", "3 BHK", "1 RK"]


def test_plans_and_renders_are_kept_as_large_images(tmp_path):
    read = brochure.read_pdf(text_pdf(BROCHURE_PAGES), tmp_path)
    assert [(n, k) for n, k, _ in read.images] == [(1, "render"), (3, "floor_plan"), (4, "master_plan"), (5, "location_map")]
    assert read.images[1][2] == ["2 BHK"]
    for n, _, _ in read.images:
        with Image.open(tmp_path / f"i{n}.jpg") as im:
            assert im.format == "JPEG" and max(im.size) == brochure.IMAGE_LONG_SIDE
    assert not (tmp_path / "i2.jpg").exists() and not (tmp_path / "i6.jpg").exists()
    again = brochure.read_pdf(text_pdf(BROCHURE_PAGES), tmp_path / "again")
    assert again.images == read.images                       # deterministic


# ---- the kit and the API --------------------------------------------------------------------------------------------------
async def test_the_kit_lists_images_pending_and_the_agent_decides(tmp_path):
    db, kits, _ = await make(tmp_path)
    kit = brochure.kit_out(await kits.upload("a1", "L1", "g.pdf", text_pdf(BROCHURE_PAGES)))
    assert [(i["id"], i["page"], i["kind"], i["state"]) for i in kit["images"]] == [
        ("i1", 1, "render", "pending"), ("i3", 3, "floor_plan", "pending"), ("i4", 4, "master_plan", "pending"),
        ("i5", 5, "location_map", "pending")]
    assert kit["images"][0]["label"] == "Artist's impression" and kit["images"][1]["label"] is None
    assert kit["images"][1]["url"] == "/api/v1/listings/L1/brochure/images/i3.jpg"
    stored = await kits.current("L1")
    assert brochure.usable_images(stored, tmp_path) == []    # nothing is used until the agent says so
    await kits.set_image("a1", "L1", "i3", "confirmed")
    await kits.set_image("a1", "L1", "i1", "confirmed")
    await kits.set_image("a1", "L1", "i4", "dropped")
    used = brochure.usable_images(await kits.current("L1"), tmp_path)
    assert [(u["id"], u["kind"], u["label"]) for u in used] == [("i1", "render", "Artist's impression"), ("i3", "floor_plan", "")]
    assert used[1]["configs"] == ["2 BHK"] and all(u["path"].endswith(f"{u['id']}.jpg") for u in used)


async def test_old_kits_without_images_still_read(tmp_path):
    db, kits, _ = await make(tmp_path)
    doc = await kits.upload("a1", "L1", "g.pdf", text_pdf(GULMOHAR))
    doc.pop("images")
    assert brochure.kit_out(doc)["images"] == [] and brochure.usable_images(doc, tmp_path) == []


async def test_api_images(tmp_path):
    _, kits, _ = await make(tmp_path)
    c = api(kits)
    kit = c.post("/api/v1/listings/L1/brochure", files={"file": ("g.pdf", text_pdf(BROCHURE_PAGES), "application/pdf")}).json()
    assert {i["id"] for i in kit["images"]} == {"i1", "i3", "i4", "i5"}
    r = c.patch("/api/v1/listings/L1/brochure/images/i3", json={"state": "confirmed"})
    assert r.status_code == 200 and next(i for i in r.json()["images"] if i["id"] == "i3")["state"] == "confirmed"
    assert set(r.json()) >= {"facts", "registration", "images"}               # the same kit, with images added
    r = c.patch("/api/v1/listings/L1/brochure/images/i3", json={"state": "dropped"})
    assert next(i for i in r.json()["images"] if i["id"] == "i3")["state"] == "dropped"
    assert c.patch("/api/v1/listings/L1/brochure/images/i3", json={"state": "maybe"}).status_code == 422
    assert c.patch("/api/v1/listings/L1/brochure/images/i3", json={"state": "confirmed", "x": 1}).status_code == 422
    assert c.patch("/api/v1/listings/L1/brochure/images/i9", json={"state": "confirmed"}).status_code == 404
    img = c.get("/api/v1/listings/L1/brochure/images/i3.jpg")
    assert img.status_code == 200 and img.headers["content-type"] == "image/jpeg" and img.content[:2] == b"\xff\xd8"
    assert img.headers["cache-control"].startswith("private")
    assert c.get("/api/v1/listings/L1/brochure/images/i2.jpg").status_code == 404     # a text page is no image
    assert c.get("/api/v1/listings/L1/brochure/images/..%2Fp1.jpg").status_code == 404
    other = api(kits, user="a2")
    assert other.get("/api/v1/listings/L1/brochure/images/i3.jpg").status_code == 404
    assert other.patch("/api/v1/listings/L1/brochure/images/i3", json={"state": "confirmed"}).status_code == 404


# ---- into the campaign ------------------------------------------------------------------------------------------------------
def plan_file(tmp_path, name="i3.jpg", size=(1600, 1130)) -> str:
    p = tmp_path / name
    Image.new("RGB", size, "white").save(p, "JPEG")
    return str(p)


def listing_sheet(**over):
    base = dict(project_name="Gulmohar Heights", locality="Ranjangaon", property_type="apartment", price_inr=4500000,
                bhk=2, carpet_sqft=650)
    base.update(over)
    rs = [Reading(k, v, "listing") for k, v in base.items() if v is not None]
    rs += [Reading("brochure.carpet_area", ["2 BHK: 650 sq ft carpet", "3 BHK: 890 sq ft carpet"], "brochure")]
    return sheet(rs)


def test_a_used_floor_plan_carries_the_configuration_and_carpet_area(tmp_path):
    plan = {"kind": "floor_plan", "path": plan_file(tmp_path), "configs": ["2 BHK"], "label": ""}
    assert "floor_plan" not in dict(campaign.plan(listing_sheet()))                       # no image: no post
    b = dict(campaign.plan(listing_sheet(), images=[plan]))["floor_plan"]
    hook = next(iter(b.hooks.values()))
    assert hook == "The 2 BHK floor plan: 650 sq ft carpet" and problems_in(hook, b.corpus()) == []
    assert b.plan_image == plan["path"] and b.plan_label == "Floor plan from the builder's brochure" and b.plan_fit == "contain"
    assert b.formats() == ["plan"] and "builder's brochure" in b.writer_note
    assert "number not in facts: 700" in problems_in("2 BHK: 700 sq ft carpet.", b.corpus())   # the guards stay
    # a plan of another configuration is not this listing's plan
    other = {**plan, "configs": ["3 BHK"]}
    assert "floor_plan" not in dict(campaign.plan(listing_sheet(), images=[other]))
    # no listing area: the confirmed brochure claim, attributed
    b = dict(campaign.plan(listing_sheet(carpet_sqft=None), images=[plan]))["floor_plan"]
    assert "as per the builder's brochure" in b.facts[0].lower() and "650 sq ft" in b.facts[0]
    # a plot has no floor plan post; a dropped or missing file is never used
    assert "floor_plan" not in dict(campaign.plan(listing_sheet(property_type="plot"), images=[plan]))
    assert "floor_plan" not in dict(campaign.plan(listing_sheet(), images=[{**plan, "path": str(tmp_path / "gone.jpg")}]))


def _render(brief, channel="instagram"):
    angle = strategist.rule_angle(brief, "buyer", channel, 0, [])
    copy = copywriter.rule_copy(angle, brief)
    design = art_director.choose(copy, angle, [], 0, brief.photo)
    return copy, design, render_layout(copy, design)


def test_a_render_is_always_labelled_artists_impression(tmp_path):
    render = {"kind": "render", "path": plan_file(tmp_path, "i1.jpg", (1600, 1000)), "configs": [], "label": "Artist's impression"}
    b = dict(campaign.plan(listing_sheet(), images=[render]))["first_look"]
    assert b.plan_label == "Artist's impression" and b.plan_fit == "cover" and b.formats() == ["plan"]
    for channel in ("instagram", "facebook"):
        copy, design, out = _render(b, channel)
        assert design.layout == "plan_full" and len(out) == 1
        assert any(i.text == "Artist's impression" for i in out[0].items), [i.text for i in out[0].items]
    # the label is on the image even if someone passes another one: the angle writes it, not the brochure kit
    b = dict(campaign.plan(listing_sheet(), images=[{**render, "label": ""}]))["first_look"]
    assert b.plan_label == "Artist's impression"


def test_the_plan_card_shows_the_plan_whole_and_full_width(tmp_path):
    im = Image.new("RGB", (1600, 1130), "white")
    for x in range(0, 1600, 4):
        for y in (0, 1, 2, 3, 1126, 1127, 1128, 1129):
            im.putpixel((x, y), (0, 0, 0))
    p = tmp_path / "plan.jpg"
    im.save(p, "JPEG", quality=95)
    b = dict(campaign.plan(listing_sheet(), images=[{"kind": "floor_plan", "path": str(p), "configs": ["2 BHK"]}]))["floor_plan"]
    copy, design, out = _render(b)
    r = out[0]
    assert r.img.size == (1080, 1350) and not [i for i in r.items if i.truncated]
    assert any(i.text == "Floor plan from the builder's brochure" for i in r.items)
    mid = r.img.getpixel((2, 800))          # the image runs edge to edge: white paper at the card's left edge
    assert min(mid) > 230, mid


async def test_a_brochure_plan_campaign_renders_guard_clean(tmp_path):
    images = [{"kind": "floor_plan", "path": plan_file(tmp_path), "configs": ["2 BHK"]},
              {"kind": "render", "path": plan_file(tmp_path, "i1.jpg"), "configs": []}]
    dropped = {}
    packs = dict(await campaign.make(listing_sheet(), tmp_path / "out", dropped=dropped, images=images))
    assert {"overview", "price_reveal", "floor_plan", "first_look"} <= set(packs), dropped   # a 2 BHK's hooks name it; so do its facts
    assert packs["floor_plan"].design["layout"] == "plan_full" and packs["floor_plan"].design["format"] == "plan"
    assert "650 sq ft" in packs["floor_plan"].caption


async def test_marketing_runs_use_only_the_owners_confirmed_images(tmp_path):
    db, kits, _ = await make(tmp_path)
    await kits.upload("a1", "L1", "g.pdf", text_pdf(BROCHURE_PAGES))
    runs = jobs.MarketingRuns(db, tmp_path)
    assert await runs._brochure_images("a1", "L1") == []
    await kits.set_image("a1", "L1", "i3", "confirmed")
    assert [i["id"] for i in await runs._brochure_images("a1", "L1")] == ["i3"]
    assert await runs._brochure_images("a2", "L1") == []     # another agent's run never takes this brochure
