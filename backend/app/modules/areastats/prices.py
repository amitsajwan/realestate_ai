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
   size priced under PLAUSIBLE of the page's own overall price is dropped (another project's line). When the line states the
   home's size in sq ft, the price per sq ft must be inside RATE_PER_SQFT (a misread unit, a whole building's price); `public`
   runs the same check on stored rows, so a price read before it goes from the pages at once.
3. published per size when the builder's site states it; or two sites give prices within AGREE of each other (the lower one);
   or one site gives it and another site's price for the project takes it in (its overall range, within AGREE). Both sites
   are the sources. Never a price from the model's own knowledge.
Sites price a project, not one MahaRERA registration of it, so pages are matched on the whole project's name (pages.family_name:
"Pristine O2 World" for "Pristine O2 World Part 3", whose exact name no page prints: 2026-11-02, 9 of 20 unpriced Upper Kharadi
projects were losing most of their pages that way). The shorter name matches more, so a page must then also name the builder or
the place. Only prices read this way: web facts and pictures keep the exact name (a picture of another phase is a wrong picture).
Stored on the register record as `prices` = {at, rows: [{bhk, from_inr, to_inr, official, sources: [{site, url, official,
quote}]}], read: [{site, url, ok, why}], seen: [{bhk, from_inr, to_inr, site, url, quote}]} (`seen`: every reading that
passed the checks, agreed or not, for the rounded price idea in areastats.priceidea). Each size's price is also kept, dated, in `price_history` ([{at, bhk, from_inr, to_inr,
official, sites}]) when it is new or differs from that size's last reading: `prices` is replaced every round and the sites
show only today's price, so this is the only record of how a project's prices moved (docs/plan/seo-system.md 8b). A round that finds nothing keeps the last rows while they are under KEEP_DAYS old:
prices change, an old one goes. `public` is what the pages show (with `sqft`, the size the lowest price is for, when its
line states it, and `per_sqft`, that price over that size); `price_from` the lowest, for the area lists.
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
PRICE_HISTORY = 400                   # dated price readings kept per project (one per size per change)
MIN_INR, MAX_INR = 1_000_000, 500_000_000   # 10 lakh .. 50 crore: outside is a misread (a booking amount, a per-sq.ft rate)
# a price is checked against the size its own line states (owner 2026-10-24: "correct prices"): a 750 sq ft 2 BHK read at
# ₹9.6 Cr is a misread unit or another project's line. Wide on purpose: sites mix carpet and saleable area, and Pune runs from
# about ₹4,000 a sq ft at the edges to ₹30,000 in the costliest streets.
RATE_PER_SQFT = (2_500, 40_000)
AREA_SQFT = (200, 10_000)             # a home's size; outside is a plot, a township's acreage or a misread
SIZES = ("1 RK", "1 BHK", "1.5 BHK", "2 BHK", "2.5 BHK", "3 BHK", "3.5 BHK", "4 BHK", "4.5 BHK", "5 BHK", "Plot", "All homes")

AMOUNT = re.compile(r"(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)\s*(crores?|cr\.?|lakhs?|lacs?|lac|l\b|l\*)?", re.I)
PRICE_LINE = re.compile(r"(?:₹|\brs\.?\s*\d|\binr\s*\d|\d\s*(?:crores?|cr\b|lakhs?|lacs?|l\b|l\*))", re.I)
PER_UNIT = re.compile(r"/\s*sq|per\s*sq|psf|/\s*month|per\s*month", re.I)
NOT_PRICE = re.compile(r"\b(emi|booking|token|down\s*payment|rent(?:al)?|offer|discount|cashback|stamp\s*duty|gst)\b", re.I)
AREA = re.compile(r"(?<![\d,.])(\d{1,2},\d{3}|\d{3,5})(?:\.\d+)?\s*(?:(?:-|–|to)\s*(\d{1,2},\d{3}|\d{3,5})(?:\.\d+)?\s*)?"
                  r"(?:sq\.?\s*\.?\s*f(?:ee)?t\b\.?|sqft\b|sft\b|square\s*f(?:ee|oo)t\b)", re.I)
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
    got = {"bhk": size, "from_inr": lo, "to_inr": hi if hi and hi > lo else None, "quote": " / ".join(quotes)[:300]}
    return got if rate_ok(got, " / ".join(quotes)) else None


