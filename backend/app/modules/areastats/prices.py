"""Prices a project's pages show, read from the web (owner 2026-10-20: "enrichment by our agent/crawler"; Upper Kharadi first).

One more step of the project-page enrichment (areastats.enrich), after the web facts and the profile, on the same pages (each
fetched once per round): the builder's own site first, then the property sites that rank for the project. Unlike the profile
it is read for finished projects too (their last homes are still sold).

For one project (a tower group is read once, on its primary record):
1. only the lines of a page with a price on them (Rs / lakh / crore) go to the model (the critical one: Gemini first); a page
   with none costs no call.
2. the model returns [{size, from_inr, to_inr, from_quote, to_quote}]: what that page asks for THIS project, per home size
   ('3 BHK Luxe' is a 3 BHK). Kept only when each quote is a line of the page, the low price is an amount CODE reads from
   from_quote and the high one from to_quote ("1.25 Cr" -> 12500000): the model never supplies a number. A size row's lines
   must name that size and no line may name several ("30 L - 49 L Dec 2019 1, 1.5, 2 BHK" is a list of other projects), and a
   size priced under PLAUSIBLE of the page's own overall price is dropped (another project's line).
3. published per size when the builder's site states it; or two sites give prices within AGREE of each other (the lower one);
   or one site gives it and another site's price for the project takes it in (its overall range, within AGREE). Both sites
   are the sources. Never a price from the model's own knowledge.
Stored on the register record as `prices` = {at, rows: [{bhk, from_inr, to_inr, official, sources: [{site, url, official,
quote}]}], read: [{site, url, ok, why}]}. A round that finds nothing keeps the last rows while they are under KEEP_DAYS old:
prices change, an old one goes. `public` is what the pages show; `price_from` the lowest, for the area lists.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from . import pages, webfacts, websearch

log = logging.getLogger(__name__)

MAX_PAGES = 4
PAGE_CHARS = 4000                     # price lines are short: what one model call reads
AGREE = 0.15                          # two sites' prices within 15% of each other agree
PLAUSIBLE = 0.7                       # a size priced under 70% of the page's own overall price is another project's
KEEP_DAYS = 45
MIN_INR, MAX_INR = 1_000_000, 500_000_000   # 10 lakh .. 50 crore: outside is a misread (a booking amount, a per-sq.ft rate)
SIZES = ("1 RK", "1 BHK", "1.5 BHK", "2 BHK", "2.5 BHK", "3 BHK", "3.5 BHK", "4 BHK", "4.5 BHK", "5 BHK", "Plot", "All homes")

AMOUNT = re.compile(r"(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)\s*(crores?|cr\.?|lakhs?|lacs?|lac|l\b|l\*)?", re.I)
PRICE_LINE = re.compile(r"(?:₹|\brs\.?\s*\d|\binr\s*\d|\d\s*(?:crores?|cr\b|lakhs?|lacs?|l\b|l\*))", re.I)
PER_UNIT = re.compile(r"/\s*sq|per\s*sq|psf|/\s*month|per\s*month", re.I)
NOT_PRICE = re.compile(r"\b(emi|booking|token|down\s*payment|rent(?:al)?|offer|discount|cashback|stamp\s*duty|gst)\b", re.I)
SIZE_IN = re.compile(r"((?:\d(?:\.5)?\s*(?:,|/|&|and|or)\s*)*\d(?:\.5)?)\s*(bhk|rk)\b", re.I)

SYSTEM = ("You read the lines of one web page that mention prices, for a housing project in Pune. Give the prices asked for "
          "THAT project only, one row per home size: size (one of " + ", ".join(SIZES) + "; a variant such as '3 BHK Luxe' is "
          "its size, '3 BHK'; 'All homes' for the project's overall price), the lowest price from_inr and the highest to_inr "
          "(null when the page gives only one), both in rupees, and for each the exact line of the page it is on, copied word "
          "for word: from_quote and to_quote (the same line when both are on it). Pages also list OTHER or similar projects, "
          "often one line each with a price, a possession date and several sizes ('30 L - 49 L Dec 2019 1, 1.5, 2 BHK'): "
          "leave those out. Leave out per-sq.ft rates, booking amounts, down payments, EMIs, rents and offers. Leave the list "
          'empty when the page gives no price for the project. Answer as JSON: {"prices": [{"size": "2 BHK", '
          '"from_inr": 9600000, "to_inr": 10200000, "from_quote": "...", "to_quote": "..."}]}')


def amounts(quote: str) -> List[int]:
    """The rupee amounts code reads from a sentence: "₹ 1.25 Cr - 1.6 Cr" -> [12500000, 16000000]; per-sq.ft rates are not."""
    out = []
    for m in AMOUNT.finditer(quote or ""):
        raw, unit = m.group(1).replace(",", ""), (m.group(2) or "").lower()
        tail = quote[m.end():m.end() + 12]
        if PER_UNIT.match(tail.strip()) or re.match(r"\s*(?:/\s*sq|sq\.?\s*ft|sqft)", tail, re.I):
            continue
        try:
            n = float(raw)
        except ValueError:
            continue
        if unit.startswith("cr"):
            n *= 10_000_000
        elif unit.startswith("l"):
            n *= 100_000
        elif "," not in m.group(1) and not m.group(0).strip()[:1] in ("₹", "r", "R", "i", "I"):
            continue   # a bare number with no unit and no rupee sign is a size or a count, not a price
        if MIN_INR <= n <= MAX_INR:
            out.append(int(round(n)))
    return out


def _close(a: Optional[int], b: Optional[int]) -> bool:
    return a is not None and b is not None and abs(a - b) <= 0.005 * max(a, b)


def price_lines(text: str, limit: int = PAGE_CHARS) -> str:
    out, size = [], 0
    for ln in text.split("\n"):
        if len(ln) < 6 or len(ln) > 400 or not PRICE_LINE.search(ln):
            continue
        if size + len(ln) > limit:
            break
        out.append(ln)
        size += len(ln) + 1
    return "\n".join(out)


def size_of(v: Any) -> Optional[str]:
    """'2BHK', '3 BHK Luxe' -> '2 BHK', '3 BHK'; 'All homes', 'Plot', '1 RK'; None for anything else."""
    s = " ".join(str(v or "").split()).lower()
    for want in ("All homes", "Plot"):
        if s == want.lower():
            return want
    m = re.match(r"(\d(?:\.5)?)\s*(bhk|rk)\b", s)
    got = f"{m.group(1)} {m.group(2).upper()}" if m else None
    return got if got in SIZES else None


def sizes_named(quote: str) -> List[set]:
    """The sizes each size mention of a line names: '2BHK' -> [{'2 BHK'}], '1, 1.5, 2 BHK' -> [{'1 BHK', '1.5 BHK', '2 BHK'}]."""
    return [{f"{n} {m.group(2).upper()}" for n in re.findall(r"\d(?:\.5)?", m.group(1))} for m in SIZE_IN.finditer(quote or "")]


def _amount_in(want: Any, quote: str) -> Optional[int]:
    n = webfacts.number(want)
    return next((a for a in amounts(quote) if n is not None and _close(a, int(n))), None)


def row_ok(row: dict, page: str) -> Optional[dict]:
    """The row with code-read amounts, or None. Each quote is on the page; the low price is one code reads from from_quote,
    the high one from to_quote; a size row's lines name that size and no line names several (a list of other projects)."""
    size = size_of(row.get("size"))
    lo_q = " ".join(str(row.get("from_quote") or row.get("quote") or "").split())
    hi_q = " ".join(str(row.get("to_quote") or "").split()) or lo_q
    quotes = list(dict.fromkeys([lo_q, hi_q]))
    if size is None or any(NOT_PRICE.search(q) or not webfacts.on_page(q, page) for q in quotes):
        return None
    if size != "All homes":
        named = [m for q in quotes for m in sizes_named(q)]
        if not named or any(len(m) > 1 or size not in m for m in named):
            return None
    lo = _amount_in(row.get("from_inr"), lo_q)
    if lo is None:
        return None
    hi = _amount_in(row.get("to_inr"), hi_q) if row.get("to_inr") else None
    return {"bhk": size, "from_inr": lo, "to_inr": hi if hi and hi > lo else None, "quote": " / ".join(quotes)[:300]}


