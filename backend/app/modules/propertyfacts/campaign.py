"""CA-1: a property's fact sheet -> a campaign of posts, one per angle the facts support.

Each angle is a small function: usable facts in, a creative Brief out (or None when the facts it needs are missing). Every number
a post may say is written into the Brief's facts, so the creative guards accept it and still reject anything invented.
Confirmed brochure facts (level builder_claim) feed their own angles only, each worded "as per the builder's brochure"; the
angles that speak for MahaRERA (possession, rera_check, layout_size) need MahaRERA's own record and are skipped without it.
Images the agent confirmed from the brochure (brochure.usable_images) carry two angles: `floor_plan` shows a plan big with the
configuration and carpet area it belongs to (the listing's own, or a confirmed brochure claim, attributed), and `first_look`
shows a render, always labelled "Artist's impression". Neither ever goes into the walkthrough reel (agent photos only).
To add an angle: write one function and add it to ANGLES."""
import logging
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from app.modules.creative import i18n, pipeline
from app.modules.creative.guards import problems_in
from app.modules.creative.hooks import PATTERNS
from app.modules.creative.listing_brief import price_label
from app.modules.creative.models import Brief, CardBrand, CreativePack, Voice
from app.platform.text import bhk_label

from . import advert, surroundings
from .facts import Fact

log = logging.getLogger(__name__)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def day(iso: str) -> str:
    """'2029-04-30' -> '30 Apr 2029'."""
    return f"{int(iso[8:10])} {MONTHS[int(iso[5:7]) - 1]} {iso[:4]}"


LINK_LINE = {"en": "Full details of {where}, with its MahaRERA record: link in bio.",
             "mr": "{where} ची पूर्ण माहिती, MahaRERA नोंदीसह: बायोमधील लिंक.",
             "hi": "{where} की पूरी जानकारी, MahaRERA रिकॉर्ड के साथ: बायो में लिंक."}
LINK_LINE_PLAIN = {"en": "Full details of {where}: link in bio.",   # no MahaRERA record read: none is promised
                   "mr": "{where} ची पूर्ण माहिती: बायोमधील लिंक.",
                   "hi": "{where} की पूरी जानकारी: बायो में लिंक."}
BROCHURE = "as per the builder's brochure"
ARTISTS_IMPRESSION = "Artist's impression"   # brochure_parse.ARTISTS_IMPRESSION: on every render a post shows
PLAN_LABEL = "Floor plan from the builder's brochure"

