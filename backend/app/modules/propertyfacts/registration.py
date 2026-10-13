"""PF-2: find a listing's MahaRERA registration and read its official facts.

Our own project register (newsroom `projects`, kept fresh by the area sweep in areastats.refresh: completion dates and homes
booked re-read every 30 days) is asked first; MahaRERA itself only when the register lacks the project or its details are stale.
The register is read-only here: it feeds the area stats and the newsroom, so out-of-area projects are not written into it.

MahaRERA's public search filters by project name (verified 2026-10-06; its `regno` filter is ignored), so a listing is matched
by name, then told apart from same-named projects by its registration number or its taluka. A wrong match would put another
project's dates on a post, so anything unclear is left unmatched and says why."""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, List, Optional, Tuple
from urllib.parse import quote

from app.modules.agentprojects.maharera import MahaReraError, parse_general
from app.modules.newsroom.register import maharera_id
from app.modules.newsroom.sources.maharera import PUNE_DISTRICT, SEARCH, parse_projects, parse_total
from app.modules.newsroom.types import MahaReraProject
from app.platform import trace

from .facts import Reading
from .place import Place

log = logging.getLogger(__name__)

GetText = Callable[[str], Awaitable[str]]                 # url -> body text
FetchGeneral = Callable[[int], Awaitable[Optional[dict]]]  # MahaRERA internal id -> general-details answer
REGISTER_FRESH_DAYS = 45  # the sweep re-reads details every 30 days; allow a margin before going to MahaRERA ourselves
TRIES = 4
RETRY_DELAY = 3.0  # seconds, grows per try; tests set it to 0 (the site fails in bursts of several seconds)


@dataclass
class Match:
    project: Optional[MahaReraProject]
    how: str                                    # why this one, or why none
    candidates: List[MahaReraProject] = field(default_factory=list)


def search_url(name: str, district: int = PUNE_DISTRICT) -> str:
    # spaces must be %20: the site finds nothing for "gulmohar+city" (verified 2026-10-06)
    return SEARCH.format(district=district, page=1).replace("project_name=", "project_name=" + quote(name.strip(), safe=""))


def _words(s: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (s or "").lower()))


GENERIC = {"plots", "plot", "na", "phase", "layout", "project", "projects", "wing", "wings", "apartment", "apartments",
           "bungalows", "villas", "row", "houses", "the", "i", "ii", "iii", "1", "2", "3", "a", "b", "c"}


def core(s: str) -> str:
    """The name without generic words ("Gulmohar City Plots" -> "gulmohar city"), for close matches only."""
    return " ".join(w for w in _words(s).split() if w not in GENERIC)


def same_name(a: MahaReraProject, name: str) -> bool:
    return _words(a.name) == _words(name)


def choose(projects: List[MahaReraProject], name: str, rera_no: str = "", place: Optional[Place] = None) -> Match:
    rera_no = (rera_no or "").strip().upper()
    if rera_no:
        hit = [p for p in projects if p.regno.upper() == rera_no]
        if hit:
            return Match(hit[0], "registration number", projects)
    named = [p for p in projects if same_name(p, name)]
    if rera_no:
        return Match(None, f"{rera_no} is not among MahaRERA's projects named {name!r}", named)
    if not named:
        return Match(None, f"no MahaRERA project named {name!r} in Pune district", projects)
    if len(named) == 1:
        return Match(named[0], "the only MahaRERA project with this name in Pune district", named)
    if place and place.taluka:
        local = [p for p in named if _words(p.location) == _words(place.taluka)]
        if len(local) == 1:
            return Match(local[0], f"name and taluka ({place.taluka})", named)
    return Match(None, f"{len(named)} MahaRERA projects are named {name!r}; the locality does not say which", named)


async def search(get_text: GetText, name: str) -> Optional[List[MahaReraProject]]:
    """The search cards for a name ([] when MahaRERA has none); None when the site did not answer after TRIES. A real answer
    always carries its result count ("Showing Final <n>"); the site's failures come back as pages without it."""
    delay = RETRY_DELAY
    for attempt in range(TRIES):
        try:
            body = await get_text(search_url(name))
            if parse_total(body) is not None:
                return parse_projects(body)
        except Exception:
            pass
        if attempt < TRIES - 1:
            await asyncio.sleep(delay)
            delay *= 2
    return None


