"""Brochure selling points: the vision read's structured facts, the AI draft's selling_points and warnings, the listing
schema, the offer and amenities angles (confirmed points only, never "pre-launch") and the marketing question."""
import json
from datetime import date
from types import SimpleNamespace

import pytest
from PIL import Image

from app.modules.ai_listing.service import AIListingService
from app.modules.listings.schemas import ListingCreate, ListingUpdate
from app.modules.propertyfacts import boost, campaign, files, points, understand
from app.modules.propertyfacts.facts import Reading, sheet
from app.modules.propertyfacts.gather import listing_readings

GULMOHAR = {"starting_price_inr": "₹2,99,000/-", "booking_amount_inr": "₹1 लाख", "offer_label": "PRE-LAUNCHING OFFER",
            "water": "24 hours", "power": "24 hours", "road_widths_ft": [25, "18", "15 फूट"], "vastu": True,
            "total_acres": "30", "village": "Malthan", "taluka": "Shirur"}


def test_amounts_as_printed():
    assert points.parse_inr("₹2,99,000/-") == 299000
    assert points.parse_inr("₹1 लाख") == 100000
    assert points.parse_inr("१ लाख") == 100000
    assert points.parse_inr("2.99 lakh") == 299000
    assert points.parse_inr("1.2 Cr") == 12000000
    assert points.parse_inr("abc") is None and points.parse_inr(True) is None


def test_clean_facts_parses_and_drops():
    f = points.clean_facts(GULMOHAR)
    assert f == {"starting_price_inr": 299000, "booking_amount_inr": 100000, "offer_label": "PRE-LAUNCHING OFFER",
                 "water": "24 hours", "power": "24 hours", "road_widths_ft": [25, 18, 15], "vastu": True,
                 "total_acres": 30.0, "village": "Malthan", "taluka": "Shirur"}
    bad = points.clean_facts({"offer_label": "High returns assured", "water": "secure income", "booking_amount_inr": 500000,
                              "starting_price_inr": 299000, "village": "मळठण"})
    assert bad == {"starting_price_inr": 299000}   # booking above the price, hype, a non-Latin name: all dropped


class _Resp:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


@pytest.mark.asyncio
async def test_vision_read_merges_facts_across_pages(tmp_path, monkeypatch):
    pages = []
    for i in range(2):
        p = tmp_path / f"page{i}.jpg"
        Image.new("RGB", (60, 80), "white").save(p)
        pages.append(str(p))
    replies = [
        {"claims": ["Pre-launching offer for early buyers", "Plots in Malthan, Shirur"], "rera_no": "", "project_name": "Gulmohar City",
         "language": "mr", "facts": {"starting_price_inr": "₹2,99,000/-", "booking_amount_inr": "₹1 लाख", "offer_label": "Pre-launching offer",
                                     "road_widths_ft": [25, 18, 15], "village": "Malthan"}},
        {"claims": ["30 acre project"], "language": "en",
         "facts": {"starting_price_inr": 350000, "total_acres": 30, "water": "24 hours", "vastu": True}},
    ]
    calls = iter(replies)

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, headers=None):
            return _Resp(__import__("json").dumps(next(calls)))

    from app.modules.photoquality import vision_review
    monkeypatch.setattr(vision_review, "default_clients", lambda: [SimpleNamespace(model="m", url="u", api_key="k", trusted=True)])
    monkeypatch.setattr(files.httpx, "AsyncClient", FakeClient)
    out = await files.read_pages(pages)
    f = out["facts"]
    assert f["starting_price_inr"] == 299000          # the first trusted page wins
    assert f["booking_amount_inr"] == 100000 and f["total_acres"] == 30 and f["water"] == "24 hours" and f["vastu"] is True
    assert out["language"] == "mr"
    assert not any("pre-launch" in c.lower() for c in files.clean_claims(out["claims"]))


class FakeRegister:
    async def all_projects(self):
        return []

    async def project(self, regno):
        return None


@pytest.mark.asyncio
async def test_draft_selling_points_price_and_warnings():
    b = {"text": "", "claims": ["Plots in Malthan, Shirur"], "rera_no": None, "pages": 4, "project_name": "Gulmohar City",
         "facts": points.clean_facts(GULMOHAR), "language": "mr"}
    svc = AIListingService(llm=None)
    d = await svc.from_text("Plots near Ranjangaon", brochure=b, agent_text="")
    assert d.draft["price_inr"] == 299000 and d.sources["price_inr"] == "brochure"
    assert d.draft["total_acres"] == 30.0
    keys = [p["key"] for p in d.selling_points]
    assert keys == ["starting_price", "booking_amount", "offer", "water", "power", "roads", "vastu", "land_area"]
    sp = {p["key"]: p for p in d.selling_points}
    assert sp["starting_price"]["text"] == "Plots from ₹2.99 lakh" and sp["starting_price"]["text_local"] == "₹2.99 लाखांपासून प्लॉट"
    assert sp["booking_amount"]["value"] == 100000 and sp["roads"]["text"] == "Roads 25, 18 and 15 ft wide"
    assert all(p["source"] == "brochure" for p in d.selling_points)
    assert points.WARN_BOOKING in d.warnings and points.WARN_PRELAUNCH in d.warnings


