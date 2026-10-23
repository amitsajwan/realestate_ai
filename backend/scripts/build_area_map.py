"""One-time: draw an area's street map from OpenStreetMap for its "most active projects" map (app/modules/areastats/areamap.py).

Reads the streets, the river and the parks inside the area's box (areamap.MAPS[area].box) from the Overpass API, or from a saved
answer (--osm), and writes a plain SVG in the site's colours to frontend/public/maps/<area slug>.svg. The picture is drawn for
exactly that box, so the page can place a pin at (lon - west) / (east - west), (north - lat) / (north - south) of its size.
Labels: the roads buyers know by name (LABELS, along the road) and the area's own place names (PLACES below). Map data © OpenStreetMap
contributors (ODbL): the page shows that line under the map.

  PYTHONPATH=. python scripts/build_area_map.py upper_kharadi [--osm saved-overpass.json]

Run it again only when the box changes or the streets have changed a lot (a new road): a year is plenty.
"""
import argparse
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.areas import BY_KEY  # noqa: E402
from app.modules.areastats.areamap import MAPS  # noqa: E402

OVERPASS = "https://overpass-api.de/api/interpreter"
WIDTH = 1000
# drawn widths: casing (the edge) and the road itself
ROADS = {"motorway": (13, 10), "trunk": (13, 10), "primary": (12, 9), "secondary": (9, 6.5), "tertiary": (7, 4.5),
         "unclassified": (0, 2.4), "residential": (0, 2.2), "living_street": (0, 2)}
# per area: the roads buyers know by name (labelled, OSM's names), and the area's spine (drawn as wide as a main road even
# where OSM files it as a smaller road: Upper Kharadi Main Rd is "tertiary")
LABELS = {"upper_kharadi": {"Nagar Road": "Pune–Nagar Road", "Upper Kharadi Main Rd": "Upper Kharadi Main Road",
                            "Manjari - Wagholi Road": "Manjari–Wagholi Road", "Lohgaon - Wagholi Road": "Lohegaon–Wagholi Road",
                            "Kharadi South Main Road": "Kharadi South Main Road"}}
SPINE = {"upper_kharadi": ("Upper Kharadi Main Rd",)}
# the area's own place names and landmarks: (text, lat, lon, kind)
PLACES = {
    "upper_kharadi": [("KHARADI", 18.5585, 73.9455, "area"), ("WAGHOLI", 18.5810, 73.9880, "area"),
                      ("MANJARI", 18.5365, 73.9700, "area"), ("EON IT Park", 18.5520, 73.9508, "landmark"),
                      ("← Viman Nagar, Phoenix Marketcity", 18.5640, 73.9400, "edge")],
}
LAND, PARK, WATER, ROAD, CASING, TEXT = "#f3eddf", "#e1e9d6", "#c7dcea", "#ffffff", "#e2d4b2", "#6b6250"


