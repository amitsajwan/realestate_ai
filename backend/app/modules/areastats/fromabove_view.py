"""What a project page shows of its site from above (areastats.fromabove stores it as `from_above` on the register record):
kept apart, with no imports, so that pages can read it without pulling in the satellite code."""
import math
from typing import Optional, Tuple

VERSION = 4               # the look's rules (areastats.fromabove.LOOK_VERSION): an older look is not shown
PIN_MOVED_M = 50         # a pin moved further than this since the pictures were taken: they are of other ground


def metres_apart(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    dy = (a[0] - b[0]) * 111320
    dx = (a[1] - b[1]) * 111320 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dx, dy)


def public_view(d: dict, pin: Optional[Tuple[float, float]]) -> Optional[dict]:
    """What the page shows: the yearly row, the summary, each season's line and the video, as /uploads URLs; only under the
    current rules (`version`), while the page's pin is within PIN_MOVED_M of where the pictures were taken, and not when the
    pin was found doubtful (buildings standing before the project registered: the pictures may be a neighbour's)."""
    fa = d.get("from_above") or {}
    if fa.get("none") or fa.get("pin") == "doubtful" or int(fa.get("version") or 1) < VERSION:
        return None
    if not fa.get("story") or not fa.get("where") or not fa.get("credit") or pin is None or fa.get("lat") is None             or metres_apart(pin, (fa["lat"], fa["lon"])) > PIN_MOVED_M:
        return None
    # no share of roofs or concrete: the satellite at 10 m does not tell them from cleared ground (2026-11-20)
    frames = [{"year": f["year"], "day": f["day"], "src": "/uploads/" + f["path"], "width": f["width"], "height": f["height"]}
              for f in fa.get("frames") or [] if f.get("path")]
    if len(frames) < 3:
        return None
    v = fa.get("video") or None
    video = {"src": "/uploads/" + v["path"], "poster": "/uploads/" + v["poster"], "width": v["width"], "height": v["height"],
             "from": v["from"], "to": v["to"], "months": v["months"]} if v and v.get("path") else None
    seasons = [{"label": s["label"], "day": s["day"], "line": s["line"]} for s in fa.get("seasons") or [] if s.get("line")]
    return {"pin": {"lat": fa["lat"], "lon": fa["lon"]}, "story": fa["story"], "where": fa["where"], "credit": fa["credit"],
            "frames": frames, "seasons": seasons, "video": video, "updated": fa["at"].date().isoformat()
            if hasattr(fa.get("at"), "date") else None}
