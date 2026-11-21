"""What a page shows of Esri's sharp past pictures (areastats.esripast stores it as `esri_past` on the register record or the
area's `area_from_space` document): kept apart, with no imports of the pass, so pages can read it without the HTTP code."""
from typing import Optional, Tuple

from .fromabove_view import PIN_MOVED_M, metres_apart

VERSION = 1


def public_view(d: dict, pin: Optional[Tuple[float, float]]) -> Optional[dict]:
    """{zoom, shots: [{release, captured, source, res}]} oldest first, while the pin is where the captures were looked up and
    there are two or more; None otherwise. The site builds Esri's own tile addresses from `release` (nothing is stored)."""
    ep = d.get("esri_past") or {}
    if int(ep.get("version") or 0) < VERSION or pin is None or ep.get("lat") is None:
        return None
    if metres_apart(pin, (ep["lat"], ep["lon"])) > PIN_MOVED_M:
        return None
    shots = [{"release": int(s["release"]), "captured": s["captured"], "source": s.get("source") or "",
              "res": s.get("res")} for s in ep.get("shown") or [] if s.get("release") and s.get("captured")]
    if len(shots) < 2:
        return None
    return {"zoom": int(ep.get("zoom") or 18), "shots": sorted(shots, key=lambda s: s["captured"])}
