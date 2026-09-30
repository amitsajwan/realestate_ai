"""Understanding and answering a comment. Rules handle the common case; the LLM classifies the rest and drafts answers to questions.
Every LLM draft is checked before it can be posted: length, no phone numbers, no hype, only our own link, and no number that is not in the
post it answers. Anything that fails the checks becomes a safe template or goes to a human."""
import re
from dataclasses import dataclass
from typing import Optional

from app.modules.marketing.polish import HYPE, PHONE

INTENTS = ("interested", "question", "praise", "greeting", "complaint", "spam", "other")
GREETING = re.compile(r"^\W*(hi+|hello+|hey+|hii+|namaste|namaskar|good (morning|afternoon|evening)|hello you there)\W*$", re.I)
MAX_REPLY = 320
URL = re.compile(r"https?://\S+", re.I)
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
INTERESTED = re.compile(r"\b(interested|intrested|details|dm|price\??|rate\??|contact|available)\b|इंटरेस्टेड|रुचि|आवड|डिटेल|किंमत|कीमत", re.I)
SPAM = re.compile(r"(whatsapp me|dm me|click here|earn money|crypto|forex|loan offer|followers|http|www\.|t\.me/|bit\.ly)", re.I)
ABUSE = re.compile(r"\b(fraud|scam|cheat|fake|liar|stupid|idiot|bloody)\b", re.I)

TEMPLATES = {
    "en": {
        "interested": "Thanks{name}! Here are the details: {link} . Share your budget and preferred area there and our team will get back to you.",
        "question": "Good question{name}! Our team will reply here soon. Meanwhile, the full details are here: {link}",
        "praise": "Thank you{name}! Follow the page for more Pune property guides and listings.",
        "greeting": "Hello{name}! Comment INTERESTED on a listing for the details, or ask your question here and our team will help.",
    },
    "hi": {
        "interested": "धन्यवाद{name}! पूरी जानकारी यहाँ है: {link} . वहाँ अपना बजट और पसंदीदा इलाका बताएं, हमारी टीम आपसे संपर्क करेगी।",
        "question": "अच्छा सवाल{name}! हमारी टीम जल्द यहीं जवाब देगी। पूरी जानकारी यहाँ है: {link}",
        "praise": "धन्यवाद{name}! पुणे की प्रॉपर्टी गाइड और लिस्टिंग के लिए पेज को फॉलो करें।",
        "greeting": "नमस्ते{name}! विवरण के लिए कमेंट में INTERESTED लिखें, या अपना सवाल यहीं पूछें, हमारी टीम मदद करेगी।",
    },
    "mr": {
        "interested": "धन्यवाद{name}! संपूर्ण माहिती इथे आहे: {link} . तिथे तुमचे बजेट आणि आवडते क्षेत्र सांगा, आमची टीम तुमच्याशी संपर्क करेल.",
        "question": "छान प्रश्न{name}! आमची टीम लवकरच इथेच उत्तर देईल. संपूर्ण माहिती इथे आहे: {link}",
        "praise": "धन्यवाद{name}! पुण्यातील प्रॉपर्टी गाइड आणि लिस्टिंगसाठी पेज फॉलो करा.",
        "greeting": "नमस्कार{name}! तपशीलासाठी कमेंटमध्ये INTERESTED लिहा, किंवा तुमचा प्रश्न इथेच विचारा, आमची टीम मदत करेल.",
    },
}

SYSTEM = (
    "You handle comments on a Pune real-estate Facebook Page run by the 'PUNE Property team'. Classify the comment and, if it asks a question "
    "that the POST FACTS answer, draft a reply. Reply ONLY with one JSON object: "
    '{"intent": "interested|question|praise|complaint|spam|other", "language": "en|hi|mr", "answerable": true or false, "reply": "..."}. '
    "Rules for reply: same language as the comment (Marathi or Hindi in Devanagari is fine), at most 2 short sentences, friendly, plain. "
    "Use ONLY facts from POST FACTS. If the answer is not in POST FACTS, set answerable=false and reply=''. "
    "Never invent prices, distances, dates, amenities, approvals or RERA details. Never include phone numbers, links, or promises. "
    "Never use words like best, perfect, guaranteed, dream. 'interested' means the person wants details or to be contacted."
)