def _months(a: Optional[str], b: Optional[str]) -> Optional[int]:
    if not a or not b:
        return None
    ya, ma = int(a[:4]), int(a[5:7])
    yb, mb = int(b[:4]), int(b[5:7])
    return (yb - ya) * 12 + (mb - ma)


def readings(card: MahaReraProject, general: Optional[dict], fetched_at: datetime) -> List[Reading]:
    """Official readings from the search card and, when it was read, the project's general details."""
    url = card.url

    def r(key, value, source="maharera"):
        return Reading(key, value, source, url, fetched_at)

    out = [r("rera_no", card.regno), r("project_name", card.name), r("taluka", card.location), r("pincode", card.pincode),
           r("maharera_url", url)]
    if card.promoter:
        out.append(r("promoter", card.promoter))
    if general:
        out += [r("project_type", general.get("project_type")), r("registered_on", general.get("registered_on")),
                r("possession_at_registration", general.get("completion_at_registration")),
                r("possession_now", general.get("completion_now")),
                r("units_total", general.get("units_total")), r("units_booked", general.get("units_booked"))]
        moved = _months(general.get("completion_at_registration"), general.get("completion_now"))
        if moved is not None:
            out.append(r("possession_moved_months", moved, "calc"))
    return [x for x in out if x.value not in (None, "")]


CANDIDATES = 3


def card_of(d: dict) -> MahaReraProject:
    """A register record as a search card."""
    return MahaReraProject(regno=d.get("regno") or d["_id"], name=d.get("name", ""), promoter=d.get("promoter", ""),
                           location=d.get("taluka", ""), district=d.get("district", ""), pincode=d.get("pincode", ""),
                           last_modified=d.get("last_modified", ""), url=d.get("source_url", ""))


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def fresh(d: dict, now: datetime) -> bool:
    at = d.get("details_checked_at")
    return bool(d.get("details_ok")) and isinstance(at, datetime) and _aware(now) - _aware(at) <= timedelta(days=REGISTER_FRESH_DAYS)


async def from_register(register: Any, name: str, rera_no: str, place: Optional[Place],
                        now: datetime) -> Optional[Tuple[Match, List[Reading]]]:
    """(match, readings) from our register when it holds the project with fresh details; None to ask MahaRERA."""
    rera_no = (rera_no or "").strip().upper()
    if rera_no:
        d = await register.project(rera_no)
        docs = [d] if d else []
    else:
        everything = await register.all_projects()
        docs = [d for d in everything if _words(d.get("name", "")) == _words(name)]
        if not docs and core(name):  # close names are never taken on their own: the agent confirms one (understand.py)
            close = sorted((d for d in everything if core(d.get("name", "")) == core(name)),
                           key=lambda d: not d.get("details_ok"))[:CANDIDATES]
            if close:
                return Match(None, f"close names in our register for {name!r}", [card_of(d) for d in close]), []
    if not docs:
        return None
    m = choose([card_of(d) for d in docs], name or docs[0].get("name", ""), rera_no, place)
    if m.project is None:
        return (m, []) if m.candidates and not rera_no else None
    d = next(x for x in docs if (x.get("regno") or x["_id"]) == m.project.regno)
    if not fresh(d, now):
        return None
    general = {k: d.get(k) for k in ("project_type", "registered_on", "units_total", "units_booked")}
    general.update(completion_at_registration=d.get("completion_at_registration"), completion_now=d.get("completion_now"))
    m.how += " (our register)"
    return m, readings(m.project, general, _aware(d["details_checked_at"]))


async def _group(groups: Any, rera_no: str, name: str) -> Optional[dict]:
    """The marketed project (agentprojects.groups) this number belongs to, or (with no number) this name. A number that is
    not a member never takes the group from the name: a look-alike tower is not part of the project. Never raises."""
    if groups is None:
        return None
    rera = (rera_no or "").strip().upper()
    try:
        return await groups.resolve(rera, "" if rera else (name or ""))
    except Exception as e:
        log.info("project group lookup failed: %s", type(e).__name__)
        return None


async def _register_doc(register: Any, regno: str) -> Optional[dict]:
    if register is None:
        return None
    try:
        return await register.project(regno)
    except Exception:
        return None


