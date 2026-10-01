"""The weekly rhythm (pure) and the built plan (creative rendered on the deterministic path, no network)."""
import asyncio
import socket
import tempfile
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import pytest
from PIL import Image

from app.modules.calendar import adapters, builder, library
from app.modules.calendar.plan import AREAS, build_plan
from app.modules.calendar.schedule import IST
from app.modules.calendar.store import Store

from ..fakes import FakeDb

START = date(2026, 10, 12)  # a Monday


def by_channel(items):
    out = defaultdict(list)
    for i in items:
        out[i.channel].append(i)
    return out


def weeks_of(items):
    out = defaultdict(list)
    for i in items:
        out[i.week].append(i)
    return out


def test_four_weeks_five_items_per_channel_per_week():
    items = by_channel(build_plan(START, 4))
    for ch, rows in items.items():
        assert Counter(i.week for i in rows) == {1: 5, 2: 5, 3: 5, 4: 5}, ch


def test_instagram_week_has_showcase_checklist_myth_poll_or_number_agent_and_a_reel():
    for w, rows in weeks_of(by_channel(build_plan(START, 4))["instagram"]).items():
        assert Counter(i.role for i in rows) == {"showcase": 1, "checklist": 1, "mythpoll": 1, "agent": 1, "reel": 1}, w
        assert Counter(i.kind for i in rows) == {"showcase": 1, "post": 3, "reel": 1}


def test_facebook_week_has_two_educational_a_showcase_an_agent_or_poll_and_the_reel():
    for w, rows in weeks_of(by_channel(build_plan(START, 4))["facebook_page"]).items():
        roles = Counter(i.role for i in rows)
        assert roles["edu_a"] == 1 and roles["edu_b"] == 1 and roles["showcase"] == 1 and roles["reel"] == 1
        assert roles["agent"] + roles["poll"] == 1
    kinds = [next(i.role for i in rows if i.role in ("agent", "poll")) for _, rows in sorted(weeks_of(by_channel(build_plan(START, 4))["facebook_page"]).items())]
    assert kinds == ["agent", "poll", "agent", "poll"]


def test_the_myth_poll_number_slot_rotates():
    mp = [i for i in by_channel(build_plan(START, 4))["instagram"] if i.role == "mythpoll"]
    assert [library.BY_SLUG[i.ref].pillar for i in mp][:2] == ["myth", "poll"]
    assert mp[2].prefer == "stat" and mp[2].ref in adapters.STAT_SLUGS
    assert library.BY_SLUG[mp[3].ref].pillar == "myth"


def test_times_are_10_or_19_ist_and_gaps_are_at_least_12_hours():
    for ch, rows in by_channel(build_plan(START, 4)).items():
        times = sorted(i.due_at for i in rows)
        assert all(b - a >= timedelta(hours=12) for a, b in zip(times, times[1:])), ch
        for t in times:
            local = t.astimezone(IST)
            assert (local.hour, local.minute) in ((10, 0), (19, 0)) and local.date() >= START
    days = {i.due_at.astimezone(IST).weekday() for i in by_channel(build_plan(START, 4))["instagram"]}
    assert len(days) >= 6  # varied weekdays


def test_a_library_slug_never_repeats_within_60_days_on_either_channel():
    seen = defaultdict(list)
    for i in build_plan(START, 8):
        if i.source in ("library", "agent"):
            seen[i.ref].append(i.due_at)
    for slug, times in seen.items():
        times.sort()
        assert all(b - a >= timedelta(days=60) for a, b in zip(times, times[1:])), slug


def test_showcase_homes_rotate_through_the_three_areas():
    items = by_channel(build_plan(START, 4))
    for ch, first in (("instagram", 0), ("facebook_page", 1)):
        rows = sorted((i for i in items[ch] if i.kind == "showcase"), key=lambda i: i.due_at)
        areas = [adapters.get_home(i.ref).locality for i in rows]
        assert areas == [AREAS[(first + k) % 3] for k in range(4)]
    homes = [i.ref for i in items["instagram"] if i.kind == "showcase"]
    assert len(set(homes)) == len(homes)


def test_reel_templates_alternate_and_both_channels_share_one_reel():
    items = build_plan(START, 4)
    reels = defaultdict(dict)
    for i in items:
        if i.kind == "reel":
            reels[i.week][i.channel] = i
    assert [reels[w]["instagram"].template for w in (1, 2, 3, 4)] == ["tip", "tour", "pitch", "tip"]
    for w, pair in reels.items():
        assert pair["instagram"].ref == pair["facebook_page"].ref and pair["instagram"].reel_ref == pair["facebook_page"].reel_ref
    assert library.BY_SLUG[reels[1]["instagram"].reel_ref].pillar in ("checklist", "explainer")
    assert adapters.get_home(reels[2]["instagram"].reel_ref)


