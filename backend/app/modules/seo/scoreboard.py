"""Are we above MagicBricks? (docs/plan/index-everything.md I6) Our place and the big portals' places for every Google search we
already ran, read from the stored results (areastats.websearch, `web_search_results`): no new searches, no cost.

Once a week (inside the seo loop, app/modules/seo/runner.py) it reads the searches run in the last WINDOW_DAYS and keeps on the
`seo_scoreboard` mark: how many showed us at all, how many show us above magicbricks.com (or show us and not them), the searches
where MagicBricks sits just above us (NEXT: the ones a better page most likely wins) and the ones we win, plus one line per week
(`history`) so the owner sees the count move. 99acres and housing.com are kept beside MagicBricks on every row.

The same results say whether a portal has started to show what only we show (docs/plan/seo-system.md 8b, H6a): homes booked
("244 of 416 units booked") and moved completion dates ("possession delayed"), read from each portal result's title and
snippet like rival.shows (the kind of fact, never their text). `format` on the mark: per portal the results showing each,
and up to FORMAT_EXAMPLES of them; the weekly note says so once a portal reaches FORMAT_ALERT.

MagicBricks is the rival we chose; it is not always the one above us. On 2026-11-06 Housiey held Ravet's searches with a thinner
page than ours (docs/plan/rival-housiey-ravet.md) and the board never named it. So `leaders` counts every other site in the same
results: how often it sat above us (or showed when we did not), overall and per area, so the rival to study is read from Google
in any area we add, not picked by hand.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.modules.areastats.demand import our_host, rank_of
from app.modules.areastats.websearch import RESULTS, site
from app.modules.newsroom.store import Store

MARK = "seo_scoreboard"
EVERY = timedelta(days=7)
WINDOW_DAYS = 28
RIVALS = {"magicbricks": "magicbricks.com", "acres99": "99acres.com", "housing": "housing.com"}
CLOSE = 3            # places: MagicBricks this close above us is a search to win next
SHOWN = 25
HISTORY = 26         # weeks kept
OUR_FORMAT = {
    "booked": re.compile(r"\b\d[\d,]*\s+(?:of|out of)\s+\d[\d,]*\s+(?:homes|units|flats|apartments)\b"
                         r"|\b(?:units?|homes|flats)\s+(?:booked|sold)\b|\b\d{1,3}\s?%\s+(?:booked|sold)\b", re.I),
    "date_moved": re.compile(r"\b(?:possession|completion)(?:\s+date)?\s+(?:delayed|postponed|moved|revised|extended|pushed)\b"
                             r"|\bdelayed\s+possession\b", re.I),
}
FORMAT_ALERT = 3     # portal results in the window showing one of them: they may be taking our format
FORMAT_EXAMPLES = 5
LEADERS_SHOWN = 10
AREA_LEADERS = 3


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def above(ours: Optional[int], rival: Optional[int]) -> bool:
    """We show, and the rival is not above us."""
    return ours is not None and (rival is None or ours < rival)


def row(doc: dict, host: str) -> dict:
    results = doc.get("results") or []
    out = {"query": doc["_id"], "kind": doc.get("kind"), "regno": doc.get("regno"), "at": doc.get("at"), "ours": rank_of(results, host)}
    out.update({k: rank_of(results, site) for k, site in RIVALS.items()})
    return out


def portal_format(docs: List[dict]) -> dict:
    """{portal: {booked, date_moved, examples: [{query, link, shows}]}}: portal results whose title or snippet shows homes booked or
    a moved completion date."""
    out = {k: {"booked": 0, "date_moved": 0, "examples": []} for k in RIVALS}
    for d in docs:
        for r in d.get("results") or []:
            if r.get("type", "organic") != "organic" or r.get("ad"):
                continue
            host = site(r.get("link", ""))
            portal = next((k for k, h in RIVALS.items() if host == h or host.endswith("." + h)), None)
            if portal is None:
                continue
            text = f"{r.get('title') or ''} {r.get('snippet') or ''}"
            hits = sorted(k for k, rx in OUR_FORMAT.items() if rx.search(text))
            for k in hits:
                out[portal][k] += 1
            if hits and len(out[portal]["examples"]) < FORMAT_EXAMPLES:
                out[portal]["examples"].append({"query": d["_id"], "link": r.get("link"), "shows": hits})
    return out


def leaders(docs: List[dict], host: str) -> List[dict]:
    """Every other site in the searches' organic results, most often above us first: {site, searches (it showed), above_us
    (it showed above us, or we did not show), top3}. One count per search per site, however many of its pages showed."""
    tally: dict = {}
    for d in docs:
        results = d.get("results") or []
        ours = rank_of(results, host)
        seen = set()
        for r in results:
            if r.get("type", "organic") != "organic" or r.get("ad") or int(r.get("position") or 0) <= 0:
                continue
            s = site(r.get("link", ""))
            if not s or s == host or s.endswith("." + host) or s in seen:
                continue
            seen.add(s)
            pos = int(r["position"])
            t = tally.setdefault(s, {"site": s, "searches": 0, "above_us": 0, "top3": 0})
            t["searches"] += 1
            t["top3"] += pos <= 3
            t["above_us"] += ours is None or pos < ours
    return sorted(tally.values(), key=lambda t: (-t["above_us"], -t["top3"], t["site"]))


def area_leaders(docs: List[dict], host: str) -> dict:
    """{area: the AREA_LEADERS sites most often above us} for the searches tied to an area: who to study there."""
    by_area: dict = {}
    for d in docs:
        if d.get("area"):
            by_area.setdefault(d["area"], []).append(d)
    return {a: leaders(ds, host)[:AREA_LEADERS] for a, ds in sorted(by_area.items())}


def leader_line(board: dict) -> str:
    """The weekly note's line on who sits above us, when the board has counted it."""
    top = [t for t in board.get("leaders") or [] if t.get("above_us")][:3]
    if not top or not board.get("searches"):
        return ""
    names = ", ".join(f"{t['site']} {t['above_us']}" for t in top)
    return f"Above us most often, of {board['searches']} Google searches: {names}."


def format_alert(fmt: Optional[dict]) -> List[str]:
    """The portals that reached FORMAT_ALERT results showing our kind of fact, for the weekly note."""
    names = {"magicbricks": "MagicBricks", "acres99": "99acres", "housing": "Housing.com"}
    return [names[k] for k, v in (fmt or {}).items() if k in names and v.get("booked", 0) + v.get("date_moved", 0) >= FORMAT_ALERT]


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
    fmt = portal_format(docs)
    s["leaders"], s["area_leaders"] = leaders(docs, host)[:LEADERS_SHOWN], area_leaders(docs, host)
    line = {k: s[k] for k in ("searches", "ours", "magicbricks", "above_mb", "above_mb_when_shown")}
    line["portal_format"] = sum(v["booked"] + v["date_moved"] for v in fmt.values())
    history = ((mark.get("history") or []) + [{"at": now, **line}])[-HISTORY:]
    await store.set_mark(MARK, at=now, history=history, format=fmt, **s)
    return line
