"""Prices on their own turn, area by area (owner 2026-10-21: "read prices, but start with Upper Kharadi, Kharadi, Wagholi").

The page rewrite (areastats.enrich) reads prices too, but one project every 30 minutes and every REFRESH_DAYS (60), while a price
is shown only KEEP_DAYS (45) after it was read: most projects had no price, and a read price lapsed before its refresh. The size
pages (/projects/area/<place>/2-bhk) and "Flat prices in <place>" need 3 priced projects per size, so this round reads prices
only, inside the enrich loop, one project every EVERY (PRICES_EVERY_MINUTES), in this order:
  0. projects with 90% or more of their homes booked (pages.nearly_sold) after all the others;
  1. FIRST places (Upper Kharadi, Kharadi, Wagholi), then our other areas outward from Kharadi (NEAR_KHARADI), then every other
     place;
  2. within a place, new launches (registered in the last year) and hot projects first; then never read before, then the
     oldest read; a project whose read found nothing waits EMPTY_DAYS, one read again every REFRESH_DAYS (before its price
     lapses at KEEP_DAYS);
  3. projects people look at first (hot, then Search Console impressions), then the newest.
Only projects still being sold (filed completion date not passed, not sold out; owner 2026-10-21: completed projects are not
worked on) and only a group's primary record (towers are priced once). The pages read are the project's stored Google results;
a project with none costs one Serper search, at most SEARCHES_PER_DAY a day (PRICES_SEARCHES_PER_DAY). It waits while most free
model tiers are resting (enrich.busy), like a rewrite.
On the record: `prices` (areastats.prices), `prices_tried_at`, `prices_checked`. The round's mark `prices_round` keeps the day's
searches and per-place coverage for the owner (Studio → Insights → Pages).
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.core.areas import AREAS
from app.modules.newsroom.store import Store

from . import budget, hot, pages, prices, websearch

log = logging.getLogger(__name__)

FIRST = ("upper_kharadi", "kharadi", "wagholi")
# our areas nearest Kharadi first (owner 2026-10-21), by rough road distance from Kharadi: Keshav Nagar ~5 km over the Mundhwa
# bridge, Lohegaon ~8 km; then the west side, ~20-30 km. Any area added to app.core.areas later goes after these.
EAST = FIRST + ("keshav_nagar", "lohegaon")   # east Pune: our main target for now (owner 2026-10-26)
NEAR_KHARADI = EAST + ("baner", "wakad", "hinjawadi")
ORDER = tuple(k for k in NEAR_KHARADI if k in {a.key for a in AREAS}) + tuple(a.key for a in AREAS if a.key not in NEAR_KHARADI)
# read once more, before their turn, so they have the single-site readings (`prices.seen`) the price idea needs (owner
# 2026-10-31: "lets do upper kharadi and wagholi projects now"); other places get them at their next read
IDEA_FIRST = ("upper_kharadi", "wagholi")
AI_FROM = "2027-01-01"                # prices are read by a model: as enrich.AI_FROM (enrich imports this module)
EVERY_MINUTES = 15                    # ~96 projects a day, up to 4 model calls each (only pages with price lines are sent)
REFRESH_DAYS = 30                     # read again well before prices.KEEP_DAYS
RETRY_DAYS = 1
EMPTY_DAYS = 14                       # a read that found no price (no results, no price lines) is tried again after this
SEARCHES_PER_DAY = 10
ROUND_SECONDS = 240
MARK = "prices_round"


def every() -> timedelta:
    return timedelta(minutes=max(5, int(os.environ.get("PRICES_EVERY_MINUTES") or EVERY_MINUTES)))


def searches_per_day() -> int:
    return max(0, int(os.environ.get("PRICES_SEARCHES_PER_DAY") or SEARCHES_PER_DAY))


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def place_of(d: dict) -> Optional[str]:
    return d.get("pune_place") or d.get("locality")


def area_rank(d: dict) -> int:
    """0 for Upper Kharadi, then outward from Kharadi through our areas (ORDER); every other place after them."""
    place = place_of(d)
    if place not in ORDER and d.get("locality") in ORDER:
        place = d["locality"]   # a place inside one of our areas (Kesnand in Wagholi) counts as that area
    return ORDER.index(place) if place in ORDER else len(ORDER)


def on_top(d: dict, now: datetime) -> bool:
    """On an east Pune "top" list (seo.facets ranks pages.buyable projects): the pages a buyer opens from the home page and the
    area pages, so their pictures, prices and text come first, like a hot project's (owner 2026-10-26: "we should have projects
    totally enriched"). A ready project with homes left counts too: it is on the list."""
    return area_rank(d) < len(EAST) and pages.indexable(d) and pages.buyable(d, now.date())


