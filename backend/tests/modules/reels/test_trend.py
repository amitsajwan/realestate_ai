"""Trend reels: every figure comes from dated, sourced facts or a deterministic calculation; a reel with a number that is not in its facts, an
expired fact or a weak hook is refused; the reel director works without photos or a voice."""
import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from app.modules.reels import director, ffmpeg, trend
from scripts import trend_reels

from ..fakes import FakeDb

pytestmark = pytest.mark.asyncio
TODAY = date(2026, 10, 5)


def test_the_cost_sheet_adds_the_taxes_and_nothing_else():
    c = trend.cost_sheet(6_000_000)
    assert c == {"base": 6_000_000, "stamp_duty": 420_000, "registration": 30_000, "gst": 200_000, "extra": 650_000, "total": 6_650_000}
    ready = trend.cost_sheet(6_000_000, under_construction=False)
    assert ready["gst"] == 0 and ready["total"] == 6_450_000
    # registration is 1% below the cap
    assert trend.cost_sheet(2_000_000)["registration"] == 20_000
    # a woman's stamp duty rate is one point lower
    assert trend.cost_sheet(6_000_000, stamp_pct=6.0)["stamp_duty"] == 360_000


def test_money_and_area_formatting_and_arithmetic():
    assert trend.lakh(420_000) == "Rs 4.2 lakh" and trend.lakh(6_650_000) == "Rs 66.5 lakh" and trend.lakh(30_000) == "Rs 30,000"
    assert trend.lakh(200_000) == "Rs 2 lakh"
    assert trend.area_for_budget(5_000_000, 5_000, 6_500) == (770, 1000)
    assert trend.area_for_budget(5_000_000, 8_600, 10_400) == (480, 580)


def test_every_reel_passes_its_own_checks_today():
    for r in trend.TRENDS:
        assert trend.check(r, TODAY) == [], r.slug
    assert len({r.slug for r in trend.TRENDS}) == len(trend.TRENDS) == len(trend.BY_SLUG)


def test_every_fact_is_sourced_dated_and_only_official_facts_say_official():
    for f in trend.FACTS.values():
        assert f.source and f.url.startswith("https://") and f.as_of < f.valid_until
        assert f.kind in (trend.OFFICIAL, trend.SECONDARY)
    # the metro facts come from the Cabinet's own release; prices and rates from portals and advice sites are labelled secondary
    assert trend.FACTS["metro_2b_approved"].kind == trend.OFFICIAL and "pib.gov.in" in trend.FACTS["metro_2b_approved"].url
    assert {f.id for f in trend.FACTS.values() if f.kind == trend.SECONDARY} >= {"psf_wagholi", "psf_kharadi", "stamp_duty_man", "gst_under_construction"}


def test_a_number_that_is_not_in_the_facts_is_refused():
    r = trend.BY_SLUG["trend-60l-flat-real-cost"]
    bad = replace(r, beats=(*r.beats[:1], {"screen": "Parking costs ₹3 lakh", "voice": "Parking costs three lakh."}, *r.beats[2:]))
    assert any("not in the facts" in p for p in trend.check(bad, TODAY))
    ok_words = replace(r, beats=(*r.beats[:1], {"screen": "Parking is extra", "voice": "Parking is extra."}, *r.beats[2:]))
    assert trend.check(ok_words, TODAY) == []


def test_an_expired_fact_blocks_the_reel_and_a_scare_hook_or_weak_caption_is_flagged():
    r = trend.BY_SLUG["trend-wagholi-metro"]
    assert any("expired" in p for p in trend.check(r, date(2028, 1, 1)))
    assert any("scare hook" in p for p in trend.check(replace(r, beats=({"screen": "Don't buy near a planned *station*", "voice": "x"}, *r.beats[1:])), TODAY))
    assert any(p.startswith("hook:") for p in trend.check(replace(r, caption="Metro\n\nmore"), TODAY))
    assert any("unknown fact" in p for p in trend.check(replace(r, facts=("nope",)), TODAY))


