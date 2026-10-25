"""The places Pune buyers commute to, for a project page's "distance to work hubs" (docs/plan/project-page-v2.md).

The positions are approximate centres (the campus, the terminal, the station building), good to about 0.005 degrees (~500 m),
set by hand on 2026-10-25. A page gives straight-line distance from them, never a drive time, so that precision is enough.
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class WorkHub:
    name: str
    lat: float
    lon: float


HUBS: Tuple[WorkHub, ...] = (
    WorkHub("EON IT Park, Kharadi", 18.5532, 73.9497),
    WorkHub("World Trade Center, Kharadi", 18.5520, 73.9484),
    WorkHub("Magarpatta City", 18.5155, 73.9280),
    WorkHub("Hinjawadi Phase 1 (Rajiv Gandhi Infotech Park)", 18.5915, 73.7385),
    WorkHub("Pune Airport (Lohegaon)", 18.5797, 73.9089),
    WorkHub("Pune Railway Station", 18.5289, 73.8744),
    WorkHub("Baner-Balewadi High Street", 18.5700, 73.7745),
)
