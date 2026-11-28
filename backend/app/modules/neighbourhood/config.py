"""Settings for neighbourhood research, read from the environment in one place (CLAUDE.md rule 5).

NEIGHBOURHOOD_ENABLED (default on) runs the loop. Researchers that spend money have their own switch and cap:
NEIGHBOURHOOD_ROUTES (default on when GOOGLE_MAPS_API_KEY is set) measures drive times with Google's Routes API, at most
NEIGHBOURHOOD_ROUTE_ELEMENTS_PER_MONTH route reads a month (owner approved about Rs 1,000 a month, 2026-11-28).
Schools (NEIGHBOURHOOD_SCHOOLS): NEIGHBOURHOOD_SCHOOL_GEOCODES_PER_RUN Google Places calls a run (searches and 30-day re-reads
together, default 300), NEIGHBOURHOOD_SCHOOL_DETAILS_PER_RUN CBSE details pages a run (for pincodes, default 100).
Rent (NEIGHBOURHOOD_RENT): as every place researcher, at most NEIGHBOURHOOD_PLACES_PER_CYCLE places a cycle (the loop's limit);
NEIGHBOURHOOD_RENT_SEARCHES_PER_RUN Serper searches a cycle to find a portal's rent page for a place when its address cannot be guessed (default 10; SERPER_API_KEY).
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
    school_geocodes_per_run: int = 300  # Google Places calls the schools researcher makes in one run
    school_details_per_run: int = 100   # CBSE (SARAS) details pages read in one run, for each school's pincode
    rent_searches_per_run: int = 10     # Serper searches the rent researcher may spend in one loop cycle
    serper_key: str = ""


def load() -> Config:
    key = (os.environ.get("GOOGLE_MAPS_API_KEY") or "").strip()
    return Config(enabled=_flag("NEIGHBOURHOOD_ENABLED", True), google_key=key,
                  routes=_flag("NEIGHBOURHOOD_ROUTES", bool(key)) and bool(key),
                  route_elements_per_month=_int("NEIGHBOURHOOD_ROUTE_ELEMENTS_PER_MONTH", 2000),
                  rent_enabled=_flag("NEIGHBOURHOOD_RENT", True), schools_enabled=_flag("NEIGHBOURHOOD_SCHOOLS", True),
                  places_per_cycle=_int("NEIGHBOURHOOD_PLACES_PER_CYCLE", 10),
                  school_geocodes_per_run=_int("NEIGHBOURHOOD_SCHOOL_GEOCODES_PER_RUN", 300),
                  school_details_per_run=_int("NEIGHBOURHOOD_SCHOOL_DETAILS_PER_RUN", 100),
                  rent_searches_per_run=_int("NEIGHBOURHOOD_RENT_SEARCHES_PER_RUN", 10),
                  serper_key=(os.environ.get("SERPER_API_KEY") or "").strip())
