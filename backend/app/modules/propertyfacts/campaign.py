"""CA-1: a property's fact sheet -> a campaign of posts, one per angle the facts support.

Each angle is a small function: usable facts in, a creative Brief out (or None when the facts it needs are missing). Every number
a post may say is written into the Brief's facts, so the creative guards accept it and still reject anything invented.
To add an angle: write one function and add it to ANGLES."""
import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from app.modules.creative import pipeline
from app.modules.creative.hooks import PATTERNS
from app.modules.creative.listing_brief import price_label
from app.modules.creative.models import Brief, CardBrand, CreativePack, Voice

from . import surroundings
from .facts import Fact

log = logging.getLogger(__name__)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def day(iso: str) -> str:
    """'2029-04-30' -> '30 Apr 2029'."""
    return f"{int(iso[8:10])} {MONTHS[int(iso[5:7]) - 1]} {iso[:4]}"


def link_line_for(where: str) -> str:
    """Instagram's pointer to the listing page (Facebook swaps it for the link itself: schedule.facebook_caption)."""
    return f"Full details of {where}, with its MahaRERA record: link in bio."


class Ctx:
    """Usable fact values, with the names every angle needs."""

    def __init__(self, facts: Dict[str, Fact], photo: str = "none", link: str = "", voice: Optional[Voice] = None,
                 card_brand: Optional[CardBrand] = None, contact: Sequence[str] = (), language: str = "en"):
        self.v: Dict[str, Any] = {k: f.value for k, f in facts.items() if f.usable}
        self.photo, self.link = photo, link
        self.project = self.v.get("project_name") or ""
        self.locality = self.v.get("locality") or ""
        areas = ", ".join(p for p in (self.locality, self.v.get("city") or "Pune") if p) if self.locality else ""
        v = voice or Voice()
        self.voice = v if v.areas else replace(v, areas=areas)  # who speaks; the prompts set the post in this area
        self.card_brand, self.contact, self.language = card_brand, list(contact), language  # an agent's footer and contact
        self.where = ", ".join(p for p in (self.project, self.locality) if p)
        self.plot = self.v.get("property_type") == "plot"
        self.kind = "plot" if self.plot else "home"
        self.sqft = self.v.get("plot_sqft") or self.v.get("carpet_sqft")

    def tags(self) -> List[str]:
        words = [w.capitalize() for w in self.locality.split()]
        return ["#" + "".join(words)] * bool(words) + ["#PuneProperty", "#PlotsInPune" if self.plot else "#PuneHomes", "#MahaRERA"]

    def brief(self, hook: str = "", **kw) -> Brief:
        """A Brief with this property's tags, photo, link and chip; `hook` (when given) opens the post whatever pattern runs."""
        if hook:
            kw["hooks"] = {p: hook for p in PATTERNS}
        kw.setdefault("kicker", self.project.upper()[:28])
        where = self.where or "this property"
        kw.setdefault("intro", f"{where}." if self.where else "")
        kw.setdefault("link_line", link_line_for(where))
        kw.setdefault("writer_note", f"This post markets one property: {where}. Its listed price, project name, MahaRERA "
                                     "details and nearby places are facts you may use exactly as written; add no other number.")
        kw.setdefault("hashtags", self.tags())
        kw.setdefault("photo", self.photo)
        kw.setdefault("link", self.link)
        kw.setdefault("voice", self.voice)
        kw.setdefault("mode", "listing")
        kw.setdefault("card_brand", self.card_brand)
        kw.setdefault("contact", list(self.contact))
        kw.setdefault("language", self.language)
        return Brief(**kw)


def price_reveal(c: Ctx) -> Optional[Brief]:
    if not (c.v.get("price_inr") and c.sqft):
        return None
    price = price_label(c.v["price_inr"])
    line = f"A {c.sqft:,} sq ft {c.kind} at {c.where} is listed at {price}."
    return c.brief(hook=f"{price} for a {c.kind} in {c.project or c.locality}", topic=f"Price of a {c.kind} at {c.where}", short=f"{c.kind} price", stat_value=price,
                   stat_label=f"for this {c.kind}", facts=[line],
                   tip="Ask what the price includes: development charges, stamp duty and registration.", prefer="stat")


def size_in_guntha(c: Ctx) -> Optional[Brief]:
    g, sqm = c.v.get("plot_guntha"), c.v.get("plot_sqm")
    if not (g and c.sqft):
        return None
    line = f"{c.sqft:,} sq ft is {g} guntha, about {sqm:,} sq m. 1 guntha is 1,089 sq ft."
    return c.brief(hook=f"{g} guntha: the plot at {c.project or c.locality}", topic="How big is this plot?", short="plot size", stat_value=f"{g} guntha",
                   stat_label="is the size of this plot", facts=[line],
                   tip="Walk the boundary stones on site before you pay a token.", prefer="stat")


