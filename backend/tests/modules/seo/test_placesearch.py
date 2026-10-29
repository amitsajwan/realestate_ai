"""A search that names a place opens its area page (app/modules/seo/placesearch.py)."""
from app.modules.seo import placesearch

LIVE = [
    {"path": "/projects/area/kharadi/2-bhk", "place": "kharadi", "intent": "all", "bhk": 2, "label": "2 BHK flats"},
    {"path": "/projects/area/kharadi/top", "place": "kharadi", "intent": "top", "bhk": None, "label": "Top projects"},
    {"path": "/projects/area/kharadi/possession-2027", "place": "kharadi", "intent": "all", "bhk": None, "possession": 2027,
     "label": "Possession 2027"},
]


def test_an_area_name_opens_the_area_page():
    assert placesearch.pick("kharadi", LIVE) == {"path": "/projects/area/kharadi", "label": "New projects in Kharadi", "place": "Kharadi"}


def test_a_size_opens_its_live_list_and_a_size_without_one_opens_the_area_page():
    assert placesearch.pick("2 bhk flats in kharadi", LIVE)["path"] == "/projects/area/kharadi/2-bhk"
    assert placesearch.pick("2bhk kharadi", LIVE)["label"] == "2 BHK flats in Kharadi"
    assert placesearch.pick("4 bhk kharadi", LIVE)["path"] == "/projects/area/kharadi"


def test_top_opens_the_top_list():
    assert placesearch.pick("best projects kharadi", LIVE)["path"] == "/projects/area/kharadi/top"


def test_a_project_name_or_a_place_without_a_page_names_nothing():
    assert placesearch.pick("godrej ivara", LIVE) is None
    assert placesearch.pick("", LIVE) is None
