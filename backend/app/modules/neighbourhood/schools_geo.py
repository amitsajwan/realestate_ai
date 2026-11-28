"""Where a school is: its pin on Google Maps (Places API (New) Text Search), judged by the rules the project pins use
(propertyfacts/pin.py, not imported: the two modules stand side by side).

One Text Search per school, "<name>, <board's address>, <pincode>", biased to the board's own position when it gives one
(CISCE does) or else to Pune. A candidate is the school only when
- its name carries the school's distinctive words (two thirds of them at least, a word of five letters or more may be spelt one
  letter apart; "PM SHRI" and the words every school has, "school", "public", "english medium", count for nothing);
- it is not a business of another kind (a shop, a coaching class, a hotel...);
- the pincode in Google's address is the board's, when both have one; without a board pincode a place word of the board's
  address must be in Google's;
- it stands inside Pune district (MAX_FROM_PUNE_KM from the city centre) and, when the board gives its own position, within
  NEAR_BOARD_KM of it.
Google's terms: the place id may be kept for good, the position only 30 days, so a placed school is re-read by its id (Place
Details, location only, the cheapest call) once its position is REFRESH_DAYS old; a school Google did not find is asked again
after REFRESH_DAYS. Without a key nothing is asked.
"""
import logging
import math
import re
from typing import List, Optional, Tuple

import httpx

log = logging.getLogger(__name__)

SEARCH = "https://places.googleapis.com/v1/places:searchText"
DETAILS = "https://places.googleapis.com/v1/places/{id}"
SEARCH_FIELDS = "places.id,places.displayName,places.formattedAddress,places.location,places.types"
DETAILS_FIELDS = "id,location"
PUNE = (18.5204, 73.8567)
MAX_FROM_PUNE_KM = 75.0          # Pune district reaches Baramati and Indapur; a pin further off is another town's school
NEAR_BOARD_KM = 3.0
BIAS_M = 15000.0
REFRESH_DAYS = 30
PINCODE = re.compile(r"\b4\d{5}\b")
GENERIC = frozenset({"school", "schools", "public", "english", "medium", "high", "higher", "secondary", "senior", "primary",
                     "junior", "college", "the", "and", "of", "for", "pune", "pm", "shri", "pvt", "ltd", "trust", "sr", "no",
                     "academy", "international", "global", "world", "education", "educational", "society", "campus", "branch",
                     "cbse", "icse", "isc", "co", "ed", "maharashtra", "india", "a", "an", "at", "in"})
