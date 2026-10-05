"""Adapters: library entry -> creative Brief -> pack; the guards keep invented facts out; showcase and reel items."""
import re
from types import SimpleNamespace
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image

from app.modules.calendar import adapters, builder, library
from app.modules.calendar.plan import Item
from app.modules.creative import copywriter, guards, strategist
from app.modules.creative.models import Brief
from app.platform.meta_graph.config import SocialConfig

NUM = re.compile(r"\d+")


def entry_text(e):
    return " ".join([e.title, *e.points, e.body, e.review]).lower()


@pytest.mark.parametrize("entry", library.ENTRIES, ids=lambda e: e.slug)
async def test_every_entry_becomes_a_brief_whose_copy_passes_the_creative_guards(entry):
    for channel in ("instagram", "facebook_page"):
        b = adapters.entry_to_brief(entry, channel=channel)
        assert isinstance(b, Brief) and b.topic and b.facts
        # facts come only from the entry itself: every number in the brief is a number in the entry (or a stat the entry states in words)
        words_to_num = {"four": "4", "five": "5", "two": "2", "three": "3", "thirty": "30"}
        text = entry_text(entry) + " " + " ".join(words_to_num[w] for w in words_to_num if w in entry_text(entry))
        assert set(NUM.findall(b.corpus())) <= set(NUM.findall(text)), (entry.slug, b.corpus())
        audience = "agent" if entry.pillar == "agent" else "buyer"
        ch = "facebook" if channel == "facebook_page" else "instagram"
        angle = strategist.rule_angle(b, audience, ch, 3)
        copy = await copywriter.write(angle, b)
        assert guards.problems_in(copy.caption(ch, ""), b.corpus()) == [], entry.slug
        assert guards.problems_in(copy.hook, b.corpus()) == [], entry.slug


def test_structure_is_cut_from_the_entry_not_invented():
    myth = adapters.entry_to_brief(library.BY_SLUG["myth-token-booking"])
    assert myth.formats()[:3] == ["stat", "myth-vs-fact", "carousel"] and myth.prefer == "myth-vs-fact" and "10%" in myth.truth
    poll = adapters.entry_to_brief(library.BY_SLUG["poll-ready-vs-uc"])
    assert poll.options == ["Ready to move", "Under construction"] and poll.prefer == "poll"
    many = adapters.entry_to_brief(library.BY_SLUG["poll-top-priority"])
    assert many.options == [] and many.prefer == "single"  # four options cannot become a two-way poll
    check = adapters.entry_to_brief(library.BY_SLUG["red-flags-in-ads"])
    assert len(check.steps) == 6 and check.prefer == "carousel"
    fb = adapters.entry_to_brief(library.BY_SLUG["red-flags-in-ads"], channel="facebook_page")
    assert fb.prefer == "single"  # Facebook shows one image
    assert adapters.entry_to_brief(library.BY_SLUG["carpet-under-rera"]).link == ""
    assert adapters.entry_to_brief(library.BY_SLUG["myth-near-metro"]).link.endswith("/insights/metro-kharadi-wagholi-approved-not-running")


def test_verification_notes_are_kept_in_the_library():
    for e in library.ENTRIES:
        assert e.review and len(e.review) > 20


class InventingLLM:
    """An LLM that tries to add facts: a price, a count of flats, a phone number, a hype word."""

    async def json(self, system, user):
        return {"hook": "Only 7 flats left at Rs 40 lakh", "idea": "Book now", "proof": ["7 flats left"], "pain": "x", "format": "single",
                "first_line": "Only 7 flats left at 40 lakh, call 9876543210", "body": "Guaranteed 20% returns. Best deal ever.",
                "support": "Prices will rise 30%", "question": "Call now?", "hashtags": ["#a"], "slides": ["Buy 3 flats"], "cta": "Call 9876543210"}

    async def text(self, system, user):
        return "Only 7 flats left at 40 lakh"


