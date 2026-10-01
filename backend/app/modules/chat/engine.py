"""The conversation: pure logic (no database, no network except an optional LLM call), so it is easy to test and reuse for other channels.

State lives in a plain dict (`data`). One call to `turn()` reads the visitor's message, updates the state, answers any question from the vetted
knowledge base (or, failing that, from an LLM restricted to that knowledge and checked before use), and then asks for the next missing detail.
A phone number is only accepted after the visitor has been shown the consent line, and never guessed.
"""
from app.core import brand
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.modules.engage.brain import ABUSE, valid_reply
from app.modules.knowledge.reply import answer as grounded_answer, has_topic, topics_in
from app.modules.onboarding.phone import normalize_indian_mobile
from app.modules.tracking import requirement as rq

from . import kb

CONSENT = f"By sharing your number you agree that {brand.NAME} may contact you about this enquiry."
ORDER = ["tx", "locality", "bhk", "budget", "timeline", "name", "phone"]
GREETING = re.compile(r"^\W*(hi+|hello+|hey+|namaste|namaskar|hii+|good (morning|afternoon|evening))\W*$", re.I)
YES = re.compile(r"^\W*(yes|y|yeah|yep|ok|okay|sure|haan|ha|ho|confirm|please do)\W*$", re.I)
NO = re.compile(r"^\W*(no|nope|not now|later|skip|nahi|nako|no thanks|na|maybe later)\W*$", re.I)
HUMAN = re.compile(r"\b(talk|speak|connect|call)\b.*\b(human|person|agent|someone|team|me)\b|\bcall me\b|\breal person\b", re.I)
PHONE_RX = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
QUESTION = re.compile(r"\?|^\s*(what|how|why|when|where|which|who|is|are|can|could|do|does|will|should|kya|kaise|kitna|kitni|kab|kaun|kahan)\b", re.I)

PROMPTS = {
    "tx": ("Are you looking to buy or to rent?", ["Buy", "Rent", "Just exploring"]),
    "locality": ("Which area are you most interested in?", ["Kharadi", "Upper Kharadi", "Wagholi", "Somewhere else"]),
    "bhk": ("How many bedrooms do you need?", ["1 BHK", "2 BHK", "3 BHK", "4 BHK"]),
    "budget": ("What budget do you have in mind?", ["Under 50 lakh", "50-80 lakh", "80 lakh to 1.2 crore", "1.2 to 2 crore", "Above 2 crore"]),
    "timeline": ("When are you planning to move?", ["Right now", "In 1-3 months", "In 3-6 months", "Just looking"]),
    "name": ("What should I call you?", []),
    "phone": (f"Share your mobile number and our team will send you matching homes and answer anything I cannot. {CONSENT}", ["Not now"]),
}


def new_data() -> dict:
    return {"tx": None, "locality": None, "bhk": None, "budget_min": None, "budget_max": None, "timeline": None, "financing": None,
            "name": None, "phone": None, "pending_phone": None, "consent_shown": False, "declined": [], "asked": None,
            "lead_done": False, "questions": [], "needs_human": False, "greeted": False, "missing": []}


@dataclass
class Turn:
    reply: str
    quick: List[str] = field(default_factory=list)
    lead: Optional[dict] = None       # set once, when a phone number has been confirmed with consent
    needs_human: bool = False


def filled(d: dict, f: str) -> bool:
    if f == "budget":
        return d["budget_min"] is not None or d["budget_max"] is not None
    return bool(d.get(f))


def next_field(d: dict) -> Optional[str]:
    return next((f for f in ORDER if not filled(d, f) and f not in d["declined"]), None)


def _phone_in(text: str) -> Optional[str]:
    m = PHONE_RX.search(text)
    if not m:
        return None
    try:
        return normalize_indian_mobile(m.group(0))
    except Exception:
        return None


def _name_in(text: str, asked: Optional[str]) -> Optional[str]:
    m = re.search(r"(?:my name is|i am|i'm|this is|mera naam|maza nav|naam)\s+([A-Za-z][A-Za-z .'-]{1,40})", text, re.I)
    cand = m.group(1) if m else (text.strip() if asked == "name" else None)
    if not cand or NO.match(cand) or PHONE_RX.search(cand) or len(cand.split()) > 4 or not re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,40}", cand.strip()):
        return None
    cand = re.split(r"\b(hai|and|,)\b", cand)[0].strip()
    return cand.title() if len(cand) >= 2 else None


