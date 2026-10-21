"""Area list pages as facets (docs/plan/area-intent-pages.md section 11): one page per search intent per Pune place, drawn from
the MahaRERA register by code, so a new page costs no code and a new search can never make a second copy of one.

A facet is {place, intent, filters}:
- place:   a Pune place key from the register (`pune_place`, app/core/pune_places.py), e.g. "kharadi";
- intent:  "new-launches" (registered in the last LAUNCH_DAYS), "top" (homes booked lately), "ready-to-move" (filed completion
           date passed in the last READY_DAYS), or "all" (every project still being built);
- filters: {"bhk": 2} (home size: projects with a published price for that size, areastats.prices), {"possession": 2027}
           (filed completion year) and/or {"builder": "<builder slug>"}.
Its URL is `/projects/area/<place slug>/<intent>[/<n>-bhk][/possession-<year>][/by-<builder slug>]`; "all" has no segment of
its own (`/projects/area/kharadi/possession-2027`, `/projects/area/lohegaon/2-bhk`). `key` is the one canonical id; `parse` turns any segment order into it.

`view(db, place_slug, segments)` gives everything a page shows: the ranked rows with one sourced reason each, the answer
paragraph written from the numbers, what changed in the last CHANGES_DAYS, the month the data last changed and page_updated.
Every number comes from MahaRERA's records with the date we read them; no score is ever shown.
"""
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from app.core import pune_places
from app.core.areas import AREAS
from app.modules.areastats import hot, prices
from app.modules.areastats.hubs import _primaries, link_name
from app.modules.areastats.pages import _long, booked, builder_key, cluster_stamps, cluster_updated, completion_passed, indexable, is_old
from app.modules.areastats.service import _count, _day
from app.modules.areastats.text import builder_slug
from app.modules.newsroom.store import Store

INTENTS = ("new-launches", "top", "ready-to-move", "all")
LAUNCH_DAYS = hot.LAUNCH_DAYS        # 365: "new launch" = registered with MahaRERA in the last year
READY_DAYS = 3 * 365                 # filed completion date passed in the last three years
MIN_PROJECTS = 3                     # fewer is a thin page: noindex, not in the sitemap (decision 4)
MIN_PRICED = 2                       # projects with a price before a place page shows that size's price range
MAX_ROWS = 30
CHANGES_DAYS = 31
CHANGES_SHOWN = 8
FIRST_YEAR, LAST_YEAR = 2024, 2035   # possession years a page can be about
BHKS = (1, 2, 3, 4)
SEED_BHKS = (1, 2, 3)                # every place's first size pages ("1/2/3 bhk flats in <place>" are the most searched)                  # home sizes a page can be about ("2 BHK" takes in "2.5 BHK", as the listing pages do)
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

LABEL = {"new-launches": "New launch projects", "top": "Top projects", "ready-to-move": "Ready to move projects",
         "all": "Residential projects"}
# the area keys we market (app/core/areas.py) are Pune place keys too: their seeds come first
FOCUS = tuple(a.key for a in AREAS)


@dataclass(frozen=True)
class Facet:
    place: str                                   # pune place key
    intent: str = "all"
    possession: Optional[int] = None
    builder: Optional[str] = None                # builder slug (areastats.text.builder_slug)
    bhk: Optional[int] = None                    # home size, one of BHKS

    @property
    def key(self) -> str:
        bits = [self.place, self.intent]
        if self.bhk:
            bits.append(f"bhk={self.bhk}")
        if self.possession:
            bits.append(f"possession={self.possession}")
        if self.builder:
            bits.append(f"builder={self.builder}")
        return "|".join(bits)

    @property
    def segments(self) -> List[str]:
        out = [] if self.intent == "all" else [self.intent]
        if self.bhk:
            out.append(f"{self.bhk}-bhk")
        if self.possession:
            out.append(f"possession-{self.possession}")
        if self.builder:
            out.append(f"by-{self.builder}")
        return out

    @property
    def path(self) -> str:
        return "/projects/area/" + "/".join([place_slug(self.place), *self.segments])

    @property
    def kind(self) -> str:
        """The facet's type for learning which types earn (11.6): "new-launches", "all+possession", "top+builder"..."""
        f = [k for k, v in (("bhk", self.bhk), ("possession", self.possession), ("builder", self.builder)) if v]
        return "+".join([self.intent, *f])

    @property
    def is_place_page(self) -> bool:
        """The plain place page (/projects/area/<place>), which exists already and is not a facet page."""
        return self.intent == "all" and not self.possession and not self.builder and not self.bhk

    def parent(self) -> "Facet":
        if self.builder:
            return Facet(self.place, self.intent, self.possession, None, self.bhk)
        if self.possession:
            return Facet(self.place, self.intent, None, None, self.bhk)
        if self.bhk:
            return Facet(self.place, self.intent)
        return Facet(self.place)


