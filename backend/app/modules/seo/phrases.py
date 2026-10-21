"""What a buyer's search asks for, as a facet (docs/plan/area-intent-pages.md 11.2), by fixed rules and the word list in
vocabulary.json. Never by a model: a phrase either maps to a page we can answer from MahaRERA's records, to a page type we
already have (BHK and budget pages, from agents' listings), or it is kept with the words we did not understand.

parse(phrase, builders) -> {
  facet:       a seo.facets.Facet, or None;
  existing:    the path of an existing page type that answers it (seo.gaps.template: 2/3 BHK, budget pages), or None;
  place:       the Pune place key it names, or None;
  unanswerable: words naming something our records do not hold ("gated community", "plots");
  unknown:     the other words we did not understand (the weekly unknown-words list).
}
"""
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.core import pune_places

from . import gaps
from .facets import BHKS, FIRST_YEAR, LAST_YEAR, Facet

VOCAB = Path(__file__).with_name("vocabulary.json")
# words in builders' names that say nothing about which builder ("Kolte Patil Developers" is "kolte patil")
GENERIC = {"developers", "developer", "builders", "builder", "group", "realty", "realtors", "properties", "property", "infra",
           "infrastructure", "constructions", "construction", "ltd", "limited", "pvt", "private", "llp", "estates", "estate",
           "promoters", "homes", "housing", "projects", "lifespaces", "spaces", "ventures", "enterprises", "and", "co", "the",
           "india", "pune", "shree", "shri", "sai", "new", "m", "s"}


@lru_cache(maxsize=1)
def vocabulary() -> dict:
    return json.loads(VOCAB.read_text(encoding="utf-8"))


def _norm(s: str) -> str:
    return " " + re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip() + " "


def _take(text: str, phrase: str) -> Tuple[bool, str]:
    """Whether the phrase is in the text as whole words; the text with it blanked out."""
    p = _norm(phrase)
    if len(p) > 2 and p in text:
        return True, text.replace(p, " ")
    return False, text


def _blank(text: str, phrase: str) -> str:
    p = _norm(phrase)
    return text.replace(p, " ") if len(p) > 2 else text


def _place(text: str) -> Tuple[Optional[str], str]:
    """The place a search names, however it is spelt ("lohegoan" is Lohegaon: pune_places.in_search), and the text without it."""
    hit = pune_places.in_search(text)
    if hit is None:
        return None, text
    return hit[0].key, text.replace(_norm(hit[1]), " ")


def builder_names(builders: List[dict]) -> Dict[str, str]:
    """{short name people type: builder slug}, e.g. {"kolte patil": "kolte-patil-developers"}; names shared by two builders
    are left out (we never guess which one)."""
    seen: Dict[str, set] = {}
    for b in builders:
        slug = b.get("slug") or ""
        short = " ".join(w for w in slug.split("-") if w not in GENERIC)
        if len(short.replace(" ", "")) >= 4:
            seen.setdefault(short, set()).add(slug)
    return {k: next(iter(v)) for k, v in seen.items() if len(v) == 1}


def parse(phrase: str, builders: Optional[Dict[str, str]] = None) -> dict:
    v = vocabulary()
    text = _norm(phrase)
    out: dict = {"facet": None, "existing": None, "place": None, "unanswerable": [], "unknown": []}
    for w in sorted(v["unanswerable"], key=len, reverse=True):
        hit, text2 = _take(text, w)
        if hit:
            out["unanswerable"].append(w)
            text = text2
    # "2 bhk flats in lohegaon" (and "2 bhk flat price in ...") is a size page drawn from published prices; a budget ("under 50
    # lakh") or a size we have no page for goes to the existing page types
    size = re.search(r"\b(\d)(?:\.5)?\s*bhk\b", phrase.lower())
    bhk = int(size.group(1)) if size and int(size.group(1)) in BHKS else None
    if bhk:
        text = re.sub(r" \d(?: 5)? ?bhk ", " ", text)
    budget = [w for w in v["existing_pages"] if w not in v["size_price_words"]]
    if any(_norm(w) in text for w in budget) or (size and not bhk) or (not bhk and any(_norm(w) in text for w in v["existing_pages"])):
        out["existing"] = gaps.template(phrase, list((builders or {}).values()))
        return out
    for w in v["size_price_words"]:
        text = _blank(text, w)
    place, text = _place(text)
    out["place"] = place
    builder = None
    for short, slug in sorted((builders or {}).items(), key=lambda x: -len(x[0])):
        hit, text = _take(text, short)
        if hit:
            builder = slug
            break
    possession = None
    if any(_norm(w) in text for w in v["possession_words"]):
        m = re.search(r"\b(20\d\d)\b", text)
        if m and FIRST_YEAR <= int(m.group(1)) <= LAST_YEAR:
            possession = int(m.group(1))
        for w in v["possession_words"]:
            text = _blank(text, w)
    intent = None
    for name in ("ready-to-move", "new-launches", "top", "all"):
        for w in sorted(v["intents"][name], key=len, reverse=True):
            hit, text = _take(text, w)
            if hit and intent is None:
                intent = name
    for w in sorted(v["stop"], key=len, reverse=True):
        text = _blank(text, w)
    out["unknown"] = [w for w in text.split() if not w.isdigit() and len(w) > 1]
    if bhk and intent is None:
        intent = "all"
    if place and intent and not out["unanswerable"]:
        out["facet"] = Facet(place, intent, possession, builder, bhk)
    return out