def fetch(box) -> dict:
    s, w, n, e = box
    q = (f'[out:json][timeout:90];(way["highway"~"^({"|".join(ROADS)})$"]({s},{w},{n},{e});'
         f'way["waterway"="river"]({s},{w},{n},{e});way["leisure"="park"]({s},{w},{n},{e});'
         f'way["landuse"~"^(grass|recreation_ground)$"]({s},{w},{n},{e}););out geom tags;')
    req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode(),
                                 headers={"User-Agent": "avasetu-area-map/1.0 (https://avasetu.in)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def projector(box):
    s, w, n, e = box
    height = WIDTH * (n - s) / ((e - w) * math.cos(math.radians((n + s) / 2)))
    return (lambda lat, lon: ((lon - w) / (e - w) * WIDTH, (n - lat) / (n - s) * height)), height


def simplify(pts, tol=0.9):
    """Ramer-Douglas-Peucker: fewer points, same look at this size."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy) or 1e-9
    far, at = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / norm
        if d > far:
            far, at = d, i
    if far <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:at + 1], tol)[:-1] + simplify(pts[at:], tol)


def path(pts, close=False, digits=1) -> str:
    return "M" + " L".join(f"{x:.{digits}f} {y:.{digits}f}" for x, y in pts) + (" Z" if close else "")


CHAR = 8.6        # average width of a 15 px label character


def label_spot(pts, text: str, height: float):
    """The middle of a road's longest straight piece that holds the whole label inside the picture (a label cut at the edge read
    "Manjari–Wa"): (x, y, angle in degrees kept readable, length), or None."""
    half = len(text) * CHAR / 2
    best = None
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        ln = math.hypot(x2 - x1, y2 - y1)
        x, y = (x1 + x2) / 2, (y1 + y2) / 2
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
        dx, dy = abs(math.cos(math.radians(ang))) * half, abs(math.sin(math.radians(ang))) * half
        fits = ln >= 40 and dx + 10 <= x <= WIDTH - dx - 10 and dy + 14 <= y <= height - dy - 14
        if fits and (best is None or ln > best[3]):
            best = (x, y, ang, ln)
    return best


def draw(osm: dict, box, places, labels=None, spine=()) -> str:
    to, height = projector(box)
    parks, rivers, roads = [], [], {k: [] for k in ROADS}
    names: dict = {}
    for el in osm.get("elements") or []:
        geom = el.get("geometry") or []
        if el.get("type") != "way" or len(geom) < 2:
            continue
        tags = el.get("tags") or {}
        hw = tags.get("highway")
        minor = hw in ("living_street", "residential", "unclassified")
        pts = simplify([to(g["lat"], g["lon"]) for g in geom], tol=1.6 if minor else 0.9)
        if hw in roads:
            if tags.get("name") in spine:
                hw = "secondary"
            roads[hw].append(pts)
            name = (labels or {}).get(tags.get("name") or "")
            if name:
                spot = label_spot(pts, name, height)
                if spot and (name not in names or spot[3] > names[name][3]):
                    names[name] = spot
        elif tags.get("waterway") == "river":
            rivers.append(pts)
        elif geom[0] == geom[-1]:
            parks.append(pts)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height:.0f}" width="{WIDTH}" height="{height:.0f}">',
           f'<rect width="{WIDTH}" height="{height:.0f}" fill="{LAND}"/>']
    out += [f'<path d="{path(p, True)}" fill="{PARK}"/>' for p in parks]
    out += [f'<path d="{path(p)}" fill="none" stroke="{WATER}" stroke-width="16" stroke-linecap="round"/>' for p in rivers]
    out.append('<g fill="none" stroke-linecap="round" stroke-linejoin="round">')
    for hw in ("living_street", "residential", "unclassified"):
        out += [f'<path d="{path(p, digits=0)}" stroke="{ROAD}" stroke-width="{ROADS[hw][1]}"/>' for p in roads[hw]]
    majors = ("tertiary", "secondary", "primary", "trunk", "motorway")
    for hw in majors:   # every edge first, then every road, so crossings join cleanly
        out += [f'<path d="{path(p)}" stroke="{CASING}" stroke-width="{ROADS[hw][0]}"/>' for p in roads[hw]]
    for hw in majors:
        out += [f'<path d="{path(p)}" stroke="{ROAD}" stroke-width="{ROADS[hw][1]}"/>' for p in roads[hw]]
    out.append("</g>")
    font = 'font-family="Poppins, Arial, sans-serif"'
    halo = f'paint-order="stroke" stroke="{LAND}" stroke-width="4" stroke-linejoin="round"'
    for name, (x, y, ang, ln) in names.items():
        out.append(f'<text x="{x:.0f}" y="{y:.0f}" transform="rotate({ang:.0f} {x:.0f} {y:.0f})" text-anchor="middle" dy="4" {font} '
                   f'font-size="15" font-weight="600" fill="{TEXT}" {halo}>{name}</text>')
    for text, lat, lon, kind in places:
        x, y = to(lat, lon)
        if kind == "area":
            out.append(f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" {font} font-size="20" font-weight="600" letter-spacing="5" '
                       f'fill="#a69a7e" {halo}>{text}</text>')
        elif kind == "edge":
            out.append(f'<text x="{max(x, 8):.0f}" y="{y:.0f}" {font} font-size="14" fill="{TEXT}" {halo}>{text}</text>')
        else:
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="#8a7f68"/>'
                       f'<text x="{x + 9:.0f}" y="{y + 5:.0f}" {font} font-size="15" font-weight="600" fill="#3d4a5c" {halo}>{text}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("area", help="area key, e.g. upper_kharadi")
    ap.add_argument("--osm", type=Path, help="a saved Overpass answer instead of asking Overpass")
    args = ap.parse_args()
    m = MAPS[args.area]
    osm = json.loads(args.osm.read_text(encoding="utf-8")) if args.osm else fetch(m.box)
    svg = draw(osm, m.box, PLACES.get(args.area, []), LABELS.get(args.area), SPINE.get(args.area, ()))
    target = BACKEND.parent / "frontend" / "public" / m.picture.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(svg, encoding="utf-8")
    print(f"{BY_KEY[args.area].name}: {target} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
