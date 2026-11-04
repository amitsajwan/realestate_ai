"""Which highlights a page shows (areastats.profile.shown_highlights)."""
from app.modules.areastats import profile


def _h(text):
    return {"topic": "amenities", "text": text, "official": True, "sources": [{"site": "a.com", "quote": text}]}


def test_empty_marketing_lines_are_not_shown_and_stay_on_the_record():
    kept = {"highlights": [_h("Layouts planned for natural light, ventilation and daily comfort"), _h("Covered parking"), _h("Over 35 amenities"), _h("2.48 acres")]}
    assert [h["text"] for h in profile.shown_highlights(kept)] == ["Covered parking", "Over 35 amenities", "2.48 acres"]
    assert len(kept["highlights"]) == 4
