"""L1: free rules before any model (docs/RADAR.md §5). Keeps comments that could be a home question; drops spam, brokers and
ourselves. Hindi and Marathi words are matched in Latin and Devanagari script."""
import re
from typing import Optional

HOME = re.compile(
    r"\b(\d\s*bhk|bhk|flat|flats|apartment|apt|villa|row\s*house|plot|price|prices|rate|rates|cost|budget|lakh|lac|lacs|lakhs|cr|crore|"
    r"possession|carpet|sq\s*ft|sqft|emi|loan|booking|available|availability|inventory|rera|site\s*visit|visit|location|"
    r"rent|resale|ready\s*to\s*move|under\s*construction|kitna|kitne|kitni|kimat|keemat|kiti|kuthe|kab\s*milega|"
    r"interested|details|contact|brochure|floor\s*plan|parking|maintenance)\b"
    r"|किंमत|कीमत|फ्लॅट|फ्लैट|घर|भाड़ा|भाडे|बजट|लाख|कब्जा|ताबा", re.I)
PHONE = re.compile(r"(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}")
BROKER = re.compile(r"\b(contact (?:us|me) for|dm (?:us|me) for|call (?:us|me|now)|whatsapp (?:us|me|now)|best deals?|"
                    r"we (?:have|deal)|our project|channel partner|cp\b|brokerage|investment opportunity|guaranteed returns?)", re.I)
SPAM = re.compile(r"(https?://|www\.|t\.me/|bit\.ly|subscribe to my|check my channel|earn \d|crypto|forex)", re.I)
PRAISE_ONLY = re.compile(r"^\W*(nice|good|great|super|awesome|wow|beautiful|amazing|thanks?|thank you|👍|❤️|🔥)\W*$", re.I)


def reject_reason(text: str, author: str = "", own_names: tuple = ()) -> Optional[str]:
    """None when the comment should go on to the model; otherwise why it was dropped."""
    t = (text or "").strip()
    if len(t) < 3:
        return "empty"
    if author and author.lower() in {n.lower() for n in own_names}:
        return "own"
    if PRAISE_ONLY.match(t):
        return "praise"
    if SPAM.search(t):
        return "spam"
    if PHONE.search(t) and BROKER.search(t):
        return "broker"
    if not HOME.search(t) and "?" not in t:
        return "no home words"
    if not HOME.search(t) and len(t) > 280:
        return "no home words"
    return None
