"""Lead board: the owner's open buyer leads shown to signed-in agents without the buyer's name or number, so an agent can ask for
one and say what they would pay for it (owner, 2026-10-31: "we are getting leads ... agents signed in but haven't added listings.
A report of genuine leads, how old and how genuine, they see the lead but no number and name, and decide or bid. A page we can pass
the link to").

Who is on the board: a lead of an owner account that is not won, lost or passed, came in within BOARD_DAYS, and left an Indian
mobile number; a test entry (the word "test" in the name) is left out. Each card says only what helps an agent decide: the project
or area, BHK, budget, when, how they pay, where they came from, how old the lead is, and why we think the buyer is real (they wrote
back, picked up our call, gave their own budget, read many pages). Never the name, the phone, or their own words, since a buyer's
words often carry a name or a number.

A card is named by `ref`, a hash of the lead id, so the board never shows the id that opens the lead in Studio.
Asks (`lead_asks`, written only here): one per agent per lead, with an optional offer (a fee for the lead, or a share of the
brokerage when the deal closes). Offers are sealed: an agent sees how many agents asked, never what they offered; the owner sees
every ask and gives the lead to one of them, which is an ordinary pass (InboxService.pass_lead, by "board"), and the others are told
it went.
"""
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Callable, Dict, Iterable, List, Optional

from app.modules.notifications.service import notify
from app.modules.tracking import contact as contactmod
from app.modules.tracking import scoring
from app.modules.tracking.requirement import TIMELINE_LABEL, bhk_text, budget_text

from . import handover
from .service import InboxError, InboxService

log = logging.getLogger(__name__)

BOARD_DAYS = 30
MAX_LEADS = 300
MAX_NOTE = 200
MANY_PAGES = 5
OFFER_KINDS = ("none", "fee", "share")
CHANNEL_WORDS = {"whatsapp": "WhatsApp", "messenger": "Messenger", "instagram": "Instagram", "website": "the website chat"}
_TEST = re.compile(r"\btest", re.I)


def ref_of(lead_id: str) -> str:
    return hashlib.sha256(f"lead-board:{lead_id}".encode()).hexdigest()[:12]


def _age(created: datetime, now: datetime) -> str:
    days = (now - created).days
    if days <= 0:
        return "Came in today"
    return "Came in yesterday" if days == 1 else f"Came in {days} days ago"


def offer_text(kind: Optional[str], value: Optional[float]) -> Optional[str]:
    if kind == "fee" and value:
        return f"₹{int(value):,} for the lead"
    if kind == "share" and value:
        return f"{value:g}% of the brokerage on closing"
    return None


def signals(lead: dict, convs: List[dict], pages: int) -> List[str]:
    """Why we think this is a real buyer, strongest first; each one is something that happened, never a guess."""
    out = []
    wrote = [c["channel"] for c in convs for m in (c["doc"].get("messages") or []) if (m.get("role") or "") in contactmod.THEM]
    if wrote:
        out.append(f"Wrote to us on {CHANNEL_WORDS.get(wrote[-1], wrote[-1])}")
    if any(k.get("outcome") == "answered" for k in lead.get("calls") or []):
        out.append("Picked up our call")
    req = lead.get("requirement") or {}
    told = [w for w, v in (("budget", req.get("budget_min_inr") or req.get("budget_max_inr")), ("BHK", req.get("bhk")),
                           ("when", req.get("timeline"))) if v]
    if told and req.get("source") in ("stated", "mixed"):
        out.append("Told us their " + ", ".join(told) + " themselves")
    if pages >= MANY_PAGES:
        out.append(f"Read {pages} pages on the site")
    out.append("Left a mobile number")
    return out


