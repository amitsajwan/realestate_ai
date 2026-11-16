"""Where a project itself is: its pin on Google Maps (Places API (New)), so distances to nearby places are measured from the
project, not from the middle of its locality (2026-10-14: every Kharadi page listed the same five places at the same distances).

One Text Search per project ("<project>, <locality>, Pune"), biased to the locality's centre. A candidate is accepted only when
its name carries the project's name, it is within MAX_KM of the locality's centre and its address's pincode (when it has one)
is the project's MahaRERA pincode. No candidate passing means no pin: the page then shows no distances at all.

MahaRERA registers towers and phases, Google Maps knows the project: "Kumar Primeview G2" is "Kumar Primeview" there, and two
project pages in three had no position because the tower's code was asked of the candidate's name (2026-11-16). So a candidate
may also carry a name the project is sold under: the ones the caller knows (`names`) and the registered name without the tower,
wing or phase labels at its end (`sold_as`). The first search's candidates are judged against all of them; if none passes, Google
is asked once more under the first such name. A tower's page then stands on its project's pin, which is the same site.

Google's terms: the place id may be kept for good, the position only for 30 days, so a found pin is re-read by id (Place Details,
location only) once it is REFRESH_DAYS old; a project not found is searched again after REFRESH_DAYS. Answers are kept in
`project_pins`, one document per project key (the MahaRERA number when known). No key configured: nothing is asked."""
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Sequence

import httpx

from .surroundings import km

log = logging.getLogger(__name__)

SEARCH = "https://places.googleapis.com/v1/places:searchText"
DETAILS = "https://places.googleapis.com/v1/places/{id}"
SEARCH_FIELDS = "places.id,places.displayName,places.formattedAddress,places.location,places.types"
DETAILS_FIELDS = "id,location"                 # Place Details Essentials: the cheapest call that gives a position
COLLECTION = "project_pins"
MAX_KM = 6.0                                   # from the locality's centre
BIAS_M = 10000.0
REFRESH_DAYS = 30
PINCODE = re.compile(r"\b4\d{5}\b")            # Pune district pincodes
# words that say what a place is, not which one: "Nyati Evoque Phase 2" and "Nyati Evoque" are one project
# ("tower" is not one: "TITAN TOWER" matched a Titan watch shop on 2026-10-14)
GENERIC = frozenset({"phase", "wing", "building", "bldg", "project", "the", "by", "and", "of", "at", "in", "pune", "co", "op",
                     "society", "chs", "sector", "inclusive", "housing"})   # "Atulyam-Inclusive Housing": the main project's share
OFFICE_TYPES = frozenset({"real_estate_agency", "corporate_office"})   # a sales office can sit kilometres from the site
# a business with the project's name is not the project: shops, places to eat, hospitals, schools, hotels, banks...
NOT_A_SITE = re.compile(r"store|shop|mall|restaurant|food|cafe|bakery|bar$|hospital|doctor|clinic|pharmacy|school|university|"
                        r"lodging|hotel|bank|atm|gym|salon|spa|car_|gas_station|church|hindu_temple|mosque|place_of_worship")


# what ends a registered name without being part of the project's: "Building C", "T9 A1", "G2", "2.O", "Phase II"
PART_LABEL = frozenset({"tower", "towers", "wing", "wings", "building", "buildings", "bldg", "phase", "ph", "block"})
PART_CODE = re.compile(r"^(?:[a-z]|[a-z]\d{1,2}|\d{1,2}[a-z]?|[ivx]{1,4})$")
NAMES_SEARCHED = 2                             # Text Searches for one project: its registered name, then one sold-under name


@dataclass(frozen=True)
class Pin:
    lat: float
    lon: float
    place_id: str
    name: str
    address: str
    url: str


def _words(s: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (s or "").lower())


def name_matches(project: str, candidate: str, locality: str = "") -> bool:
    """The candidate's name carries every distinctive word of the project's name ("EAST STREET" -> "East Street Kharadi"),
    or the same letters with the spaces removed ("Gulmohar City" / "GulmoharCity")."""
    skip = GENERIC | set(_words(locality))
    want = [w for w in _words(project) if w not in skip and not w.isdigit()]
    if not want:
        return False
    have = _words(candidate)
    if all(w in have for w in want):
        return True
    return "".join(want) in "".join(have)


def sold_as(project: str) -> str:
    """The registered name without the tower, wing or phase labels and codes at its end: "Sara Kasturi Building C" ->
    "Sara Kasturi", "BramhaCorp Business Park T9 A1" -> "BramhaCorp Business Park". Two words always stay, so a short name
    ("VTP X1") is left as it is; "" when nothing was cut."""
    words = (project or "").split()
    n = len(words)
    while n > 2:
        w = "".join(_words(words[n - 1]))
        if w and w not in PART_LABEL and not PART_CODE.match(w):
            break
        n -= 1
    return " ".join(words[:n]).strip(" -,&") if n < len(words) else ""


