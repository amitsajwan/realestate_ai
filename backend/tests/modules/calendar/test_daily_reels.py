"""The daily reel rhythm (pure plan), area-insight reels (facts, wording, drawn slides) and the stored rows (consent gate, flag)."""
import asyncio
import re
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from app.core import areas
from app.modules.calendar import adapters, area_reels, builder, library
from app.modules.calendar.plan import (GUIDE_PILLARS, area_of_slug, area_reel_slug, build_daily_plan, project_reel_slug)
from app.modules.calendar.schedule import IST, MIN_GAP, NO_REPEAT
from app.modules.calendar.store import Store
from app.modules.knowledge.grounding import project_slug_of
from app.platform.text import PHONE

from ..fakes import FakeDb

START = date(2026, 10, 12)  # a Monday
ALL = [a.key for a in areas.AREAS]


def stats(key="wagholi", projects=41, completing=((2026, 6), (2027, 12)), total=5210, booked=3100, recent=("Rohan Abhilasha 4", "Goyal My Home")):
    a = areas.get(key)
    return {"area": {"key": a.key, "name": a.name, "slug": a.slug, "tier": a.tier}, "as_of": "2026-10-04", "projects": projects,
            "completing": [{"year": y, "projects": n} for y, n in completing], "units_total": total, "units_booked": booked,
            "recent": [{"name": n, "regno": "P52100080076", "promoter": "X", "completion": "2029-10-30", "updated": "2026-09-28",
                        "url": "https://maharerait.maharashtra.gov.in/x"} for n in recent], "source": "MahaRERA public records"}


def fake_stats(thin=()):
    async def fn(db, key):
        return stats(key, projects=1) if key in thin else stats(key)
    return fn


def per_channel(items):
    out = defaultdict(list)
    for i in items:
        out[i.channel].append(i)
    return out


# ---- the plan (pure) ---------------------------------------------------------------------------------------------------------------
def test_a_week_has_two_reels_a_day_on_each_channel_twelve_hours_apart():
    items = build_daily_plan(START, 7, ALL)
    for ch, rows in per_channel(items).items():
        assert Counter(i.due_at.astimezone(IST).date() for i in rows) == {START + timedelta(days=d): 2 for d in range(7)}, ch
        times = sorted(i.due_at for i in rows)
        assert all(b - a >= MIN_GAP for a, b in zip(times, times[1:])), ch
        assert {i.kind for i in rows} == {"reel"}
    assert set(per_channel(items)) == {"instagram", "facebook_page"}


def test_morning_is_an_area_insight_and_evening_a_guide_without_consented_stock():
    for i in build_daily_plan(START, 7, ALL):
        h = i.due_at.astimezone(IST).hour
        if h == 8:
            assert (i.role, i.template, i.source) == ("area", "area", "area_insight") and i.area and i.ref == area_reel_slug(i.area, i.due_at.astimezone(IST).date())
        else:
            assert h == 20 and (i.role, i.template, i.source) == ("guide", "tip", "reel")
            assert library.BY_SLUG[i.ref].pillar in GUIDE_PILLARS and i.reel_ref == i.ref


def test_areas_rotate_and_the_affordable_belt_gets_at_least_half_the_mornings():
    mornings = [i for i in build_daily_plan(START, 24, ALL) if i.channel == "instagram" and i.role == "area"]
    assert len(mornings) == 24
    tiers = Counter(areas.get(i.area).tier for i in mornings)
    assert tiers["affordable"] >= len(mornings) / 2
    assert set(i.area for i in mornings) == set(ALL)  # every area comes round
    assert all(a.area != b.area for a, b in zip(mornings, mornings[1:]))


def test_areas_without_a_reel_are_skipped_and_no_area_means_no_morning():
    some = ["wagholi", "baner", "lohegaon"]
    items = build_daily_plan(START, 7, some)
    assert {i.area for i in items if i.role == "area"} <= set(some)
    none = build_daily_plan(START, 3, [])
    assert not [i for i in none if i.role == "area"] and len([i for i in none if i.channel == "instagram"]) == 3


