"""Agent-recruitment reels: honest scripts, the hook rules (no logo on frame one, 'for agents' on frame one), the calendar rows and the funnel."""
import asyncio
from dataclasses import replace
from datetime import date, time
from pathlib import Path

import pytest

from app.modules.calendar import adapters, reach
from app.modules.calendar.store import Store
from app.modules.reels import agent_reels as ar
from app.modules.reels import compose
from scripts import agent_reels as cli

from ..fakes import FakeDb


def test_all_ten_scripts_pass_their_checks_and_cover_the_experiment():
    assert [p for s in ar.SCRIPTS for p in ar.check_script(s)] == []
    groups = [s.group for s in ar.SCRIPTS]
    assert (groups.count("pain"), groups.count("demo"), groups.count("before_after"), groups.count("result")) == (3, 3, 2, 2)
    assert sorted(ar.ORDER) == sorted(ar.BY_CODE) and len(set(ar.ORDER)) == 10


@pytest.mark.parametrize("field,text", [
    ("result", "Reel *in seconds*"),
    ("screen_line", "We *publish* everywhere for you"),
    ("caption", "Save 30 minutes on every post"),
    ("result", "Your assistant works 24/7"),
    ("hook", "Pune agents, are you still typing every single property post?"),
    ("pain", "एजेंट"),
])
def test_claims_we_cannot_back_up_are_refused(field, text):
    s = replace(ar.BY_CODE["A1"], **{field: text})
    assert ar.check_script(s)
    with pytest.raises(ValueError):
        ar.scenes(s)


def test_fifty_plus_is_allowed_only_where_it_describes_the_viewer():
    assert ar.check_script(ar.BY_CODE["D2"]) == []
    assert ar.check_script(replace(ar.BY_CODE["A1"], hook="50+ properties?"))


def test_five_scenes_hook_first_for_agents_and_comment_agent_last():
    scenes, opts = ar.scenes(ar.BY_CODE["C1"])
    assert len(scenes) == 5 and opts["hook_tag"] is False
    hook, pain, screen, result, cta = scenes
    assert hook.kicker == ar.KICKER and hook.seconds <= 2.2
    assert pain.kicker == "Before" and screen.kicker.startswith("After")
    assert screen.screen and screen.layout == "top" and isinstance(screen.image, compose.Image.Image)
    assert "*AGENT*" in cta.lines[0].text
    total = compose.plan([s.seconds for s in scenes], opts["xfade"]).total
    assert 10 <= total <= 15


def test_no_brand_tag_on_the_hook_frames_but_from_scene_two(monkeypatch):
    scenes, opts = ar.scenes(ar.BY_CODE["A1"])
    r = compose.Renderer(scenes, transition=opts["transition"], xfade=opts["xfade"], hook_tag=False)
    seen, orig = [], compose._chrome
    monkeypatch.setattr(compose, "_chrome", lambda *a, **k: seen.append(k.get("tag_alpha", 1.0)) or orig(*a, **k))
    r.frame_at(0.0), r.frame_at(1.0), r.cover(), r.frame_at(r.tl.starts[1] + 0.8)
    assert seen == [0.0, 0.0, 0.0, 1.0]
    monkeypatch.undo()
    plain = compose.Renderer(scenes, transition=opts["transition"], xfade=opts["xfade"], hook_tag=True)
    assert r.frame_at(0.0).tobytes() != plain.frame_at(0.0).tobytes()          # the tag is gone from the first frame
    assert r.frame_at(r.tl.starts[2] + 1.0).tobytes() == plain.frame_at(r.tl.starts[2] + 1.0).tobytes()  # and back later


def test_the_sample_phone_number_on_the_lead_screen_is_covered():
    img = ar._screen_image("19-lead-detail.jpg")
    x0, y0, x1, y1 = ar.REDACT["19-lead-detail.jpg"][0]
    box = img.crop((x0, y0, x1, y1)).convert("L")
    assert box.getextrema()[1] - box.getextrema()[0] <= 2   # one flat colour: no digits left


def test_captions_carry_the_keyword_and_on_facebook_the_tagged_trial_link():
    fb, ig = ar.caption("B2", "facebook_page"), ar.caption("B2", "instagram")
    assert "Comment AGENT" in fb and fb.endswith("/trial?src=reel_b2_fb") and "free trial" in fb and "sample data" in fb
    assert "Comment AGENT" in ig and "http" not in ig
    assert not ar.BANNED.search(fb)


def test_plan_adds_one_planned_reel_a_day_for_agents_only_once():
    store = Store(FakeDb())
    said = []
    n = asyncio.run(cli.plan(store, date(2026, 10, 6), time(19, 30), ["facebook_page"], say=said.append))
    assert n == 10
    rows = asyncio.run(store.all())
    assert {r["status"] for r in rows} == {"planned"} and {r["kind"] for r in rows} == {"reel"}
    assert [r["creative"]["reel_code"] for r in rows] == list(ar.ORDER)
    assert all(reach.audience(r) == "agents" for r in rows)
    assert reach.hashtags({**rows[0], "channel": "instagram"}) == reach.AGENT_TAGS[:5]
    assert asyncio.run(cli.plan(store, date(2026, 10, 6), time(19, 30), ["facebook_page"], say=said.append)) == 0


def test_the_calendar_renders_an_agent_row_by_its_code(tmp_path):
    made = []
    doc = {"_id": "x", "slug": "agent-reel-a1", "creative": {"template": "agent", "reel_key": "agent-a1", "reel_code": "A1"}}
    rel = adapters.render_agent_reel(doc, tmp_path, composer=lambda sc, dest, **o: made.append((len(sc), dest, o)) or dest)
    assert rel == "calendar/reels/agent-a1.mp4" and made[0][0] == 5 and made[0][2]["hook_tag"] is False


def test_agent_rows_get_the_footer_but_no_buyer_interest_line():
    doc = {"_id": "x", "slug": "agent-reel-a1", "kind": "reel", "channel": "facebook_page", "caption": ar.caption("A1", "facebook_page"),
           "creative": {"source": "agent_reels"}}
    out = asyncio.run(adapters.with_interest(FakeDb(), doc))
    assert "Interested? One tap" not in out["caption"] and "/trial?src=reel_a1_fb" in out["caption"]


def test_funnel_traces_requests_signups_and_first_property_to_the_reel():
    comments = [{"reel_code": "C1", "intent": "interested"}, {"reel_code": "C1", "intent": "spam"}, {"reel_code": None, "intent": "interested"}]
    requests = [{"source": "reel_c1_fb", "phone": "+91 98220 11111"}, {"source": "reel_c1_fb", "phone": "9822011111"},   # same person twice
                {"source": "reel_c1_ig", "phone": "9822022222"}, {"source": "reel_b2_fb", "phone": "9822033333"},
                {"source": "wa", "phone": "9822044444"}]
    users = [{"_id": "u1", "phone": "919822011111"}, {"_id": "u3", "phone": "9822033333"}]
    listings = [{"agent_id": "u1"}]
    f = ar.funnel(comments, requests, users, listings)
    assert f["C1"] == {"comments": 1, "requests": 2, "signed_up": 1, "added_property": 1}
    assert f["B2"] == {"comments": 0, "requests": 1, "signed_up": 1, "added_property": 0}
    assert sum(v["requests"] for v in f.values()) == 3
