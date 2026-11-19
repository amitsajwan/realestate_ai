"""Searches typed in Marathi or Hindi are read, not dropped, and counted by language (app/modules/seo/marathi.py, phrases.py,
grow.collect; docs/plan/seo-system.md "Marathi searches")."""
import json
from datetime import datetime, timezone

import httpx
import pytest

from app.modules.newsroom.store import Store
from app.modules.seo import grow, phrases
from app.modules.seo.facets import Facet

from ..fakes import FakeDb

NOW = datetime(2026, 11, 19, tzinfo=timezone.utc)


@pytest.mark.parametrize("search, facet, lang", [
    ("लोहगाव मध्ये फ्लॅट", Facet("lohegaon", "all"), "mr"),
    ("खराडीमध्ये फ्लॅट", Facet("kharadi", "all"), "mr"),
    ("वाघोलीत नवीन प्रोजेक्ट", Facet("wagholi", "new-launches"), "mr"),
    ("विमान नगर मध्ये रेडी टू मूव्ह फ्लॅट", Facet("viman_nagar", "ready-to-move"), "mr"),
    ("२ बीएचके फ्लॅट वाघोली", Facet("wagholi", "all", bhk=2), "mr"),
    ("केशवनगर फ्लॅट", Facet("keshav_nagar", "all"), "mr"),
    ("खराड़ी में फ्लैट", Facet("kharadi", "all"), "hi"),
    ("लोहगांव में फ्लैट", Facet("lohegaon", "all"), "hi"),
    ("kharadi madhe flat", Facet("kharadi", "all"), "mr-latn"),
    ("flats in kharadi", Facet("kharadi", "all"), "en"),
])
def test_a_marathi_or_hindi_search_maps_to_the_same_page_as_its_english_one(search, facet, lang):
    p = phrases.parse(search, {})
    assert p["facet"] == facet and p["lang"] == lang and p["unknown"] == []


def test_a_marathi_word_we_cannot_read_is_kept_as_typed_not_dropped():
    p = phrases.parse("खराडी फ्लॅट स्वस्त", {})
    assert p["place"] == "kharadi" and p["unknown"] == ["स्वस्त"]


def test_a_marathi_search_for_something_we_do_not_hold_goes_on_the_gaps_list():
    p = phrases.parse("वाघोलीमधील प्लॉट", {})
    assert p["place"] == "wagholi" and p["unanswerable"] == ["plot"] and p["facet"] is None


def test_the_weekly_round_counts_searches_by_language_with_their_places_and_impressions():
    rows = [
        {"_id": "लोहगाव मध्ये फ्लॅट", "gsc": {"impressions": 12}, "sources": ["search_console"]},
        {"_id": "वाघोलीत नवीन प्रोजेक्ट", "sources": ["autocomplete"]},
        {"_id": "खराड़ी में फ्लैट", "gsc": {"impressions": 3}, "sources": ["search_console"]},
        {"_id": "flats in kharadi", "gsc": {"impressions": 400}, "sources": ["search_console"]},
    ]
    got = grow.collect(rows, {})
    mr, hi = got["languages"]["mr"], got["languages"]["hi"]
    assert set(got["languages"]) == {"mr", "hi"}
    assert (mr["phrases"], mr["impressions"], mr["autocomplete"]) == (2, 12, 1)
    assert mr["places"] == {"lohegaon": 1, "wagholi": 1}
    assert mr["top"][0] == {"phrase": "लोहगाव मध्ये फ्लॅट", "impressions": 12, "facet": "lohegaon|all"}
    assert (hi["phrases"], hi["impressions"]) == (1, 3)
    # a Marathi search adds its demand to the page it means, beside the English searches for it
    assert "लोहगाव मध्ये फ्लॅट" in got["facets"]["lohegaon|all"]["phrases"]


async def test_the_weekly_probe_asks_google_autocomplete_in_marathi_too(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    asked = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        asked.append((body["q"], body["hl"]))
        return httpx.Response(200, json={"suggestions": [{"value": body["q"] + " 2 bhk"}]})

    store = Store(FakeDb())
    n = await grow.discover(store, NOW, [], 0, httpx.MockTransport(handler))
    english = [q for q, hl in asked if hl == "en"]
    marathi = [q for q, hl in asked if hl == "mr"]
    assert len(english) == len(marathi) == grow.AUTOCOMPLETE_PER_WEEK and n == len(asked)
    assert "खराडी मध्ये फ्लॅट" in marathi