async def test_an_llm_cannot_add_facts_to_a_library_pack():
    out = Path(tempfile.mkdtemp(prefix="adapters-"))
    entry = library.BY_SLUG["carpet-under-rera"]
    pack = await adapters.make_pack(entry, "instagram", InventingLLM(), [], out, seed=2)
    brief = adapters.entry_to_brief(entry)
    assert guards.problems_in(pack.caption, brief.corpus(), allow_url=True) == []
    for bad in ("7 flats", "40 lakh", "9876543210", "Guaranteed", "30%", "20%"):
        assert bad not in pack.caption
    assert pack.images and Image.open(pack.images[0]).size == (1080, 1350)
    fb = await adapters.make_pack(entry, "facebook_page", None, [], out, seed=2)
    assert Image.open(fb.images[0]).size == (1080, 1080)


async def test_hindi_entry_keeps_its_prerendered_card_and_caption():
    out = Path(tempfile.mkdtemp(prefix="adapters-"))
    entry = library.BY_SLUG["agent-hindi"]
    pack = await adapters.make_pack(entry, "instagram", None, [], out)
    assert pack.caption == entry.ig_caption and Image.open(pack.images[0]).size == (1080, 1350)


class RaisingLLM:
    async def json(self, system, user):
        raise TimeoutError("llm down")

    text = json


async def test_llm_failure_falls_back_to_the_deterministic_path_and_says_so():
    out = Path(tempfile.mkdtemp(prefix="builder-"))
    it = Item("instagram", "post", datetime(2026, 10, 14, 4, 30, tzinfo=timezone.utc), 1, "mythpoll", "library", "myth-rera-means-safe", "myth-vs-fact")
    pack, how = await builder._pack(it, RaisingLLM(), [], out)
    assert how.startswith("rules") and pack.images and pack.report["ok"]
    pack2, how2 = await builder._pack(it, None, [], out)
    assert how2 == "rules"


def test_showcase_item_renders_labelled_images_and_a_valid_caption():
    uploads = Path(tempfile.mkdtemp(prefix="show-"))
    home = adapters.get_home("kharadi-2bhk-ready")
    ig = adapters.showcase_item(home, "instagram", uploads)
    fb = adapters.showcase_item(home, "facebook_page", uploads)
    assert len(ig["images"]) == 5 and fb["images"] == ["showcase/kharadi-2bhk-ready/facebook.jpg"]
    assert all((uploads / p).is_file() for p in ig["images"] + fb["images"])
    assert "Sample listing" in ig["caption"] and "http" not in ig["caption"] and "link in our bio" in ig["caption"]


def test_reel_item_scripts_captions_and_render_with_a_stub_composer():
    uploads = Path(tempfile.mkdtemp(prefix="reel-"))
    spec = adapters.ReelSpec("tip", "reel-w1-tip", "red-flags-in-ads")
    entry = library.BY_SLUG["red-flags-in-ads"]
    scenes, _ = adapters.reel_scenes(spec, entry)
    assert len(scenes) == 5 and "property ad" in scenes[0].lines[0].text
    assert adapters.reel_caption(spec, "instagram", entry) == entry.ig_caption
    pitch = adapters.ReelSpec("pitch", "reel-w3-pitch", "")
    assert "http" not in adapters.reel_caption(pitch, "instagram") and "http" in adapters.reel_caption(pitch, "facebook_page")
    tour = adapters.ReelSpec("tour", "reel-w2-tour", "kharadi-2bhk-ready")
    assert "Sample listing" in adapters.reel_caption(tour, "facebook_page")
    calls = []

    def composer(scenes, dest, **options):
        calls.append(dest)
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(b"mp4")

    assert adapters.render_reel(spec, uploads, entry, composer) == "calendar/reels/reel-w1-tip.mp4"
    assert adapters.render_reel(spec, uploads, entry, composer) == "calendar/reels/reel-w1-tip.mp4" and len(calls) == 1  # already rendered
    for s in (tour, pitch):
        assert adapters.reel_scenes(s)[0]


