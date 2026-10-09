"""The discovery agent (docs/RADAR.md §6): once a day, a tool-calling loop finds where Pune buyers are asking now and proposes new
watches. It is the radar's one agent, and it is read-only: its tools search and read, and `propose_watch` only adds a watch the
bandit then tests on a small budget (bandit.py) and retires if it finds nothing. It cannot post, reply or spend beyond its caps
(MAX_SEARCHES quota-costing searches and MAX_PROPOSALS watches per run, `steps` model turns). Every run is logged in radar_runs.

Protocol with the model (JSON mode through the gateway): each turn returns
    {"thought": "...", "tool": "<name>", "args": {...}}   or   {"thought": "...", "done": true, "summary": "..."}"""
import json
import logging
from datetime import timedelta
from typing import Any, Callable, Dict, List

from . import bandit, places, store
from .sources import ALL as SOURCES
from .sources import KINDS

log = logging.getLogger(__name__)

MAX_SEARCHES = 6
MAX_PROPOSALS = 12

SYSTEM = """You are the discovery agent of a Pune home-buyer radar. Goal: find NEW places online where people ask about buying or
renting homes in our areas (questions like "2BHK price?", "possession kab?"), and propose them as watches.
Good watches: recent, much-viewed YouTube videos about a specific Pune project or area (people comment questions there);
search queries naming a project or area; subreddits or search terms where Pune people ask about flats; RSS feeds of forums.
Weak watches: news, builder ads, generic "real estate tips", other cities.
Start with `overview` to see what works and which areas are thin, then search for the gaps, then propose.
Tools (call one per turn):
- overview(): areas with leads found in 14 days, best and worst watches
- projects(area): MahaRERA projects registered in an area (names to search for)
- youtube_search(query, area): recent popular videos (costs quota; at most %d searches per run)
- reddit_search(query, subreddit): recent posts in a subreddit
- propose_watch(source, kind, value, area, reason): add a watch; source/kind one of %s; value is a query, video id, subreddit,
  feed URL or hashtag (no #). Max %d per run.
Reply ONLY with JSON: {"thought": "...", "tool": "...", "args": {...}} or {"thought": "...", "done": true, "summary": "..."}"""