def place_slug(key: str) -> str:
    return key.replace("_", "-")


def place_key(slug: str) -> str:
    return (slug or "").strip().lower().replace("-", "_")


def place_name(key: str, docs: Optional[List[dict]] = None) -> str:
    p = pune_places.BY_KEY.get(key)
    if p:
        return p.name
    for d in docs or []:
        if d.get("pune_place") == key and d.get("pune_place_name"):
            return d["pune_place_name"]
    return key.replace("_", " ").title()


_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){0,15}$")


def parse(place: str, segments: List[str]) -> Optional[Facet]:
    """The facet for URL segments in any order; None for a segment we do not know or a repeated one."""
    intent, possession, builder, bhk = "all", None, None, None
    for s in segments:
        s = (s or "").strip().lower()
        if s in INTENTS and s != "all" and intent == "all":
            intent = s
        elif (m := re.fullmatch(r"(\d)-bhk", s)) and bhk is None and int(m.group(1)) in BHKS:
            bhk = int(m.group(1))
        elif (m := re.fullmatch(r"possession-(\d{4})", s)) and possession is None and FIRST_YEAR <= int(m.group(1)) <= LAST_YEAR:
            possession = int(m.group(1))
        elif s.startswith("by-") and builder is None and _SLUG.match(s[3:]):
            builder = s[3:]
        else:
            return None
    return Facet(place_key(place), intent, possession, builder, bhk)


def from_key(key: str) -> Optional[Facet]:
    bits = key.split("|")
    if len(bits) < 2 or bits[1] not in INTENTS:
        return None
    kw: dict = {}
    for b in bits[2:]:
        k, _, v = b.partition("=")
        if k == "possession" and v.isdigit():
            kw["possession"] = int(v)
        elif k == "builder" and v:
            kw["builder"] = v
        elif k == "bhk" and v.isdigit() and int(v) in BHKS:
            kw["bhk"] = int(v)
        else:
            return None
    return Facet(bits[0], bits[1], **kw)


# ---- which projects a facet lists, in which order, and why --------------------------------------------------------------------

def _aware(d) -> Optional[datetime]:
    return hot._when(d)


def _year(day: Optional[str]) -> Optional[int]:
    return int(day[:4]) if day and day[:4].isdigit() else None


def _month(d: Optional[datetime]) -> Optional[str]:
    return f"{_MONTHS[d.month - 1]} {d.year}" if d else None


def _ready(d: dict, now: datetime) -> bool:
    day = _day(d.get("completion_now"))
    return bool(day) and completion_passed(d, now.date()) and day >= (now.date() - timedelta(days=READY_DAYS)).isoformat()


def _share(d: dict) -> Optional[float]:
    total, b = _count(d.get("units_total")), booked(d)
    return b / total if total and b is not None and total > 0 else None


def size_price(d: dict, bhk: int, now: datetime) -> Optional[dict]:
    """The project's published price for homes of that size ("2 BHK" and "2.5 BHK"), lowest first, or None:
    {from_inr, to_inr, official, sites}. Only prices areastats.prices publishes (builder's site, or two sites agreeing)."""
    shown = prices.public(d.get("prices"), now)
    rows = [r for r in (shown or {}).get("rows") or [] if r.get("bhk") in (f"{bhk} BHK", f"{bhk}.5 BHK") and r.get("from_inr")]
    if not rows:
        return None
    lo = min(rows, key=lambda r: r["from_inr"])
    tops = [r.get("to_inr") or r["from_inr"] for r in rows]
    return {"from_inr": lo["from_inr"], "to_inr": max(tops) if max(tops) > lo["from_inr"] else None,
            "official": bool(lo.get("official")), "sites": [s["site"] for s in lo.get("sources") or []]}


