"""Understanding and answering a comment. Rules handle the common case; the LLM classifies the rest and drafts answers to questions.
Every LLM draft is checked before it can be posted: length, no phone numbers, no hype, only our own link, and no number that is not in the
post it answers. Anything that fails the checks becomes a safe template or goes to a human."""
from app.core import brand
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.modules.knowledge.reply import answer as grounded_answer, has_topic
from app.platform.text import HYPE, PHONE

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
        "interested": "Thanks{name}! Details and price: {link} . Leave your WhatsApp number there and our team will send you the price list and floor plans.",
        "question": "Good question{name}! Our team will reply here soon. Meanwhile, the full details are here: {link} . Leave your WhatsApp number there for the price list.",
        "praise": "Thank you{name}! Follow the page for more Pune property guides and listings.",
        "greeting": "Hello{name}! Comment INTERESTED on a listing for the details, or ask your question here and our team will help.",
    },
    "hi": {
        "interested": "धन्यवाद{name}! पूरी जानकारी और कीमत यहाँ है: {link} . वहाँ अपना WhatsApp नंबर दें, हमारी टीम आपको प्राइस लिस्ट और फ्लोर प्लान भेजेगी।",
        "question": "अच्छा सवाल{name}! हमारी टीम जल्द यहीं जवाब देगी। पूरी जानकारी यहाँ है: {link}",
        "praise": "धन्यवाद{name}! पुणे की प्रॉपर्टी गाइड और लिस्टिंग के लिए पेज को फॉलो करें।",
        "greeting": "नमस्ते{name}! विवरण के लिए कमेंट में INTERESTED लिखें, या अपना सवाल यहीं पूछें, हमारी टीम मदद करेगी।",
    },
    "mr": {
        "interested": "धन्यवाद{name}! संपूर्ण माहिती आणि किंमत इथे आहे: {link} . तिथे तुमचा WhatsApp नंबर द्या, आमची टीम तुम्हाला प्राइस लिस्ट आणि फ्लोअर प्लॅन पाठवेल.",
        "question": "छान प्रश्न{name}! आमची टीम लवकरच इथेच उत्तर देईल. संपूर्ण माहिती इथे आहे: {link}",
        "praise": "धन्यवाद{name}! पुण्यातील प्रॉपर्टी गाइड आणि लिस्टिंगसाठी पेज फॉलो करा.",
        "greeting": "नमस्कार{name}! तपशीलासाठी कमेंटमध्ये INTERESTED लिहा, किंवा तुमचा प्रश्न इथेच विचारा, आमची टीम मदत करेल.",
    },
}

# Instagram: links in comments are not clickable, so replies point at the bio. Only the wording with a link differs from Facebook.
BIO = {"en": "the link in our bio", "hi": "हमारे बायो का लिंक", "mr": "आमच्या बायोमधील लिंक"}
IG_TEMPLATES = {
    "en": {
        "interested": "Thanks{name}! Full details are at the link in our bio. Leave your WhatsApp number there and our team will send you the price list and floor plans.",
        "question": "Good question{name}! Our team will reply here soon. Meanwhile, the details are at the link in our bio.",
        "praise": "Thank you{name}! Follow this account for more Pune property guides and listings.",
    },
    "hi": {
        "interested": "धन्यवाद{name}! पूरी जानकारी हमारे बायो के लिंक पर है। वहाँ अपना WhatsApp नंबर दें, हमारी टीम आपको प्राइस लिस्ट और फ्लोर प्लान भेजेगी।",
        "question": "अच्छा सवाल{name}! हमारी टीम जल्द यहीं जवाब देगी। पूरी जानकारी हमारे बायो के लिंक पर है।",
        "praise": "धन्यवाद{name}! पुणे की प्रॉपर्टी गाइड और लिस्टिंग के लिए इस अकाउंट को फॉलो करें।",
    },
    "mr": {
        "interested": "धन्यवाद{name}! संपूर्ण माहिती आमच्या बायोमधील लिंकवर आहे. तिथे तुमचा WhatsApp नंबर द्या, आमची टीम तुम्हाला प्राइस लिस्ट आणि फ्लोअर प्लॅन पाठवेल.",
        "question": "छान प्रश्न{name}! आमची टीम लवकरच इथेच उत्तर देईल. संपूर्ण माहिती आमच्या बायोमधील लिंकवर आहे.",
        "praise": "धन्यवाद{name}! पुण्यातील प्रॉपर्टी गाइड आणि लिस्टिंगसाठी हे अकाउंट फॉलो करा.",
    },
}
DM_ME = re.compile(r"\bdm\s*(me|us)\b|\b(pls|please)\s+dm\b|\bmessage me\b|\bmsg me\b", re.I)

