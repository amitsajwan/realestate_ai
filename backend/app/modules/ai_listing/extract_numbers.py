"""Deterministic parsers for numbers: transaction, price, area, BHK, floors. Input is normalised text."""
import re
from typing import Optional

_UNIT_MULT = {"cr": 1e7, "lakh": 1e5, "k": 1e3}
_UNIT_RE = r"crores?|crs?|karod|lakhs?|lacs?|lks?|l|k|thousand|hazaa?r|hajar"
MONEY_RE = re.compile(r"(?<![\w.])(?P<n>\d[\d,]*(?:\.\d+)?)\s*(?P<u>" + _UNIT_RE + r")(?![a-z])")
_UNIT_AHEAD = re.compile(r"\s*(?:" + _UNIT_RE + r")(?![a-z])")
RS_RE = re.compile(r"(?:rs\.?|inr|₹|rupees?)\s*(?P<n>\d[\d,]*(?:\.\d+)?)")
PER_MONTH_RE = re.compile(r"(?P<n>\d[\d,]*(?:\.\d+)?)\s*(?:/-)?\s*(?:/|per|a)\s*(?:month|mo|mth)\b")
SLASHDASH_RE = re.compile(r"(?<![\w.])(?P<n>\d[\d,]{3,})\s*/-")
RENT_BARE_RE = re.compile(r"(?:rent|rental)\s*(?:of|is|:|-|=)?\s*(?:rs\.?|₹)?\s*(?P<n>\d[\d,]{3,})")
_EXCLUDE_BEFORE = re.compile(r"(?:deposit|advance|maintenance|brokerage|token|emi|booking|registration|stamp)\W*(?:\w+\W+){0,2}$")
_RATE_AFTER = re.compile(r"^\s*(?:/|per|a|p\.?)\s*(?:sq|sft|psf|sqft|feet|foot)")


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def _unit_kind(u: str) -> str:
    if u.startswith(("cr", "karod")):
        return "cr"
    if u.startswith("l"):
        return "lakh"
    return "k"


def parse_price(t: str) -> Optional[tuple[int, float]]:
    """First plausible price token -> (rupees, confidence)."""
    cands: list[tuple[int, int, float, float]] = []  # start, end, value, conf
    prev = None
    for m in MONEY_RE.finditer(t):
        kind = _unit_kind(m.group("u"))
        val = _num(m.group("n")) * _UNIT_MULT[kind]
        if prev and prev[2] == "cr" and kind == "lakh" and re.fullmatch(r"\s*(?:and|&|\+)?\s*", t[prev[1]:m.start()]):
            c = cands[-1]
            cands[-1] = (c[0], m.end(), c[2] + val, c[3])
            prev = (m.start(), m.end(), "lakh")
            continue
        cands.append((m.start(), m.end(), val, 0.95))
        prev = (m.start(), m.end(), kind)
    for rx, conf in ((RS_RE, 0.9), (PER_MONTH_RE, 0.9), (SLASHDASH_RE, 0.85), (RENT_BARE_RE, 0.85)):
        for m in rx.finditer(t):
            if _UNIT_AHEAD.match(t[m.end():]):
                continue
            if any(s <= m.start("n") < e for s, e, _, _ in cands):
                continue
            cands.append((m.start("n"), m.end("n"), _num(m.group("n")), conf))
    for s, e, val, conf in sorted(cands):
        if _EXCLUDE_BEFORE.search(t[max(0, s - 24):s]) or _RATE_AFTER.match(t[e:e + 14]):
            continue
        if val >= 500:
            return int(round(val)), conf
    return None


_RENT = re.compile(r"(?<![a-z])(?:rent|rental|rented|kiraye|kiraya|kirayen|bhade|bhaade|bhada|lease|to let|tolet)(?![a-z])"
                   r"|per month|/\s*month|/\s*mo\b|a month")
_SALE = re.compile(r"(?<![a-z])(?:sale|sell|selling|resale|bikau|bechna|bechne|bechni|vikri|buy|ownership|for sell)(?![a-z])")


def parse_transaction(t: str, price: Optional[int]) -> Optional[tuple[str, float]]:
    r, s = _RENT.search(t), _SALE.search(t)
    if r and (not s or r.start() < s.start()):
        return "rent", 0.95
    if s:
        return "sale", 0.95
    if price is not None:
        return ("sale", 0.6) if price >= 500000 else ("rent", 0.6)
    return None


