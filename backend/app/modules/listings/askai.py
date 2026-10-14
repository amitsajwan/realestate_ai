"""Ask AI: the agent's own ChatGPT, Gemini or Claude, used by hand. Studio shows ready prompts built from what we know of the
listing; the agent runs one in their AI tab and pastes the answer back. `read_answer` splits it into the parts the prompts
ask for and checks every number against our records, so only lines they back can be kept (as the listing's highlights); the
PICTURES part becomes the listing's picture plan, which the team fills with photos. The brochure stays stored on the listing
but is not used here (owner, 2026-10-14).

    checked   every number is in our records: the listing, its highlights, the MahaRERA-checked sheet, published web facts
    unchecked a number found nowhere: never kept
    words     no numbers: the agent decides whether the wording is true
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.rera import SEARCH as RERA, find_all as reras
from app.modules.creative.guards import numbers

from .about import MAX_TEXT, _PHONE, _URL
from .schemas import PICTURE_TYPES

MAX_LINES = 60
LANG_NAME = {"en": "English", "mr": "Marathi (Devanagari script)", "hi": "Hindi (Devanagari script)"}
LISTING_KEYS = ("title", "project_name", "locality", "city", "bhk", "price_inr", "carpet_sqft", "super_built_up_sqft",
                "size_min_sqft", "size_max_sqft", "total_acres", "floor", "total_floors", "possession", "rera_no", "amenities")
MONEY = re.compile(r"(\d+(?:[.,]\d+)*)\s*(crores?|cr|lakhs?|lacs?|lac)\b", re.I)
SOURCE = re.compile(r"\s*\((?:source|sources)\s*:\s*([^)]*)\)\s*$", re.I)
BULLET = re.compile(r"^\s*(?:[-*•·▪►]+\s*|\d+[.)]\s+)")
CHATTY = re.compile(r"^(would you like|do you want|let me know|i can |i'll |here (?:is|are)|sure[,!]|note:|sources?:?$)", re.I)


# ---- what we know --------------------------------------------------------------------------------------------------------
def _num(n: str) -> str:
    """'1,250' -> '1250', '3.0' -> '3', '2.50' -> '2.5': one spelling per number on both sides."""
    n = n.replace(",", "")
    return n.rstrip("0").rstrip(".") if "." in n else n


def _rupees(text: str) -> List[float]:
    out = []
    for m in MONEY.finditer(text or ""):
        try:
            v = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        out.append(v * (1e7 if m.group(2).lower().startswith("cr") else 1e5))
    return out


class Known:
    """The numbers our records hold."""

    def __init__(self, text: str):
        self.reras = set(reras(text))
        self.nums = {_num(n) for n in numbers(text)}
        self.money = _rupees(text) + [float(n) for n in self.nums if re.fullmatch(r"\d{6,}", n)]

    def has(self, raw: str, rupees: Optional[float]) -> bool:
        return _num(raw) in self.nums or bool(rupees and any(abs(v - rupees) <= rupees * 0.01 for v in self.money))


def _facts_lines(sheet: Optional[dict]) -> List[str]:
    out = []
    for f in (sheet or {}).get("facts") or []:
        v = f.get("value")
        if f.get("usable") and isinstance(v, (str, int, float)) and str(v).strip() and not str(v).startswith("http"):
            out.append(f"{f['key'].replace('_', ' ').replace('.', ': ')}: {v}")
    return out[:30]


def _web_lines(web: Optional[dict]) -> List[str]:
    return [str(f.get("text") or "") for f in (web or {}).get("facts") or [] if f.get("text")]


def known(listing: dict, sheet: Optional[dict], web: Optional[dict]) -> Known:
    mine = {k: listing.get(k) for k in LISTING_KEYS if listing.get(k) not in (None, "", [])}
    points = [f"{p.get('label') or p.get('key')}: {p.get('value')}" for p in listing.get("selling_points") or [] if isinstance(p, dict)]
    about = listing.get("about") if isinstance(listing.get("about"), dict) else {}
    return Known("\n".join([json.dumps(mine, ensure_ascii=False, default=str), *points, *(about.get("highlights") or []),
                            *_facts_lines(sheet), *_web_lines(web)]))


async def gather(db, listing: dict) -> Tuple[Optional[dict], Optional[dict]]:
    """(MahaRERA-checked sheet, published web facts) for this listing. Each is optional; never raises."""
    from app.modules.propertyfacts.store import FactsStore
    sheet = web = None
    try:
        sheet = await FactsStore(db).find(listing.get("rera_no") or "", listing.get("project_name") or "", listing.get("locality") or "")
    except Exception:
        pass
    regno = (sheet or {}).get("rera_no") or listing.get("rera_no") or ""
    if regno:
        try:
            from app.modules.areastats.pages import web_facts_for
            web = await web_facts_for(db, regno)
        except Exception:
            pass
    return sheet, web


# ---- the prompts ---------------------------------------------------------------------------------------------------------
def _money(n: Any) -> str:
    try:
        v = float(n)
    except (TypeError, ValueError):
        return ""
    return f"₹{v / 1e7:.2f} crore".replace(".00 ", " ") if v >= 1e7 else f"₹{v / 1e5:.0f} lakh"


def brief(listing: dict, sheet: Optional[dict], web: Optional[dict]) -> str:
    """What the AI is told is already true: our records only."""
    about = listing.get("about") if isinstance(listing.get("about"), dict) else {}
    project = about.get("project_name") or listing.get("project_name") or ""
    place = ", ".join(x for x in (listing.get("locality"), listing.get("city")) if x)
    bhk = listing.get("bhk")
    lines = [f"- Listing: {listing.get('title') or ''}".rstrip()]
    if project:
        lines.append(f"- Project: {project}" + (f", builder {about['builder_known_as']}" if about.get("builder_known_as") else ""))
    if place:
        lines.append(f"- Place: {place}")
    if listing.get("rera_no") or (sheet or {}).get("rera_no"):
        lines.append(f"- MahaRERA number: {listing.get('rera_no') or sheet['rera_no']}")
    offer = [f"{bhk:g} BHK" if isinstance(bhk, (int, float)) else "", str(listing.get("property_type") or ""),
             "for rent" if listing.get("transaction") == "rent" else "for sale"]
    lines.append("- On offer: " + " ".join(x for x in offer if x))
    if listing.get("price_inr"):
        onwards = "onwards" in str(listing.get("title") or "").lower()
        lines.append(f"- Price: {_money(listing['price_inr'])}{' onwards' if onwards else ''} (the agent's price)")
    if listing.get("carpet_sqft"):
        lines.append(f"- Carpet area: {listing['carpet_sqft']} sq ft")
    if listing.get("amenities"):
        lines.append("- Amenities: " + ", ".join(listing["amenities"][:15]))
    checked = _facts_lines(sheet) + _web_lines(web)
    if checked:
        lines.append("- Checked facts (MahaRERA and the builder's website):")
        lines += [f"  - {x}" for x in checked[:25]]
    if about.get("highlights"):
        lines.append("- Highlights the agent checked:")
        lines += [f"  - {h}" for h in about["highlights"][:6]]
    return "\n".join(lines)


def _audience(listing: dict) -> str:
    where = listing.get("locality") or listing.get("city") or "Pune"
    if listing.get("transaction") == "rent":
        return f"tenants looking to rent in {where}, Pune: working professionals and young families aged 25 to 40"
    return f"home buyers looking in {where}, Pune: families and working professionals aged 28 to 45, buying a home to live in"


RULES = """RULES (an answer that breaks one is useless to me):
- Use only the FACTS above. Never add a number, distance, travel time, date, price or amenity that is not in them.
- Never write: ready to move, possession soon, best, no.1, guaranteed, assured returns, investment, lowest price, limited offer, hurry.
- No phone numbers, no website links, no emojis inside sentences, hashtags only at the very end of a caption.
- One call to action only: "Message me for the brochure and a site visit"."""


def prompts(listing: dict, sheet: Optional[dict], web: Optional[dict], language: str = "en") -> List[Dict[str, str]]:
    facts = brief(listing, sheet, web)
    name = (listing.get("about") or {}).get("project_name") or listing.get("project_name") or listing.get("title") or "this property"
    place = ", ".join(x for x in (listing.get("locality"), listing.get("city")) if x) or "Pune"
    area = listing.get("locality") or "this area"
    lang = LANG_NAME.get(language, "English")
    audience = _audience(listing)
    who = audience.split(":")[0]
    rera = ("Put the MahaRERA number in every caption." if (listing.get("rera_no") or (sheet or {}).get("rera_no"))
            else "There is no MahaRERA number in the facts: do not invent one.")
    return [
        {"id": "plan", "title": "Marketing plan",
         "use": "The full plan: who buys, why they visit, 5 pictures for your team to find, captions and a reel. Best in ChatGPT "
                "(thinking on) or Claude. Paste the whole answer back.",
         "text": f"""You are a senior real-estate marketer who has sold homes in {area}, Pune for ten years. I am a MahaRERA-registered agent.

