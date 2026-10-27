"""Approximate area and network of an IP address, from DB-IP's free monthly files kept on our own disk.

The address is looked up at the moment of the request and never stored or sent anywhere (docs/plan/site-live-presence.md D6):
only the result (city, region, network name, data-centre or not) is kept. Mobile networks route many Pune phones through Mumbai
or another hub, so the city is "approx." wherever it is shown. Data: DB-IP Lite (CC BY 4.0), which asks for the credit
"IP Geolocation by DB-IP" with a link next to where it is shown.

Files: <dir>/dbip-city-lite.mmdb and <dir>/dbip-asn-lite.mmdb, refreshed by `refresh` (the tracking loop calls it). A missing
or broken file makes `lookup` return None; it never raises."""
import asyncio
import gzip
import ipaddress
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

import httpx
import maxminddb

log = logging.getLogger(__name__)

FILES = {"city": "dbip-city-lite.mmdb", "asn": "dbip-asn-lite.mmdb"}
URL = "https://download.db-ip.com/free/dbip-{kind}-lite-{month}.mmdb.gz"
MAX_AGE = timedelta(days=35)   # DB-IP publishes at the start of each month
CREDIT = "IP Geolocation by DB-IP"
CREDIT_URL = "https://db-ip.com"

# Networks of cloud and hosting companies: a page opened from one is a robot (crawler, preview, uptime check, headless test), not
# a person. Not here on purpose: Cloudflare, Akamai and Fastly, which also carry people (iCloud Private Relay, WARP).
DATA_CENTRES = ("amazon", "google", "microsoft", "digitalocean", "ovh", "hetzner", "linode", "vultr", "oracle", "alibaba",
                "tencent", "contabo", "leaseweb", "scaleway", "choopa", "m247", "datacamp", "hostinger", "ionos")
# Indian networks by the names people know them by (DB-IP gives the registered company name)
NETWORKS = (("jio", "Jio"), ("airtel", "Airtel"), ("bharti", "Airtel"), ("vodafone", "Vi"), ("idea cellular", "Vi"),
            ("bsnl", "BSNL"), ("bharat sanchar", "BSNL"), ("atria convergence", "ACT Fibernet"), ("hathway", "Hathway"),
            ("tata", "Tata"), ("excitel", "Excitel"), ("you broadband", "YOU Broadband"), ("spectranet", "Spectra"))


@dataclass(frozen=True)
class Place:
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]
    network: Optional[str]
    robot: bool


def network_name(org: Optional[str]) -> Optional[str]:
    """'Reliance Jio Infocomm Limited' -> 'Jio'; an unknown company keeps its name without 'Pvt Ltd' and the like."""
    if not org:
        return None
    low = org.lower()
    for mark, name in NETWORKS:
        if mark in low:
            return name
    words = [w for w in org.replace(",", " ").split() if w.lower().strip(".") not in ("pvt", "private", "ltd", "limited", "inc", "llc")]
    return " ".join(words)[:40] or None


def is_data_centre(org: Optional[str]) -> bool:
    low = (org or "").lower()
    return any(mark in low for mark in DATA_CENTRES)


def _public(ip: Optional[str]) -> Optional[str]:
    try:
        addr = ipaddress.ip_address((ip or "").strip())
    except ValueError:
        return None
    return str(addr) if addr.is_global else None


class GeoIP:
    """Opens the two files on first use and again when a refresh replaced them."""

    def __init__(self, directory: Path):
        self.dir = Path(directory)
        self._readers: Dict[str, Tuple[float, object]] = {}

    def _reader(self, kind: str):
        path = self.dir / FILES[kind]
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return None
        held = self._readers.get(kind)
        if held and held[0] == mtime:
            return held[1]
        try:
            reader = maxminddb.open_database(str(path))
        except Exception as e:  # a half-written or broken file: no answer, not a failed request
            log.warning("geoip: cannot open %s: %s", path, e)
            return None
        self._readers[kind] = (mtime, reader)
        return reader

    def lookup(self, ip: Optional[str]) -> Optional[Place]:
        addr = _public(ip)
        if not addr:
            return None
        try:
            city_db, asn_db = self._reader("city"), self._reader("asn")
            if city_db is None and asn_db is None:
                return None
            c = (city_db.get(addr) if city_db else None) or {}
            a = (asn_db.get(addr) if asn_db else None) or {}
        except Exception as e:
            log.warning("geoip: lookup failed: %s", e)
            return None
        org = a.get("autonomous_system_organization")
        region = next((s.get("names", {}).get("en") for s in c.get("subdivisions") or []), None)
        return Place(city=(c.get("city") or {}).get("names", {}).get("en"), region=region,
                     country=(c.get("country") or {}).get("iso_code"), network=network_name(org), robot=is_data_centre(org))


def _month(now: datetime, back: int = 0) -> str:
    y, m = now.year, now.month - back
    while m < 1:
        y, m = y - 1, m + 12
    return f"{y:04d}-{m:02d}"


def stale(directory: Path, now: Callable[[], datetime] = datetime.utcnow) -> bool:
    """True when either file is missing or older than MAX_AGE."""
    for name in FILES.values():
        try:
            if now() - datetime.utcfromtimestamp((Path(directory) / name).stat().st_mtime) > MAX_AGE:
                return True
        except OSError:
            return True
    return False


async def refresh(directory: Path, client: Optional[httpx.AsyncClient] = None, now: Callable[[], datetime] = datetime.utcnow) -> bool:
    """Download this month's files (last month's while this month's is not out yet), unpack beside the old ones, then swap them
    in with one rename each, so a lookup never reads a half-written file. Returns True when both files were replaced."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    own = client is None
    client = client or httpx.AsyncClient(timeout=120, follow_redirects=True)
    try:
        for kind, name in FILES.items():
            for back in (0, 1):
                gz = directory / (name + ".gz.part")
                async with client.stream("GET", URL.format(kind=kind, month=_month(now(), back))) as res:
                    if res.status_code == 404:
                        continue
                    res.raise_for_status()
                    with open(gz, "wb") as out:
                        async for chunk in res.aiter_bytes():
                            out.write(chunk)
                break
            else:
                log.warning("geoip: no %s file for this month or the last", kind)
                return False
            part = directory / (name + ".part")
            await asyncio.to_thread(_gunzip, gz, part)
            maxminddb.open_database(str(part)).close()  # a file that does not open is never swapped in
            os.replace(part, directory / name)
            gz.unlink(missing_ok=True)
            log.info("geoip: %s updated", name)
        return True
    finally:
        if own:
            await client.aclose()


def _gunzip(src: Path, dst: Path) -> None:
    with gzip.open(src, "rb") as f_in, open(dst, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
