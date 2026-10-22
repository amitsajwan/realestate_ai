"""A project's home types and payment plan as the listing carries them (listings.schemas.Configuration, payment_plan): what
the details post, the creative room's fact book and the captions say about prices. Pure: listing dict in, values out.

    rows(listing)        [{"bhk", "label", "carpet_sqft", "price_inr"}], smallest first; the listing's own one home when it
                         has no table; [] when it has neither a BHK nor a price
    bhk_range(rows)      "2, 3 & 4 BHK"
    from_price(listing)  the lowest price of the table, else the listing's price
"""
import re
from typing import Any, Dict, List, Optional

from app.platform.text import bhk_label, money as rupees

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MONTH = re.compile(r"(\d{4})-(0[1-9]|1[0-2])(?:-\d{2})?")


def rows(listing: dict) -> List[Dict[str, Any]]:
    table = [c for c in listing.get("configurations") or [] if isinstance(c, dict) and c.get("bhk")]
    if not table and (listing.get("bhk") or listing.get("price_inr")) and listing.get("property_type") != "plot":
        table = [{"bhk": listing.get("bhk"), "carpet_sqft": listing.get("carpet_sqft"), "price_inr": listing.get("price_inr")}]
    out = []
    for c in sorted(table, key=lambda c: (float(c.get("bhk") or 0), c.get("carpet_sqft") or 0, c.get("price_inr") or 0)):
        out.append({"bhk": c.get("bhk"), "label": bhk_label(float(c["bhk"])) if c.get("bhk") else "Home",
                    "carpet_sqft": c.get("carpet_sqft"), "price_inr": c.get("price_inr")})
    return out


def bhk_range(table: List[Dict[str, Any]]) -> str:
    """'2, 3 & 4 BHK' (each BHK once, in order); '2 BHK' for one; '' without rows."""
    nums = list(dict.fromkeys(r["label"].replace(" BHK", "") for r in table if r["label"].endswith(" BHK")))
    if not nums:
        return ""
    return (", ".join(nums[:-1]) + " & " + nums[-1] if len(nums) > 1 else nums[0]) + " BHK"


def from_price(listing: dict) -> Optional[int]:
    prices = [r["price_inr"] for r in rows(listing) if r.get("price_inr")]
    return min(prices) if prices else (listing.get("price_inr") or None)


def several(listing: dict) -> bool:
    """More than one home type is on offer: prices are 'from', never one flat's price."""
    return len(rows(listing)) > 1 or listing.get("listing_scope") == "layout"


def short_price(n: Optional[int]) -> str:
    """12000000 -> '₹1.20 Cr', 8500000 -> '₹85 Lakh' (as builders print a price sheet)."""
    if not n:
        return ""
    if n >= 10_000_000:
        return f"₹{n / 10_000_000:.2f} Cr"
    lakh = n / 100_000
    return f"₹{lakh:.0f} Lakh" if lakh == int(lakh) else f"₹{lakh:.1f} Lakh"


def deal(listing: dict) -> tuple:
    """(money line, plan line) a reel closes on, '' for what the listing lacks: ('2, 3 & 4 BHK from ₹1.20 Cr',
    '20:20:30:30 payment plan'); one home: ('2 BHK at ₹1.29 Cr', ...)."""
    table, low = rows(listing), from_price(listing)
    plot = listing.get("property_type") == "plot"
    if listing.get("transaction") == "rent":   # a rent is a month's money ('₹25,000/month'), never '₹0.2 Lakh'
        what = table[0]["label"] if table else ""
        return ((f"{what} at " if what else "") + rupees(int(low), rent=True)) if low else "", ""
    if several(listing):
        what = bhk_range(table) or ("Plots" if plot else "Homes")
        money = f"{what} from {short_price(low)}" if low else ""
    else:
        what = table[0]["label"] if table else ("Plot" if plot else "")
        money = (f"{what} at {short_price(low)}" if what else short_price(low)) if low else ""
    plan = payment_plan(listing)
    return money, (f"{plan} payment plan" if plan else "")


def payment_plan(listing: dict) -> str:
    return " ".join(str(listing.get("payment_plan") or "").split())


def possession(listing: dict) -> str:
    """'Aug 2032' for the builder's month, 'Ready to move', 'Under construction', or ''."""
    p = str(listing.get("possession") or "").strip()
    m = MONTH.fullmatch(p)
    if m:
        return f"{MONTHS[int(m.group(2)) - 1]} {m.group(1)}"
    return {"ready": "Ready to move", "under_construction": "Under construction"}.get(p, "")
