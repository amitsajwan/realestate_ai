"""The voice-over: one take cut into lines (with the per-line fallback), the ducked music mix, the conversational Hindi and
Marathi rules script, and the walkthrough caption in the reel's language. Fakes only: no TTS key, no network, no ffmpeg."""
import re
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from app.modules.reels import listing_reel as lr, narration, voice
from app.modules.reels.director import _valid

SR = narration.SR
LISTING = dict(_id="L1", title="2 BHK in Kharadi", transaction="sale", property_type="apartment", price_inr=8500000, city="Pune",
               locality="Kharadi", bhk=2, carpet_sqft=780, floor=7, total_floors=22, furnishing="semi", possession="ready",
               amenities=["Gym", "Parking", "Lift"], about={"highlights": ["East-facing balcony"]})
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def tone(seconds: float, f: float = 220.0) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    return 0.4 * np.sin(2 * np.pi * f * t)


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SR))


def pcm(*parts) -> np.ndarray:
    return (np.concatenate(parts) * 32767).astype("<i2")


def take_of(n: int, gap: float = 1.2) -> np.ndarray:
    """n spoken lines, the second with a short pause inside it (a comma or a '?'), with `gap` seconds between lines."""
    parts = [silence(0.1)]
    for i in range(n):
        parts.append(tone(0.9 + 0.1 * i, 200 + 40 * i))
        if i == 1:
            parts += [silence(0.4), tone(0.5)]
        parts.append(silence(gap if i < n - 1 else 0.2))
    return pcm(*parts)


# ---- cutting one take into lines ----------------------------------------------------------------------------------------------
def test_a_take_is_cut_at_its_long_pauses_only():
    pieces = narration.split(take_of(4), 4)
    assert pieces is not None and len(pieces) == 4
    secs = [p.size / SR for p in pieces]
    assert secs[0] == pytest.approx(0.9 + narration.HEAD_S + narration.TAIL_S, abs=0.03)
    assert secs[1] == pytest.approx(1.0 + 0.4 + 0.5 + narration.HEAD_S + narration.TAIL_S, abs=0.03)   # the short pause stays inside


def test_a_take_that_does_not_cut_into_one_piece_per_line_is_refused():
    assert narration.split(take_of(4), 5) is None                      # a line missing
    assert narration.split(take_of(4), 3) is None                      # a line too many
    assert narration.split(take_of(4, gap=0.5), 4) is None             # pauses too short to tell lines apart
    assert narration.split(pcm(silence(2.0)), 3) is None               # nothing spoken
    assert narration.split(take_of(1), 1) is None                      # one line needs no cutting


def test_take_ssml_has_one_break_between_lines_and_escapes_text():
    s = voice.take_ssml(["Price 85 lakh.", "Gym & pool <ok>", "Comment interested."])
    assert s.startswith("<speak>") and s.endswith("</speak>") and s.count("<break") == 2
    assert "&amp;" in s and "&lt;ok&gt;" in s and f'time="{voice.LINE_BREAK_MS}ms"' in s


class FakeVoice:
    """Stands in for voice.synth: records each request; `take_fails` makes the one-take request fail."""

    def __init__(self, take_fails: bool = False, line_fails: bool = False):
        self.takes, self.lines = [], []
        self.take_fails, self.line_fails = take_fails, line_fails

    def __call__(self, text, lang="en", ssml=False):
        if ssml:
            self.takes.append(text)
            if self.take_fails:
                raise voice.VoiceError("HTTP 400")
            return b"take"
        self.lines.append(text)
        if self.line_fails:
            raise voice.VoiceError("HTTP 403")
        return b"line"


LINES = ["एक", "दो", "तीन", "चार"]


def test_voice_lines_uses_one_take_when_it_cuts_cleanly(tmp_path, monkeypatch):
    fake = FakeVoice()
    monkeypatch.setattr(narration.voice, "synth", fake)
    monkeypatch.setattr(narration, "_decode", lambda mp3: take_of(4))
    clips, how = narration.voice_lines(LINES, "hi", tmp_path)
    assert how == "take" and len(fake.takes) == 1 and not fake.lines
    assert "दो" in fake.takes[0] and fake.takes[0].count("<break") == 3
    assert [c.suffix for c in clips] == [".wav"] * 4 and all(c.is_file() for c in clips)