def plausible(readings: List[dict]) -> List[dict]:
    """One page's rows without the sizes priced far under the page's own overall price (another project's line)."""
    overall = [r["from_inr"] for r in readings if r["bhk"] == "All homes"]
    if not overall:
        return readings
    floor = PLAUSIBLE * min(overall)
    return [r for r in readings if r["bhk"] == "All homes" or r["from_inr"] >= floor]


def areas_in(quote: str) -> List[int]:
    """The home sizes in sq ft a line states: '2 BHK 740 - 957 sq.ft ₹72 L' -> [740, 957]. A rate ('₹12,000 per sq ft',
    '₹9,500/sq ft') is not a size, and neither is a number outside AREA_SQFT."""
    out = []
    for m in AREA.finditer(quote or ""):
        if re.search(r"(?:₹|rs\.?|inr)\s*$", quote[max(0, m.start() - 5):m.start()], re.I):
            continue
        out += [int(g.replace(",", "")) for g in m.groups() if g and AREA_SQFT[0] <= int(g.replace(",", "")) <= AREA_SQFT[1]]
    return out


def rate_ok(row: dict, quote: str) -> bool:
    """A price fits the size its own line states: price / sq ft inside RATE_PER_SQFT. The smallest size goes with the lowest
    price and the largest with the highest. A line with no size, and a plot, are not checked (nothing to divide by)."""
    sizes = areas_in(quote)
    if not sizes or row.get("bhk") == "Plot":
        return True
    lo, hi = RATE_PER_SQFT
    pairs = [(row["from_inr"], min(sizes))] + ([(row["to_inr"], max(sizes))] if row.get("to_inr") else [])
    return all(lo <= price / sqft <= hi for price, sqft in pairs)


def sqft_of(row: dict, quote: str) -> Optional[int]:
    """The size its lowest price is for, as the line states it (carpet or saleable: sites differ); None when not stated."""
    sizes = areas_in(quote)
    return min(sizes) if sizes and row.get("bhk") != "Plot" else None


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
    """The critical model (Gemini first, then every provider) for prices: a price is the fact a buyer acts on. The enrichment's
    budgeted client (areastats.budget) already sends prices to Gemini for the projects that matter and meters it: kept."""
    if getattr(llm, "budgeted", False):
        return llm
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
    exact, name = pages.names(doc)[0], pages.family_name(doc)
    if search is None and allow_search:
        search = websearch.provider()
    results = await webfacts.results_for(store, doc, exact, search if allow_search else None, now)
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
        if ok and name != exact and not src["official"] and not _same_builder_or_place(doc, text):
            ok, not_ok = False, "page names another project of that name"
        if not ok:
            read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": False, "why": not_ok})
            continue
        got, why = await read_prices(llm, src, name, text)
        readings += got
        read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": bool(got), "why": why})
    rows = agree(readings)
    old = doc.get("prices") or {}
    seen = [{k: r.get(k) for k in ("bhk", "from_inr", "to_inr", "site", "url", "quote")} for r in readings]
    if not rows and old.get("rows") and _fresh(old.get("at"), now):
        rows, at = old["rows"], old["at"]   # a site down for a day: keep the last good prices a while
        seen = seen or old.get("seen") or []
    else:
        at = now
    checked = f"{len(rows)} prices from {sum(1 for r in read if r['ok'])} of {len(read)} sites"
    fields = {"prices": {"at": at, "name": name, "rows": rows, "read": read, "seen": seen}}
    if at == now:   # read this round, not the last good prices kept while a site is down
        fields.update(history(doc, rows, now))
    return {"ok": bool(rows), "at": now, "checked": checked}, fields


def _same_builder_or_place(doc: dict, text: str) -> bool:
    """A page matched on the whole project's name also names the builder or the place: "Shree Sai Hills" is a name others use."""
    low = (text or "").lower()
    place = str(doc.get("pune_place_name") or doc.get("pune_place") or "").replace("_", " ").lower()
    locality = str(doc.get("locality") or "").replace("_", " ").lower()
    return any(w and re.search(rf"\b{re.escape(w)}\b", low) for w in (*webfacts.builder_words(doc), place, locality))


