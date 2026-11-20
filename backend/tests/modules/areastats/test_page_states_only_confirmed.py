"""A project page states only what it can stand behind (seo-system rule 9: MahaRERA, the builder's site, or two sites that agree),
in its own voice. An outside review of Godrej Ivara (2026-11-20) found "(not yet confirmed)" amenities and sizes, a size with no
kind of area, and "as housiey.com states" in the cautions: each pinned here."""
from datetime import date, datetime, timezone

from app.modules.areastats import pages, profile
from app.modules.areastats.cautions import cautions

TODAY = date(2026, 11, 20)
DENSE = {"completion_now": "2032-12-16", "completion_at_registration": "2032-08-31", "units_total": 2792, "units_booked": 500}


def land(official: bool, sites=("housiey.com", "squareyards.com")) -> dict:
    return {"facts": [{"key": "land_acres", "value": 12.8, "official": official,
                       "sources": [{"site": s, "url": None} for s in (sites[:1] if official else sites)]}]}


def test_the_density_caution_says_where_the_land_figure_is_from_by_kind_and_never_names_a_portal():
    from_sites = next(c for c in cautions(DENSE, web=land(False), today=TODAY) if c["key"] == "dense")
    assert "2,792 homes on 12.8 acres, from two property sites that agree" in from_sites["text"]
    assert ".com" not in from_sites["text"]
    from_builder = next(c for c in cautions(DENSE, web=land(True, ("godrejproperties.com",)), today=TODAY) if c["key"] == "dense")
    assert "from the builder's website" in from_builder["text"]
    assert ".com" not in from_builder["text"]


def test_one_property_sites_highlight_stays_on_the_record_but_not_on_the_page():
    one = {"topic": "parking", "text": "Basement and visitor parking", "official": False,
           "sources": [{"site": "a.com", "url": "https://a.com", "quote": "Basement and visitor parking"}]}
    two = {"topic": "open_space", "text": "Six towers", "official": False,
           "sources": [{"site": "a.com", "url": "https://a.com", "quote": "6 towers"}, {"site": "b.com", "url": "https://b.com", "quote": "six towers"}]}
    own = {"topic": "amenities", "text": "A clubhouse", "official": True,
           "sources": [{"site": "builder.com", "url": "https://builder.com", "quote": "A clubhouse"}]}
    stored = {"at": datetime(2026, 11, 7, tzinfo=timezone.utc), "highlights": [one, two, own]}
    assert [h["text"] for h in profile.public(stored)["highlights"]] == ["Six towers", "A clubhouse"]
    # the page-text model and the page check still read every highlight MahaRERA does not contradict
    assert len(profile.shown_highlights(stored)) == 3


def test_a_size_from_one_site_or_without_its_kind_of_area_is_not_stated():
    sizes = [{"bhk": "2 BHK", "low": 729, "high": 729, "kind": "carpet area", "official": True, "one_site": False},
             {"bhk": "3 BHK", "low": 875, "high": 1250, "kind": "area kind not stated", "official": False, "one_site": False},
             {"bhk": "4 BHK", "low": 1550, "high": 1650, "kind": "carpet area", "official": False, "one_site": True}]
    assert [x["bhk"] for x in pages.shown_sizes(sizes)] == ["2 BHK"]
    assert pages.shown_sizes(None) == []
