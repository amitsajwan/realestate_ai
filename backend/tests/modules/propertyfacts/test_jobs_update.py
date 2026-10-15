"""A finished campaign meets a changed listing: only what the change touches is made again; edited and approved posts stay."""
from datetime import timedelta

from PIL import Image

from app.modules.calendar.store import Store as CalendarStore
from app.modules.propertyfacts import jobs

from .test_jobs import LISTING, NOW, setup

LATER = [NOW]


def tick(runs, minutes=5):
    LATER[0] = LATER[0] + timedelta(minutes=minutes)
    runs.now = lambda t=LATER[0]: t


async def finish(runs):
    """Run the queued job, answering any question (files: go on without; else the first option)."""
    await runs.run_once()
    for _ in range(10):
        d = await runs.latest("a1", "L1")
        if d["status"] != "asking":
            return d
        for q in d["questions"]:
            await runs.answer("a1", "L1", q["key"], "skip" if q["key"] == "files" else q["options"][0]["value"])
        await runs.run_once()
    return await runs.latest("a1", "L1")


async def first_run(tmp_path, listing=LISTING):
    LATER[0] = NOW
    db, runs, _, _ = await setup(tmp_path, listing)
    await runs.create("a1", "L1")
    d = await finish(runs)
    assert d["status"] == "done" and d["inputs"] and all(p["brief"] and p["photo"] == "none" for p in d["posts"])
    tick(runs)
    return db, runs, d


async def change(db, **fields):
    await db.get_collection("listings").update_one({"_id": "L1"}, {"$set": {**fields, "updated_at": LATER[0] + timedelta(minutes=1)}})


def photo(tmp_path, name="p1.jpg"):
    (tmp_path / "images").mkdir(exist_ok=True)
    Image.new("RGB", (800, 800), (120, 140, 160)).save(tmp_path / "images" / name)
    return {"kind": "image", "url": f"/uploads/images/{name}", "order": 0}


async def test_nothing_that_matters_changed_keeps_the_run(tmp_path):
    db, runs, done = await first_run(tmp_path)
    await change(db, description="new words")              # touched, but no fact the posts use
    again, created = await runs.create("a1", "L1")
    assert not created and again["_id"] == done["_id"]


async def test_a_new_video_makes_only_the_video_reel(tmp_path):
    db, runs, done = await first_run(tmp_path)
    (tmp_path / "videos").mkdir()
    (tmp_path / "videos" / "v1.mp4").write_bytes(b"mp4")
    made = []

    async def video_reel(job, listing, video, out, project, link_line):
        made.append(video.name)
        return {"kind": "video", "status": "done", "video": "/uploads/campaigns/L1/x/reels/video.mp4", "caption": "c"}
    runs._video_reel = video_reel
    await change(db, media=[{"kind": "video", "url": "/uploads/videos/v1.mp4"}])
    run, created = await runs.create("a1", "L1")
    assert created and run["mode"] == "update" and run["changes"] == ["video"] and run["base_run"] == done["_id"]
    d = await finish(runs)
    assert d["_id"] == run["_id"] and d["status"] == "done" and made == ["v1.mp4"]
    assert [(p["angle"], p["caption"], p["images"]) for p in d["posts"]] == \
           [(p["angle"], p["caption"], p["images"]) for p in done["posts"]]
    assert d["redone"] == [] and [r for r in d["reels"] if r["kind"] == "video"][0]["status"] == "done"
    same, created = await runs.create("a1", "L1")           # the update run's inputs are now the listing's
    assert not created and same["_id"] == run["_id"]


async def test_new_photos_remake_the_posts_without_one_but_not_an_edited_post(tmp_path):
    db, runs, done = await first_run(tmp_path)
    edited = done["posts"][0]
    await runs.edit_post("a1", "L1", edited["angle"], edited["caption"] + "\nOur words.")
    await change(db, media=[photo(tmp_path)])
    run, created = await runs.create("a1", "L1")
    assert created and run["changes"] == ["photos"]
    d = await finish(runs)
    posts = {p["angle"]: p for p in d["posts"]}
    kept = posts[edited["angle"]]
    assert kept["caption"].endswith("Our words.") and kept["stale"] and kept["newer"]["photo"] == "photo"
    assert kept["images"] == edited["images"]
    others = [p for a, p in posts.items() if a != edited["angle"]]
    assert others and all(p["photo"] == "photo" and not p.get("stale") for p in others)
    assert set(d["redone"]) == set(posts)
    assert jobs.run_out(d)["stale"] == [edited["angle"]]


async def test_a_fact_change_remakes_the_posts_that_say_it_and_spares_approved_ones(tmp_path):
    db, runs, done = await first_run(tmp_path)
    await runs.to_calendar("a1", "L1")
    cal = CalendarStore(db)
    rows = {(r["channel"], r["slug"]): r for r in await cal.all()}
    await cal.approve(rows[("instagram", "campaign-L1-overview")]["_id"])
    tick(runs)
    await change(db, price_inr=3500000)
    run, created = await runs.create("a1", "L1")
    assert created and run["changes"] == ["facts"] and run["calendar"]
    d = await finish(runs)
    posts, before = {p["angle"]: p for p in d["posts"]}, {p["angle"]: p for p in done["posts"]}
    assert "price_reveal" in d["redone"] and "35" in posts["price_reveal"]["caption"] and not posts["price_reveal"].get("stale")
    assert posts["overview"]["caption"] == before["overview"]["caption"] and posts["overview"]["stale"]   # approved: kept
    assert "35" in posts["overview"]["newer"]["caption"]
    if "plot_checklist" in posts:                                    # says no price: untouched
        assert "plot_checklist" not in d["redone"] and posts["plot_checklist"]["caption"] == before["plot_checklist"]["caption"]
    # the price post goes to the calendar as its ad reel (schedule.items): its planned row took the new price
    old = rows[("instagram", "campaign-L1-price_reveal-ad")]
    ig = await cal.get(old["_id"])
    assert ig["caption"] != old["caption"] and "35" in ig["caption"]
    ok = await cal.get(rows[("instagram", "campaign-L1-overview")]["_id"])
    assert ok["caption"] == rows[("instagram", "campaign-L1-overview")]["caption"]  # approved row untouched


async def test_a_new_brochure_remakes_no_post(tmp_path):
    """Posts are made from the listing, the facts and the photos, never from the PDF: a new brochure changes none of them."""
    db, runs, done = await first_run(tmp_path)
    (tmp_path / "documents").mkdir()
    (tmp_path / "documents" / "b.pdf").write_bytes(b"%PDF")
    await change(db, media=[{"kind": "document", "url": "/uploads/documents/b.pdf"}])
    run, created = await runs.create("a1", "L1")
    assert created and run["changes"] == ["brochure"]
    d = await finish(runs)
    assert d["status"] == "done" and not d["redone"] and d["posts"] == done["posts"]


async def test_again_remakes_everything_but_keeps_an_edited_post(tmp_path):
    db, runs, done = await first_run(tmp_path)
    angle = done["posts"][1]["angle"]
    await runs.edit_post("a1", "L1", angle, done["posts"][1]["caption"] + "\nMine.")
    run, created = await runs.create("a1", "L1", again=True)
    assert created and run["mode"] == "full" and run["base_run"] == done["_id"]
    d = await finish(runs)
    post = next(p for p in d["posts"] if p["angle"] == angle)
    assert post["caption"].endswith("Mine.") and post["stale"] and post["newer"]["caption"]
