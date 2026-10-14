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


def squash(base: str) -> str:
    """A base name with its spaces gone, so a spelling with or without a space is one project: "palm nest" = "palmnest"."""
    return re.sub(r"[^a-z0-9]", "", base or "")


# words that only label a tower or phase: never the end of a project's name
LABEL_WORDS = {"tower", "towers", "wing", "wings", "building", "buildings", "bldg", "phase", "phases", "block", "plot", "sector"}
ROMAN = re.compile(r"^[ivxlcdm]+$", re.I)


def _cased(tokens: list) -> list:
    """Capitals as people write them when MahaRERA filed in capitals: "ROHAN ABHILASHA" -> "Rohan Abhilasha"; acronyms
    (no vowel: "VTP", "VNSVL") and roman numerals stay."""
    if not tokens or not all(t.isupper() or t.isdigit() for t in tokens):
        return tokens
    return [t if t.isdigit() or ROMAN.match(t) and len(t) <= 4 or not re.search(r"[AEIOUY]", t) else t.capitalize() for t in tokens]


def _tokens(name: str) -> list:
    return re.findall(r"[A-Za-z0-9]+", unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode())


def group_name(names: list) -> str:
    """The name one project's registrations share, as people write it: the words all of them start with, without a trailing
    tower or phase label. ["ROHAN ABHILASHA BUILDING A", "Rohan Abhilasha Building C"] -> "Rohan Abhilasha";
    ["Hinjewadi Phase 3 - Tower 15", "Hinjewadi Phase 3-Tower 1"] -> "Hinjewadi Phase 3". When they share no first word
    ("PALM NEST PHASE I", "PALMNEST PHASE III") it is the first name without its tower label. The spelling comes from a name
    in mixed case when there is one (MahaRERA often files in capitals)."""
    names = [n for n in names if n]
    lists = [words(n) for n in names]
    if not lists:
        return ""
    k = 0
    while all(len(w) > k and w[k] == lists[0][k] for w in lists):
        k += 1
    while k and lists[0][k - 1] in LABEL_WORDS:
        k -= 1
    if not k:   # spelt apart: the first name's own base ("palm nest"), in its own spelling
        base = base_name(names[0]).split()
        return " ".join(_cased(_tokens(names[0])[:len(base)])) if base else ""
    source = next((n for n in names if not n.isupper() and words(n)[:k] == lists[0][:k]), names[0])
    return " ".join(_cased(_tokens(source)[:k]))
