"""Our names go to every voice in Devanagari (reels.spoken_names, voice.spoken): the one form Google's Indian voices say right."""
import re

from app.core.pune_places import PLACES
from app.modules.reels import voice
from app.modules.reels.spoken_names import PLAIN_WORDS, SPOKEN


def test_every_register_place_has_a_spoken_form():
    missing = []
    for p in PLACES:
        if p.name in SPOKEN:
            continue
        parts = [w for w in re.split(r"\s+and\s+|[()]", p.name) if w.strip()]
        for part in parts:
            words = [w for w in part.split() if w not in PLAIN_WORDS]
            if words and " ".join(words) not in SPOKEN and not all(w in SPOKEN for w in words):
                missing.append(p.name)
    assert not missing, f"add these to reels/spoken_names.py: {missing}"


def test_english_line_says_names_in_devanagari_with_hindi_spelling():
    said = voice.spoken("Buying a flat in Upper Kharadi? Most projects carry Wagholi's PIN, 1,200 sq ft.", "en")
    assert said == "Buying a flat in अपर खराड़ी? Most projects carry वाघोली's PIN, 1,200 square feet."


def test_marathi_keeps_its_spelling_and_captions_stay_latin():
    assert voice.spoken("Kharadi madhe", "mr") == "खराडी madhe"
    assert voice.for_voice("Upper Kharadi", "en") == "Upper Kharadi"   # an English caption keeps the Latin name


def test_a_name_inside_a_word_is_left_alone():
    assert voice.spoken("Susan saw Baner", "en") == "Susan saw बाणेर"