def rate_per_sqft(c: Ctx) -> Optional[Brief]:
    r = c.v.get("price_per_sqft")
    if not r:
        return None
    price = price_label(c.v["price_inr"])
    return c.brief(hook=f"₹{r:,} per sq ft in {c.locality}", topic=f"Rate per sq ft at {c.where}", short="rate per sq ft", stat_value=f"₹{r:,} per sq ft",
                   stat_label=f"listed rate in {c.locality}",
                   facts=[f"{price} for {c.sqft:,} sq ft works out to ₹{r:,} per sq ft."],
                   tip="Compare the rate per sq ft, not the total price.", prefer="stat")


def emi(c: Ctx) -> Optional[Brief]:
    e = c.v.get("emi")
    if not e:
        return None
    loan = price_label(e["loan"])
    rate = f"{e['rate']:g}%"
    line = f"EMI of ₹{e['emi']:,} a month on a {loan} loan (80% of the price) at {rate} for {e['years']} years."
    return c.brief(hook=f"₹{e['emi']:,} a month for this {c.kind}", topic=f"Monthly EMI for this {c.kind}", short="monthly EMI", stat_value=f"₹{e['emi']:,}",
                   stat_label=f"a month EMI for this {c.kind}", facts=[line],
                   tip="Ask your bank for its actual rate before you plan.", prefer="stat")


def possession(c: Ctx) -> Optional[Brief]:
    now, then = c.v.get("possession_now"), c.v.get("possession_at_registration")
    if not now:
        return None
    moved = c.v.get("possession_moved_months") or 0
    facts = [f"MahaRERA completion date for {c.project}: {day(now)}."]
    if then and moved > 0:
        facts.append(f"At registration it was {day(then)}; it has moved by {moved} months.")
        return c.brief(topic=f"Completion date of {c.project}", short="completion date",
                       myth="The brochure date is the final date", truth=f"MahaRERA now shows {day(now)} for {c.project}.",
                       facts=facts, tip="Check the MahaRERA date, not the brochure.", prefer="myth-vs-fact")
    return c.brief(topic=f"Completion date of {c.project}", short="completion date", stat_value=day(now),
                   stat_label="MahaRERA completion date", facts=facts,
                   tip="Check the MahaRERA date, not the brochure.", prefer="stat")


def rera_check(c: Ctx) -> Optional[Brief]:
    rera = c.v.get("rera_no")
    if not rera:
        return None
    steps = ["Open the MahaRERA website", f"Search for {rera}", "Check the completion date and approvals",
             "Match the promoter name with your agreement", "Read the latest quarterly progress update"]
    return c.brief(hook=f"How do you check {c.project} on MahaRERA?", topic=f"Check {c.project} on MahaRERA", short="MahaRERA check", steps=steps,
                   facts=[f"{c.project} is registered on MahaRERA as {rera}."],
                   tip="Ask for the MahaRERA number before any token.", prefer="checklist")


def _km(x: float) -> str:
    return f"{x:g} km"


def _near(c: Ctx) -> List[Tuple[str, Dict[str, Any]]]:
    """(category key, place) for every nearby place, nearest first."""
    out = [(k, p) for k, v in c.v.items() if k.startswith("nearby.") and isinstance(v, list) for p in v]
    return sorted(out, key=lambda kp: kp[1]["km"])


def nearby(c: Ctx) -> Optional[Brief]:
    near = _near(c)
    if len(near) < 3:
        return None
    steps = [f"{surroundings.label(k)}: {p['name']}, about {_km(p['km'])}" for k, p in near[:6]]
    return c.brief(hook=f"What is near {c.project or c.locality}?", topic=f"What is near {c.where}", short="what is nearby", steps=steps, facts=steps,
                   tip="Distances are straight-line; drive the route once at peak hour.", prefer="carousel")


def near_work(c: Ctx) -> Optional[Brief]:
    work = (c.v.get("nearby.industry") or [])
    if not work:
        return None
    w = work[0]
    lines = [f"{p['name']} is about {_km(p['km'])} away (straight line)." for p in work]
    return c.brief(hook=f"{_km(w['km'])} from {c.project or c.locality} to work", topic=f"Work nearby: {c.where}", short="work nearby", stat_value=_km(w["km"]),
                   stat_label=f"to {w['name']}", facts=lines,
                   tip="Drive to work once at shift-change time before you decide.", prefer="stat")


