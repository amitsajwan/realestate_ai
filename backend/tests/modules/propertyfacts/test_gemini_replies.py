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
