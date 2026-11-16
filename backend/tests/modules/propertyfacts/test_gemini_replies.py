"""Gemini wraps its JSON in a list: the pilot on KP Supernova's brochure lost all 25 page labels to it (2026-11-07)."""
import json

from app.modules.propertyfacts import brochure_triage
from app.platform import gemini


def test_page_labels_in_a_bare_list_are_kept():
    labels = brochure_triage.clean([{"page": 16, "kind": "floor_plan", "other_project": False, "cgi": False, "note": "2 BHK"}], [16])
    assert labels[16]["kind"] == "floor_plan"


def test_page_labels_in_the_asked_shape_still_work():
    assert brochure_triage.clean({"pages": [{"page": 1, "kind": "cover"}]}, [1])[1]["kind"] == "cover"


async def test_a_reading_wrapped_in_a_list_is_the_reading(monkeypatch):
    async def post(model, body, timeout):
        return [{"text": json.dumps([{"unit_plan": True}])}]
    monkeypatch.setattr(gemini, "_post", post)
    assert await gemini.read([b"\xff\xd8x"], "read") == {"unit_plan": True}


def test_a_one_page_brochures_label_arrives_unwrapped_and_is_kept():
    assert brochure_triage.clean({"page": 1, "kind": "floor_plan"}, [1])[1]["kind"] == "floor_plan"


async def test_the_model_judges_each_picture_once_and_the_word_count_gate_reads_its_verdict(tmp_path):
    from PIL import Image
    from app.modules.propertyfacts import listing_posts
    clean, advert = str(tmp_path / "clean.jpg"), str(tmp_path / "advert.jpg")
    Image.new("RGB", (900, 700), (90, 120, 150)).save(clean)
    Image.new("RGB", (900, 700), (200, 80, 60)).save(advert)
    asked = []

    async def ask(images, prompt):
        asked.append(prompt)
        return {"advert": len(asked) == 2}
    assert await listing_posts.judge_pictures([clean, advert], ask) == 2
    assert listing_posts.printed_words(clean) == 0 and listing_posts.printed_words(advert) == 99
    assert await listing_posts.judge_pictures([clean, advert], ask) == 0 and len(asked) == 2


def test_shops_are_not_called_homes():
    from app.modules.propertyfacts import listing_posts
    assert listing_posts.units_word({"property_type": "office"}) == "Shops and offices"
    assert listing_posts.units_word({"property_type": "apartment"}) == "Homes"


def test_a_project_with_a_confirmed_size_is_not_asked_one_or_many_again():
    from app.modules.propertyfacts import understand
    listing = {"property_type": "apartment", "listing_scope": "layout", "carpet_sqft": 810, "bhk": 2, "rera_no": "PM1260002501030"}
    _, ask = understand.decide(listing, {}, True)
    assert "scope_check" in [q["key"] for q in ask]
    _, ask = understand.decide({**listing, "size_min_sqft": 810, "size_max_sqft": 810}, {}, True)
    assert "scope_check" not in [q["key"] for q in ask]


def test_a_price_row_of_a_shop_is_not_called_a_home():
    from app.modules.propertyfacts import listing_posts
    assert listing_posts.row_label({"property_type": "office"}, {"label": "Home"}) == "Shop/office"
    assert listing_posts.row_label({"property_type": "apartment"}, {"label": "Home"}) == "Home"
    assert listing_posts.row_label({"property_type": "office"}, {"label": "2 BHK"}) == "2 BHK"