_QUAL = (r"(?P<q>rera\s*carpet|carpet|sbua|sba|super\s*built[\s-]*up|super\s*area|built[\s-]*up|bua)")
_AREA_UNIT = (r"(?P<u>sq\.?\s*ft\.?|sqft|sq\.?\s*feet|square\s*fe+t|square\s*foot|sft|sf|sqyd|sq\.?\s*yards?|sq\.?\s*yd\.?|"
              r"sq\.?\s*m(?:et(?:er|re)s?|trs?)?|sqm|guntha|gunthe|acres?|gaj)(?![a-z])")
QUAL_FIRST = re.compile(_QUAL + r"\s*(?:area)?\s*(?:is|of|:|-|=)?\s*(?P<n>\d[\d,]*(?:\.\d+)?)(?!\s*(?:lakh|lac|l\b|cr|k\b|bhk|%|/|th|st|nd|rd))"
                        r"(?:\s*" + _AREA_UNIT + r")?")
NUM_QUAL = re.compile(r"(?<![\w.])(?P<n>\d[\d,]*(?:\.\d+)?)\s*" + _QUAL)
UNIT_FIRST = re.compile(r"(?<![\w.])(?P<n>\d[\d,]*(?:\.\d+)?)\s*" + _AREA_UNIT)
_QUAL_BEFORE = re.compile(_QUAL.replace("(?P<q>", "(?P<q3>") + r"\s*(?:area)?\s*(?:is|of|:|-|=)?\s*$")
_QUAL_AFTER = re.compile(r"^[\s,:(\-]*(?:" + _QUAL.replace("(?P<q>", "(?P<q2>") + r")")


def _factor(unit: str) -> float:
    u = unit.replace(" ", "").replace(".", "")
    if u.startswith(("sqyd", "sqyard", "gaj")):
        return 9.0
    if u.startswith(("sqm", "sqmet", "sqmtr")):
        return 10.7639
    if u.startswith("guntha"):
        return 1089.0
    if u.startswith("acre"):
        return 43560.0
    return 1.0


def _kind(q: str) -> str:
    return "carpet" if "carpet" in q else "sba"


def parse_areas(t: str) -> dict[str, tuple[int, float]]:
    """-> {'carpet': (sqft, conf), 'sba': (sqft, conf)}"""
    items: list[tuple[int, int, float, Optional[str]]] = []  # start, end, sqft, forced kind
    unit_starts = set()
    for m in UNIT_FIRST.finditer(t):
        items.append((m.start(), m.end(), _num(m.group("n")) * _factor(m.group("u")), None))
        unit_starts.add(m.start("n"))
    q_first = [(m.start("n"), m.end("n"), _num(m.group("n")), _kind(m.group("q"))) for m in QUAL_FIRST.finditer(t)
               if m.start("n") not in unit_starts]
    n_first = [(m.start("n"), m.end("n"), _num(m.group("n")), _kind(m.group("q"))) for m in NUM_QUAL.finditer(t)
               if m.start("n") not in unit_starts]
    if q_first and n_first:  # "carpet 950 sba 1300" vs "950 carpet 1300 sba": keep the style that starts first
        qpos = min(QUAL_FIRST.search(t).start(), q_first[0][0])
        (q_first if n_first[0][0] < qpos else n_first).clear()
    items += q_first + n_first
    out: dict[str, tuple[int, float]] = {}
    pos = 0
    for start, end, v, forced in sorted(items):
        if not 50 <= v <= 5_000_000:
            continue
        v = int(round(v))
        kind, conf, pos_next = forced, 0.95, end
        if kind is None:
            qb = _QUAL_BEFORE.search(t[max(pos, start - 26):start])
            qa = _QUAL_AFTER.match(t[end:end + 24])
            if qb:
                kind = _kind(qb.group("q3"))
            elif qa:
                kind, pos_next = _kind(qa.group("q2")), end + qa.end()
        pos = pos_next
        if kind is None:
            kind, conf = ("carpet" if not out else "sba"), 0.6
            if kind in out or (kind == "sba" and "carpet" not in out):
                continue
        out.setdefault(kind, (v, conf))
    return out