@pytest.mark.parametrize("decoded", [lambda mp3: take_of(3), lambda mp3: take_of(4, gap=0.5), lambda mp3: np.zeros(10, "<i2")])
def test_voice_lines_falls_back_to_one_request_per_line_when_the_take_does_not_cut(tmp_path, monkeypatch, decoded):
    fake = FakeVoice()
    monkeypatch.setattr(narration.voice, "synth", fake)
    monkeypatch.setattr(narration, "_decode", decoded)
    clips, how = narration.voice_lines(LINES, "mr", tmp_path)
    assert how == "lines" and len(fake.takes) == 1 and fake.lines == LINES
    assert [c.name for c in clips] == ["b0.mp3", "b1.mp3", "b2.mp3", "b3.mp3"]


def test_voice_lines_falls_back_when_the_take_is_refused_or_cannot_be_decoded(tmp_path, monkeypatch):
    fake = FakeVoice(take_fails=True)
    monkeypatch.setattr(narration.voice, "synth", fake)
    assert narration.voice_lines(LINES, "hi", tmp_path)[1] == "lines" and fake.lines == LINES

    def broken(mp3):
        raise narration.ffmpeg.FfmpegError("ffmpeg failed")
    fake = FakeVoice()
    monkeypatch.setattr(narration.voice, "synth", fake)
    monkeypatch.setattr(narration, "_decode", broken)
    assert narration.voice_lines(LINES, "hi", tmp_path)[1] == "lines" and fake.takes and fake.lines == LINES


def test_no_voice_at_all_when_the_lines_fail_too(tmp_path, monkeypatch):
    monkeypatch.setattr(narration.voice, "synth", FakeVoice(take_fails=True, line_fails=True))
    with pytest.raises(voice.VoiceError):
        narration.voice_lines(LINES, "en", tmp_path)


def test_a_single_line_is_never_sent_as_a_take(tmp_path, monkeypatch):
    fake = FakeVoice()
    monkeypatch.setattr(narration.voice, "synth", fake)
    assert narration.voice_lines(["Hello."], "en", tmp_path)[1] == "lines" and not fake.takes


# ---- the mix: the music steps back under the voice ---------------------------------------------------------------------------
def test_the_music_is_ducked_under_the_voice_and_comes_back():
    g = narration.graph(3, [0.0, 3.0, 6.5], 9.0, music=True)
    assert [int(x) for x in re.findall(r"adelay=(\d+)\|", g)] == [350, 3250, 6750]
    assert "amix=inputs=3:normalize=0,apad=whole_dur=9.00,volume=1.35,asplit=2[voice][key]" in g
    assert f"[3:a]aresample=48000,volume={narration.BED_GAIN:.2f}[bed]" in g
    assert "[bed][key]sidechaincompress=" in g and "release=" in g     # keyed by the voice; released between lines and at the end
    assert g.endswith("[voice][ducked]amix=inputs=2:normalize=0:duration=first[out]")
    plain = narration.graph(2, [0.0, 3.0], 6.0, music=False)
    assert "sidechaincompress" not in plain and "asplit" not in plain and plain.endswith("volume=1.35[out]")


