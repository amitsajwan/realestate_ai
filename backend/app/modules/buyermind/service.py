"""The deep mind for one lead (docs/plan/buyer-mind.md step 3): read the lead, think with the lookups, check what it wrote,
keep the brief and the buyer profile.

Collections (this module is their only writer, ARCHITECTURE §4): `lead_briefs` and `buyer_profiles`, both _id = the lead id,
the latest replacing the one before. What it reads comes through the owners' functions: the lead's card from the Inbox
(InboxService.handover_for, the same facts the agent gets when a buyer is passed), project pages from areastats, passages from
knowledge. It sends nothing.
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Optional

from app.modules.areastats import pages as project_pages
from app.modules.inbox.service import InboxService
from app.modules.knowledge import vectors
from app.platform import llm as gateway
from app.platform.toolloop import run_tools

from . import brief as briefs
from . import config, profile, tools

log = logging.getLogger(__name__)

HAND_GAP = timedelta(minutes=2)
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

    async def think_if_due(self, agent_id: str, lead_id: str, since: Optional[datetime]) -> str:
        """The background run (inbox.followups, through app.wiring): think again only when something happened after the last
        brief (`since`: the lead came in or the buyer wrote). 'off' with BUYER_MIND unset, 'fresh' when the brief is newer,
        'thought' when it thought."""
        if not self.settings.enabled:
            return "off"
        last = await self.briefs.find_one({"_id": lead_id})
        if last and since and last.get("at") and last["at"] >= since:
            return "fresh"
        await self.think(agent_id, lead_id)
        return "thought"

    async def think_by_hand(self, agent_id: str, lead_id: str) -> dict:
        """'Think about this lead' in Studio: works with BUYER_MIND off, so the owner can try it on real leads first. Once per
        HAND_GAP a lead, since each run is several model calls."""
        last = await self.briefs.find_one({"_id": lead_id, "agent_id": agent_id})
        if last and last.get("at") and self.now() - last["at"] < HAND_GAP:
            raise TooSoon(int((HAND_GAP - (self.now() - last["at"])).total_seconds()) + 1)
        await self.think(agent_id, lead_id)
        return await self.view(agent_id, lead_id)

    async def view(self, agent_id: str, lead_id: str) -> dict:
        """The brief and the profile as Studio shows them; nulls when the mind has not thought about this lead yet."""
        doc = await self.briefs.find_one({"_id": lead_id, "agent_id": agent_id})
        prof = await self.profiles.find_one({"_id": lead_id, "agent_id": agent_id})
        return {"brief": (doc or {}).get("brief"), "at": _iso((doc or {}).get("at")), "outcome": (doc or {}).get("outcome"),
                "lookups": [x["tool"] for x in (doc or {}).get("lookups") or [] if x.get("ok")],
                "profile": {k: prof.get(k) for k in ("said", "implied", "unknown")} if prof else None}


# what a chat may tell the buyer from the mind's brief (docs/plan/buyer-mind.md step 4): only what the checks held to a lookup
BRIEF_FRESH = timedelta(days=7)        # prices and dates move; an older brief is not said to a buyer
MAX_CHAT_FACTS = 6


async def chat_facts(db, lead_id: Optional[str], now: Optional[datetime] = None) -> list[str]:
    """The lead's latest brief as facts the chat may say to the buyer, for WhatsApp and DMs (through app.wiring): the problems to
    tell them, the published price range and the other projects it looked up. Nothing when there is no lead, the brief came from
    the rules (no model), the mind was not sure, or the brief is older than BRIEF_FRESH. What it read into the buyer ("implied")
    and the agent's draft never go to the buyer."""
    if not lead_id:
        return []
    doc = await db.get_collection("lead_briefs").find_one({"_id": lead_id})
    b = (doc or {}).get("brief") or {}
    at = (doc or {}).get("at")
    if b.get("by") != "mind" or b.get("confidence") == "low" or not isinstance(at, datetime) or (now or datetime.utcnow()) - at > BRIEF_FRESH:
        return []
    out = [f"To tell them: {f}" for f in b.get("flags") or []]
    if b.get("price_idea"):
        out.append(f"Published prices (indicative, not a quote): {b['price_idea']}")
    names = [a.get("name") or a.get("slug") for a in b.get("alternatives") or [] if a.get("slug")]
    if names:
        out.append("Other projects in the area our team looked up for them: " + ", ".join(n for n in names if n))
    return [ISO_DAY.sub(_spoken_day, x) for x in out[:MAX_CHAT_FACTS]]


ISO_DAY = re.compile(r"\b(20\d\d)-(0[1-9]|1[0-2])-([0-3]\d)\b")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def _spoken_day(m: "re.Match") -> str:
    """2026-10-20 -> 20 October 2026: how a buyer reads a date, and the month's name lets the chat's checks accept "20 Oct"."""
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(1)}"


class TooSoon(Exception):
    def __init__(self, wait_s: int):
        super().__init__(f"Thought about this lead a moment ago; try again in {wait_s} s")
        self.wait_s = wait_s


def _iso(dt: Any) -> Optional[str]:
    return dt.isoformat() + "Z" if isinstance(dt, datetime) else None


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