def new_or_hot(d: dict, now: datetime) -> bool:
    """Registered with MahaRERA in the last year (a new launch) or hot (selling, searched for, in the news): people want these."""
    return bool(hot.launch(d, now)) or int(d.get("hot_score") or 0) >= hot.HOT_MIN


def selling(d: dict, now: datetime) -> bool:
    """A primary record of a project still being sold: priced once per group, never when sold out, nor when completed unless it is
    on a top list (homes left to buy)."""
    return (bool(d.get("page_slug")) and not d.get("cluster_primary") and pages.indexable(d) and pages.homes(d)
            and str(d.get("completion_now") or "9999") >= AI_FROM
            and (not pages.completion_passed(d, now.date()) or on_top(d, now)) and not pages.sold_out(d))


def tier_of(d: dict, now: Optional[datetime] = None) -> str:
    """How much a project's model reading may spend (areastats.budget.route): premium when people look at it (hot, shown by
    Google, on an east Pune top list) or it is in the FIRST areas, where a price matters most; plain otherwise."""
    if (int(d.get("hot_score") or 0) >= hot.HOT_MIN or int(d.get("gsc_impressions") or 0) > 0 or area_rank(d) < len(FIRST)
            or on_top(d, now or datetime.now(timezone.utc))):
        return budget.PREMIUM
    return budget.PLAIN


def unanswered(d: dict) -> bool:
    """The last read failed for a service (no model key, a crash), not for the project: tried again after RETRY_DAYS."""
    why = str(d.get("prices_checked") or "")
    return why == "no LLM key" or why.startswith("failed")


def no_seen(d: dict) -> bool:
    """Pages were read for prices before `seen` was kept, in an IDEA_FIRST place, and no read has been tried since that one (a
    read that fails writes no `prices`: the project waits its normal turn then, instead of coming up every round)."""
    p = d.get("prices") or {}
    if place_of(d) not in IDEA_FIRST or not p.get("read") or "seen" in p:
        return False
    tried, read_at = _aware(d.get("prices_tried_at")), _aware(p.get("at"))
    return tried is None or read_at is None or tried <= read_at + timedelta(minutes=1)


def unread_by_family(d: dict) -> bool:
    """No price yet, and its last read looked for the exact registration's name, which most pages do not print (prices,
    2026-11-02): read once more under the whole project's name instead of waiting EMPTY_DAYS. The step records the name it read
    under whatever it finds, so this comes up once."""
    family = pages.family_name(d)
    return (family != pages.names(d)[0] and d.get("prices_read_as") != family and not (d.get("prices") or {}).get("rows"))


def priority(d: dict, now: datetime) -> Optional[tuple]:
    """Sort key (lower first) for a project whose prices are due, or None when they are not."""
    if not selling(d, now):
        return None
    tried = _aware(d.get("prices_tried_at"))
    got = (d.get("prices") or {}).get("rows")
    read_at = _aware((d.get("prices") or {}).get("at"))
    if no_seen(d) or unread_by_family(d):
        tried = read_at = None   # due now, ordered like a project never read
    elif tried is not None:
        wait = timedelta(days=RETRY_DAYS if unanswered(d) else REFRESH_DAYS if got else EMPTY_DAYS)
        if now - tried < wait:
            return None
    elif read_at is not None and now - read_at < timedelta(days=REFRESH_DAYS):
        return None   # read by the page rewrite lately
    never = tried is None and read_at is None
    when = (tried or read_at or now).timestamp()
    return (1 if pages.nearly_sold(d) else 0, 0 if on_top(d, now) else 1, area_rank(d), 0 if new_or_hot(d, now) else 1,
            0 if never else 1,
            when if not never else 0, -int(d.get("hot_score") or 0), -int(d.get("gsc_impressions") or 0), -pages.recency(d))


