"""Are we above MagicBricks? (docs/plan/index-everything.md I6) Our place and the big portals' places for every Google search we
already ran, read from the stored results (areastats.websearch, `web_search_results`): no new searches, no cost.

Once a week (inside the seo loop, app/modules/seo/runner.py) it reads the searches run in the last WINDOW_DAYS and keeps on the
`seo_scoreboard` mark: how many showed us at all, how many show us above magicbricks.com (or show us and not them), the searches
where MagicBricks sits just above us (NEXT: the ones a better page most likely wins) and the ones we win, plus one line per week
(`history`) so the owner sees the count move. 99acres and housing.com are kept beside MagicBricks on every row.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.modules.areastats.demand import our_host, rank_of
from app.modules.areastats.websearch import RESULTS
from app.modules.newsroom.store import Store

MARK = "seo_scoreboard"
EVERY = timedelta(days=7)
WINDOW_DAYS = 28
RIVALS = {"magicbricks": "magicbricks.com", "acres99": "99acres.com", "housing": "housing.com"}
CLOSE = 3            # places: MagicBricks this close above us is a search to win next
SHOWN = 25
HISTORY = 26         # weeks kept


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def above(ours: Optional[int], rival: Optional[int]) -> bool:
    """We show, and the rival is not above us."""
    return ours is not None and (rival is None or ours < rival)


def row(doc: dict, host: str) -> dict:
    results = doc.get("results") or []
    out = {"query": doc["_id"], "kind": doc.get("kind"), "at": doc.get("at"), "ours": rank_of(results, host)}
    out.update({k: rank_of(results, site) for k, site in RIVALS.items()})
    return out


def score(rows: List[dict]) -> dict:
    mb_shown = [r for r in rows if r["magicbricks"] is not None]
    nxt = [r for r in mb_shown if r["ours"] is not None and 0 < r["ours"] - r["magicbricks"] <= CLOSE]
    nxt += [r for r in mb_shown if r["ours"] is None and r["magicbricks"] <= CLOSE]   # they are top, we are not on the page
    won = [r for r in rows if above(r["ours"], r["magicbricks"])]
    return {"searches": len(rows), "ours": sum(1 for r in rows if r["ours"] is not None), "magicbricks": len(mb_shown),
            "above_mb": len(won), "above_mb_when_shown": sum(1 for r in mb_shown if above(r["ours"], r["magicbricks"])),
            "next": sorted(nxt, key=lambda r: (r["ours"] is None, (r["ours"] or 99) - r["magicbricks"]))[:SHOWN],
            "won": sorted(won, key=lambda r: r["ours"])[:SHOWN]}


async def run_once(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    """This week's scoreboard. None when it already ran this week or no search was stored yet."""
    mark = await store.get_mark(MARK)
    last = _aware(mark.get("at"))
    if not force and last is not None and now - last < EVERY:
        return None
    since = now - timedelta(days=WINDOW_DAYS)
    host = our_host()
    docs = [d for d in await store.db.get_collection(RESULTS).find({}).to_list(None) if (_aware(d.get("at")) or since) >= since]
    if not docs:
        return None
    s = score([row(d, host) for d in docs])
    line = {k: s[k] for k in ("searches", "ours", "magicbricks", "above_mb", "above_mb_when_shown")}
    history = ((mark.get("history") or []) + [{"at": now, **line}])[-HISTORY:]
    await store.set_mark(MARK, at=now, history=history, **s)
    return line
