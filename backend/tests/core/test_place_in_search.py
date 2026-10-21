"""A place in a buyer's search, however it is spelt (app/core/pune_places.in_search, app/core/areas.in_search)."""
import json
from pathlib import Path

import pytest

from app.core import areas, pune_places


@pytest.mark.parametrize("q,key", [
    ("flats in lohegoan", "lohegaon"), ("properties in lohgaon pune", "lohegaon"), ("2 bhk flats in vagholi", "wagholi"),
    ("flats in hinjwadi", "hinjawadi"), ("new projects kharedi", "kharadi"), ("flats in kondwa", "kondhwa"),
    ("viman nagr flats", "viman_nagar"), ("talegoan flats", "talegaon"), ("projects in upper kharadi", "upper_kharadi"),
    ("akurdi flats", "akurdi"), ("oundh flats", "aundh"),
])
def test_place_however_spelt(q, key):
    hit = pune_places.in_search(q)
    assert hit is not None and hit[0].key == key


@pytest.mark.parametrize("q", ["flats in pune", "ready to move flats", "possession 2027 projects", "property rates", "top 10 builders",
                               "gated community", "under construction projects"])
def test_no_place_guessed(q):
    assert pune_places.in_search(q) is None


def test_no_buyer_word_sounds_like_a_place():
    v = json.loads((Path(pune_places.__file__).parents[1] / "modules" / "seo" / "vocabulary.json").read_text())
    words = {w for k, x in v.items() if k != "_about" for ys in (x.values() if isinstance(x, dict) else [x]) for y in ys
             for w in y.split()}
    words |= {"flats", "apartments", "properties", "houses", "resale", "rental", "possession", "builders", "township", "budget"}
    assert [w for w in words if pune_places.in_search(w)] == []


def test_shared_sounds_are_never_used():
    # Kharadi and Akurdi would both be "krd" without the leading vowel: each sound names one place only
    keys = {}
    for p in pune_places.PLACES:
        for al in (p.name.lower(),) + p.aliases:
            keys.setdefault(pune_places.sound(al), set()).add(p.key)
    assert all(len(keys[k]) == 1 for k in pune_places.SOUNDS)


def test_areas_in_search_falls_back_to_the_sound():
    assert [a.key for a in areas.in_search("flats in lohegoan")] == ["lohegaon"]
    assert areas.in_search("flats in pune") == ()
