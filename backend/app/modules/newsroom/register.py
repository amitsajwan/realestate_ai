"""The project register (docs/TASKS.md T1.2): one record per MahaRERA registration number in our areas. Pure logic, no I/O;
store.py writes the records. Facts only, each with where and when it came from: no ratings, no opinions about builders.

A project is ours by its pincode (MahaRERA gives the taluka, "Haveli", not the locality) or by an area named in its project name:
policy.AREA_PINCODES / SHARED_PINCODES say which, and why. News links are made only on a clear match (the registration number,
or the full project name in a story about the same area), because a wrong link on a public project page is worse than none."""
import re
from datetime import datetime
from typing import List, Optional, Tuple

from .policy import AREA_PINCODES, NAME_ONLY_PINCODE_PREFIXES, SHARED_PINCODES, UPPER_KHARADI_PINCODES
from .stages.filter import named_areas, other_locality_named
from .types import MahaReraProject

REGNO = re.compile(r"\bP[A-Z]?\d{9,13}\b")  # PR1260002601907 (current), P52100012345 (older)
# words that do not make a project name specific: "The Element" or "Wing A Phase 2" alone could be anything
_PLAIN = {"the", "a", "an", "of", "and", "at", "in", "by", "phase", "wing", "wings", "building", "buildings", "tower", "towers",
          "cluster", "plot", "sector", "part", "project", "residency", "residences", "homes", "apartments", "mhada"}
MIN_NAME_WORDS = 2  # specific words a name needs before a story that merely contains it is linked


def locality(p: MahaReraProject) -> Optional[Tuple[str, str]]:
    """(area, how we know) for a project in our areas, else None."""
    return locality_of(p.name, p.pincode)


def locality_of(name: str, pincode: str) -> Optional[Tuple[str, str]]:
    """(area key, how we know) from a project's name and pincode, else None. An area's own pincode wins over the name
    (unless the name says Upper Kharadi, the finer answer, or names only a locality we do not cover); on a shared pincode the
    name must say which of its areas; elsewhere a name alone counts only near Pune city."""
    named = named_areas(name)
    pin = (pincode or "").strip()
    by_pin = AREA_PINCODES.get(pin)
    if by_pin:
        if pin in UPPER_KHARADI_PINCODES and "upper_kharadi" in named:
            return "upper_kharadi", "pincode and project name"
        if not named and other_locality_named(name):  # "Solitaire Business Hub Viman Nagar" in 411047 is not Lohegaon
            return None
        return by_pin, "pincode"
    shared = [a for a in named if a in SHARED_PINCODES.get(pin, ())]
    if shared:
        return shared[0], "pincode and project name"
    if named and (not pin or pin.startswith(NAME_ONLY_PINCODE_PREFIXES)):
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


_DETAIL_ID = re.compile(r"/public/project/view/(\d+)(?:[/?#]|$)")


def maharera_id(source_url: str) -> Optional[int]:
    """MahaRERA's internal project id from a record's source_url (.../public/project/view/<id>), for its project API."""
    m = _DETAIL_ID.search(source_url or "")
    return int(m.group(1)) if m else None


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
