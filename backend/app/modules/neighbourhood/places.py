"""Which places the research covers and where they are: the place pages of the site (/projects/area/<place>), each with a
centre, and a project's own pin for project pages. Read-only over the register and the place list; the research workstream
fills these in from what areastats already uses for place pages.
"""
from typing import List, Optional, Tuple


async def all_places(db) -> List[str]:
    """Place slugs the research runs for, most important first (the place pages in search before the rest)."""
    return []


async def centre(db, place: str) -> Optional[Tuple[float, float]]:
    """(lat, lon) the place's research is measured from, or None when we have no reliable position."""
    return None


async def project(db, slug: str) -> Optional[dict]:
    """The register document a project page shows, by its page slug, with `place` (its place slug) and its pinned `geo`."""
    return None
