"""Selling points printed on a builder's brochure, as structured facts (files.READ_PROMPT "facts").

The vision reader returns them alongside the loose claims; this module checks and parses them (₹2,99,000/- -> 299000,
"₹1 लाख" -> 100000), merges them across pages, and turns them into the `selling_points` an agent confirms on the listing:

    {key, text, text_local?, value, source: "brochure"}   (keys: POINT_KEYS)

They are facts as printed, so the claims' hype filter does not apply to them; returns, "secure income", "high growth" are
still dropped. Only points the agent confirmed (`confirmed: true`) ever reach the posts (gather.listing_readings ->
"point.<key>" facts, source "agent confirmed"). Pure: no I/O."""
import re
from typing import Any, Dict, List, Optional

FACT_KEYS = ("starting_price_inr", "booking_amount_inr", "offer_label", "water", "power", "road_widths_ft", "vastu",
             "total_acres", "village", "taluka")
POINT_KEYS = ("starting_price", "booking_amount", "offer", "water", "power", "roads", "vastu", "land_area")
MAX_POINTS = 12

PRELAUNCH = re.compile(r"pre[\s\-_]*launch", re.I)
# never said in a post, even when printed: returns and income promises
BANNED = re.compile(r"\b(returns?|appreciation|profit|earning|income|growth|investment|assured|guaranteed?)\b"
                    r"|गुंतवणूक|परतावा|कमाई|निवेश|मुनाफ|उत्पन्न", re.I)
_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
_LAKH = re.compile(r"^\s*(?:lakhs?|lacs?|lac|l\b|लाख|लक्ष)", re.I)
_CRORE = re.compile(r"^\s*(?:crores?|cr\b|कोटी|करोड़|करोड)", re.I)
_THOUSAND = re.compile(r"^\s*(?:k\b|thousand|हजार|हज़ार)", re.I)
_PLACE = re.compile(r"[A-Za-z][A-Za-z .'-]{1,58}")

WARN_BOOKING = ("The booking amount is over 10% of the price. Under RERA (section 13) a builder can't take more than 10% "
                "before a registered sale agreement — confirm the terms with the builder.")
WARN_PRELAUNCH = ("Pre-launch offers can't be advertised before MahaRERA registration. We won't use the word 'pre-launch' "
                  "in posts.")


def parse_inr(x: Any) -> Optional[int]:
    """A rupee amount as printed -> int: 299000, "₹2,99,000/-", "₹1 लाख", "2.99 lakh", "१ लाख", "1.2 Cr". None otherwise."""
    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, (int, float)):
        v = float(x)
    else:
        s = str(x).translate(_DEV_DIGITS)
        m = _NUM.search(s)
        if not m:
            return None
        try:
            v = float(m.group(0).replace(",", ""))
        except ValueError:
            return None
        rest = s[m.end():]
        if _CRORE.match(rest):
            v *= 1_00_00_000
        elif _LAKH.match(rest):
            v *= 1_00_000
        elif _THOUSAND.match(rest):
            v *= 1_000
    v = int(round(v))
    return v if 1_000 <= v <= 1_000_000_000 else None


def _num(x: Any) -> Optional[float]:
    if isinstance(x, bool) or x is None:
        return None
    m = _NUM.search(str(x).translate(_DEV_DIGITS))
    try:
        return float(m.group(0).replace(",", "")) if m else None
    except ValueError:
        return None


def _text(x: Any, n: int = 40) -> Optional[str]:
    s = re.sub(r"\s+", " ", str(x or "")).strip().strip('"')
    if not s or len(s) > n or BANNED.search(s):
        return None
    return s


def _bool(x: Any) -> Optional[bool]:
    if isinstance(x, bool):
        return x
    if str(x).strip().lower() in ("true", "yes", "1"):
        return True
    if str(x).strip().lower() in ("false", "no", "0"):
        return False
    return None


def clean_facts(raw: Any) -> Dict[str, Any]:
    """The reader's "facts" object, checked: only valid, parsed values (missing keys mean "not printed")."""
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Any] = {}
    price = parse_inr(raw.get("starting_price_inr"))
    if price and 10_000 <= price <= 500_000_000:
        out["starting_price_inr"] = price
    booking = parse_inr(raw.get("booking_amount_inr"))
    if booking and (not price or booking < price):
        out["booking_amount_inr"] = booking
    for k, n in (("offer_label", 60), ("water", 40), ("power", 40)):
        t = _text(raw.get(k), n)
        if t:
            out[k] = t
    roads = []
    for r in raw.get("road_widths_ft") or [] if isinstance(raw.get("road_widths_ft"), list) else []:
        v = _num(r)
        if v and 5 <= v <= 200 and int(v) not in roads:
            roads.append(int(v))
    if roads:
        out["road_widths_ft"] = roads[:6]
    vastu = _bool(raw.get("vastu"))
    if vastu is not None:
        out["vastu"] = vastu
    acres = _num(raw.get("total_acres"))
    if acres and 0.1 <= acres <= 5000:
        out["total_acres"] = round(acres, 2)
    for k in ("village", "taluka"):
        t = str(raw.get(k) or "").strip()
        if _PLACE.fullmatch(t) and not BANNED.search(t):
            out[k] = t.title() if t.islower() else t
    return out


def merge(into: Dict[str, Any], new: Dict[str, Any], trusted: bool, trusted_keys: set) -> None:
    """Merge one page's checked facts: the first trusted reader's value wins; an untrusted value only fills a gap (and is
    replaced by a trusted one later). `trusted_keys` tracks which keys a trusted reader set."""
    for k, v in new.items():
        if k in trusted_keys:
            continue
        if trusted:
            into[k] = v
            trusted_keys.add(k)
        elif k not in into:
            into[k] = v


