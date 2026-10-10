"""CA-1: a property's fact sheet -> a campaign of posts, one per angle the facts support.

Each angle is a small function: usable facts in, a creative Brief out (or None when the facts it needs are missing). Every number
a post may say is written into the Brief's facts, so the creative guards accept it and still reject anything invented.
To add an angle: write one function and add it to ANGLES."""
import hashlib
import logging
import re
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Tuple

from app.modules.creative import i18n, pipeline
from app.modules.creative.hooks import PATTERNS
from app.modules.creative.listing_brief import price_label
from app.modules.creative.models import Brief, CardBrand, CreativePack, Voice

from . import calc, surroundings
from .facts import Fact

log = logging.getLogger(__name__)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def day(iso: str) -> str:
    """'2029-04-30' -> '30 Apr 2029'."""
    return f"{int(iso[8:10])} {MONTHS[int(iso[5:7]) - 1]} {iso[:4]}"


LINK_LINE = {"en": "Full details of {where}, with its MahaRERA record: link in bio.",
             "mr": "{where} ची पूर्ण माहिती, MahaRERA नोंदीसह: बायोमधील लिंक.",
             "hi": "{where} की पूरी जानकारी, MahaRERA रिकॉर्ड के साथ: बायो में लिंक."}
LINK_LINE_PLAIN = {"en": "Full details of {where}: link in bio.",   # no MahaRERA record to point to
                   "mr": "{where} ची पूर्ण माहिती: बायोमधील लिंक.",
                   "hi": "{where} की पूरी जानकारी: बायो में लिंक."}

# The caption's closing question for each angle, in each post language: one a buyer can answer about THIS subject
# (a price card does not ask how many site visits they made). Code-written, so a translation never changes it.
ASKS: Dict[str, Dict[str, str]] = {
    "overview": {"en": "Would you like to see it on a site visit? Tell us below.",
                 "mr": "साइट व्हिजिटला येऊन पाहायला आवडेल का? खाली सांगा.",
                 "hi": "क्या आप साइट विज़िट पर इसे देखना चाहेंगे? नीचे बताइए."},
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
    "land_area": {"en": "How much open space would you want in a layout? Tell us below.",
                  "mr": "ले-आउटमध्ये तुम्हाला किती मोकळी जागा हवी? खाली सांगा.",
                  "hi": "लेआउट में आपको कितनी खुली जगह चाहिए? नीचे बताइए."},
    "plot_or_flat": {"en": "Plot or flat: which would you pick? Tell us in the comments.",
                     "mr": "प्लॉट की फ्लॅट: तुम्ही काय निवडाल? कमेंटमध्ये सांगा.",
                     "hi": "प्लॉट या फ्लैट: आप क्या चुनेंगे? कमेंट में बताइए."},
    "offer": {"en": "Would you like the booking terms on WhatsApp? Tell us below.",
              "mr": "बुकिंगच्या अटी WhatsApp वर हव्या आहेत का? खाली सांगा.",
              "hi": "क्या बुकिंग की शर्तें WhatsApp पर चाहिए? नीचे बताइए."},
    "amenities": {"en": "Which of these matters most to you? Tell us below.",
                  "mr": "यापैकी तुमच्यासाठी सर्वात महत्त्वाचे काय? खाली सांगा.",
                  "hi": "इनमें से आपके लिए सबसे ज़रूरी क्या है? नीचे बताइए."},
    "plot_myth": {"en": "Did you know a plot needs an NA order? Tell us below.",
                  "mr": "प्लॉटसाठी NA ऑर्डर लागते हे तुम्हाला माहीत होते का? खाली सांगा.",
                  "hi": "क्या आप जानते थे कि प्लॉट के लिए NA ऑर्डर चाहिए? नीचे बताइए."},
}


def link_line_for(where: str, language: str = "en", registered: bool = True) -> str:
    """Instagram's pointer to the listing page (Facebook swaps it for the link itself: schedule.facebook_caption).
    `registered`: the property has a MahaRERA number, so the page carries its record."""
    if language in ("mr", "hi"):  # a place name as the language spells it (Ranjangaon -> रांजणगाव); project names stay
        where = ", ".join(i18n.PLACES.get(p.strip(), {}).get(language, p.strip()) for p in where.split(","))
    lines = LINK_LINE if registered else LINK_LINE_PLAIN
    return lines.get(language, lines["en"]).format(where=where)