def inr(v: int) -> str:
    """₹ in the words buyers use: "₹78 lakh", "₹1.25 crore"."""
    if v >= 10_000_000:
        return f"₹{v / 10_000_000:.2f}".rstrip("0").rstrip(".") + " crore"
    return f"₹{v / 100_000:.1f}".rstrip("0").rstrip(".") + " lakh"


def _price_why(sp: dict, bhk: int) -> str:
    rng = f"{inr(sp['from_inr'])} to {inr(sp['to_inr'])}" if sp.get("to_inr") else f"from {inr(sp['from_inr'])}"
    src = "the builder's site" if sp["official"] else " and ".join(sp["sites"][:2]) or "two property sites"
    return f"{bhk} BHK {rng} ({src})"


def members(f: Facet, docs: List[dict], now: datetime) -> List[Tuple[dict, str]]:
    """[(record, reason)] the facet lists, best first. Only pages search may list (indexable primaries)."""
    pool = [d for d in docs if d.get("pune_place") == f.place and indexable(d)]
    if f.bhk:
        sized = {id(d): sp for d in pool if (sp := size_price(d, f.bhk, now))}
        pool = [d for d in pool if id(d) in sized]
        if f.intent == "all":
            # "2 bhk flats in <place>": every project still being sold with a 2 BHK price, cheapest first
            rows = [((sized[id(d)]["from_inr"],), d, _price_why(sized[id(d)], f.bhk)) for d in pool
                    if not is_old(d, now.date()) and not (f.builder and builder_slug(d.get("promoter")) != f.builder)
                    and not (f.possession and _year(_day(d.get("completion_now"))) != f.possession)]
            rows.sort(key=lambda r: (r[0], link_name(r[1]).lower()))
            return [(d, why) for _, d, why in rows]
        out = members(Facet(f.place, f.intent, f.possession, f.builder), pool, now)
        return [(d, f"{_price_why(sized[id(d)], f.bhk)}; {why}") for d, why in out]
    if f.builder:
        pool = [d for d in pool if builder_slug(d.get("promoter")) == f.builder]
    if f.possession:
        pool = [d for d in pool if _year(_day(d.get("completion_now"))) == f.possession]
    rows: List[Tuple[tuple, dict, str]] = []
    for d in pool:
        if f.intent == "new-launches":
            sig = hot.launch(d, now)
            if sig:
                on = _aware(d.get("registered_on"))
                rows.append(((-(on.timestamp() if on else 0),), d, f"registered with MahaRERA on {_long(on.date().isoformat())}"))
        elif f.intent == "top":
            if is_old(d, now.date()):
                continue
            sig, share = hot.bookings(d, now), _share(d)
            if sig:
                rows.append(((0, -sig["value"], -(share or 0)), d, sig["evidence"]))
            elif share is not None and booked(d):
                rows.append(((1, 0, -share), d, f"{booked(d)} of {_count(d.get('units_total'))} homes booked ({round(100 * share)}%)"))
        elif f.intent == "ready-to-move":
            if _ready(d, now):
                share = _share(d)
                left = f", {_count(d['units_total']) - booked(d)} of {_count(d['units_total'])} homes not booked" \
                    if share is not None and share < 1 else ""
                rows.append(((-(int(_day(d['completion_now']).replace('-', ''))),), d,
                             f"completion filed for {_long(_day(d['completion_now']))}, now passed{left}"))
        else:
            if is_old(d, now.date()):
                continue
            day = _day(d.get("completion_now")) or "9999"
            moved = len(d.get("completion_history") or [])
            rows.append(((day,), d, f"completion filed for {_long(_day(d.get('completion_now')))}"
                         + (f", moved {moved} time{'s' if moved > 1 else ''}" if moved else "")))
    rows.sort(key=lambda r: (r[0], link_name(r[1]).lower()))
    return [(d, why) for _, d, why in rows]


