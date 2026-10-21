"""The page doctor's "rival" fix (docs/plan/index-everything.md I6, second half): where MagicBricks ranks just above our page for
the page's own search, lead our search description with the facts their result shows, from our record.

Which pages: the scoreboard's `next` rows (seo.scoreboard) that are project or target searches with a register number: MagicBricks within
CLOSE places above us, or in the top places while we are not on the page. What their result shows is read from its title and
snippet in the stored Google result (price, home sizes, possession); never their text or numbers, only which kind of fact.
Our description then leads with those of them our record holds (published prices, the sizes priced, the filed possession date),
then homes booked and the MahaRERA number. Logged and measured like every fix (seo/actions.py `rival`, field seo_description).
"""
import re
from datetime import datetime
from typing import Dict, List, Optional, Set

from app.modules.areastats import prices
from app.modules.areastats.pages import _long, booked, names
from app.modules.areastats.service import _count, _day
from app.modules.areastats.websearch import RESULTS, site
from app.modules.newsroom.store import Store

from . import scoreboard

MB = "magicbricks.com"
MAX = 160
SHOWS = {"price": prices.PRICE_LINE, "bhk": re.compile(r"\b\d(?:\.5)?\s*bhk\b", re.I),
         "possession": re.compile(r"\b(possession|ready to move|completion|handover)\b", re.I)}


def _inr(n: int) -> str:
    if n >= 10_000_000:
        return f"₹{n / 10_000_000:.2f}".rstrip("0").rstrip(".") + " Cr"
    return f"₹{n / 100_000:.2f}".rstrip("0").rstrip(".") + " L"


def shows(result: dict) -> Set[str]:
    """Which kinds of fact a search result's title and snippet show."""
    text = f"{result.get('title') or ''} {result.get('snippet') or ''}"
    return {k for k, rx in SHOWS.items() if rx.search(text)}


def description(doc: dict, wants: Set[str], now: Optional[datetime] = None) -> Optional[str]:
    """Our search description led by the facts the rival shows that we hold; None when we hold none of them."""
    shown = doc.get("search_name") or names(doc)[0]
    lead, rest = [], []
    rows = (prices.public(doc.get("prices"), now) or {}).get("rows") or []
    sized = [r for r in rows if "BHK" in r["bhk"]]
    bhk = ", ".join(dict.fromkeys(r["bhk"].replace(" BHK", "") for r in sized))
    if rows and "price" in wants:
        lead.append((f"{bhk} BHK from " if bhk else "from ") + _inr(min(r["from_inr"] for r in rows)))
    elif bhk and "bhk" in wants:
        lead.append(f"{bhk} BHK homes")
    when = _day(doc.get("completion_now"))
    if when:
        (lead if "possession" in wants else rest).append(f"possession filed for {_long(when)}")
    if not lead:
        return None
    total, sold = _count(doc.get("units_total")), booked(doc)
    if total and sold is not None and sold <= total:
        rest.append(f"{sold} of {total} homes booked")
    text = f"{shown}: " + ", ".join(lead + rest) + f". MahaRERA {doc.get('regno') or doc['_id']}."
    return text if len(text) <= MAX else text[:MAX - 1].rsplit(" ", 1)[0] + "…"


async def targets(store: Store) -> Dict[str, dict]:
    """{regno: {query, ours, magicbricks, wants}} for the project searches where MagicBricks is just above us."""
    out: Dict[str, dict] = {}
    rows: List[dict] = (await store.get_mark(scoreboard.MARK)).get("next") or []
    coll = store.db.get_collection(RESULTS)
    for r in rows:
        if r.get("kind") not in ("project", "target") or not r.get("regno") or r["regno"] in out:
            continue
        doc = await coll.find_one({"_id": r["query"]}) or {}
        mb = next((x for x in doc.get("results") or [] if x.get("type", "organic") == "organic" and not x.get("ad")
                   and site(x.get("link", "")).endswith(MB)), None)
        if mb is None:
            continue
        out[r["regno"]] = {"query": r["query"], "ours": r.get("ours"), "magicbricks": r.get("magicbricks"), "wants": shows(mb)}
    return out
