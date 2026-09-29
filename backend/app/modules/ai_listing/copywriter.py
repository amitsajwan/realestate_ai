"""Deterministic English title/description built only from extracted facts (never invents anything)."""
import calendar
from typing import Any, Optional

_TYPE_LABEL = {"apartment": "Apartment", "villa": "Villa", "house": "Independent house", "plot": "Plot",
               "commercial": "Commercial property", "office": "Office space", "shop": "Shop"}


def format_inr(n: int) -> str:
    """Indian digit grouping: 8500000 -> 85,00,000."""
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def format_price_short(n: int, rent: bool = False) -> str:
    def trim(x: float) -> str:
        return f"{x:.2f}".rstrip("0").rstrip(".")
    if rent:
        return f"Rs {format_inr(n)}/month"
    if n >= 10_000_000:
        return f"{trim(n / 1e7)} Cr"
    if n >= 100_000:
        return f"{trim(n / 1e5)} L"
    return f"Rs {format_inr(n)}"


def _bhk(v: Any) -> str:
    return f"{int(v) if float(v) == int(v) else v} BHK"


def _label(f: dict) -> str:
    bhk, t = f.get("bhk"), f.get("property_type")
    if bhk is not None and t in (None, "apartment"):
        return _bhk(bhk)
    if bhk is not None:
        return f"{_bhk(bhk)} {_TYPE_LABEL[t]}"
    return _TYPE_LABEL.get(t, "") if t else ""


def _where(f: dict) -> str:
    return ", ".join(x for x in (f.get("locality"), f.get("city")) if x)


def make_title(f: dict) -> Optional[str]:
    label = _label(f)
    if not (label or f.get("price_inr") or f.get("locality")):
        return None
    tx = f.get("transaction")
    parts = [label or "Property"]
    if tx:
        parts.append(f"for {tx}")
    where = _where(f)
    if where:
        parts.append(f"in {where}")
    title = " ".join(parts)
    if f.get("price_inr"):
        title += " - " + format_price_short(f["price_inr"], tx == "rent")
    return title[:120]


def _possession(p: str) -> str:
    if p == "ready":
        return "ready to move in"
    if p == "under_construction":
        return "under construction"
    if len(p) == 7 and p[4] == "-" and p[5:].isdigit() and 1 <= int(p[5:]) <= 12:
        return f"possession expected in {calendar.month_name[int(p[5:])]} {p[:4]}"
    return f"possession {p}"


def make_description_en(f: dict) -> Optional[str]:
    label = _label(f)
    if not (label or f.get("price_inr") or f.get("locality")):
        return None
    tx = f.get("transaction")
    s = []
    art = "An" if label[:1] in ("A", "I", "O", "E", "U", "8") else "A"
    lead = f"{art} {label}" if label else "A property"
    sent = lead + (f" is available for {tx}" if tx else " is listed")
    if f.get("locality") or f.get("city"):
        sent += f" in {_where(f)}"
    if f.get("project_name"):
        sent += f" ({f['project_name']})"
    s.append(sent + ".")
    facts = []
    if f.get("carpet_sqft"):
        facts.append(f"a carpet area of {format_inr(f['carpet_sqft'])} sq ft")
    if f.get("super_built_up_sqft"):
        facts.append(f"a super built-up area of {format_inr(f['super_built_up_sqft'])} sq ft")
    if facts:
        s.append("It has " + " and ".join(facts) + ".")
    extra = []
    if f.get("floor") is not None and f.get("total_floors"):
        extra.append(f"on floor {f['floor']} of {f['total_floors']}")
    elif f.get("floor") is not None:
        extra.append("on the ground floor" if f["floor"] == 0 else f"on floor {f['floor']}")
    elif f.get("total_floors"):
        extra.append(f"in a {f['total_floors']}-floor building")
    if f.get("furnishing"):
        extra.append({"semi": "semi-furnished"}.get(f["furnishing"], f["furnishing"]))
    if f.get("possession"):
        extra.append(_possession(f["possession"]))
    if extra:
        s.append("It is " + ", ".join(extra) + ".")
    if f.get("price_inr"):
        what = "monthly rent" if tx == "rent" else "asking price"
        price = f["price_inr"]
        full = f"Rs {format_inr(price)}"
        short = format_price_short(price, tx == "rent")
        s.append(f"The {what} is {full}" + ("" if short == full or tx == "rent" else f" ({short})") + ".")
    tail = []
    if f.get("amenities"):
        tail.append("Amenities mentioned: " + ", ".join(f["amenities"]))
    if f.get("rera_no"):
        tail.append(f"RERA no. {f['rera_no']}")
    if tail:
        s.append(". ".join(tail) + ".")
    return " ".join(s[:5])
