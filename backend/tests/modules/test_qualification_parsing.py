"""Pure-function tests: message parsing, requirement validation/merging/formatting, matching rules."""
import pytest
from pydantic import ValidationError

from app.modules.tracking import matching
from app.modules.tracking import requirement as rq
from app.modules.tracking.schemas import InquiryIn

from .qual_helpers import listing


def exp(bhk=None, lo=None, hi=None, timeline=None, financing=None):
    out = {}
    if bhk is not None:
        out["bhk"] = bhk
    if lo is not None or hi is not None:
        out["budget_min_inr"], out["budget_max_inr"] = lo, hi
    if timeline:
        out["timeline"] = timeline
    if financing:
        out["financing"] = financing
    return out


L, CR = 100_000, 10_000_000

CASES = [
    ("2bhk under 90 lakh, need it next month, home loan", exp(2, None, 90 * L, "1_3_months", "home_loan")),
    ("Looking for 3 BHK, budget 80-90L", exp(3, 80 * L, 90 * L)),
    ("budget 1.2cr", exp(None, None, 12_000_000)),
    ("85 lakh", exp(None, None, 85 * L)),
    ("under 1 crore", exp(None, None, CR)),
    ("80L-1.2Cr please", exp(None, 80 * L, 12_000_000)),
    ("do bhk chahiye jaldi", exp(2, timeline="now")),
    ("teen BHK flat, 1 to 1.5 cr", exp(3, CR, 15_000_000)),
    ("just looking", exp(timeline="exploring")),
    ("need it asap", exp(timeline="now")),
    ("want to buy immediately", exp(timeline="now")),
    ("planning in 3 months", exp(timeline="1_3_months")),
    ("in 5 months maybe", exp(timeline="3_6_months")),
    ("within 6 months", exp(timeline="3_6_months")),
    ("in 12 months", exp(timeline="exploring")),
    ("3-6 months", exp(timeline="3_6_months")),
    ("1-3 months", exp(timeline="1_3_months")),
    ("cash payment", exp(financing="own_funds")),
    ("I have own funds", exp(financing="own_funds")),
    ("no loan needed", exp(financing="own_funds")),
    ("I will need a home loan", exp(financing="home_loan")),
    ("loan approved already", exp(financing="home_loan")),
    ("Interested in 3 BHK", exp(3)),
    ("2.5 bhk please", exp(2.5)),
    ("4bhk villa", exp(4)),
    ("ek bhk", exp(1)),
    ("1 BHK under 40 lakhs", exp(1, None, 40 * L)),
    ("2 bhk 80 lakh tak", exp(2, None, 80 * L)),
    ("above 2 crore", exp(None, 2 * CR, None)),
    ("budget around 75-85 lac", exp(None, 75 * L, 85 * L)),
    ("hello, interested", {}),
    ("Is 2BHK available?", exp(2)),
    ("1200 sqft 2bhk", exp(2)),
    ("want 3 bhk in 2 months on loan", exp(3, timeline="1_3_months", financing="home_loan")),
    ("next week visit", exp(timeline="now")),
    ("budget 2cr, loan not needed", exp(None, None, 2 * CR, financing="own_funds")),
    ("मुझे 80 लाख में घर चाहिए", exp(None, None, 80 * L)),
    ("1.5 cr max", exp(None, None, 15_000_000)),
    ("no rush, exploring options, 2 bhk 60L", exp(2, None, 60 * L, "exploring")),
    ("Rs 85,00,000 budget", exp(None, None, 85 * L)),
    ("three bhk in Baner, 90 lakhs, abhi jaldi", exp(3, None, 90 * L, "now")),
    ("ready for 2 BHK 75 to 85 lakh, this month, self funded", exp(2, 75 * L, 85 * L, "now", "own_funds")),
    ("", {}),
    (None, {}),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_message_parsing_table(text, expected):
    assert rq.infer_from_message(text) == expected


def test_table_has_enough_samples():
    assert len(CASES) >= 25


# ---- validation ----

def test_requirement_validation():
    assert rq.Requirement(budget_min_inr=1, budget_max_inr=1).budget_max_inr == 1
    for bad in (dict(budget_min_inr=9, budget_max_inr=5), dict(bhk=0), dict(bhk=11), dict(timeline="soon"),
                dict(financing="cash"), dict(budget_min_inr=-1)):
        with pytest.raises(ValidationError):
            rq.Requirement(**bad)


def test_inquiry_body_validation_and_backward_compat():
    old = InquiryIn(agent_slug="rahul", anon_id="anon-visitor-1", name="Amit", phone="9876543210", consent=True)
    assert old.bhk is None and old.timeline is None
    with pytest.raises(ValidationError):
        InquiryIn(agent_slug="rahul", anon_id="anon-visitor-1", name="Amit", phone="9876543210",
                  budget_min_inr=9_000_000, budget_max_inr=5_000_000)
    with pytest.raises(ValidationError):
        InquiryIn(agent_slug="rahul", anon_id="anon-visitor-1", name="Amit", phone="9876543210", timeline="whenever")


# ---- formatting ----

@pytest.mark.parametrize("n,txt", [(8_000_000, "80L"), (12_000_000, "1.2Cr"), (10_000_000, "1Cr"),
                                   (7_500_000, "75L"), (850_000, "8.5L"), (50_000, "50,000")])
def test_fmt_inr(n, txt):
    assert rq.fmt_inr(n) == txt


def test_budget_text_and_line():
    assert rq.budget_text(0, 5_000_000) == "under 50L"
    assert rq.budget_text(8_000_000, 12_000_000) == "80L-1.2Cr"
    assert rq.budget_text(20_000_000, None) == "above 2Cr"
    assert rq.budget_text(None, None) is None
    line = rq.requirement_line({"bhk": 2, "budget_min_inr": 8_000_000, "budget_max_inr": 9_000_000,
                                "localities": ["Baner"], "timeline": "1_3_months"})
    assert line == "2 BHK · 80L-90L · Baner · 1-3 months"
    assert rq.requirement_line({"localities": []}) is None and rq.requirement_line(None) is None


# ---- merging ----

def test_merge_stated_beats_inferred_and_newer_stated_wins():
    m = rq.merge(None, {"bhk": 3}, {"bhk": "stated"})
    m = rq.merge(m, {"bhk": 2}, {"bhk": "inferred"})
    assert m["bhk"] == 3  # inferred never overrides stated
    m = rq.merge(m, {"bhk": 4}, {"bhk": "stated"})
    assert m["bhk"] == 4  # newer stated beats older stated


def test_merge_newer_inferred_replaces_older_inferred_and_defaults_are_weakest():
    m = rq.merge(None, {"bhk": 2}, {"bhk": "inferred"})
    m = rq.merge(m, {"bhk": 3}, {"bhk": "default"})
    assert m["bhk"] == 2  # listing default does not override a parsed value
    m = rq.merge(m, {"bhk": 3}, {"bhk": "inferred"})
    assert m["bhk"] == 3


def test_merge_budget_is_a_pair_and_localities_union():
    m = rq.merge(None, {"budget_min_inr": 1, "budget_max_inr": 9}, {"budget": "inferred"})
    m = rq.merge(m, {"budget_min_inr": None, "budget_max_inr": 5}, {"budget": "inferred"})
    assert (m["budget_min_inr"], m["budget_max_inr"]) == (None, 5)
    m = rq.merge(m, {"localities": ["Baner"]}, {"localities": "default"})
    m = rq.merge(m, {"localities": ["baner", "Wakad"]}, {"localities": "default"})
    assert m["localities"] == ["Baner", "Wakad"]


def test_public_source_and_empty():
    stored = rq.merge(None, {"bhk": 2, "timeline": "now"}, {"bhk": "stated", "timeline": "inferred"})
    assert rq.public(stored)["source"] == "mixed"
    assert rq.public(rq.merge(None, {"bhk": 2}, {"bhk": "stated"}))["source"] == "stated"
    assert rq.public(rq.merge(None, {"bhk": 2}, {"bhk": "inferred"}))["source"] == "inferred"
    assert "field_sources" not in rq.public(stored)
    assert rq.public(None) is None and rq.public(rq.merge(None, {}, {})) is None


# ---- matching ----

REQ = {"bhk": 2, "budget_min_inr": 8_000_000, "budget_max_inr": 9_000_000, "localities": ["Baner"]}


def test_match_full_score_and_reasons():
    pct, reasons = matching.match_listing(REQ, listing("X"), "sale", "apartment")
    assert pct == 100
    assert any("2 BHK" in r for r in reasons) and any("within budget 80L-90L" in r for r in reasons)
    assert "In Baner" in reasons and any("Same property type" in r for r in reasons)


def test_match_partial_budget_and_bhk():
    over = matching.match_listing(REQ, listing("X", price=9_800_000), "sale", "apartment")  # +8.9% over
    assert over[0] == 100 - 20 and any("slightly above" in r for r in over[1])
    far = matching.match_listing(REQ, listing("X", price=12_000_000), "sale", "apartment")
    assert far[0] == 60 and not any("budget" in r for r in far[1])
    below = matching.match_listing(REQ, listing("X", price=7_500_000), "sale", "apartment")
    assert below[0] == 80
    bhk1 = matching.match_listing(REQ, listing("X", bhk=3), "sale", "apartment")
    assert bhk1[0] == 55  # one bedroom off: partial credit, but capped below the 60% recommend threshold
    assert matching.match_listing(REQ, listing("X", locality="Wakad"), "sale", "apartment")[0] == 75


def test_match_transaction_mismatch_excluded_and_unknown_dimensions_neutral():
    assert matching.match_listing(REQ, listing("X", transaction="rent"), "sale") is None
    pct, reasons = matching.match_listing({"bhk": 2}, listing("X"), "sale", None)
    assert pct in (62, 63)  # type/budget/locality earn neutral half credit
    assert reasons == ["2 BHK matches"]


def test_top_matches_filters_sorts_and_limits():
    ls = [listing("A", price=8_800_000), listing("B", price=8_500_000), listing("C", price=8_600_000),
          listing("D", price=8_100_000), listing("E", status="draft"), listing("F", status="sold"),
          listing("G", locality="Wakad", price=1_000_000, bhk=5)]
    out = matching.top_matches(REQ, ls, "sale", "apartment")
    assert [m["listing_id"] for m in out] == ["D", "B", "C"]  # all 100, cheaper first, max 3
    assert all(m["match_pct"] >= 40 for m in out)
    assert matching.top_matches(REQ, [listing("G", locality="Wakad", price=1_000_000, bhk=5)], "sale", "apartment") == []
    assert matching.top_matches({}, ls) == [] and matching.top_matches(None, ls) == []
    under = matching.top_matches(REQ, [listing("U", status="under_offer")], "sale", "apartment")
    assert under and under[0]["listing_id"] == "U"
