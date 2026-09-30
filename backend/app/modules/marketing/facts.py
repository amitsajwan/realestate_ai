"""Listing facts + formatting helpers + per-language word tables. Everything here is derived from the listing only."""
from dataclasses import dataclass, field
from typing import List, Optional

PUBLIC_NAME = "PUNE Property team"
LAKH = 100_000
CRORE = 10_000_000

# Round ceilings for the "under Rs X" angle (rupees). Sale first, then monthly rent.
SALE_CEILINGS = [1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000, 7_500_000, 10_000_000, 15_000_000,
                 20_000_000, 30_000_000, 50_000_000, 75_000_000, 100_000_000]
RENT_CEILINGS = [10_000, 15_000, 20_000, 25_000, 30_000, 40_000, 50_000, 75_000, 100_000, 150_000, 200_000,
                 300_000, 500_000]


def _trim(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def money(n: int, rent: bool = False) -> str:
    """8500000 -> '₹85 Lakh', 12500000 -> '₹1.25 Cr', 45000 -> '₹45,000' (+ '/month' for rent)."""
    if n >= CRORE:
        s = f"₹{_trim(n / CRORE)} Cr"
    elif n >= LAKH:
        s = f"₹{_trim(n / LAKH)} Lakh"
    else:
        s = f"₹{n:,}"
    return s + "/month" if rent else s


def budget_phrase(price: int, rent: bool = False) -> str:
    """'under Rs 1 Cr': smallest round ceiling strictly above the price."""
    ceilings = RENT_CEILINGS if rent else SALE_CEILINGS
    for c in ceilings:
        if price < c:
            return f"under {money(c, rent)}"
    step = 50_000_000 if not rent else 500_000
    c = (price // step + 1) * step
    return f"under {money(c, rent)}"


def sqft(n: int) -> str:
    return f"{n:,} sq ft"


def bhk_label(b: float) -> str:
    return f"{int(b)} BHK" if float(b).is_integer() else f"{b:g} BHK"


T = {
    "en": {
        "tx": {"sale": "for sale", "rent": "for rent"},
        "types": {"apartment": "apartment", "villa": "villa", "house": "house", "plot": "plot",
                  "commercial": "commercial property", "office": "office", "shop": "shop"},
        "poss": {"ready": "Ready to move", "under_construction": "Under construction"},
        "furn": {"unfurnished": "Unfurnished", "semi": "Semi-furnished", "furnished": "Furnished"},
        "title": "{bhk}{type} {tx} in {loc}",
        "area": "Area", "possession": "Possession", "amen": "Amenities", "floor": "Floor {f} of {t}",
        "floor1": "Floor {f}", "rera": "RERA", "price": "Price", "details_link": "Details and photos",
    },
    "hi": {
        "tx": {"sale": "बिक्री के लिए", "rent": "किराये के लिए"},
        "types": {"apartment": "अपार्टमेंट", "villa": "विला", "house": "घर", "plot": "प्लॉट",
                  "commercial": "कमर्शियल प्रॉपर्टी", "office": "ऑफिस", "shop": "दुकान"},
        "poss": {"ready": "तैयार (रेडी टू मूव)", "under_construction": "निर्माणाधीन"},
        "furn": {"unfurnished": "बिना फर्नीचर", "semi": "सेमी-फर्निश्ड", "furnished": "फर्निश्ड"},
        "title": "{loc} में {bhk}{type} {tx}",
        "area": "क्षेत्रफल", "possession": "पजेशन", "amen": "सुविधाएं", "floor": "मंज़िल {f}, कुल {t}",
        "floor1": "मंज़िल {f}", "rera": "RERA", "price": "कीमत", "details_link": "विवरण और फोटो",
    },
    "mr": {
        "tx": {"sale": "विक्रीसाठी", "rent": "भाड्याने"},
        "types": {"apartment": "अपार्टमेंट", "villa": "व्हिला", "house": "घर", "plot": "प्लॉट",
                  "commercial": "कमर्शियल प्रॉपर्टी", "office": "ऑफिस", "shop": "दुकान"},
        "poss": {"ready": "तयार (रेडी टू मूव)", "under_construction": "बांधकाम सुरू"},
        "furn": {"unfurnished": "अनफर्निश्ड", "semi": "सेमी-फर्निश्ड", "furnished": "फर्निश्ड"},
        "title": "{loc} येथे {bhk}{type} {tx}",
        "area": "क्षेत्रफळ", "possession": "ताबा", "amen": "सुविधा", "floor": "मजला {f}, एकूण {t}",
        "floor1": "मजला {f}", "rera": "RERA", "price": "किंमत", "details_link": "तपशील आणि फोटो",
    },
}
SUPPORTED = tuple(T)


@dataclass
class Facts:
    listing_id: str
    transaction: str = "sale"
    ptype: str = "apartment"
    price: Optional[int] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    project: Optional[str] = None
    bhk: Optional[float] = None
    area: Optional[int] = None
    area_kind: Optional[str] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    furnishing: Optional[str] = None
    possession: Optional[str] = None
    rera: Optional[str] = None
    amenities: List[str] = field(default_factory=list)
    agent_name: str = ""
    agent_phone: Optional[str] = None
    share_url: str = ""

    @classmethod
    def from_docs(cls, listing: dict, profile: Optional[dict], share_url: str) -> "Facts":
        profile = profile or {}
        carpet, sba = listing.get("carpet_sqft"), listing.get("super_built_up_sqft")
        return cls(
            listing_id=str(listing.get("_id") or listing.get("id") or ""),
            transaction=listing.get("transaction") or "sale", ptype=listing.get("property_type") or "apartment",
            price=listing.get("price_inr"), city=listing.get("city"), locality=listing.get("locality"),
            project=listing.get("project_name"), bhk=listing.get("bhk"),
            area=carpet or sba, area_kind="carpet" if carpet else ("super built-up" if sba else None),
            floor=listing.get("floor"), total_floors=listing.get("total_floors"),
            furnishing=listing.get("furnishing"), possession=listing.get("possession"), rera=listing.get("rera_no"),
            amenities=[a for a in (listing.get("amenities") or []) if a],
            agent_name=PUBLIC_NAME, agent_phone=profile.get("phone"),  # posts are signed by the team, never by an agent's own name
            share_url=share_url)

    # -- derived text ------------------------------------------------------------------------
    @property
    def rent(self) -> bool:
        return self.transaction == "rent"

    @property
    def price_text(self) -> Optional[str]:
        return money(self.price, self.rent) if self.price else None

    @property
    def bhk_text(self) -> Optional[str]:
        return bhk_label(self.bhk) if self.bhk else None

    @property
    def area_text(self) -> Optional[str]:
        return sqft(self.area) if self.area else None

    @property
    def loc(self) -> str:
        return ", ".join(p for p in (self.locality, self.city) if p)

    def type_text(self, lang: str = "en") -> str:
        return T[lang]["types"].get(self.ptype, self.ptype)

    def possession_text(self, lang: str = "en") -> Optional[str]:
        if not self.possession:
            return None
        return T[lang]["poss"].get(self.possession, self.possession)

    def floor_text(self, lang: str = "en") -> Optional[str]:
        if self.floor is None:
            return None
        if self.total_floors:
            return T[lang]["floor"].format(f=self.floor, t=self.total_floors)
        return T[lang]["floor1"].format(f=self.floor)

    def title_line(self, lang: str = "en") -> str:
        t = T[lang]
        bhk = f"{self.bhk_text} " if self.bhk_text else ""
        loc = self.loc or self.city or ""
        s = t["title"].format(bhk=bhk, type=self.type_text(lang), tx=t["tx"][self.transaction], loc=loc)
        if not loc:  # no location known: drop the dangling preposition
            s = s.replace(" in ", "").replace(" में ", " ").replace(" येथे ", " ").strip()
        return s.replace("  ", " ").strip()

    def angle(self) -> str:
        """Deterministic one-line buyer angle (contract rules), always English."""
        prefix = {"ready": "Ready-to-move", "under_construction": "Under-construction"}.get(self.possession or "", "")
        parts = [prefix, self.bhk_text or "", self.type_text("en")]
        s = " ".join(p for p in parts if p)
        if self.rent:
            s += " for rent"
        if self.locality or self.city:
            s += f" in {self.locality or self.city}"
        if self.price:
            s += f" {budget_phrase(self.price, self.rent)}"
        return s[0].upper() + s[1:]

    def protected(self) -> List[str]:
        """Facts an LLM re-write must never drop (when they are present in the draft)."""
        out = [self.price_text, self.bhk_text, self.locality, self.area_text, self.rera]
        return [x for x in out if x]
