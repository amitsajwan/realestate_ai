"""Ask AI: the agent's own ChatGPT, Gemini or Claude, used by hand. Studio shows ready prompts built from what we know of the
listing; the agent runs one in their AI tab and pastes the answer back; `check` marks every line by where its numbers are
found, so only lines our records or the builder's brochure back can be kept (as the listing's highlights).

    checked   every number is in our records: the listing, the MahaRERA-checked sheet, published web facts
    builder   every number is found, some only in the builder's brochure (a claim, said as the builder's)
    unchecked a number found nowhere: never kept
    words     no numbers: the agent decides whether the wording is true
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.modules.creative.guards import numbers

from .about import MAX_TEXT, _PHONE, _URL

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
    """The numbers our records and the builder's brochure hold, kept apart."""

    def __init__(self, official: str, builder: str):
        self.official, self.builder = official, builder
        self.nums = {k: {_num(n) for n in numbers(t)} for k, t in (("official", official), ("builder", builder))}
        self.money = {k: _rupees(t) + [float(n) for n in self.nums[k] if re.fullmatch(r"\d{6,}", n)]
                      for k, t in (("official", official), ("builder", builder))}

    def where(self, raw: str, rupees: Optional[float]) -> Optional[str]:
        for k in ("official", "builder"):
            if _num(raw) in self.nums[k] or (rupees and any(abs(v - rupees) <= rupees * 0.01 for v in self.money[k])):
                return k
        return None


def _facts_lines(sheet: Optional[dict]) -> List[str]:
    out = []
    for f in (sheet or {}).get("facts") or []:
        v = f.get("value")
        if f.get("usable") and isinstance(v, (str, int, float)) and str(v).strip() and not str(v).startswith("http"):
            out.append(f"{f['key'].replace('_', ' ').replace('.', ': ')}: {v}")
    return out[:30]


def _web_lines(web: Optional[dict]) -> List[str]:
    return [str(f.get("text") or "") for f in (web or {}).get("facts") or [] if f.get("text")]


def _claims(listing: dict) -> List[str]:
    fc = listing.get("file_claims") if isinstance(listing.get("file_claims"), dict) else {}
    return [str(c) for c in (fc.get("brochure") or []) + (fc.get("video") or []) if c]


def known(listing: dict, sheet: Optional[dict], web: Optional[dict], brochure_text: str = "") -> Known:
    mine = {k: listing.get(k) for k in LISTING_KEYS if listing.get(k) not in (None, "", [])}
    points = [f"{p.get('label') or p.get('key')}: {p.get('value')}" for p in listing.get("selling_points") or [] if isinstance(p, dict)]
    about = listing.get("about") if isinstance(listing.get("about"), dict) else {}
    official = "\n".join([json.dumps(mine, ensure_ascii=False, default=str), *points, *(about.get("highlights") or []),
                          *_facts_lines(sheet), *_web_lines(web)])
    fc = listing.get("file_claims") if isinstance(listing.get("file_claims"), dict) else {}
    builder = "\n".join([*_claims(listing), json.dumps(fc.get("brochure_facts") or {}, ensure_ascii=False, default=str), brochure_text])
    return Known(official, builder)


async def gather(db, listing: dict, uploads_dir: Path) -> Tuple[Optional[dict], Optional[dict], str]:
    """(MahaRERA-checked sheet, published web facts, brochure words) for this listing. Each part is optional; never raises."""
    from app.modules.propertyfacts import brochure_doc, files
    from app.modules.propertyfacts.store import FactsStore
    sheet = web = None
    text = ""
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
    try:
        pdf = files.brochure_pdf(listing, uploads_dir)
        text = brochure_doc.full_text(brochure_doc.cached(pdf, uploads_dir)) if pdf else ""
    except Exception:
        pass
    return sheet, web, text


# ---- the prompts ---------------------------------------------------------------------------------------------------------
def _money(n: Any) -> str:
    try:
        v = float(n)
    except (TypeError, ValueError):
        return ""
    return f"₹{v / 1e7:.2f} crore".replace(".00 ", " ") if v >= 1e7 else f"₹{v / 1e5:.0f} lakh"


def brief(listing: dict, sheet: Optional[dict], web: Optional[dict]) -> str:
    """What the AI is told is already true: our records, then the builder's claims labelled as such."""
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
    claims = _claims(listing)
    if claims:
        lines.append("- The builder's brochure says (claims, not checked):")
        lines += [f"  - {c}" for c in claims[:12]]
    return "\n".join(lines)


def _audience(listing: dict) -> str:
    where = listing.get("locality") or listing.get("city") or "Pune"
    who = "tenants" if listing.get("transaction") == "rent" else "home buyers"
    return f"{who} looking in {where}, Pune: families and working professionals aged 28 to 45, buying (or renting) for themselves"


