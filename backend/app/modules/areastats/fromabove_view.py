"""What a project page shows of its site from above (areastats.fromabove stores it as `from_above` on the register record):
kept apart, with no imports, so that pages can read it without pulling in the satellite code."""
import math
from typing import Optional, Tuple

PIN_MOVED_M = 50         # a pin moved further than this since the pictures were taken: they are of other ground


def metres_apart(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    dy = (a[0] - b[0]) * 111320
    dx = (a[1] - b[1]) * 111320 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dx, dy)


def public_view(d: dict, pin: Optional[Tuple[float, float]]) -> Optional[dict]:
    """What the page shows: the yearly row, the sentence and the month-by-month loop as /uploads URLs, only while the page's pin
    is within PIN_MOVED_M of where the pictures were taken; None otherwise and for a project with nothing to say."""
    fa = d.get("from_above") or {}
    if fa.get("none") or not fa.get("story") or not fa.get("where") or not fa.get("credit") or pin is None or fa.get("lat") is None \
            or metres_apart(pin, (fa["lat"], fa["lon"])) > PIN_MOVED_M:
        return None
    frames = [{"year": f["year"], "day": f["day"], "src": "/uploads/" + f["path"], "width": f["width"], "height": f["height"],
               "built": f["built"]} for f in fa.get("frames") or [] if f.get("path")]
    if len(frames) < 3:
        return None
    v = fa.get("video") or None
    video = {"src": "/uploads/" + v["path"], "poster": "/uploads/" + v["poster"], "width": v["width"], "height": v["height"],
             "from": v["from"], "to": v["to"], "months": v["months"]} if v and v.get("path") else None
    return {"pin": {"lat": fa["lat"], "lon": fa["lon"]}, "story": fa["story"], "where": fa.get("where"),
            "credit": fa.get("credit"), "frames": frames, "video": video}