@dataclass
class Decision:
    intent: str
    language: str
    reply: Optional[str]
    needs_human: bool = False
    reason: str = ""


def detect_language(text: str) -> str:
    if re.search(r"[ऀ-ॿ]", text or ""):
        return "mr" if re.search(r"(आहे|तुम्ही|किंमत|हवे|माहिती|पाहिजे)", text) else "hi"
    return "en"


def first_name(name: Optional[str]) -> str:
    n = (name or "").strip().split(" ")[0]
    return f" {n}" if n and re.fullmatch(r"[A-Za-zऀ-ॿ.'-]{1,30}", n) else ""


def render(kind: str, lang: str, name: Optional[str], link: str) -> str:
    return TEMPLATES.get(lang, TEMPLATES["en"])[kind].format(name=first_name(name), link=link)


def valid_reply(reply: str, facts: str, link: str) -> bool:
    """A drafted answer may not contain phone numbers, hype, foreign links, or numbers that the post did not state."""
    if not reply or len(reply) > MAX_REPLY:
        return False
    if PHONE.search(reply) or HYPE.search(reply):
        return False
    if URL.findall(reply):  # the link is added by us afterwards; the model may not add any
        return False
    allowed = set(NUM.findall(facts or ""))
    return all(n in allowed for n in NUM.findall(reply))


def by_rules(text: str) -> Optional[str]:
    """Cheap, certain cases first: spam and abuse are not answered, plain 'INTERESTED'-style comments are."""
    t = (text or "").strip()
    if not t:
        return "other"
    if SPAM.search(t):
        return "spam"
    if ABUSE.search(t):
        return "complaint"
    if GREETING.match(t):
        return "greeting"
    if re.fullmatch(r"(?i)\W*(i'?m |i am |very |so )?(interested|intrested)\W*(pls|please|sir|mam|madam|details)?\W*", t):
        return "interested"
    return None


async def decide(text: str, from_name: Optional[str], facts: str, link: str, llm) -> Decision:
    lang = detect_language(text)
    intent = by_rules(text)
    if intent == "interested":
        return Decision("interested", lang, render("interested", lang, from_name, link))
    if intent == "greeting":
        return Decision("greeting", lang, render("greeting", lang, from_name, link))
    if intent in ("spam", "other"):
        return Decision(intent, lang, None, reason="not answered")
    if intent == "complaint":
        return Decision("complaint", lang, None, needs_human=True, reason="possible complaint or abuse")

    raw = None
    if llm is not None and hasattr(llm, "json"):
        raw = await llm.json(SYSTEM, f"POST FACTS:\n{(facts or '')[:900]}\n\nCOMMENT:\n{text[:500]}")
    if not isinstance(raw, dict) or raw.get("intent") not in INTENTS:
        # LLM unavailable or unusable: keyword fallback, and a person looks at anything else
        if INTERESTED.search(text):
            return Decision("interested", lang, render("interested", lang, from_name, link), reason="keyword fallback")
        return Decision("other", lang, None, needs_human=True, reason="LLM unavailable, unclear comment")

    intent = raw["intent"]
    lang = raw.get("language") if raw.get("language") in ("en", "hi", "mr") else lang
    if intent == "spam":
        return Decision("spam", lang, None, reason="not answered")
    if intent == "complaint":
        return Decision("complaint", lang, None, needs_human=True, reason="complaint")
    if intent == "interested":
        return Decision("interested", lang, render("interested", lang, from_name, link))
    if intent == "praise":
        return Decision("praise", lang, render("praise", lang, from_name, link))
    if intent == "greeting":
        return Decision("greeting", lang, render("greeting", lang, from_name, link))
    if intent == "question":
        draft = (raw.get("reply") or "").strip()
        if raw.get("answerable") is True and valid_reply(draft, facts, link):
            return Decision("question", lang, f"{draft} More details: {link}")
        return Decision("question", lang, render("question", lang, from_name, link), needs_human=True, reason="not answerable from post facts")
    return Decision("other", lang, None, needs_human=text.strip().endswith("?"), reason="other")