class Tools:
    def __init__(self, db, run: Dict[str, Any]):
        self.db, self.run = db, run
        self.searches = 0
        self.proposed: List[dict] = []

    async def overview(self) -> dict:
        since = store.now() - timedelta(days=14)
        rows = await self.db.get_collection(store.SIGNALS).aggregate([
            {"$match": {"created_at": {"$gte": since}, "shown": True}}, {"$group": {"_id": "$area", "n": {"$sum": 1}}}]).to_list(50)
        found = {r["_id"] or "unknown": r["n"] for r in rows}
        ws = await self.db.get_collection(store.WATCHES).find({"active": True}).to_list(3000)
        ranked = sorted(ws, key=bandit.mean, reverse=True)

        def row(w):
            return {"source": w["source"], "kind": w["kind"], "value": w["value"][:80], "area": w.get("area"),
                    "hits": w.get("hits", 0), "checks": w.get("checks", 0)}
        return {"areas": {p.key: found.get(p.key, 0) for p in places.all_places()}, "unknown_area": found.get("unknown", 0),
                "best_watches": [row(w) for w in ranked[:8]], "worst_watches": [row(w) for w in ranked[-5:]],
                "watches_by_source": {s: sum(1 for w in ws if w["source"] == s) for s in SOURCES}}

    async def projects(self, area: str = "") -> dict:
        from app.modules.areastats.pages import listing
        rows = await listing(self.db, area=area or None, only_indexable=False, limit=40)
        return {"area": area, "projects": [{"name": r["name"], "promoter": r.get("promoter"), "completion": r.get("completion_now")}
                                           for r in rows if r.get("active")][:25]}

    async def youtube_search(self, query: str = "", area: str = "") -> dict:
        if self.searches >= MAX_SEARCHES or await store.used(self.db, "yt_search") >= 90:
            return {"error": "search budget used up for this run"}
        self.searches += 1
        await store.spend(self.db, "yt_search")
        found = await SOURCES["youtube"].search(query, area or None, max_age_days=270, limit=8)
        known = {w["value"] for w in await self.db.get_collection(store.WATCHES).find(
            {"source": "youtube", "kind": "video", "value": {"$in": [p.value for p in found]}}, {"value": 1}).to_list(50)}
        return {"videos": [{"id": p.value, "title": p.title, "info": p.evidence, "already_watched": p.value in known} for p in found]}

    async def reddit_search(self, query: str = "", subreddit: str = "pune") -> dict:
        try:
            found = await SOURCES["reddit"].search(query, None, subreddit)
        except Exception as e:
            return {"error": f"reddit unavailable ({type(e).__name__})"}
        return {"posts": [{"title": p.title[:120], "info": p.evidence} for p in found[:10]]}

    async def propose_watch(self, source: str = "", kind: str = "", value: str = "", area: str = "", reason: str = "") -> dict:
        if len(self.proposed) >= MAX_PROPOSALS:
            return {"error": "proposal limit reached; finish"}
        if kind not in KINDS.get(source, ()):
            return {"error": f"unknown source/kind; use one of {KINDS}"}
        value = value.strip().lstrip("#")
        if not 2 <= len(value) <= 300:
            return {"error": "bad value"}
        p = places.get(area or "")
        res = await self.db.get_collection(store.WATCHES).update_one(
            {"source": source, "kind": kind, "value": value},
            {"$setOnInsert": {"created_at": store.now(), "active": True, "hits": 0, "found": 0, "checks": 0, "cursor": None,
                              "area": p.key if p else None, "origin": "agent", "reason": reason[:200], "run_id": self.run["_id"]}},
            upsert=True)
        if not res.upserted_id:
            return {"ok": False, "note": "already watched"}
        self.proposed.append({"source": source, "kind": kind, "value": value, "area": p.key if p else None, "reason": reason[:200]})
        return {"ok": True, "proposed": len(self.proposed)}

    def table(self) -> Dict[str, Callable]:
        return {"overview": self.overview, "projects": self.projects, "youtube_search": self.youtube_search,
                "reddit_search": self.reddit_search, "propose_watch": self.propose_watch}


async def run(db, llm, steps: int = 12) -> dict:
    if llm is None:
        return {"skipped": "no model"}
    rec = {"_id": f"discovery:{store.now().strftime('%Y%m%dT%H%M')}", "started_at": store.now(), "steps": []}
    tools = Tools(db, rec)
    table = tools.table()
    system = SYSTEM % (MAX_SEARCHES, json.dumps(KINDS), MAX_PROPOSALS)
    transcript: List[str] = []
    summary = ""
    for i in range(steps):
        user = "Begin." if not transcript else "So far:\n" + "\n".join(transcript[-10:]) + "\nNext step?"
        msg = await llm.json(system, user)
        if not isinstance(msg, dict):
            break
        if msg.get("done"):
            summary = str(msg.get("summary") or "")[:500]
            break
        name, args = str(msg.get("tool") or ""), msg.get("args") or {}
        fn = table.get(name)
        if fn is None or not isinstance(args, dict):
            result: Any = {"error": f"unknown tool {name!r}"}
        else:
            try:
                result = await fn(**{k: str(v) for k, v in args.items() if k in fn.__code__.co_varnames})
            except Exception as e:
                log.exception("radar discovery: tool %s failed", name)
                result = {"error": type(e).__name__}
        out = json.dumps(result, default=str)[:1800]
        transcript.append(f"[{i + 1}] {name}({json.dumps(args)[:200]}) -> {out}")
        rec["steps"].append({"thought": str(msg.get("thought") or "")[:300], "tool": name, "args": args, "result": out[:600]})
    rec.update(finished_at=store.now(), proposed=tools.proposed, searches=tools.searches, summary=summary)
    await db.get_collection(store.RUNS).replace_one({"_id": rec["_id"]}, rec, upsert=True)
    return {"proposed": len(tools.proposed), "searches": tools.searches, "steps": len(rec["steps"])}
