"""Reads one project's public record from MahaRERA's own API (the JSON behind maharerait.maharashtra.gov.in/public/project/view/<id>).

No login and no captcha: the public view page calls this endpoint with just the internal project id (verified 2026-10-03).
The promoter name is not in this answer, so callers keep it from the search card (the newsroom register has it).
"""
import asyncio
import logging
from typing import Awaitable, Callable, Optional

import httpx

log = logging.getLogger(__name__)

API = ("https://maharerait.maharashtra.gov.in/api/maha-rera-public-view-project-registration-service/public/"
       "projectregistartion/getProjectGeneralDetailsByProjectId")
VIEW = "https://maharerait.maharashtra.gov.in/public/project/view/"
TIMEOUT_S = 30.0
TRIES = 3
RETRY_DELAY = 3.0  # seconds, grows per try; tests set it to 0

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


def make_fetch(transport: Optional[httpx.AsyncBaseTransport] = None) -> Fetch:
    async def fetch(maharera_id: int) -> Optional[dict]:
        delay = RETRY_DELAY
        for attempt in range(TRIES):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT_S, transport=transport,
                                             headers={"User-Agent": "Mozilla/5.0 (Avasetu project check)"}) as c:
                    res = await c.post(API, json={"projectId": int(maharera_id)})
                if res.status_code == 200:
                    return res.json()
                log.warning("MahaRERA project %s answered %s", maharera_id, res.status_code)
            except (httpx.HTTPError, ValueError) as e:
                log.warning("MahaRERA project %s failed: %s", maharera_id, e)
            if attempt < TRIES - 1:
                await asyncio.sleep(delay)
                delay *= 2
        return None
    return fetch