def regnos(f: Facet, docs: List[dict], now: datetime) -> List[str]:
    return [d.get("regno") or d["_id"] for d, _ in members(f, docs, now)[:MAX_ROWS]]


# ---- what changed lately, and the month the data last changed ------------------------------------------------------------------

def changes(rows: List[dict], now: datetime) -> List[dict]:
    """Dated changes among the listed projects in the last CHANGES_DAYS: registrations, completion dates that moved, homes booked.
    [{at, text, slug, source}], newest first."""
    since, out = now - timedelta(days=CHANGES_DAYS), []
    for d in rows:
        name = link_name(d)
        on = _aware(d.get("registered_on"))
        if on and since <= on <= now:
            out.append({"at": on, "text": f"{name} was registered with MahaRERA", "slug": d["page_slug"]})
        for h in d.get("completion_history") or []:
            seen = _aware(h.get("seen_at"))
            if seen and seen >= since and h.get("to"):
                out.append({"at": seen, "slug": d["page_slug"],
                            "text": f"{name}'s filed completion date moved from {_long(_day(h.get('from'))) or 'an earlier date'} "
                                    f"to {_long(_day(h['to']))}"})
        hist = sorted(((t, h["booked"]) for h in d.get("booked_history") or []
                       if (t := _aware(h.get("at"))) and isinstance(h.get("booked"), int)), key=lambda x: x[0])
        before = [b for t, b in hist if t < since]
        inside = [(t, b) for t, b in hist if t >= since]
        if before and inside and inside[-1][1] > before[-1]:
            out.append({"at": inside[-1][0], "slug": d["page_slug"],
                        "text": f"{inside[-1][1] - before[-1]} more homes booked at {name}"})
    out.sort(key=lambda c: c["at"], reverse=True)
    return [{**c, "at": c["at"].date().isoformat(), "source": "MahaRERA"} for c in out[:CHANGES_SHOWN]]


# ---- the page ----------------------------------------------------------------------------------------------------------------

def _row(d: dict, why: str, n: int) -> dict:
    total = _count(d.get("units_total"))
    return {"rank": n, "slug": d["page_slug"], "name": link_name(d), "legal_name": d.get("name", ""),
            "regno": d.get("regno") or d["_id"], "promoter": d.get("promoter") or None,
            "builder_slug": builder_key(d) or None,   # the brand page when there is one (areastats.brands)
            "registered_on": _day(d.get("registered_on")), "completion_now": _day(d.get("completion_now")),
            "completion_at_registration": _day(d.get("completion_at_registration")),
            "units_total": total, "units_booked": booked(d), "reason": why, "source": "MahaRERA"}


def _price_row(row: dict, d: dict, bhk: int, now: datetime) -> dict:
    sp = size_price(d, bhk, now) or {}
    return {**row, "price_from": sp.get("from_inr"), "price_to": sp.get("to_inr"),
            "price_source": ("builder's site" if sp.get("official") else ", ".join(sp.get("sites") or [])) or None,
            "source": "MahaRERA; price from " + ("the builder's site" if sp.get("official") else "property sites")}