def card(lead: dict, project: Optional[dict], convs: List[dict], pages: int, now: datetime) -> dict:
    """What an agent sees of one lead. Pure: the caller reads the lead, its project page brief, its chats and its page count."""
    req = lead.get("requirement") or {}
    areas = list(dict.fromkeys(([project["area"]] if project and project.get("area") else []) + list(req.get("localities") or [])))
    value = scoring.score(lead.get("score_base", 0), lead["last_activity_at"], now, req.get("timeline"))
    sig = signals(lead, convs, pages)
    state = contactmod.state_of(lead, convs)["state"]
    return {
        "ref": ref_of(lead["_id"]),
        "project": project["name"] if project else None,
        "areas": areas,
        "bhk": bhk_text(req.get("bhk")),
        "budget": budget_text(req.get("budget_min_inr"), req.get("budget_max_inr")),
        "when": TIMELINE_LABEL.get(req.get("timeline") or ""),
        "paying": handover.FINANCING_LABEL.get(req.get("financing") or ""),
        "wants": handover.ask_of(lead.get("message"))["want"],
        "came_from": handover.source_text(lead),
        "age": _age(lead["created_at"], now),
        "created_at": lead["created_at"],
        "last_active_at": lead["last_activity_at"],
        "temperature": scoring.temperature(value),
        # talked = they answered us (a message or a picked-up call); the rest left a number and nothing more yet
        "genuine": "talked" if (sig[0].startswith(("Wrote", "Picked")) or state == "in_touch") else "number",
        "signals": sig,
    }


def _on_board(lead: dict, since: datetime) -> bool:
    return (lead.get("stage") not in ("won", "lost") and not lead.get("passed_to") and bool(contactmod.wa_digits(lead.get("phone")))
            and isinstance(lead.get("created_at"), datetime) and lead["created_at"] >= since
            and not _TEST.search(lead.get("name") or ""))


