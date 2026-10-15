"""Understanding and answering a comment. Rules handle the common case; the LLM classifies the rest and drafts answers to questions.
Every LLM draft is checked before it can be posted: length, no phone numbers, no hype, only our own link, and no number that is not in the
post it answers. Anything that fails the checks becomes a safe template or goes to a human."""
from app.core import brand
import re
import zlib
from dataclasses import dataclass, field
from typing import List, Optional

from app.modules.knowledge import site
from app.modules.knowledge.reply import answer as grounded_answer, has_topic, topics_in
from app.modules.tracking import requirement as rq
from app.platform.text import HYPE, PHONE, normalize_indian_mobile

INTENTS = ("interested", "question", "praise", "greeting", "complaint", "spam", "other")
GREETING = re.compile(r"^\W*(hi+|hello+|hey+|hii+|namaste|namaskar|good (morning|afternoon|evening)|hello you there)\W*$", re.I)
MAX_REPLY = 320
URL = re.compile(r"https?://\S+", re.I)
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
INTERESTED = re.compile(r"\b(interested|intrested|info|details|dm|price\??|rate\??|contact|available)\b|इंटरेस्टेड|रुचि|आवड|डिटेल|किंमत|कीमत", re.I)
SPAM = re.compile(r"(whatsapp me|dm me|click here|earn money|crypto|forex|loan offer|followers|http|www\.|t\.me/|bit\.ly)", re.I)
ABUSE = re.compile(r"\b(fraud|scam|cheat|fake|liar|stupid|idiot|bloody)\b", re.I)
# Spam without the "whatsapp me" / "dm me" wording: a buyer writing "whatsapp me on 98765 43210" is a lead, not a spammer
SPAM_HARD = re.compile(r"(click here|earn money|work from home|crypto|forex|loan offer|followers|http|www\.|t\.me/|bit\.ly)", re.I)
COMMENT_PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?|0)?[6-9](?:[\s-]?\d){9}(?!\d)")  # as people type it: "98765 43210", "+91-98765-43210"
# Asking for material or a call back, in words the INTERESTED keywords miss ("send brochure", "माहिती पाहिजे", "pls share")
WANTS_INFO = re.compile(r"\b(brochure|floor\s*plans?|price\s*list|more\s*info|send\s*(me\s*)?(the\s*)?(details|info|pics|photos)|share\s*(the\s*)?(details|info)|"
                        r"call\s*(me|back)|contact\s*me|details\s*(bhejo|send|pls|please)|bhej\s*do|pathva)\b|"
                        r"माहिती|जानकारी|ब्रोशर|डिटेल्स", re.I)
# Short positive comments ("Nice", "Wow 😍", "👍"): thanked, never sent to a person
PRAISE = re.compile(r"^\W*((very |so |too )?(nice|wow+|superb|beautiful|awesome|amazing|lovely|great|good|excellent|mast|zakkas|sundar|chan|"
                    r"khoob|badhiya|osm|gorgeous|congrats|congratulations)\b[\s!.]*(flat|home|house|property|one|place|view|work|post)?|"
                    r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2764\uFE0F\s]+)[\W\U0001F300-\U0001FAFF]*$", re.I)
# The price is too high for them: a salesperson asks for their budget instead of letting them go
OBJECTION = re.compile(r"\b(too\s+(expensive|costly|high)|very\s+(expensive|costly|high)|over\s*priced|expensive|costly|mehenga|mahenga|mehnga|"
                       r"mahag|out of (my )?budget|not in (my )?budget|budget (se )?(bahar|jyada|zyada))\b|महंगा|महाग", re.I)
WANT = re.compile(r"\b(interested|intrested|need|want|looking|require|requirement|searching|chahiye|pahije|hava|havay|any|options?|available|suggest|have you)\b|चाहिए|पाहिजे|हवा", re.I)