def also_known(project: str, names: Sequence[str], locality: str = "") -> List[str]:
    """The other names a candidate may carry, the caller's first: each once, not the registered name itself, and only with two
    distinctive words left, so a builder's name alone ("Kumar") never stands for a project."""
    skip = GENERIC | set(_words(locality))
    out: List[str] = []
    seen = {" ".join(_words(project))}
    for n in [*names, sold_as(project)]:
        key = " ".join(_words(n or ""))
        if key in seen or len([w for w in _words(n or "") if w not in skip and not w.isdigit()]) < 2:
            continue
        seen.add(key)
        out.append(n.strip())
    return out


def check(c: dict, project: str, locality: str, pincode: str, centre: Optional[tuple],
          names: Sequence[str] = ()) -> Optional[str]:
    """Why a Text Search candidate is not this project, or None when it is. `names`: other names the project is sold under."""
    name = ((c.get("displayName") or {}).get("text") or "").strip()
    loc = c.get("location") or {}
    if not isinstance(loc.get("latitude"), (int, float)) or not isinstance(loc.get("longitude"), (int, float)):
        return "no position"
    if not any(name_matches(n, name, locality) for n in (project, *names)):
        return f"name {name!r} is not {project!r}"
    business = [t for t in c.get("types") or [] if NOT_A_SITE.search(t)]
    if business:
        return f"{name!r} is a {business[0].replace('_', ' ')}, not the site"
    pins = PINCODE.findall(c.get("formattedAddress") or "")
    if pincode and pins and pincode not in pins:
        return f"pincode {pins[-1]}, MahaRERA says {pincode}"
    if centre:
        d = km(centre[0], centre[1], loc["latitude"], loc["longitude"])
        if d > MAX_KM:
            return f"{d:.1f} km from {locality or 'the locality'}'s centre"
    return None


def pick(places: Any, project: str, locality: str, pincode: str, centre: Optional[tuple], names: Sequence[str] = ()) -> tuple:
    """(the accepted candidate or None, why each was refused). The site itself before a sales office, then nearest the centre."""
    ok, why = [], []
    for c in places if isinstance(places, list) else []:
        r = check(c, project, locality, pincode, centre, names)
        (why.append(r) if r else ok.append(c))
    if not ok:
        return None, why

    def rank(c):
        loc = c["location"]
        office = bool(OFFICE_TYPES & set(c.get("types") or []))
        return (office, km(centre[0], centre[1], loc["latitude"], loc["longitude"]) if centre else 0.0)
    return sorted(ok, key=rank)[0], why


def _pin(doc: dict) -> Pin:
    return Pin(lat=doc["lat"], lon=doc["lon"], place_id=doc["place_id"], name=doc.get("name", ""),
               address=doc.get("address", ""), url=f"https://www.google.com/maps/place/?q=place_id:{doc['place_id']}")


