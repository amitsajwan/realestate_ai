"""The deep mind for one lead (docs/plan/buyer-mind.md step 3): read the lead, think with the lookups, check what it wrote,
keep the brief and the buyer profile.

Collections (this module is their only writer, ARCHITECTURE §4): `lead_briefs` and `buyer_profiles`, both _id = the lead id,
the latest replacing the one before. What it reads comes through the owners' functions: the lead's card from the Inbox
(InboxService.handover_for, the same facts the agent gets when a buyer is passed), project pages from areastats, passages from
knowledge. It sends nothing.
"""
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from app.modules.areastats import pages as project_pages
from app.modules.inbox.service import InboxService
from app.modules.knowledge import vectors
from app.platform import llm as gateway
from app.platform.toolloop import run_tools

from . import brief as briefs
from . import config, profile, tools

log = logging.getLogger(__name__)

LeadReader = Callable[[str, str], Awaitable[dict]]   # (agent_id, lead_id) -> {"card": handover card, "project": chat_brief or None}


class BuyerMind:
    def __init__(self, db, llm: Any, read_lead: LeadReader, project: tools.ProjectReader, area_search: tools.AreaSearch,
                 settings: Optional[config.Settings] = None, now: Callable[[], datetime] = datetime.utcnow):
        self.briefs, self.profiles = db.get_collection("lead_briefs"), db.get_collection("buyer_profiles")
        self.llm, self.read_lead, self.now = llm, read_lead, now
        self.tools = tools.tools(project, area_search)
        self.settings = settings or config.load()

    async def think(self, agent_id: str, lead_id: str) -> dict:
        """Think about one lead now and keep the brief; the brief comes from the card alone when the model gives nothing usable.
        Raises what the lead reader raises for a lead that is not this agent's."""
        lead = await self.read_lead(agent_id, lead_id)
        card = lead.get("card") or {}
        card_text = profile.prompt_text(card)
        slug = (lead.get("project") or {}).get("slug")
        result = await run_tools(self.llm, briefs.SYSTEM, briefs.user_prompt(card_text, slug), self.tools, pipeline="buyermind",
                                 ref=lead_id, max_rounds=self.settings.max_rounds, effort=self.settings.effort)
        corpus = card_text + "\n" + result.results_text()
        brief = briefs.checked(result.answer, corpus) if result.answer else briefs.fallback(card)
        now = self.now()
        doc = {"_id": lead_id, "agent_id": agent_id, "at": now, "brief": brief, "outcome": result.outcome, "rounds": result.rounds,
               "lookups": [{"tool": c.name, "arguments": c.arguments, "ok": c.ok} for c in result.calls]}
        await self.briefs.update_one({"_id": lead_id}, {"$set": doc}, upsert=True)
        prof = profile.build(lead_id, agent_id, card, brief if brief["by"] == "mind" else None, now)
        await self.profiles.update_one({"_id": lead_id}, {"$set": prof}, upsert=True)
        if brief["problems"]:
            log.info("buyermind lead=%s kept the brief without: %s", lead_id, "; ".join(brief["problems"])[:300])
        return doc

    async def latest(self, agent_id: str, lead_id: str) -> Optional[dict]:
        return await self.briefs.find_one({"_id": lead_id, "agent_id": agent_id})

    async def profile_of(self, agent_id: str, lead_id: str) -> Optional[dict]:
        return await self.profiles.find_one({"_id": lead_id, "agent_id": agent_id})


async def _area_search(question: str) -> list:
    return await vectors.search(question, limit=tools.MAX_PASSAGES)


def build(db, llm: Any = None) -> BuyerMind:
    """The mind on the live collections: the Inbox's lead card, project pages, the knowledge search, every text provider."""
    inbox = InboxService(db)

    async def read_lead(agent_id: str, lead_id: str) -> dict:
        return await inbox.handover_for(agent_id, lead_id)

    async def project(slug: str) -> Optional[dict]:
        return await project_pages.project_page(db, slug)

    return BuyerMind(db, llm if llm is not None else gateway.default_llm(), read_lead, project, _area_search)
