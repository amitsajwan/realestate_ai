"""Which MahaRERA project registration a property's ads may print (AR-3; MahaRERA Order 46C/2025, docs/MARKETING.md "MahaRERA on
our ads"). The answer becomes the QR badge on the pack cards, the campaign cards and the reel's closing scene
(marketing.maharera); None means no badge and no registration line.

Trusted, in this order:
    1. MahaRERA's own record of the number (the fact sheet's `rera_no` read from MahaRERA), with its project page for the QR
    2. the agent's own listing (`rera_no`, a P5 project number), unless the agent answered "exempt" on the brochure kit or
       MahaRERA's record says another number (a conflict is raised with the run, never printed)
    3. the brochure kit's registration when it is `verified` or `registered_by_agent` (the agent said so and gave the number)
Never: an `unverified` brochure number, `unknown`, `exempt`, a number in conflict, or the agent's own registration (A5...)."""
from typing import Any, Dict, Optional

from app.modules.marketing.maharera import ProjectRegistration, project_regno, registration, view_url
from app.modules.newsroom.store import Store as Register

from .brochure import Brochures
from .facts import Fact
from .store import FactsStore, facts_of

TRUSTED_KIT = ("verified", "registered_by_agent")


def _page(facts: Dict[str, Fact], regno: str) -> str:
    """The project's MahaRERA page from the sheet, when it belongs to this very number."""
    url, num = facts.get("maharera_url"), facts.get("rera_no")
    if not (url and url.usable and num and any(r.source == "maharera" and project_regno(r.value) == regno for r in num.readings)):
        return ""
    return view_url(url.value)


def trusted(listing: Optional[dict], facts: Optional[Dict[str, Fact]] = None,
            kit: Optional[dict] = None) -> Optional[ProjectRegistration]:
    """The registration to print for this property (see the module notes): its QR leads to the project's MahaRERA page when
    the sheet holds it, else to the MahaRERA site."""
    listing, facts = listing or {}, facts or {}
    if (listing.get("title") or "").strip().lower().startswith("sample"):
        return None
    f = facts.get("rera_no")
    if f is not None and f.level == "conflict":
        return None
    reg = (kit or {}).get("registration") or {}
    if f is not None and f.usable and "maharera" in f.sources and project_regno(f.value):
        num = project_regno(f.value)
        return registration(num, _page(facts, num))
    if reg.get("status") == "exempt":
        return None
    own = project_regno(listing.get("rera_no")) or (project_regno(f.value) if f is not None and f.usable and "listing" in f.sources
                                                      else "")
    if own:
        return registration(own, _page(facts, own))
    if reg.get("status") in TRUSTED_KIT and project_regno(reg.get("rera_no")):
        num = project_regno(reg["rera_no"])
        return registration(num, _page(facts, num))
    return None


async def for_listing(db: Any, listing: dict) -> Optional[ProjectRegistration]:
    """trusted() from what is kept: the listing's brochure kit, its last fact sheet and, for the QR's project page, our MahaRERA
    register (newsroom `projects`). Read-only. Wired into marketing.maharera (app/wiring.py)."""
    lid = str(listing.get("_id") or listing.get("id") or "")
    kit = await Brochures(db, "").current(lid) if lid else None
    sheet = await FactsStore(db).find(project_regno(listing.get("rera_no")), listing.get("project_name") or "",
                                      listing.get("locality") or "")
    facts = facts_of(sheet)
    reg = trusted(listing, facts, kit)
    if reg is None or view_url(reg.url):
        return reg
    project = await Register(db).project(reg.regno) or {}
    return registration(reg.regno, project.get("source_url")) or reg
