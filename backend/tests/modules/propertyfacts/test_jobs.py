"""Start marketing: step 1 (facts and page) always before step 2 (posts); one job per listing at a time."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.modules.propertyfacts import jobs
from app.modules.propertyfacts.store import FactsStore

from ..fakes import FakeDb
from .test_register_and_store import RECORD, Db, Register, WithRegister

NOW = datetime(2026, 10, 6, 12, 0)
RENDERED = []


def fake_ad_reel(script, pictures, out, kicker=None):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"mp4")
    RENDERED.append((out.name, script, kicker))
    return out


BOOSTS = []


def fake_boost_reel(scenes, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"mp4")
    poster = out.with_name(out.stem + "-cover.jpg")
    poster.write_bytes(b"jpg")
    BOOSTS.append(scenes)
    return {"video": out, "poster": poster, "seconds": round(sum(s.seconds for s in scenes), 1)}


class FakeReelJobs:
    """The listing reel queue: the walkthrough is queued, then rendered by its own worker."""

    def __init__(self):
        self.docs = {}
        self.jobs = self

    async def create(self, agent_id, listing_id, lang, again=False, style="tour"):
        self.asked = {"lang": lang, "style": style}
        doc = {"_id": "reel1", "status": "queued", "video_path": None}
        self.docs[doc["_id"]] = doc
        return doc, True

    async def find_one(self, flt):
        return self.docs.get(flt["_id"])

    def render(self):
        self.docs["reel1"].update(status="done", video_path="/uploads/reels/listing-L1-en-reel1.mp4")
LISTING = {"_id": "L1", "agent_id": "a1", "status": "live", "title": "Plot in Gulmohar City", "transaction": "sale",
           "property_type": "plot", "price_inr": 3230000, "carpet_sqft": 1927, "locality": "Ranjangaon", "city": "Pune",
           "project_name": "Gulmohar City", "media": []}


PROJECT_URL = "https://avasetu.in/projects/gulmohar-city-ranjangaon"
PAGES = {"P52100076768": {"slug": "gulmohar-city-ranjangaon", "path": "/projects/gulmohar-city-ranjangaon",
                          "url": PROJECT_URL, "indexable": False}}


async def page_for(db, regno):
    return PAGES.get(regno)


def with_photos(tmp_path, n=2, listing=LISTING):
    from PIL import Image
    (tmp_path / "images").mkdir(exist_ok=True)
    media = []
    for i in range(n):
        Image.new("RGB", (64, 48), (40 + 60 * i, 120, 200 - 50 * i)).save(tmp_path / "images" / f"p{i}.jpg")
        media.append({"kind": "image", "url": f"/uploads/images/p{i}.jpg", "order": i})
    return {**listing, "media": media}


async def setup(tmp_path, listing=LISTING, fail_posts=False, pages=page_for):
    db = FakeDb()
    await db.get_collection("listings").insert_one(dict(listing))
    await db.get_collection("agent_public_profiles").insert_one({"agent_id": "a1", "slug": "priya"})
    clients = WithRegister(Register(RECORD))
    runs = jobs.MarketingRuns(db, tmp_path, "https://avasetu.in", clients_factory=lambda: clients, now=lambda: NOW,
                              ad_renderer=fake_ad_reel, reel_jobs=FakeReelJobs(), facts_store=clients.facts_store,
                              page_for=pages, boost_renderer=fake_boost_reel)
    one = runs.run_once

    async def run_once():  # these listings carry no files: go on without, as the agent would
        ran = await one()
        d = await runs._latest({"listing_id": listing["_id"]})
        if d and d["status"] == "asking" and [q["key"] for q in d["questions"]] == ["files"]:
            await runs.answer(d["agent_id"], d["listing_id"], "files", "skip")
            await one()
        return ran
    runs.run_once = run_once
    if fail_posts:
        async def boom(*a, **k):
            raise RuntimeError("render failed")
        runs_make = jobs.campaign.make
        jobs.campaign.make = boom
        return db, runs, clients, runs_make
    return db, runs, clients, None


async def test_facts_then_posts(tmp_path):
    db, runs, clients, _ = await setup(tmp_path)
    doc, created = await runs.create("a1", "L1")
    assert created and doc["status"] == "queued"
    again, created2 = await runs.create("a1", "L1")
    assert not created2 and again["_id"] == doc["_id"]          # one at a time
    assert await runs.run_once()
    d = await runs.latest("a1", "L1")
    assert d["status"] == "done" and d["facts_done_at"] == NOW
    assert d["facts"]["maharera"] == "P52100076768" and d["facts"]["usable"] > 10
    assert d["page_url"] == PROJECT_URL                                   # a registered project: its own page is the link
    assert d["listing_url"] == "https://avasetu.in/agent/priya/listings/L1"
    assert len(d["posts"]) >= 10 and all(i.startswith("/uploads/campaigns/L1/") for p in d["posts"] for i in p["images"])
    assert (await clients.facts_store.get("P52100076768"))["listing_id"] == "L1"     # the knowledge base is kept
    assert all("Full details of Gulmohar City, Ranjangaon, with its MahaRERA record: link in bio." in p["caption"]
               for p in d["posts"])
    out = jobs.run_out(d, "https://api.avasetu.in/")
    assert out["posts"][0]["images"][0].startswith("https://api.avasetu.in/uploads/campaigns/L1/")


async def test_posts_failing_keeps_the_facts(tmp_path):
    db, runs, clients, real = await setup(tmp_path, fail_posts=True)
    try:
        await runs.create("a1", "L1")
        await runs.run_once()
    finally:
        jobs.campaign.make = real
    d = await runs.latest("a1", "L1")
    assert d["status"] == "failed" and d["facts_done_at"] == NOW and d["facts"]["maharera"] == "P52100076768"
    assert d["error"].startswith("The facts are saved")
    assert await clients.facts_store.get("P52100076768")


async def test_only_published_listings_and_owner(tmp_path):
    db, runs, _, _ = await setup(tmp_path, {**LISTING, "status": "draft"})
    with pytest.raises(jobs.RunError) as e:
        await runs.create("a1", "L1")
    assert e.value.status_code == 409
    with pytest.raises(jobs.RunError) as e:
        await runs.create("someone-else", "L1")
    assert e.value.status_code == 404


async def test_a_done_run_is_reused_until_the_listing_changes_or_again(tmp_path):
    db, runs, _, _ = await setup(tmp_path)
    first, _ = await runs.create("a1", "L1")
    await runs.run_once()
    same, created = await runs.create("a1", "L1")
    assert not created and same["_id"] == first["_id"]
    _, created = await runs.create("a1", "L1", again=True)
    assert created


async def test_an_interrupted_run_is_failed_later(tmp_path):
    db, runs, _, _ = await setup(tmp_path)
    await runs.create("a1", "L1")
    await runs.claim()
    later = jobs.MarketingRuns(db, tmp_path, now=lambda: NOW + timedelta(hours=1))
    await later.fail_stale()
    d = await later.latest("a1", "L1")
    assert d["status"] == "failed" and "interrupted" in d["error"]


async def test_send_to_calendar_plans_rows_for_approval(tmp_path):
    from datetime import timezone

    from app.modules.calendar.store import Store as CalendarStore
    from app.modules.propertyfacts import schedule
    db, runs, _, _ = await setup(tmp_path, listing=with_photos(tmp_path))   # 2 photos: the walkthrough reel is queued
    with pytest.raises(jobs.RunError):                       # nothing to send before the posts exist
        await runs.to_calendar("a1", "L1")
    await runs.create("a1", "L1")
    await runs.run_once()
    cal = CalendarStore(db)
    other = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)       # 19:30 IST on the 8th: blocks that evening on Instagram
    await cal.add("brand-post", "instagram", "x", "a.png", other, status="planned")
    out = await runs.to_calendar("a1", "L1")
    n = len(out["posts"])
    rows = [r for r in await cal.all() if r["slug"].startswith("campaign-L1-")]
    posts = [r for r in rows if r["kind"] == "post"]
    reels = [r for r in rows if r["kind"] == "reel"]
    ads = [r for r in reels if r["slug"].endswith("-ad")]
    assert len(ads) == 2 * min(jobs.AD_REELS, n) and all(r["status"] == "planned" for r in rows)   # a post goes out as its ad reel
    assert len(posts) == 2 * (n - min(jobs.AD_REELS, n) + 1)                                      # the overview also as a post
    assert all(r["creative"]["experiment"] == "ad_reel" and r["creative"]["variant"] for r in ads)
    assert all(r["video"].startswith("campaigns/L1/") and r["video"].endswith(".mp4") for r in reels)
    assert all(r["agent_id"] == "a1" and r["listing_id"] == "L1" for r in rows)
    ig = sorted((r for r in rows if r["channel"] == "instagram"), key=lambda r: r["due_at"])
    assert ig[0]["slug"] == "campaign-L1-overview-ad"
    when = [r["due_at"].astimezone(schedule.IST).strftime("%m-%d %H:%M") for r in ig[:4]]
    # two a day (11:00 and 19:00 IST); the 8th's 19:00 is within 6 h of the brand post at 19:30, so the next free slot follows
    assert when == ["10-07 11:00", "10-07 19:00", "10-08 11:00", "10-09 11:00"]
    assert all(not i.startswith("/") and i.startswith("campaigns/L1/") for r in posts for i in r["images"])
    fb = next(r for r in rows if r["channel"] == "facebook_page")
    assert PROJECT_URL + "?src=fb_" in fb["caption"] and "link in bio" not in fb["caption"]
    assert "link in bio" in ig[0]["caption"]
    again = await runs.to_calendar("a1", "L1")                # pressing twice adds nothing
    assert len([r for r in await cal.all() if r["slug"].startswith("campaign-L1-")]) == 2 * n + 2
    assert len(again["calendar"]) == 2 * n + 2
    assert jobs.run_out(again)["calendar"][0]["due_at"] == "2026-10-07T05:30:00Z"   # 11 am IST
    # the walkthrough reel renders later (its own worker): sending again then adds it on both channels
    runs.reel_jobs.render()
    d = await runs.latest("a1", "L1")
    assert next(r for r in d["reels"] if r["kind"] == "walkthrough")["status"] == "done"
    await runs.to_calendar("a1", "L1")
    walk = [r for r in await cal.all() if r["slug"] == "campaign-L1-walkthrough"]
    assert {r["channel"] for r in walk} == {"instagram", "facebook_page"} and walk[0]["video"] == "reels/listing-L1-en-reel1.mp4"
    assert "Full details of Gulmohar City, Ranjangaon" in next(r for r in walk if r["channel"] == "instagram")["caption"]
    style = jobs.walkthrough_style("L1")
    assert runs.reel_jobs.asked == {"lang": "en", "style": style}
    assert all(r["tags"]["experiment"] == "walkthrough_style" and r["tags"]["variant"] == style for r in walk)   # results compare the two
    assert {r["creative"]["layout"] for r in walk} == {"stacked_walkthrough_reel" if style == "stack" else "walkthrough_reel"}


async def test_reels_are_made_after_the_posts(tmp_path):
    RENDERED.clear()
    db, runs, _, _ = await setup(tmp_path)
    await runs.create("a1", "L1")
    await runs.run_once()
    d = await runs.latest("a1", "L1")
    ads = [r for r in d["reels"] if r["kind"] == "ad"]
    assert len(ads) == min(jobs.AD_REELS, len(d["posts"])) and all(k == "GULMOHAR CITY" for _, _, k in RENDERED)
    assert [r["angle"] for r in ads] == [p["angle"] for p in d["posts"][:len(ads)]]
    assert ads[0]["script"]["hook"] and "INFO" in ads[0]["caption"] and ads[0]["format"] in ("price_reveal", "three_reasons", "pov",
                                                                                            "myth_fact", "checklist")
    out = jobs.run_out(d, "https://api.avasetu.in")
    assert out["reels"][0]["video"].startswith("https://api.avasetu.in/uploads/campaigns/L1/")


async def test_each_reel_is_saved_as_it_is_made(tmp_path):
    RENDERED.clear()
    db, runs, _, _ = await setup(tmp_path)
    await runs.create("a1", "L1")
    seen = []
    orig = runs._set

    async def spy(jid, **f):
        if "reels" in f:
            seen.append(len(f["reels"]))
        return await orig(jid, **f)
    runs._set = spy
    await runs.run_once()
    d = await runs.latest("a1", "L1")
    ads = [r for r in d["reels"] if r["kind"] == "ad"]
    assert len(ads) == min(jobs.AD_REELS, len(d["posts"]))
    assert seen[:len(ads)] == list(range(1, len(ads) + 1))   # reel i lands before reel i+1 is rendered: Studio can show them


async def test_a_reel_failure_never_loses_the_posts(tmp_path):
    def broken(*a, **k):
        raise RuntimeError("ffmpeg missing")
    db, runs, _, _ = await setup(tmp_path)
    runs.ad_renderer = broken
    await runs.create("a1", "L1")
    await runs.run_once()
    d = await runs.latest("a1", "L1")
    assert d["status"] == "done" and len(d["posts"]) >= 10
    assert [r["kind"] for r in d["reels"]] == ["walkthrough"]


async def test_edit_a_post_updates_planned_rows_only(tmp_path):
    from app.modules.calendar.store import Store as CalendarStore
    db, runs, _, _ = await setup(tmp_path)
    await runs.create("a1", "L1")
    await runs.run_once()
    await runs.to_calendar("a1", "L1")
    cal = CalendarStore(db)
    rows = {(r["channel"], r["slug"]): r for r in await cal.all()}
    approved = rows[("facebook_page", "campaign-L1-price_reveal-ad")]
    await cal.approve(approved["_id"])                              # the owner already approved the Facebook one
    text = "Our plot at Gulmohar City, Ranjangaon: ₹32.3 lakh.\n\nFull details of Gulmohar City, Ranjangaon, with its MahaRERA record: link in bio."
    run, problems = await runs.edit_post("a1", "L1", "price_reveal", text)
    assert problems == [] and run["synced"] == 1
    post = next(p for p in run["posts"] if p["angle"] == "price_reveal")
    assert post["caption"] == text and post["edited"]
    assert text.splitlines()[0] in (await cal.get(rows[("instagram", "campaign-L1-price_reveal-ad")]["_id"]))["caption"]   # the reel takes the new text
    assert (await cal.get(approved["_id"]))["caption"] == approved["caption"]        # approved rows are never changed
    _, problems = await runs.edit_post("a1", "L1", "price_reveal", "Only ₹25 lakh! Best deal, call 9876543210")
    assert any("number not in facts" in p for p in problems) and "phone number" in problems and "hype word" in problems
    with pytest.raises(jobs.RunError):
        await runs.edit_post("a1", "L1", "price_reveal", "   ")
    with pytest.raises(jobs.RunError) as e:
        await runs.edit_post("a1", "L1", "no_such_angle", "x")
    assert e.value.status_code == 404


async def test_improve_a_post_with_a_note(tmp_path):
    from ..creative.helpers import FakeLlm
    db, runs, _, _ = await setup(tmp_path)
    await runs.create("a1", "L1")
    await runs.run_once()
    llm = FakeLlm(text_reply="")
    runs.llm_factory = lambda: llm
    run = await runs.redo_post("a1", "L1", "near_work", "mention the MIDC jobs")
    post = next(p for p in run["posts"] if p["angle"] == "near_work")
    assert post["redos"] == 1 and post["note"] == "mention the MIDC jobs"
    assert all("/near_work/redo1/" in i for i in post["images"])
    assert any("The agent asked for this change: mention the MIDC jobs" in c[2] for c in llm.calls)   # the note reached the writer
    assert (await runs.latest("a1", "L1"))["posts"] == run["posts"]


async def test_page_first_no_posts_until_the_project_page_exists(tmp_path):
    async def no_page(db, regno):
        return None
    db, runs, clients, _ = await setup(tmp_path, pages=no_page)
    await runs.create("a1", "L1")
    await runs.run_once()
    d = await runs.latest("a1", "L1")
    assert d["status"] == "failed" and d["posts"] == [] and "project page for P52100076768 is not ready" in d["error"]
    assert d["facts"]["maharera"] == "P52100076768" and await clients.facts_store.get("P52100076768")   # the facts are kept
    reg = await db.get_collection("projects").find_one({"_id": "P52100076768"})
    assert reg and "property_facts" in reg.get("watched_by", [])          # on the watch list, so its page can be made
    # once the page exists, starting again makes the campaign with the project page as its link
    runs.page_for = page_for
    runs.now = lambda: NOW + timedelta(minutes=5)           # started again a few minutes later
    await runs.create("a1", "L1", again=True)
    await runs.run_once()
    d = await runs.latest("a1", "L1")
    assert d["status"] == "done" and d["page_url"] == PROJECT_URL and d["posts"]


async def test_a_property_without_a_registration_uses_its_listing_page(tmp_path):
    async def never(db, regno):
        raise AssertionError("no project page lookup without a MahaRERA number")
    listing = {**LISTING, "project_name": "", "rera_no": ""}
    db, runs, clients, _ = await setup(tmp_path, listing, pages=never)
    clients.register = Register()          # nothing in our register, and the search finds no project by name
    await runs.create("a1", "L1")
    await runs.run_once()
    d = await runs.latest("a1", "L1")
    assert d["page_url"] == d["listing_url"] == "https://avasetu.in/agent/priya/listings/L1"


async def test_page_first_asks_for_the_page_text_without_waiting(tmp_path):
    asked = []

    async def enrich_now(db, regno, by="campaign"):
        asked.append((regno, by))
        return True
    db, runs, _, _ = await setup(tmp_path)
    runs.enrich_now = enrich_now
    await runs.create("a1", "L1")
    await runs.run_once()
    assert asked == [("P52100076768", "campaign")] and (await runs.latest("a1", "L1"))["status"] == "done"

    async def broken(db, regno, by="campaign"):
        raise RuntimeError("loop off")
    runs.enrich_now = broken                                    # enrichment down: the campaign still goes on
    runs.now = lambda: NOW + timedelta(minutes=5)
    await runs.create("a1", "L1", again=True)
    await runs.run_once()
    assert (await runs.latest("a1", "L1"))["status"] == "done"


async def test_after_the_earlier_rows_were_skipped_sending_again_adds_the_posts(tmp_path):
    """Live 2026-10-06, Gulmohar: the campaign was made again after its first rows were skipped; Send added nothing."""
    from app.modules.calendar.store import Store as CalendarStore
    db, runs, _, _ = await setup(tmp_path)
    await runs.create("a1", "L1")
    await runs.run_once()
    cal = CalendarStore(db)
    first = await runs.to_calendar("a1", "L1")
    n = len(first["calendar"])
    for r in await cal.all():
        if r["slug"].startswith("campaign-L1-"):
            await cal.skip(r["_id"])
    await runs.to_calendar("a1", "L1")
    planned = [r for r in await cal.all() if r["slug"].startswith("campaign-L1-") and r["status"] == "planned"]
    assert len(planned) == n


async def test_walkthrough_reel_rules(tmp_path):
    """A video: no walkthrough entry (the video reel covers it). No video, fewer than 2 photos: the run's own pictures
    (brochure pages, stills) when 2 are usable, else a note asking for photos."""
    from PIL import Image
    db, runs, _, _ = await setup(tmp_path)
    reels = await runs._reels({"_id": "r", "agent_id": "a1", "listing_id": "L1"}, LISTING, [], tmp_path, "X", "")
    assert reels == [{"kind": "walkthrough", "status": "skipped", "note": jobs.WALKTHROUGH_NOTE}]
    (tmp_path / "brochure").mkdir()
    pool = []
    for i in range(2):
        f = tmp_path / "brochure" / f"page{i:02d}.jpg"
        Image.new("RGB", (64, 48), (30 + 80 * i, 140, 90)).save(f)
        pool.append(str(f))
    seen = {}

    async def create(agent_id, listing_id, lang, again=False, photos=None, style="tour"):
        seen["photos"] = photos
        return {"_id": "reel1", "status": "queued", "video_path": None}, True
    runs.reel_jobs.create = create
    reels = await runs._reels({"_id": "r", "agent_id": "a1", "listing_id": "L1"}, LISTING, [], tmp_path, "X", "", pool=pool)
    assert reels[0]["status"] == "queued" and seen["photos"] == pool
    runs._video = lambda listing: tmp_path / "v.mp4"

    async def video_reel(*a, **k):
        return {"kind": "video", "status": "done"}
    runs._video_reel = video_reel
    reels = await runs._reels({"_id": "r", "agent_id": "a1", "listing_id": "L1"}, LISTING, [], tmp_path, "X", "", pool=pool)
    assert [r["kind"] for r in reels] == ["video"]
def test_the_walkthrough_style_is_fixed_per_listing_and_splits_listings_about_evenly():
    assert all(jobs.walkthrough_style("L1") == jobs.walkthrough_style("L1") for _ in range(3))
    styles = [jobs.walkthrough_style(f"listing-{i}") for i in range(400)]
    assert set(styles) == {"tour", "stack"} and 150 < styles.count("stack") < 250


async def test_the_walkthrough_is_made_in_the_campaign_language(tmp_path, monkeypatch):
    from app.modules.reels import listing_reel
    monkeypatch.setattr(listing_reel, "listing_photos", lambda listing, uploads: [Path("a.jpg"), Path("b.jpg")])   # a listing with 2 photos
    db, runs, _, _ = await setup(tmp_path)
    await runs.create("a1", "L1", language="mr")
    await runs.run_once()
    d = await runs.latest("a1", "L1")
    walk = next(r for r in d["reels"] if r["kind"] == "walkthrough")
    assert runs.reel_jobs.asked["lang"] == "mr" and walk["language"] == "mr" and walk["style"] == jobs.walkthrough_style("L1")
    head = walk["caption"].splitlines()[0]   # the caption follows the reel's language too
    assert any("\u0900" <= ch <= "\u097f" for ch in head) and " for " not in head
