"""Who gets a lead (docs/RADAR.md §5 step 9, v3): the agent whose listing matches it best; with no match, the agent with live
listings in that area who has the fewest open radar leads (so one agent is not buried); else the owner (RADAR_OWNER_AGENT_ID)."""
from typing import List, Optional

from . import places, store
from .score import Match


async def _agent_of_slug(db, slug: str) -> Optional[str]:
    doc = await db.get_collection("agent_public_profiles").find_one({"slug": slug}, {"agent_id": 1})
    return str(doc["agent_id"]) if doc and doc.get("agent_id") else None


async def _area_agents(db, area_key: Optional[str]) -> List[str]:
    p = places.get(area_key or "")
    if not p:
        return []
    items = await places.public_listings(db, p, 100)
    out: List[str] = []
    for slug in dict.fromkeys(it.agent.slug for it in items):
        agent = await _agent_of_slug(db, slug)
        if agent:
            out.append(agent)
    return out


async def assign(db, area_key: Optional[str], matches: List[Match], owner: str) -> Optional[str]:
    for m in matches:
        agent = await _agent_of_slug(db, m.agent_slug)
        if agent:
            return agent
    agents = await _area_agents(db, area_key)
    if agents:
        load = {a: await db.get_collection(store.SIGNALS).count_documents({"agent_id": a, "status": "scored", "shown": True})
                for a in agents}
        return min(agents, key=lambda a: (load[a], a))
    return owner or None