# The caption's closing question for each angle, in each post language: one a buyer can answer about THIS subject
# (a price card does not ask how many site visits they made). Code-written, so a translation never changes it.
ASKS: Dict[str, Dict[str, str]] = {
    "price_reveal": {"en": "What would you ask about this price? Tell us below.",
                     "mr": "या किमतीबद्दल तुम्ही काय विचाराल? खाली सांगा.",
                     "hi": "इस कीमत के बारे में आप क्या पूछेंगे? नीचे बताइए."},
    "possession": {"en": "Do you check the MahaRERA date before you book? Tell us below.",
                   "mr": "बुकिंगपूर्वी तुम्ही MahaRERA वरची तारीख तपासता का? खाली सांगा.",
                   "hi": "बुकिंग से पहले क्या आप MahaRERA की तारीख देखते हैं? नीचे बताइए."},
    "near_work": {"en": "How far is your work from home today? Tell us below.",
                  "mr": "आज तुमचे काम घरापासून किती दूर आहे? खाली सांगा.",
                  "hi": "आज आपका काम घर से कितनी दूर है? नीचे बताइए."},
    "nearby": {"en": "Which place nearby matters most to you? Tell us below.",
               "mr": "जवळपासचे कोणते ठिकाण तुमच्यासाठी सर्वात महत्त्वाचे आहे? खाली सांगा.",
               "hi": "पास की कौन-सी जगह आपके लिए सबसे ज़रूरी है? नीचे बताइए."},
    "size_in_guntha": {"en": "Do you think of land in guntha or in sq ft? Tell us below.",
                       "mr": "तुम्ही जमीन गुंठ्यात मोजता की sq ft मध्ये? खाली सांगा.",
                       "hi": "आप ज़मीन गुंठा में सोचते हैं या sq ft में? नीचे बताइए."},
    "rera_check": {"en": "Have you looked up a project on MahaRERA before? Tell us below.",
                   "mr": "तुम्ही याआधी MahaRERA वर एखादा प्रकल्प तपासला आहे का? खाली सांगा.",
                   "hi": "क्या आपने पहले कभी MahaRERA पर कोई प्रोजेक्ट देखा है? नीचे बताइए."},
    "emi": {"en": "What EMI did you plan for? Tell us below.",
            "mr": "तुम्ही किती EMI ठरवला आहे? खाली सांगा.",
            "hi": "आपने कितनी EMI सोची है? नीचे बताइए."},
    "plot_checklist": {"en": "Which paper would you check first? Tell us below.",
                       "mr": "तुम्ही सर्वात आधी कोणता कागद तपासाल? खाली सांगा.",
                       "hi": "आप सबसे पहले कौन-सा कागज़ जाँचेंगे? नीचे बताइए."},
    "rate_per_sqft": {"en": "Do you compare the rate per sq ft before a site visit? Tell us below.",
                      "mr": "साइट व्हिजिटपूर्वी तुम्ही प्रति sq ft दराची तुलना करता का? खाली सांगा.",
                      "hi": "साइट विज़िट से पहले क्या आप प्रति sq ft दर की तुलना करते हैं? नीचे बताइए."},
    "layout_size": {"en": "Do you prefer a smaller layout or a bigger one? Tell us below.",
                    "mr": "तुम्हाला लहान ले-आउट आवडतो की मोठा? खाली सांगा.",
                    "hi": "आपको छोटा लेआउट पसंद है या बड़ा? नीचे बताइए."},
    "plot_or_flat": {"en": "Plot or flat: which would you pick? Tell us in the comments.",
                     "mr": "प्लॉट की फ्लॅट: तुम्ही काय निवडाल? कमेंटमध्ये सांगा.",
                     "hi": "प्लॉट या फ्लैट: आप क्या चुनेंगे? कमेंट में बताइए."},
    "amenities": {"en": "Which amenity would you use most? Tell us below.",
                  "mr": "तुम्ही कोणती सुविधा सर्वात जास्त वापराल? खाली सांगा.",
                  "hi": "आप कौन-सी सुविधा सबसे ज़्यादा इस्तेमाल करेंगे? नीचे बताइए."},
    "specifications": {"en": "Which of these do you check first on a site visit? Tell us below.",
                       "mr": "साइट व्हिजिटला तुम्ही यापैकी सर्वात आधी काय तपासता? खाली सांगा.",
                       "hi": "साइट विज़िट पर आप इनमें से सबसे पहले क्या जाँचते हैं? नीचे बताइए."},
    "configurations": {"en": "Which size suits your family? Tell us below.",
                       "mr": "तुमच्या कुटुंबासाठी कोणता आकार योग्य आहे? खाली सांगा.",
                       "hi": "आपके परिवार के लिए कौन-सा साइज़ सही है? नीचे बताइए."},
    "floor_plan": {"en": "Which room would you set up first? Tell us below.",
                   "mr": "तुम्ही सर्वात आधी कोणती खोली सजवाल? खाली सांगा.",
                   "hi": "आप सबसे पहले कौन-सा कमरा सजाएँगे? नीचे बताइए."},
    "first_look": {"en": "What would you ask the builder on a site visit? Tell us below.",
                   "mr": "साइट व्हिजिटला तुम्ही बिल्डरला काय विचाराल? खाली सांगा.",
                   "hi": "साइट विज़िट पर आप बिल्डर से क्या पूछेंगे? नीचे बताइए."},
    "plot_myth": {"en": "Did you know a plot needs an NA order? Tell us below.",
                  "mr": "प्लॉटसाठी NA ऑर्डर लागते हे तुम्हाला माहीत होते का? खाली सांगा.",
                  "hi": "क्या आप जानते थे कि प्लॉट के लिए NA ऑर्डर चाहिए? नीचे बताइए."},
}


