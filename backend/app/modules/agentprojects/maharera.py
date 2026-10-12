"""Reads one project's public record from MahaRERA's own API (the JSON behind maharerait.maharashtra.gov.in/public/project/view/<id>).

No login and no captcha: the public view page calls this endpoint with just the internal project id (verified 2026-10-03).
The promoter name is not in this answer, so callers keep it from the search card (the newsroom register has it).
"""
import asyncio
import logging
import ssl
from pathlib import Path
from typing import Awaitable, Callable, List, Optional

import certifi
import httpx

log = logging.getLogger(__name__)

API = ("https://maharerait.maharashtra.gov.in/api/maha-rera-public-view-project-registration-service/public/"
       "projectregistartion/getProjectGeneralDetailsByProjectId")
BUILDINGS_API = ("https://maharerait.maharashtra.gov.in/api/maha-rera-public-view-project-registration-service/public/"
                 "projectregistartion/getBuildingWingUnitSummary")  # open, same {"projectId"} body (verified 2026-10-07)
VIEW = "https://maharerait.maharashtra.gov.in/public/project/view/"
TIMEOUT_S = 30.0
TRIES = 3
RETRY_DELAY = 3.0  # seconds, grows per try; tests set it to 0
# MahaRERA's server sends the wrong intermediate (GlobalSign RSA OV SSL CA 2018) for a certificate issued by GlobalSign GCC R46
# OV TLS CA 2025 (seen 2026-10-12): browsers fetch the right one, Python cannot, and every read failed. We add it ourselves.
INTERMEDIATE = Path(__file__).parent / "assets" / "globalsign_gcc_r46_ov_tls_ca_2025.pem"


def _tls() -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.load_verify_locations(cafile=str(INTERMEDIATE))
    return ctx


TLS = _tls()

Fetch = Callable[[int], Awaitable[Optional[dict]]]


class MahaReraError(Exception):
    pass


def view_url(maharera_id: int) -> str:
    return f"{VIEW}{int(maharera_id)}"


def _date(v) -> Optional[str]:
    s = str(v or "")[:10]
    return s if len(s) == 10 and s[4] == "-" and s[7] == "-" else None


def _int(v) -> Optional[int]:
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def parse_general(body: dict, regno: str, maharera_id: int) -> dict:
    """The MahaRERA answer -> Rera fields. Raises when the record is missing or is a different registration."""
    if not isinstance(body, dict) or str(body.get("status")) != "1" or not isinstance(body.get("responseObject"), dict):
        raise MahaReraError("MahaRERA did not return the project")
    r = body["responseObject"]
    got = str(r.get("projectRegistartionNo") or "").strip().upper()
    if got != regno.upper():
        raise MahaReraError(f"MahaRERA id {maharera_id} is {got or 'unknown'}, not {regno}")
    now = _date(r.get("projectProposeComplitionDate")) or _date(r.get("revisedDate"))
    return {
        "regno": got,
        "name": str(r.get("projectName") or "").strip(),
        "project_type": str(r.get("projectTypeName") or "").strip(),
        "registered_on": _date(r.get("reraRegistrationDate")),
        "completion_at_registration": _date(r.get("originalProjectProposeCompletionDate")) or now,
        "completion_now": now,
        "units_total": _int(r.get("totalNumberOfUnits")),
        "units_booked": _int(r.get("totalNumberOfSoldUnits")),
        "url": view_url(maharera_id),
    }


def _name(v) -> Optional[str]:
    s = str(v or "").strip()
    return None if s.upper() in ("", "NA", "N/A", "-", "NONE", "NULL") else s


def parse_buildings(body: dict, regno: str, maharera_id: int) -> List[dict]:
    """MahaRERA's building/wing summary -> [{name, wing, floors, units_residential, units_other, units_total}]. [] when the
    project has no buildings (a plotted layout answers with none). Raises when the answer is not this project's: every row's
    projectId must be `maharera_id` and its projectRegistartionNo `regno`. Floors: sanctioned, else proposed (MahaRERA also
    gives habitable floors, often fewer: 15 sanctioned, 12 habitable for Anshul Medora C). Wing "NA" means no wings."""
    if not isinstance(body, dict) or str(body.get("status")) != "1":
        raise MahaReraError("MahaRERA did not return the buildings")
    rows = body.get("responseObject") or []
    if not isinstance(rows, list):
        raise MahaReraError("MahaRERA buildings answer is not a list")
    out = []
    for r in rows:
        if not isinstance(r, dict) or r.get("isActive") == 0:
            continue
        got = str(r.get("projectRegistartionNo") or "").strip().upper()
        if got != regno.upper() or _int(r.get("projectId")) != int(maharera_id):
            raise MahaReraError(f"MahaRERA buildings for id {maharera_id} are {got or 'unknown'}, not {regno}")
        res, other = _int(r.get("residentialUnitCount")), _int(r.get("nonResidentialUnitCount"))
        out.append({
            "name": _name(r.get("advertisedBuildingNameNumber")) or _name(r.get("buildingNameNumber")),
            "wing": _name(r.get("buildingWingsNameNumber")),
            "floors": _int(r.get("noOfBuildingWingFloorSanctioned")) or _int(r.get("noOfBuildingWingFloorProposed")),
            "units_residential": res, "units_other": other,
            "units_total": _int(r.get("totalUnitCount")) or ((res or 0) + (other or 0)) or None,
        })
    return out


def building_totals(buildings: List[dict]) -> dict:
    """{towers, max_floors, units_total, units_residential, units_other}; a tower is a distinct building name."""
    names = {(b.get("name") or f"#{i}") for i, b in enumerate(buildings)}
    floors = [b["floors"] for b in buildings if b.get("floors")]

    def total(k: str) -> Optional[int]:
        return sum(b.get(k) or 0 for b in buildings) or None

    return {"towers": len(names) if buildings else None, "max_floors": max(floors) if floors else None,
            "units_total": total("units_total"), "units_residential": total("units_residential"), "units_other": total("units_other")}


def _make(url: str, what: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> Fetch:
    async def fetch(maharera_id: int) -> Optional[dict]:
        delay = RETRY_DELAY
        for attempt in range(TRIES):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT_S, transport=transport, verify=TLS,
                                             headers={"User-Agent": "Mozilla/5.0 (Avasetu project check)"}) as c:
                    res = await c.post(url, json={"projectId": int(maharera_id)})
                if res.status_code == 200:
                    return res.json()
                log.warning("MahaRERA %s %s answered %s", what, maharera_id, res.status_code)
            except (httpx.HTTPError, ValueError) as e:
                log.warning("MahaRERA %s %s failed: %s", what, maharera_id, e)
            if attempt < TRIES - 1:
                await asyncio.sleep(delay)
                delay *= 2
        return None
    return fetch


def make_fetch(transport: Optional[httpx.AsyncBaseTransport] = None) -> Fetch:
    return _make(API, "project", transport)


def make_fetch_buildings(transport: Optional[httpx.AsyncBaseTransport] = None) -> Fetch:
    """The open building/wing summary (no login, no captcha). MahaRERA's other detail endpoints (amenities, land, geo, unit
    types) need its login and captcha: never used."""
    return _make(BUILDINGS_API, "buildings", transport)
