import pytest
from PIL import Image

from app.modules.creative.catalog import LAYOUTS, palettes_for
from app.modules.creative.layouts import all_layouts, render_layout
from app.modules.creative.layouts.base import violations
from app.modules.creative.models import SIZES

from .helpers import build

CASES = [(l, ch) for l in LAYOUTS for ch in ("instagram", "facebook")]


def test_there_are_at_least_eight_layouts():
    assert len(all_layouts()) >= 8


@pytest.mark.parametrize("layout,channel", CASES)
def test_exact_size_and_safe_margins(layout, channel):
    copy, design, _ = build(layout, channel)
    rendered = render_layout(copy, design)
    assert rendered
    for r in rendered:
        assert r.img.size == SIZES[channel] == r.size
        assert violations(r) == [], violations(r)
        assert not any(i.truncated for i in r.items)


@pytest.mark.parametrize("layout", list(LAYOUTS))
def test_nothing_is_cut_by_the_instagram_grid_crop(layout):
    copy, design, _ = build(layout, "instagram")
    for r in render_layout(copy, design):
        x0, x1 = (1080 - 1012) // 2, 1080 - (1080 - 1012) // 2
        for i in r.items:
            assert i.box[0] >= x0 and i.box[2] <= x1, (layout, i.text)


@pytest.mark.parametrize("layout", list(LAYOUTS))
def test_every_allowed_palette_renders_readable_text(layout):
    for pal in palettes_for(layout):
        copy, design, _ = build(layout, "instagram", pal)
        for r in render_layout(copy, design):
            for i in r.items:
                if i.role == "mock":
                    continue
                need = 3.0 if i.size >= 40 else 4.5
                assert i.contrast >= need, (layout, pal, i.text, round(i.contrast, 2))


def test_carousel_returns_cover_slides_and_closing():
    copy, design, _ = build("checklist")
    out = render_layout(copy, design)
    assert len(out) == len(copy.slides) + 2
    assert all(isinstance(r.img, Image.Image) for r in out)


def test_layouts_really_differ():
    """A crude check that the eight layouts are visually different: their downscaled pixels are far apart."""
    thumbs = {}
    for l in LAYOUTS:
        copy, design, _ = build(l)
        thumbs[l] = render_layout(copy, design)[0].img.convert("L").resize((24, 30))
    ids = list(thumbs)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            diff = sum(abs(x - y) for x, y in zip(thumbs[a].getdata(), thumbs[b].getdata())) / 720
            assert diff > 4, (a, b, diff)


def test_unknown_layout_raises():
    copy, design, _ = build("poll")
    design.layout = "nope"
    with pytest.raises(ValueError):
        render_layout(copy, design)