SYSTEM = (
    f"You handle comments on a Pune real-estate Facebook Page run by the '{brand.TEAM}'. Classify the comment and, if it asks a question "
    "that the POST FACTS answer, draft a reply. Reply ONLY with one JSON object: "
    '{"intent": "interested|question|praise|complaint|spam|other", "language": "en|hi|mr", "answerable": true or false, "reply": "..."}. '
    "A question about the property, price, location, area, availability, metro or process is intent 'question' (never 'other'). "
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
    missing: Optional[str] = None                      # what the grounded reply could not answer (for the owner)
    basis: List[str] = field(default_factory=list)     # the facts the reply rests on (stored as answer_basis)
    gaps: List[str] = field(default_factory=list)      # topics the grounded reply could not answer ('other' = no known topic)


def detect_language(text: str) -> str:
    if re.search(r"[ऀ-ॿ]", text or ""):
        return "mr" if re.search(r"(आहे|तुम्ही|किंमत|हवे|माहिती|पाहिजे)", text) else "hi"
    return "en"


def first_name(name: Optional[str]) -> str:
    n = (name or "").strip().split(" ")[0]
    return f" {n}" if n and re.fullmatch(r"[A-Za-zऀ-ॿ.'-]{1,30}", n) else ""


# Comments on our agent-recruitment posts and reels ("Comment AGENT"): the reply is about the pilot, never price lists or floor plans.
AGENT_ASK = re.compile(r"\b(agents?|join|pilot|interested|intrested|details|demo|how|kaise|cost|charges?|free|yes|haan|ha)\b|एजेंट|इंटरेस्टेड|जानकारी", re.I)
AGENT_TEMPLATES = {
    "en": {"facebook": "Thanks{name}! The Avasetu pilot is free for Pune property agents. Join here: {link} . We have also sent you a message.",
           "instagram": "Thanks{name}! We have sent you a message with the free pilot link. It is also at the link in our bio."},
    "hi": {"facebook": "धन्यवाद{name}! पुणे के प्रॉपर्टी एजेंट्स के लिए Avasetu पायलट फ्री है। यहाँ जुड़ें: {link} . हमने आपको मैसेज भी भेजा है।",
           "instagram": "धन्यवाद{name}! हमने आपको फ्री पायलट का लिंक मैसेज में भेजा है। यह हमारे बायो के लिंक में भी है।"},
}


def agent_reply(lang: str, name: Optional[str], link: str, channel: str = "facebook") -> str:
    t = AGENT_TEMPLATES.get(lang, AGENT_TEMPLATES["en"])["instagram" if channel == "instagram" else "facebook"]
    return t.format(name=first_name(name), link=link)


def render(kind: str, lang: str, name: Optional[str], link: str, channel: str = "facebook") -> str:
    if channel == "instagram":
        t = IG_TEMPLATES.get(lang, IG_TEMPLATES["en"]).get(kind)
        if t:
            return t.format(name=first_name(name))
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


QUESTION_WORDS = re.compile(r"\?|^\s*(what|where|how|which|when|is|are|can|do|does|kya|kaise|kitna|kitni|kahan|kab|kuthe|kiti|kay)\b|\b(location|price|rate|address|available|availability|metro|possession|rera|loan|size|floor)\b", re.I)


def looks_like_question(text: str) -> bool:
    return bool(QUESTION_WORDS.search(text or ""))


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


def wants_a_person(text: str, handle: str) -> bool:
    """Instagram: '@ourhandle ...' mentions and 'DM me' asks are for a person, unless the rest is plain spam."""
    t = text or ""
    if not (DM_ME.search(t) or (handle and ("@" + handle.lower()) in t.lower())):
        return False
    return not SPAM.search(re.sub(r"dm\s*(me|us)", "", t, flags=re.I))


ASKING = re.compile(r"\?|^\s*(what|where|how|which|when|is|are|can|could|do|does|will|kya|kaise|kitna|kitni|kahan|kab|kuthe|kiti|kay)\b|\b(kitna|kitne|kitni|kab|kahan|kuthe|kiti|kya|milega|milegi|tell me|send|share|please)\b|[?？]", re.I)


def asks_about_the_post(text: str) -> bool:
    """A question, or a very short comment that names one thing ('carpet area', 'possession date'): worth a grounded answer."""
    return has_topic(text) and (bool(ASKING.search(text)) or len(text.split()) <= 4)


REPLY_LANG = {"en": "en", "hi": "hi", "hinglish": "hi", "mr": "mr", "mr_latn": "mr"}


async def grounded_decision(text: str, grounding, link: str, llm, channel: str) -> Decision:
    """Answer a question from what we know about the post's home, project or area. Only when the answer is not fully covered is a person asked as well."""
    r = await grounded_answer(text, grounding, channel, llm)
    reply = r.text.replace("{interest_url}", link)
    reason = "grounded answer" if r.confident else f"not in our facts: {r.missing}"
    return Decision("question", REPLY_LANG.get(r.language, "en"), reply, needs_human=not r.confident, reason=reason, missing=r.missing, basis=r.basis,
                    gaps=list(r.gaps))


async def decide(text: str, from_name: Optional[str], facts: str, link: str, llm, channel: str = "facebook", handle: str = "", grounding=None,
                 audience: str = "buyers") -> Decision:
    ig = channel == "instagram"
    if ig and wants_a_person(text, handle):
        return Decision("question", detect_language(text), None, needs_human=True, reason="mention or DM request")
    lang = detect_language(text)
    intent = by_rules(text)
    if audience == "agents" and intent not in ("spam", "complaint") and AGENT_ASK.search(text or ""):
        said = lang if lang in AGENT_TEMPLATES else "en"
        return Decision("interested", said, agent_reply(said, from_name, link, channel),
                        reason="agent asks about the pilot")
    if ig:
        link = BIO["en"]  # never put a URL in an Instagram reply
    if grounding is not None and intent is None and asks_about_the_post(text):
        # the LLM (when there is one) still gets to say it is spam, abuse or plain praise; a question about the post is answered from facts
        raw = await llm.json(SYSTEM, f"POST FACTS:\n{(facts or '')[:900]}\n\nCOMMENT:\n{text[:500]}") if llm is not None and hasattr(llm, "json") else None
        said = raw.get("intent") if isinstance(raw, dict) else None
        if said == "spam":
            return Decision("spam", lang, None, reason="not answered")
        if said == "complaint":
            return Decision("complaint", lang, None, needs_human=True, reason="complaint")
        if said not in ("praise", "greeting"):
            return await grounded_decision(text, grounding, link, llm, channel)
    if intent == "interested":
        return Decision("interested", lang, render("interested", lang, from_name, link, channel))
    if intent == "greeting":
        return Decision("greeting", lang, render("greeting", lang, from_name, link, channel))
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
            return Decision("interested", lang, render("interested", lang, from_name, link, channel), reason="keyword fallback")
        if looks_like_question(text):
            return Decision("question", lang, render("question", lang, from_name, link, channel), needs_human=True, reason="LLM unavailable")
        return Decision("other", lang, None, needs_human=True, reason="LLM unavailable, unclear comment")

    intent = raw["intent"]
    lang = raw.get("language") if raw.get("language") in ("en", "hi", "mr") else lang
    if intent == "spam":
        return Decision("spam", lang, None, reason="not answered")
    if intent == "complaint":
        return Decision("complaint", lang, None, needs_human=True, reason="complaint")
    if intent == "interested":
        return Decision("interested", lang, render("interested", lang, from_name, link, channel))
    if intent == "praise":
        return Decision("praise", lang, render("praise", lang, from_name, link, channel))
    if intent == "greeting":
        return Decision("greeting", lang, render("greeting", lang, from_name, link, channel))
    if intent == "question" and grounding is not None:
        # a question in words no keyword knows: answered from everything we know about the post (and its gap recorded), not from the
        # short post summary alone
        return await grounded_decision(text, grounding, link, llm, channel)
    if intent == "question":
        draft = (raw.get("reply") or "").strip()
        if raw.get("answerable") is True and valid_reply(draft, facts, link):
            return Decision("question", lang, f"{draft} More details: {link}" if not ig else f"{draft} More details: the link in our bio.")
        return Decision("question", lang, render("question", lang, from_name, link, channel), needs_human=True, reason="not answerable from post facts")
    if looks_like_question(text):
        return Decision("question", lang, render("question", lang, from_name, link, channel), needs_human=True, reason="question the post cannot answer")
    return Decision("other", lang, None, reason="other")


# The private message (Messenger / Instagram DM) sent once to someone who commented interest or a question. It asks for what turns a
# commenter into a lead an agent can call; their answer is read back into the lead (EngageService.collect_dm_replies).
DM_TEMPLATES = {
    "en": "Hi{name}, thanks for your comment{topic}. To send you the price list and floor plans on WhatsApp, please reply here with "
          "1) your WhatsApp number, 2) your budget, 3) when you plan to buy. Details: {link}",
    "hi": "नमस्ते{name}, आपके कमेंट{topic} के लिए धन्यवाद। प्राइस लिस्ट और फ्लोर प्लान WhatsApp पर भेजने के लिए यहीं जवाब दें: "
          "1) आपका WhatsApp नंबर, 2) आपका बजट, 3) आप कब तक खरीदना चाहते हैं। जानकारी: {link}",
    "mr": "नमस्कार{name}, तुमच्या कमेंटसाठी{topic} धन्यवाद. प्राइस लिस्ट आणि फ्लोअर प्लॅन WhatsApp वर पाठवण्यासाठी इथेच उत्तर द्या: "
          "1) तुमचा WhatsApp नंबर, 2) तुमचे बजेट, 3) तुम्ही कधी खरेदी करणार. माहिती: {link}",
}
DM_AGENTS = ("Hi{name}, thanks for asking about Avasetu. The pilot is free. Reply here with your WhatsApp number and the areas you work in, "
             "and we will set it up with you. Or join here: {link}")


def dm_text(language: str, name: Optional[str], link: str, topic: str = "", audience: str = "buyers") -> str:
    first = f" {name.split()[0]}" if name and name.split() else ""
    if audience == "agents":
        return DM_AGENTS.format(name=first, link=link)
    on = (f" on {topic}" if language == "en" else f" ({topic})") if topic else ""
    return DM_TEMPLATES.get(language, DM_TEMPLATES["en"]).format(name=first, topic=on, link=link)