def test_secondary_facts_are_listed_for_the_human_and_captions_carry_sources():
    assert trend.secondary_facts(trend.BY_SLUG["trend-wagholi-metro"]) == []
    assert {f.id for f in trend.secondary_facts(trend.BY_SLUG["trend-50l-kharadi-wagholi"])} == {"psf_wagholi", "psf_kharadi"}
    caps = trend.captions(trend.BY_SLUG["trend-wagholi-metro"])
    assert "Source: PIB, Union Cabinet release, 2025-06-25" in caps["facebook"] and "not investment, tax or legal advice" in caps["facebook"]
    assert caps["instagram"].endswith("#Avasetu") and "#Avasetu" not in caps["facebook"]
    assert caps["facebook"].splitlines()[0] == "Is the metro to Wagholi built yet? No: approved, not running."


def test_the_director_keeps_every_beat_when_there_are_no_photos():
    script = trend.script_of(trend.BY_SLUG["trend-50l-kharadi-wagholi"])
    beats, picks = director.fit_beats(script, [])
    assert len(beats) == len(script["beats"]) + 1 and picks == [None] * len(beats)
    assert beats[-1]["screen"] == script["cta_screen"]


@pytest.mark.skipif(not ffmpeg.available(), reason="ffmpeg cannot run here")
def test_a_trend_reel_renders_without_a_voice_key(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_TTS_API_KEY", raising=False)
    out = trend.render(trend.BY_SLUG["trend-wagholi-metro"], tmp_path / "r.mp4", today=TODAY)
    info = ffmpeg.probe(out)
    assert (info.width, info.height) == (1080, 1920) and info.has_audio and 8 < info.duration < 29
    assert (tmp_path / "r-cover.jpg").is_file()


def test_render_refuses_a_reel_that_fails_its_checks(tmp_path, monkeypatch):
    r = trend.BY_SLUG["trend-wagholi-metro"]
    with pytest.raises(ValueError, match="trend-wagholi-metro"):
        trend.render(replace(r, facts=("psf_nope",)), tmp_path / "x.mp4", today=TODAY)


@pytest.mark.skipif(not ffmpeg.available(), reason="ffmpeg cannot run here")
async def test_the_script_renders_a_manifest_and_queues_planned_rows_once(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_TTS_API_KEY", raising=False)
    monkeypatch.setenv("UPLOAD_DIRECTORY", str(tmp_path / "uploads"))
    monkeypatch.setattr(trend, "TRENDS", [trend.BY_SLUG["trend-wagholi-metro"], trend.BY_SLUG["trend-60l-flat-real-cost"]])
    manifest = trend_reels.render_all(tmp_path / "out", TODAY)
    assert [m["slug"] for m in manifest] == ["trend-wagholi-metro", "trend-60l-flat-real-cost"]
    saved = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert saved[1]["confirm_before_approving"] == ["stamp_duty_man", "registration", "gst_under_construction"]
    db = FakeDb()
    assert await trend_reels.queue(db, manifest, tmp_path / "out", TODAY, dry=True, log=lambda *_: None) == 0
    assert await trend_reels.queue(db, manifest, tmp_path / "out", TODAY, dry=False, log=lambda *_: None) == 4  # 2 reels x 2 channels
    rows = db.get_collection("content_calendar").docs
    assert {r["status"] for r in rows} == {"planned"} and {r["kind"] for r in rows} == {"reel"}
    assert {r["channel"] for r in rows} == {"instagram", "facebook_page"}
    assert all((tmp_path / "uploads" / r["video"]).is_file() for r in rows)
    first = next(r for r in rows if r["slug"] == "trend-wagholi-metro" and r["channel"] == "instagram")
    assert first["creative"]["experiment"] == "EXP-002" and first["creative"]["source"] == "trend_reels"
    assert "Source: PIB" in first["caption"]
    assert await trend_reels.queue(db, manifest, tmp_path / "out", TODAY, dry=False, log=lambda *_: None) == 0  # idempotent
