"""Rebuild app/modules/propertyfacts/data/pune_neighbourhoods.json.gz: every named OSM suburb, neighbourhood, quarter, village
and hamlet node in the Pune district box (surroundings.LOCAL_BOX), for communities/discover.py when Overpass does not answer.

    python scripts/osm_neighbourhoods.py            # asks Overpass (main server, then the mirrors) tile by tile
    python scripts/osm_neighbourhoods.py a.json ... # or builds the file from Overpass answers saved earlier (out body)
"""
import gzip
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.modules.communities.discover import KINDS, LOCAL  # noqa: E402
from app.modules.propertyfacts.surroundings import LOCAL_BOX, OVERPASS, OVERPASS_MIRRORS  # noqa: E402


def tiles():
    s, n, w, e = LOCAL_BOX
    ms, mw = (s + n) / 2, (w + e) / 2
    return [(s, w, ms, mw), (s, mw, ms, e), (ms, w, n, mw), (ms, mw, n, e)]


def fetch() -> list:
    out = []
    for box in tiles():
        q = (f'[out:json][timeout:120];node({",".join(f"{x:.2f}" for x in box)})["place"~"^({"|".join(KINDS)})$"]["name"];'
             "out body qt;")
        for url in (OVERPASS, *OVERPASS_MIRRORS):
            try:
                r = httpx.post(url, data={"data": q}, timeout=150, headers={"User-Agent": "Mozilla/5.0 (avasetu.in)"})
                if r.status_code == 200:
                    out += r.json()["elements"]
                    break
                print(url, r.status_code)
            except httpx.HTTPError as e:
                print(url, type(e).__name__)
        else:
            raise SystemExit(f"no Overpass server answered for {box}; try again later")
    return out


def main(files: list) -> None:
    elements = [e for f in files for e in json.loads(Path(f).read_text(encoding="utf-8"))["elements"]] if files else fetch()
    rows = {}
    for e in elements:
        t = e.get("tags") or {}
        name = (t.get("name:en") or t.get("name") or "").strip()
        if name and t.get("place") in KINDS and "lat" in e:
            rows[e["id"]] = [name, t["place"], round(e["lat"], 6), round(e["lon"], 6), e["id"]]
    LOCAL.write_bytes(gzip.compress(json.dumps(sorted(rows.values()), ensure_ascii=False).encode("utf-8")))
    print(f"{len(rows)} places -> {LOCAL}")


if __name__ == "__main__":
    main(sys.argv[1:])