def history(doc: dict, rows: List[dict], now: datetime) -> dict:
    """{"price_history": [...]} with a dated reading for each size whose price is new or changed since that size's last
    reading; {} when nothing changed. A reading is never removed except past PRICE_HISTORY, oldest first."""
    hist = list(doc.get("price_history") or [])
    last = {h.get("bhk"): h for h in hist if isinstance(h, dict)}
    new = []
    for r in rows:
        before = last.get(r["bhk"])
        if before and (before.get("from_inr"), before.get("to_inr"), before.get("official")) == \
                (r["from_inr"], r.get("to_inr"), r["official"]):
            continue
        new.append({"at": now, "bhk": r["bhk"], "from_inr": r["from_inr"], "to_inr": r.get("to_inr"), "official": r["official"],
                    "sites": [s["site"] for s in r.get("sources") or []]})
    return {"price_history": (hist + new)[-PRICE_HISTORY:]} if new else {}


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _fresh(at: Any, now: datetime) -> bool:
    return isinstance(at, datetime) and _aware(now) - _aware(at) < timedelta(days=KEEP_DAYS)


def public(prices: Optional[dict], now: Optional[datetime] = None) -> Optional[dict]:
    """What a project page shows: each size's price with its sources (a link only to the builder's own site); None when none."""
    if not prices or not prices.get("rows") or not _fresh(prices.get("at"), now or datetime.now(timezone.utc)):
        return None
    at = prices["at"]
    # rows read before the size check are checked here too, on the line they were read from (no re-read needed)
    rows = [(r, _quote(r)) for r in prices["rows"]]
    rows = [(r, q) for r, q in rows if rate_ok(r, q)]
    if not rows:
        return None
    return {"read_at": at.date().isoformat(),
            "rows": [{"bhk": r["bhk"], "from_inr": r["from_inr"], "to_inr": r.get("to_inr"), "official": r.get("official", False),
                      "sqft": sqft, "per_sqft": round(r["from_inr"] / sqft) if sqft else None,
                      "sources": [{"site": s["site"], "url": s["url"] if s.get("official") else None} for s in r.get("sources") or []]}
                     for r, q in rows for sqft in (sqft_of(r, q),)]}


def _quote(row: dict) -> str:
    """The line the shown price was read from: the first source is the one picked (agree)."""
    sources = row.get("sources") or []
    return str(sources[0].get("quote") or "") if sources else ""


def ideas(prices: Optional[dict], now: Optional[datetime] = None) -> List[dict]:
    """[{bhk, from_inr, to_inr}]: the sizes `public` does not show that one site priced (`seen`: every reading that passed the
    checks, kept since 2026-10-31), lowest price to highest over the sites. For areastats.priceidea, which only shows them
    rounded; [] when none or the reading is past KEEP_DAYS."""
    if not prices or not _fresh(prices.get("at"), now or datetime.now(timezone.utc)):
        return []
    shown = {r["bhk"] for r in (public(prices, now) or {}).get("rows") or []}
    per: dict = {}
    for r in prices.get("seen") or []:
        if r.get("bhk") in shown or r.get("bhk") in (None, "All homes", "Plot") or not r.get("from_inr"):
            continue
        if not rate_ok(r, str(r.get("quote") or "")):
            continue
        lo, hi = per.get(r["bhk"], (None, None))
        top = r.get("to_inr") or r["from_inr"]
        per[r["bhk"]] = (min(lo or r["from_inr"], r["from_inr"]), max(hi or top, top))
    return [{"bhk": b, "from_inr": lo, "to_inr": hi if hi > lo else None} for b, (lo, hi) in per.items()]


def starts(prices: Optional[dict], now: Optional[datetime] = None) -> dict:
    """{bhk: starting price} for one project: the published price per size, else one site's (`ideas`). For the area's bands."""
    out = {r["bhk"]: r["from_inr"] for r in ideas(prices, now)}
    out.update({r["bhk"]: r["from_inr"] for r in (public(prices, now) or {}).get("rows") or [] if r["bhk"] not in ("All homes", "Plot")})
    return out


def price_from(doc: dict, now: Optional[datetime] = None) -> Optional[int]:
    """The lowest published price, for the area lists ("from ₹1.25 Cr"); None when there is none."""
    shown = public(doc.get("prices"), now)
    return min(r["from_inr"] for r in shown["rows"]) if shown else None
