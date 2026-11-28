"""The monthly cap on paid route reads (Google Routes API elements: one origin to one destination at one departure time).

The count is kept in this module's own collection, `area_research`, under kind "commute_budget" and the month as its place
(_id "commute_budget|2026-11"), so it survives restarts and the loop never spends past NEIGHBOURHOOD_ROUTE_ELEMENTS_PER_MONTH.

A researcher that would go over the cap raises NotNow: the loop stops that researcher for this cycle without marking the place
as tried, so it is measured first once the month turns, instead of waiting a whole refresh period.
"""
from datetime import datetime

KIND = "commute_budget"


class NotNow(Exception):
    """Nothing wrong; this researcher cannot run any more this cycle (its monthly budget is spent)."""


def month_of(now: datetime) -> str:
    return now.strftime("%Y-%m")


async def used(store, now: datetime) -> int:
    doc = await store.get(KIND, month_of(now))
    return int(((doc or {}).get("data") or {}).get("elements") or 0)


async def spend(store, now: datetime, elements: int) -> None:
    if elements <= 0:
        return
    month = month_of(now)
    await store.research.update_one({"_id": f"{KIND}|{month}"},
                                    {"$inc": {"data.elements": elements},
                                     "$set": {"kind": KIND, "place": month, "tried_at": now, "computed_at": now, "ok": True}},
                                    upsert=True)
