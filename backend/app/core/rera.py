"""MahaRERA project registration numbers, both forms: P + 11 digits (P52100078796, older) and P + a letter + 13 digits
(PR1260002501386, current since 2025; our register also holds PP... and PM... numbers). One pattern for every parser;
"Gat No. 123" and a bare "PR" never match."""
import re
from typing import List, Optional

BODY = r"P(?:\d{11}|[A-Z]\d{13})"
SEARCH = re.compile(rf"(?<![A-Za-z0-9]){BODY}(?![A-Za-z0-9])", re.I)   # in running text, not inside a longer code
SPACED = re.compile(r"(?<![A-Za-z0-9])P\s?(?:[A-Z](?:\s?\d){13}|\d(?:\s?\d){10})(?![A-Za-z0-9])", re.I)  # 'P 52100 076768'
FULL = re.compile(BODY, re.I)
EXAMPLE = "PR1260002501386 or P52100078796"
HINT = f"A MahaRERA project number looks like {EXAMPLE}."


def is_rera_no(s: Optional[str]) -> bool:
    return bool(s) and FULL.fullmatch(s.strip()) is not None


def normalise(s: Optional[str]) -> str:
    """'P 52100 076768' -> 'P52100076768', 'pr1260002501386' -> 'PR1260002501386'; '' when it is not one."""
    v = re.sub(r"\s", "", s or "").upper()
    return v if FULL.fullmatch(v) else ""


def find(text: Optional[str]) -> Optional[str]:
    """The first number in the text, upper-cased, or None."""
    m = SEARCH.search(text or "")
    return m.group(0).upper() if m else None


def find_all(text: Optional[str]) -> List[str]:
    """Every number in the text, upper-cased, first seen first, no repeats (a brochure can print several)."""
    out: List[str] = []
    for m in SEARCH.finditer(text or ""):
        v = m.group(0).upper()
        if v not in out:
            out.append(v)
    return out
