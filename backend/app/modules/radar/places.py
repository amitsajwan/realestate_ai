"""Where the radar looks: the site's areas (app/core/areas.py) plus radar-only places that have a project we sell but no
locality page yet. A radar-only place links to its project page and has its own searches (plots, not flats, for Gulmohar City).
Promote a place to app/core/areas.py once its area facts are written; then delete it here."""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from app.core import areas as site


@dataclass(frozen=True)
class Place:
    key: str
    name: str
    page: str                       # where a reply sends people
    listing_locality: str           # listings.locality of what we sell there
    aliases: Tuple[str, ...]
    queries: Tuple[str, ...]        # YouTube searches


EXTRA: Tuple[Place, ...] = (
    # Gulmohar City (MahaRERA P52100076768): plots near Ranjangaon MIDC, Shirur taluka; listing locality is "Shirur"
    Place("ranjangaon", "Ranjangaon", "/projects/gulmohar-city-pune", "Shirur",
          ("ranjangaon", "ranjangaon midc", "रांजणगाव", "shirur", "शिरूर", "karegaon", "gulmohar city"),
          ("Ranjangaon plots", "Ranjangaon MIDC plot for sale", "Shirur Pune plots", "Gulmohar City Ranjangaon",
           "रांजणगाव प्लॉट")),
)
BY_KEY: Dict[str, Place] = {p.key: p for p in EXTRA}
SITE_QUERY_TEMPLATES = ("{area} Pune flats", "{area} Pune 2 BHK project review", "{area} पुणे फ्लॅट")


def all_places() -> Tuple[Place, ...]:
    own = tuple(Place(a.key, a.name, a.page, a.name, a.aliases, tuple(t.format(area=a.name) for t in SITE_QUERY_TEMPLATES))
                for a in site.AREAS)
    return own + EXTRA


def keys() -> Tuple[str, ...]:
    return tuple(p.key for p in all_places())


def get(key: str) -> Optional[Place]:
    k = (key or "").strip().lower()
    if k in BY_KEY:
        return BY_KEY[k]
    a = site.get(k)
    return next((p for p in all_places() if p.key == a.key), None) if a else None


def named_in(text: str) -> Optional[Place]:
    """The site's own matcher first (it knows Upper Kharadi vs Kharadi), then radar-only places."""
    found = site.named_in(text)
    if found:
        return get(found[0].key)
    t = (text or "").lower()
    return next((p for p in EXTRA if any(al in t for al in p.aliases)), None)
