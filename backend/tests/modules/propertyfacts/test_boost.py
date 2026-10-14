"""The master boost pair: made in the marketing run after the posts, never failing it; boosted, remade and counted."""
from datetime import timedelta
from pathlib import Path

from app.modules.propertyfacts import boost, jobs
from app.modules.reels.compose import PHONE_RE, TextLine

from . import test_jobs
from .test_jobs import LISTING, NOW, setup
from .test_jobs_update import change, finish, first_run, photo, tick


def texts(scene):
    return [l.text if isinstance(l, TextLine) else l for l in scene.lines]


async def made(tmp_path, monkeypatch, listing=LISTING):
    monkeypatch.setenv("WHATSAPP_PUBLIC_NUMBER", "9876543210")
    db, runs, _, _ = await setup(tmp_path, listing)
    await runs.create("a1", "L1")
    return db, runs, await finish(runs)


async def test_the_run_makes_the_boost_pair(tmp_path, monkeypatch):
    test_jobs.BOOSTS.clear()
    db, runs, d = await made(tmp_path, monkeypatch)
    assert d["status"] == "done" and d["posts"]
    b = jobs.run_out(d, "https://api.x")["boost"]
    assert b["state"] == "ready" and b["error"] is None and b["ready_at"] is None
    assert set(b) >= {"reel", "carousel", "copy", "wa_prefill", "wa_link", "tracked_link", "codes", "guide", "meta_open_url",
                      "reel_permalink", "boosted_at", "daily_spend_inr", "days"}
    assert b["reel"]["video_url"].startswith("https://api.x/uploads/campaigns/L1/") and b["reel"]["duration_s"] < 29
    assert 3 <= len(b["carousel"]["images"]) <= 6 and b["carousel"]["zip_url"].endswith(".zip")
    for u in b["carousel"]["images"] + [b["carousel"]["zip_url"]]:
        assert (tmp_path / u[len("https://api.x/uploads/"):]).is_file()
    # the reel: the hook first (price and place), every beat at most 7 words, no phone number, the WhatsApp end card last
    scenes = test_jobs.BOOSTS[-1]
    hook = texts(scenes[0])[0]
    assert "₹32.3L" in hook and ("Ranjangaon" in hook or "MIDC" in hook or "IndoSpace" in hook) and len(hook.split()) <= 7
    assert all(len(texts(s)[0].split()) <= 7 for s in scenes[1:] if s.lines)
    assert not any(PHONE_RE.search(t) for s in scenes for t in texts(s))
    assert any("P52100076768" in t for s in scenes for t in texts(s))           # registered: the proof card
    assert texts(scenes[-1])[0] == boost.END_LINE
    # copy, links, guide
    assert len(b["copy"]["reel"]["primary_text"]) <= 125 and len(b["copy"]["reel"]["headline"]) <= 40
    assert b["copy"]["post"]["primary_text"].startswith("Saw the Gulmohar City video?") and b["copy"]["cta"] == "WHATSAPP_MESSAGE"
    links = db.get_collection("interest_links").docs
    assert {(l["ref"], l["channel"]) for l in links} >= {("campaign-L1-boost_reel", "boost"), ("campaign-L1-boost_post", "boost")}
    assert b["wa_prefill"] == f"Hi, I'm interested in Gulmohar City Ranjangaon [ref {b['codes']['reel']}]"
    assert b["wa_link"].startswith("https://wa.me/919876543210?text=Hi%2C") and b["tracked_link"].endswith("/i/" + b["codes"]["reel"])
    assert b["guide"]["radius_km"] == 25 and b["guide"]["daily_budget_inr"] == 250 and b["guide"]["days"] == 5
    assert b["guide"]["carousel_daily_inr"] == 150 and b["guide"]["carousel_delay_days"] == 2