# Towns along one road whose buyers look at each other's property (a Ranjangaon MIDC worker looks at Shirur and Shikrapur).
CORRIDORS: Dict[str, Tuple[str, ...]] = {
    "the Pune-Ahmednagar road": ("Kharadi", "Wagholi", "Lonikand", "Koregaon Bhima", "Sanaswadi", "Shikrapur", "Malthan",
                                 "Karegaon", "Ranjangaon", "Shirur"),
}


def corridor(*places: str) -> Tuple[str, Tuple[str, ...]]:
    """(road, its towns) for the first place that lies on a known corridor; ("", ()) otherwise."""
    for road, towns in CORRIDORS.items():
        low = {t.lower() for t in towns}
        if any((p or "").strip().lower() in low for p in places):
            return road, towns
    return "", ()


def reader_note(v: Dict[str, Any], plot: bool, layout: bool) -> str:
    """Who sees this post and how they may be spoken to: guidance for the writing models, never a fixed line."""
    loc = v.get("locality") or ""
    road, towns = corridor(loc, v.get("taluka") or "")
    work = [p["name"] for p in (v.get("nearby.industry") or [])[:2] if isinstance(p, dict) and p.get("name")]
    who = [f"people who live or work in and around {loc}" if loc else "Pune property buyers"]
    if towns:
        who.append(f"families and workers along {road} ({', '.join(towns)})")
    if work:
        who.append(f"people who work at {' or '.join(work)}")
    kind = ("plot buyers (a home to build later, or land near their work)" if plot else "home buyers") + (
        "; this is a whole project, so the price is where it starts" if layout else "")
    return ("Who sees this post: " + "; ".join(who) + f"; mostly {kind}. Write for them, in their terms. When it fits this "
            "post (not every post, vary it), you may speak to them directly: a question about where they live or work, a "
            "nearby town or workplace that a fact above names, or a closing question they answer by naming their town. "
            "Never invent a distance, a time or a place that the facts do not give.")


def previous_note(previous: Sequence[str]) -> str:
    if not previous:
        return ""
    return ("Already posted for this property (do not repeat these openings; take a new angle or a new detail of the same "
            "fact):\n" + "\n".join(f"- {p}" for p in previous[:12]))


MAX_PLOT_SQFT = 20_000   # half an acre: a bigger "plot size" is the whole layout's area typed in the size field