def plausible(readings: List[dict]) -> List[dict]:
    """One page's rows without the sizes priced far under the page's own overall price (another project's line)."""
    overall = [r["from_inr"] for r in readings if r["bhk"] == "All homes"]
    if not overall:
        return readings
    floor = PLAUSIBLE * min(overall)
    return [r for r in readings if r["bhk"] == "All homes" or r["from_inr"] >= floor]


async def read_prices(llm, src: dict, name: str, text: str) -> tuple:
    """(readings, why): [{bhk, from_inr, to_inr, quote, site, url, official}] that passed the checks."""
    part = price_lines(text)
    if not part:
        return [], "no prices on the page"
    try:
        out = await llm.json(SYSTEM, f"Project: {name}\nPage: {src['url']}\n\n{part}")
    except Exception as e:
        log.exception("prices: model call failed for %s", src["url"])
        return [], f"model call failed ({type(e).__name__})"
    readings, refused = [], 0
    for r in (out or {}).get("prices") or []:
        got = row_ok(r if isinstance(r, dict) else {}, text)
        if got is None:
            refused += 1
            continue
        readings.append({**got, "site": src["site"], "url": src["url"], "official": src["official"]})
    kept = plausible(readings)
    refused += len(readings) - len(kept)
    return kept, f"{len(kept)} prices" + (f", {refused} refused" if refused else "")


def _covers(other: dict, r: dict) -> bool:
    """Another site's price range for the project takes in this size's price (within AGREE)."""
    top = other.get("to_inr") or other["from_inr"]
    return other["from_inr"] * (1 - AGREE) <= r["from_inr"] <= top * (1 + AGREE)


