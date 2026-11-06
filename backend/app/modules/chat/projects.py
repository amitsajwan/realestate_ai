"""Project cards for the chat when none of the agent's own listings fits (owner, 2026-10-20, a real chat: the bot said 'no homes in Kharadi'
while our site has 132 active Kharadi project pages).

Two sources, in this order:
  agent_projects   projects an agent brought with their own price sheet: a size that fits the BHK and budget shows its price
  the register     our MahaRERA project pages in the buyer's area (active, homes still open, not finished long ago): those that fit
                   their size and budget on a published price first, then the owner's banner picks, then the hottest (areastats.hot).
                   Same rule as the home plan: a published price for that size above the budget, or a sheet with only other sizes,
                   leaves the project out. A project with no published price stays, with no price and no claim that it fits.

Never on a card: a MHADA project. The bot stays silent on MHADA (owner, 2026-10-20), and the hottest project in Kharadi on 2026-11-06 was one.

A card has the listing card's shape (chat.service.card) plus kind "project", so the website widget and WhatsApp's card_lines draw it
unchanged; `locality` carries the area and the filed completion month, which the widget shows under the title.
"""
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.core import areas as area_registry
from app.modules.areastats import hot, hubs, pages, prices, spotlight
from app.modules.areastats.areamap import card_pictures
from app.platform.text import money

log = logging.getLogger(__name__)

MAX_CARDS = 3
BUDGET_SLACK = 1.1   # a home up to 10% over the stated top is still worth showing
MHADA = re.compile(r"\bmhada\b", re.I)
PUBLISHED = "the asking price published online"


def _area(req: dict) -> Optional[area_registry.Area]:
    for name in req.get("localities") or []:
        found = area_registry.named_in(name) or ((area_registry.get(name),) if area_registry.get(name) else ())
        if found:
            return found[0]
    return None


def _month(day: Optional[str]) -> Optional[str]:
    if not day:
        return None
    y, m = day[:4], int(day[5:7])
    return f"{pages._MONTHS[m - 1]} {y}"


def _fits(conf: dict, req: dict) -> bool:
    bhk, hi, lo = req.get("bhk"), req.get("budget_max_inr"), req.get("budget_min_inr")
    if bhk and conf.get("bhk") and abs(float(conf["bhk"]) - float(bhk)) > 0.5:
        return False
    price = conf.get("price_inr")
    if hi and isinstance(price, int) and price > hi * BUDGET_SLACK:
        return False
    if lo and isinstance(price, int) and price < lo * 0.7:
        return False
    return True


async def _agent_project_cards(db, area: area_registry.Area, req: dict) -> List[dict]:
    out = []
    for p in await db.get_collection("agent_projects").find({}).to_list(200):
        if not area_registry.named_in(p.get("locality") or "") or area_registry.named_in(p.get("locality") or "")[0].key != area.key:
            continue
        fit = [c for c in p.get("configurations") or [] if _fits(c, req)]
        if not fit or not p.get("rera_no"):
            continue
        page = await pages.page_for(db, p["rera_no"])
        if not page:
            continue
        best = min(fit, key=lambda c: c.get("price_inr") or 10 ** 12)
        price = best.get("price_inr")
        when = _month(f"{p['possession_target']}-01") if (p.get("possession_target") or "")[:7].count("-") == 1 else None
        out.append({"id": f"project-{p['rera_no']}", "kind": "project", "title": (p.get("name") or "Project")[:90],
                    "locality": " · ".join(x for x in (area.name, f"possession {when}" if when else None) if x),
                    "bhk": best.get("bhk"), "carpet_sqft": best.get("carpet_sqft"),
                    "price_text": money(price) if isinstance(price, int) else None, "price_inr": price if isinstance(price, int) else None,
                    "sample": False, "url": page["path"], "image_url": None, "priced": isinstance(price, int)})
    return out


def _has_homes(d: dict) -> bool:
    """False only when MahaRERA's buildings say there are no homes (a shops-only or office project like 96 Arrcade); unknown counts as homes."""
    n = (d.get("building_totals") or {}).get("units_residential")
    return not isinstance(n, int) or n > 0


