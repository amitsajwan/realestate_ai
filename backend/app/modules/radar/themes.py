"""Demand insights (docs/RADAR.md §6): once a week, the buyer questions found per area are grouped by meaning and each group is
named: "Wagholi: 34 asked about possession delays". Feeds agent reports (`area_demand`), FAQ gaps and reel topics.
Clustering: average-linkage agglomerative on cosine distance over the stored embeddings, cut at CUT (numpy, a few hundred
questions per area). Groups smaller than MIN_SIZE are left out. The model only names a group from its own questions."""
import logging
from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Optional

import numpy as np

from . import places, store

log = logging.getLogger(__name__)

CUT = 0.16            # cosine distance: e5 questions on the same topic sit within ~0.1-0.15
MIN_SIZE = 3
MAX_PER_AREA = 400

NAMER = """These are questions people asked about homes in one Pune area this week. Name what they have in common in at most
6 plain English words (e.g. "possession date delays", "2 BHK prices under 70L", "home loan eligibility"). Return ONLY JSON:
{"theme": "...", "faq": "one question a buyer guide page should answer"}"""


def cluster(vectors: np.ndarray, cut: float = CUT) -> List[List[int]]:
    """Average-linkage agglomerative clustering; returns groups of row indices, largest first."""
    n = len(vectors)
    if n == 0:
        return []
    groups: Dict[int, List[int]] = {i: [i] for i in range(n)}
    sim = (vectors @ vectors.T).astype(np.float64)
    np.fill_diagonal(sim, -np.inf)
    alive = np.ones(n, dtype=bool)
    while alive.sum() > 1:
        masked = np.where(alive[:, None] & alive[None, :], sim, -np.inf)
        a, b = np.unravel_index(int(np.argmax(masked)), masked.shape)
        if 1 - masked[a, b] > cut:
            break
        na, nb = len(groups[a]), len(groups[b])
        merged = (na * sim[a] + nb * sim[b]) / (na + nb)   # Lance-Williams update for average linkage
        sim[a], sim[:, a] = merged, merged
        sim[a, a] = -np.inf
        alive[b] = False
        sim[b], sim[:, b] = -np.inf, -np.inf
        groups[a] += groups.pop(b)
    return sorted(groups.values(), key=len, reverse=True)


async def build(db, llm, days: int = 7) -> Dict[str, int]:
    from app.platform import embed
    since = store.now() - timedelta(days=days)
    model = embed.model_name()
    docs = await db.get_collection(store.SIGNALS).find(
        {"status": {"$in": ["scored", "sent", "converted", "skipped"]}, "created_at": {"$gte": since}, "embed_model": model,
         "intent.role": {"$in": ["buyer", "investor", "renter"]}},
        {"embedding": 1, "area": 1, "intent.question": 1, "text": 1}).to_list(5000)
    by_area: Dict[str, List[dict]] = defaultdict(list)
    for d in docs:
        by_area[d.get("area") or "pune"].append(d)
    week = store.now().strftime("%G-W%V")
    out = {}
    for area, rows in by_area.items():
        rows = rows[:MAX_PER_AREA]
        vecs = np.asarray([r["embedding"] for r in rows], dtype=np.float32)
        themes = []
        for g in cluster(vecs):
            if len(g) < MIN_SIZE:
                continue
            qs = [((rows[i].get("intent") or {}).get("question") or rows[i].get("text", ""))[:160] for i in g]
            named = await llm.json(NAMER, "\n".join(f"- {q}" for q in qs[:25])) if llm is not None else None
            themes.append({"theme": str((named or {}).get("theme") or qs[0])[:80], "faq": str((named or {}).get("faq") or "")[:200],
                           "count": len(g), "examples": qs[:5], "signal_ids": [rows[i]["_id"] for i in g[:50]]})
        await db.get_collection(store.THEMES).update_one(
            {"week": week, "area": area}, {"$set": {"themes": themes, "questions": len(rows), "at": store.now()}}, upsert=True)
        out[area] = len(themes)
    return out


async def area_demand(db, area: str, weeks: int = 1) -> Optional[dict]:
    """For agent reports: how many asked in an area lately and about what. None when nothing was found."""
    p = places.get(area)
    key = p.key if p else area
    docs = await db.get_collection(store.THEMES).find({"area": key}).sort("week", -1).to_list(weeks)
    if not docs:
        return None
    return {"area": key, "name": p.name if p else area, "weeks": [
        {"week": d["week"], "questions": d.get("questions", 0),
         "themes": [{"theme": t["theme"], "count": t["count"], "faq": t.get("faq", ""), "examples": t.get("examples", [])[:3]}
                    for t in d.get("themes", [])]} for d in docs]}