class Ctx:
    """Usable fact values, with the names every angle needs."""

    def __init__(self, facts: Dict[str, Fact], photo: str = "none", link: str = "", voice: Optional[Voice] = None,
                 card_brand: Optional[CardBrand] = None, contact: Sequence[str] = (), language: str = "en",
                 previous: Sequence[str] = (), names: Optional[Dict[str, str]] = None, claims: Sequence[str] = (),
                 today: Optional[date] = None):
        self.v: Dict[str, Any] = {k: f.value for k, f in facts.items() if f.usable}
        self.today = today or date.today()
        # the builder's claims (listing.file_claims.brochure): only their wording of a place's name is used, never a number
        self.claims = [str(x) for x in list(claims) + list(self.v.get("claims.brochure") or []) if x]
        self.used: set = set()   # facts an earlier angle already headlined ("price", "place:Ranjangaon MIDC")
        self.previous = list(previous)   # opening lines of this property's posts that are already live
        self.photo, self.link = photo, link
        self.project = self.v.get("project_name") or ""
        # the project's name as every post of this campaign writes it (Devanagari in a Marathi/Hindi campaign when chosen)
        self.name = (names or {}).get(self.project) or self.project
        # an English campaign keeps its name as written; a Marathi/Hindi one only when make() chose its spelling (names)
        self.names = {self.project: self.name} if self.project and (names or language == "en") else {}
        self.locality = self.v.get("locality") or ""
        areas = ", ".join(p for p in (self.locality, self.v.get("city") or "Pune") if p) if self.locality else ""
        v = voice or Voice()
        self.voice = v if v.areas else replace(v, areas=areas)  # who speaks; the prompts set the post in this area
        self.contact, self.language = list(contact), language  # an agent's contact lines and the post language
        if card_brand is not None:  # an agent's cards also carry this listing's price and MahaRERA number
            price = price_label(self.v["price_inr"]) if self.v.get("price_inr") else ""
            card_brand = replace(card_brand, price=card_brand.price or price, rera=card_brand.rera or str(self.v.get("rera_no") or ""))
        self.card_brand = card_brand
        self.where = ", ".join(p for p in (self.project, self.locality) if p)
        self.where_named = ", ".join(p for p in (self.name, self.locality) if p)
        self.plot = self.v.get("property_type") == "plot"
        self.kind = "plot" if self.plot else "home"
        self.layout = self.v.get("listing_scope") == "layout"   # a whole project: the price is a starting price
        self.registered = bool(self.v.get("rera_no"))
        # one unit's size, never more than MAX_PLOT_SQFT for a plot or layout: its plot/carpet field can hold the whole layout
        # (live 2026-10-10, Gulmohar City: its 30 acres, 1,306,800 sq ft, posted as "this plot is 1200 guntha")
        sqft = self.v.get("size_min_sqft") or self.v.get("plot_sqft") or self.v.get("carpet_sqft")
        self.sqft = None if not sqft or (self.plot or self.layout) and float(sqft) > MAX_PLOT_SQFT else sqft
        self.readers = reader_note(self.v, self.plot, self.layout)

    def place(self, key: str, p: Dict[str, Any]) -> str:
        """A nearby place as a buyer names it (surroundings.short_name), in the builder's brochure wording when a claim names
        the same place ("Ranjangaon MIDC 10 min" -> "Ranjangaon MIDC")."""
        short = surroundings.short_name(key, p.get("name") or "", self.locality or self.v.get("taluka") or "")
        mine, core = _tokens(short) | _tokens(p.get("name") or ""), _tokens(short)
        for claim in self.claims:
            for m in _CLAIMED_PLACE.finditer(claim):
                said = m.group(1).strip(" -,:")
                theirs = _tokens(said)
                if theirs and theirs <= mine and len(theirs & core) >= min(2, len(core)):
                    return said
        return short

    def tags(self) -> List[str]:
        words = [w.capitalize() for w in self.locality.split()]
        return ["#" + "".join(words)] * bool(words) + ["#PuneProperty", "#PlotsInPune" if self.plot else "#PuneHomes", "#MahaRERA"]

    def brief(self, hook: str = "", angle: str = "", **kw) -> Brief:
        """A Brief with this property's tags, photo, link and chip; `hook` (when given) opens the post whatever pattern runs;
        `angle` picks the closing question (ASKS)."""
        if hook:
            kw["hooks"] = {p: hook for p in PATTERNS}
        if angle in ASKS:
            kw.setdefault("asks", dict(ASKS[angle]))
        kw.setdefault("kicker", self.name.upper()[:28])
        where = self.where or "this property"
        named = self.where_named
        if named and self.language in ("mr", "hi"):   # the place as the language spells it, the name as the campaign writes it
            named = ", ".join(i18n.PLACES.get(p.strip(), {}).get(self.language, p.strip()) for p in named.split(","))
        kw.setdefault("intro", f"{named}." if self.where else "")
        kw.setdefault("link_line", link_line_for(self.where_named or where, self.language, self.registered))
        kw.setdefault("names", dict(self.names))
        if kw.get("prefer") != "poll":   # the last card asks for a WhatsApp message (a poll's card asks for a vote)
            kw.setdefault("cta", i18n.WHATSAPP_US)
        what = f"a project of many {self.kind}s, {where}, whose price is a starting price" if self.layout else f"one property: {where}"
        kw.setdefault("writer_note", "\n".join(n for n in (
            f"This post markets {what}. Its listed price, project name, MahaRERA details and nearby places are facts you "
            "may use exactly as written; add no other number.", self.readers, previous_note(self.previous)) if n))
        kw.setdefault("hashtags", self.tags())
        kw.setdefault("photo", self.photo)
        kw.setdefault("link", self.link)
        kw.setdefault("voice", self.voice)
        kw.setdefault("mode", "listing")
        kw.setdefault("card_brand", self.card_brand)
        kw.setdefault("contact", list(self.contact))
        kw.setdefault("language", self.language)
        return Brief(**kw)


_CLAIMED_PLACE = re.compile(r"([A-Z][A-Za-z.&' -]{1,40}?)\s*[-:,(]?\s*\d+\s*(?:min|mins|minutes)\b")
_GENERIC_WORDS = {"the", "of", "and", "to", "from", "near", "only", "just", "away", "drive"}


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z]{3,}", (text or "").lower()) if t not in _GENERIC_WORDS}


