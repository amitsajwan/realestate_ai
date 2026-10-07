"""Plain data passed between the creative stages. No behaviour beyond small helpers, no I/O."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.core import brand

AUDIENCES = ("buyer", "agent")
CHANNELS = ("instagram", "facebook")
FORMATS = ("single", "carousel", "myth-vs-fact", "stat", "checklist", "before-after", "poll")
SIZES = {"instagram": (1080, 1350), "facebook": (1080, 1080)}


@dataclass(frozen=True)
class Voice:
    """Who speaks in the prompts and the sign-off. The default is the brand's own desk."""
    name: str = brand.NAME
    team: str = brand.TEAM
    areas: str = ""                       # where a listing post is set ("Ranjangaon, Pune"); the brand prompts name their own areas


@dataclass(frozen=True)
class CardBrand:
    """Whose name is on the card footer. None on a Brief means the brand's own (logo, name, tagline). An agent's card shows
    their logo, name and phone instead; the phone is drawn by code, never written by a model."""
    name: str
    line: str = ""                        # second footer line: "Call +91 99219 93099" (or a tagline)
    logo: str = ""                        # local image file; a square logo is drawn in a circle; missing -> a plain disc
    phone: str = ""                       # "+91 99219 93099": with it, single cards and a carousel's last slide carry a
                                          # contact strip (name, phone, price, MahaRERA number)
    price: str = ""                       # "₹32.3 lakh" (the listing's price, when known)
    rera: str = ""                        # "P52100076768" (the MahaRERA number, when known)


LANGUAGES = ("en", "mr", "hi")


@dataclass
class Brief:
    """What the desk knows. `facts` is the ONLY source of numbers and claims. The optional fields carry ready structure
    (short, factual strings) that lets a format be drawn; a format is possible only if its fields are present."""
    topic: str
    facts: List[str] = field(default_factory=list)
    short: str = ""                       # 2-4 word name of the subject, e.g. "site visits", "RERA number"
    stat_value: str = ""                  # "3", "4 months", "0"
    stat_label: str = ""                  # "site visits before you pay a token"
    myth: str = ""                        # a belief people hold (<= 9 words)
    truth: str = ""                       # the correction (<= 14 words)
    question: str = ""                    # poll question
    options: List[str] = field(default_factory=list)  # exactly two short choices
    messy: List[str] = field(default_factory=list)    # "what goes wrong" items
    clean: List[str] = field(default_factory=list)    # "what good looks like" items
    compare: Tuple[str, str] = ("", "")   # ("Messy file", "Clean file") for the comparison hook
    steps: List[str] = field(default_factory=list)    # checklist / carousel items (<= 14 words each)
    tip: str = ""                         # one line for the quote/tip card
    photo: str = ""                       # key of a bundled photo, optional
    cta: str = ""                         # optional override of the card call to action
    link: str = ""                        # Facebook caption link, optional
    hashtags: List[str] = field(default_factory=list)
    hooks: Dict[str, str] = field(default_factory=dict)  # optional hand-written hooks by pattern id
    prefer: str = ""                      # optional format the desk wants (used when the brief supports it); otherwise rotated
    kicker: str = ""                      # optional chip text on the card ("GULMOHAR CITY"); otherwise one per format
    intro: str = ""                       # optional caption intro line, instead of the format's generic one
    link_line: str = ""                   # optional Instagram line pointing to the link in bio, instead of "Full guide: ..."
    writer_note: str = ""                 # optional extra context for the LLM copywriter (a property post may use its price)
    voice: Voice = field(default_factory=Voice)
    mode: str = "brand"                   # "brand" (explainers: no prices) or "listing" (markets one property); see prompts.py
    card_brand: Optional[CardBrand] = None  # an agent's footer on the cards; None = the brand's own
    contact: List[str] = field(default_factory=list)  # lines code adds to every caption ("📞 +91 ...", "🌐 house-deal.com")
    language: str = "en"                  # "mr"/"hi": the cards and caption are translated after the English copy passes
    asks: Dict[str, str] = field(default_factory=dict)  # the caption's closing question by language ("en", "mr", "hi"),
                                          # written for this post's subject; replaces the format's generic question
    listing_transaction: str = ""
    listing_property_type: str = ""
    listing_price_inr: str = ""
    listing_bhk: str = ""
    listing_carpet_sqft: str = ""
    listing_locality: str = ""
    listing_project_name: str = ""
    listing_rera_no: str = ""
    listing_amenities: List[str] = field(default_factory=list)
    listing_media_refs: List[str] = field(default_factory=list)  # photo URLs; kept out of corpus() (URLs carry stray digits)

    def corpus(self) -> str:
        """Every string a number or claim may legitimately come from."""
        parts = [self.topic, self.short, self.stat_value, self.stat_label, self.myth, self.truth, self.question,
                 self.tip, self.listing_transaction, self.listing_property_type, self.listing_price_inr,
                 self.listing_bhk, self.listing_carpet_sqft, self.listing_locality, self.listing_project_name,
                 self.listing_rera_no, *self.facts, *self.options, *self.messy, *self.clean, *self.steps,
                 *self.compare, *self.listing_amenities]
        return " \n ".join(p for p in parts if p)

    def formats(self) -> List[str]:
        """Formats this brief has the material for, in a stable order."""
        out = []
        if self.stat_value and self.stat_label:
            out.append("stat")
        if self.myth and self.truth:
            out.append("myth-vs-fact")
        if len(self.options) == 2 and self.question:
            out.append("poll")
        if len(self.messy) >= 2 and len(self.clean) >= 2:
            out.append("before-after")
        if len(self.steps) >= 3:
            out += ["carousel", "checklist"]
        out.append("single")
        return out