async def _group_cards(register: Any, group: dict) -> List[MahaReraProject]:
    """The group's registrations as search cards, from our register when it has them."""
    out = []
    for r in group["registrations"]:
        d = await _register_doc(register, r["regno"])
        out.append(card_of(d) if d else MahaReraProject(
            regno=r["regno"], name=f"{group['name']} {r.get('tower', '')}".strip(), promoter=group.get("promoter", ""),
            location="", district="", pincode=group.get("pincode", ""), last_modified="", url=""))
    return out


async def as_group(rs: List[Reading], group: Optional[dict], register: Any, asked: str) -> List[Reading]:
    """A member tower's readings as the marketed project's, when the listing names that project (`asked`, "Lodha Camelot"):
    its name is the group's (MahaRERA's working name stays as `maharera_name`), and its units are every tower's together,
    or left out when a tower's count is not in our register (one tower's 88 homes are not the project's). A tower's own
    page (asked by MahaRERA's name), one registration, or no group: the readings as they are."""
    if not group or len(group.get("registrations") or []) < 2 or _words(asked or "") != _words(group["name"]):
        return rs
    out: List[Reading] = []
    for x in rs:
        if x.key == "project_name":
            out += [Reading("maharera_name", x.value, x.source, x.url, x.fetched_at),
                    Reading("project_name", group["name"], "agent project", "", x.fetched_at)]
        elif x.key == "units_total":
            counts = [((await _register_doc(register, r["regno"])) or {}).get("units_total") for r in group["registrations"]]
            if all(isinstance(c, int) and c > 0 for c in counts):
                out.append(Reading("units_total", sum(counts), "calc", x.url, x.fetched_at))
        elif x.key != "units_booked":
            out.append(x)
    return out


async def lookup(get_text: GetText, fetch_general: FetchGeneral, name: str, rera_no: str = "",
                 place: Optional[Place] = None, now: Optional[datetime] = None,
                 register: Any = None, groups: Any = None) -> "tuple[Match, List[Reading]]":
    """`register`: the newsroom Store (or a fake with project(regno) and all_projects()); asked before MahaRERA.
    `groups`: agentprojects.groups.Groups (or a fake with resolve(regno, name)). A marketed name sold under several
    registrations ("Lodha Camelot") is not a MahaRERA name: the tower the name says is looked up, else its towers are offered
    to pick from (never one guessed); a member's number is searched on MahaRERA under the working name MahaRERA uses for it."""
    now = now or datetime.utcnow()
    asked = name
    group = await _group(groups, rera_no, name)
    if group and not (rera_no or "").strip():
        if not group["regno"]:
            cards = await _group_cards(register, group)
            towers = ", ".join(f"{r.get('tower') or r['regno']} ({r['regno']})" for r in group["registrations"])
            return Match(None, f"{group['name']} is sold under {len(cards)} MahaRERA registrations: {towers}; "
                               "say which tower", cards), []
        rera_no = group["regno"]
    if register is not None and ((name or "").strip() or (rera_no or "").strip()):
        got = await from_register(register, name, rera_no, place, now)
        if got:
            if group and got[0].project is not None:
                got[0].how += f" ({group['name']}, {group['tower'] or 'one of its registrations'})"
            return got[0], await as_group(got[1], group if got[0].project is not None else None, register, asked)
    if group and group["regno"]:  # MahaRERA's search knows a member by its working name, not the marketed one
        d = await _register_doc(register, group["regno"])
        if d and d.get("name"):
            name = d["name"]
    if not (name or "").strip():
        return Match(None, "the listing has no project name to search MahaRERA by"), []
    found = await search(get_text, name)
    if found is None:
        trace.event(log, "rera", rera_no or name, "lookup", trace.FAILED, reason=f"MahaRERA search did not answer after {TRIES} tries")
        return Match(None, "could not check MahaRERA right now (its search did not answer); try again later"), []
    m = choose(found, name, rera_no, place)
    if m.project is None:
        trace.event(log, "rera", rera_no or name, "lookup", trace.SKIPPED, reason=m.how, found=len(found))
        return m, []
    general = None
    mid = maharera_id(m.project.url)
    if mid:
        body = await fetch_general(mid)
        try:
            general = parse_general(body, m.project.regno, mid) if body else None
        except MahaReraError as e:
            trace.event(log, "rera", m.project.regno, "project_details", trace.FAILED, reason=str(e))
            general = None
    trace.event(log, "rera", m.project.regno, "lookup", trace.OK if general else trace.FALLBACK, how=m.how,
                details="read" if general else "not read (card only)")
    return m, await as_group(readings(m.project, general, now), group, register, asked)