def price_reveal(c: Ctx) -> Optional[Brief]:
    if not (c.v.get("price_inr") and c.sqft):
        return None
    price = price_label(c.v["price_inr"])
    if c.layout:
        line = f"{c.kind.capitalize()}s at {c.where} start at {price}, for {c.sqft:,} sq ft."
        c.used.add("price")
        return c.brief(angle="price_reveal", hook=f"{c.kind.capitalize()}s from {price} in {c.project or c.locality}",
                       topic=f"Starting price at {c.where}", short="starting price", stat_value=price,
                       stat_label=f"starting price for a {c.kind}", facts=[line],
                       tip="Ask what the price includes: development charges, stamp duty and registration.", prefer="stat")
    line = f"A {c.sqft:,} sq ft {c.kind} at {c.where} is listed at {price}."
    c.used.add("price")
    return c.brief(angle="price_reveal", hook=f"{price} for a {c.kind} in {c.project or c.locality}", topic=f"Price of a {c.kind} at {c.where}", short=f"{c.kind} price", stat_value=price,
                   stat_label=f"for this {c.kind}", facts=[line],
                   tip="Ask what the price includes: development charges, stamp duty and registration.", prefer="stat")


# The RERA-safe line under any booking amount (a builder takes at most 10% before a registered agreement, RERA s.13)
BALANCE_LINE = {"en": "Balance as per the registered agreement.", "mr": "शिल्लक रक्कम नोंदणीकृत करारानुसार.",
                "hi": "बाकी राशि पंजीकृत अनुबंध के अनुसार."}


def offer(c: Ctx) -> Optional[Brief]:
    """The starting price and the booking amount, from the agent-confirmed selling points only. The offer's printed name is
    never used ("pre-launch" cannot be advertised before MahaRERA registration)."""
    booking = c.v.get("point.booking_amount")
    if not booking:
        return None
    start = c.v.get("point.starting_price") or (c.v.get("price_inr") if c.layout else None)
    book = price_label(int(booking))
    kinds = f"{c.kind.capitalize()}s"
    facts = [f"Booking amount at {c.where or 'this project'}: {book}.", BALANCE_LINE["en"]]
    if start:
        price = price_label(int(start))
        facts.insert(0, f"{kinds} at {c.where or 'this project'} start at {price}.")
        hook, stat, label = f"{kinds} from {price} · Book with {book}", book, f"to book; {kinds.lower()} from {price}"
    else:
        hook, stat, label = f"Book with {book} at {c.project or c.locality}", book, "to book"
    c.used.add("booking")
    return c.brief(angle="offer", hook=hook, topic=f"Booking at {c.where}", short="booking amount", stat_value=stat,
                   stat_label=label, facts=facts, tip=BALANCE_LINE["en"], prefer="stat")


def amenities(c: Ctx) -> Optional[Brief]:
    """Water, power, roads and vastu as one checklist card, from the agent-confirmed selling points only (at least two)."""
    steps = []
    for key, word in (("water", "Water"), ("power", "Power")):
        v = c.v.get(f"point.{key}")
        if v:
            steps.append(f"{word}: {v}")
    roads = c.v.get("point.roads")
    if roads:
        xs = [str(x) for x in roads]
        steps.append("Roads " + (xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]) + " ft wide")
    if c.v.get("point.vastu") is True:
        steps.append(f"{c.kind.capitalize()}s as per vastu")
    if len(steps) < 2:
        return None
    return c.brief(angle="amenities", hook=f"What {c.project or c.locality or 'the project'} gives every {c.kind}",
                   topic=f"Basics at {c.where}", short="water, power, roads", steps=steps, facts=steps,
                   tip="See the water source and the power line on your site visit.", prefer="checklist")


def size_in_guntha(c: Ctx) -> Optional[Brief]:
    lo, hi = c.v.get("size_min_sqft"), c.v.get("size_max_sqft")
    if c.plot and c.layout and lo and hi and hi > lo:
        glo, ghi = calc.guntha(lo), calc.guntha(hi)
        line = f"Plot sizes at {c.where}: {lo:,} to {hi:,} sq ft, that is {glo:g} to {ghi:g} guntha. 1 guntha is 1,089 sq ft."
        return c.brief(angle="size_in_guntha", hook=f"{glo:g} to {ghi:g} guntha: plot sizes at {c.project or c.locality}",
                       topic="How big are these plots?", short="plot sizes", stat_value=f"{glo:g}-{ghi:g} guntha",
                       stat_label="plot sizes on offer", facts=[line],
                       tip="Walk the boundary stones on site before you pay a token.", prefer="stat")
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
    if not e or c.layout:  # a starting price: an EMI on it would read as the EMI of every unit
        return None
    loan = price_label(e["loan"])
    rate = f"{e['rate']:g}%"
    line = f"EMI of ₹{e['emi']:,} a month on a {loan} loan (80% of the price) at {rate} for {e['years']} years."
    return c.brief(angle="emi", hook=f"₹{e['emi']:,} a month for this {c.kind}", topic=f"Monthly EMI for this {c.kind}", short="monthly EMI", stat_value=f"₹{e['emi']:,}",
                   stat_label=f"a month EMI for this {c.kind}", facts=[line],
                   tip="Ask your bank for its actual rate before you plan.", prefer="stat")