def answer(f: Facet, place: str, rows: List[dict], as_of: str) -> str:
    """The 40-60 word answer at the top, written by code from the numbers (featured snippets and AI answers quote it)."""
    n = len(rows)
    who = f" by {rows[0]['promoter']}" if f.builder and rows and rows[0].get("promoter") else ""
    year = f" with completion filed for {f.possession}" if f.possession else ""
    if not rows:
        return f"As of {as_of}, no project in {place}{who}{year} matches this list in MahaRERA's records."
    first = rows[0]
    if f.bhk:
        lows = [r["price_from"] for r in rows if r.get("price_from")]
        span = f" Prices start from {inr(min(lows))} to {inr(max(lows))} across them." if len(lows) > 1 else ""
        if f.intent == "all":
            return (f"As of {as_of}, {n} project{'s' if n > 1 else ''}{who} in {place}{year} being built or recently finished have "
                    f"{f.bhk} BHK flats with a published price. The lowest is {first['name']}: {first['reason']}.{span} Each one's "
                    f"possession date and homes booked are from MahaRERA.")
        base = answer(Facet(f.place, f.intent, f.possession, f.builder), place, rows, as_of)
        return f"{base} All {n} have {f.bhk} BHK flats with a published price.{span}"
    if f.intent == "new-launches":
        dates = sorted(r["completion_now"] for r in rows if r["completion_now"])
        soon = f" The earliest filed completion date among them is {_long(dates[0])}." if dates else ""
        return (f"As of {as_of}, {n} project{'s' if n > 1 else ''}{who} in {place}{year} were registered with MahaRERA in the last "
                f"12 months. The newest is {first['name']} ({_long(first['registered_on'])}).{soon}")
    if f.intent == "top":
        return (f"As of {as_of}, {first['name']} leads {n} projects{who} in {place}{year} on homes booked: {first['reason']}. "
                f"We rank by homes booked in the last 90 days as MahaRERA shows them, then by the share of homes booked.")
    if f.intent == "ready-to-move":
        return (f"As of {as_of}, {n} project{'s' if n > 1 else ''}{who} in {place}{year} have passed the completion date filed with "
                f"MahaRERA in the last three years, the newest {first['name']} ({_long(first['completion_now'])}). Ask the builder for "
                f"the occupancy certificate (OC) before you book.")
    return (f"As of {as_of}, {n} project{'s' if n > 1 else ''}{who} in {place} being built have completion filed with MahaRERA"
            f"{' for ' + str(f.possession) if f.possession else ''}. The earliest is {first['name']} ({_long(first['completion_now'])}).")


def title(f: Facet, place: str, n: int, month: Optional[str], builder_name: Optional[str] = None) -> str:
    """Search title, aiming at 60 characters: "New Launch Projects in Kharadi, Pune (Oct 2026): 7 on MahaRERA"."""
    what = {"new-launches": "New Launch Projects", "top": "Top Projects", "ready-to-move": "Ready to Move Flats",
            "all": "Projects"}[f.intent]
    if f.bhk:
        # "2 bhk flats in lohegaon": the size and "flats" lead, as people search
        what = {"new-launches": f"New Launch {f.bhk} BHK Flats", "top": f"Top Projects with {f.bhk} BHK Flats",
                "ready-to-move": f"Ready to Move {f.bhk} BHK Flats", "all": f"{f.bhk} BHK Flats"}[f.intent]
    if f.possession and f.intent == "all" and not f.bhk:
        what = f"Projects with Possession {f.possession}"
    elif f.possession:
        what += f", Possession {f.possession}"
    if builder_name:
        what = f"{builder_name} {what}"
    when = f" ({month})" if month else ""
    tail = f"{n} Projects, Prices" if f.bhk else f"{n} on MahaRERA"
    for t in (f"{what} in {place}, Pune{when}: {tail}", f"{what} in {place}, Pune: {tail}", f"{what} in {place}, Pune{when}",
              f"{what} in {place}{when}", f"{what} in {place}"):
        if len(t) <= 62:
            return t
    return f"{what} in {place}"


def h1(f: Facet, place: str, builder_name: Optional[str] = None) -> str:
    what = LABEL[f.intent]
    if f.bhk:
        what = {"new-launches": f"New launch {f.bhk} BHK flats", "top": f"Top projects with {f.bhk} BHK flats",
                "ready-to-move": f"Ready to move {f.bhk} BHK flats", "all": f"{f.bhk} BHK flats in new projects"}[f.intent]
    if f.possession and f.intent == "all" and not f.bhk:
        what = f"Projects with possession in {f.possession}"
    elif f.possession:
        what += f" with possession in {f.possession}"
    if builder_name:
        what = f"{builder_name}: {what[0].lower()}{what[1:]}"
    return f"{what} in {place}, Pune"


