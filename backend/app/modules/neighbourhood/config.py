"""Settings for neighbourhood research, read from the environment in one place (CLAUDE.md rule 5).

NEIGHBOURHOOD_ENABLED (default on) runs the loop. Researchers that spend money have their own switch and cap:
NEIGHBOURHOOD_ROUTES (default on when GOOGLE_MAPS_API_KEY is set) measures drive times with Google's Routes API, at most
NEIGHBOURHOOD_ROUTE_ELEMENTS_PER_MONTH route reads a month (owner approved about Rs 1,000 a month, 2026-11-28).
"""
import os
from dataclasses import dataclass

TRUE = ("1", "true", "yes", "on")


def _flag(name: str, default: bool) -> bool:
    v = (os.environ.get(name) or "").strip().lower()
    return default if not v else v in TRUE


def _int(name: str, default: int) -> int:
    try:
        return int((os.environ.get(name) or "").strip() or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    enabled: bool = True
    google_key: str = ""
    routes: bool = False
    route_elements_per_month: int = 2000
    rent_enabled: bool = True
    schools_enabled: bool = True
    places_per_cycle: int = 10          # places one researcher handles per loop cycle, so a cycle stays short


def load() -> Config:
    key = (os.environ.get("GOOGLE_MAPS_API_KEY") or "").strip()
    return Config(enabled=_flag("NEIGHBOURHOOD_ENABLED", True), google_key=key,
                  routes=_flag("NEIGHBOURHOOD_ROUTES", bool(key)) and bool(key),
                  route_elements_per_month=_int("NEIGHBOURHOOD_ROUTE_ELEMENTS_PER_MONTH", 2000),
                  rent_enabled=_flag("NEIGHBOURHOOD_RENT", True), schools_enabled=_flag("NEIGHBOURHOOD_SCHOOLS", True),
                  places_per_cycle=_int("NEIGHBOURHOOD_PLACES_PER_CYCLE", 10))