async def test_publish_reel_dry_run_and_live_call_shape(monkeypatch):
    uploads = Path(tempfile.mkdtemp(prefix="reel-"))
    (uploads / "calendar" / "reels").mkdir(parents=True)
    (uploads / "calendar" / "reels" / "reel-w1-tip.mp4").write_bytes(b"mp4")
    doc = {"channel": "instagram", "caption": "cap", "video": "calendar/reels/reel-w1-tip.mp4", "slug": "reel-w1-tip", "creative": {"reel_key": "reel-w1-tip"}}
    res = await adapters.publish_reel(doc, SocialConfig(dry_run=True), uploads)
    assert res.external_id.startswith("dryrun_")
    sent = []

    async def fake(channel, url, caption, cfg=None, file_path=None, **kw):
        sent.append((channel, url, caption, Path(file_path).name))
        return res

    monkeypatch.setattr(adapters._reel_publish, "publish_reel", fake)
    live = SocialConfig(dry_run=False, page_id="P", ig_id="I", media_base_url="https://media.test", page_token="EAAB" + "x" * 30)
    await adapters.publish_reel(doc, live, uploads)
    assert sent == [("instagram", "https://media.test/uploads/reels/reel-w1-tip.mp4", "cap", "reel-w1-tip.mp4")]
    assert (uploads / "reels" / "reel-w1-tip.mp4").is_file()  # staged where /uploads serves it
    assert not (uploads / "reels" / "reel-w1-tip-cover.jpg").exists()   # no cover rendered: published exactly as before


async def test_publish_reel_sends_the_cover_to_instagram_only(monkeypatch):
    uploads = Path(tempfile.mkdtemp(prefix="reel-"))
    (uploads / "calendar" / "reels").mkdir(parents=True)
    (uploads / "calendar" / "reels" / "reel-w1-tip.mp4").write_bytes(b"mp4")
    (uploads / "calendar" / "reels" / "reel-w1-tip-cover.jpg").write_bytes(b"jpg")
    sent = []

    async def fake(channel, url, caption, cfg=None, file_path=None, **kw):
        sent.append((channel, kw.get("cover_url")))
        return SimpleNamespace(external_id="x", permalink=None)

    monkeypatch.setattr(adapters._reel_publish, "publish_reel", fake)
    live = SocialConfig(dry_run=False, page_id="P", ig_id="I", media_base_url="https://media.test", page_token="EAAB" + "x" * 30)
    for ch in ("instagram", "facebook_page"):
        doc = {"channel": ch, "caption": "cap", "video": "calendar/reels/reel-w1-tip.mp4", "slug": "reel-w1-tip",
               "creative": {"reel_key": "reel-w1-tip"}}
        await adapters.publish_reel(doc, live, uploads)
    assert sent == [("instagram", "https://media.test/uploads/reels/reel-w1-tip-cover.jpg"), ("facebook_page", None)]
    assert (uploads / "reels" / "reel-w1-tip-cover.jpg").read_bytes() == b"jpg"   # staged next to the mp4


def test_a_slides_reel_opens_on_the_posts_hook_line(tmp_path, monkeypatch):
    from app.modules.reels import slides
    seen = []

    def fake(paths, dest, hook=None, **kw):
        seen.append(hook)
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(b"mp4")
        return dest

    monkeypatch.setattr(slides, "make_slides_reel", fake)
    base = {"images": ["a.jpg", "b.jpg"], "caption": "Caption first line\nmore"}
    adapters.render_slides_reel_for({**base, "_id": "r1", "creative": {"hook": "The creative's hook"}}, tmp_path)
    adapters.render_slides_reel_for({**base, "_id": "r2"}, tmp_path)
    assert seen == ["The creative's hook", "Caption first line\nmore"]  # make_slides_reel keeps the first line