POSSESSION_CARD_MONTHS = 18   # a completion date further off than this is not something an ad leads with


def possession_card_ok(c: Ctx) -> bool:
    """A completion date may go on a card only when MahaRERA has not moved it (a moved date reads as "delayed" to a buyer;
    it stays in the facts, the fact sheet and the project page) and it is near: within POSSESSION_CARD_MONTHS."""
    now = c.v.get("possession_now")
    if not now or (c.v.get("possession_moved_months") or 0) > 0:
        return False
    try:
        y, m = int(str(now)[:4]), int(str(now)[5:7])
    except (TypeError, ValueError):
        return False
    months = (y - c.today.year) * 12 + (m - c.today.month)
    return 0 <= months <= POSSESSION_CARD_MONTHS


def possession(c: Ctx) -> Optional[Brief]:
    now = c.v.get("possession_now")
    if not possession_card_ok(c):
        return None
    facts = [f"MahaRERA completion date for {c.project}: {day(now)}."]
    return c.brief(angle="possession", topic=f"Completion date of {c.project}", short="completion date", stat_value=day(now),
                   stat_label="MahaRERA completion date", facts=facts,
                   tip="Check the MahaRERA date, not the brochure.", prefer="stat")


def rera_check(c: Ctx) -> Optional[Brief]:
    rera = c.v.get("rera_no")
    if not rera:
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


# what a buyer asks about first; one place of each kind before a second of any kind
NEARBY_ORDER = ("bus", "railway", "airport", "hospital", "school", "college", "market", "industry", "temple", "bank")


def nearby(c: Ctx) -> Optional[Brief]:
    """Up to 6 places, one per kind first (bus stand, station, hospital, school...), none that an earlier post headlined."""
    near = [(k, p, c.place(k, p)) for k, p in _near(c)]
    near = [x for x in near if f"place:{x[2]}" not in c.used]
    rank = {k: i for i, k in enumerate(NEARBY_ORDER)}
    first: Dict[str, Tuple[str, Dict[str, Any], str]] = {}
    for x in near:
        first.setdefault(x[0], x)
    picks = sorted(first.values(), key=lambda x: rank.get(x[0].split(".", 1)[-1], len(rank)))[:6]
    picks += [x for x in near if x not in picks][:6 - len(picks)]
    if len(picks) < 3:
        return None
    picks.sort(key=lambda x: x[1]["km"])
    c.used.update(f"place:{n}" for _, _, n in picks)
    steps = [f"{surroundings.label(k)}: {n}, about {_km(p['km'])}" for k, p, n in picks]
    return c.brief(angle="nearby", hook=f"What is near {c.project or c.locality}?", topic=f"What is near {c.where}", short="what is nearby", steps=steps, facts=steps,
                   tip="Distances are straight-line; drive the route once at peak hour.", prefer="carousel")


def near_work(c: Ctx) -> Optional[Brief]:
    work = (c.v.get("nearby.industry") or [])
    if not work:
        return None
    named = [(p, c.place("industry", p)) for p in work]
    w, name = named[0]
    c.used.add(f"place:{name}")
    lines = [f"{n} is about {_km(p['km'])} away (straight line)." for p, n in named]
    return c.brief(angle="near_work", hook=f"{_km(w['km'])} from {c.project or c.locality} to work", topic=f"Work nearby: {c.where}", short="work nearby", stat_value=_km(w["km"]),
                   stat_label=f"to {name}", facts=lines,
                   tip="Drive to work once at shift-change time before you decide.", prefer="stat")


def layout_size(c: Ctx) -> Optional[Brief]:
    units, on = c.v.get("units_total"), c.v.get("registered_on")
    if not units:
        return None
    unit = "plots" if c.plot else "homes"
    line = f"{c.project} has {units} {unit}, registered on MahaRERA" + (f" on {day(on)}." if on else ".")
    return c.brief(angle="layout_size", hook=f"{units} {unit} in {c.project}", topic=f"How big is {c.project}?", short="project size", stat_value=str(units),
                   stat_label=f"{unit} in {c.project}", facts=[line],
                   tip="A smaller layout means fewer neighbours sharing the roads and water.", prefer="stat")