def test_both_channels_share_one_reel_per_slot():
    by_slot = defaultdict(set)
    for i in build_daily_plan(START, 7, ALL):
        by_slot[i.due_at].add(i.ref)
    assert all(len(refs) == 1 for refs in by_slot.values())


def test_consented_projects_fill_evenings_once_each_then_guides():
    projects = [{"slug": "amco-equa", "agent_id": "a1", "area": "upper_kharadi"}, {"slug": "goyal-my-home", "agent_id": "a1", "area": "wagholi"}]
    ev = [i for i in build_daily_plan(START, 7, ALL, projects) if i.channel == "instagram" and i.due_at.astimezone(IST).hour == 20]
    assert [i.role for i in ev] == ["project", "project", "guide", "guide", "guide", "guide", "guide"]
    p = ev[0]
    assert p.source == "agentprojects" and p.agent_id == "a1" and p.ref == project_reel_slug(p.reel_ref) and p.area
    assert project_slug_of(p.ref) == p.reel_ref  # the comment assistant finds the project record from the row slug


def test_guides_and_projects_respect_the_60_day_rule_against_existing_rows():
    first = build_daily_plan(START, 7, ALL, [{"slug": "amco-equa", "agent_id": "a1"}])
    existing = [(i.channel, i.slug, i.due_at) for i in first]
    later = build_daily_plan(START + timedelta(days=7), 7, ALL, [{"slug": "amco-equa", "agent_id": "a1"}], existing=existing)
    used = {i.slug: i.due_at for i in first if i.role in ("guide", "project")}
    for i in later:
        if i.slug in used:
            assert i.due_at - used[i.slug] >= NO_REPEAT
    assert not [i for i in later if i.role == "project"]


def test_rerun_adds_nothing_and_existing_posts_keep_their_gap():
    first = build_daily_plan(START, 7, ALL)
    assert build_daily_plan(START, 7, ALL, existing=[(i.channel, i.slug, i.due_at) for i in first]) == []
    weekly = datetime.combine(START, time(10, 0), tzinfo=IST).astimezone(timezone.utc)  # a weekly post at 10:00 IST on Instagram
    items = build_daily_plan(START, 1, ALL, existing=[("instagram", "x", weekly)])
    ig = [i for i in items if i.channel == "instagram"]
    assert all(abs(i.due_at - weekly) >= MIN_GAP for i in ig)
    assert len([i for i in items if i.channel == "facebook_page"]) == 2


def test_past_slots_are_skipped_and_three_a_day_uses_a_six_hour_gap():
    now = datetime.combine(START, time(12, 0), tzinfo=IST)
    assert [i.due_at.astimezone(IST).hour for i in build_daily_plan(START, 1, ALL, now=now) if i.channel == "instagram"] == [20]
    three = per_channel(build_daily_plan(START, 7, ALL, per_day=3))["instagram"]
    assert len(three) == 21 and Counter(i.role for i in three)["area"] == 7


def test_area_slug_round_trip():
    assert area_of_slug(area_reel_slug("upper_kharadi", START)) == "upper_kharadi"
    assert area_of_slug("documents-before-booking") is None


# ---- area-insight reels -------------------------------------------------------------------------------------------------------------
def test_area_reel_slides_and_captions_say_only_the_facts():
    r = area_reels.reel_from_stats(stats())
    assert 4 <= len(r.slides) <= 5
    text = " ".join(r.script)
    assert "41" in text and "2027" in text and "3,100 of 5,210" in text and "Rohan Abhilasha 4" in text
    assert "avasetu.in/localities/wagholi" in r.slides[-1].lines[0]
    for cap in (r.caption_ig, r.caption_fb):
        assert cap.splitlines()[0] == "Wagholi in MahaRERA records: 41 projects."
        assert "Source: MahaRERA public records, as of 4 Oct 2026." in cap
        assert "localities/wagholi" in cap
        assert area_reels.wording_problems(cap) == []
        assert not re.search(r"newly registered|\bbest\b|₹|lakh|crore|will rise|expected", cap, re.I)
    assert "https://" not in r.caption_ig and "link in our bio" in r.caption_ig
    assert r.caption_fb.count("/localities/wagholi") == 1