TEMPLATES = {
    "en": {
        "interested": "Thanks{name}! Details and price: {link} . Leave your WhatsApp number there and our team will send you the price list and floor plans.",
        "interested_dm": "Thanks{name}! Details and price: {link} . We have also sent you a message \U0001F4E9",
        "question": "Good question{name}! We will answer here within a few hours. Meanwhile, the full details are here: {link}",
        "praise": "Thank you{name}! Follow the page for more Pune property guides and listings.",
        "greeting": "Hello{name}! Comment INTERESTED on a listing for the details, or ask your question here and our team will help.",
        "phone": "Thanks{name}! Our team will call you shortly. For your privacy you may delete the number from this comment now.",
        "requirement": "Thanks{name}! Noted: {want}. Matching homes and prices are here: {link}",
        "requirement_dm": "Thanks{name}! Noted: {want}. Matching homes and prices are here: {link} . We are also sending you a message with options.",
        "objection": "Understood{name}. Tell us your budget and preferred area, and we will share homes that fit: {link}",
    },
    "hi": {
        "interested": "धन्यवाद{name}! पूरी जानकारी और कीमत यहाँ है: {link} . वहाँ अपना WhatsApp नंबर दें, हमारी टीम आपको प्राइस लिस्ट और फ्लोर प्लान भेजेगी।",
        "interested_dm": "धन्यवाद{name}! पूरी जानकारी और कीमत यहाँ है: {link} . हमने आपको मैसेज भी भेजा है \U0001F4E9",
        "question": "अच्छा सवाल{name}! हम कुछ घंटों में यहीं जवाब देंगे। पूरी जानकारी यहाँ है: {link}",
        "praise": "धन्यवाद{name}! पुणे की प्रॉपर्टी गाइड और लिस्टिंग के लिए पेज को फॉलो करें।",
        "greeting": "नमस्ते{name}! विवरण के लिए कमेंट में INTERESTED लिखें, या अपना सवाल यहीं पूछें, हमारी टीम मदद करेगी।",
        "phone": "धन्यवाद{name}! हमारी टीम आपको जल्द कॉल करेगी। अपनी प्राइवेसी के लिए आप इस कमेंट से नंबर हटा सकते हैं।",
        "requirement": "धन्यवाद{name}! नोट किया: {want}। मिलते-जुलते घर और कीमतें यहाँ हैं: {link}",
        "requirement_dm": "धन्यवाद{name}! नोट किया: {want}। मिलते-जुलते घर और कीमतें यहाँ हैं: {link} . हम आपको विकल्पों के साथ मैसेज भी भेज रहे हैं।",
        "objection": "समझ गए{name}। अपना बजट और पसंदीदा एरिया बताएं, हम आपके बजट के घर भेजेंगे: {link}",
    },
    "mr": {
        "interested": "धन्यवाद{name}! संपूर्ण माहिती आणि किंमत इथे आहे: {link} . तिथे तुमचा WhatsApp नंबर द्या, आमची टीम तुम्हाला प्राइस लिस्ट आणि फ्लोअर प्लॅन पाठवेल.",
        "interested_dm": "धन्यवाद{name}! संपूर्ण माहिती आणि किंमत इथे आहे: {link} . आम्ही तुम्हाला मेसेजही पाठवला आहे \U0001F4E9",
        "question": "छान प्रश्न{name}! आम्ही काही तासांत इथेच उत्तर देऊ. संपूर्ण माहिती इथे आहे: {link}",
        "praise": "धन्यवाद{name}! पुण्यातील प्रॉपर्टी गाइड आणि लिस्टिंगसाठी पेज फॉलो करा.",
        "greeting": "नमस्कार{name}! तपशीलासाठी कमेंटमध्ये INTERESTED लिहा, किंवा तुमचा प्रश्न इथेच विचारा, आमची टीम मदत करेल.",
        "phone": "धन्यवाद{name}! आमची टीम तुम्हाला लवकरच कॉल करेल. तुमच्या प्रायव्हसीसाठी तुम्ही या कमेंटमधून नंबर काढू शकता.",
        "requirement": "धन्यवाद{name}! नोंद केली: {want}. जुळणारी घरे आणि किंमती इथे आहेत: {link}",
        "requirement_dm": "धन्यवाद{name}! नोंद केली: {want}. जुळणारी घरे आणि किंमती इथे आहेत: {link} . आम्ही तुम्हाला पर्यायांसह मेसेजही पाठवत आहोत.",
        "objection": "समजले{name}. तुमचे बजेट आणि आवडता एरिया सांगा, आम्ही तुमच्या बजेटमधील घरे पाठवू: {link}",
    },
}