MY GOAL: WhatsApp enquiries from serious buyers for {name} in {place}, from Instagram and Facebook posts. Likes do not matter. A clear, true post makes the right buyer message me; a vague or exaggerated one makes no one message.

AUDIENCE: {audience}.
LANGUAGE of the headline, captions and reel: {lang}. Everything else in English.

FACTS (only these are true):
{facts}

THINK FIRST. Under the heading "Thinking", in short bullets:
1. Who buys here: their job, family, budget, where they live now, and which 2 or 3 nearby projects they compare this one with.
2. The 3 strongest reasons to visit, each backed by a fact above. Name the fact.
3. The 2 doubts that stop them enquiring (price, possession, traffic, builder, size) and which fact answers each, or "no fact answers this".
4. Which picture would stop their thumb while scrolling, and why.

THEN ANSWER IN EXACTLY THIS FORMAT. My software reads the headings, so keep them as they are:

HEADLINE: <at most 8 words, names the place>

PICTURES:
1. <type> | <what the picture shows, specific enough for my team to find it> | <where to find it: the builder's website gallery (which page), Google Maps, or "agent's own photo"> | <text on the picture, at most 6 words> | <why it is at this position>
(exactly 5 pictures in carousel order. <type> is one of: {", ".join(PICTURE_TYPES)}. Picture 1 stops the scroll; the last is the floor plan or the price card. Never stock photos of people.)