def test_units_slide_only_when_both_numbers_are_known():
    r = area_reels.reel_from_stats(stats(total=None, booked=None))
    assert not [s for s in r.slides if s.kicker == "HOMES BOOKED"] and "booked" not in r.caption_ig.lower()
    assert len(r.slides) == 4


def test_thin_data_gives_no_reel_never_padding():
    assert area_reels.reel_from_stats(None) is None
    assert area_reels.reel_from_stats(stats(projects=2)) is None
    assert area_reels.reel_from_stats(stats(completing=(), total=None, booked=None)) is None  # 3 slides only
    assert area_reels.reel_from_stats(stats(completing=(), total=None, booked=None, recent=())) is None
    bad = stats()
    bad["area"]["key"] = "mumbai"
    assert area_reels.reel_from_stats(bad) is None


def test_names_that_break_a_wording_rule_are_left_out():
    r = area_reels.reel_from_stats(stats(recent=("Best Homes Phase 1", "Goyal My Home")))
    assert "Best" not in r.caption_ig and "Goyal My Home" in r.caption_ig


def test_wording_check_catches_banned_phrases():
    for bad in ("12 newly registered projects", "the best area", "prices will rise", "from ₹45 lakh", "new launch in Wagholi"):
        assert area_reels.wording_problems(bad), bad


def test_drawn_slides_pass_the_creative_checks():
    long = stats(key="keshav_nagar", completing=((2026, 3), (2027, 14), (2028, 9), (2029, 4)),
                 recent=("Kolte Patil Life Republic Sector R10 Phase 2 Tower A and B", "Goyal My Home Upper Kharadi Phase 2", "Rohan Abhilasha 4"))
    for s in (stats(), long, stats(key="upper_kharadi", total=None, booked=None)):
        rendered = area_reels.draw(area_reels.reel_from_stats(s))
        assert area_reels.check(rendered) == [], s["area"]["key"]
        assert all(r.size == (1080, 1920) for r in rendered)
        assert any("Source: MahaRERA public records" in it.text for r in rendered for it in r.items)


def test_area_reel_is_none_for_thin_data_or_a_failing_stats_source():
    assert asyncio.run(area_reels.area_reel(None, "wagholi", fake_stats(thin=("wagholi",)))) is None

    async def boom(db, key):
        raise RuntimeError("db down")
    assert asyncio.run(area_reels.area_reel(None, "wagholi", boom)) is None


def test_video_plays_every_slide_through_the_reels_encoder():
    with tempfile.TemporaryDirectory() as d:
        paths = area_reels.save_slides(area_reels.reel_from_stats(stats()), Path(d) / "s")
        seen = {}

        def encode(frames, total, out, music=None):
            seen["frames"] = sum(1 for _ in frames)
            seen["total"] = total
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_bytes(b"mp4")
            return Path(out)
        out = area_reels.render_video(paths, Path(d) / "r.mp4", encode=encode)
        assert out.is_file() and (Path(d) / "r-cover.jpg").is_file()
        assert seen["total"] > 4 * 2.5 and seen["frames"] == round(seen["total"] * 30)


# ---- stored rows ----------------------------------------------------------------------------------------------------------------------
def _project(slug="amco-equa"):
    return {"_id": slug, "agent_id": "ag1", "slug": slug, "status": "live", "name": "AMCO Equa", "builder": "AMCO", "locality": "Upper Kharadi",
            "rera_no": "P52100032093", "configurations": [{"label": "2 BHK", "bhk": 2, "carpet_sqft": 700, "price_inr": 7500000}],
            "rera": {"units_total": 200, "units_booked": 150, "completion_now": "2026-12-31", "checked_at": "2026-10-03"},
            "possession_target": "2027-12-31", "media": []}


async def _seed(db, consent):
    await db.get_collection("concierge_agents").insert_one({"_id": "ag1", "consent": {"given": consent}})
    await db.get_collection("agent_public_profiles").insert_one({"_id": "p1", "agent_id": "ag1", "slug": "house-deal", "is_public": True,
                                                                 "branding_data": {"business_name": "House Deal"}})
    await db.get_collection("agent_projects").insert_one(_project())


