"""WhatsApp follow-up drafts. Deterministic templates built from real facts; an optional injected LLM may only
re-word them and is rejected if any protected fact (name, listing, budget, price) goes missing."""
import logging
import re
from datetime import datetime
from typing import Awaitable, Callable, List, Optional
from urllib.parse import quote

from .requirement import bhk_text, budget_text, fmt_inr

logger = logging.getLogger(__name__)
Polish = Callable[[str, str], Awaitable[str]]  # (draft, language) -> reworded draft

# language -> template pieces. {name} {title} {budget} {match} {price} {loc} are always real values.
T = {
    "en": {
        "hi_title": "Hi {name}, thanks for your interest in {title}.",
        "hi": "Hi {name}, thanks for reaching out.",
        "budget": "I have noted your budget of {budget}{what}.",
        "match": "I also have {match} at {price} in {loc} that could suit you.",
        "visit": "Would you like to schedule a site visit this week?",
        "more": "Let me know if you would like more details.",
    },
    "hi": {
        "hi_title": "नमस्ते {name}, {title} में रुचि दिखाने के लिए धन्यवाद।",
        "hi": "नमस्ते {name}, संपर्क करने के लिए धन्यवाद।",
        "budget": "मैंने आपका बजट {budget}{what} नोट किया है।",
        "match": "मेरे पास {match} भी है, {loc} में {price} में, जो आपके लिए ठीक रह सकता है।",
        "visit": "क्या आप इस हफ्ते साइट विज़िट करना चाहेंगे?",
        "more": "अधिक जानकारी चाहिए तो बताइए।",
    },
    "mr": {
        "hi_title": "नमस्कार {name}, {title} मध्ये रस दाखवल्याबद्दल धन्यवाद.",
        "hi": "नमस्कार {name}, संपर्क केल्याबद्दल धन्यवाद.",
        "budget": "मी तुमचे बजेट {budget}{what} नोंदवले आहे.",
        "match": "माझ्याकडे {match} देखील आहे, {loc} मध्ये {price} ला, जे तुम्हाला योग्य ठरू शकते.",
        "visit": "या आठवड्यात साइट व्हिजिट ठरवायची का?",
        "more": "अधिक माहिती हवी असल्यास कळवा.",
    },
}
SOON = ("now", "1_3_months")


def whatsapp_url(phone: str, message: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return f"https://wa.me/{digits}?text={quote(message, safe='')}"


def build_draft(contact: dict, req: Optional[dict], listing_title: Optional[str], match: Optional[dict],
                language: str, now: datetime) -> dict:
    """-> {message, language, based_on, protected}. `protected` are facts a polish step must preserve."""
    lang = language if language in T else "en"
    t = T[lang]
    first = (contact.get("name") or "there").split()[0]
    req = req or {}
    parts: List[str] = []
    based: List[str] = []
    protected = [first]

    days = (now - contact["last_activity_at"]).days
    if contact["stage"] in ("new", "contacted") and days >= 1:
        based.append(f"No reply for {days} day{'s' if days != 1 else ''}")
    if listing_title:
        parts.append(t["hi_title"].format(name=first, title=listing_title))
        protected.append(listing_title)
        based.append(f"Enquired about {listing_title}")
    else:
        parts.append(t["hi"].format(name=first))

    b = budget_text(req.get("budget_min_inr"), req.get("budget_max_inr"))
    if b:
        what = ""
        if req.get("bhk"):
            what += f" for a {bhk_text(req['bhk'])}"
        if req.get("localities"):
            what += " in " + ", ".join(req["localities"])
        parts.append(t["budget"].format(budget=b, what=what if lang == "en" else ""))
        protected.append(b)
        based.append(f"Budget {b}")
    if match:
        price = fmt_inr(match["price_inr"]) if isinstance(match.get("price_inr"), int) else ""
        parts.append(t["match"].format(match=match["title"], price=price, loc=match.get("locality") or ""))
        protected += [match["title"], price]
        why = f"New listing in {match['locality']}" if match.get("locality") else "Matching listing"
        based.append(why + (" within budget" if b else ""))
    parts.append(t["visit"] if req.get("timeline") in SOON or contact["stage"] == "site_visit" else t["more"])
    if req.get("timeline") in SOON:
        based.append("Wants to buy soon")
    return {"message": " ".join(parts), "language": lang, "based_on": based, "protected": [p for p in protected if p]}


async def polish_safely(draft: dict, polish: Optional[Polish]) -> str:
    """Return the LLM-polished message only when every protected fact survived; otherwise the template."""
    msg = draft["message"]
    if polish is None:
        return msg
    try:
        out = (await polish(msg, draft["language"]) or "").strip()
    except Exception:  # never let the optional LLM break the draft
        logger.warning("followup polish failed; using template", exc_info=True)
        return msg
    if out and len(out) <= 1000 and all(p in out for p in draft["protected"]):
        return out
    return msg