NOT_A_SCHOOL = re.compile(r"store|shop|restaurant|food|cafe|bakery|hotel|lodging|real_estate|bank|atm|hospital|doctor|"
                          r"clinic|pharmacy|gym|salon|spa|car_|gas_station|tutor|coaching|place_of_worship|church|temple|mosque|"
                          r"preschool|child_care|kindergarten")   # a board's school runs to class 8 at least, not a play school


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in kilometres (haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _words(s: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (s or "").lower())


def _one_apart(a: str, b: str) -> bool:
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return a[i + (len(a) == len(b)):] == b[i + 1:]


def _same(a: str, b: str) -> bool:
    return a == b or (min(len(a), len(b)) >= 5 and not a.isdigit() and _one_apart(a, b))


def distinctive(name: str) -> List[str]:
    return [w for w in _words(name) if w not in GENERIC and not (w.isdigit() and len(w) > 2)]


def name_matches(school: str, candidate: str, address: str = "") -> bool:
    """The candidate's name carries two thirds of the school's distinctive words (all of them when it has one or two):
    "PODAR INTERNATIONAL SCHOOL- WAGHOLI" is "Podar International School, Wagholi". The place words a board adds to a name that
    are also in its address ("CRIMSON ANISHA GLOBAL SCHOOL MARUNJI MULSHI", address "... MARUNJI, MULSHI") are left out of the
    count when other words remain, as Google calls it "Crimson Anisha School" (VM check 2026-11-28)."""
    want = distinctive(school)
    places = set(place_words(address))
    if len([w for w in want if w not in places]) >= 2:
        want = [w for w in want if w not in places]
    if not want:
        return False
    have = _words(candidate)
    hit = sum(1 for w in want if any(_same(w, h) for h in have))
    need = len(want) if len(want) <= 2 else math.ceil(len(want) * 2 / 3)
    return hit >= need


def place_words(address: str) -> List[str]:
    """Words of a board's address that name a place (no numbers, no road words): "SR .NO 22/70,UBALE NAGAR,WAGHOLI,PUNE"
    -> ["ubale", "wagholi"]."""
    skip = GENERIC | {"road", "rd", "nagar", "near", "opp", "behind", "plot", "survey", "s", "gat", "lane", "chowk", "colony",
                      "dist", "district", "tal", "taluka", "post", "at", "nr", "street", "phase", "sector", "next", "to"}
    return [w for w in _words(address) if len(w) >= 4 and not w.isdigit() and w not in skip]


def check(c: dict, school: dict) -> Optional[str]:
    """Why a Text Search candidate is not this school, or None when it is."""
    name = ((c.get("displayName") or {}).get("text") or "").strip()
    loc = c.get("location") or {}
    lat, lon = loc.get("latitude"), loc.get("longitude")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return "no position"
    if not name_matches(school.get("name") or "", name, school.get("address") or ""):
        return f"name {name!r} is not {school.get('name')!r}"
    other = [t for t in c.get("types") or [] if NOT_A_SCHOOL.search(t)]
    if other:
        return f"{name!r} is a {other[0].replace('_', ' ')}"
    address = c.get("formattedAddress") or ""
    pins = PINCODE.findall(address)
    want = school.get("pincode") or ""
    if want and pins and want not in pins:
        return f"pincode {pins[-1]}, the board says {want}"
    if not want:
        words = place_words(school.get("address") or "")
        if words and not any(w in _words(address) or w in _words(name) for w in words):
            return "no place of the board's address in Google's"
    if km(PUNE[0], PUNE[1], lat, lon) > MAX_FROM_PUNE_KM:
        return "outside Pune district"
    if isinstance(school.get("board_lat"), (int, float)) and isinstance(school.get("board_lon"), (int, float)):
        d = km(school["board_lat"], school["board_lon"], lat, lon)
        if d > NEAR_BOARD_KM:
            return f"{d:.1f} km from the board's own position"
    return None


def pick(candidates: list, school: dict) -> Tuple[Optional[dict], List[str]]:
    ok, why = [], []
    for c in candidates if isinstance(candidates, list) else []:
        r = check(c, school)
        (why.append(r) if r else ok.append(c))
    if not ok:
        return None, why
    is_school = [c for c in ok if any("school" in t for t in c.get("types") or [])]
    return (is_school or ok)[0], why


def query(school: dict) -> str:
    name = re.sub(r"(?i)^pm\s+shri\s+", "", school.get("name") or "").strip()
    parts = [name, school.get("address") or "", school.get("pincode") or ""]
    q = ", ".join(p for p in parts if p)
    return q if "pune" in q.lower() else q + ", Pune"


async def _call(http: httpx.AsyncClient, key: str, method: str, url: str, fields: str, body: Optional[dict] = None):
    headers = {"X-Goog-Api-Key": key, "X-Goog-FieldMask": fields}
    try:
        r = await (http.post(url, json=body, headers=headers) if method == "POST" else http.get(url, headers=headers))
    except httpx.HTTPError as e:
        log.warning("schools: google places %s", type(e).__name__)
        return None
    if r.status_code == 404:
        return {}
    if r.status_code != 200:
        log.warning("schools: google places answered %s %s", r.status_code, r.text[:200])
        return None
    try:
        return r.json()
    except ValueError:
        return None


async def find(http: httpx.AsyncClient, key: str, school: dict) -> Tuple[Optional[dict], str]:
    """(the accepted place {lat, lon, place_id, name, address} or None, a plain note). None with note "no answer" when Google
    did not answer (asked again next run)."""
    centre = (school["board_lat"], school["board_lon"]) if isinstance(school.get("board_lat"), (int, float)) else PUNE
    body = {"textQuery": query(school), "regionCode": "IN", "pageSize": 5,
            "locationBias": {"circle": {"center": {"latitude": centre[0], "longitude": centre[1]}, "radius": BIAS_M}}}
    got = await _call(http, key, "POST", SEARCH, SEARCH_FIELDS, body)
    if got is None:
        return None, "no answer"
    best, why = pick(got.get("places") or [], school)
    if best is None:
        return None, "not found on Google Maps" + (f" ({'; '.join(why[:3])})" if why else "")
    loc = best["location"]
    name = (best.get("displayName") or {}).get("text") or ""
    return ({"lat": loc["latitude"], "lon": loc["longitude"], "place_id": best["id"], "name": name,
             "address": best.get("formattedAddress") or ""}, f"Google Maps: {name}")


async def reread(http: httpx.AsyncClient, key: str, place_id: str) -> Tuple[Optional[Tuple[float, float]], str]:
    """A kept place's position again by its id: ((lat, lon), "") or (None, "gone") when Google no longer has it, (None, "no
    answer") when it did not answer."""
    got = await _call(http, key, "GET", DETAILS.format(id=place_id), DETAILS_FIELDS)
    if got is None:
        return None, "no answer"
    loc = got.get("location") or {}
    if isinstance(loc.get("latitude"), (int, float)) and isinstance(loc.get("longitude"), (int, float)):
        return (loc["latitude"], loc["longitude"]), ""
    return None, "gone"
