"""AR-3: the MahaRERA badge on the creative cards (top right, beside or under the kicker chip), scannable, inside the safe area,
and the layouts still pass the critic's checks with it."""
from dataclasses import replace

import pytest

from app.modules.creative.catalog import LAYOUTS
from app.modules.creative.layouts import render_layout
from app.modules.creative.layouts.base import violations
from app.modules.creative.models import SIZES, CardBrand
from app.modules.marketing.maharera import registration

from .helpers import build
from ..qr_helpers import decode

VIEW = "https://maharerait.maharashtra.gov.in/public/project/view/40123"
REG = registration("P52100076768", VIEW)
AGENT = CardBrand("Sharma Realty", "Call / WhatsApp +91 98765 43210", phone="+91 98765 43210", price="₹85 lakh", rera="P52100076768")
BUYER_LAYOUTS = [l for l in LAYOUTS if l != "product_showcase"]   # agent-recruitment posts market no project


def problems(rendered):
    """What the critic would block on: margins, truncation, small text, low contrast."""
    out = set()
    for r in rendered:
        out |= {("margins", r.index)} if violations(r) else set()
        for i in r.items:
            if i.truncated:
                out.add(("truncated", r.index, i.text[:20]))
            if i.role not in ("mock", "ui", "brand", "chip", "meta", "numeral") and i.size < 24:
                out.add(("font", r.index, i.text[:20]))
            if i.role != "mock" and i.contrast < (3.0 if i.size >= 40 else 4.5):
                out.add(("contrast", r.index, i.text[:20]))
    return out


@pytest.mark.parametrize("who", [None, AGENT], ids=["brand", "agent"])
@pytest.mark.parametrize("channel", ["instagram", "facebook"])
@pytest.mark.parametrize("layout", BUYER_LAYOUTS)
def test_badge_scans_and_adds_no_problem(layout, channel, who):
    copy, design, _ = build(layout, channel)
    plain = render_layout(copy, replace(design, brand=who))
    rendered = render_layout(copy, replace(design, brand=who, maharera=REG))
    assert problems(rendered) <= problems(plain), problems(rendered) - problems(plain)
    first, last = rendered[0], rendered[-1]          # the card, or a carousel's cover and its closing slide
    for r in {id(first): first, id(last): last}.values():
        assert r.size == SIZES[channel]
        assert decode(r.img) == VIEW, (layout, r.index)
        texts = [i.text for i in r.items]
        assert "MahaRERA: P52100076768" in texts and "maharera.maharashtra.gov.in" in texts
        badge = next(i for i in r.items if i.text == "MahaRERA: P52100076768")
        assert badge.box[0] > r.size[0] // 3 and badge.box[1] < r.size[1] // 3    # the top right
        hooks = [i for i in r.items if i.role in ("hook", "hero", "label", "myth")]
        assert all(h.box[1] > badge.box[3] for h in hooks), (layout, r.index)       # the headline stays below it


@pytest.mark.parametrize("layout", BUYER_LAYOUTS)
def test_no_badge_without_a_registration(layout):
    copy, design, _ = build(layout, "instagram")
    for r in render_layout(copy, design):
        assert not any(i.text.startswith("MahaRERA:") for i in r.items)
        assert decode(r.img) == ""