async def test_a_boost_failure_never_fails_the_run(tmp_path, monkeypatch):
    monkeypatch.setenv("WHATSAPP_PUBLIC_NUMBER", "9876543210")
    db, runs, _, _ = await setup(tmp_path)

    def boom(scenes, out):
        raise RuntimeError("ffmpeg missing")
    runs.boost_renderer = boom
    await runs.create("a1", "L1")
    d = await finish(runs)
    assert d["status"] == "done" and d["posts"] and d["error"] in (None, "")
    assert d["boost"]["state"] == "failed" and "ffmpeg missing" in d["boost"]["error"]


async def test_boosted_then_counted_then_finished(tmp_path, monkeypatch):
    db, runs, d = await made(tmp_path, monkeypatch)
    out = await runs.boost("a1", "L1", 250, 5)
    assert out["boost"]["state"] == "boosted" and out["boost"]["daily_spend_inr"] == 250
    codes = out["boost"]["codes"]
    ev = db.get_collection("interest_events")
    for t in ("click", "click", "interest"):
        await ev.insert_one({"code": codes["reel"], "type": t, "anon_id": "x", "ts": NOW})
    runs.now = lambda: NOW + timedelta(days=1, hours=1)
    res = await boost.results(db, await runs.latest("a1", "L1"), [{"clicks": 4, "interests": 1}], runs.now())
    assert res["boost_results"] == {"clicks": 2, "interests": 1, "spend_inr": 500, "cost_per_enquiry": 500}
    assert res["organic"] == {"clicks": 4, "interests": 1}
    runs.now = lambda: NOW + timedelta(days=6)
    assert (await runs.latest("a1", "L1"))["boost"]["state"] == "finished"


async def test_remake_runs_in_the_background(tmp_path, monkeypatch):
    db, runs, d = await made(tmp_path, monkeypatch)
    first = d["boost"]["reel"]["video_url"]
    runs.now = lambda: NOW + timedelta(minutes=30)
    r = await runs.remake_boost("a1", "L1")
    assert r["boost"]["state"] == "making"
    assert await runs.run_once()
    again = await runs.latest("a1", "L1")
    assert again["boost"]["state"] == "ready" and again["boost"]["reel"]["video_url"] != first
    assert again["boost"]["codes"] == d["boost"]["codes"]                         # the same tracked links
    assert not await runs.run_once()


async def test_an_update_remakes_the_boost_only_when_what_it_uses_changed(tmp_path, monkeypatch):
    monkeypatch.setenv("WHATSAPP_PUBLIC_NUMBER", "9876543210")
    db, runs, done = await first_run(tmp_path)
    before = done["boost"]
    assert before["state"] == "ready"
    await change(db, media=[photo(tmp_path)])                    # a new photo: the reel and the first card show it
    run, created = await runs.create("a1", "L1")
    assert created and run["mode"] == "update"
    d = await finish(runs)
    assert d["boost"]["state"] == "ready" and d["boost"]["key"] != before["key"]
    tick(runs)
    await change(db, price_inr=3330000)                          # the price is on the hook: remade
    await runs.create("a1", "L1")
    d2 = await finish(runs)
    assert d2["boost"]["key"] != d["boost"]["key"] and "₹33.3L" in d2["boost"]["copy"]["reel"]["primary_text"]


def test_guide_by_area():
    assert boost.guide("Kharadi")["daily_budget_inr"] == 400 and boost.guide("Keshav Nagar")["radius_km"] == 15
    assert boost.guide("Shikrapur")["radius_km"] == 25 and boost.guide("Baner")["daily_budget_inr"] == 300
    assert boost.guide("Baner")["age_min"] == 28 and boost.guide("Baner")["age_max"] == 55


async def test_copy_in_the_run_language(tmp_path, monkeypatch):
    monkeypatch.setenv("WHATSAPP_PUBLIC_NUMBER", "9876543210")
    db, runs, _, _ = await setup(tmp_path)
    await runs.create("a1", "L1", language="mr")
    d = await finish(runs)
    c = d["boost"]["copy"]
    assert "WhatsApp" in c["reel"]["primary_text"] and "रांजणगाव" in c["reel"]["headline"]
    assert len(c["post"]["primary_text"]) <= 125
