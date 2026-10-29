"""The area page a buyer's search names: "kharadi", "2 bhk kharadi", "top projects in wagholi", "flats in lohegoan".

The project search box (areastats.pages.search) matches project names, so "kharadi" found MahaRERA towers called "Kharadi Pune
Phase I" and "2 bhk kharadi" found nothing (2026-10-29). A search that names one of our places is better answered by its area
page, or by its list for the size or kind asked when that list is live (grow.live_pages); else the place page itself.
"""
import re
from typing import List, Optional

from app.core import pune_places
from app.core.areas import BY_KEY as OUR_AREAS

from . import facets

BHK = re.compile(r"(?<![0-9])([1-4])\s*(?:bhk|bed|bedroom)s?\b", re.I)
KIND = (("ready-to-move", re.compile(r"\bready\b|\brtm\b|\bmove in\b", re.I)),
        ("new-launches", re.compile(r"\bnew launch|\blaunch(es|ed)?\b|\bupcoming\b", re.I)),
        ("top", re.compile(r"\btop\b|\bbest\b", re.I)))


def pick(q: str, live: List[dict]) -> Optional[dict]:
    """{path, label, place} for the page the search names, or None when it names no place we have a page for. `live`: the live
    list pages (grow.live_pages); a size or kind with no live page falls back to the place page, never to a 404."""
    hit = pune_places.in_search(q or "")
    if hit is None:
        return None
    place = hit[0]
    ours = [p for p in live if p.get("place") == place.key]
    if not ours and place.key not in OUR_AREAS:
        return None
    m = BHK.search(q)
    bhk = int(m.group(1)) if m else None
    intent = next((k for k, rx in KIND if rx.search(q)), "all")
    for want_intent, want_bhk in ((intent, bhk), ("all", bhk), (intent, None)):
        page = next((p for p in ours if p["intent"] == want_intent and p.get("bhk") == want_bhk and not p.get("possession")
                     and not p.get("builder") and not (want_intent == "all" and not want_bhk)), None)
        if page:
            return {"path": page["path"], "label": f"{page['label']} in {place.name}", "place": place.name}
    return {"path": f"/projects/area/{facets.place_slug(place.key)}", "label": f"New projects in {place.name}", "place": place.name}
