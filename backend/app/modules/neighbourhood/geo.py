"""Small sums every researcher needs: straight-line distance, the km a page says, the middle of a set of pins, and place names.
No database and no network here."""
import math
from statistics import median
from typing import Iterable, Optional, Tuple

from app.core import pune_places


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line (great-circle) distance in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def shown_km(d: float) -> float:
    """What a page says: one decimal under 10 km, whole km beyond. A centre is itself a choice; more would claim too much."""
    return round(d, 1) if d < 10 else float(round(d))


def middle(points: Iterable[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    """The median latitude and longitude of some pins: one pin filed under the wrong place moves it very little, where a mean
    would be pulled towards it (96 Arrcade was filed in Kharadi and stands in Charholi)."""
    pts = list(points)
    if not pts:
        return None
    return round(median(p[0] for p in pts), 6), round(median(p[1] for p in pts), 6)


def key_of(place: str) -> str:
    """A place's key in the register ("viman_nagar") from its page slug ("viman-nagar") or the key itself."""
    return (place or "").strip().lower().replace("-", "_")


def slug_of(key: str) -> str:
    return (key or "").strip().lower().replace("_", "-")


def place_name(place: str) -> str:
    """The name a buyer uses for a place slug or key ("viman-nagar" -> "Viman Nagar"), else the slug in title case."""
    p = pune_places.BY_KEY.get(key_of(place))
    return p.name if p else key_of(place).replace("_", " ").title()


def day_of(v) -> Optional[str]:
    """"YYYY-MM-DD" from a register date (a string, or a datetime), else None; the register's own reading of its dates."""
    s = str(v or "")[:10]
    return s if len(s) == 10 and s[4] == "-" and s[7] == "-" and s[:4].isdigit() else None