# ---- selling points -----------------------------------------------------------------------------------------------------
def lakh(n: int) -> str:
    """299000 -> '₹2.99 lakh', 100000 -> '₹1 lakh', 50000 -> '₹50,000' (the campaign's price_label)."""
    from app.modules.creative.listing_brief import price_label
    return price_label(int(n))


def _local_money(s: str, lang: str) -> str:
    words = {"mr": {"lakh": "लाख", "crore": "कोटी"}, "hi": {"lakh": "लाख", "crore": "करोड़"}}[lang]
    return re.sub(r"\b(lakh|crore)\b", lambda m: words[m.group(1)], s)


def _from_mr(lab: str) -> str:
    """'₹2.99 lakh' -> '₹2.99 लाखांपासून' (Marathi 'from', in the oblique form)."""
    m = _local_money(lab, "mr")
    if m.endswith("लाख"):
        return m + "ांपासून"
    if m.endswith("कोटी"):
        return m + "ंपासून"
    return m + " पासून"


def _and(xs: List[str], word: str) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + f" {word} " + xs[-1]


_HOURS = re.compile(r"24\s*(?:x\s*7|hours?|hrs?|h\b|तास|घंटे)", re.I)
KIND = {"plot": ("Plots", "प्लॉट", "प्लॉट"), "apartment": ("Flats", "फ्लॅट", "फ्लैट"), "house": ("Homes", "घरे", "घर"),
        "villa": ("Villas", "व्हिला", "विला")}
UNKNOWN_KIND = ("Units", "युनिट", "यूनिट")   # the type not known yet: never "Plots" by default (a flat project once read as plots)


def selling_points(facts: Dict[str, Any], language: str = "en", property_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """[{key, text, text_local?, value, source: "brochure"}] from checked facts. `language`: the brochure's ("mr"/"hi" adds
    text_local). The offer's label is kept as printed (the agent sees it); the posts never print it (campaign.offer)."""
    lang = language if language in ("mr", "hi") else ""
    en_kind, mr_kind, hi_kind = KIND.get(property_type or "", UNKNOWN_KIND)
    out: List[Dict[str, Any]] = []

    def add(key: str, value: Any, text: str, mr: str = "", hi: str = "") -> None:
        p = {"key": key, "text": text, "value": value, "source": "brochure"}
        local = {"mr": mr, "hi": hi}.get(lang) if lang else ""
        if local:
            p["text_local"] = local
        out.append(p)

    price = facts.get("starting_price_inr")
    if price:
        lab = lakh(price)
        add("starting_price", price, f"{en_kind} from {lab}", f"{_from_mr(lab)} {mr_kind}",
            f"{_local_money(lab, 'hi')} से {hi_kind}")
    booking = facts.get("booking_amount_inr")
    if booking:
        lab = lakh(booking)
        add("booking_amount", booking, f"Book with {lab}", f"{_local_money(lab, 'mr')} भरून बुकिंग",
            f"{_local_money(lab, 'hi')} में बुकिंग")
    if facts.get("offer_label"):
        lab = facts["offer_label"]
        add("offer", lab, f"Offer: {lab}", f"ऑफर: {lab}", f"ऑफ़र: {lab}")
    for key, en, mr, hi in (("water", "water", "पाणीपुरवठा", "पानी"), ("power", "power supply", "वीजपुरवठा", "बिजली")):
        v = facts.get(key)
        if not v:
            continue
        if _HOURS.search(v):
            add(key, v, f"24-hour {en}", f"24 तास {mr}", f"24 घंटे {hi}")
        else:
            add(key, v, f"{en.capitalize()}: {v}", f"{mr}: {v}", f"{hi}: {v}")
    roads = facts.get("road_widths_ft")
    if roads:
        xs = [str(r) for r in roads]
        add("roads", list(roads), f"Roads {_and(xs, 'and')} ft wide", f"{_and(xs, 'व')} फूट रस्ते", f"{_and(xs, 'और')} फुट सड़कें")
    if facts.get("vastu") is True:
        add("vastu", True, f"Vastu-compliant {en_kind.lower()}", f"वास्तुशास्त्रानुसार {mr_kind}", f"वास्तु के अनुसार {hi_kind}")
    acres = facts.get("total_acres")
    if acres:
        add("land_area", acres, f"{acres:g} acres of land", f"{acres:g} एकर जमीन", f"{acres:g} एकड़ ज़मीन")
    return out[:MAX_POINTS]


def warnings(facts: Dict[str, Any], price_inr: Optional[int] = None) -> List[str]:
    """Compliance notes for the agent: a booking amount over 10% of the price (RERA s.13), a pre-launch offer."""
    out = []
    price = facts.get("starting_price_inr") or price_inr
    booking = facts.get("booking_amount_inr")
    if price and booking and booking > 0.10 * price:
        out.append(WARN_BOOKING)
    if PRELAUNCH.search(str(facts.get("offer_label") or "")):
        out.append(WARN_PRELAUNCH)
    return out


def confirmed(listing: dict) -> Dict[str, Any]:
    """{key: value} of the listing's confirmed (and not dismissed) selling points."""
    out: Dict[str, Any] = {}
    for p in listing.get("selling_points") or []:
        if isinstance(p, dict) and p.get("confirmed") and not p.get("dismissed") and p.get("key") in POINT_KEYS \
                and p.get("value") not in (None, "", [], False):
            out.setdefault(p["key"], p["value"])
    return out


def pending(listing: dict) -> List[Dict[str, Any]]:
    """Points read from the brochure that the agent has neither confirmed nor dismissed."""
    return [p for p in listing.get("selling_points") or []
            if isinstance(p, dict) and not p.get("confirmed") and not p.get("dismissed")]
