"""The owner's Rankings tab and the weekly numbers (docs/plan/rank-loop.md R9), read from what the rank loop stores.

rankings(store, now) -> {
  week:      this week's site numbers (clicks, impressions, project pages on page one and near it) and last week's, from the daily
             snapshots seo.targets keeps;
  doctor:    the last round (pages, fix, why) and the fix-type results table (seo.doctor.results);
  actions:   the latest fixes with before / after numbers;
  targets:   project pages with a target search: position, impressions, our Google rank history and who ranks above us
             (the stored Serper results for that search);
  conflicts: searches that show two of our pages (seo.targets R2);
  gaps:      searches with no page in the top 20 (seo.gaps R7);
  scoreboard: searches where we are above MagicBricks, the ones to win next, and the count per week (seo.scoreboard I6);
  request_indexing: pages Google has not indexed, most worth the owner's Request indexing first (seo.note);
  coverage:  indexed share per child sitemap (area-kharadi, core, builders...), least indexed first (seo.coverage).
}
Owner only (marketer sites are never public).
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.modules.areastats.demand import our_host, rank_of
from app.modules.areastats.websearch import RESULTS, site
from app.modules.newsroom.store import Store

from . import aivisits, coverage, doctor, gaps, note, scoreboard, targets
from .actions import ACTIONS, gain

TARGETS_SHOWN = 60
ACTIONS_SHOWN = 40


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _iso(d) -> Optional[str]:
    d = _aware(d)
    return d.isoformat() if d else None


def week(history: List[dict], now: datetime) -> dict:
    """The newest snapshot and the one from about a week before it (None when there is none yet)."""
    snaps = [h for h in history if _aware(h.get("at"))]
    if not snaps:
        return {"now": None, "week_ago": None}
    last = snaps[-1]
    before = [h for h in snaps if _aware(last["at"]) - _aware(h["at"]) >= timedelta(days=7)]
    clean = lambda h: {k: (_iso(v) if k == "at" else v) for k, v in h.items()} if h else None   # noqa: E731
    return {"now": clean(last), "week_ago": clean(before[-1] if before else None)}


async def above_us(store: Store, phrase: str) -> dict:
    """Our place for a search and the sites above us, from the latest stored results for it."""
    doc = await store.db.get_collection(RESULTS).find_one({"_id": phrase})
    if not doc:
        return {"checked_at": None, "our_rank": None, "above": []}
    results = doc.get("results") or []
    ours = rank_of(results, our_host())
    organic = [r for r in results if r.get("type", "organic") == "organic" and not r.get("ad") and int(r.get("position") or 0) > 0]
    above = [site(r.get("link", "")) for r in sorted(organic, key=lambda r: int(r["position"]))
             if ours is None or int(r["position"]) < ours]
    return {"checked_at": _iso(doc.get("at")), "our_rank": ours, "above": list(dict.fromkeys(a for a in above if a))[:6]}


async def rankings(store: Store, now: datetime) -> dict:
    tmark = await store.get_mark(targets.MARK)
    dmark = await store.get_mark(doctor.MARK)
    docs = [d for d in await store.all_projects() if d.get("seo_target") and d.get("page_slug")]
    docs.sort(key=lambda d: -int((d.get("seo_target") or {}).get("impressions") or 0))
    demand = store.db.get_collection(targets.DEMAND)
    rows = []
    for d in docs[:TARGETS_SHOWN]:
        t = d["seo_target"]
        dem = await demand.find_one({"_id": t["phrase"]}) or {}
        rows.append({"path": f"/projects/{d['page_slug']}", "name": d.get("search_name") or d.get("name", ""),
                     "phrase": t["phrase"], "impressions": t.get("impressions"), "position": t.get("position"),
                     "page_position": d.get("gsc_position"), "clicks": d.get("gsc_clicks"),
                     "history": [{"at": _iso(h.get("at")), "position": h.get("position")} for h in (dem.get("gsc_history") or [])][-30:],
                     "page_fix_at": _iso(d.get("page_fix_at")), "page_fix": d.get("page_fix"), **await above_us(store, t["phrase"])})
    acts = await store.db.get_collection(ACTIONS).find({}).to_list(20000)
    acts.sort(key=lambda a: _aware(a.get("at")) or now, reverse=True)
    actions = [{"path": a.get("path"), "fix": a.get("fix"), "at": _iso(a.get("at")), "phrase": a.get("phrase"), "note": a.get("note"),
                "before": a.get("before"), "after14": {k: v for k, v in (a.get("after14") or {}).items() if k != "at"} or None,
                "after28": {k: v for k, v in (a.get("after28") or {}).items() if k != "at"} or None,
                "gain": gain(a), "reverted": bool(a.get("reverted")),
                "new": a.get("new") if a.get("fix") in ("title", "description") else None}
               for a in acts[:ACTIONS_SHOWN]]
    conflicts = await store.get_mark(targets.CONFLICTS)
    gapmark = await store.get_mark(gaps.MARK)
    return {
        "week": week(tmark.get("history") or [], now),
        "targets_at": _iso(tmark.get("at")),
        "doctor": {"at": _iso(dmark.get("at")), "treated": dmark.get("treated") or [], "menu": dmark.get("menu") or list(doctor.FIXES),
                   "results": await doctor.results(store)},
        "actions": actions,
        "targets": rows,
        "conflicts": {"at": _iso(conflicts.get("at")), "total": conflicts.get("total") or 0, "items": conflicts.get("items") or []},
        "gaps": {"at": _iso(gapmark.get("at")), "total": gapmark.get("total") or 0, "items": gapmark.get("items") or []},
        "scoreboard": _board(await store.get_mark(scoreboard.MARK)),
        "request_indexing": await note.request_list(store),
        "coverage": {"at": _iso((cov := await store.get_mark(coverage.MARK)).get("at")), "by_sitemap": cov.get("by_sitemap") or []},
        "ai": await aivisits.summary(store.db, now),
    }


def _board(m: dict) -> dict:
    clean = lambda r: {k: (_iso(v) if k == "at" else v) for k, v in r.items()}   # noqa: E731
    return {"at": _iso(m.get("at")), **{k: m.get(k) or 0 for k in ("searches", "ours", "magicbricks", "above_mb", "above_mb_when_shown")},
            "next": [clean(r) for r in m.get("next") or []], "won": [clean(r) for r in m.get("won") or []],
            "history": [clean(h) for h in m.get("history") or []]}


def week_lines(w: dict) -> List[str]:
    """Plain lines for the weekly e-mail: each number with last week's beside it."""
    now, ago = w.get("now"), w.get("week_ago") or {}
    if not now:
        return ["No ranking numbers yet (Search Console has not been read)."]
    label = {"clicks": "Clicks (28 days)", "impressions": "Impressions (28 days)", "page_one": "Project pages on page one",
             "near_page_one": "Project pages near page one (8-20)", "targeted": "Pages with a target search"}
    out = []
    for k, name in label.items():
        v, p = now.get(k), ago.get(k)
        out.append(f"{name}: {v}" + (f" (week before: {p}, {'+' if v - p >= 0 else ''}{v - p})" if isinstance(p, int) and isinstance(v, int) else ""))
    return out
