"""The project register (docs/TASKS.md T1.2): one record per MahaRERA registration number in our areas. Pure logic, no I/O;
store.py writes the records. Facts only, each with where and when it came from: no ratings, no opinions about builders.

A project is ours by its pincode (MahaRERA gives the taluka, "Haveli", not the locality) or by an area named in its project name.
News links are made only on a clear match (the registration number, or the full project name in a story about the same
area), because a wrong link on a public project page is worse than none."""
import re
from datetime import datetime
from typing import List, Optional, Tuple

from .policy import AREA_PINCODES
from .stages.filter import named_areas
from .types import MahaReraProject

REGNO = re.compile(r"\bP[A-Z]?\d{9,13}\b")  # PR1260002601907 (current), P52100012345 (older)
# words that do not make a project name specific: "The Element" or "Wing A Phase 2" alone could be anything
_PLAIN = {"the", "a", "an", "of", "and", "at", "in", "by", "phase", "wing", "wings", "building", "buildings", "tower", "towers",
          "cluster", "plot", "sector", "part", "project", "residency", "residences", "homes", "apartments", "mhada"}
MIN_NAME_WORDS = 2  # specific words a name needs before a story that merely contains it is linked


def locality(p: MahaReraProject) -> Optional[Tuple[str, str]]:
    """(area, how we know) for a project in our areas, else None. The pincode wins over the name; within Kharadi's pincode
    a name that says Upper Kharadi is the finer answer."""
    named = named_areas(p.name)
    by_pin = AREA_PINCODES.get((p.pincode or "").strip())
    if by_pin:
        if by_pin == "kharadi" and "upper_kharadi" in named:
            return "upper_kharadi", "pincode and project name"
        return by_pin, "pincode"
    if named:
        return ("upper_kharadi" if "upper_kharadi" in named else named[0]), "project name"
    return None


def records(projects: List[MahaReraProject], now: datetime) -> List[dict]:
    """The fields to store for each in-area project: what the MahaRERA card says, with its source and when we read it."""
    out = []
    for p in projects:
        where = locality(p)
        if where is None:
            continue
        out.append({
            "regno": p.regno, "name": p.name, "promoter": p.promoter, "taluka": p.location, "district": p.district,
            "pincode": p.pincode, "locality": where[0], "locality_from": where[1], "last_modified": p.last_modified,
            "source": "MahaRERA", "source_url": p.url, "checked_at": now,
        })
    return out


def _words(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def specific_name(name: str) -> bool:
    return sum(1 for w in _words(name) if w not in _PLAIN and not w.isdigit() and len(w) > 1) >= MIN_NAME_WORDS


def regnos_in(text: str) -> List[str]:
    return list(dict.fromkeys(REGNO.findall(text or "")))


def names_project(project: dict, text: str) -> bool:
    """True when `text` contains the project's full name, word for word, and the name is specific enough to mean that project."""
    name = _words(project.get("name", ""))
    if not name or not specific_name(project.get("name", "")):
        return False
    return re.search(r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(map(re.escape, name)) + r"(?![a-z0-9])", (text or "").lower()) is not None
