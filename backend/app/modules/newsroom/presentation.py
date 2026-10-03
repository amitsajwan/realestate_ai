"""How an approved item is shown: headline, summary parts, card hook, 'as of' date, our own page URL. Pure functions over the stored
item document, no I/O. Everything here is cut from the checked draft and its facts; nothing is invented.

The stored draft text is a post such as 'what\\n\\nOur view: ..\\n\\nWhat to check: ..\\n\\nSource: X, as of 5 Oct 2026. <url>\\n\\n<question>\\n\\n#tags';
`split_text` takes it apart so the website, the cards and the captions can each reuse the parts."""
from app.core import brand
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from . import policy

URL = re.compile(r"https?://\S+|www\.\S+", re.I)
TAG = re.compile(r"#\w+")
PHONE = re.compile(r"(?<!\w)(?!\d{4}-\d{2}-\d{2}(?!\d))\+?\d[\d\s\-]{8,}\d(?!\w)")  # a date like 2026-10-01 is not a phone
BRAND = brand.TEAM
SPACE = re.compile(r"\s+")
AREA_NAMES = {"kharadi": "Kharadi", "upper_kharadi": "Upper Kharadi", "wagholi": "Wagholi"}
AREA_SLUGS = {"kharadi": "kharadi", "upper_kharadi": "upper-kharadi", "wagholi": "wagholi"}
PILLAR_LABELS = {"infrastructure": "Infrastructure", "new_supply": "New supply", "rules_money": "Rules and money",
                 "locality_life": "Locality life", "education": "Buyer education", "digest": "This week"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
HOOK_MAX_WORDS = 12
LINE_MAX_WORDS = 22
GOOGLE_HOSTS = ("news.google.com", "google.com/rss", "news.url.google")


def site_url() -> str:
    return (os.environ.get("PUBLIC_SITE_URL") or policy.SITE).rstrip("/")


def news_url(item_id: str) -> str:
    return f"{site_url()}/news/{item_id}"


def one_line(s: object) -> str:
    return SPACE.sub(" ", PHONE.sub("", str(s or ""))).strip()


@dataclass
class Parts:
    summary: str = ""
    our_view: str = ""
    what_to_check: str = ""
    question: str = ""
    source_line: str = ""
    tags: List[str] = field(default_factory=list)


def _strip_prefix(p: str, prefixes: Tuple[str, ...]) -> Optional[str]:
    for pre in prefixes:
        if p.lower().startswith(pre.lower()):
            return p[len(pre):].strip()
    return None


def split_text(text: str) -> Parts:
    """The draft text as named parts. Link line, hashtags, disclaimer and footer never end up in `summary`."""
    parts, summary = Parts(), []
    paras = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    for i, p in enumerate(paras):
        flat = one_line(p)
        if not TAG.sub("", flat).strip():
            parts.tags += TAG.findall(flat)
        elif flat == policy.DISCLAIMER or flat.startswith((f"{brand.NAME} ·", "PUNE Property ·")):
            continue
        elif (v := _strip_prefix(flat, ("Our view:", "Why it may matter:"))) is not None:
            parts.our_view = v.replace("This is our view, not a fact from the source.", "").strip()
        elif (v := _strip_prefix(flat, ("What to check:",))) is not None:
            parts.what_to_check = v
        elif flat.lower().startswith("source:") or (URL.search(flat) and len(flat) < 260):
            parts.source_line = flat
        elif "?" in flat and i > 0 and not parts.question:  # 'Does this change ...? Tell us in the comments.'
            parts.question = flat
        else:
            summary.append(URL.sub("", flat).strip())
    parts.summary = one_line(" ".join(summary))
    return parts


def as_of(doc: dict):
    """The 'as of' datetime: the facts' date, else the source publish date, else None."""
    f = doc.get("facts") or {}
    raw = doc.get("raw") or {}
    return f.get("as_of") or raw.get("published_at") or raw.get("fetched_at")


def as_of_label(doc: dict) -> str:
    d = as_of(doc)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}" if d else ""


def source_name(doc: dict) -> str:
    names = [n for n in ((doc.get("draft") or {}).get("source_names") or []) if n and n.strip()]
    if names:
        return names[0].strip()
    s = ((doc.get("raw") or {}).get("source") or "").replace("_", " ").strip()
    return s if any(c.isupper() for c in s) else s.title()  # "MahaRERA" stays as written


def is_google_redirect(url: str) -> bool:
    return any(h in (url or "").lower() for h in GOOGLE_HOSTS)


