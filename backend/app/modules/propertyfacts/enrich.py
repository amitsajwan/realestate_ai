"""Facts for a MahaRERA project with no listing: the same gatherer and the same kept sheet as a listing campaign, for the
project's own page (areastats.enrich calls this one project at a time; docs/plan/project-pages.md). No LLM here.

A project and a listing in it share one sheet (keyed by the registration number). Re-gathering a project keeps the agent's
offer an earlier campaign stored (price, size, type: readings from "listing"), so a background refresh never wipes what a
post quoted. Sources keep their limits: one shared Clients per process (Nominatim at most 1 request a second, answers
cached), MahaRERA only when our register lacks the project or its details are stale."""
from datetime import datetime
from typing import Any, Dict, Optional

from .gather import Clients, gather
from .public import view
from .store import FactsStore

OFFER_KEYS = ("transaction", "property_type", "price_inr", "carpet_sqft", "bhk", "amenities")
_clients: Optional[Clients] = None


def _shared_clients(db) -> Clients:
    """One Clients for the process, so its Nominatim throttle and cache span every project."""
    global _clients
    if _clients is None:
        from app.modules.newsroom.store import Store as Register
        _clients = Clients(register=Register(db), facts_store=FactsStore(db))
    return _clients


def _offer(kept: Optional[dict]) -> Dict[str, Any]:
    """The agent's offer from a kept sheet: values whose readings came from the agent's listing."""
    out: Dict[str, Any] = {}
    for f in (kept or {}).get("facts") or []:
        key = "carpet_sqft" if f["key"] == "plot_sqft" else f["key"]
        if key in OFFER_KEYS and any(r.get("source") == "listing" for r in f.get("readings") or []):
            out[key] = f.get("value")
    if kept and kept.get("listing_id"):
        out["id"] = kept["listing_id"]
    return out


async def gather_project(db, regno: str, name: str, locality: Optional[str], city: str = "Pune",
                         now: Optional[datetime] = None, clients: Any = None) -> dict:
    """Gather and keep the facts for one registered project. Returns {"key", "view", "notes", "match"}: `view` is what
    GET /public/property-facts/by-regno/{regno} serves (None when nothing usable was found). Never raises for a source that
    is down: the sheet says what could not be found."""
    now = now or datetime.utcnow()
    clients = clients or _shared_clients(db)
    store = clients.facts_store or FactsStore(db)
    regno = (regno or "").strip().upper()
    kept = await store.get(regno) if regno else None
    doc = {**_offer(kept), "project_name": name, "rera_no": regno, "locality": locality or "", "city": city}
    sheet = await gather({k: v for k, v in doc.items() if v not in (None, "")}, clients, now)
    saved = await store.find(regno, name, locality or "")
    return {"key": (saved or {}).get("_id"), "view": view(saved), "notes": list(sheet.notes),
            "match": sheet.match.how if sheet.match else ""}
