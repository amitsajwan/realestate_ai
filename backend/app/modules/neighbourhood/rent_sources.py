"""Asked rent from the portals' listing pages (owner 2026-11-28: reading the portals is fine; asked rent only, never "you will
earn"). Plain parse and arithmetic, so each can be checked against a saved page (tests/modules/neighbourhood/fixtures).

What each portal serves without a login (read 2026-11-28 with AvasetuBot's user agent; each site's robots.txt allows these pages):
- MagicBricks, /<n>-bhk-flats-for-rent-in-<place>-pune-pppfr: the page's `window.SERVER_PRELOADED_STATE_` JSON carries the
  first 30 listings of that size: id, price (rent a month), bedroomD, caSqFt/carpetArea, prjname (society), propTypeD,
  transType, lmtDName (locality), pmtLat/pmtLong. MagicBricks spells some places its own way (hinjewadi), see ALIASES.
- NoBroker, /flats-for-rent-in-<place>_pune: the Next.js flight data (`self.__next_f.push`) holds `initialProperties`, about
  25 listings of every size: id, type ("BHK2", "RK1"), rent, propertySize, buildingName/society, buildingType, latitude/
  longitude (with accurateLocation), sharedAccomodation.
- Square Yards, /rent/property-for-rent-in-<place>-pune: schema.org JSON-LD, one Apartment (rooms, floorSize, society as
  address.name, geo) and one RentAction (price) per listing, joined by their url, about 24 a page.
- Not read: 99acres (403 to any reader) and Housing.com (406), as webfacts.SKIP_SITES found for project pages.
Owners' and agents' names, phone numbers and descriptions are on those pages and are never read into a listing.

`rows` turns listings into one row per flat size: residential flats only (no PG, shared rooms, rooms, independent houses,
villas, penthouses, studios or offices), the same flat listed on two portals counted once (same size, rent, area within 25 sq ft
and society), rents outside OUTLIER_LOW-OUTLIER_HIGH times the size's median dropped, then the 25th percentile, median and 75th
percentile, rounded to Rs 500.
"""
import json
import re
from typing import Dict, Iterable, List, Optional

BHKS = (1, 2, 3)
OUTLIER_LOW, OUTLIER_HIGH = 0.25, 4.0
ROUND_TO = 500
MIN_RENT, MAX_RENT = 3000, 1_000_000           # a month; outside is a typo or a sale price
# MagicBricks, NoBroker and Square Yards spell some places their own way; tried after the place's own words
ALIASES: Dict[str, tuple] = {"hinjawadi": ("hinjewadi",), "lohegaon": ("lohgaon",), "pimpri-chinchwad": ("pimpri",)}
NOT_A_FLAT = re.compile(r"(?i)\b(pg|paying guest|hostel|shared|sharing|room|rooms|independent house|villa|bungalow|row house|"
                        r"penthouse|studio|office|shop|showroom|commercial|warehouse|godown|plot|land|co-?living)\b")
FLAT_KINDS = ("apartment", "multistorey apartment", "builder floor", "builder floor apartment", "flat", "residential apartment")


def place_words(place: str) -> List[str]:
    """URL words to try for a place slug: its own ("upper_kharadi" -> "upper-kharadi"), then ALIASES."""
    own = place.strip().lower().replace("_", "-").replace(" ", "-")
    out = [own]
    for a in ALIASES.get(own, ()):
        if a not in out:
            out.append(a)
    return out


def magicbricks_url(word: str, bhk: int) -> str:
    return f"https://www.magicbricks.com/{bhk}-bhk-flats-for-rent-in-{word}-pune-pppfr"


def nobroker_url(word: str) -> str:
    return f"https://www.nobroker.in/flats-for-rent-in-{word}_pune"


def squareyards_url(word: str) -> str:
    return f"https://www.squareyards.com/rent/property-for-rent-in-{word}-pune"


def _int(v) -> Optional[int]:
    try:
        n = int(float(str(v).replace(",", "").strip()))
    except (TypeError, ValueError):
        return None
    return n


def _listing(source: str, lid, rent, bhk, sqft, society, lat=None, lon=None) -> Optional[dict]:
    rent, bhk, sqft = _int(rent), _int(bhk), _int(sqft)
    if not rent or not (MIN_RENT <= rent <= MAX_RENT) or bhk not in BHKS:
        return None
    out = {"source": source, "id": str(lid or ""), "rent": rent, "bhk": bhk, "sqft": sqft if sqft and sqft > 100 else None,
           "society": " ".join(str(society or "").split())}
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and lat and lon:
        out.update({"lat": round(float(lat), 6), "lon": round(float(lon), 6)})
    return out


def _json_after(text: str, marker: str):
    i = text.find(marker)
    if i < 0:
        return None
    j = i + len(marker)
    while j < len(text) and text[j] in " =\t\n":
        j += 1
    try:
        return json.JSONDecoder().raw_decode(text[j:])[0]
    except ValueError:
        return None


def parse_magicbricks(page: str) -> List[dict]:
    state = _json_after(page or "", "window.SERVER_PRELOADED_STATE_")
    out = []
    for r in (state or {}).get("searchResult") or [] if isinstance(state, dict) else []:
        if not isinstance(r, dict) or str(r.get("transType") or r.get("transactionTypeD") or "").lower() != "rent":
            continue
        kind = str(r.get("propTypeD") or "").strip().lower()
        title = f"{r.get('propertyTitle') or ''} {r.get('auto_desc') or ''}"
        if kind not in FLAT_KINDS or NOT_A_FLAT.search(title):
            continue
        got = _listing("magicbricks", r.get("id"), r.get("price"), r.get("bedroomD"), r.get("caSqFt") or r.get("carpetArea"),
                       r.get("prjname"), r.get("pmtLat"), r.get("pmtLong"))
        if got:
            out.append(got)
    return out