def areas(doc: dict) -> List[str]:
    return [a for a in ((doc.get("relevance") or {}).get("areas") or []) if a in AREA_NAMES]


def area_names(doc: dict) -> List[str]:
    return [AREA_NAMES[a] for a in areas(doc)]


def pillar(doc: dict) -> str:
    return (doc.get("relevance") or {}).get("pillar") or ("digest" if (doc.get("draft") or {}).get("format") == "digest" else "locality_life")


def pillar_label(doc: dict) -> str:
    return PILLAR_LABELS.get(pillar(doc), "Local news")


def words(s: str) -> List[str]:
    return [w for w in SPACE.split(s.strip()) if w]


def _first_fact(doc: dict) -> str:
    for f in (doc.get("facts") or {}).get("facts") or []:
        t = one_line(URL.sub("", f.get("text", "")))
        if t:
            return t
    return ""


def _cut_clause(text: str, limit: int) -> str:
    """The longest natural prefix of `text` with at most `limit` words: whole sentence, then clause, then plain words."""
    text = text.strip().rstrip(".")
    if len(words(text)) <= limit:
        return text
    best = ""
    for m in re.finditer(r",|;| - | – | — |:|\(| and | with | after | as | for | while | but | which | that ", text):
        head = text[:m.start()].strip(" ,;:-–—")
        if 4 <= len(words(head)) <= limit and len(head) > len(best):
            best = head
    return best or " ".join(words(text)[:limit])


def headline(doc: dict) -> str:
    """Our own plain headline: the stored draft title, else the first checked fact (our wording), never the source's headline."""
    d = doc.get("draft") or {}
    t = one_line(d.get("title"))
    if t:
        return t.rstrip(".")
    fact = _first_fact(doc)
    if fact:
        return _cut_clause(fact, 18)
    return one_line(split_text(d.get("text", "")).summary)[:90] or "Local update"


def hook(doc: dict) -> str:
    """The card headline: at most HOOK_MAX_WORDS words of the headline, cut at a clause so it still reads as a statement."""
    return _cut_clause(headline(doc), HOOK_MAX_WORDS)


def support_line(doc: dict) -> str:
    """One supporting line for the card: the first fact (or summary sentence) that is not just the hook again."""
    h = hook(doc).lower()
    hw = set(re.findall(r"\w+", h))
    cands = [one_line(URL.sub("", f.get("text", ""))) for f in (doc.get("facts") or {}).get("facts") or []]
    cands.append(split_text((doc.get("draft") or {}).get("text", "")).summary)
    for c in cands:
        for s in re.split(r"(?<=[.!?])\s+", c):
            s = s.strip()
            sw = set(re.findall(r"\w+", s.lower()))
            if not s or h in s.lower() or (sw and len(sw & hw) / len(sw) >= 0.6):  # restates the hook
                continue
            if len(words(s)) >= 4:
                return _cut_clause(s, LINE_MAX_WORDS)
    return ""


FIGURE = re.compile(r"(₹\s?\d[\d,]*(?:\.\d+)?\s*(?:crore|lakh|cr|lakhs|crores)?|\d[\d,]*(?:\.\d+)?\s*(?:crore|crores|lakh|lakhs|km|kms|%|percent))", re.I)


def figure(doc: dict) -> Optional[Tuple[str, str]]:
    """(figure, hook) when the hook carries a rupee amount or a percentage that can stand as the big number of a card. The figure is
    cut from the hook as written, so nothing new appears on the card."""
    h = hook(doc)
    m = FIGURE.search(h)
    if not m or not (m.group(0).startswith("₹") or re.search(r"%|percent", m.group(0), re.I)):
        return None
    return m.group(0).strip(), h


HASHTAGS_BASE = ["#Pune", brand.HASHTAG]
HASHTAG_BY_PILLAR = {"infrastructure": "#PuneInfrastructure", "new_supply": "#MahaRERA", "rules_money": "#HomeBuyerTips",
                     "locality_life": "#PuneLife", "education": "#HomeBuyerTips", "digest": "#PuneNews"}
AREA_TAGS = {"kharadi": "#Kharadi", "upper_kharadi": "#UpperKharadi", "wagholi": "#Wagholi"}


def hashtags(doc: dict, limit: int = 8) -> List[str]:
    tags = list(HASHTAGS_BASE) + [AREA_TAGS[a] for a in areas(doc)] + [HASHTAG_BY_PILLAR.get(pillar(doc), "#PuneNews")]
    seen: List[str] = []
    for t in tags + ["#PuneRealEstate"]:
        if t not in seen:
            seen.append(t)
    return seen[:limit]