def test_agent_attraction_is_about_one_in_four():
    items = build_plan(START, 4)
    agent = [i for i in items if i.role == "agent" or (i.kind == "reel" and i.template == "pitch")]
    assert 0.15 <= len(agent) / len(items) <= 0.3, len(agent) / len(items)


def test_hindi_and_marathi_agent_posts_only_with_the_flag():
    local = {"agent-hindi", "agent-marathi"}
    assert not local & {i.ref for i in build_plan(START, 12)}
    with_flag = {i.ref for i in build_plan(START, 12, include_local=True)}
    assert local & with_flag


def test_planning_twice_adds_nothing_and_existing_slugs_count_as_used():
    first = build_plan(START, 4)
    existing = [(i.channel, i.ref, i.due_at) for i in first]
    assert build_plan(START, 4, existing=existing) == []
    later = build_plan(START + timedelta(weeks=4), 4, existing=existing)
    assert later and not {i.ref for i in later if i.source in ("library", "agent")} & {i.ref for i in first if i.source in ("library", "agent")}


# ---- the built plan (creative made, deterministic path) -------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    uploads = Path(tempfile.mkdtemp(prefix="plan-built-"))
    store = Store(FakeDb())

    def no_network(*a, **k):
        raise AssertionError("the plan builder must not use the network")

    loop = asyncio.new_event_loop()  # created before the patch: an event loop itself opens a local socket pair
    try:
        with mock.patch.object(socket.socket, "connect", no_network):
            made = loop.run_until_complete(builder.build_and_store(store, START, 4, uploads))
            rows = loop.run_until_complete(store.all())
            again = loop.run_until_complete(builder.build_and_store(store, START, 4, uploads))
    finally:
        loop.close()
    return uploads, rows, made, again


def test_everything_is_planned_not_approved(built):
    _, rows, _, _ = built
    assert len(rows) == 40 and {r["status"] for r in rows} == {"planned"}


def test_planning_again_creates_no_new_rows(built):
    assert built[3] == []


def test_images_exist_with_the_right_sizes_and_facebook_has_one_image(built):
    uploads, rows, _, _ = built
    for r in rows:
        if r["kind"] == "reel":
            assert r["images"] == [] and r["video"] is None and r["creative"]["template"] in ("tip", "tour", "pitch")
            continue
        assert r["images"] and r["image_path"] == r["images"][0]
        if r["channel"] == "facebook_page":
            assert len(r["images"]) == 1
        for rel in r["images"]:
            with Image.open(uploads / rel) as im:
                if r["kind"] == "showcase":
                    assert im.size in ((1080, 1350), (1200, 630))
                else:
                    assert im.size == ((1080, 1350) if r["channel"] == "instagram" else (1080, 1080)), (r["slug"], im.size)
    assert any(len(r["images"]) >= 4 for r in rows if r["channel"] == "instagram" and r["kind"] == "post")  # a real carousel exists


def test_no_layout_twice_in_a_row_on_a_channel(built):
    _, rows, _, _ = built
    for ch in ("instagram", "facebook_page"):
        seq = [r["creative"]["layout"] for r in sorted(rows, key=lambda r: r["due_at"]) if r["channel"] == ch and r["kind"] != "reel"]
        assert all(a != b for a, b in zip(seq, seq[1:])), seq
        assert len(set(seq)) >= 5, seq  # real variety


def test_captions_are_clean_and_instagram_has_no_url(built):
    from app.modules.marketing.polish import HYPE, PHONE
    _, rows, _, _ = built
    for r in rows:
        assert r["caption"].strip() and not PHONE.search(r["caption"]) and not HYPE.search(r["caption"]), r["slug"]
        if r["channel"] == "instagram":
            assert "http" not in r["caption"] and "www." not in r["caption"], r["slug"]
        assert r["creative"].get("ok", True), (r["slug"], r["creative"].get("problems"))
        assert r["creative"]["path"] in ("rules", "showcase", "reel")


def test_showcase_items_are_labelled_samples(built):
    _, rows, _, _ = built
    shows = [r for r in rows if r["kind"] == "showcase"]
    assert len(shows) == 8 and all("Sample listing" in r["caption"] for r in shows)