RULES = """Rules:
- Use only the facts above. Do not add any number, distance, date, price or amenity that is not listed above.
- Say a brochure claim as the builder's ("the builder says"), never as checked.
- Never write: ready to move, possession soon, best, guaranteed, assured returns, investment, lowest price, limited offer.
- No phone numbers, no website links, no hashtags inside sentences.
- One call to action only: "Message me for the brochure and a site visit"."""


def prompts(listing: dict, sheet: Optional[dict], web: Optional[dict], language: str = "en") -> List[Dict[str, str]]:
    facts = brief(listing, sheet, web)
    name = (listing.get("about") or {}).get("project_name") or listing.get("project_name") or listing.get("title") or "this property"
    place = ", ".join(x for x in (listing.get("locality"), listing.get("city")) if x) or "Pune"
    lang = LANG_NAME.get(language, "English")
    audience = _audience(listing)
    return [
        {"id": "facts", "title": "Find project facts", "use": "Best in ChatGPT or Gemini with web search on. Paste the answer back to check it.",
         "text": f"""I am a real-estate agent in Pune. Before I advertise {name} in {place}, find its facts on the web.

What I already know:
{facts}

Search the builder's official website and the MahaRERA record first. Use property portals only when two of them agree.
Find: configurations (BHK) with carpet areas in sq ft; starting prices; land area and open space; towers and floors; amenities; possession date as on MahaRERA; travel time or distance to IT parks, the airport, the railway station, schools and hospitals.

Answer with one fact per line, exactly like this:
- <the fact in one short sentence> (source: <website name>)

Mark prices from marketing websites as (indicative). Leave out anything you cannot find on a page: never estimate. No links, no phone numbers, no other text."""},
        {"id": "posts", "title": "Post ideas", "use": "A headline, 5 pictures in order and 3 captions for Instagram and Facebook.",
         "text": f"""Write social media posts for {name} in {place}.

Audience: {audience}.
Language: {lang}.

Facts:
{facts}

Give me:
1. One headline, at most 8 words, naming the place.
2. Five pictures for a carousel, in order: what each picture shows and the 6-word text on it. Start with the building, end with floor plan and price.
3. Three captions (Instagram and Facebook), each at most 80 words, each with a different opening line. Put the MahaRERA number in each caption when it is listed above.

{RULES}"""},
        {"id": "reel", "title": "Reel script", "use": "A 20-second voice-over in 5 scenes.",
         "text": f"""Write a 20-second Instagram reel script for {name} in {place}.

Audience: {audience}.
Language of the voice-over: {lang}.

Facts:
{facts}

Five scenes. For each scene give: the picture to show, the text on screen (at most 6 words), and the spoken line (at most 12 words).
Scene 1 is the hook: the place and the price. Scene 5 is the call to action.

{RULES}"""},
        {"id": "faq", "title": "Buyer questions", "use": "Six questions buyers ask before a site visit, answered from the facts.",
         "text": f"""List the six questions {audience.split(':')[0]} ask most before visiting {name} in {place}, and answer each in at most 2 sentences.

Language: {lang}.

Facts:
{facts}

Answer only from the facts above. When the facts do not answer a question, write: "Ask me and I will check with the builder."
{RULES}"""},
    ]


# ---- checking a pasted answer --------------------------------------------------------------------------------------------
def _lines(text: str) -> List[str]:
    out = []
    for raw in (text or "").replace("\r", "").split("\n"):
        line = BULLET.sub("", raw.replace("**", "").replace("\t", " · ")).strip(" ·")
        line = re.sub(r"\s+", " ", line)
        heading = len(line.split()) <= 4 and not re.search(r"\d", line)
        if heading or len(line) < 8 or re.fullmatch(r"\+\d+", line) or line.endswith("?") or CHATTY.match(line):
            continue
        out.append(line[:400])
    return list(dict.fromkeys(out))[:MAX_LINES]


def check(text: str, k: Known) -> List[Dict[str, Any]]:
    """Each kept line of the pasted answer with its status, the numbers found nowhere, and the text to keep (no source note,
    no link, at most the highlight length)."""
    out = []
    for line in _lines(text):
        m = SOURCE.search(line)
        source = m.group(1).strip() if m else ""
        body = SOURCE.sub("", line).strip()
        keep = _URL.sub("", body).strip()
        money = {_num(x.group(1)): v for x, v in zip(MONEY.finditer(body), _rupees(body))}
        found = [(n, k.where(n, money.get(n))) for n in dict.fromkeys(_num(n) for n in numbers(body))]
        missing = [n for n, w in found if w is None]
        if _PHONE.search(body):
            status, missing = "unchecked", missing or ["phone number"]
        elif missing:
            status = "unchecked"
        elif not found:
            status = "words"
        else:
            status = "builder" if any(w == "builder" for _, w in found) else "checked"
        out.append({"text": body, "source": source, "status": status, "missing": missing,
                    "keep": keep[:MAX_TEXT] if status != "unchecked" and keep else ""})
    return out
