"""Plain data passed between the creative stages. No behaviour beyond small helpers, no I/O."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

AUDIENCES = ("buyer", "agent")
CHANNELS = ("instagram", "facebook")
FORMATS = ("single", "carousel", "myth-vs-fact", "stat", "checklist", "before-after", "poll")
SIZES = {"instagram": (1080, 1350), "facebook": (1080, 1080)}


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

    def corpus(self) -> str:
        """Every string a number or claim may legitimately come from."""
        parts = [self.topic, self.short, self.stat_value, self.stat_label, self.myth, self.truth, self.question,
                 self.tip, *self.facts, *self.options, *self.messy, *self.clean, *self.steps, *self.compare]
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

    def caption(self, channel: str, link: str = "") -> str:
        parts = [self.caption_first_line.strip()]
        if self.body.strip():
            parts.append(self.body.strip())
        if self.cta_question.strip():
            parts.append(self.cta_question.strip())
        if channel == "instagram":
            if link:
                parts.append("Full guide: link in our bio.")
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