CAPTIONS:
A. <first line: a hook built on reason 1 from your thinking>
<the rest of the caption, at most 80 words>
B. <hook built on reason 2, then the caption>
C. <hook built on reason 3, then the caption>
{rera}

REEL:
1. <picture type> | <text on screen, at most 6 words> | <spoken line, at most 12 words>
(exactly 5 scenes, 20 seconds in all. Scene 1 names the place and the price; scene 5 is the call to action.)

STILL MISSING:
- <a question buyers will ask that the facts do not answer; I will get it from the builder>

{RULES}"""},
        {"id": "facts", "title": "Find project facts",
         "use": "Web research, one fact per line with its source. Best in ChatGPT or Gemini with web search on. Paste the answer "
                "back: every number is checked.",
         "text": f"""You are a careful property researcher. I am a MahaRERA-registered agent in Pune and I must not advertise anything I cannot prove. Find the facts of {name} in {place} on the web.

WHAT I ALREADY KNOW:
{facts}

HOW TO SEARCH:
1. The builder's official website for this project first, then its MahaRERA registration page.
2. Property portals (99acres, MagicBricks, Housing.com, NoBroker) only when two of them say the same thing.
3. Ignore blogs, forums, ads and "upcoming project" pages. When sources disagree, give both values with both sources; do not pick one.

FIND:
- each configuration (BHK) with its carpet area in sq ft
- the starting price of each configuration
- land area, open space, towers and floors, total homes
- amenities (only those the builder lists for THIS project)
- possession date on MahaRERA, and the builder's date if it differs
- travel distance or time to the nearest IT parks, the airport, the railway station, schools and hospitals
- what the builder's gallery shows (building, amenities, interiors, views, plans)

ANSWER: one fact per line, exactly like this, and nothing else:
- <the fact in one short sentence> (source: <website name>)

Mark prices from marketing or channel-partner websites as (indicative). Leave out anything you could not find on a page: never estimate, never round. No links, no phone numbers."""},
        {"id": "faq", "title": "Buyer questions", "use": "Six questions buyers ask before a site visit, answered from the facts.",
         "text": f"""You are an experienced property agent in {area}, Pune. Think about what {who} really ask before they visit {name}: money, possession, size, travel, the builder, the society.

LANGUAGE: {lang}.

FACTS:
{facts}

List the six questions they ask most, each answered in at most 2 sentences, in this format:
Q: <question>
A: <answer>

Answer only from the facts. When the facts do not answer a question, write: "Ask me and I will check with the builder."
{RULES}"""},
    ]


# ---- reading a pasted answer ---------------------------------------------------------------------------------------------
SECTIONS = {"thinking": "thinking", "headline": "headline", "pictures": "pictures", "captions": "captions", "caption": "captions",
            "reel": "reel", "still missing": "missing"}
SECTION = re.compile(r"^\s*(?:#+\s*)?(thinking|headline|pictures|captions?|reel|still missing)\s*:?\s*(.*)$", re.I)
CAPTION_START = re.compile(r"^\s*(?:caption\s*)?([A-C1-3])[.):]\s*", re.I)
TYPE_WORDS = [("floor plan", ("floor plan", "unit plan", "layout plan")), ("master plan", ("master plan", "site plan")),
              ("location map", ("location", "map", "connectivity")), ("price card", ("price",)),
              ("interior", ("interior", "living", "bedroom", "kitchen", "deck", "balcony", "sample flat")),
              ("view", ("view", "skyline", "aerial")),
              ("building render", ("render", "exterior", "facade", "tower", "building", "elevation")),
              ("amenity", ("amenit", "pool", "club", "garden", "gym", "court", "landscap"))]


def _type(raw: str) -> str:
    low = raw.lower().strip()
    if low in PICTURE_TYPES:
        return low
    for t, words in TYPE_WORDS:
        if any(w in low for w in words):
            return t
    return "amenity"


def _status(body: str, k: Known) -> Tuple[str, List[str]]:
    """A MahaRERA number must be the listing's own; the other numbers must be in our records."""
    wrong = [r for r in reras(body) if r not in k.reras]
    body = RERA.sub(" ", body)
    money = {_num(x.group(1)): v for x, v in zip(MONEY.finditer(body), _rupees(body))}
    found = list(dict.fromkeys(_num(n) for n in numbers(body)))
    missing = wrong + [n for n in found if not k.has(n, money.get(n))]
    if _PHONE.search(body):
        return "unchecked", missing or ["phone number"]
    if missing:
        return "unchecked", missing
    if not found:
        return "words", []
    return "checked", []