def link_line_for(where: str, language: str = "en", maharera: bool = True) -> str:
    """Instagram's pointer to the listing page (Facebook swaps it for the link itself: schedule.facebook_caption). Without a
    MahaRERA record (`maharera=False`) the line promises none."""
    if language in ("mr", "hi"):  # a place name as the language spells it (Ranjangaon -> रांजणगाव); project names stay
        where = ", ".join(i18n.PLACES.get(p.strip(), {}).get(language, p.strip()) for p in where.split(","))
    lines = LINK_LINE if maharera else LINK_LINE_PLAIN
    return lines.get(language, lines["en"]).format(where=where)


class Ctx:
    """Usable fact values, with the names every angle needs."""

    def __init__(self, facts: Dict[str, Fact], photo: str = "none", link: str = "", voice: Optional[Voice] = None,
                 card_brand: Optional[CardBrand] = None, contact: Sequence[str] = (), language: str = "en",
                 images: Sequence[Dict[str, Any]] = (), kit: Optional[dict] = None):
        self.v: Dict[str, Any] = {k: f.value for k, f in facts.items() if f.usable}
        # the project registration the cards may print (the QR badge and the strip's MahaRERA line): advert.trusted, which
        # reads the brochure kit's answer too (`exempt` or an unverified number: none)
        self.registration = advert.trusted({}, facts, kit)
        self.claims: Dict[str, Any] = {k: f.value for k, f in facts.items() if f.level == "builder_claim"}  # say whose claim
        # MahaRERA's own record was read (not only a number typed into the listing or printed in a brochure)
        self.maharera = any("maharera" in f.sources for f in facts.values() if f.usable)
        self.photo, self.link = photo, link
        self.project = self.v.get("project_name") or self.claims.get("project_name") or ""
        self.locality = self.v.get("locality") or ""
        areas = ", ".join(p for p in (self.locality, self.v.get("city") or "Pune") if p) if self.locality else ""
        v = voice or Voice()
        self.voice = v if v.areas else replace(v, areas=areas)  # who speaks; the prompts set the post in this area
        self.contact, self.language = list(contact), language  # an agent's contact lines and the post language
        if card_brand is not None:  # an agent's cards also carry this listing's price and MahaRERA number
            price = price_label(self.v["price_inr"]) if self.v.get("price_inr") else ""
            card_brand = replace(card_brand, price=card_brand.price or price,
                                 rera=card_brand.rera or (self.registration.regno if self.registration else ""))
        self.card_brand = card_brand
        self.where = ", ".join(p for p in (self.project, self.locality) if p)
        self.plot = self.v.get("property_type") == "plot"
        self.kind = "plot" if self.plot else "home"
        self.sqft = self.v.get("plot_sqft") or self.v.get("carpet_sqft")
        # images the agent confirmed from the brochure (brochure.usable_images): {kind, path, label, configs}
        self.images = [dict(i) for i in images if isinstance(i, dict) and i.get("path") and Path(str(i["path"])).is_file()]

    def tags(self) -> List[str]:
        words = [w.capitalize() for w in self.locality.split()]
        return (["#" + "".join(words)] * bool(words) + ["#PuneProperty", "#PlotsInPune" if self.plot else "#PuneHomes"]
                + ["#MahaRERA"] * self.maharera)

    def brief(self, hook: str = "", angle: str = "", **kw) -> Brief:
        """A Brief with this property's tags, photo, link and chip; `hook` (when given) opens the post whatever pattern runs;
        `angle` picks the closing question (ASKS)."""
        if hook:
            kw["hooks"] = {p: hook for p in PATTERNS}
        if angle in ASKS:
            kw.setdefault("asks", dict(ASKS[angle]))
        kw.setdefault("kicker", self.project.upper()[:28])
        where = self.where or "this property"
        kw.setdefault("intro", f"{where}." if self.where else "")
        kw.setdefault("link_line", link_line_for(where, self.language, self.maharera))
        official = "MahaRERA details and " if self.maharera else ""
        kw.setdefault("writer_note", f"This post markets one property: {where}. Its listed price, project name, {official}"
                                     "nearby places are facts you may use exactly as written; add no other number.")
        kw.setdefault("hashtags", self.tags())
        kw.setdefault("photo", self.photo)
        kw.setdefault("link", self.link)
        kw.setdefault("voice", self.voice)
        kw.setdefault("mode", "listing")
        kw.setdefault("card_brand", self.card_brand)
        kw.setdefault("maharera", self.registration)
        kw.setdefault("contact", list(self.contact))
        kw.setdefault("language", self.language)
        return Brief(**kw)


