"""Soft plausibility warnings for a draft. They never change values."""
from typing import Optional

from .copywriter import format_inr, format_price_short
from .gazetteer import LOCALITIES


def build_warnings(f: dict, conf: dict) -> list[str]:
    w: list[str] = []
    if not f.get("city"):
        w.append("City not found in the text; please add the city.")
    tx, price = f.get("transaction"), f.get("price_inr")
    if tx and conf.get("transaction", 1) < 0.7 and price:
        w.append(f"Sale or rent was not stated; assumed '{tx}' from the price.")
    carpet, sba = f.get("carpet_sqft"), f.get("super_built_up_sqft")
    if carpet and sba and carpet > sba:
        w.append("Carpet area is larger than super built-up area; please check the areas.")
    for key, label in (("carpet_sqft", "carpet"), ("super_built_up_sqft", "super built-up")):
        if f.get(key) and conf.get(key, 1) < 0.7 and not (carpet and sba):
            w.append(f"Area type was not stated; treated as {label} area.")
            break
    area: Optional[int] = sba or carpet
    if price and tx == "rent":
        if price < 1500 or price > 1_000_000:
            w.append(f"Monthly rent of Rs {format_inr(price)} looks unusual; please check.")
    elif price and tx == "sale":
        if price < 100_000:
            w.append(f"Sale price of Rs {format_inr(price)} looks very low; did you mean lakh or crore?")
        elif area and f.get("property_type") != "plot":
            psf = price / area
            loc = LOCALITIES.get(f.get("locality", ""))
            if loc:
                lo, hi = loc[1]
                if psf < lo * 0.5:
                    w.append(f"Price looks low for {f['locality']} (about Rs {format_inr(int(psf))}/sq ft; "
                             f"typical Rs {format_inr(lo)}-{format_inr(hi)}).")
                elif psf > hi * 1.8:
                    w.append(f"Price looks high for {f['locality']} (about Rs {format_inr(int(psf))}/sq ft; "
                             f"typical Rs {format_inr(lo)}-{format_inr(hi)}).")
            elif psf < 1500 or psf > 120_000:
                w.append(f"Price of {format_price_short(price)} for {format_inr(area)} sq ft "
                         f"(Rs {format_inr(int(psf))}/sq ft) looks unusual.")
    bhk = f.get("bhk")
    if bhk and area and f.get("property_type") in (None, "apartment") and bhk >= 1:
        per = (carpet or area) / bhk
        if per < 180 or per > 1800:
            w.append(f"Area of {format_inr(carpet or area)} sq ft looks implausible for {bhk:g} BHK; please check.")
    if f.get("floor") is not None and f.get("total_floors") and f["floor"] > f["total_floors"]:
        w.append("Floor number is higher than the total floors.")
    return w
