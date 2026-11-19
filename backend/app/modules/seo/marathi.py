"""Searches typed in Marathi or Hindi, read into the English words seo.phrases understands (docs/plan/seo-system.md, "Marathi
searches"). Before this, `phrases._norm` kept only a-z and 0-9, so "लोहगाव मध्ये फ्लॅट" became an empty phrase and Marathi
demand counted as nothing. We cannot decide on Marathi pages without knowing how many people search in Marathi, so every
phrase now says its language and the weekly round counts them (grow.collect -> `languages`).

By fixed rules and word lists, never a model, like the rest of the parser:
- place names come from the Devanagari spellings our voices already use (reels.spoken_names), joined to app.core.pune_places;
- the words of a property search ("फ्लॅट", "मध्ये", "नवीन प्रोजेक्ट") come from vocabulary.json "devanagari";
- Marathi endings on a name are taken off ("वाघोलीत", "खराडीमधील", "लोहगावमध्ये");
- Marathi typed in English letters ("kharadi madhe flat") is told apart by its own words (vocabulary.json "roman_marathi").
A Devanagari word we cannot read is kept as it is, so it shows on the unknown words list instead of disappearing.
"""
import re
from functools import lru_cache
from typing import Dict, List, Tuple

from app.core import pune_places
from app.modules.reels.spoken_names import SPOKEN

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
# endings Marathi puts on a place name (in, of, from, near), longest first; Hindi writes them as separate words
ENDINGS = ("मध्ये", "मधील", "मधले", "मधला", "मधली", "मधे", "मधून", "तील", "च्या", "ातील", "ात", "ला", "चा", "ची", "चे", "त")
# the sign of Marathi: words Hindi does not use for a property search
MARATHI_SIGNS = {"मध्ये", "मधील", "मधे", "फ्लॅट", "फ्लॅट्स", "घरे", "प्रकल्प", "नवीन", "किंमत", "पुण्यात", "पुण्यातील",
                 "सदनिका", "जवळ", "आणि", "येथे", "येथील", "मालमत्ता", "ताबा", "विक्रीसाठी"}
HINDI_SIGNS = {"में", "फ्लैट", "मकान", "के", "का", "की", "पास", "नया", "नए", "कीमत", "बिक्री", "प्रॉपर्टी"}


def fold(s: str) -> str:
    """One spelling for the ways people type the same Devanagari word: Hindi's खराड़ी and Marathi's खराडी, लोहगांव and
    लोहगाव, शिक्रापुर and शिक्रापूर (no nukta, no nasal dot, short and long vowels the same)."""
    s = s.translate(DIGITS)
    s = re.sub("[़ँं]", "", s)
    return s.replace("ू", "ु").replace("ी", "ि").replace("ै", "े")


def has_devanagari(phrase: str) -> bool:
    return bool(DEVANAGARI.search(phrase or ""))


@lru_cache(maxsize=1)
def _places() -> Dict[str, str]:
    """{folded Devanagari name: English name} for every name in spoken_names that is a Pune place we list. A name written
    with and without its space ("केशवनगर", "केशव नगर") is both."""
    out: Dict[str, str] = {}
    for en, dev in SPOKEN.items():
        if en == "Pune" or not pune_places.in_search(en):
            continue
        for form in {dev, dev.replace(" ", "")}:
            out[fold(form)] = en
    return out


def _words(vocab: dict) -> Dict[str, str]:
    return {fold(k): v for k, v in (vocab.get("devanagari") or {}).items()}


def _stem(word: str, known: Dict[str, str]) -> Tuple[str, str]:
    """(the word without a Marathi ending, when that leaves a name or word we know; else the word, '')."""
    if word in known:
        return word, ""
    for e in ENDINGS:
        e = fold(e)
        if word.endswith(e) and len(word) > len(e) + 1 and word[: -len(e)] in known:
            return word[: -len(e)], e
    return word, ""


def language(phrase: str, vocab: dict) -> str:
    """"mr" (Marathi in Devanagari), "hi" (Hindi), "deva" (Devanagari, too short to tell), "mr-latn" (Marathi in English
    letters) or "en"."""
    if has_devanagari(phrase):
        words = set(re.findall(r"[ऀ-ॿ]+", phrase))
        if words & MARATHI_SIGNS or any(w.endswith(("मध्ये", "मधील", "तील")) for w in words):
            return "mr"
        if words & HINDI_SIGNS:
            return "hi"
        return "deva"
    latin = set(re.findall(r"[a-z]+", (phrase or "").lower()))
    return "mr-latn" if latin & set(vocab.get("roman_marathi") or ()) else "en"


def to_english(phrase: str, vocab: dict) -> Tuple[str, List[str]]:
    """(the phrase with every Devanagari name and word we know put in English, the Devanagari words we could not read).
    Latin words and digits stay as they are ("2 bhk फ्लॅट वाघोली" -> "2 bhk flats wagholi")."""
    places, words = _places(), _words(vocab)
    known = {**words, **{k: v.lower() for k, v in places.items()}}
    text = fold(phrase or "")
    # names and phrases of two or more words first ("विमान नगर", "रेडी टू मूव्ह"), longest first
    for k in sorted((k for k in known if " " in k), key=len, reverse=True):
        text = re.sub(rf"(?<![ऀ-ॿ]){re.escape(k)}", f" {known[k]} ", text)
    out, unread = [], []
    for w in text.split():
        if not DEVANAGARI.search(w):
            out.append(w)
            continue
        stem, ending = _stem(w, known)
        if stem in known:
            out.append(known[stem])
            if ending:
                out.append("in")
        else:
            unread.append(w)
    return " ".join(out), unread