def test_mix_passes_the_lines_then_the_bed_to_ffmpeg(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(narration.ffmpeg, "run", lambda args, **kw: seen.append(args) or "")
    clips = [tmp_path / "a.wav", tmp_path / "b.wav"]
    out = narration.mix(tmp_path, clips, [0.0, 3.0], 6.0, tmp_path / "bed.wav")
    args = seen[0]
    assert [args[i + 1] for i, a in enumerate(args) if a == "-i"] == [str(c) for c in clips] + [str(tmp_path / "bed.wav")]
    assert "sidechaincompress" in args[args.index("-filter_complex") + 1] and out == tmp_path / "narration.m4a"


def test_render_uses_the_one_take_lines(tmp_path, monkeypatch):
    fake, seen = FakeVoice(), {}
    monkeypatch.setattr(narration.voice, "synth", fake)
    monkeypatch.setattr(narration, "_decode", lambda mp3: take_of(5))
    monkeypatch.setattr(lr.ffmpeg, "run", lambda args, **kw: seen.setdefault("mix", args) and "")
    monkeypatch.setattr(lr.ffmpeg, "probe", lambda p: SimpleNamespace(duration=2.5))

    def make_reel(scenes, out, music=None, **kw):
        seen["scenes"] = scenes
        return Path(out)
    monkeypatch.setattr(lr, "make_reel", make_reel)
    subject, facts, f = lr.reel_facts(LISTING, {})
    script = lr.with_cta(lr.rules_script(f, "hi"), "hi")
    out = lr.render(script, ["a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg"], "hi", tmp_path / "r.mp4", voiced=True)
    assert out == {"audio": "voice+music", "note": ""}
    assert len(fake.takes) == 1 and not fake.lines
    inputs = [seen["mix"][i + 1] for i, a in enumerate(seen["mix"]) if a == "-i"]
    assert [Path(x).name for x in inputs[:5]] == [f"take{i}.wav" for i in range(5)] and inputs[5].endswith("bed.wav")


# ---- the spoken Hindi and Marathi script ---------------------------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_hindi_and_marathi_rules_scripts_are_spoken_sentences_with_the_same_facts(lang):
    for listing in (LISTING,
                    dict(_id="b", transaction="rent", price_inr=45000, city="Pune", locality="Wakad", bhk=1, floor=0, total_floors=4,
                         amenities=["Gate"]),
                    dict(_id="c", transaction="sale", price_inr=12500000, city="Pune", locality="Baner", bhk=3,
                         super_built_up_sqft=1050, floor=3, possession="under_construction", furnishing="furnished"),
                    dict(_id="d", transaction="sale", property_type="plot", city="Pune")):
        subject, facts, f = lr.reel_facts(listing, {})
        script = lr.rules_script(f, lang)
        assert _valid(script, subject + "\n" + "\n".join(f"- {x}" for x in facts)), script
        assert not lr.pushy(script)
        for b in script["beats"]:
            assert not DEVANAGARI.search(b["screen"]) and b["voice"].endswith("।" if lang == "hi" else ".")
            assert "मजला 7" not in b["voice"] and "एकूण" not in b["voice"] and "कुल 22" not in b["voice"]
    subject, facts, f = lr.reel_facts(LISTING, {})
    voices = [b["voice"] for b in lr.rules_script(f, lang)["beats"]]
    if lang == "hi":
        assert voices[:3] == ["Kharadi, Pune में एक 2 BHK अपार्टमेंट, बिक्री के लिए।", "कीमत है 85 लाख रुपये।",
                              "कार्पेट एरिया है 780 स्क्वेयर फीट, और यह 22 मंज़िला बिल्डिंग में 7वीं मंज़िल पर है।"]
    else:
        assert voices[:3] == ["Kharadi, Pune मध्ये एक 2 BHK अपार्टमेंट, विक्रीसाठी.", "किंमत आहे 85 लाख रुपये.",
                              "कार्पेट एरिया आहे 780 स्क्वेअर फूट, आणि हे 22 मजली इमारतीत 7व्या मजल्यावर आहे."]
    assert "Gym, Parking" in voices[3]


def test_the_english_rules_script_is_unchanged():
    subject, facts, f = lr.reel_facts(LISTING, {})
    assert [b["voice"] for b in lr.rules_script(f, "en")["beats"]][:3] == [
        "2 BHK apartment for sale in Kharadi, Pune.", "Price 85 lakh rupees.", "780 square feet carpet area, on floor 7 of 22."]


def test_the_llm_prompt_asks_for_conversational_lines_and_facts_only():
    assert "talks to a friend" in lr.SYSTEM and "never labels" in lr.SYSTEM and "Use ONLY the facts given" in lr.SYSTEM


# ---- the walkthrough caption in the reel's language --------------------------------------------------------------------------
def test_the_caption_follows_the_reel_language_with_the_same_facts():
    attribution = "Listed by Rahul Homes · RERA A51800012345"
    caps = {lang: lr.caption(LISTING, attribution, lang) for lang in ("en", "hi", "mr")}
    assert caps["en"] == lr.caption(LISTING, attribution)          # English stays the default
    assert caps["en"].startswith("2 BHK apartment for sale in Kharadi, Pune\n₹85 Lakh · 780 sq ft carpet")
    assert caps["hi"].startswith("Kharadi, Pune में 2 BHK अपार्टमेंट बिक्री के लिए\n₹85 Lakh · 780 sq ft कार्पेट")
    assert caps["mr"].startswith("Kharadi, Pune येथे 2 BHK अपार्टमेंट विक्रीसाठी\n₹85 Lakh · 780 sq ft कार्पेट")
    for text in caps.values():
        assert attribution in text and "#Avasetu" in text and not re.search(r"[6-9]\d{9}", text)
    assert lr.caption(LISTING, "", "xx") == lr.caption(LISTING, "", "en")