def _build(consent, enabled=True, thin=()):
    db = FakeDb()
    store = Store(db)
    with tempfile.TemporaryDirectory() as d:
        async def go():
            if consent is not None:
                await _seed(db, consent)
            return await builder.build_daily_and_store(store, START, 7, Path(d), stats_fn=fake_stats(thin), enabled=enabled)
        made = asyncio.run(go())
        rows = asyncio.run(store.all())
        files = {r["_id"]: all((Path(d) / p).is_file() for p in r["images"]) for r in rows}
    return made, rows, files


def test_flag_off_plans_nothing():
    made, rows, _ = _build(None, enabled=False)
    assert made == [] and rows == []


def test_rows_are_planned_with_slug_channel_kind_caption_source_and_area():
    made, rows, files = _build(None, thin=("baner", "wakad"))
    assert len(rows) == 28
    assert {r["status"] for r in rows} == {"planned"} and {r["kind"] for r in rows} == {"reel"}
    area_rows = [r for r in rows if r["creative"]["template"] == "area"]
    assert area_rows and all(r["area"] == r["creative"]["area"] and r["slug"].startswith("area-" + r["area"]) for r in area_rows)
    assert not {"baner", "wakad"} & {r["area"] for r in area_rows}
    assert all(r["images"] and files[r["_id"]] and r["creative"]["source"] == "area_insight" for r in area_rows)
    guides = [r for r in rows if r["creative"]["template"] == "tip"]
    assert len(guides) == 14 and all(r["caption"] and r["creative"]["source"] == "reel" for r in guides)


def test_no_consent_means_no_project_reels():
    _, rows, _ = _build(False)
    assert not [r for r in rows if r["creative"]["source"] == "agentprojects"]


def test_consented_project_becomes_an_evening_reel_for_its_agent():
    _, rows, _ = _build(True)
    proj = [r for r in rows if r["creative"]["source"] == "agentprojects"]
    assert {r["channel"] for r in proj} == {"instagram", "facebook_page"} and len(proj) == 2
    r = proj[0]
    assert r["agent_id"] == "ag1" and r["area"] == "upper_kharadi" and r["slug"] == "amco-equa-reel"
    assert r["creative"]["project"]["rera_no"] == "P52100032093" and r["creative"]["agent"] == {"name": "House Deal"}
    assert "Prices as quoted by House Deal" in r["caption"] and not PHONE.search(r["caption"])


def test_render_reel_for_draws_area_and_project_reels():
    with tempfile.TemporaryDirectory() as d:
        up = Path(d)
        paths = area_reels.save_slides(area_reels.reel_from_stats(stats()), up / "calendar/areareels/x")
        calls = []
        doc = {"slug": "area-wagholi-20261012", "creative": {"template": "area", "reel_key": "area-wagholi-20261012",
                                                             "slides": [p.relative_to(up).as_posix() for p in paths]}}
        rel = adapters._render_daily(doc, up, composer=lambda *a: calls.append(a))
        assert rel == "calendar/reels/area-wagholi-20261012.mp4" and len(calls[0][0]) == len(paths)
        pdoc = {"slug": "amco-equa-reel", "creative": {"template": "project", "reel_key": "amco-equa-reel", "project": {"x": 1}, "agent": {"name": "A"}}}
        adapters._render_daily(pdoc, up, composer=lambda *a: calls.append(a))
        assert calls[1][:2] == ({"x": 1}, {"name": "A"})



def test_daily_reel_rows_are_tagged_with_format_and_area():
    made, rows, _ = _build(True)
    assert rows and all(r["tags"]["kind"] == "reel" for r in rows)
    formats = {r["tags"]["format"] for r in rows}
    assert "area" in formats and formats <= {"area", "project", "tip", "tour", "pitch"}
    assert all(r["tags"]["area"] != "unknown" for r in rows if r["tags"]["format"] in ("area", "project"))
