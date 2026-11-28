"""Places of worship never go on a nearby list (owner 2026-11-28): not gathered, not shown from sheets gathered before, not
posted, and not kept from an agent's listing text."""
from app.modules.ai_listing import about
from app.modules.propertyfacts import campaign, public, surroundings

LAT, LON = 18.55, 73.94


def test_no_category_asks_for_or_keeps_places_of_worship():
    assert "temple" not in surroundings.CATEGORIES and "temple" not in surroundings.GOOGLE_TYPES
    assert not any("place_of_worship" in f for _, fs, _ in surroundings.CATEGORIES.values() for f in fs)
    assert surroundings.category({"amenity": "place_of_worship", "religion": "hindu"}) is None
    els = [{"type": "node", "id": 1, "lat": LAT, "lon": LON, "tags": {"amenity": "place_of_worship", "name": "Shiv Mandir"}}]
    assert surroundings.from_overpass(els, LAT, LON) == {}
    assert not surroundings.shown("nearby.temple") and surroundings.shown("nearby.hospital")


def test_an_old_sheet_with_temples_shows_only_the_other_places():
    doc = {"facts": [
        {"key": "located_at", "value": "project", "usable": True},
        {"key": "nearby.temple", "value": [{"name": "Ganesh Temple", "km": 0.3}], "usable": True, "readings": [{"source": "osm"}]},
        {"key": "nearby.hospital", "value": [{"name": "Manipal Hospital", "km": 1.2}], "usable": True,
         "readings": [{"source": "google"}]}]}
    out = public.view(doc)
    assert [n["name"] for n in out["nearby"]] == ["Manipal Hospital"]


def test_campaign_posts_never_list_a_temple():
    assert "temple" not in campaign.NEARBY_ORDER and "temple" not in campaign.CLAIMED_ONLY


def test_an_agents_listing_text_naming_a_temple_keeps_only_the_other_places():
    text = "2 BHK flat. Near Shree Ganesh Mandir, near DPS Pune school, near St Mary's Church."
    raw = {"nearby": [{"type": "other", "name": "Shree Ganesh Mandir"}, {"type": "school", "name": "DPS Pune"},
                      {"type": "other", "name": "St Mary's Church"}]}
    assert [n["name"] for n in about.sanitise_llm_about(raw, text).get("nearby", [])] == ["DPS Pune"]
    assert not any(about._WORSHIP.search(n["name"]) for n in about.extract_about(text).get("nearby", []))
    assert not about._WORSHIP.search("Mathura Heights")