class LeadBoard:
    def __init__(self, db, inbox: InboxService, owners: Iterable[str], now: Optional[Callable[[], datetime]] = None):
        self.db, self.inbox, self.owners = db, inbox, [o for o in owners if o]
        self.now = now or datetime.utcnow

    def c(self, name: str):
        return self.db.get_collection(name)

    def is_owner(self, user_id: str) -> bool:
        return user_id in self.owners

    async def _leads(self) -> List[dict]:
        since = self.now() - timedelta(days=BOARD_DAYS)
        rows = await self.c("contacts").find({"agent_id": {"$in": self.owners}, "created_at": {"$gte": since}}).sort(
            "created_at", -1).limit(MAX_LEADS).to_list(MAX_LEADS)
        return [r for r in rows if _on_board(r, since)]

    async def _find(self, ref: str) -> dict:
        lead = next((r for r in await self._leads() if ref_of(r["_id"]) == ref), None)
        if lead is None:
            raise InboxError("This lead is no longer on the board", 404)
        return lead

    async def cards(self, viewer: str) -> dict:
        """The board for one viewer, newest lead first. An agent sees their own ask and how many asked; the owner sees every ask
        with the offer, and the lead id to open it."""
        leads = await self._leads()
        now = self.now()
        convs = await contactmod.conversations_by_lead(self.db, leads)
        ids = [r["_id"] for r in leads]
        pages: Dict[str, set] = {i: set() for i in ids}
        for e in await self.c("events").find({"contact_id": {"$in": ids}}, {"contact_id": 1, "path": 1}).to_list(20000):
            if e.get("path"):
                pages[e["contact_id"]].add(e["path"].split("?")[0])
        asks: Dict[str, List[dict]] = {i: [] for i in ids}
        for a in await self.c("lead_asks").find({"lead_id": {"$in": ids}, "status": "open"}).to_list(2000):
            asks[a["lead_id"]].append(a)
        owner = self.is_owner(viewer)
        names = await self._names({a["agent_id"] for rows in asks.values() for a in rows}) if owner else {}
        out = []
        for lead in leads:
            row = card(lead, await self.inbox.project_of(lead), convs[lead["_id"]], len(pages[lead["_id"]]), now)
            mine = next((a for a in asks[lead["_id"]] if a["agent_id"] == viewer), None)
            row["asked"] = len(asks[lead["_id"]])
            row["mine"] = self._ask_view(mine) if mine else None
            if owner:
                row["lead_id"] = lead["_id"]
                row["asks"] = [{**self._ask_view(a), "agent_id": a["agent_id"], "agent_name": names.get(a["agent_id"], "Agent")}
                               for a in sorted(asks[lead["_id"]], key=lambda a: a["at"])]
            out.append(row)
        return {"items": out, "owner": owner, "days": BOARD_DAYS}

    @staticmethod
    def _ask_view(a: dict) -> dict:
        return {"offer_kind": a.get("offer_kind") or "none", "offer_value": a.get("offer_value"),
                "offer": offer_text(a.get("offer_kind"), a.get("offer_value")), "note": a.get("note"), "at": a["at"]}

    async def _names(self, agent_ids) -> Dict[str, str]:
        rows = await self.c("agent_public_profiles").find({"agent_id": {"$in": list(agent_ids)}}).to_list(500)
        return {str(p["agent_id"]): self.inbox._agent_name(p) for p in rows}

    async def ask(self, agent_id: str, ref: str, offer_kind: str = "none", offer_value: Optional[float] = None,
                  note: Optional[str] = None) -> dict:
        """An agent asks for a lead (asking again changes their offer). The owner gets a Studio alert."""
        if self.is_owner(agent_id):
            raise InboxError("These are your own leads. Give one to an agent from its card.", 409)
        prof = await self.inbox._live_agent(agent_id)   # a lead can only be passed to an agent with a live page
        if offer_kind not in OFFER_KINDS:
            raise InboxError("Unknown offer", 422)
        if offer_kind == "share" and not (offer_value and 0 < offer_value <= 100):
            raise InboxError("A share is a percent between 1 and 100", 422)
        if offer_kind == "fee" and not (offer_value and 0 < offer_value <= 1_000_000):
            raise InboxError("Say the fee in rupees", 422)
        lead = await self._find(ref)
        now = self.now()
        rid = f"{lead['_id']}:{agent_id}"
        doc = {"lead_id": lead["_id"], "owner_id": lead["agent_id"], "agent_id": agent_id, "status": "open",
               "offer_kind": offer_kind, "offer_value": offer_value if offer_kind != "none" else None,
               "note": (note or "").strip()[:MAX_NOTE] or None, "at": now}
        if await self.c("lead_asks").find_one({"_id": rid}):
            await self.c("lead_asks").update_one({"_id": rid}, {"$set": doc})
        else:
            await self.c("lead_asks").insert_one({"_id": rid, **doc})
        row = card(lead, await self.inbox.project_of(lead), [], 0, now)
        what = " · ".join(p for p in (row["bhk"], row["project"] or ", ".join(row["areas"][:2])) if p) or "a buyer"
        offer = offer_text(doc["offer_kind"], doc["offer_value"])
        await notify(self.db, lead["agent_id"], "lead_asked",
                     f"{self.inbox._agent_name(prof)} asked for the lead ({what}){': ' + offer if offer else ''}.",
                     {"screen": "/studio/lead-board", "lead_id": lead["_id"]}, now)
        return self._ask_view(doc)

    async def withdraw(self, agent_id: str, ref: str) -> dict:
        lead = await self._find(ref)
        await self.c("lead_asks").delete_one({"_id": f"{lead['_id']}:{agent_id}", "status": "open"})
        return {"ok": True}

    async def give(self, owner_id: str, ref: str, agent_id: str) -> dict:
        """The owner gives the lead to an agent who asked: the usual pass (lead, chats, card on WhatsApp); every other ask on it
        closes and those agents get a Studio alert."""
        if not self.is_owner(owner_id):
            raise InboxError("Only the owner gives leads", 403)
        lead = await self._find(ref)
        if lead["agent_id"] != owner_id:
            raise InboxError("This lead is in another owner account", 409)
        chosen = await self.c("lead_asks").find_one({"_id": f"{lead['_id']}:{agent_id}", "status": "open"})
        if not chosen:
            raise InboxError("That agent has not asked for this lead", 404)
        result = await self.inbox.pass_lead(owner_id, lead["_id"], agent_id, by="board")
        now = self.now()
        for a in await self.c("lead_asks").find({"lead_id": lead["_id"], "status": "open"}).to_list(200):
            won = a["agent_id"] == agent_id
            await self.c("lead_asks").update_one({"_id": a["_id"]}, {"$set": {"status": "given" if won else "closed", "closed_at": now}})
            if not won:
                await notify(self.db, a["agent_id"], "lead_ask_closed",
                             "A lead you asked for on the lead board went to another agent. New leads come up on the board every day.",
                             {"screen": "/studio/lead-board"}, now)
        log.info("lead board: %s given to %s", lead["_id"], agent_id)
        return result
