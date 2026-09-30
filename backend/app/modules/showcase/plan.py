"""A proposed posting plan: one sample home every 2 days, alternating channels and areas (no two neighbours share an area)."""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List

from .samples import HOMES

AREAS = ("Kharadi", "Wagholi", "Upper Kharadi")


@dataclass(frozen=True)
class Slot:
    day: date
    slug: str
    locality: str
    channel: str   # 'instagram' | 'facebook'


def schedule_plan(start: date, days: int = 14, every: int = 2) -> List[Slot]:
    used: Dict[str, int] = {}
    slots: List[Slot] = []
    n = (days + every - 1) // every
    for i in range(n):
        area = AREAS[i % len(AREAS)]
        pool = [h for h in HOMES if h.locality == area]
        # the least-used home of that area, ready homes first on ties
        home = min(pool, key=lambda h: (used.get(h.slug, 0), not h.ready, h.slug))
        used[home.slug] = used.get(home.slug, 0) + 1
        slots.append(Slot(start + timedelta(days=i * every), home.slug, area, "instagram" if i % 2 == 0 else "facebook"))
    return slots
