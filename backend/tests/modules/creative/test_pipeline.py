import os

from PIL import Image

from app.modules.creative import pipeline
from app.modules.creative.guards import problems_in
from app.modules.creative.samples import agent_briefs, buyer_briefs

from .helpers import FakeLlm, simple_brief


async def test_fallback_without_llm_is_good_and_guard_passing(tmp_path):
    for i, b in enumerate(buyer_briefs()):
        pack = await pipeline.make(b, "buyer", "instagram", None, seed=i, out_dir=tmp_path)
        assert pack.report["ok"], pack.report
        assert not pack.used_llm and pack.images and all(os.path.isfile(p) for p in pack.images)
        assert problems_in(pack.caption, b.corpus()) == []
        assert "http" not in pack.caption
        with Image.open(pack.images[0]) as im:
            assert im.size == (1080, 1350)


async def test_agent_posts_and_facebook_size(tmp_path):
    pack = await pipeline.make(agent_briefs()[0], "agent", "facebook", None, seed=1, out_dir=tmp_path)
    assert pack.report["ok"]
    with Image.open(pack.images[0]) as im:
        assert im.size == (1080, 1080)


async def test_carousel_gives_a_list_of_images(tmp_path):
    b = buyer_briefs()[0]
    pack = await pipeline.make(b, "buyer", "instagram", None, seed=0, out_dir=tmp_path)
    assert pack.design["format"] == "carousel" and len(pack.images) == len(b.steps) + 2
    assert pack.design["slides"] == len(pack.images)


async def test_recent_layouts_are_avoided(tmp_path):
    b = buyer_briefs()[4]
    layouts = set()
    for seed in range(6):
        pack = await pipeline.make(b, "buyer", "instagram", None, seed=seed, recent_layouts=["photo_led", "quote_tip"], out_dir=tmp_path)
        layouts.add(pack.design["layout"])
        assert pack.design["layout"] != "quote_tip"
    assert layouts == {"photo_led"}


async def test_llm_outage_falls_back_to_rules(tmp_path):
    pack = await pipeline.make(simple_brief(), "buyer", "instagram", FakeLlm(RuntimeError("x"), RuntimeError("x"), RuntimeError("x")), seed=0, out_dir=tmp_path)
    assert pack.report["ok"] and pack.images


async def test_critic_failure_triggers_one_regeneration_with_feedback(tmp_path):
    bad = {"hook": "Is your date in writing?", "format": "single"}
    # attempt 1: valid hook, but the copywriter reply is garbage -> rule copy (still fine). Force a failure through an over-long support.
    llm = FakeLlm(bad, {"support": "x"}, bad, {"support": "y"})
    pack = await pipeline.make(simple_brief(), "buyer", "instagram", llm, seed=0, out_dir=tmp_path)
    assert pack.report["ok"]


async def test_failed_first_attempt_is_retried(tmp_path, monkeypatch):
    from app.modules.creative import critic
    from app.modules.creative.models import Problem, Report
    calls = {"n": 0}
    real = critic.review

    def flaky(*a, **k):
        calls["n"] += 1
        rep = real(*a, **k)
        if calls["n"] == 1:
            rep.problems.append(Problem("hook_length", "forced"))
        return rep

    monkeypatch.setattr(critic, "review", flaky)
    llm = FakeLlm({"hook": "Is your date in writing?"}, {}, {"hook": "Do you have the date in writing?"}, {})
    pack = await pipeline.make(simple_brief(), "buyer", "instagram", llm, seed=0, out_dir=tmp_path)
    assert calls["n"] == 2 and pack.attempts == 2 and pack.report["ok"]
    feedback_seen = [c for c in llm.calls if "reviewer rejected" in c[2]]
    assert feedback_seen


async def test_pack_fields(tmp_path):
    pack = await pipeline.make(simple_brief(), "buyer", "facebook", None, seed=2, out_dir=tmp_path)
    assert pack.caption and pack.hashtags and pack.alt_text and pack.design["layout"] and pack.angle["hook"]
    assert pack.channel == "facebook" and pack.audience == "buyer"