# Instagram: links in comments are not clickable, so replies point at the bio. Only the wording with a link differs from Facebook.
BIO = {"en": "the link in our bio", "hi": "हमारे बायो का लिंक", "mr": "आमच्या बायोमधील लिंक"}
IG_TEMPLATES = {
    "en": {
        "interested": "Thanks{name}! Full details are at the link in our bio. Leave your WhatsApp number there and our team will send you the price list and floor plans.",
        "interested_dm": "Thanks{name}! We have sent you a message with the details and price \U0001F4E9",
        "question": "Good question{name}! We will answer here within a few hours. Meanwhile, the details are at the link in our bio.",
        "praise": "Thank you{name}! Follow this account for more Pune property guides and listings.",
        "requirement": "Thanks{name}! Noted: {want}. Matching homes and prices are at the link in our bio.",
        "requirement_dm": "Thanks{name}! Noted: {want}. We are sending you a message with matching homes and prices \U0001F4E9",
        "objection": "Understood{name}. Tell us your budget and preferred area, and we will share homes that fit. The link in our bio has more.",
    },
    "hi": {
        "interested": "धन्यवाद{name}! पूरी जानकारी हमारे बायो के लिंक पर है। वहाँ अपना WhatsApp नंबर दें, हमारी टीम आपको प्राइस लिस्ट और फ्लोर प्लान भेजेगी।",
        "interested_dm": "धन्यवाद{name}! हमने आपको जानकारी और कीमत के साथ मैसेज भेजा है \U0001F4E9",
        "question": "अच्छा सवाल{name}! हम कुछ घंटों में यहीं जवाब देंगे। पूरी जानकारी हमारे बायो के लिंक पर है।",
        "praise": "धन्यवाद{name}! पुणे की प्रॉपर्टी गाइड और लिस्टिंग के लिए इस अकाउंट को फॉलो करें।",
        "requirement": "धन्यवाद{name}! नोट किया: {want}। मिलते-जुलते घर और कीमतें हमारे बायो के लिंक पर हैं।",
        "requirement_dm": "धन्यवाद{name}! नोट किया: {want}। हम आपको मिलते-जुलते घर और कीमतें मैसेज में भेज रहे हैं \U0001F4E9",
        "objection": "समझ गए{name}। अपना बजट और पसंदीदा एरिया बताएं, हम आपके बजट के घर भेजेंगे। ज़्यादा जानकारी हमारे बायो के लिंक में।",
    },
    "mr": {
        "interested": "धन्यवाद{name}! संपूर्ण माहिती आमच्या बायोमधील लिंकवर आहे. तिथे तुमचा WhatsApp नंबर द्या, आमची टीम तुम्हाला प्राइस लिस्ट आणि फ्लोअर प्लॅन पाठवेल.",
        "interested_dm": "धन्यवाद{name}! आम्ही तुम्हाला माहिती आणि किंमतीसह मेसेज पाठवला आहे \U0001F4E9",
        "question": "छान प्रश्न{name}! आम्ही काही तासांत इथेच उत्तर देऊ. संपूर्ण माहिती आमच्या बायोमधील लिंकवर आहे.",
        "praise": "धन्यवाद{name}! पुण्यातील प्रॉपर्टी गाइड आणि लिस्टिंगसाठी हे अकाउंट फॉलो करा.",
        "requirement": "धन्यवाद{name}! नोंद केली: {want}. जुळणारी घरे आणि किंमती आमच्या बायोमधील लिंकवर आहेत.",
        "requirement_dm": "धन्यवाद{name}! नोंद केली: {want}. आम्ही तुम्हाला जुळणारी घरे आणि किंमती मेसेजमध्ये पाठवत आहोत \U0001F4E9",
        "objection": "समजले{name}. तुमचे बजेट आणि आवडता एरिया सांगा, आम्ही तुमच्या बजेटमधील घरे पाठवू. अधिक माहिती आमच्या बायोमधील लिंकवर.",
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
    "Never use words like best, perfect, guaranteed, dream. 'interested' means the person wants details or to be contacted: that includes "
    "asking for a brochure, price list, call back or site visit, and stating what they are looking for (BHK, area or budget)."
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
    phone: Optional[str] = None                        # a mobile number the commenter wrote, asking to be called (never repeated in a reply)
    requirement: dict = field(default_factory=dict)    # what they said they want (tracking.requirement fields), for the lead
    signal: str = ""                                   # phone | requirement | objection | visit | info: how warm the lead is


# How warm each kind of comment is, added to the lead's base score (EngageService._record_lead)
SIGNAL_SCORE = {"phone": 15, "requirement": 8, "visit": 8, "objection": 4, "info": 4}


def detect_language(text: str) -> str:
    if re.search(r"[ऀ-ॿ]", text or ""):
        return "mr" if re.search(r"(आहे|तुम्ही|किंमत|हवे|माहिती|पाहिजे)", text) else "hi"
    return "en"


def first_name(name: Optional[str]) -> str:
    n = (name or "").strip().split(" ")[0]
    return f" {n}" if n and re.fullmatch(r"[A-Za-zऀ-ॿ.'-]{1,30}", n) else ""


# Comments on our agent-recruitment posts and reels ("Comment AGENT"): the reply is about the free trial, never price lists or floor plans.
AGENT_ASK = re.compile(r"\b(agents?|join|pilot|trial|interested|intrested|details|demo|how|kaise|cost|charges?|free|yes|haan|ha)\b|एजेंट|इंटरेस्टेड|जानकारी|ट्रायल", re.I)
AGENT_TEMPLATES = {
    "en": {"facebook": "Thanks{name}! Claim your free Avasetu trial: 1 month free, every property, no card. Open to the first 20 Pune agents. Claim it here: {link} . We have also sent you a message.",
           "instagram": "Thanks{name}! We have sent you a message with the link to claim your free trial. It is also at the link in our bio."},
    "hi": {"facebook": "धन्यवाद{name}! Avasetu का फ्री ट्रायल लें: पहली 3 प्रॉपर्टी की मार्केटिंग फ्री, कोई कार्ड नहीं। यहाँ क्लेम करें: {link} . हमने आपको मैसेज भी भेजा है।",
           "instagram": "धन्यवाद{name}! हमने आपको फ्री ट्रायल का लिंक मैसेज में भेजा है। यह हमारे बायो के लिंक में भी है।"},
}


def agent_reply(lang: str, name: Optional[str], link: str, channel: str = "facebook") -> str:
    t = AGENT_TEMPLATES.get(lang, AGENT_TEMPLATES["en"])["instagram" if channel == "instagram" else "facebook"]
    return t.format(name=first_name(name), link=link)


# More English wordings (the most common case): ten identical replies under one post read as a bot to people and to Meta's spam filter.
# The pick is fixed per commenter, so one person never sees two wordings of the same reply.
EN_VARIANTS = {
    "facebook": {
        "interested": ("Hi{name}, here are the details and price: {link} . Leave your WhatsApp number there and we will send the price list and floor plans.",
                       "Sure{name}! Everything about this home, with the price, is here: {link} . Add your WhatsApp number there for the price list."),
        "interested_dm": ("Hi{name}, details and price are here: {link} . Check your messages too \U0001F4E9",
                          "Sure{name}! We just messaged you. The details are also here: {link}"),
        "praise": ("Thanks a lot{name}! \U0001F64F Follow the page for more from Pune.",
                   "Glad you liked it{name}! Follow the page for more guides like this."),
    },
    "instagram": {
        "interested": ("Hi{name}, the details and price are at the link in our bio. Leave your WhatsApp number there for the price list and floor plans.",),
        "interested_dm": ("Hi{name}, check your messages \U0001F4E9 We sent the details and price.",
                          "Sure{name}! We just messaged you the details."),
        "praise": ("Thanks a lot{name}! \U0001F64F Follow for more from Pune.", "Glad you liked it{name}! Follow for more guides like this."),
    },
}


def _pick(options: tuple, name: Optional[str]) -> str:
    return options[zlib.crc32((name or "").encode("utf-8")) % len(options)]


def render(kind: str, lang: str, name: Optional[str], link: str, channel: str = "facebook", want: str = "") -> str:
    ch = "instagram" if channel == "instagram" else "facebook"
    if ch == "instagram":
        t = IG_TEMPLATES.get(lang, IG_TEMPLATES["en"]).get(kind)
    if ch == "facebook" or not t:
        t = TEMPLATES.get(lang, TEMPLATES["en"])[kind]
    if lang == "en" and kind in EN_VARIANTS[ch]:
        t = _pick((t,) + EN_VARIANTS[ch][kind], name)
    return t.format(name=first_name(name), link=link, want=want)


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


def phone_in(text: str) -> Optional[str]:
    """A mobile number written in the comment, normalised (+91...), or None."""
    m = COMMENT_PHONE.search(text or "")
    if not m:
        return None
    try:
        return normalize_indian_mobile(m.group(0))
    except ValueError:
        return None


def requirement_in(text: str) -> dict:
    """What a commenter says they are looking for ("Need 2bhk in Baner under 80L", "Any 3 BHK?", "budget 70 lakh, any option?"). Empty when the
    comment only asks about the post ("Is it 2 BHK?", "price 85 lakh?"): two details, or one with a word of wanting."""
    found = {k: v for k, v in rq.infer_from_message(text).items() if v not in (None, [], "")}
    named = {("budget" if k.startswith("budget") else k) for k in {"bhk", "budget_min_inr", "budget_max_inr", "localities"} & set(found)}
    if not {"bhk", "budget"} & named:
        return {}
    return found if len(named) >= 2 or WANT.search(text or "") else {}


def want_text(req: dict) -> str:
    bits = [rq.bhk_text(req.get("bhk")), ", ".join(req.get("localities") or []) or None, rq.budget_text(req.get("budget_min_inr"), req.get("budget_max_inr"))]
    return ", ".join(b for b in bits if b)


REPLY_LANG = {"en": "en", "hi": "hi", "hinglish": "hi", "mr": "mr", "mr_latn": "mr"}


async def grounded_decision(text: str, grounding, link: str, llm, channel: str) -> Decision:
    """Answer a question from what we know about the post's home, project or area. Only when the answer is not fully covered is a person asked as well."""
    r = await grounded_answer(text, grounding, channel, llm)
    reply = r.text.replace("{interest_url}", link)
    reason = "grounded answer" if r.confident else f"not in our facts: {r.missing}"
    return Decision("question", REPLY_LANG.get(r.language, "en"), reply, needs_human=not r.confident, reason=reason, missing=r.missing, basis=r.basis,
                    gaps=list(r.gaps), signal="visit" if "visit" in topics_in(text) else "")


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
                        reason="agent asks about the free trial")
    if ig:
        link = BIO["en"]  # never put a URL in an Instagram reply
    if audience != "agents" and intent != "complaint" and not SPAM_HARD.search(text or ""):
        phone = phone_in(text)
        if phone:
            # "call me 98765 43210": the warmest comment there is. The reply never repeats the number; the lead gets it
            return Decision("interested", lang, render("phone", lang, from_name, link, channel), reason="number in the comment", phone=phone,
                            requirement=requirement_in(text), signal="phone")
        if intent in (None, "spam"):
            req = requirement_in(text)
            if intent == "spam" and not req:  # "whatsapp me for 2bhk wagholi" is a buyer; anything else stays spam
                return Decision("spam", lang, None, reason="not answered")
            if req:
                return Decision("interested", lang, render("requirement", lang, from_name, link, channel, want=want_text(req)),
                                reason="stated a requirement", requirement=req, signal="requirement")
            if OBJECTION.search(text or ""):
                return Decision("interested", lang, render("objection", lang, from_name, link, channel), reason="price objection", signal="objection")
            if WANTS_INFO.search(text or "") and not asks_about_the_post(text):
                return Decision("interested", lang, render("interested", lang, from_name, link, channel), reason="asked for details", signal="info")
            if intent is None and PRAISE.match(text or ""):
                return Decision("praise", lang, render("praise", lang, from_name, link, channel), reason="short praise")
    about_us = site.best(text, min_score=1) if intent is None and looks_like_question(text) else None
    if about_us is not None and about_us.audience != "buyer":
        # 'what is Avasetu?', 'how much for agents?': the same vetted answer as the website chat
        more = "Details: the link in our bio." if ig else f"Details: {link}"
        return Decision("question", lang, f"{about_us.answer} {more}", reason=f"about us: {about_us.id}")
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
    "en": "Hi{name}, thanks for your comment{topic}. Reply here with your WhatsApp number and we will send you the price list and floor plans. "
          "Your budget helps too, if you like. Details: {link}",
    "hi": "नमस्ते{name}, आपके कमेंट{topic} के लिए धन्यवाद। अपना WhatsApp नंबर यहीं भेजें, हम आपको प्राइस लिस्ट और फ्लोर प्लान भेजेंगे। "
          "चाहें तो अपना बजट भी बताएं। जानकारी: {link}",
    "mr": "नमस्कार{name}, तुमच्या कमेंट{topic}साठी धन्यवाद. तुमचा WhatsApp नंबर इथेच पाठवा, आम्ही तुम्हाला प्राइस लिस्ट आणि फ्लोअर प्लॅन पाठवू. "
          "हवे असल्यास तुमचे बजेट पण सांगा. माहिती: {link}",
}
DM_AGENTS = ("Hi{name}, thanks for asking about Avasetu. Claim your free trial: 1 month free, every property, no card. Open to the first 20 Pune agents. Reply here with your WhatsApp number and the areas you work in, "
             "and we will set it up with you. Or join here: {link}")


def dm_text(language: str, name: Optional[str], link: str, topic: str = "", audience: str = "buyers") -> str:
    first = f" {name.split()[0]}" if name and name.split() else ""
    if audience == "agents":
        return DM_AGENTS.format(name=first, link=link)
    on = (f" on {topic}" if language == "en" else f" ({topic})") if topic else ""
    return DM_TEMPLATES.get(language, DM_TEMPLATES["en"]).format(name=first, topic=on, link=link)