def extract(d: dict, text: str) -> List[str]:
    """Update `d` from the visitor's message. Returns the fields that were newly filled."""
    before = {f: filled(d, f) for f in ORDER}
    t, low, asked = text.strip(), text.strip().lower(), d["asked"]

    if YES.match(t) and d["pending_phone"]:
        d["phone"], d["pending_phone"] = d["pending_phone"], None
    elif NO.match(t) and d["pending_phone"]:
        d["pending_phone"] = None
        d["declined"].append("phone")
    elif NO.match(t) and asked and asked not in d["declined"] and not filled(d, asked):
        d["declined"].append(asked)

    if not d["tx"]:
        if re.search(r"\b(rent|rental|kiraya|kiraye|lease)\b", low):
            d["tx"] = "rent"
        elif re.search(r"\b(buy|buying|purchase|kharid\w*|ghar lena|invest)\b", low) or (asked == "tx" and low == "buy"):
            d["tx"] = "buy"
        elif asked == "tx" and re.search(r"exploring|just looking|browsing", low):
            d["tx"] = "exploring"

    found = rq.infer_from_message(t)
    if found.get("localities") and not d["locality"]:
        d["locality"] = found["localities"][0]
    if not filled(d, "budget") and ("budget_min_inr" in found or "budget_max_inr" in found):
        d["budget_min"], d["budget_max"] = found.get("budget_min_inr"), found.get("budget_max_inr")
    for src, dst in (("bhk", "bhk"), ("timeline", "timeline"), ("financing", "financing")):
        if found.get(src) and not d[dst]:
            d[dst] = found[src]
    if asked == "bhk" and not d["bhk"]:
        m = re.fullmatch(r"\s*(\d(?:\.5)?)\s*(?:bhk)?\s*\+?\s*", low)
        if m and 0.5 <= float(m.group(1)) <= 10:
            d["bhk"] = float(m.group(1))
    if asked == "timeline" and not d["timeline"]:  # short typed answers to "when are you planning to move?"
        if re.search(r"just looking|exploring|browsing|not sure|no idea|dont know|don't know", low):
            d["timeline"] = "exploring"
        elif re.fullmatch(r"\W*(now|today|asap|immediately|this month|urgent|jaldi|abhi)\W*", low):
            d["timeline"] = "now"
        elif re.fullmatch(r"\W*(soon|few months|couple of months|next few months)\W*", low):
            d["timeline"] = "1_3_months"
    if asked == "locality" and not d["locality"] and not NO.match(t) and 2 <= len(t) <= 40 and re.fullmatch(r"[A-Za-z .'-]+", t):
        d["locality"] = "Other" if low in ("somewhere else", "other", "elsewhere") else t.title()
    if asked == "tx" and low == "just exploring":
        d["timeline"] = d["timeline"] or "exploring"

    phone = _phone_in(t)
    if phone:
        if d["consent_shown"]:
            d["phone"], d["pending_phone"] = phone, None
        else:  # volunteered before we showed the consent line: ask to confirm first
            d["pending_phone"] = phone
    if not d["name"]:
        d["name"] = _name_in(t, asked)
    return [f for f in ORDER if filled(d, f) and not before[f]]


def is_question(text: str) -> bool:
    return bool(QUESTION.search(text)) and not YES.match(text) and not NO.match(text)


LLM_SYSTEM = (
    f"You answer a home buyer's question for the {brand.TEAM}, using ONLY the KNOWLEDGE below. Reply with one JSON object: "
    '{"answerable": true or false, "answer": "..."}. The answer is at most 3 short sentences, in the buyer\'s language, friendly and plain. '
    "If KNOWLEDGE does not contain the answer, set answerable=false and answer=''. Never invent prices, distances, dates, amenities, approvals or "
    "availability. Never include phone numbers or links. Never use words like best, perfect, guaranteed, dream."
)


async def answer(text: str, llm) -> Optional[str]:
    hit = kb.best(text, min_score=1)
    if hit:
        return hit.answer
    hits = kb.search(text, 3)
    context = "\n".join(f"- {e.answer}" for _, e in hits) if hits else ""
    if not context or llm is None or not hasattr(llm, "json"):
        return None
    raw = await llm.json(LLM_SYSTEM, f"KNOWLEDGE:\n{context}\n\nQUESTION:\n{text[:400]}")
    if isinstance(raw, dict) and raw.get("answerable") is True:
        draft = (raw.get("answer") or "").strip()
        if valid_reply(draft, context, ""):
            return draft
    return None


def summary(d: dict) -> str:
    bits = [f"Chat enquiry ({d['tx'] or 'not stated'})"]
    if d["locality"]:
        bits.append(f"area {d['locality']}")
    if d["bhk"]:
        bits.append(rq.bhk_text(d["bhk"]) or f"{d['bhk']} BHK")
    b = rq.budget_text(d["budget_min"], d["budget_max"])
    if b:
        bits.append(f"budget {b}")
    if d["timeline"]:
        bits.append(f"timeline {d['timeline'].replace('_', '-')}")
    text = ", ".join(bits) + "."
    if d["questions"]:
        text += " Asked: " + " | ".join(q[:120] for q in d["questions"][-2:])
    return text[:900]


