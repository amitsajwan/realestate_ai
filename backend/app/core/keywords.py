"""The short word a buyer sends us on WhatsApp for a project (owner 2026-10-20: 'why not LODHA to +91 ...'): the project's own distinctive
name, IVARA for Godrej Ivara, CAMELOT for Lodha Camelot. Captions and comment replies say it; the chat bots read it. When two live
listings would share a word, each says its full name instead. Posts not made from a listing keep their interest code."""
import re
from typing import List, Optional

# not a project's own name: builder brands, and words many projects share
BRANDS = {"godrej", "lodha", "kolte", "patil", "pride", "rohan", "goel", "ganga", "vtp", "kumar", "gera", "panchshil", "mahindra", "tata",
          "shapoorji", "pallonji", "nyati", "majestique", "puraniks", "kalpataru", "sobha", "prestige", "brigade", "piramal", "birla",
          "runwal", "paranjape", "vilas", "javdekar", "goyal", "amco", "triaa", "anshul", "kohinoor", "marvel", "rama", "venkatesh", "lunkad"}
GENERIC = {"city", "homes", "home", "park", "heights", "towers", "tower", "residency", "residences", "phase", "enclave", "greens", "county",
           "nagar", "estate", "apartments", "apartment", "villas", "plots", "the", "by", "at", "and", "my", "new", "upper", "pune", "kharadi",
           "wagholi", "lohegaon", "project", "projects", "life", "living", "one", "gardens", "garden", "court", "square", "avenue"}
LIVE = ("live", "under_offer")


def _words(name: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (name or "").split(",")[0].lower())


def short_word(name: str) -> str:
    """'Godrej Ivara' -> 'IVARA', 'Lodha Camelot' -> 'CAMELOT', 'Gulmohar City' -> 'GULMOHAR'; the whole name squeezed when no word is
    the project's own ('Goyal My Home' -> 'GOYALMYHOME'); '' for no name."""
    words = _words(name)
    own = [w for w in words if w not in BRANDS and w not in GENERIC and len(w) >= 4 and not w.isdigit()]
    if own:
        return own[-1].upper()
    return "".join(words)[:16].upper()


def full_word(name: str) -> str:
    """The full project name as the buyer may type it: 'Godrej Ivara' -> 'GODREJ IVARA'."""
    return " ".join(_words(name)).upper()


def project_name(listing: dict) -> str:
    about = listing.get("about") if isinstance(listing.get("about"), dict) else {}
    return str(listing.get("project_name") or about.get("project_name") or "").strip()


async def _live_listings(db) -> List[dict]:
    return [d for d in await db.get_collection("listings").find({"status": {"$in": list(LIVE)}}).to_list(1000) if project_name(d)]


async def listing_keyword(db, listing_id) -> str:
    """The word captions and replies give for this listing: its short word, or its full name when another live listing shares the short
    word; '' when the listing is not live or has no project name."""
    listings = await _live_listings(db)
    me = next((d for d in listings if d["_id"] == listing_id), None)
    if me is None:
        return ""
    word = short_word(project_name(me))
    if any(d["_id"] != listing_id and short_word(project_name(d)) == word for d in listings):
        return full_word(project_name(me))
    return word


async def keyword_for_post(db, row: Optional[dict]) -> str:
    """The word for a calendar post: its listing's word, '' for a post not made from a listing (it keeps its code)."""
    return await listing_keyword(db, row["listing_id"]) if row and row.get("listing_id") else ""


async def listings_named_in(db, text: str) -> List[dict]:
    """The live listings a message names by their word or full name ('IVARA', 'godrej ivara price?')."""
    low = (text or "").lower()
    listings = await _live_listings(db)
    # a builder's name ('LODHA', as people often say it) names its project while only one live project carries it
    brand_of = {}
    for d in listings:
        for w in {w for w in _words(project_name(d)) if w in BRANDS}:
            brand_of.setdefault(w, []).append(d)
    out = []
    for d in listings:
        name = project_name(d)
        brands = [w for w in _words(name) if w in BRANDS and len(brand_of.get(w, [])) == 1]
        if any(w and re.search(rf"\b{re.escape(w.lower())}\b", low) for w in (short_word(name), full_word(name), *brands)):
            out.append(d)
    if len(out) > 1:   # 'godrej ivara' names Ivara; a shared short word alone names both
        full = [d for d in out if re.search(rf"\b{re.escape(full_word(project_name(d)).lower())}\b", low)]
        out = full or out
    return out


def without_word(text: str, listing: dict) -> str:
    """The message with the listing's word and full name taken out."""
    name = project_name(listing)
    for w in sorted({full_word(name), short_word(name), *(w.upper() for w in _words(name) if w in BRANDS)}, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(w)}\b", " ", text, flags=re.I)
    return text