def layout_size(c: Ctx) -> Optional[Brief]:
    units, on = c.v.get("units_total"), c.v.get("registered_on")
    if not units:
        return None
    unit = "plots" if c.plot else "homes"
    line = f"{c.project} has {units} {unit}, registered on MahaRERA" + (f" on {day(on)}." if on else ".")
    return c.brief(hook=f"{units} {unit} in {c.project}", topic=f"How big is {c.project}?", short="project size", stat_value=str(units),
                   stat_label=f"{unit} in {c.project}", facts=[line],
                   tip="A smaller layout means fewer neighbours sharing the roads and water.", prefer="stat")


def plot_or_flat(c: Ctx) -> Optional[Brief]:
    if not c.v.get("price_inr"):
        return None
    price = price_label(c.v["price_inr"])
    return c.brief(hook=f"Plot or flat for {price}?", topic=f"Plot or flat for {price}?", short="plot or flat", question=f"Plot or flat for {price}?",
                   options=["A plot", "A flat"], facts=[f"A plot at {c.where} is listed at {price}."], prefer="poll")


def plot_checklist(c: Ctx) -> Optional[Brief]:
    if not c.plot:
        return None
    steps = ["NA order for the land", "7/12 extract in the seller's name", "Approved layout plan",
             "MahaRERA registration of the layout", "Boundary stones marked on site"]
    return c.brief(hook="Plot papers to check before any token", topic="Before you buy a plot", short="plot papers", steps=steps, facts=steps,
                   tip="Get every paper checked by a lawyer before the token.", prefer="checklist")


def plot_myth(c: Ctx) -> Optional[Brief]:
    if not c.plot:
        return None
    return c.brief(topic="Is every plot ready to build on?", short="NA plot", myth="Every plot is ready to build on",
                   truth="Check the NA order and the approved layout first.",
                   facts=["A plot needs an NA order and an approved layout before you build."], prefer="myth-vs-fact")


@dataclass(frozen=True)
class AngleDef:
    id: str
    build: Callable[[Ctx], Optional[Brief]]


ANGLES: Tuple[AngleDef, ...] = tuple(AngleDef(f.__name__, f) for f in (
    price_reveal, possession, near_work, nearby, size_in_guntha, rera_check, emi, plot_checklist, rate_per_sqft, layout_size,
    plot_or_flat, plot_myth))


def plan(facts: Dict[str, Fact], photo: str = "none", link: str = "", angles: Sequence[AngleDef] = ANGLES,
         voice: Optional[Voice] = None, card_brand: Optional[CardBrand] = None, contact: Sequence[str] = (),
         language: str = "en") -> List[Tuple[str, Brief]]:
    """`voice`, `card_brand`, `contact`, `language`: whose posts these are (default ours) and in which language."""
    c = Ctx(facts, photo, link, voice, card_brand, contact, language)
    out = []
    for a in angles:
        b = a.build(c)
        if b is not None:
            out.append((a.id, b))
    return out


RETRIES = 3  # other seeds (other layouts) to try before an angle is dropped: some layouts cannot fit some texts


async def make(facts: Dict[str, Fact], out_dir: Path, llm: Any = None, photo: str = "none", link: str = "",
               channel: str = "instagram", dropped: Optional[Dict[str, Any]] = None,
               voice: Optional[Voice] = None, card_brand: Optional[CardBrand] = None, contact: Sequence[str] = (),
               language: str = "en") -> List[Tuple[str, CreativePack]]:
    """Render every planned angle; consecutive posts avoid repeating a layout. An angle that fails a guard is retried with
    other seeds, then dropped (its problems go into `dropped` when given). `voice`: who speaks (default the brand desk)."""
    packs: List[Tuple[str, CreativePack]] = []
    recent: List[str] = []
    for i, (aid, brief) in enumerate(plan(facts, photo, link, voice=voice, card_brand=card_brand, contact=contact, language=language)):
        for attempt in range(RETRIES):
            pack = await pipeline.make(brief, "buyer", channel, llm, seed=i + 17 * attempt, recent_layouts=recent,
                                       out_dir=Path(out_dir) / aid, reviewer=None)
            if pack.report.get("ok"):
                packs.append((aid, pack))
                recent.append(str(pack.design.get("layout")))
                break
        else:
            log.info("campaign angle %s dropped: %s", aid, pack.report.get("problems"))
            if dropped is not None:
                dropped[aid] = pack.report.get("problems")
    return packs