@dataclass
class Angle:
    audience: str
    channel: str
    pain: str            # the audience pain or desire, one sentence
    idea: str            # the one idea the post carries
    hook: str            # <= 9 words
    pattern: str         # hook pattern id
    proof: List[str]     # facts, all taken from the brief
    fmt: str             # one of FORMATS
    cta: str             # what we ask the viewer to do
    source: str = "rules"  # "llm" or "rules"


@dataclass
class Copy:
    hook: str
    support: str                      # one line under the hook (<= 14 words); may be ""
    slides: List[str]                 # carousel / checklist slide texts (<= 14 words each)
    caption_first_line: str
    body: str
    cta_question: str
    hashtags: List[str]
    card_cta: str = ""                # the short line on the card ("Save this", "Comment INTERESTED")
    payload: Dict[str, object] = field(default_factory=dict)  # structure for the layouts (stat, myth, options, ...)
    variants: Dict[str, str] = field(default_factory=dict)    # "hinglish" / "marathi" captions, when asked
    source: str = "rules"
    link_line: str = ""               # Instagram's pointer to the link in bio (Brief.link_line), else the default
    contact: List[str] = field(default_factory=list)  # Brief.contact: added after the copy, never checked as copy
    language: str = "en"              # the language the card texts and caption are in

    def caption(self, channel: str, link: str = "") -> str:
        parts = [self.caption_first_line.strip()]
        if self.body.strip():
            parts.append(self.body.strip())
        if self.cta_question.strip():
            parts.append(self.cta_question.strip())
        if self.contact:
            parts.append("\n".join(self.contact))
        if channel == "instagram":
            if link:
                parts.append(self.link_line or "Full guide: link in our bio.")
        elif link:
            parts.append(f"\U0001F517 {link}")
        parts.append(" ".join(self.hashtags))
        return "\n\n".join(p for p in parts if p)


@dataclass
class Design:
    layout: str
    palette: str
    photo: str = ""
    emphasis: Tuple[str, ...] = ()
    size: Tuple[int, int] = (1080, 1350)
    notes: str = ""
    brand: Optional[CardBrand] = None  # Brief.card_brand, for the footer


@dataclass
class Problem:
    rule: str
    message: str
    severity: str = "error"   # "error" blocks the pack, "warn" is advice


@dataclass
class Report:
    problems: List[Problem] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(p.severity == "error" for p in self.problems)

    def errors(self) -> List[Problem]:
        return [p for p in self.problems if p.severity == "error"]

    def as_dict(self) -> dict:
        return {"ok": self.ok, "problems": [{"rule": p.rule, "message": p.message, "severity": p.severity} for p in self.problems]}


@dataclass
class CreativePack:
    channel: str
    audience: str
    images: List[str]                 # file paths, cover first
    caption: str
    hashtags: List[str]
    design: Dict[str, object]
    report: Dict[str, object]
    angle: Dict[str, object] = field(default_factory=dict)
    alt_text: str = ""
    variants: Dict[str, str] = field(default_factory=dict)
    used_llm: bool = False
    attempts: int = 1
    prompts: List[str] = field(default_factory=list)  # tags of the prompts whose output was kept ("copywriter@1/listing")
