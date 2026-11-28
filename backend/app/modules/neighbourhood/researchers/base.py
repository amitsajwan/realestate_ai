"""What every researcher is. One file per kind of fact (commute.py, schools.py, ...), listed in researchers/__init__.py.

A researcher has:
- `kind`: its stable name, the key of its block on pages ("commute", "schools", "rent", "profile", "being_built", "jobs").
- `every`: how old its data may get before the loop runs it again for a place.
- `scope`: "place" (run once per place page, /projects/area/<place>) or "city" (once for all of Pune, stored under store.CITY).
- `run(ctx, place)`: gather and return Found(data, sources), or None when there is nothing to store. Raise only for a failure
  worth retrying; the loop notes it and keeps the last good data.
- `present(data, view)`: turn stored data into the block a page shows for a place or a project, or None to hide the block (too
  few listings, too few schools: a thin block is worse than none). `view` carries the place and, on a project page, the
  project's own pin, so distances are measured from the project and not the area's centre.
- `enabled(cfg)`: whether it runs at all (paid researchers have their own switch in config.py).
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, List, Optional


@dataclass
class Found:
    data: Any
    sources: List[dict]   # [{"name", "url"?, "read_on": "YYYY-MM-DD"}]


@dataclass
class Context:
    db: Any
    store: Any
    now: datetime
    cfg: Any
    http: Any = None       # an httpx.AsyncClient the loop opens once per cycle (tests pass one with a MockTransport)


@dataclass
class ViewContext:
    place: str                         # place slug, as in /projects/area/<place>
    lat: Optional[float] = None        # the project's pinned position, on a project page
    lon: Optional[float] = None
    project: Optional[dict] = None     # the register document, on a project page
    now: Optional[datetime] = None


def _always(cfg: Any) -> bool:
    return True


@dataclass
class Researcher:
    kind: str
    every: timedelta
    run: Callable[[Context, str], Awaitable[Optional[Found]]]
    present: Callable[[Any, ViewContext], Optional[dict]]
    scope: str = "place"
    enabled: Callable[[Any], bool] = field(default=_always)