def facet_view(f: Facet, docs: List[dict], now: datetime, stamps: Optional[dict] = None) -> dict:
    """Everything the page shows for a facet, from records already loaded (`docs`: every register record)."""
    prim = _primaries(docs)
    listed = members(f, prim, now)
    rows_docs = [d for d, _ in listed[:MAX_ROWS]]
    rows = [_row(d, why, i + 1) for i, (d, why) in enumerate(listed[:MAX_ROWS])]
    if f.bhk:
        rows = [_price_row(r, d, f.bhk, now) for r, d in zip(rows, rows_docs)]
    place = place_name(f.place, docs)
    as_of = _long(now.date().isoformat())
    changed = changes(rows_docs, now)
    stamps = stamps if stamps is not None else cluster_stamps(docs)
    updated = [u for u in (cluster_updated(d, docs, stamps) for d in rows_docs) if u]
    # the month in the title is the month the data last changed, never just today's month
    last_change = max((datetime.fromisoformat(c["at"]).replace(tzinfo=timezone.utc) for c in changed), default=None)
    builder_name = next((r["promoter"] for r in rows if r.get("promoter")), None) if f.builder else None
    return {
        "key": f.key, "path": f.path, "place": {"key": f.place, "slug": place_slug(f.place), "name": place},
        "intent": f.intent, "possession": f.possession, "builder": f.builder, "builder_name": builder_name, "bhk": f.bhk,
        "title": title(f, place, len(listed), _month(last_change), builder_name), "h1": h1(f, place, builder_name),
        "answer": answer(f, place, rows, as_of), "rows": rows, "count": len(listed), "changes": changed,
        "month": _month(last_change), "page_updated": max(updated) if updated else None,
        "indexable": len(listed) >= MIN_PROJECTS, "as_of": now.date().isoformat(), "source": "MahaRERA public records",
    }


async def view(db, place: str, segments: List[str], now: Optional[datetime] = None) -> Optional[dict]:
    """The page for URL segments, or {"redirect_to": path} when they are in another order; None for an unknown facet."""
    f = parse(place, segments)
    if f is None or f.is_place_page:
        return None
    if f.segments != [s.strip().lower() for s in segments]:
        return {"redirect_to": f.path}
    now = now or datetime.now(timezone.utc)
    docs = await Store(db).shared_projects()
    if not any(d.get("pune_place") == f.place for d in docs):
        return None
    return facet_view(f, docs, now)


def place_prices(place: str, docs: List[dict], now: datetime) -> dict:
    """The place page's "Flat prices in <place>" table: per home size, how many projects being sold have a published price, the
    lowest and highest starting price, and the cheapest project. {as_of, sizes: [{bhk, projects, low, high, cheapest}]}.
    Prices only as areastats.prices publishes them; MIN_PRICED projects or a size is left out (one project is not a price)."""
    pool = [d for d in _primaries(docs) if d.get("pune_place") == place and indexable(d) and not is_old(d, now.date())]
    sizes = []
    for b in BHKS:
        got = sorted(((sp["from_inr"], link_name(d), d["page_slug"]) for d in pool if (sp := size_price(d, b, now))), key=lambda x: x[:2])
        if len(got) >= MIN_PRICED:
            sizes.append({"bhk": b, "projects": len(got), "low": got[0][0], "high": got[-1][0],
                          "cheapest": {"name": got[0][1], "slug": got[0][2]}, "path": Facet(place, "all", bhk=b).path})
    return {"place": place, "as_of": now.date().isoformat(), "sizes": sizes}


async def prices_view(db, place: str, now: Optional[datetime] = None) -> dict:
    return place_prices(place_key(place), await Store(db).shared_projects(), now or datetime.now(timezone.utc))


def seeds(docs: List[dict]) -> List[Facet]:
    """The first facets for every place with an indexable project: focus areas first, then by how many projects a place has."""
    counts: Dict[str, int] = {}
    for d in docs:
        if d.get("pune_place") and d.get("page_slug") and indexable(d):
            counts[d["pune_place"]] = counts.get(d["pune_place"], 0) + 1
    order = sorted(counts, key=lambda k: (k not in FOCUS, FOCUS.index(k) if k in FOCUS else 0, -counts[k], k))
    return [Facet(k, i) for k in order for i in ("new-launches", "top", "ready-to-move")] + \
        [Facet(k, "all", bhk=b) for k in order for b in SEED_BHKS]
