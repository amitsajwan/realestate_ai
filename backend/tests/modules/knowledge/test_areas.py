"""The curated area facts may not say anything our own pages do not: parsed from frontend/lib/marketing/localities.ts and insights.ts like the calendar guards do."""
import re
from pathlib import Path

import pytest

from app.modules.calendar.guards import FRONTEND, PREDICT, PRICE
from app.core import areas as registry
from app.modules.knowledge.areas import AREAS, area_facts, normalise
from app.platform.text import HYPE, PHONE

LOC = FRONTEND / "lib" / "marketing" / "localities.ts"
INS = FRONTEND / "lib" / "marketing" / "insights.ts"
pytestmark = pytest.mark.skipif(not (LOC.is_file() and INS.is_file()), reason="frontend sources are not on this machine")
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def blocks() -> dict:
    """slug -> the text of that locality's block in localities.ts"""
    text = LOC.read_text(encoding="utf-8")
    marks = list(re.finditer(r"^\s{4}slug: '([a-z0-9-]+)'", text, re.M))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[m.group(1)] = text[m.start():end]
    return out


def statements(a):
    return [f for f in a.facts if not f.startswith("Check:")]


def test_the_same_areas_as_the_site_pages():
    assert {a.slug for a in AREAS.values()} == set(blocks())
    assert {normalise(n) for n in ("Kharadi", "upper-kharadi", "Upper  Kharadi", "WAGHOLI")} == {"kharadi", "upper_kharadi", "wagholi"}
    assert area_facts("Nashik") is None and area_facts(None) is None


def test_every_area_in_the_registry_has_facts_and_every_spelling_finds_it():
    assert list(AREAS) == [a.key for a in registry.AREAS]
    for a in registry.AREAS:
        assert AREAS[a.key].slug == a.slug and AREAS[a.key].name == a.name
        for spelling in (a.key, a.slug, a.name, a.name.upper(), *a.aliases):
            assert normalise(spelling) == a.key, spelling
    assert normalise("Hinjewadi") == "hinjawadi" and normalise("Lohgaon") == "lohegaon" and normalise("Keshav  Nagar") == "keshav_nagar"


def _ts_field(block: str, name: str):
    m = re.search(r"(?<![A-Za-z_])" + name + r": (\[[^\]]*\]|'[^']*')", block)
    assert m, f"{name} missing in {block[:60]!r}"
    v = m.group(1)
    return re.findall(r"'([^']*)'", v) if v.startswith("[") else v.strip("'")


def test_the_locality_pages_mirror_the_area_list_in_order_with_the_same_names_tiers_and_spellings():
    """frontend/lib/marketing/localities.ts copies app/core/areas.py (the /localities index groups by tier, the enquiry tags the key)."""
    pages = blocks()
    assert list(pages) == [a.slug for a in registry.AREAS]
    for a in registry.AREAS:
        b = pages[a.slug]
        assert _ts_field(b, "key") == a.key and _ts_field(b, "name") == a.name and _ts_field(b, "tier") == a.tier
        assert _ts_field(b, "aliases") == list(a.aliases)
        assert len(f"locality_{a.key}") <= 40  # the lead source field holds at most 40 characters


@pytest.mark.parametrize("key", list(AREAS))
def test_every_number_in_the_area_facts_is_on_our_pages(key):
    a = AREAS[key]
    corpus = LOC.read_text(encoding="utf-8") + INS.read_text(encoding="utf-8")
    pages = {n.replace(",", "") for n in NUM.findall(corpus)}
    for s in a.facts + tuple(x for pair in a.faq for x in pair):
        assert {n.replace(",", "") for n in NUM.findall(s)} <= pages, s


@pytest.mark.parametrize("key", list(AREAS))
def test_every_name_in_the_area_facts_is_on_our_pages(key):
    """No invented school, mall or campus: a capitalised word mid-sentence must be on the locality's own page or in the insight guides."""
    a = AREAS[key]
    corpus = (LOC.read_text(encoding="utf-8") + INS.read_text(encoding="utf-8")).lower()
    for s in statements(a) + [x for pair in a.faq for x in pair]:
        for m in re.finditer(r"(?<=[a-z,;(] )[A-Z][A-Za-z]+", s):
            assert m.group(0).lower() in corpus, f"{m.group(0)!r} in {s!r}"


@pytest.mark.parametrize("key", list(AREAS))
def test_metro_is_always_approved_not_running_and_only_the_right_lines_per_area(key):
    a = AREAS[key]
    block = blocks()[a.slug]
    for s in a.facts + tuple(pair[1] for pair in a.faq):
        if re.search(r"metro|corridor 2b|line 4", s, re.I) and not s.startswith("Check"):
            assert re.search(r"approved|check the (current|latest)|not running yet|not yet", s, re.I), s
            assert not re.search(r"\bwill (open|run|start|be running)|opens in|coming soon|soon", s, re.I), s
        for line in re.findall(r"Line 4|Corridor 2B", s):
            assert line in block, f"{line} is not on the {a.slug} page"


@pytest.mark.parametrize("key", list(AREAS))
def test_no_prices_predictions_hype_or_phones(key):
    a = AREAS[key]
    for s in a.facts + tuple(x for pair in a.faq for x in pair):
        for rx in (PRICE, PREDICT, HYPE, PHONE):
            assert not rx.search(s), (rx.pattern, s)


@pytest.mark.parametrize("key", list(AREAS))
def test_the_headline_facts_match_the_locality_page(key):
    a = AREAS[key]
    block = blocks()[a.slug].lower()
    if key == "kharadi":
        assert "eon it park" in " ".join(a.facts).lower() and "world trade center pune" in " ".join(a.facts).lower()
        assert "eon it park" in block and "world trade center pune" in block
    if key == "wagholi":
        assert "11.6 km" in " ".join(a.facts) and "11.6 km" in (LOC.read_text(encoding="utf-8"))
    # the commute is always framed as 'try it yourself', never quoted
    assert any("9:00 am and 6:30 pm" in f or "rush hour" in f for f in a.facts)