class Pins:
    """The lookup with its kept answers. `transport` is for tests."""

    def __init__(self, db, key: Optional[str], timeout: float = 20.0, transport: Optional[httpx.AsyncBaseTransport] = None):
        self.col = db.get_collection(COLLECTION)
        self.key, self.timeout, self.transport = (key or "").strip(), timeout, transport

    async def _call(self, method: str, url: str, fields: str, body: Optional[dict] = None) -> Optional[dict]:
        headers = {"X-Goog-Api-Key": self.key, "X-Goog-FieldMask": fields}
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as c:
                r = await (c.post(url, json=body, headers=headers) if method == "POST" else c.get(url, headers=headers))
        except httpx.HTTPError as e:
            log.warning("google places: %s %s", url, type(e).__name__)
            return None
        if r.status_code != 200:
            log.warning("google places: %s answered %s %s", url, r.status_code, r.text[:200])
            return None
        try:
            return r.json()
        except ValueError:
            return None

    async def search(self, query: str, centre: Optional[tuple] = None, radius_m: float = BIAS_M) -> Optional[List[dict]]:
        """Google's candidates for a free query near a centre, unjudged: [{name, address, lat, lon, place_id, types}]. The area
        maps (areastats.mappins) judge them by the name a project is sold under. None without a key or when Google did not answer."""
        if not self.key or not (query or "").strip():
            return None
        body: dict = {"textQuery": query, "regionCode": "IN", "pageSize": 5}
        if centre:
            body["locationBias"] = {"circle": {"center": {"latitude": centre[0], "longitude": centre[1]}, "radius": radius_m}}
        got = await self._call("POST", SEARCH, SEARCH_FIELDS, body)
        if got is None:
            return None
        out = []
        for c in got.get("places") or []:
            loc = c.get("location") or {}
            if isinstance(loc.get("latitude"), (int, float)) and isinstance(loc.get("longitude"), (int, float)) and c.get("id"):
                out.append({"name": ((c.get("displayName") or {}).get("text") or "").strip(), "address": c.get("formattedAddress") or "",
                            "lat": loc["latitude"], "lon": loc["longitude"], "place_id": c["id"], "types": list(c.get("types") or [])})
        return out

    async def keep(self, key: str, c: dict, now: datetime) -> None:
        """Keep a place found elsewhere as the project's pin ({name, address, lat, lon, place_id}): `find` then answers with it and
        re-reads it by id. The place check (areastats.placecheck) finds it without assuming the pincode that made `find` refuse it."""
        note = f"Google Maps: {c.get('name') or ''}, {c.get('address') or ''}".strip(", ")
        await self.col.update_one({"_id": key}, {"$set": {"at": now, "place_id": c["place_id"], "name": c.get("name") or "",
                                                          "address": c.get("address") or "", "lat": c["lat"], "lon": c["lon"],
                                                          "checked": note}}, upsert=True)

    async def find(self, key: str, project: str, locality: str, pincode: str = "", centre: Optional[tuple] = None,
                   now: Optional[datetime] = None, names: Sequence[str] = ()) -> tuple:
        """(Pin or None, a plain note on how it was found or why not). `names`: the names the project is sold under, tried
        after the registered one. A kept "not found" is asked again before it is REFRESH_DAYS old when it was decided without
        a name we have now, so the answers kept before 2026-11-16 heal on the project's next round."""
        if not self.key:
            return None, "no Google Maps key: distances are not measured"
        if not (project or "").strip():
            return None, "no project name to find on Google Maps"
        now = now or datetime.utcnow()
        kept = await self.col.find_one({"_id": key})
        at = kept.get("at") if kept else None
        if isinstance(at, datetime):   # Mongo hands dates back naive (UTC); callers pass naive or aware
            at, ref = at.replace(tzinfo=None), (now.astimezone(timezone.utc).replace(tzinfo=None) if now.tzinfo else now)
        fresh = kept and isinstance(at, datetime) and ref - at < timedelta(days=REFRESH_DAYS)
        others = also_known(project, names, locality)
        tried = [" ".join(_words(n)) for n in (project, *others)]
        if fresh and not kept.get("place_id") and set(tried) - set(kept.get("names") or [" ".join(_words(kept.get("project") or ""))]):
            fresh = False                           # refused under fewer names than we know now
        if fresh:
            return (_pin(kept), kept.get("checked", "")) if kept.get("place_id") else (None, kept.get("checked", ""))
        if kept and kept.get("place_id"):          # found before: re-read only its position
            got = await self._call("GET", DETAILS.format(id=kept["place_id"]), DETAILS_FIELDS)
            loc = (got or {}).get("location") or {}
            if isinstance(loc.get("latitude"), (int, float)) and isinstance(loc.get("longitude"), (int, float)):
                await self.col.update_one({"_id": key}, {"$set": {"lat": loc["latitude"], "lon": loc["longitude"], "at": now}})
                return _pin({**kept, "lat": loc["latitude"], "lon": loc["longitude"]}), kept.get("checked", "")
            if got is None:
                return None, "Google Maps did not answer"
            # the place is gone from Google: search again below
        best, refused = None, []
        for asked in [project, *others][:NAMES_SEARCHED]:
            body = {"textQuery": ", ".join(p for p in (asked, locality, "Pune") if p), "regionCode": "IN", "pageSize": 5}
            if centre:
                body["locationBias"] = {"circle": {"center": {"latitude": centre[0], "longitude": centre[1]}, "radius": BIAS_M}}
            got = await self._call("POST", SEARCH, SEARCH_FIELDS, body)
            if got is None:
                return None, "Google Maps did not answer"
            best, why = pick(got.get("places") or [], project, locality, pincode, centre, others)
            refused += why
            if best is not None:
                break
        if best is None:
            note = "not found on Google Maps" + (f" ({'; '.join(refused[:3])})" if refused else "")
            await self.col.update_one({"_id": key}, {"$set": {"at": now, "place_id": None, "checked": note, "names": tried,
                                                              "project": project, "locality": locality}}, upsert=True)
            return None, note
        loc = best["location"]
        name = (best.get("displayName") or {}).get("text") or ""
        note = f"Google Maps: {name}, {best.get('formattedAddress') or ''}".strip(", ")
        doc = {"at": now, "place_id": best["id"], "name": name, "address": best.get("formattedAddress") or "",
               "lat": loc["latitude"], "lon": loc["longitude"], "checked": note, "project": project, "locality": locality}
        await self.col.update_one({"_id": key}, {"$set": doc}, upsert=True)
        return _pin(doc), note