def _ack(new: List[str], d: dict) -> str:
    bits = []
    if "tx" in new and d["tx"] in ("buy", "rent"):
        bits.append(d["tx"])
    if "locality" in new:
        bits.append(d["locality"])
    if "bhk" in new:
        bits.append(rq.bhk_text(d["bhk"]) or "")
    if "budget" in new:
        bits.append(rq.budget_text(d["budget_min"], d["budget_max"]) or "")
    if "timeline" in new:
        bits.append({"now": "moving soon", "1_3_months": "moving in 1-3 months", "3_6_months": "moving in 3-6 months", "exploring": "just exploring"}.get(d["timeline"], ""))
    bits = [b for b in bits if b]
    return ("Got it: " + ", ".join(bits) + ".") if bits else ""


async def turn(d: dict, text: str, llm, grounding=None) -> Turn:
    """`grounding` (knowledge.Grounding) is what we know about the home, post or area the visitor is looking at; questions about it are answered
    from it, and what it does not cover is said plainly and handed to a person."""
    text = (text or "").strip()
    first = not d["greeted"]
    d["greeted"] = True
    if ABUSE.search(text):
        return Turn("I will pass this to our team so they can look into it. If you would like help finding a home, just tell me what you need.", needs_human=True)
    if first and GREETING.match(text):
        p, q = PROMPTS[nf := next_field(d) or "tx"]
        d["asked"] = nf
        return Turn(f"Hi! I am the {brand.NAME} assistant. I can answer basic questions about buying or renting in Pune and pass your requirement to our team. {p}", q)

    new = extract(d, text)
    parts: List[str] = []
    quick: List[str] = []
    lead = None
    needs_human = False

    if HUMAN.search(text):
        d["needs_human"] = needs_human = True
        parts.append("Of course, our team can take it from here.")
    # 'ready' or 'Kharadi' typed straight after we asked about timeline or area is the answer to that, not a question about the home
    short_reply = bool(d["asked"]) and len(text.split()) <= 3 and "?" not in text and set(topics_in(text)) <= {"possession", "price", "location", "size"}
    if grounding is not None and has_topic(text) and not short_reply and (is_question(text) or len(text.split()) <= 6):
        d["questions"].append(text[:200])
        r = await grounded_answer(text, grounding, "chat", llm)
        parts.append(r.text)
        if not r.confident:
            d["needs_human"] = needs_human = True
            d.setdefault("missing", []).append((r.missing or "")[:100])
    elif is_question(text) and not (d["asked"] and not kb.search(text, 1) and len(text.split()) <= 3):
        d["questions"].append(text[:200])
        ans = await answer(text, llm)
        if ans:
            parts.append(ans)
        else:
            d["needs_human"] = needs_human = True
            parts.append("I do not want to guess on that one. I will ask our team to confirm it for you.")
    ack = _ack(new, d)
    if ack and not parts:
        parts.append(ack)

    if "phone" in new and not d["lead_done"]:
        d["lead_done"] = True
        d["asked"] = None
        lead = {"name": d["name"] or "Website visitor", "phone": d["phone"], "message": summary(d), "bhk": d["bhk"],
                "budget_min_inr": d["budget_min"], "budget_max_inr": d["budget_max"], "timeline": d["timeline"], "financing": d["financing"]}
        parts.append(f"Thank you{(' ' + d['name'].split()[0]) if d['name'] else ''}! Our team will contact you soon with matching options. You can keep asking me questions in the meantime.")
        return Turn(" ".join(parts), [], lead, needs_human)

    if d["pending_phone"]:
        p = d["pending_phone"]
        d["consent_shown"] = True
        d["asked"] = "phone"
        parts.append(f"Can our team contact you on {p[-10:-5]} {p[-5:]}? Reply YES to confirm. {CONSENT}")
        return Turn(" ".join(parts), ["Yes", "No"], None, needs_human)

    nf = next_field(d)
    if d["needs_human"] and not d["phone"] and "phone" not in d["declined"]:
        nf = "phone"
    if nf:
        prompt, quick = PROMPTS[nf]
        d["asked"] = nf
        if nf == "phone":
            d["consent_shown"] = True
        parts.append(prompt)
    else:
        d["asked"] = None
        parts.append("Is there anything else I can help you with?")
    return Turn(" ".join(p for p in parts if p), quick, None, needs_human)
