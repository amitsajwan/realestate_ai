"""The Pune areas we cover: one list that every module reads (news register, reach tags, locality pages, replies, reels).

Add an area here, not in a module. Order is the order pages and menus show them. `tier` says who the area mostly serves:
"affordable" (first homes, budget belts) or "it" (IT-corridor buyers). Pincodes are NOT here: several areas share one
(Hinjawadi and Wakad, Keshav Nagar and Mundhwa), so mapping a MahaRERA project to an area lives with the register
(app/modules/newsroom/policy.py), where it is verified against real project records.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class Area:
    key: str                      # stable id used in data: "upper_kharadi"
    name: str                     # display name: "Upper Kharadi"
    slug: str                     # site path: /localities/<slug>
    tier: str                     # "affordable" | "it"
    aliases: Tuple[str, ...] = ()  # other spellings people write, lower case
    hashtags: Tuple[str, ...] = ()  # most specific first; reach adds buyer tags after these

    @property
    def page(self) -> str:
        return f"/localities/{self.slug}"

    @property
    def location_env(self) -> str:
        """Environment variable holding this area's Instagram location (Facebook place) id."""
        return f"IG_LOCATION_{self.key.upper()}"


AREAS: Tuple[Area, ...] = (
    Area("kharadi", "Kharadi", "kharadi", "it", ("kharadi",), ("#KharadiPune", "#KharadiFlats")),
    Area("upper_kharadi", "Upper Kharadi", "upper-kharadi", "affordable", ("upper kharadi", "upper-kharadi"), ("#UpperKharadi", "#KharadiPune")),
    Area("wagholi", "Wagholi", "wagholi", "affordable", ("wagholi",), ("#WagholiPune", "#WagholiHomes")),
    Area("lohegaon", "Lohegaon", "lohegaon", "affordable", ("lohegaon", "lohgaon"), ("#LohegaonPune", "#Lohegaon")),
    Area("keshav_nagar", "Keshav Nagar", "keshav-nagar", "affordable", ("keshav nagar", "keshavnagar", "keshav-nagar"),
         ("#KeshavNagarPune", "#Mundhwa")),
    Area("hinjawadi", "Hinjawadi", "hinjawadi", "it", ("hinjawadi", "hinjewadi"), ("#HinjewadiPune", "#Hinjawadi")),
    Area("wakad", "Wakad", "wakad", "it", ("wakad",), ("#WakadPune", "#Wakad")),
    Area("baner", "Baner", "baner", "it", ("baner",), ("#BanerPune", "#Baner")),
)
BY_KEY: Dict[str, Area] = {a.key: a for a in AREAS}
BY_SLUG: Dict[str, Area] = {a.slug: a for a in AREAS}


def get(key_or_slug: str) -> Optional[Area]:
    k = (key_or_slug or "").strip().lower()
    return BY_KEY.get(k) or BY_SLUG.get(k) or BY_KEY.get(k.replace("-", "_").replace(" ", "_"))


def named_in(text: str) -> Tuple[Area, ...]:
    """Areas named in free text, most specific first ("Upper Kharadi" before "Kharadi"; Kharadi is dropped when only
    Upper Kharadi is meant)."""
    t = f" {(text or '').lower()} "
    found = [a for a in AREAS if any(f"{al}" in t for al in a.aliases)]
    if BY_KEY["upper_kharadi"] in found and t.count("kharadi") == t.count("upper kharadi") + t.count("upper-kharadi"):
        found = [a for a in found if a.key != "kharadi"]
    return tuple(sorted(found, key=lambda a: -max(len(al) for al in a.aliases if al in t)))