def agree(readings: List[dict]) -> List[dict]:
    """One row per size: the builder's site's; else the lower of two sites within AGREE of each other; else one site's,
    when another site's price for the project (its overall range or any size) takes it in."""
    out = []
    for size in SIZES:
        rs = [r for r in readings if r["bhk"] == size]
        own = [r for r in rs if r["official"]]
        pick = backing = None
        if own:
            pick, backing = own[0], [own[0]]
        for i, a in enumerate(rs if pick is None else []):
            b = next((b for b in rs[i + 1:] if b["site"] != a["site"]
                      and abs(a["from_inr"] - b["from_inr"]) <= AGREE * max(a["from_inr"], b["from_inr"])), None)
            if b:
                pick = a if a["from_inr"] <= b["from_inr"] else b
                backing = [pick, b if pick is a else a]
                break
        for a in rs if pick is None else []:
            b = next((b for b in readings if b["site"] != a["site"] and _covers(b, a)), None)
            if b:
                pick, backing = a, [a, b]
                break
        if pick is None:
            continue
        out.append({"bhk": size, "from_inr": pick["from_inr"], "to_inr": pick.get("to_inr"), "official": bool(own),
                    "sources": [{"site": r["site"], "url": r["url"], "official": r["official"], "quote": r["quote"]} for r in backing]})
    # 'All homes' only when no size has a price of its own
    sized = [r for r in out if r["bhk"] != "All homes"]
    return sized or out


def _model(llm):
    """The critical model (Gemini first, then every provider) for prices: a price is the fact a buyer acts on."""
    try:
        from app.platform.llm import critical_llm
        return critical_llm() or llm
    except Exception:
        return llm


async def gather(store, doc: dict, llm, now: datetime, fetch: Optional[webfacts.Fetch] = None,
                 search: Optional[websearch.Search] = None, allow_search: bool = True) -> tuple:
    """(step, register fields) for areastats.enrich and areastats.pricing. allow_search=False: only stored Google results are
    used (the pricing round's daily search budget is spent)."""
    if doc.get("cluster_primary"):
        return {"ok": True, "at": now, "checked": "read on the group's primary record"}, {}
    if llm is None:
        return {"ok": False, "at": now, "checked": "no LLM key"}, {}
    llm = _model(llm)
    name = pages.names(doc)[0]
    if search is None and allow_search:
        search = websearch.provider()
    results = await webfacts.results_for(store, doc, name, search if allow_search else None, now)
    sources = webfacts.sources_for(doc, results, name, limit=webfacts.MAX_TRIES)
    if not sources:
        return {"ok": False, "at": now, "checked": "no web results name the project"}, {}
    fetch = fetch or webfacts.fetch_page
    readings, read = [], []
    for src in sources:
        if sum(1 for r in read if r["why"] != "page not read") >= MAX_PAGES:
            break
        raw = await fetch(src["url"])
        if not raw:
            read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": False, "why": "page not read"})
            continue
        text = webfacts.page_text(raw)
        ok, not_ok = webfacts.about_project(doc, name, text, src)
        if not ok:
            read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": False, "why": not_ok})
            continue
        got, why = await read_prices(llm, src, name, text)
        readings += got
        read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": bool(got), "why": why})
    rows = agree(readings)
    old = doc.get("prices") or {}
    if not rows and old.get("rows") and _fresh(old.get("at"), now):
        rows, at = old["rows"], old["at"]   # a site down for a day: keep the last good prices a while
    else:
        at = now
    checked = f"{len(rows)} prices from {sum(1 for r in read if r['ok'])} of {len(read)} sites"
    return {"ok": bool(rows), "at": now, "checked": checked}, {"prices": {"at": at, "name": name, "rows": rows, "read": read}}


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _fresh(at: Any, now: datetime) -> bool:
    return isinstance(at, datetime) and _aware(now) - _aware(at) < timedelta(days=KEEP_DAYS)


def public(prices: Optional[dict], now: Optional[datetime] = None) -> Optional[dict]:
    """What a project page shows: each size's price with its sources (a link only to the builder's own site); None when none."""
    if not prices or not prices.get("rows") or not _fresh(prices.get("at"), now or datetime.now(timezone.utc)):
        return None
    at = prices["at"]
    return {"read_at": at.date().isoformat(),
            "rows": [{"bhk": r["bhk"], "from_inr": r["from_inr"], "to_inr": r.get("to_inr"), "official": r.get("official", False),
                      "sources": [{"site": s["site"], "url": s["url"] if s.get("official") else None} for s in r.get("sources") or []]}
                     for r in prices["rows"]]}


def price_from(doc: dict, now: Optional[datetime] = None) -> Optional[int]:
    """The lowest published price, for the area lists ("from ₹1.25 Cr"); None when there is none."""
    shown = public(doc.get("prices"), now)
    return min(r["from_inr"] for r in shown["rows"]) if shown else None