def land_area(c: Ctx) -> Optional[Brief]:
    acres = c.v.get("total_acres")
    if not (c.layout and acres):
        return None
    units = c.v.get("units_total")
    unit = "plots" if c.plot else "homes"
    line = f"{c.project or c.where} is spread over {acres:g} acres" + (f", with {units} {unit}." if units else ".")
    return c.brief(angle="land_area", hook=f"{acres:g} acres: {c.project or c.locality}", topic=f"How big is {c.project or c.where}?",
                   short="land area", stat_value=f"{acres:g} acres", stat_label=f"of land at {c.project or c.locality}", facts=[line],
                   tip="Ask how much of the land is roads and open space.", prefer="stat")


def plot_or_flat(c: Ctx) -> Optional[Brief]:
    if not c.v.get("price_inr") or "price" in c.used:   # the price post already headlined this price
        return None
    price = price_label(c.v["price_inr"])
    if c.layout:
        return c.brief(angle="plot_or_flat", hook=f"Plot or flat from {price}?", topic=f"Plot or flat from {price}?", short="plot or flat",
                       question=f"Plot or flat from {price}?", options=["A plot", "A flat"],
                       facts=[f"Plots at {c.where} start at {price}."], prefer="poll")
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


def overview(c: Ctx) -> Optional[Brief]:
    """The whole property on one carousel: price on the cover, then size, location, possession and the visit slide.
    A slide whose facts are missing is left out; under 3 slides there is no overview."""
    price = price_label(c.v["price_inr"]) if c.v.get("price_inr") else ""
    steps = []
    lo, hi, units = c.v.get("size_min_sqft"), c.v.get("size_max_sqft"), c.v.get("units_total")
    unit = "plots" if c.plot else "homes"
    if c.layout and lo and hi and hi > lo:
        steps.append(f"{lo:,} to {hi:,} sq ft" + (f", {units} {unit} in all." if units else "."))
    elif c.sqft:
        steps.append(f"{c.sqft:,} sq ft {c.kind}" + (f", one of {units} {unit}." if units else "."))
    elif units:
        steps.append(f"{units} {unit} in {c.project or c.locality}.")
    near = _near(c)[:2]
    if c.locality or near:
        at = f"In {c.locality}" if c.locality else "Nearby"
        steps.append(at + ("" if not near else ": " + ", ".join(f"{c.place(k, p)} {_km(p['km'])}" for k, p in near)) + ".")
    now, rera = c.v.get("possession_now"), c.v.get("rera_no")
    now = now if possession_card_ok(c) else None   # a moved or far-off date is not put on a card
    if now or rera:
        steps.append((f"Completion {day(now)} on MahaRERA" if now else "Registered on MahaRERA") + (f" ({rera})." if rera else "."))
    if len(steps) < 2:   # with the visit slide below, fewer than 3 slides: not an overview
        return None
    steps.append("Book a site visit: full details in the caption.")
    lead = (f"{c.kind.capitalize()}s from {price}" if c.layout else f"{price} for a {c.kind}") if price else f"A {c.kind}"
    hook = f"{lead} at {c.project or c.locality}" if (c.project or c.locality) else lead
    facts = [f"{c.kind.capitalize()}s at {c.where} start at {price}." if c.layout else f"This {c.kind} at {c.where} is listed at {price}."] if price else []
    return c.brief(angle="overview", hook=hook, topic=f"{c.where or 'This property'} at a glance", short="property overview",
                   steps=steps, facts=facts + steps, tip="Visit the site and match every detail with MahaRERA.", prefer="carousel")


@dataclass(frozen=True)
class AngleDef:
    id: str
    build: Callable[[Ctx], Optional[Brief]]


FOLLOW_UPS = 4  # angles posted after the overview, the first ones in ANGLES order that the facts support
# What a buyer asks first: the price, then the EMI, the size, how far, the land, and the checks last. A possession card comes
# only for a near, unmoved date (possession_card_ok), after the land.
ANGLES: Tuple[AngleDef, ...] = tuple(AngleDef(f.__name__, f) for f in (
    overview, price_reveal, offer, emi, size_in_guntha, amenities, near_work, land_area, possession, nearby, rate_per_sqft, layout_size, rera_check,
    plot_checklist, plot_or_flat, plot_myth))


