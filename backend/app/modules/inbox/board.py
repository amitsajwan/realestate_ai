"""Lead board: the owner's open buyer leads shown to signed-in agents without the buyer's name or number, so an agent can ask for
one and say what they would pay for it (owner, 2026-10-31: "we are getting leads ... agents signed in but haven't added listings.
A report of genuine leads, how old and how genuine, they see the lead but no number and name, and decide or bid. A page we can pass
the link to").

Who is on the board (owner, 2026-10-31: "show all leads even if they are passed to House Deal before, we will manage leads from
there"): every lead of an owner account, and every lead the owner passed to an agent (by hand, by a rule or from the board), at
any age, unless the deal is won. A lost lead stays, marked lost (another agent may still serve it). A lead with no mobile number
stays when it says what they want (a BHK, budget, area or date); a comment or hello with nothing more is a conversation and lives
in the Inbox. Every lead reads as open, whoever had it before (owner, 2026-10-31: "start from scratch, as if nothing shared"):
any agent, the holder too, can ask, and no card says who has it or how far our follow-up got ("think how it can be sold, not
information that is not required"). Giving it moves it from the holder to the new agent (or leaves it with the holder, if they
are the one given it).

Left out: any lead whose number is ours or an agent's (every Studio sign-in, every agent page's number and office number, our
WhatsApp line and the owner's own mobile; owner, 2026-10-31: "remove leads which have any phone numbers we know"), and, of the
owner's own leads, an enquiry from a signed-in Studio browser (its events are marked staff) or one with "test" in the name.
Anything else the owner takes off with "Remove from board" (`lead_board_off`, written only here).

Each card says only what helps an agent decide: the project or area, BHK, budget, when, how they pay, where they came from, how
old the lead is, why we think the buyer is real (they wrote back, picked up our call, gave their own budget, came back on other
days, compared projects), and what they did on the site (owner, 2026-10-31: "what the visitor was checking, what pages, anything
that helps agents decide"): the pages in order with reading time, visits and days, phone or computer, the city of the visit, taps
on WhatsApp or call. Never the name, the phone, or their own words, since a buyer's words often carry a name or a number.

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

from app.core import brand
from app.modules.areastats import pages as project_pages
from app.modules.notifications.service import notify
from app.modules.tracking import contact as contactmod
from app.modules.tracking import live, scoring
from app.modules.tracking.requirement import TIMELINE_LABEL, bhk_text, budget_text

from . import handover
from .service import InboxError, InboxService, _lead_digits

log = logging.getLogger(__name__)

MAX_LEADS = 500
# the viewer id of "View as an agent": an agent who holds nothing and asked for nothing (owner, 2026-10-31: "I cannot view it
# myself, as I am always logged in, I need a third party view")
PREVIEW = "agent-preview"
# our own numbers that may sit on no account (owner's personal mobile, our WhatsApp line); agents' come from their pages
OUR_NUMBERS = ("+919767971656", "+919834256406")
MAX_NOTE = 200
MANY_PAGES = 5
OFFER_KINDS = ("none", "fee", "share")
CHANNEL_WORDS = {"whatsapp": "WhatsApp", "messenger": "Messenger", "instagram": "Instagram", "website": "the website chat"}
_TEST = re.compile(r"\btest", re.I)
MAX_PAGES = 8
NAMES_TTL = timedelta(hours=1)
IST = timedelta(hours=5, minutes=30)
AGENT_PAGES = handover.AGENT_PAGES
_SKIP = handover.SKIP_PAGES
_PROJECT = re.compile(r"^/projects/([a-z0-9-]+)/?$")
_names: Dict[str, tuple] = {}   # project page slug -> (name, read at, area): a board read every 30 s must not re-read the register
DEMAND_DAYS = 7
DEMAND_TTL = timedelta(minutes=10)
MAX_DEMAND_EVENTS = 50000
_demand: Dict[str, tuple] = {}  # owners key -> (demand, read at)


def _title(slug: str) -> str:
    return slug.replace("-", " ").strip().title()


def _path(e: dict) -> str:
    return (e.get("path") or "").split("?")[0].split("#")[0]


def page_label(path: str, names: Dict[str, str]) -> Optional[str]:
    """A page as a person names it: 'Mansha Phase-II', 'Kharadi projects (2 BHK)', 'Upper Kharadi area guide'. None for pages that
    say nothing about what a buyer wants (an agent's own site, the enquiry form, a short link, our pages for agents)."""
    path = path.split("?")[0].split("#")[0].rstrip("/") or "/"
    if path.startswith(_SKIP) or path.startswith(AGENT_PAGES):
        return None
    fixed = {"/": "Home page", "/projects": "All projects", "/localities": "Areas list", "/news": "News", "/builders": "Builders",
             "/check": "MahaRERA project check", "/insights": "Market insights"}
    if path in fixed:
        return fixed[path]
    parts = path.strip("/").split("/")
    if parts[0] == "projects" and len(parts) >= 3 and parts[1] == "area":
        extra = ("top picks" if parts[3] == "top" else parts[3].upper().replace("-", " ")) if len(parts) > 3 else None
        return f"{_title(parts[2])} projects" + (f" ({extra})" if extra else "")
    if parts[0] == "projects" and len(parts) == 2:
        return names.get(parts[1]) or _title(parts[1])
    if parts[0] == "localities" and len(parts) == 2:
        return f"{_title(parts[1])} area guide"
    if parts[0] in ("1-bhk", "2-bhk", "3-bhk") and len(parts) >= 2:
        return f"{parts[0][0]} BHK in {_title(parts[1])}"
    prefix = {"news": "News", "guides": "Guide", "builders": "Builder"}.get(parts[0])
    if prefix and len(parts) >= 2:
        return f"{prefix}: {_title(parts[-1])}"
    return _title(parts[-1])


def _took(start: datetime, end: datetime) -> str:
    """'40 minutes', '2 hours', '3 days'."""
    mins = max(1, int((end - start).total_seconds() // 60))
    if mins < 60:
        return f"{mins} minute{'s' if mins != 1 else ''}"
    hours = mins // 60
    if hours < 48:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    return f"{hours // 24} days"


def _device(label: Optional[str]) -> Optional[str]:
    low = (label or "").lower()
    if not low:
        return None
    if "ipad" in low or "tablet" in low:
        return "Tablet"
    return "Phone" if ("phone" in low or "android" in low) else "Computer"


def activity(events: List[dict], names: Dict[str, str]) -> dict:
    """What they did on the site, from their events (any order). Robot views are dropped."""
    evs = sorted((e for e in events if not e.get("robot") and isinstance(e.get("ts"), datetime)), key=lambda e: e["ts"])
    views = [e for e in evs if e["type"] in live.VIEW_TYPES]
    pages: Dict[str, dict] = {}
    for e in views:
        label = page_label(_path(e), names)
        if label:
            row = pages.setdefault(label, {"label": label, "read_s": 0})
            row["read_s"] += e.get("read_s") or 0
    last = next((e for e in reversed(views) if e.get("device") or e.get("area")), {})
    return {
        "pages": [{"label": r["label"], "minutes": round(r["read_s"] / 60)} for r in list(pages.values())[:MAX_PAGES]],
        "more_pages": max(0, len(pages) - MAX_PAGES),
        "page_count": len(pages),
        "projects_seen": len({_path(e).rstrip("/") for e in views if _PROJECT.match(_path(e))}),
        "visits": len(live.visits_of(views)),
        "days": len({(e["ts"] + IST).date() for e in views}),
        "read_min": round(sum(e.get("read_s") or 0 for e in views) / 60),
        "device": _device(last.get("device")),
        "city": (last.get("area") or "").split(",")[0] or None,
        "taps": [live.ACTIONS[t] for t in ("whatsapp_click", "call_click", "share") if any(e["type"] == t for e in evs)],
        "enquiries": sum(1 for e in evs if e["type"] == "inquiry"),
        "agent_pages": any(_path(e).startswith(AGENT_PAGES) for e in views),
    }


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


def signals(lead: dict, convs: List[dict], act: dict) -> List[str]:
    """Why we think this is a real buyer, strongest first; each one is something that happened, never a guess."""
    out = []
    wrote = [c["channel"] for c in convs for m in (c["doc"].get("messages") or []) if (m.get("role") or "") in contactmod.THEM]
    if wrote:
        n = len(wrote)
        out.append(f"Replied to us on {CHANNEL_WORDS.get(wrote[-1], wrote[-1])}" + (f" ({n} messages)" if n > 1 else ""))
    if any(k.get("outcome") == "answered" for k in lead.get("calls") or []):
        out.append("Picked up our call")
    req = lead.get("requirement") or {}
    told = [w for w, v in (("budget", req.get("budget_min_inr") or req.get("budget_max_inr")), ("BHK", req.get("bhk")),
                           ("when", req.get("timeline"))) if v]
    if told and req.get("source") in ("stated", "mixed"):
        out.append("Told us their " + ", ".join(told) + " themselves")
    if act["days"] > 1:
        out.append(f"Came back on {act['days']} different days")
    if act["enquiries"] > 1:
        out.append(f"Sent {act['enquiries']} enquiries")
    if act["projects_seen"] > 1:
        out.append(f"Compared {act['projects_seen']} projects")
    elif act["page_count"] >= MANY_PAGES:
        out.append(f"Read {act['page_count']} pages on the site")
    if act["taps"]:
        out.append(", ".join(act["taps"]))
    out.append("Left a mobile number" if contactmod.wa_digits(lead.get("phone")) else "No number yet: reached us on "
               + (handover.source_text(lead) if lead.get("source") else "the website"))
    return out


def card(lead: dict, project: Optional[dict], convs: List[dict], events: List[dict], names: Dict[str, str], now: datetime) -> dict:
    """What an agent sees of one lead. Pure: the caller reads the lead, its project page brief, its chats, its events and the
    names of the project pages in them."""
    req = lead.get("requirement") or {}
    areas = list(dict.fromkeys(([project["area"]] if project and project.get("area") else []) + list(req.get("localities") or [])))
    value = scoring.score(lead.get("score_base", 0), lead["last_activity_at"], now, req.get("timeline"))
    act = activity(events, names)
    sig = signals(lead, convs, act)
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
        # called = a call to them was answered (a person spoke with them); replied = they wrote back to our message (2026-10-31: five
        # leads read "spoke with us" for replying "Yes" or "Katraj" to our WhatsApp bot, and nobody had called any of them)
        "genuine": ("called" if any(k.get("outcome") == "answered" for k in lead.get("calls") or [])
                    else "replied" if sig[0].startswith("Replied")
                    else "number" if contactmod.wa_digits(lead.get("phone")) else "no_number"),
        "signals": sig,
        "activity": {k: v for k, v in act.items() if k != "agent_pages"},
        # they opened our pages for agents: worth a look before paying for it (an agent trying the form, not a buyer)
        "caution": "Also opened our pages for agents: may be an agent, not a buyer" if act["agent_pages"] else None,
    }


def _wants_something(lead: dict) -> bool:
    """A BHK, budget, area or date they gave. A comment's text alone is not one (the Studio Leads list draws the same line)."""
    req = {k: v for k, v in (lead.get("requirement") or {}).items() if k != "source"}
    return any(req.values())


def _on_board(lead: dict) -> bool:
    return (lead.get("stage") != "won" and isinstance(lead.get("created_at"), datetime) and isinstance(lead.get("last_activity_at"), datetime)
            and (bool(contactmod.wa_digits(lead.get("phone"))) or _wants_something(lead)))


class LeadBoard:
    def __init__(self, db, inbox: InboxService, owners: Iterable[str], now: Optional[Callable[[], datetime]] = None):
        self.db, self.inbox, self.owners = db, inbox, [o for o in owners if o]
        self.now = now or datetime.utcnow

    def c(self, name: str):
        return self.db.get_collection(name)

    def is_owner(self, user_id: str) -> bool:
        return user_id in self.owners

    async def _leads(self) -> List[dict]:
        rows = await self.c("contacts").find({"$or": [{"agent_id": {"$in": self.owners}}, {"passed_by": {"$in": self.owners}}]}).sort(
            "created_at", -1).limit(MAX_LEADS).to_list(MAX_LEADS)
        rows = [r for r in rows if _on_board(r)]
        off = {d["_id"] for d in await self.c("lead_board_off").find({"_id": {"$in": [r["_id"] for r in rows]}}).to_list(MAX_LEADS)}
        known = await self._known_numbers()
        # an enquiry from a signed-in Studio browser (its events are marked staff) is one of us trying the form; a passed lead
        # was looked at when it was passed, so only its number counts
        own = [r["_id"] for r in rows if not r.get("passed_by")]
        staff = {e["contact_id"] for e in await self.c("events").find(
            {"contact_id": {"$in": own}, "staff": True}, {"contact_id": 1}).to_list(MAX_LEADS * 20)}

        def test(r: dict) -> bool:
            return (contactmod.wa_digits(r.get("phone")) in known
                    or not r.get("passed_by") and (r["_id"] in staff or bool(_TEST.search(r.get("name") or ""))))
        return [r for r in rows if r["_id"] not in off and not test(r)]

    async def _project_names(self, events: List[dict]) -> Dict[str, str]:
        """The names shown on the project pages in these events; one register read per slug an hour."""
        now = self.now()
        slugs = {m.group(1) for m in (_PROJECT.match(_path(e)) for e in events) if m}
        for slug in slugs:
            if slug not in _names or now - _names[slug][1] > NAMES_TTL:
                brief = await project_pages.chat_brief(self.db, slug)
                _names[slug] = (brief["name"] if brief else None, now, brief.get("area") if brief else None)
        return {slug: _names[slug][0] for slug in slugs if _names[slug][0]}

    async def _area_of(self, path: str) -> Optional[str]:
        """The area a page is about: a project page's area, an area list or an area guide; None for other pages."""
        parts = path.split("?")[0].strip("/").split("/")
        if len(parts) >= 3 and parts[:2] == ["projects", "area"]:
            return _title(parts[2])
        if len(parts) == 2 and parts[0] == "localities":
            return _title(parts[1])
        if len(parts) == 2 and parts[0] == "projects":
            await self._project_names([{"path": path}])
            return (_names.get(parts[1]) or (None, None, None))[2]
        return None

    async def demand(self) -> dict:
        """What buyers did on our pages in the last DEMAND_DAYS, from the events (robots and our own signed-in browsers left out):
        people who read our pages, enquiries sent, and per area the people who read its pages and the enquiries made on them
        (owner, 2026-10-31: the board should look like a working system; this is the real activity behind it, never made up)."""
        now = self.now()
        key = ",".join(sorted(self.owners))
        if key in _demand and now - _demand[key][1] < DEMAND_TTL:
            return _demand[key][0]
        since = now - timedelta(days=DEMAND_DAYS)
        rows = await self.c("events").find({"agent_id": {"$in": self.owners}, "ts": {"$gte": since},
                                            "type": {"$in": live.VIEW_TYPES + ["inquiry"]}},
                                           {"anon_id": 1, "path": 1, "type": 1, "robot": 1, "staff": 1}).to_list(MAX_DEMAND_EVENTS)
        skip = {e.get("anon_id") for e in rows if e.get("robot") or e.get("staff")}
        rows = [e for e in rows if e.get("anon_id") and e["anon_id"] not in skip]
        readers: Dict[str, set] = {}
        asked: Dict[str, int] = {}
        for e in rows:
            area = await self._area_of(_path(e))
            if not area:
                continue
            if e["type"] == "inquiry":
                asked[area] = asked.get(area, 0) + 1
            else:
                readers.setdefault(area, set()).add(e["anon_id"])
        areas = [{"area": a, "readers": len(r), "enquiries": asked.get(a, 0)} for a, r in readers.items()]
        out = {"days": DEMAND_DAYS,
               "visitors": len({e["anon_id"] for e in rows if e["type"] != "inquiry"}),
               "enquiries": sum(1 for e in rows if e["type"] == "inquiry"),
               "areas": sorted(areas, key=lambda r: (-r["readers"], -r["enquiries"], r["area"]))[:8]}
        _demand[key] = (out, now)
        return out

    async def _known_numbers(self) -> set:
        """Every number that is ours or an agent's, as 12-digit 91... strings: Studio sign-ins, agent pages (their number and
        office number: House Deal's team WhatsApp), our public WhatsApp and the owner's own (owner, 2026-10-31: "remove leads which
        have any phone numbers we know, like Avasetu 9767971656, House Deal, or any agent numbers")."""
        found = [u.get("phone") for u in await self.c("users").find({"phone": {"$nin": [None, ""]}}, {"phone": 1}).to_list(5000)]
        for p in await self.c("agent_public_profiles").find({}, {"phone": 1, "branding_data": 1}).to_list(5000):
            b = p.get("branding_data") or {}
            found += [p.get("phone"), b.get("office_phone"), b.get("whatsapp"), b.get("whatsapp_number"), b.get("phone")]
        found += [brand.posts_whatsapp_number(), *OUR_NUMBERS]
        return {contactmod.wa_digits(n) for n in found} - {None}

    async def remove(self, owner_id: str, ref: str) -> dict:
        """The owner takes a lead off the board (a test, or one they keep for themselves). Open asks on it close quietly."""
        if not self.is_owner(owner_id):
            raise InboxError("Only the owner removes leads", 403)
        lead = await self._find(ref)
        now = self.now()
        await self.c("lead_board_off").insert_one({"_id": lead["_id"], "by": owner_id, "at": now})
        for a in await self.c("lead_asks").find({"lead_id": lead["_id"], "status": "open"}).to_list(200):
            await self.c("lead_asks").update_one({"_id": a["_id"]}, {"$set": {"status": "removed", "closed_at": now}})
        return {"ok": True}

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
        # their events: those tied to the lead, and the same browsers' visits that were not (before the enquiry on another page,
        # or after it)
        events: Dict[str, List[dict]] = {i: [] for i in ids}
        by_anon = {a: r["_id"] for r in leads for a in r.get("anon_ids") or []}
        rows = await self.c("events").find({"$or": [{"contact_id": {"$in": ids}}, {"anon_id": {"$in": list(by_anon)}}]}, {
            "contact_id": 1, "anon_id": 1, "path": 1, "type": 1, "ts": 1, "last_seen": 1, "read_s": 1, "device": 1, "area": 1,
            "robot": 1}).to_list(20000)
        for e in rows:
            lid = e.get("contact_id") if e.get("contact_id") in events else by_anon.get(e.get("anon_id"))
            if lid in events:
                events[lid].append(e)
        names = await self._project_names(rows)
        asks: Dict[str, List[dict]] = {i: [] for i in ids}
        for a in await self.c("lead_asks").find({"lead_id": {"$in": ids}, "status": "open"}).to_list(2000):
            asks[a["lead_id"]].append(a)
        owner = self.is_owner(viewer)
        agents = await self._names({a["agent_id"] for rows in asks.values() for a in rows}) if owner else {}
        out = []
        for lead in leads:
            row = card(lead, await self.inbox.project_of(lead), convs[lead["_id"]], events[lead["_id"]], names, now)
            mine = next((a for a in asks[lead["_id"]] if a["agent_id"] == viewer), None)
            # given from the board to another agent: the others see how fast it went, and cannot ask any more
            h = lead.get("handover") or {}
            row["given"] = (f"Given to an agent {_took(lead['created_at'], h['at'])} after it came in"
                            if h.get("by") == "board" and isinstance(h.get("at"), datetime) and lead["agent_id"] != viewer and not owner
                            else None)
            row["asked"] = len(asks[lead["_id"]])
            row["mine"] = self._ask_view(mine) if mine else None
            if owner:
                row["lead_id"] = lead["_id"]
                row["asks"] = [{**self._ask_view(a), "agent_id": a["agent_id"], "agent_name": agents.get(a["agent_id"], "Agent")}
                               for a in sorted(asks[lead["_id"]], key=lambda a: a["at"])]
            out.append(row)
        new_week = sum(1 for r in leads if now - r["created_at"] <= timedelta(days=DEMAND_DAYS))
        return {"items": out, "owner": owner, "preview": viewer == PREVIEW, "demand": {**await self.demand(), "new_leads": new_week}}

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
        owner = self._owner_of(lead)
        now = self.now()
        rid = f"{lead['_id']}:{agent_id}"
        doc = {"lead_id": lead["_id"], "owner_id": owner, "agent_id": agent_id, "status": "open",
               "offer_kind": offer_kind, "offer_value": offer_value if offer_kind != "none" else None,
               "note": (note or "").strip()[:MAX_NOTE] or None, "at": now}
        if await self.c("lead_asks").find_one({"_id": rid}):
            await self.c("lead_asks").update_one({"_id": rid}, {"$set": doc})
        else:
            await self.c("lead_asks").insert_one({"_id": rid, **doc})
        row = card(lead, await self.inbox.project_of(lead), [], [], {}, now)
        what = " · ".join(p for p in (row["bhk"], row["project"] or ", ".join(row["areas"][:2])) if p) or "a buyer"
        offer = offer_text(doc["offer_kind"], doc["offer_value"])
        await notify(self.db, owner, "lead_asked",
                     f"{self.inbox._agent_name(prof)} asked for the lead ({what}){': ' + offer if offer else ''}.",
                     {"screen": "/studio/lead-board", "lead_id": lead["_id"]}, now)
        return self._ask_view(doc)

    def _owner_of(self, lead: dict) -> str:
        """The owner whose lead it is: the account it is in, or the one that passed it on."""
        return lead["agent_id"] if lead["agent_id"] in self.owners else lead.get("passed_by") or lead["agent_id"]

    async def agents(self, owner_id: str) -> List[dict]:
        """The live agents the owner can send the board to from their own WhatsApp (owner, 2026-10-31: "if I send from my personal
        number, how will I get the agent list; there should be a button to select agents"), with their WhatsApp digits, how many
        listings they have (the ones with none are who the board is for) and whether they asked for a lead yet."""
        if not self.is_owner(owner_id):
            raise InboxError("Only the owner sends the board", 403)
        rows = []
        for a in await self.inbox.agents(owner_id):
            prof = await self.c("agent_public_profiles").find_one({"agent_id": a["agent_id"]}) or {}
            digits = _lead_digits(prof)
            if not digits:
                continue
            rows.append({"agent_id": a["agent_id"], "name": a["name"], "first_name": (prof.get("agent_name") or a["name"]).split()[0].title(),
                         "whatsapp": digits, "listings": await self.c("listings").count_documents({"agent_id": a["agent_id"]}),
                         "asked": await self.c("lead_asks").count_documents({"agent_id": a["agent_id"]})})
        return sorted(rows, key=lambda r: (r["listings"] > 0, r["name"].lower()))

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
        passed = lead["agent_id"] not in self.owners
        if not passed and lead["agent_id"] != owner_id or passed and lead.get("passed_by") != owner_id:
            raise InboxError("This lead is in another owner account", 409)
        chosen = await self.c("lead_asks").find_one({"_id": f"{lead['_id']}:{agent_id}", "status": "open"})
        if not chosen:
            raise InboxError("That agent has not asked for this lead", 404)
        now = self.now()
        if lead["agent_id"] == agent_id:
            # they had it from before: it stays with them, now as given from the board
            await self.c("contacts").update_one({"_id": lead["_id"]}, {"$set": {"handover.by": "board", "handover.at": now}})
            name = (await self._names([agent_id])).get(agent_id, "the agent")
            result = {"passed_to": name, "lead_id": lead["_id"], "card": {"text": "", "lines": [], "missing": []},
                      "whatsapp_status": None, "whatsapp_error": None, "rule_added": None, "whatsapp_url": None}
        else:
            # a lead passed before moves on from the agent who has it, and stays the owner's pass (Leads > Passed)
            result = await self.inbox.pass_lead(lead["agent_id"], lead["_id"], agent_id, by="board")
            if passed:
                await self.c("contacts").update_one({"_id": result["lead_id"]}, {"$set": {"passed_by": owner_id}})
        for a in await self.c("lead_asks").find({"lead_id": lead["_id"], "status": "open"}).to_list(200):
            won = a["agent_id"] == agent_id
            await self.c("lead_asks").update_one({"_id": a["_id"]}, {"$set": {"status": "given" if won else "closed", "closed_at": now}})
            if not won:
                await notify(self.db, a["agent_id"], "lead_ask_closed",
                             "A lead you asked for on the lead board went to another agent. New leads come up on the board every day.",
                             {"screen": "/studio/lead-board"}, now)
        log.info("lead board: %s given to %s", lead["_id"], agent_id)
        return result