def _price(d: dict, req: dict, floors: dict, now: datetime) -> Tuple[bool, Optional[int]]:
    """(may it be shown to this buyer, the price to show), from the prices the project page publishes."""
    rows = (prices.homes_only(prices.public(d.get("prices"), now), prices.floor_for(d, floors)) or {}).get("rows") or []
    if not rows:
        return True, None
    bhk, hi = req.get("bhk"), req.get("budget_max_inr")
    if bhk:
        rows = [r for r in rows if r["bhk"] == prices.size_of(f"{float(bhk):g} BHK")]
        if not rows:
            return False, None
    low = min(r["from_inr"] for r in rows)
    return not (hi and low > hi * BUDGET_SLACK), low


def _open(d: dict) -> bool:
    left = pages.open_homes(d)
    return left is None or left >= pages.OPEN_MIN


def _picture(d: dict) -> Optional[str]:
    """Its first picture a card may show, else the builder's logo (areamap.card_pictures: never one copied from another site)."""
    pic = card_pictures(d)
    return next((p["url"] for p in pic["photos"]), None) or (pic.get("logo") or {}).get("url")


async def _register_cards(db, area: area_registry.Area, req: dict, skip: set, now: datetime) -> List[dict]:
    every = await pages.Store(db).shared_projects()   # through areastats: chat may not import newsroom (.importlinter)
    served = {d["_id"] for d in every if pages.can_host(d)}
    docs = [d for d in every if d.get("locality") == area.key and pages.can_host(d) and d.get("cluster_primary") not in served
            and not pages.is_old(d) and _has_homes(d) and _open(d) and (d.get("regno") or d["_id"]) not in skip
            and not any(MHADA.search(n or "") for n in (d.get("name"), pages.names(d)[0]))]
    floors = prices.overall_floors(docs, now)
    # the owner's picks lead only for a buyer who has said nothing: a banner note is no fit for a size or budget
    picked = {it["slug"]: it.get("note") for it in (await spotlight.get_config(db))["items"]} if not (req.get("bhk") or req.get("budget_max_inr")) else {}
    live = await spotlight.picked_slugs(db, now) if picked else set()
    found = []
    for d in docs:
        ok, price = _price(d, req, floors, now)
        if ok:
            found.append((d, price))
    wanted = bool(req.get("bhk") or req.get("budget_max_inr"))
    found.sort(key=lambda x: (bool(wanted and x[1]), x[0].get("page_slug") in live, x[0].get("hot_score") or 0,
                              pages._count(x[0].get("units_total")) or 0), reverse=True)
    out = []
    for d, price in found[:MAX_CARDS]:
        when = _month(pages._day(d.get("completion_now")))
        note = picked.get(d.get("page_slug")) if d.get("page_slug") in live else None
        fact = {"fact": note, "source": "our team"} if note else hubs.fact_line(d, now)
        out.append({"id": f"project-{d.get('regno') or d['_id']}", "kind": "project", "title": pages.names(d)[0][:90],
                    "locality": " · ".join(x for x in (area.name, f"MahaRERA completion {when}" if when else None) if x),
                    "bhk": None, "carpet_sqft": None, "price_text": f"from {money(price)}" if price else None, "price_inr": price,
                    "price_note": PUBLISHED if price else None, "sample": False, "url": f"/projects/{d['page_slug']}", "image_url": _picture(d),
                    "priced": bool(price), "hot": (d.get("hot_score") or 0) >= hot.HOT_MIN or d.get("page_slug") in live, **fact})
    return out


async def project_cards(db, req: dict, now: Optional[datetime] = None) -> List[dict]:
    """Up to three project cards in the buyer's area, priced agent projects that fit first; [] without a known area or on any failure."""
    if req.get("transaction") == "rent":
        return []
    area = _area(req)
    if area is None:
        return []
    try:
        cards = await _agent_project_cards(db, area, req)
        if len(cards) < MAX_CARDS:
            cards += await _register_cards(db, area, req, {c["id"].removeprefix("project-") for c in cards}, now or datetime.now(timezone.utc))
        return cards[:MAX_CARDS]
    except Exception as e:   # cards are a help, never a reason to drop the buyer's message
        log.info("project cards failed: %s", type(e).__name__)
        return []
