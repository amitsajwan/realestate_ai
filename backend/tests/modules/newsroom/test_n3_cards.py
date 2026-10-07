"""News cards: sizes, margins inside Instagram's 3:4 safe zone, text that fits, and nothing on a card that is not in the checked facts."""
import re
from pathlib import Path

import pytest
from PIL import Image

from app.modules.newsroom import cards, digest
from app.modules.newsroom import presentation as pr
from app.modules.newsroom.samples import SAMPLES, make_doc

SAFE_X = (1080 - 1012) // 2  # Instagram's profile grid shows the centre 1012 px of the width (3:4 crop of a 4:5 post)


@pytest.mark.parametrize("doc", SAMPLES, ids=lambda d: d["_id"])
@pytest.mark.parametrize("channel,size", [("ig", (1080, 1350)), ("fb", (1080, 1080))])
def test_card_size_margins_and_fit(doc, channel, size):
    img, r, variant = cards.render_card(doc, channel)
    assert img.size == size and variant in cards.VARIANTS
    assert cards.problems(r) == []  # nothing outside the 84 px safe area, no truncation, no overlap
    for it in r.items:
        assert it.box[0] >= SAFE_X and it.box[2] <= 1080 - SAFE_X, it.text  # also inside the 1012 px centre crop
        assert it.box[0] >= 83 and it.box[1] >= 83 and it.box[3] <= size[1] - 83, it.text
        assert not it.truncated
    for s in r.shapes:
        assert s[0] >= 83 and s[2] <= 1080 - 83


def test_variant_rule_figure_photo_headline():
    by_id = {d["_id"]: cards.choose_variant(d) for d in SAMPLES}
    assert by_id["a1b2c3d4e5"] == "figure" and by_id["b2c3d4e5f6"] == "figure" and by_id["e5f6a7b8c9"] == "figure"
    assert by_id["c3d4e5f6a7"] == "photo"          # infrastructure without a figure
    assert by_id["d4e5f6a7b8"] == "headline" and by_id["b8c9d0e1f2"] == "headline"


def test_hook_is_short_our_words_and_cut_at_a_clause():
    long = make_doc("lh", "Pune Ring Road eastern stretch gets approval from the state cabinet after months of review, with land work next",
                    ["The state cabinet approved the eastern stretch."], "infrastructure", ["kharadi"], "Times of India")
    h = pr.hook(long)
    assert len(h.split()) <= pr.HOOK_MAX_WORDS and h.split()[0] == "Pune"
    for d in SAMPLES:
        assert 2 <= len(pr.hook(d).split()) <= 12


def test_everything_on_a_card_comes_from_the_item():
    """Digits and money on the card must occur in the hook, the facts or the as-of line: nothing is invented."""
    for d in SAMPLES:
        allowed = " ".join([pr.headline(d), pr.hook(d), pr.support_line(d), pr.as_of_label(d), pr.source_name(d),
                            *(f["text"] for f in d["facts"]["facts"])])
        _, r, _ = cards.render_card(d, "ig")
        for it in r.items:
            for num in re.findall(r"\d[\d,.]*", it.text):
                assert num.rstrip(".,") in allowed, (d["_id"], it.text)


def test_figure_card_enlarges_a_figure_already_in_the_hook():
    d = SAMPLES[0]
    value, hook = pr.figure(d)
    assert value == "₹10,502 crore" and value in hook
    assert pr.figure(SAMPLES[2]) is None and pr.figure(SAMPLES[3]) is None


def test_chip_source_and_as_of_are_on_the_card():
    _, r, _ = cards.render_card(SAMPLES[2], "ig")
    texts = " | ".join(i.text for i in r.items)
    assert "NEWS · INFRASTRUCTURE" in texts and "Source: The Indian Express" in texts and "As of 29 Sep 2026" in texts
    assert "Illustrative photo" in texts  # the stock photo is labelled


def test_render_item_saves_both_jpegs_under_news(tmp_path):
    out = cards.render_item(SAMPLES[0], tmp_path)
    assert out["ig"] == "news/a1b2c3d4e5-ig.jpg" and out["fb"] == "news/a1b2c3d4e5-fb.jpg"
    for rel, size in ((out["ig"], (1080, 1350)), (out["fb"], (1080, 1080))):
        p = Path(tmp_path) / rel
        assert Image.open(p).size == size and p.stat().st_size < 400_000


def test_a_very_long_headline_still_fits_by_shrinking_or_shortening():
    d = make_doc("lg", "Pune Metro corridor 2B between Ramwadi and Wagholi receives final clearance for construction after long consultations",
                 ["Metro corridor 2B between Ramwadi and Wagholi received final clearance for construction."], "infrastructure", ["wagholi"],
                 "Hindustan Times Pune Edition")
    for ch in ("ig", "fb"):
        _, r, _ = cards.render_card(d, ch)
        assert cards.problems(r) == []


def test_digest_carousel_is_cover_stories_tip_and_closing(tmp_path):
    dg = digest.sample_digest(SAMPLES)
    out = cards.render_digest(dg, tmp_path)
    assert len(out["ig"]) == 1 + 5 + 1 + 1 <= 10 and out["fb"].endswith("-fb.jpg")
    for rel in out["ig"]:
        assert Image.open(Path(tmp_path) / rel).size == (1080, 1350)
    assert Image.open(Path(tmp_path) / out["fb"]).size == (1080, 1080)


def test_render_doc_dispatches_between_story_and_digest(tmp_path):
    assert "digest" not in cards.render_doc(SAMPLES[1], tmp_path)["ig"]
    assert isinstance(cards.render_doc(digest.sample_digest(SAMPLES), tmp_path)["ig"], list)
