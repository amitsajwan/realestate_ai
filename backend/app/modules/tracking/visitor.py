"""What we keep about the person behind an event (docs/plan/site-live-presence.md D6): device label, approximate area, network
name, robot or not, and whether it is the agent's own browser. The IP address is used for the lookup and then dropped."""
from typing import Callable, Dict, Optional

from app.platform.geoip import GeoIP, Place

from . import config, device

Lookup = Callable[[Optional[str]], Optional[Place]]
_geo: Optional[GeoIP] = None


def default_lookup(ip: Optional[str]) -> Optional[Place]:
    """One GeoIP for the process, so its open files are shared by every request."""
    global _geo
    if _geo is None:
        _geo = GeoIP(config.load().geoip_dir)
    return _geo.lookup(ip)


def area_of(place: Optional[Place]) -> Optional[str]:
    """'Pune, Maharashtra'; outside India the country is added ('Dubai, AE')."""
    if not place or not (place.city or place.region):
        return None
    parts = [place.city] if place.city else []
    if place.region and place.region != place.city:
        parts.append(place.region)
    if place.country and place.country != "IN":
        parts.append(place.country)
    return ", ".join(parts)


def fields(user_agent: Optional[str], ip: Optional[str], staff: bool, lookup: Lookup) -> Dict[str, object]:
    """The visitor fields stored on an event; empty values are left out so old and new events read the same."""
    place = lookup(ip)
    out = {"device": device.label(user_agent), "area": area_of(place), "network": place.network if place else None}
    out = {k: v for k, v in out.items() if v}
    if place and place.robot:
        out["robot"] = True
    if staff:
        out["staff"] = True
    return out