def test_no_booking_warning_at_ten_percent():
    assert points.warnings({"starting_price_inr": 1_000_000, "booking_amount_inr": 100_000}) == []


def test_listing_schema_selling_points():
    body = ListingUpdate(selling_points=[{"key": "starting_price", "text": "Plots from ₹2.99 lakh", "value": "₹2,99,000",
                                          "confirmed": True},
                                         {"key": "roads", "text": "Roads 25, 18 and 15 ft wide", "value": [25, 18, 15]}])
    assert body.selling_points[0].value == 299000 and body.selling_points[1].confirmed is False
    with pytest.raises(ValueError):
        ListingUpdate(selling_points=[{"key": "water", "text": "Assured returns", "value": "24 hours"}])
    with pytest.raises(ValueError):
        ListingUpdate(selling_points=[{"key": "vastu", "text": "a", "value": True}] * 2)
    with pytest.raises(ValueError):
        ListingUpdate(selling_points=[{"key": "vastu", "text": f"x{i}", "value": True} for i in range(13)])
    assert "selling_points" not in ListingUpdate().model_dump(exclude_unset=True)
    assert ListingCreate().model_dump()["selling_points"] is None


def _sp(confirmed=True):
    sp = points.selling_points(points.clean_facts(GULMOHAR), "mr")
    return [{**p, "confirmed": confirmed} for p in sp]


def _facts(confirmed=True):
    from datetime import datetime
    doc = {"project_name": "Gulmohar City", "locality": "Malthan", "property_type": "plot", "transaction": "sale",
           "listing_scope": "layout", "price_inr": 299000, "selling_points": _sp(confirmed)}
    return sheet(listing_readings(doc, datetime(2026, 10, 10)))


def test_offer_and_amenities_only_when_confirmed():
    on = dict(campaign.plan(_facts(True), follow_ups=None, today=date(2026, 10, 10)))
    off = dict(campaign.plan(_facts(False), follow_ups=None, today=date(2026, 10, 10)))
    assert "offer" in on and "amenities" in on and "offer" not in off and "amenities" not in off
    o = on["offer"]
    hook = next(iter(o.hooks.values()))
    assert hook == "Plots from ₹2.99 lakh · Book with ₹1 lakh"
    assert "Balance as per the registered agreement." in o.facts and o.tip == campaign.BALANCE_LINE["en"]
    assert on["amenities"].steps == ["Water: 24 hours", "Power: 24 hours", "Roads 25, 18 and 15 ft wide", "Plots as per vastu"]
    order = [a for a, _ in campaign.plan(_facts(True), follow_ups=None, today=date(2026, 10, 10))]
    assert order.index("offer") < order.index("amenities")
    for b in on.values():   # never the word pre-launch on a card
        assert "launch" not in (b.corpus() + " ".join(b.hooks.values())).lower()
    from app.modules.creative.guards import problems_in
    assert not [p for p in problems_in(hook, o.corpus()) if p.startswith("claim not in facts")]


def test_boost_hook_prefers_the_offer():
    f = boost.Facts(_facts(True))
    assert f.hook().startswith("Plots from ₹2.99L, book with ₹1L")
    assert not boost.Facts(_facts(False)).hook().startswith("Plots from ₹2.99L, book")


def test_marketing_question_and_answer():
    listing = {"property_type": "plot", "listing_scope": "layout", "rera_status": "not_registered", "selling_points": _sp(False)}
    _, ask = understand.decide(listing, {}, False, points=points.pending(listing))
    q = next(q for q in ask if q["key"] == "selling_points")
    assert q["text"].startswith("Use these selling points from the brochure in your posts?") and "Book with ₹1 lakh" in q["text"]
    assert [o["value"] for o in q["options"]] == ["all", "later"]
    done = understand.answer_points(listing, "all")["selling_points"]
    assert all(p["confirmed"] for p in done) and not points.pending({"selling_points": done})
    later = understand.answer_points(listing, "later")["selling_points"]
    assert not any(p["confirmed"] for p in later) and not points.pending({"selling_points": later})
    assert points.confirmed({"selling_points": later}) == {}
    with pytest.raises(ValueError):
        understand.answer_points(listing, "maybe")
