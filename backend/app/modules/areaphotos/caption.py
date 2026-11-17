"""The caption a scouted photo gets (docs/plan/area-pictures.md step 4): built from the Commons file's own title and the
model's `caption_hint`, then checked in code before it is kept -- never the model's words unchecked. Every credit field
(who took it, its licence, the source link) comes from Commons alone; captions here never carry one."""
import re
from typing import Optional

from app.core.areas import Area
from app.platform import guards, text

from .service import CAPTION_MAX, CAPTION_MIN

_FILE_PREFIX = re.compile(r"^file:", re.I)
_EXT = re.compile(r"\.(jpe?g|png|webp|tiff?|gif)$", re.I)
_NUMBERING = re.compile(r"\s*[\(\[][\d\s,._-]*[\)\]]\s*$")


def clean_title(commons_title: str) -> str:
    """"File:Kharadi bypass road (2).jpg" -> "Kharadi bypass road": Commons' own words for the picture, nothing added."""
    t = _EXT.sub("", _FILE_PREFIX.sub("", commons_title or "").strip())
    t = _NUMBERING.sub("", t)
    return " ".join(re.sub(r"[_-]+", " ", t).split())


def fallback(area: Area, commons_title: str) -> str:
    """A caption made by code alone, when the model's hint cannot be used: the cleaned Commons title, with the area's
    name said if the title does not already say it."""
    cleaned = clean_title(commons_title) or "a view of the area"
    if area.name.lower() in cleaned.lower() or any(al.lower() in cleaned.lower() for al in area.aliases):
        base = cleaned
    else:
        base = f"{area.name}: {cleaned}"
    return base[:CAPTION_MAX]


def _ok(candidate: str, corpus: str) -> bool:
    if not (CAPTION_MIN <= len(candidate) <= CAPTION_MAX):
        return False
    if text.HYPE.search(candidate) or text.PHONE.search(candidate):
        return False
    if guards.unsupported_orgs(candidate, corpus):
        return False
    return True


def build(area: Area, commons_title: str, caption_hint: str) -> str:
    """The caption shown for a scouted photo: the model's hint folded into the cleaned Commons title when it passes the
    checks (no claim of a name the title/area does not have, within length); the code-built fallback otherwise."""
    cleaned = clean_title(commons_title)
    hint = " ".join((caption_hint or "").split())
    corpus = f"{cleaned} {area.name} {' '.join(area.aliases)}"
    if hint:
        combined = hint if area.name.lower() in hint.lower() else f"{area.name}: {hint}"
        if _ok(combined, corpus):
            return combined[:CAPTION_MAX]
    return fallback(area, commons_title)


def reason(area: Area, verdict_shows: tuple, taken_on: str, licence: str) -> str:
    """One short, code-built sentence for the owner: what it shows, when, and its licence -- never written by the model."""
    shows = ", ".join(s.replace("_", " ") for s in verdict_shows[:2]) or "the area"
    year_month = taken_on[:7]
    return f"Shows {area.name}'s {shows}; taken {year_month}; {licence}."