def price_reveal(c: Ctx) -> Optional[Brief]:
    if not (c.v.get("price_inr") and c.sqft):
        return None
    price = price_label(c.v["price_inr"])
    line = f"A {c.sqft:,} sq ft {c.kind} at {c.where} is listed at {price}."
    return c.brief(angle="price_reveal", hook=f"{price} for a {c.kind} in {c.project or c.locality}", topic=f"Price of a {c.kind} at {c.where}", short=f"{c.kind} price", stat_value=price,
                   stat_label=f"for this {c.kind}", facts=[line],
                   tip="Ask what the price includes: development charges, stamp duty and registration.", prefer="stat")


def size_in_guntha(c: Ctx) -> Optional[Brief]:
    g, sqm = c.v.get("plot_guntha"), c.v.get("plot_sqm")
    if not (g and c.sqft):
        return None
    line = f"{c.sqft:,} sq ft is {g} guntha, about {sqm:,} sq m. 1 guntha is 1,089 sq ft."
    return c.brief(angle="size_in_guntha", hook=f"{g} guntha: the plot at {c.project or c.locality}", topic="How big is this plot?", short="plot size", stat_value=f"{g} guntha",
                   stat_label="is the size of this plot", facts=[line],
                   tip="Walk the boundary stones on site before you pay a token.", prefer="stat")


