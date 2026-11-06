"""Buyers search a project with its builder's brand in front ("Kolte Patil Life Republic"); MahaRERA's name often lacks it
(docs/plan/rival-housiey-ravet.md L4)."""
from app.modules.areastats import brands, pages


def test_a_brand_the_record_joins_by_promoter_goes_before_a_name_that_lacks_it():
    assert pages.branded_name({"name": "IVARA", "promoter": "Godrej Properties Limited"}) == "Godrej Ivara"
    assert pages.branded_name({"name": "Life Republic", "promoter": "Kolte Patil I-Ven Townships (Pune) Ltd"}) == "Kolte Patil Life Republic"


def test_no_brand_when_the_name_has_it_the_owner_named_it_or_the_promoter_is_a_land_company():
    assert pages.branded_name({"name": "Godrej Ivara", "promoter": "Godrej Properties Limited"}) is None
    assert pages.branded_name({"name": "Rohan Abhilasha", "promoter": "Rohan Builders (India) Pvt Ltd"}) is None
    assert pages.branded_name({"name": "Ganga Florentina", "promoter": "Goel Ganga Developers"}) is None
    assert pages.branded_name({"name": "Joyville Hinjawadi", "promoter": "Shapoorji Pallonji Real Estate"}) is None
    assert pages.branded_name({"name": "Ivara", "promoter": "Godrej Properties", "marketed_name_override": "Godrej Ivara"}) is None
    assert pages.branded_name({"name": "Sarita Niketan", "promoter": "Manjari Housing Projects LLP"}) is None
    assert pages.branded_name({"name": "The Unicorn", "promoter": ""}) is None


def test_the_brand_word_drops_the_company_words_buyers_do_not_type():
    by = brands.BY_SLUG
    assert [pages.brand_word(by[s]) for s in ("godrej-properties", "vilas-javdekar", "shapoorji-pallonji", "k-raheja-corp")] == \
        ["Godrej", "Vilas Javdekar", "Shapoorji Pallonji", "K Raheja"]