def next_project(docs: List[dict], now: datetime) -> Optional[dict]:
    ranked = [(k, d) for d in docs if (k := priority(d, now)) is not None]
    ranked.sort(key=lambda x: x[0])
    return ranked[0][1] if ranked else None


def coverage(docs: List[dict], now: datetime) -> List[dict]:
    """Per place in ORDER: projects being sold, how many have a price shown now, how many were read and found none."""
    out = []
    for key in ORDER:
        mine = [d for d in docs if place_of(d) == key and selling(d, now)]
        priced = sum(1 for d in mine if prices.public(d.get("prices"), now))
        empty = sum(1 for d in mine if d.get("prices_tried_at") and not prices.public(d.get("prices"), now))
        out.append({"place": key, "selling": len(mine), "priced": priced, "none_found": empty, "waiting": len(mine) - priced - empty})
    return out


async def step(store: Store, llm, now: datetime, last: Optional[datetime], busy: bool = False,
               fetch=None, search: Optional[websearch.Search] = None) -> Optional[dict]:
    """One project's prices when EVERY has passed since the last round; None when not due, nothing is due or the models rest."""
    if last is not None and now - _aware(last) < every():
        return None
    if busy or llm is None:   # no model: prices wait (nothing is recorded as tried)
        return None
    docs = await store.all_projects()
    doc = next_project(docs, now)
    if doc is None:
        return None
    if hasattr(llm, "ask"):   # the enrichment's budget (areastats.budget): Gemini for the premium projects' prices
        tier = tier_of(doc)
        if not any(llm.allowed(p, tier) for p in budget.route(tier, "prices")):
            return None
        llm = llm.ask(tier, "prices")
    put_off = int(getattr(llm, "deferred", 0) or 0)
    mark = await store.get_mark(MARK)
    day = now.date().isoformat()
    used = int(mark.get("searches") or 0) if mark.get("day") == day else 0
    base = search if search is not None else websearch.provider()
    counted = {"n": 0}

    async def budgeted(q: str):
        counted["n"] += 1
        return await base(q)
    can_search = base is not None and used < searches_per_day()
    regno = doc.get("regno") or doc["_id"]
    try:
        st, fields = await asyncio.wait_for(prices.gather(store, doc, llm, now, fetch=fetch, search=budgeted if can_search else None,
                                                          allow_search=can_search), ROUND_SECONDS)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.exception("prices: round failed for %s", regno)
        st, fields = {"ok": False, "at": now, "checked": f"failed ({type(e).__name__})"}, {}
    if int(getattr(llm, "deferred", 0) or 0) > put_off:   # the day's budget ran out half way: read again when it has room
        log.info("prices: %s put off, the model budget for today is spent", regno)
        return None
    await store.set_project(doc["_id"], **fields, prices_tried_at=now, prices_checked=st.get("checked"), prices_read_as=pages.family_name(doc))
    docs = [({**d, **fields, "prices_tried_at": now} if d["_id"] == doc["_id"] else d) for d in docs]
    await store.set_mark(MARK, at=now, day=day, searches=used + counted["n"], last={"regno": regno, "place": place_of(doc),
                         "ok": bool(st.get("ok")), "checked": st.get("checked")}, coverage=coverage(docs, now))
    log.info("prices: %s (%s) %s", regno, place_of(doc), st.get("checked"))
    return {"regno": regno, "place": place_of(doc), "ok": bool(st.get("ok")), "checked": st.get("checked")}
