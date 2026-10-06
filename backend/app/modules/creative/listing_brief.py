"""Build a Brief from a listing document (LC-1). Pure: takes the stored dict, does no I/O.

Every number the copy may use is written here as the same human string the copy would use ("₹85 lakh", "1,050 sq ft",
"2 BHK"), so the no-invented-number guard accepts listing facts and still rejects anything else."""
from typing import Any, Dict, List

from .models import Brief, Voice

_TYPE_LABEL = {"apartment": "flat", "villa": "villa", "house": "independent house", "plot": "plot",
               "commercial": "commercial property", "office": "office space", "shop": "shop"}


def _num(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".")


def price_label(price_inr: int, transaction: str = "sale") -> str:
    """8500000 -> "₹85 lakh", 12500000 -> "₹1.25 crore"; rent 25000 -> "₹25,000 a month"."""
    n = int(price_inr)
    if transaction == "rent":
        return f"₹{n:,} a month"
    if n >= 1_00_00_000:
        return f"₹{_num(n / 1_00_00_000)} crore"
    if n >= 1_00_000:
        return f"₹{_num(n / 1_00_000)} lakh"
    return f"₹{n:,}"


def _bhk(bhk: Any) -> str:
    return f"{_num(float(bhk))} BHK" if bhk else ""


def brief_from_listing(doc: Dict[str, Any]) -> Brief:
    """A Brief whose facts are only what the listing states. Missing fields stay empty; nothing is guessed."""
    transaction = (doc.get("transaction") or "").strip()
    ptype = (doc.get("property_type") or "").strip()
    kind = _TYPE_LABEL.get(ptype, "home")
    bhk = _bhk(doc.get("bhk"))
    carpet = f"{int(doc['carpet_sqft']):,} sq ft carpet" if doc.get("carpet_sqft") else ""
    price = price_label(doc["price_inr"], transaction) if doc.get("price_inr") else ""
    locality = (doc.get("locality") or "").strip()
    city = (doc.get("city") or "").strip()
    project = (doc.get("project_name") or "").strip()
    rera = (doc.get("rera_no") or "").strip()
    amenities = [a.strip() for a in doc.get("amenities") or [] if isinstance(a, str) and a.strip()]
    media = [m.get("url", "") for m in sorted(doc.get("media") or [], key=lambda m: m.get("order", 0))
             if isinstance(m, dict) and m.get("url")]

    what = " ".join(p for p in (bhk, kind) if p)
    where = ", ".join(p for p in (project, locality, city) if p)
    facts: List[str] = []
    verb = "for rent" if transaction == "rent" else "for sale" if transaction == "sale" else ""
    facts.append(" ".join(p for p in (what.capitalize(), verb, f"in {where}" if where else "") if p) + ".")
    if price:
        facts.append(f"Asking {'rent' if transaction == 'rent' else 'price'}: {price}.")
    if carpet:
        facts.append(f"Carpet area: {carpet}.")
    if rera:
        facts.append(f"MahaRERA registration: {rera}.")
    if amenities:
        facts.append("Amenities: " + ", ".join(amenities) + ".")

    return Brief(
        topic=(doc.get("title") or "").strip() or facts[0].rstrip("."),
        facts=facts,
        short=(what or kind)[:30],
        stat_value=price,
        stat_label=f"asking {'rent' if transaction == 'rent' else 'price'} for this {what or kind}" if price else "",
        steps=[f"Has {a}" for a in amenities[:6]] if len(amenities) >= 3 else [],
        tip="Ask for the carpet area and the MahaRERA number in writing before any token.",
        listing_transaction=transaction,
        listing_property_type=ptype,
        listing_price_inr=price,
        listing_bhk=bhk,
        listing_carpet_sqft=carpet,
        listing_locality=locality,
        listing_project_name=project,
        listing_rera_no=rera,
        listing_amenities=amenities,
        listing_media_refs=media,
        voice=Voice(areas=", ".join(p for p in (locality, city) if p)),
        mode="listing",
    )