_BHK_WORDS = {"one": 1, "ek": 1, "two": 2, "do": 2, "don": 2, "three": 3, "teen": 3, "tin": 3, "four": 4, "char": 4,
              "chaar": 4, "five": 5, "paanch": 5, "panch": 5, "six": 6}
BHK_RE = re.compile(r"(?<![\w.])(?P<n>\d(?:\.\d)?|" + "|".join(_BHK_WORDS) + r")\s*[-.]?\s*(?:b\.?\s?h\.?\s?k|bedrooms?|beds?|br)(?![a-z])")
RK_RE = re.compile(r"(?<![\w.])(?:1|one)\s*rk(?![a-z])|(?<![a-z])studio(?![a-z])")


def parse_bhk(t: str) -> Optional[tuple[float, float]]:
    m = BHK_RE.search(t)
    if m:
        n = m.group("n")
        v = float(_BHK_WORDS.get(n, n) if n in _BHK_WORDS else n)
        if 0.5 <= v <= 10:
            return (int(v) if v == int(v) else v), 0.95
    if RK_RE.search(t):
        return 1, 0.7
    return None


_FLOOR_OF = re.compile(r"(?<![\d/])(\d{1,2})\s*(?:st|nd|rd|th)?\s*floor\s*(?:of|out of|/|in a|in)\s*(\d{1,2})(?!\d)")
_FLOOR_OF2 = re.compile(r"floor\s*(?:no\.?|number)?\s*[:\-]?\s*(\d{1,2})\s*(?:/|of|out of)\s*(\d{1,2})(?!\d)")
_SLASH = re.compile(r"(?<![\d/.])(\d{1,2})\s*/\s*(\d{1,2})(?![\d/]|\s*(?:month|mo\b|sq|bhk|-))")
_TOTAL = re.compile(r"(\d{1,2})\s*(?:floors?|storey|storeys|story|stories|storied)\s*(?:building|tower|society|wing)"
                    r"|(?:building|tower|wing)\s*(?:of|has|with)\s*(\d{1,2})\s*(?:floors?|storey)|(\d{1,2})\s*(?:storey|storeyed)")
_TOP_OF = re.compile(r"top floor\s*(?:of|out of|in a|in)\s*(\d{1,2})(?!\d)")
_GPLUS = re.compile(r"(?<![a-z])g\s*\+\s*(\d{1,2})(?!\d)")
_FLOOR_ORD = re.compile(r"(?<![\d/])(\d{1,2})\s*(?:st|nd|rd|th)\s*floor")
_FLOOR_NUM = re.compile(r"floor\s*(?:no\.?|number)?\s*[:\-]?\s*(\d{1,2})(?![\d/])")


def parse_floors(t: str) -> dict[str, tuple[int, float]]:
    out: dict[str, tuple[int, float]] = {}
    m = _TOP_OF.search(t)
    if m and 2 <= int(m.group(1)) <= 90:
        out["floor"], out["total_floors"] = (int(m.group(1)), 0.9), (int(m.group(1)), 0.9)
    for rx in (_FLOOR_OF, _FLOOR_OF2, _SLASH) if not out else ():
        m = rx.search(t)
        if m and 0 <= int(m.group(1)) <= int(m.group(2)) <= 90 and int(m.group(2)) >= 2:
            conf = 0.95 if rx is not _SLASH else 0.85
            out["floor"], out["total_floors"] = (int(m.group(1)), conf), (int(m.group(2)), conf)
            break
    if "total_floors" not in out:
        m = _TOTAL.search(t)
        if m:
            v = int(next(g for g in m.groups() if g))
            if 2 <= v <= 90:
                out["total_floors"] = (v, 0.9)
        else:
            m = _GPLUS.search(t)
            if m:
                out["total_floors"] = (int(m.group(1)) + 1, 0.85)
    if "floor" not in out:
        m = _FLOOR_ORD.search(t) or _FLOOR_NUM.search(t)
        if m and 0 <= int(m.group(1)) <= 90:
            out["floor"] = (int(m.group(1)), 0.9)
        elif re.search(r"(?<![a-z])ground floor|(?<![a-z])gf(?![a-z])", t):
            out["floor"] = (0, 0.9)
        elif "top floor" in t and "total_floors" in out:
            out["floor"] = (out["total_floors"][0], 0.7)
    if out.get("floor") and out.get("total_floors") and out["floor"][0] > out["total_floors"][0]:
        out.pop("floor")
    return out
