"""Deterministic (no network) extractor: free text -> Extraction of listing facts with confidences."""
from typing import Optional

from . import extract_numbers as num
from . import extract_text as txt
from .geo import Geo, find_geo
from .schemas import Extraction
from .text_norm import normalise

MAX_TEXT = 6000


def extract(text: str, city_hint: Optional[str] = None) -> tuple[Extraction, Geo]:
    raw = (text or "")[:MAX_TEXT]
    ex = Extraction()
    t = normalise(raw)
    if not t:
        geo = find_geo("", city_hint)
        ex.set("city", geo.city, geo.city_conf)
        return ex, geo
    clean = txt.strip_near(t).replace("security deposit", "deposit")

    price = num.parse_price(t)
    if price:
        ex.set("price_inr", price[0], price[1])
    tx = num.parse_transaction(t, price[0] if price else None)
    if tx:
        ex.set("transaction", *tx)

    bhk = num.parse_bhk(clean)
    if bhk:
        ex.set("bhk", *bhk)
    ptype = txt.parse_type(clean, bhk is not None)
    if ptype:
        ex.set("property_type", *ptype)

    areas = num.parse_areas(t)
    if "carpet" in areas:
        ex.set("carpet_sqft", *areas["carpet"])
    if "sba" in areas:
        ex.set("super_built_up_sqft", *areas["sba"])
    for k, (v, c) in num.parse_floors(t).items():
        ex.set(k, v, c)

    for key, parsed in (("furnishing", txt.parse_furnishing(t)), ("possession", txt.parse_possession(t))):
        if parsed:
            ex.set(key, *parsed)
    ex.set("amenities", txt.parse_amenities(clean), 0.9)
    ex.set("rera_no", txt.parse_rera(raw), 0.95)

    project = txt.parse_project(raw)
    ex.set("project_name", project, 0.7)
    geo = find_geo(t, city_hint)
    if geo.locality:
        ex.set("locality", geo.locality, geo.locality_conf)
    else:
        ex.set("locality", txt.parse_unknown_locality(raw, project), 0.5)
    ex.set("city", geo.city, geo.city_conf)
    return ex, geo