def brief_key(brief: Brief) -> str:
    """What a post says, as a short hash: it changes when a fact the post uses changes (not with its picture)."""
    text = "\n".join((brief.corpus(), next(iter(brief.hooks.values()), ""), brief.language or ""))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def plan(facts: Dict[str, Fact], photo: str = "none", link: str = "", angles: Sequence[AngleDef] = ANGLES,
         voice: Optional[Voice] = None, card_brand: Optional[CardBrand] = None, contact: Sequence[str] = (),
         language: str = "en", previous: Sequence[str] = (), follow_ups: Optional[int] = FOLLOW_UPS,
         skipped: Optional[Dict[str, str]] = None, names: Optional[Dict[str, str]] = None, claims: Sequence[str] = (),
         today: Optional[date] = None) -> List[Tuple[str, Brief]]:
    """`skipped` (when given) gets each angle left out and why;
    `voice`, `card_brand`, `contact`, `language`: whose posts these are (default ours) and in which language;
    `previous`: opening lines of this property's posts already live (the writers are told not to repeat them);
    `follow_ups`: how many angles after the overview (None: every one, so an older run's post can still be edited);
    `names`: the project's name as this campaign writes it ({"Gulmohar City": "गुलमोहर सिटी"}: project_name_for);
    `claims`: the builder's brochure claims (their wording of a place is preferred); `today`: for the possession rule."""
    c = Ctx(facts, photo, link, voice, card_brand, contact, language, previous, names, claims, today)
    out = []
    from .points import PRELAUNCH
    for a in angles:
        if follow_ups is not None and len([1 for aid, _ in out if aid != "overview"]) >= follow_ups and a.id != "overview":
            if skipped is not None:
                skipped[a.id] = "enough posts already"
            continue
        b = a.build(c)
        if b is not None and PRELAUNCH.search(" ".join((b.corpus(), *b.hooks.values()))):   # never advertised
            b = None
        if b is not None:
            out.append((a.id, b))
        elif skipped is not None:
            skipped[a.id] = "the facts do not support it"
    return out


SHARPEN_SYSTEM = (
    "You are the headline writer of an Indian real-estate agent's Instagram. You rewrite one card headline so a home buyer "
    "stops scrolling: concrete, human, about the buyer's life (their commute, their family, their papers, their money), a "
    "question or a surprising contrast is welcome. You are told who sees the post: speak to them when it fits (where they "
    "live or work), but not in the same way every time, and never like the headlines already posted. Hard rules: keep every number exactly as written (same digits, same "
    "units, same rupee amounts) and add no other number; add no fact that is not in the headline or the facts; no hype "
    "(best, perfect, dream, luxury, premium, guaranteed, safe investment, returns), no 'only/just', no emojis, at most 10 "
    "words. Think like the sales lead who knows the buyer's first question (where, how far, what size, ready or not) and "
    "like the designer whose headline must read in one glance in large type: put the key number or place first. "
    'Reply with JSON only: {"headline": "..."}'
)
_NUM = re.compile(r"\d[\d,.]*")


def _numbers(text: str) -> List[str]:
    return sorted(n.rstrip(".,").replace(",", "") for n in _NUM.findall(text or ""))


async def sharpen(brief: Brief, llm: Any) -> Brief:
    """A sharper headline from the LLM, kept only when it says the same numbers as the code's headline and passes the post
    checks; otherwise the brief is returned unchanged. The facts stay the code's: only the words around them change."""
    from app.modules.creative.guards import problems_in
    old = next(iter(brief.hooks.values()), "")
    if not old:
        return brief
    facts = "; ".join(str(f) for f in (brief.facts or []))[:1500]
    try:
        reply = await llm.json(SHARPEN_SYSTEM, f"Headline: {old}\nFacts: {facts}\n{brief.writer_note}") or {}
    except Exception:
        return brief
    new = re.sub(r"\s+", " ", str(reply.get("headline") or "")).strip().strip('"')
    lost = any(en.lower() in old.lower() and en.lower() not in new.lower() for en in brief.names)  # names stay as written
    if (not new or new == old or len(new.split()) > 10 or _numbers(new) != _numbers(old) or lost
            or problems_in(new, f"{old} {facts}")):
        return brief
    return replace(brief, hooks={p: new for p in brief.hooks})


