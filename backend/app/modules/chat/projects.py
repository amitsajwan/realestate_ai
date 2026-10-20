"""Project cards for the chat when none of the agent's own listings fits (owner, 2026-10-20, a real chat: the bot said 'no homes in Kharadi'
while our site has 132 active Kharadi project pages).

Two sources, in this order:
  agent_projects   projects an agent brought with their own price sheet: a size that fits the BHK and budget shows its price
  the register     our MahaRERA project pages in the buyer's area (active, homes in them, not finished long ago), busiest first;
                   the register has no prices, so these cards carry none and the reply says the agent gives the price

A card has the listing card's shape (chat.service.card) plus kind "project", so the website widget and WhatsApp's card_lines draw it
unchanged; `locality` carries the area and the filed completion month, which the widget shows under the title.
"""
import logging
from typing import List, Optional

from app.core import areas as area_registry
from app.modules.areastats import pages
from app.platform.text import money

log = logging.getLogger(__name__)

MAX_CARDS = 3
BUDGET_SLACK = 1.1   # a home up to 10% over the stated top is still worth showing


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


async def _register_cards(db, area: area_registry.Area, skip: set) -> List[dict]:
    every = await pages.Store(db).all_projects()   # through areastats: chat may not import newsroom (.importlinter)
    served = {d["_id"] for d in every if pages.can_host(d)}
    docs = [d for d in every if d.get("locality") == area.key and pages.can_host(d) and d.get("cluster_primary") not in served
            and not pages.is_old(d) and _has_homes(d) and (d.get("regno") or d["_id"]) not in skip]
    docs.sort(key=lambda d: (d.get("hot_score") or 0, pages._count(d.get("units_total")) or 0), reverse=True)
    out = []
    for d in docs[:MAX_CARDS]:
        when = _month(pages._day(d.get("completion_now")))
        out.append({"id": f"project-{d.get('regno') or d['_id']}", "kind": "project", "title": pages.names(d)[0][:90],
                    "locality": " · ".join(x for x in (area.name, f"MahaRERA completion {when}" if when else None) if x),
                    "bhk": None, "carpet_sqft": None, "price_text": None, "price_inr": None, "sample": False,
                    "url": f"/projects/{d['page_slug']}", "image_url": None, "priced": False})
    return out


async def project_cards(db, req: dict) -> List[dict]:
    """Up to three project cards in the buyer's area, priced agent projects that fit first; [] without a known area or on any failure."""
    if req.get("transaction") == "rent":
        return []
    area = _area(req)
    if area is None:
        return []
    try:
        cards = await _agent_project_cards(db, area, req)
        if len(cards) < MAX_CARDS:
            cards += await _register_cards(db, area, {c["id"].removeprefix("project-") for c in cards})
        return cards[:MAX_CARDS]
    except Exception as e:   # cards are a help, never a reason to drop the buyer's message
        log.info("project cards failed: %s", type(e).__name__)
        return []