def rate_per_sqft(c: Ctx) -> Optional[Brief]:
    r = c.v.get("price_per_sqft")
    if not r:
        return None
    price = price_label(c.v["price_inr"])
    return c.brief(angle="rate_per_sqft", hook=f"₹{r:,} per sq ft in {c.locality}", topic=f"Rate per sq ft at {c.where}", short="rate per sq ft", stat_value=f"₹{r:,} per sq ft",
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
    return c.brief(angle="emi", hook=f"₹{e['emi']:,} a month for this {c.kind}", topic=f"Monthly EMI for this {c.kind}", short="monthly EMI", stat_value=f"₹{e['emi']:,}",
                   stat_label=f"a month EMI for this {c.kind}", facts=[line],
                   tip="Ask your bank for its actual rate before you plan.", prefer="stat")


def possession(c: Ctx) -> Optional[Brief]:
    now, then = c.v.get("possession_now"), c.v.get("possession_at_registration")
    if not (now and c.maharera):
        return None
    moved = c.v.get("possession_moved_months") or 0
    facts = [f"MahaRERA completion date for {c.project}: {day(now)}."]
    if then and moved > 0:
        facts.append(f"At registration it was {day(then)}; it has moved by {moved} months.")
        return c.brief(angle="possession", topic=f"Completion date of {c.project}", short="completion date",
                       myth="The brochure date is the final date", truth=f"MahaRERA now shows {day(now)} for {c.project}.",
                       facts=facts, tip="Check the MahaRERA date, not the brochure.", prefer="myth-vs-fact")
    return c.brief(angle="possession", topic=f"Completion date of {c.project}", short="completion date", stat_value=day(now),
                   stat_label="MahaRERA completion date", facts=facts,
                   tip="Check the MahaRERA date, not the brochure.", prefer="stat")


def rera_check(c: Ctx) -> Optional[Brief]:
    rera = c.v.get("rera_no")
    if not (rera and c.maharera):  # a number typed into the listing is not MahaRERA's record
        return None
    steps = ["Open the MahaRERA website", f"Search for {rera}", "Check the completion date and approvals",
             "Match the promoter name with your agreement", "Read the latest quarterly progress update"]
    return c.brief(angle="rera_check", hook=f"How do you check {c.project} on MahaRERA?", topic=f"Check {c.project} on MahaRERA", short="MahaRERA check", steps=steps,
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
    return c.brief(angle="nearby", hook=f"What is near {c.project or c.locality}?", topic=f"What is near {c.where}", short="what is nearby", steps=steps, facts=steps,
                   tip="Distances are straight-line; drive the route once at peak hour.", prefer="carousel")


def near_work(c: Ctx) -> Optional[Brief]:
    work = (c.v.get("nearby.industry") or [])
    if not work:
        return None
    w = work[0]
    lines = [f"{p['name']} is about {_km(p['km'])} away (straight line)." for p in work]
    return c.brief(angle="near_work", hook=f"{_km(w['km'])} from {c.project or c.locality} to work", topic=f"Work nearby: {c.where}", short="work nearby", stat_value=_km(w["km"]),
                   stat_label=f"to {w['name']}", facts=lines,
                   tip="Drive to work once at shift-change time before you decide.", prefer="stat")


def layout_size(c: Ctx) -> Optional[Brief]:
    units, on = c.v.get("units_total"), c.v.get("registered_on")
    if not (units and c.maharera):
        return None
    unit = "plots" if c.plot else "homes"
    line = f"{c.project} has {units} {unit}, registered on MahaRERA" + (f" on {day(on)}." if on else ".")
    return c.brief(angle="layout_size", hook=f"{units} {unit} in {c.project}", topic=f"How big is {c.project}?", short="project size", stat_value=str(units),
                   stat_label=f"{unit} in {c.project}", facts=[line],
                   tip="A smaller layout means fewer neighbours sharing the roads and water.", prefer="stat")


def plot_or_flat(c: Ctx) -> Optional[Brief]:
    if not c.v.get("price_inr"):
        return None
    price = price_label(c.v["price_inr"])
    return c.brief(angle="plot_or_flat", hook=f"Plot or flat for {price}?", topic=f"Plot or flat for {price}?", short="plot or flat", question=f"Plot or flat for {price}?",
                   options=["A plot", "A flat"], facts=[f"A plot at {c.where} is listed at {price}."], prefer="poll")


def plot_checklist(c: Ctx) -> Optional[Brief]:
    if not c.plot:
        return None
    steps = ["NA order for the land", "7/12 extract in the seller's name", "Approved layout plan",
             "MahaRERA registration of the layout", "Boundary stones marked on site"]
    return c.brief(angle="plot_checklist", hook="Plot papers to check before any token", topic="Before you buy a plot", short="plot papers", steps=steps, facts=steps,
                   tip="Get every paper checked by a lawyer before the token.", prefer="checklist")


def plot_myth(c: Ctx) -> Optional[Brief]:
    if not c.plot:
        return None
    return c.brief(angle="plot_myth", topic="Is every plot ready to build on?", short="NA plot", myth="Every plot is ready to build on",
                   truth="Check the NA order and the approved layout first.",
                   facts=["A plot needs an NA order and an approved layout before you build."], prefer="myth-vs-fact")


def _postable(items: Any, limit: int = 8) -> List[str]:
    """Brochure list items a post can carry as written: short, and nothing the guards refuse on its own ("luxurious")."""
    out = []
    for i in items if isinstance(items, list) else []:
        if isinstance(i, str) and i.strip() and len(i.split()) <= 14 and not problems_in(i, i):
            out.append(i.strip().rstrip("."))
    return out[:limit]


def _brochure_brief(c: Ctx, angle: str, hook: str, **kw) -> Brief:
    where = c.where or c.project or "this property"
    kw.setdefault("intro", f"{BROCHURE[0].upper() + BROCHURE[1:]} for {where}:")
    kw.setdefault("writer_note", f"This post markets one property: {where}. The items below come from the builder's brochure, "
                                 "not from MahaRERA: whenever you mention them say 'as per the builder's brochure', use them "
                                 "exactly as written, and add no other number or claim.")
    return c.brief(angle=angle, hook=hook, **kw)


def amenities(c: Ctx) -> Optional[Brief]:
    items = _postable(c.claims.get("brochure.amenities"))
    if len(items) < 3:
        return None
    name = c.project or c.locality or "this project"
    return _brochure_brief(c, "amenities", f"Amenities at {name}, {BROCHURE}", topic=f"Amenities at {name}", short="amenities",
                           steps=items[:6], facts=[f"{BROCHURE.capitalize()}, {name} has: {', '.join(items)}."],
                           tip="Ask which amenities will be ready at possession, and see them on site.", prefer="carousel")


def specifications(c: Ctx) -> Optional[Brief]:
    items = _postable(c.claims.get("brochure.specifications"))
    if len(items) < 3:
        return None
    name = c.project or c.locality or "this project"
    return _brochure_brief(c, "specifications", f"How {name} is built, {BROCHURE}", topic=f"Specifications of {name}",
                           short="specifications", steps=items[:6],
                           facts=[f"{BROCHURE.capitalize()}: {item}." for item in items],
                           tip="Ask for the specifications in your agreement, item by item.", prefer="carousel")


def configurations(c: Ctx) -> Optional[Brief]:
    configs = _postable(c.claims.get("brochure.configurations"))
    if not configs:
        return None
    sizes = _postable(c.claims.get("brochure.carpet_area"))
    name = c.project or c.locality or "this project"
    what = " and ".join([", ".join(configs[:-1]), configs[-1]] if len(configs) > 1 else configs)
    facts = [f"{BROCHURE.capitalize()}, {name} offers {what} homes."] + [f"{BROCHURE.capitalize()}, {s}." for s in sizes]
    nums = [x.split()[0] for x in configs if x.endswith(" BHK")]
    short = (" & ".join([", ".join(nums[:-1]), nums[-1]] if len(nums) > 1 else nums) + " BHK") if len(nums) == len(configs) else what
    if len(sizes) >= 3:
        kw: Dict[str, Any] = {"steps": sizes[:6], "prefer": "carousel"}
    elif len(short) <= 12:  # the big number on a stat card fits about 12 characters
        kw = {"stat_value": short, "stat_label": f"homes at {name}, {BROCHURE}", "prefer": "stat"}
        facts.append(f"{BROCHURE.capitalize()}, {short} homes at {name}.")
    else:
        kw = {"prefer": "single"}
    return _brochure_brief(c, "configurations", f"{what} at {name}, {BROCHURE}", topic=f"Home sizes at {name}",
                           short="home sizes", facts=facts, tip="Ask for the RERA carpet area of your unit in writing.", **kw)


_CARPET = re.compile(r"^\s*(?:(?P<bhk>\d(?:\.5)?)\s*BHK|(?P<rk>1\s*RK))\s*:\s*(?P<area>.+?)\s*carpet\s*$", re.I)


def _carpets(c: Ctx) -> List[Tuple[str, str, bool]]:
    """(configuration, carpet area as written, official) a floor plan post may state: the listing's own (official), else
    the confirmed brochure claims ("2 BHK: 650 sq ft carpet"), which a post must attribute. A listing with a configuration
    only ever shows that configuration's plan."""
    if c.plot:
        return []
    try:
        mine = bhk_label(float(c.v["bhk"])) if c.v.get("bhk") else ""
        if mine and c.v.get("carpet_sqft"):
            return [(mine, f"{int(c.v['carpet_sqft']):,} sq ft", True)]
    except (TypeError, ValueError):
        mine = ""
    out: List[Tuple[str, str, bool]] = []
    for item in _postable(c.claims.get("brochure.carpet_area"), limit=12):
        m = _CARPET.match(item)
        config = (bhk_label(float(m.group("bhk"))) if m.group("bhk") else "1 RK") if m else ""
        if config and (not mine or config == mine) and not any(o[0] == config for o in out):
            out.append((config, m.group("area").strip(), False))
    return out


def floor_plan(c: Ctx) -> Optional[Brief]:
    """The plan of the home, big, with its configuration and carpet area: the size made real. Needs a floor plan the agent
    confirmed and a carpet area that is official (the listing) or a confirmed brochure claim, for a configuration the plan
    names (or the only configuration there is, when the plan names none)."""
    plans = [i for i in c.images if i.get("kind") == "floor_plan"]
    carpets = _carpets(c)
    if not plans or not carpets:
        return None
    pick = None
    for config, area, official in carpets:
        plan = next((p for p in plans if config in (p.get("configs") or [])), None)
        if plan is None and len(carpets) == 1:
            plan = next((p for p in plans if not p.get("configs")), None)
        if plan is not None:
            pick = (config, area, official, plan)
            break
    if pick is None:
        return None
    config, area, official, plan = pick
    name = c.project or c.locality or "this project"
    fact = (f"The {config} at {c.where or name} has a carpet area of {area}." if official
            else f"{BROCHURE.capitalize()}, the {config} at {name} has a carpet area of {area}.")
    return _brochure_brief(c, "floor_plan", f"The {config} floor plan: {area} carpet", topic=f"Floor plan of a {config} at {name}",
                           short="floor plan", facts=[fact, f"The floor plan is from the builder's brochure for {name}."],
                           tip="Ask for the RERA carpet area of your unit in writing.", prefer="plan", plan_image=plan["path"],
                           plan_label=PLAN_LABEL, plan_fit="contain")


def first_look(c: Ctx) -> Optional[Brief]:
    """The builder's render of the project, always labelled "Artist's impression" on the image."""
    render = next((i for i in c.images if i.get("kind") == "render"), None)
    if render is None or not c.project:
        return None
    return _brochure_brief(c, "first_look", f"A first look at {c.project}", topic=f"How {c.project} will look",
                           short="first look", facts=[f"The builder's brochure shows {c.project} in an artist's impression."],
                           tip="A render is not the finished building: see the site and the sample flat.", prefer="plan",
                           plan_image=render["path"], plan_label=ARTISTS_IMPRESSION, plan_fit="cover")


@dataclass(frozen=True)
class AngleDef:
    id: str
    build: Callable[[Ctx], Optional[Brief]]


ANGLES: Tuple[AngleDef, ...] = tuple(AngleDef(f.__name__, f) for f in (
    price_reveal, floor_plan, possession, near_work, nearby, size_in_guntha, rera_check, emi, plot_checklist, rate_per_sqft,
    layout_size, plot_or_flat, plot_myth, configurations, amenities, specifications, first_look))


def plan(facts: Dict[str, Fact], photo: str = "none", link: str = "", angles: Sequence[AngleDef] = ANGLES,
         voice: Optional[Voice] = None, card_brand: Optional[CardBrand] = None, contact: Sequence[str] = (),
         language: str = "en", images: Sequence[Dict[str, Any]] = (), kit: Optional[dict] = None) -> List[Tuple[str, Brief]]:
    """`voice`, `card_brand`, `contact`, `language`: whose posts these are (default ours) and in which language. `images`: the
    brochure images the agent confirmed (brochure.usable_images); `kit`: the listing's brochure kit (its registration answer
    decides the MahaRERA badge with the facts, see advert.trusted)."""
    c = Ctx(facts, photo, link, voice, card_brand, contact, language, images, kit)
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
               language: str = "en", images: Sequence[Dict[str, Any]] = (), kit: Optional[dict] = None) -> List[Tuple[str, CreativePack]]:
    """Render every planned angle; consecutive posts avoid repeating a layout. An angle that fails a guard is retried with
    other seeds, then dropped (its problems go into `dropped` when given). `voice`: who speaks (default the brand desk)."""
    packs: List[Tuple[str, CreativePack]] = []
    recent: List[str] = []
    for i, (aid, brief) in enumerate(plan(facts, photo, link, voice=voice, card_brand=card_brand, contact=contact, language=language,
                                          images=images, kit=kit)):
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