NAME_SYSTEM = ("You write an Indian real-estate project's name in {lang}, as buyers there read it aloud (a transliteration, "
               "not a translation). Reply with JSON only: {{\"name\": \"...\"}}")
_DEVANAGARI_NAME = re.compile(r"^[\u0900-\u097F ]{2,40}$")


async def project_name_for(project: str, language: str, llm: Any) -> Dict[str, str]:
    """{project: the one spelling every post of this campaign uses}: in a Marathi/Hindi campaign the name in Devanagari, asked
    once (so card 1 and card 5 never differ); otherwise, or without a usable answer, the English spelling everywhere."""
    if not project:
        return {}
    if language in ("mr", "hi") and llm is not None:
        try:
            reply = await llm.json(NAME_SYSTEM.format(lang="Marathi (Devanagari script)" if language == "mr"
                                                      else "Hindi (Devanagari script)"), project)
        except Exception:
            reply = None
        name = re.sub(r"\s+", " ", str(reply.get("name") or "")).strip() if isinstance(reply, dict) else ""
        if _DEVANAGARI_NAME.match(name):
            return {project: name}
    return {project: project}


RETRIES = 3  # other seeds (other layouts) to try before an angle is dropped: some layouts cannot fit some texts


async def make(facts: Dict[str, Fact], out_dir: Path, llm: Any = None, photo: str = "none", link: str = "",
               channel: str = "instagram", dropped: Optional[Dict[str, Any]] = None,
               voice: Optional[Voice] = None, card_brand: Optional[CardBrand] = None, contact: Sequence[str] = (),
               language: str = "en", photos: Sequence[str] = (), previous: Sequence[str] = (),
               on_plan: Optional[Callable[[List[dict], Dict[str, str]], Awaitable[None]]] = None,
               on_post: Optional[Callable[[str, dict], Awaitable[None]]] = None,
               used: Optional[Dict[str, str]] = None, claims: Sequence[str] = (),
               today: Optional[date] = None, names: Optional[Dict[str, str]] = None) -> List[Tuple[str, CreativePack]]:
    """Render every planned angle; consecutive posts avoid repeating a layout. `photos` (the property's own: listing photos and
    the best frames of its video, best first) are shared out so each post shows a different one behind its text. An angle that fails a guard is retried with
    other seeds, then dropped (its problems go into `dropped` when given). `voice`: who speaks (default the brand desk).
    `on_plan(chosen, skipped)` hears the plan before anything is written; `on_post(angle, {"headline", "was", "state"})` hears
    each post as it is written ("content") and then designed ("designed" or "dropped"). `used` (when given) gets each angle's
    picture (a path, or "none")."""
    packs: List[Tuple[str, CreativePack]] = []
    recent: List[str] = []
    skipped: Dict[str, str] = {}
    pf = facts.get("project_name")
    if names is None:  # `names`: the spelling the run already chose (kept on the run, so redraws match)
        names = await project_name_for(str(pf.value or "") if pf is not None and pf.usable else "", language, llm)
    planned = plan(facts, photo, link, voice=voice, card_brand=card_brand, contact=contact, language=language,
                   previous=previous, skipped=skipped, names=names, claims=claims, today=today)
    if on_plan is not None:
        await on_plan([{"angle": aid, "headline": next(iter(b.hooks.values()), "")} for aid, b in planned], skipped)
    for i, (aid, brief) in enumerate(planned):
        if photos:
            brief = replace(brief, photo=photos[i % len(photos)])
        if used is not None:
            used[aid] = str(brief.photo or "none")
        was = next(iter(brief.hooks.values()), "")
        if llm is not None and brief.hooks:
            brief = await sharpen(brief, llm)
        now_ = next(iter(brief.hooks.values()), "")
        if on_post is not None:
            await on_post(aid, {"headline": now_, "was": was if was != now_ else "", "state": "content"})
        for attempt in range(RETRIES):
            pack = await pipeline.make(brief, "buyer", channel, llm, seed=i + 17 * attempt, recent_layouts=recent,
                                       out_dir=Path(out_dir) / aid, reviewer=None)
            if pack.report.get("ok"):
                packs.append((aid, pack))
                recent.append(str(pack.design.get("layout")))
                if on_post is not None:
                    await on_post(aid, {"state": "designed"})
                break
        else:
            if on_post is not None:
                await on_post(aid, {"state": "dropped"})
            log.info("campaign angle %s dropped: %s", aid, pack.report.get("problems"))
            if dropped is not None:
                dropped[aid] = pack.report.get("problems")
    return packs
