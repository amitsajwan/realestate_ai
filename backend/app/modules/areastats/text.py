"""The words a project, a builder and a tower are called by: the only place these rules live.

MahaRERA spells a project with its legal suffix, its tower label and a roman numeral. Anything that groups registrations,
builds a slug or writes a name starts here — two copies of these rules decide differently about which towers are one project
(docs/plan/seo-review.md D7: `clusters.py` re-implemented what `pages.py` owned).
"""
import re
import unicodedata
from typing import Optional

WORDS = re.compile(r"[a-z0-9]+")

# Legal-entity words that are not part of what a project is called by
LEGAL = re.compile(r"\b(m s|private|pvt|limited|ltd|llp|the|and|co|company|corporation|corp)\b")

# Labels that introduce a tower / wing / phase identifier — stripped together
# with the identifier that follows (number, roman numeral, or single letter).
# IMPORTANT: require at least one whitespace OR a dash between the label word and the identifier;
# this prevents "towers" in a project name from being consumed as "tower" + "s" identifier.
TOWER_LABEL = re.compile(
    r"\b(towers?|wings?|buildings?|phases?)(?:\s+|[-–]\s*)([0-9]+[a-z]?|[ivxlcdm]+|[a-z])\b",
    re.IGNORECASE,
)
# Reverse-order label: single-letter identifier BEFORE the label word, e.g. "H Building", "A Wing"
REVERSE_LABEL = re.compile(
    r"\b([a-z])\s+(towers|tower|wings|wing|buildings|building)\b",
    re.IGNORECASE,
)
# A lone identifier at the end of the name: "Phase I", "Block C", "– II"
TAIL_ROMAN = re.compile(r"\s+[-–]?\s*([ivxlcdm]+)\s*$", re.IGNORECASE)
TAIL_LETTER = re.compile(r"\s+[-–]?\s*([a-z])\s*$", re.IGNORECASE)
# Separators left over after stripping tokens
NOISE = re.compile(r"[\s\-–&,]+$")


def ascii_text(text: Optional[str]) -> str:
    """Lower-case, accents and non-ASCII letters dropped: the alphabet the rules below match on."""
    return unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()


def words(text: Optional[str]) -> list:
    """The name's words, in the order a searcher types them."""
    return WORDS.findall(ascii_text(text))


def promoter_key(name: Optional[str]) -> str:
    """'M/s. Rohan Builders Pvt. Ltd.' and 'ROHAN BUILDERS PRIVATE LIMITED' -> 'rohan builders'."""
    text = " ".join(WORDS.findall(ascii_text(name)))
    return " ".join(LEGAL.sub(" ", text).split())


def builder_slug(promoter: Optional[str]) -> str:
    """The builder page's slug (/builders/<slug>, pages.hubs): "M/s. Rohan Builders Pvt. Ltd." -> "rohan-builders"."""
    return "-".join(words(promoter_key(promoter)))[:80].strip("-")


def base_name(name: str) -> str:
    """Strip tower / wing / building / phase labels and their identifiers, then trailing roman / letter tokens.

    "Lodha Camelot Tower 1"         → "lodha camelot"
    "Venkatesh Vanaya Phase 1"      → "venkatesh vanaya"
    "Majestique Marbella II"        → "majestique marbella"
    "Manhattan H Building"          → "manhattan"        (label comes BEFORE the identifier)
    "Majestique Towers East Phase 1"→ "majestique towers east"   (mid-name 'towers' is preserved)
    """
    s = ascii_text(name)
    s = TOWER_LABEL.sub(" ", s)
    s = REVERSE_LABEL.sub(" ", s)
    s = TAIL_ROMAN.sub("", s)
    s = TAIL_LETTER.sub("", s)
    s = NOISE.sub("", s).strip()
    s = re.sub(r"\s{2,}", " ", s)
    return s
