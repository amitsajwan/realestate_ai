"""One-time: our own copy of the named places around Pune, so 'what is nearby' never depends on a public Overpass server
(overpass-api.de refused every request with 406 on 2026-10-08, and the mirrors were down too).

Reads Geofabrik's free OpenStreetMap extract for western India, keeps the named places of propertyfacts.surroundings'
categories inside the Pune-district box (plus a margin for the 10 km radius), and writes
app/modules/propertyfacts/data/pune_places.json.gz: [[category, name, lat, lon, osm_type, osm_id], ...].

  venv/Scripts/python -m pip install osmium      (only this script needs it; the app does not)
  PYTHONPATH=. python scripts/build_osm_places.py [--pbf western-zone-latest.osm.pbf]

Run it again only to refresh the copy (OSM changes slowly; a yearly refresh is plenty).
"""
import argparse
import gzip
import json
import sys
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.propertyfacts.surroundings import LOCAL_PLACES, category  # noqa: E402

URL = "https://download.geofabrik.de/asia/india/western-zone-latest.osm.pbf"
# Pune district with ~15 km to spare on each side (a place's 10 km radius may cross the district line)
SOUTH, NORTH, WEST, EAST = 17.70, 19.55, 73.15, 75.35


def inside(lat: float, lon: float) -> bool:
    return SOUTH <= lat <= NORTH and WEST <= lon <= EAST


def build(pbf: Path) -> list:
    import osmium

    out: list = []

    class H(osmium.SimpleHandler):
        def _keep(self, tags, lat, lon, kind, oid):
            t = {k: v for k, v in tags}
            name = (t.get("name:en") or t.get("name") or "").strip()
            cat = category(t)
            if cat and name and inside(lat, lon):
                out.append([cat, name, round(lat, 6), round(lon, 6), kind, oid])

        def node(self, n):
            if n.tags and "name" in n.tags and n.location.valid():
                self._keep(n.tags, n.location.lat, n.location.lon, "node", n.id)

        def way(self, w):
            if not (w.tags and "name" in w.tags):
                return
            pts = [(nd.lat, nd.lon) for nd in w.nodes if nd.location.valid()]
            if pts:  # the way's centre: good enough for "about 2.3 km away"
                self._keep(w.tags, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), "way", w.id)

    H().apply_file(str(pbf), locations=True, idx="flex_mem")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pbf", default="western-zone-latest.osm.pbf")
    a = ap.parse_args()
    pbf = Path(a.pbf)
    if not pbf.is_file():
        print(f"downloading {URL} ...")
        urllib.request.urlretrieve(URL, pbf)
    rows = build(pbf)
    LOCAL_PLACES.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(LOCAL_PLACES, "wt", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    by = {}
    for r in rows:
        by[r[0]] = by.get(r[0], 0) + 1
    print(f"{len(rows)} places -> {LOCAL_PLACES} ({LOCAL_PLACES.stat().st_size / 1e6:.1f} MB): {by}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