_PUSH = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
_NB_TYPE = re.compile(r"^BHK([123])$")


def parse_nobroker(page: str) -> List[dict]:
    props = None
    for chunk in _PUSH.findall(page or ""):
        if "initialProperties" not in chunk:
            continue
        try:
            text = json.loads('"' + chunk + '"')
        except ValueError:
            continue
        props = _json_after(text, '"initialProperties":')
        if props:
            break
    out = []
    for r in props or []:
        if not isinstance(r, dict) or r.get("sharedAccomodation") or str(r.get("propertyType") or "RENT").upper() != "RENT":
            continue
        m = _NB_TYPE.match(str(r.get("type") or ""))
        society = r.get("buildingName") or r.get("society") or ""
        if not m or str(r.get("buildingType") or "AP").upper() not in ("AP", "IF", "GC") or NOT_A_FLAT.search(
                f"{society} {r.get('propertyTitle') or ''}"):
            continue
        exact = bool(r.get("accurateLocation"))
        got = _listing("nobroker", r.get("id"), r.get("rent"), m.group(1), r.get("propertySize"), society,
                       r.get("latitude") if exact else None, r.get("longitude") if exact else None)
        if got:
            out.append(got)
    return out


def parse_squareyards(page: str) -> List[dict]:
    flats: Dict[str, dict] = {}
    rents: Dict[str, str] = {}
    for blob in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', page or "", re.S):
        try:
            o = json.loads(blob)
        except ValueError:
            continue
        for x in o if isinstance(o, list) else [o]:
            if not isinstance(x, dict) or not x.get("url"):
                continue
            if x.get("@type") == "Apartment":
                flats[x["url"]] = x
            elif x.get("@type") == "RentAction":
                rents[x["url"]] = x.get("price")
    out = []
    for url, f in flats.items():
        name = str(f.get("name") or "")
        if url not in rents or NOT_A_FLAT.search(name) or not re.search(r"(?i)\bflat\b|\bapartment\b", name + " " + url):
            continue
        geo = f.get("geo") or {}
        got = _listing("squareyards", url.rstrip("/").rsplit("/", 1)[-1], rents[url], f.get("numberOfRooms"), f.get("floorSize"),
                       (f.get("address") or {}).get("name"), geo.get("latitude"), geo.get("longitude"))
        if got:
            out.append(got)
    return out


PARSERS = {"magicbricks": parse_magicbricks, "nobroker": parse_nobroker, "squareyards": parse_squareyards}


def _soc(s: str) -> str:
    words = [w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in {"phase", "the", "society", "apartment",
                                                                                  "apartments", "chs", "pune"}]
    return " ".join(words)


def same_flat(a: dict, b: dict) -> bool:
    """One flat listed on two portals: same size and rent, area within 25 sq ft when both give it, same society when both name one,
    and something besides size and rent to go on (an area or a society)."""
    if a["bhk"] != b["bhk"] or a["rent"] != b["rent"]:
        return False
    sa, sb = _soc(a.get("society") or ""), _soc(b.get("society") or "")
    if sa and sb and not (sa in sb or sb in sa):
        return False
    if a.get("sqft") and b.get("sqft") and abs(a["sqft"] - b["sqft"]) > 25:
        return False
    return bool((sa and sb) or (a.get("sqft") and b.get("sqft")))


def dedupe(listings: Iterable[dict]) -> List[dict]:
    """Each listing once: a repeat of the same id on one portal, or the same flat on another portal (same_flat)."""
    out: List[dict] = []
    seen_ids = set()
    for l in listings:
        key = (l["source"], l.get("id"))
        if l.get("id") and key in seen_ids:
            continue
        seen_ids.add(key)
        if any(o["source"] != l["source"] and same_flat(o, l) for o in out):
            continue
        out.append(l)
    return out


def percentile(values: List[int], q: float) -> float:
    v = sorted(values)
    if not v:
        raise ValueError("no values")
    k = (len(v) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def _round(x: float) -> int:
    return int(round(x / ROUND_TO) * ROUND_TO)


def without_outliers(listings: List[dict]) -> List[dict]:
    if not listings:
        return []
    med = percentile([l["rent"] for l in listings], 0.5)
    return [l for l in listings if OUTLIER_LOW * med <= l["rent"] <= OUTLIER_HIGH * med]


def rows(listings: Iterable[dict]) -> List[dict]:
    """One row per flat size with any listing: {bhk: "2 BHK", low, median, high, listings, by_source}. The page gate (10+
    listings) is the researcher's present, so a thin month is still kept and counted."""
    once = dedupe(listings)
    out = []
    for bhk in BHKS:
        kept = without_outliers([l for l in once if l["bhk"] == bhk])
        if not kept:
            continue
        rents = [l["rent"] for l in kept]
        by: Dict[str, int] = {}
        for l in kept:
            by[l["source"]] = by.get(l["source"], 0) + 1
        out.append({"bhk": f"{bhk} BHK", "low": _round(percentile(rents, 0.25)), "median": _round(percentile(rents, 0.5)),
                    "high": _round(percentile(rents, 0.75)), "listings": len(kept), "by_source": by})
    return out