def _split(text: str) -> Dict[str, List[str]]:
    """The answer's lines by section; lines before any heading (a facts answer) are "facts"."""
    parts: Dict[str, List[str]] = {}
    at = "facts"
    for raw in (text or "").replace("\r", "").split("\n"):
        plain = raw.replace("**", "").replace("__", "")
        m = SECTION.match(plain)
        if m and (not m.group(2).strip() or m.group(1).lower() == "headline"):
            at = SECTIONS[m.group(1).lower()]
            if m.group(2).strip():
                parts.setdefault(at, []).append(m.group(2).strip())
            continue
        if plain.strip():
            parts.setdefault(at, []).append(plain.strip())
    return parts


def _lines(raw: List[str]) -> List[str]:
    out = []
    for r in raw:
        line = re.sub(r"\s+", " ", BULLET.sub("", r.replace("\t", " · ")).strip(" ·"))
        heading = len(line.split()) <= 4 and not re.search(r"\d", line)
        if heading or len(line) < 8 or re.fullmatch(r"\+\d+", line) or line.endswith("?") or CHATTY.match(line):
            continue
        out.append(line[:400])
    return list(dict.fromkeys(out))[:MAX_LINES]


def _fact_line(line: str, k: Known) -> Dict[str, Any]:
    m = SOURCE.search(line)
    body = SOURCE.sub("", line).strip()
    status, missing = _status(body, k)
    keep = _URL.sub("", body).strip()
    return {"text": body, "source": m.group(1).strip() if m else "", "status": status, "missing": missing,
            "keep": keep[:MAX_TEXT] if status != "unchecked" and keep else ""}


def _captions(raw: List[str], k: Known) -> List[Dict[str, Any]]:
    caps: List[List[str]] = []
    for line in raw:
        m = CAPTION_START.match(line)
        if m:
            caps.append([line[m.end():].strip()])
        elif caps:
            caps[-1].append(line)
    out = []
    for c in caps[:5]:
        text = "\n".join(x for x in c if x).strip()
        if text:
            status, missing = _status(text, k)
            out.append({"text": text, "status": status, "missing": missing})
    return out


def _rows(raw: List[str], cells: int) -> List[List[str]]:
    rows = []
    for r in raw:
        line = BULLET.sub("", r).strip()
        if line.count("|") >= cells - 1 and not re.fullmatch(r"[|\s:-]+", line):
            rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


def _pictures(raw: List[str], k: Known) -> List[Dict[str, Any]]:
    out = []
    for c in _rows(raw, 3)[:8]:
        c = c + [""] * (5 - len(c))
        text = c[3][:80]
        status, missing = _status(text, k) if text else ("words", [])
        shows = (c[1] or c[0])[:200]
        if shows:
            out.append({"type": _type(c[0]), "shows": shows, "where": c[2][:200], "text": "" if status == "unchecked" else text,
                        "why": c[4][:200], "status": status, "missing": missing})
    return out


def read_answer(text: str, k: Known) -> Dict[str, Any]:
    """The pasted answer in parts: fact lines (keepable as highlights), headline, captions, picture plan, reel and the
    questions still missing; every number checked."""
    parts = _split(text)
    head = (parts.get("headline") or [""])[0].strip()
    reel = []
    for c in _rows(parts.get("reel", []), 3)[:8]:
        c = c + [""] * (3 - len(c))
        status, missing = _status(f"{c[1]} {c[2]}", k)
        reel.append({"picture": c[0], "screen": c[1], "spoken": c[2], "status": status, "missing": missing})
    headline = None
    if head:
        status, missing = _status(head, k)
        headline = {"text": head, "status": status, "missing": missing}
    return {
        "lines": [_fact_line(x, k) for x in _lines(parts.get("facts", []))],
        "headline": headline,
        "captions": _captions(parts.get("captions", []), k),
        "pictures": _pictures(parts.get("pictures", []), k),
        "reel": reel,
        "missing": [x for x in (BULLET.sub("", r).strip() for r in parts.get("missing", [])) if x][:10],
    }
