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
in any area we add, not picked by hand. `standing` is our own line beside them, overall and per area: without it the board named
everyone but us, and the owner had to ask where we were (2026-11-06).

Only searches a buyer could type count. The same collection holds our own lookups: a MahaRERA number in quotes (to read a
project's facts or prove two towers are one) and "<builder> official website Pune". Nobody searches those, MagicBricks rarely
shows for them, and until 2026-11-06 they made up most of the count and sat in "win next" ("PR1260002501386"). They are left
out (OWN_LOOKUPS), and each row says which of our pages showed (`page`) and which kind of search it was (`by_kind`), so the
owner sees which page beat MagicBricks for which search. "Ahead" is the fair count: both show, we are higher.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urlparse

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
OWN_LOOKUPS = ("regno", "builder")   # searches we run to read facts, not searches buyers type


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def above(ours: Optional[int], rival: Optional[int]) -> bool:
    """We show, and the rival is not above us."""
    return ours is not None and (rival is None or ours < rival)


def buyer_searches(docs: List[dict]) -> List[dict]:
    """The stored searches a buyer could type: our own fact lookups (OWN_LOOKUPS) left out."""
    return [d for d in docs if d.get("kind") not in OWN_LOOKUPS]


def our_page(results: List[dict], host: str) -> Optional[str]:
    """The path of our first organic result ("/projects/kharadi-x"), None when we do not show."""
    for r in results:
        if r.get("type", "organic") == "organic" and not r.get("ad") and int(r.get("position") or 0) > 0:
            link = r.get("link", "")
            s = site(link)
            if s == host or s.endswith("." + host):
                return urlparse(link).path or "/"
    return None


def row(doc: dict, host: str) -> dict:
    results = doc.get("results") or []
    out = {"query": doc["_id"], "kind": doc.get("kind"), "area": doc.get("area"), "regno": doc.get("regno"), "at": doc.get("at"),
           "ours": rank_of(results, host), "page": our_page(results, host)}
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


def standing(docs: List[dict], host: str) -> dict:
    """Our own line for these searches: {site, searches, shows, top3, first, place, sites}. `place` is 1 + the sites that showed in
    more searches than we did, out of every site seen, so a level site does not push us down."""
    ranks = [r for r in (rank_of(d.get("results") or [], host) for d in docs) if r is not None]
    others = leaders(docs, host)
    return {"site": host, "searches": len(docs), "shows": len(ranks), "top3": sum(r <= 3 for r in ranks), "first": sum(r == 1 for r in ranks),
            "place": 1 + sum(t["searches"] > len(ranks) for t in others), "sites": len(others) + 1}


def area_standing(docs: List[dict], host: str) -> dict:
    """{area: our line} for the searches tied to an area, including areas where we never show."""
    by_area: dict = {}
    for d in docs:
        if d.get("area"):
            by_area.setdefault(d["area"], []).append(d)
    return {a: standing(ds, host) for a, ds in sorted(by_area.items())}


def leader_line(board: dict) -> str:
    """The weekly note's line on where we stand and who sits above us, when the board has counted it."""
    top = [t for t in board.get("leaders") or [] if t.get("above_us")][:3]
    if not top or not board.get("searches"):
        return ""
    names = ", ".join(f"{t['site']} {t['above_us']}" for t in top)
    us = board.get("us")
    ours = f"We show in {us['shows']} of {us['searches']} Google searches, top 3 in {us['top3']}. " if us else ""
    return f"{ours}Above us most often, of {board['searches']} Google searches: {names}."


def format_alert(fmt: Optional[dict]) -> List[str]:
    """The portals that reached FORMAT_ALERT results showing our kind of fact, for the weekly note."""
    names = {"magicbricks": "MagicBricks", "acres99": "99acres", "housing": "Housing.com"}
    return [names[k] for k, v in (fmt or {}).items() if k in names and v.get("booked", 0) + v.get("date_moved", 0) >= FORMAT_ALERT]


def counts(rows: List[dict]) -> dict:
    """{searches, ours, magicbricks, both, ahead, only_us, only_mb}: `ahead` is both showing and us higher."""
    both = [r for r in rows if r["ours"] is not None and r["magicbricks"] is not None]
    return {"searches": len(rows), "ours": sum(1 for r in rows if r["ours"] is not None),
            "magicbricks": sum(1 for r in rows if r["magicbricks"] is not None), "both": len(both),
            "ahead": sum(1 for r in both if r["ours"] < r["magicbricks"]),
            "only_us": sum(1 for r in rows if r["ours"] is not None and r["magicbricks"] is None),
            "only_mb": sum(1 for r in rows if r["ours"] is None and r["magicbricks"] is not None)}


def score(rows: List[dict]) -> dict:
    mb_shown = [r for r in rows if r["magicbricks"] is not None]
    nxt = [r for r in mb_shown if r["ours"] is not None and 0 < r["ours"] - r["magicbricks"] <= CLOSE]
    nxt += [r for r in mb_shown if r["ours"] is None and r["magicbricks"] <= CLOSE]   # they are top, we are not on the page
    won = [r for r in rows if above(r["ours"], r["magicbricks"])]
    both = [r for r in mb_shown if r["ours"] is not None]
    kinds: dict = {}
    for r in rows:
        kinds.setdefault(r.get("kind") or "other", []).append(r)
    return {"searches": len(rows), "ours": sum(1 for r in rows if r["ours"] is not None), "magicbricks": len(mb_shown),
            "above_mb": len(won), "above_mb_when_shown": sum(1 for r in mb_shown if above(r["ours"], r["magicbricks"])),
            "both": len(both), "by_kind": {k: counts(rs) for k, rs in sorted(kinds.items())},
            "next": sorted(nxt, key=lambda r: (r["ours"] is None, (r["ours"] or 99) - r["magicbricks"]))[:SHOWN],
            "won": sorted(won, key=lambda r: r["ours"])[:SHOWN],
            # head to head: both on the page; the wins most clearly ahead first, the losses closest to winning first
            "ahead_rows": sorted((r for r in both if r["ours"] < r["magicbricks"]), key=lambda r: (r["ours"] - r["magicbricks"], r["ours"]))[:SHOWN],
            "behind_rows": sorted((r for r in both if r["ours"] > r["magicbricks"]), key=lambda r: (r["ours"] - r["magicbricks"], r["ours"]))[:SHOWN]}


async def run_once(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    """This week's scoreboard. None when it already ran this week or no search was stored yet."""
    mark = await store.get_mark(MARK)
    last = _aware(mark.get("at"))
    if not force and last is not None and now - last < EVERY:
        return None
    since = now - timedelta(days=WINDOW_DAYS)
    host = our_host()
    docs = buyer_searches([d for d in await store.db.get_collection(RESULTS).find({}).to_list(None)
                           if (_aware(d.get("at")) or since) >= since])
    if not docs:
        return None
    s = score([row(d, host) for d in docs])
    fmt = portal_format(docs)
    s["leaders"], s["area_leaders"] = leaders(docs, host)[:LEADERS_SHOWN], area_leaders(docs, host)
    s["us"], s["area_us"] = standing(docs, host), area_standing(docs, host)
    line = {k: s[k] for k in ("searches", "ours", "magicbricks", "above_mb", "above_mb_when_shown", "both")}
    line["buyer_only"] = True   # weeks before 2026-11-06 counted our own lookups too: not comparable with this one
    line["portal_format"] = sum(v["booked"] + v["date_moved"] for v in fmt.values())
    history = ((mark.get("history") or []) + [{"at": now, **line}])[-HISTORY:]
    await store.set_mark(MARK, at=now, history=history, format=fmt, **s)
    return line
