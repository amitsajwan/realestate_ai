"""The conversation: pure logic (no database, no network except an optional LLM call and an optional home finder the caller passes in), so it
is easy to test and reuse for other channels.

State lives in a plain dict (`data`). One call to `turn()` reads the visitor's message, updates the state, answers any question from the vetted
knowledge base (or, failing that, from an LLM restricted to that knowledge and checked before use), shows matching homes once the area, BHK and
budget are known, and then asks for the next missing detail.

Rules the tests hold us to:
- a known slot is never asked again; intent (buy / rent) is inferred from what the buyer says (a budget in lakh or crore means buy; rent,
  per month, deposit mean rent); each question is asked at most twice;
- the number is asked at most twice per conversation, only after we gave something (an answer, homes, or a hand-off), the consent sentence is
  shown once, next to the first ask, and 'Not now' pauses the asking for at least five turns;
- a phone number is only accepted after the visitor has seen the consent line, and never guessed; the bot never repeats a full number;
- after the website lead is made the funnel stops: we answer questions and show homes, we never start the questions again;
- sample homes are always labelled; homes and prices come only from the finder (the agent's live listings), never invented.

Language: when `data["localise"]` is set (the website chat) the fixed sentences follow the buyer's language (phrases.py). WhatsApp leaves it off
and translates the English sentences itself.
"""
import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable, List, Optional

from app.core import brand
from app.modules.engage.brain import ABUSE, valid_reply
from app.modules.knowledge.reply import answer as grounded_answer, detect_language, has_topic, topics_in
from app.modules.onboarding.phone import normalize_indian_mobile
from app.modules.tracking import requirement as rq

from . import kb
from . import phrases
from .phrases import WHATSAPP, ack_word, quick as qr, say

WHATSAPP_LABEL = WHATSAPP

CONSENT = say("consent")
ORDER = ["tx", "locality", "bhk", "budget", "timeline", "name", "phone"]
MAX_ASKS = 2            # any one question
MAX_PHONE_ASKS = 2      # the number, per conversation
SNOOZE_TURNS = 5        # after 'Not now'
PHONE_GAP_TURNS = 3     # never ask for the number in back-to-back replies
MAX_NAME_USES = 2
GREETING = re.compile(r"^\W*(hi+|hello+|hey+|namaste|namaskar|hii+|good (morning|afternoon|evening)|नमस्ते|नमस्कार)\W*$", re.I)
YES = re.compile(r"^\W*(yes|y|yeah|yep|ok|okay|sure|haan|ha|ho|confirm|please do)\W*$", re.I)
NO = re.compile(r"^\W*(no|nope|not now|later|skip|nahi|nako|no thanks|na|maybe later|abhi nahi|baad mein|aata nako|nantar|अभी नहीं|आता नको)\W*$", re.I)
HUMAN = re.compile(r"\b(talk|speak|connect|call)\b.*\b(human|person|agent|someone|team|me)\b|\bcall me\b|\breal person\b", re.I)
PHONE_RX = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
QUESTION = re.compile(r"\?|^\s*(what|how|why|when|where|which|who|is|are|can|could|do|does|will|should|kya|kaise|kitna|kitni|kab|kaun|kahan)\b", re.I)
RENT_WORDS = re.compile(r"\b(rent|rental|renting|kiraya|kiraye|kirae|lease|per month|a month|monthly|deposit|bhade|bhadyane|bhada)\b|/\s*month|\bpm\b|किराए|किराया|भाड्याने", re.I)
BUY_WORDS = re.compile(r"\b(buy|buying|purchase|kharid\w*|ghar lena|invest\w*|vikat|own a)\b|खरीद|विकत", re.I)
ABOUT = re.compile(r"^\W*(tell me (more )?about (it|this|this home|the home)|details( please)?|about this home|iske baare mein( batao)?|"
                   r"yabaddal sanga|इसके बारे में बताइए|याबद्दल सांगा)\W*$", re.I)
HOMES = re.compile(r"\b(similar|show (me )?(some |the |more )?(homes|options|flats|houses|listings|properties|matches)|any (homes|flats|houses|listings)|"
                   r"(home|flat|house|more) options|what (homes|flats) do you have|ghar dikhao|aise aur ghar|asech ghar|ghare dakhva|flat dikhao)\b|"
                   r"घर दिखाइए|ऐसे और घर|असेच घर|घरे दाखवा", re.I)
SIMILAR = re.compile(r"\b(similar|aise aur|asech)\b|ऐसे और|असेच", re.I)
WHATSAPP_RX = re.compile(r"^\W*continue on whatsapp\W*$", re.I)
_RENT_AMT = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|hazaar|hazar|hajar)?\b", re.I)

PROMPTS = {
    "tx": (say("ask_tx"), ["Buy", "Rent", "Just exploring"]),
    "locality": (say("ask_locality"), ["Kharadi", "Upper Kharadi", "Wagholi", "Somewhere else"]),
    "bhk": (say("ask_bhk"), ["1 BHK", "2 BHK", "3 BHK", "4 BHK"]),
    "budget": (say("ask_budget"), ["Under 50 lakh", "50-80 lakh", "80 lakh to 1.2 crore", "1.2 to 2 crore", "Above 2 crore"]),
    "timeline": (say("ask_timeline"), ["Right now", "In 1-3 months", "In 3-6 months", "Just looking"]),
    "name": (say("ask_name"), []),
    "phone": (f"{say('ask_phone')} {CONSENT}", ["Not now"]),
}
RENT_BUDGET_QUICK = ["Under 20,000/month", "20,000-35,000/month", "Above 35,000/month"]

# words that end a name ('I am Rahul and ...') or show the phrase was not a name at all ('I am looking for ...')
NOT_NAME = set("""a an the and or but so i im am is are was me my mine you your we our looking interested searching planning trying going here
there from in at on of for to with new just only also very not no yes ok okay fine good great thanks thank sure hi hello hey namaste buying
renting selling buyer seller agent owner broker investor family working moving relocating shifting coming staying living hai hoon hu hun
aur ka ki ke se mein mai main bhi ji sir madam please pls want need would like ready free available currently still bhk lakh crore rent
buy budget flat home house property apartment kharadi wagholi pune baner hinjewadi viman nagar upper this that it urgent serious sorry
confused busy happy back done fine okay calling asking writing""".split())
NAME_TRIGGER = re.compile(r"(?:\bmy name is|\bmy name's|\bi am|\bi'm|\bim|\bthis is|\bmera naam|\bmaza nav|\bmaze nav|\bmajhe nav|\bmaza naav|\bnaam)\s+(.+)", re.I)


def new_data(localise: bool = False) -> dict:
    return {"tx": None, "locality": None, "bhk": None, "budget_min": None, "budget_max": None, "timeline": None, "financing": None,
            "name": None, "phone": None, "pending_phone": None, "consent_shown": False, "declined": [], "asked": None,
            "lead_done": False, "questions": [], "needs_human": False, "greeted": False, "missing": [],
            # v2
            "localise": localise, "lang": "en", "turn_no": 0, "asks": {}, "phone_asks": 0, "phone_snooze_until": 0, "after_lead": False,
            "name_uses": 0, "value_given": False, "shown_sig": None, "shown_ids": [], "needs_you_sent": False, "phone_asked_turn": 0, "locality_src": None, "bhk_src": None,
            "page": None}


def _upgrade(d: dict) -> dict:
    """Sessions stored before v2 lack the new keys."""
    for k, v in new_data().items():
        d.setdefault(k, v if not isinstance(v, (list, dict)) else type(v)())
    return d


@dataclass
class Turn:
    reply: str
    quick: List[str] = field(default_factory=list)
    lead: Optional[dict] = None       # set once, when a phone number has been confirmed with consent
    needs_human: bool = False
    cards: List[dict] = field(default_factory=list)
    notify_needs_you: bool = False    # the first time this chat needs a person: the caller alerts the agent


Finder = Callable[[dict, Optional[str]], Awaitable[List[dict]]]


def filled(d: dict, f: str) -> bool:
    if f == "budget":
        return d["budget_min"] is not None or d["budget_max"] is not None
    return bool(d.get(f))


def _exhausted(d: dict, f: str) -> bool:
    return f in d["declined"] or d.get("asks", {}).get(f, 0) >= MAX_ASKS


def next_field(d: dict) -> Optional[str]:
    return next((f for f in ORDER if f != "phone" and not filled(d, f) and not _exhausted(d, f)), None) or \
        ("phone" if not filled(d, "phone") and "phone" not in d["declined"] else None)


def _phone_in(text: str) -> Optional[str]:
    m = PHONE_RX.search(text)
    if not m:
        return None
    try:
        return normalize_indian_mobile(m.group(0))
    except Exception:
        return None


def _clean_name(words: List[str]) -> Optional[str]:
    out = []
    for w in words[:4]:
        w = w.strip(".,!'-")
        if not w or w.lower() in NOT_NAME or not re.fullmatch(r"[A-Za-z][A-Za-z'-]{1,20}", w):
            break
        out.append(w)
    if not out or len(out) > 3:
        return None
    return " ".join(x[:1].upper() + x[1:].lower() for x in out)


def _name_in(text: str, asked: Optional[str]) -> Optional[str]:
    """A name offered ('I am Rahul', 'mera naam Rahul hai', 'maza nav Rahul') or a short reply right after we asked for it."""
    t = text.strip()
    if PHONE_RX.search(t) or "?" in t:
        return None
    m = NAME_TRIGGER.search(t)
    if m:
        return _clean_name(re.split(r"[\s,]+", m.group(1).strip()))
    if asked == "name" and not NO.match(t) and not GREETING.match(t) and not YES.match(t):
        words = re.split(r"[\s,]+", t)
        if 1 <= len(words) <= 3 and all(re.fullmatch(r"[A-Za-z][A-Za-z.'-]{1,20}", w) for w in words):
            if words[-1].lower() in ("here", "this", "side"):
                words = words[:-1]
            name = _clean_name(words)
            return name if name and len(name.split()) == len(words) else None
    return None


def _rent_budget(text: str) -> Optional[tuple]:
    """'25k per month', '20,000-35,000/month', 'under 30000 rent' -> (min, max) in rupees per month."""
    low = text.lower().replace("₹", " ").replace("rs.", " ").replace("rs ", " ")
    vals = []
    for m in _RENT_AMT.finditer(low):
        n = float(m.group(1).replace(",", ""))
        n = n * 1000 if m.group(2) else n
        if 3_000 <= n <= 500_000:
            vals.append(int(n))
    if not vals:
        return None
    if len(vals) >= 2:
        return min(vals[:2]), max(vals[:2])
    if re.search(r"\b(above|over|more than|min|at least|from)\b", low):
        return vals[0], None
    return None, vals[0]


def _lakh_budget(text: str) -> bool:
    return bool(re.search(r"\d\s*(lakhs?|lacs?|lks|lkh|crores?|cr|l)\b|लाख|करोड", text, re.I))


def extract(d: dict, text: str) -> List[str]:
    """Update `d` from the visitor's message. Returns the fields that were newly filled."""
    before = {f: filled(d, f) for f in ORDER}
    t, low, asked = text.strip(), text.strip().lower(), d["asked"]

    if YES.match(t) and d["pending_phone"]:
        d["phone"], d["pending_phone"] = d["pending_phone"], None
    elif NO.match(t) and d["pending_phone"]:
        d["pending_phone"] = None
        _snooze_phone(d)
    elif NO.match(t) and asked in ("phone", None):
        _snooze_phone(d)
    elif NO.match(t) and asked and asked not in d["declined"] and not filled(d, asked):
        d["declined"].append(asked)

    found = rq.infer_from_message(t)
    if not d["tx"]:
        if RENT_WORDS.search(low):
            d["tx"] = "rent"
        elif BUY_WORDS.search(low) or (asked == "tx" and low == "buy"):
            d["tx"] = "buy"
        elif ("budget_min_inr" in found or "budget_max_inr" in found) and _lakh_budget(t):
            d["tx"] = "buy"  # a budget in lakh or crore is a purchase budget
        elif asked == "tx" and re.search(r"exploring|just looking|browsing", low):
            d["tx"] = "exploring"

    # a statement ('actually 3 BHK', 'make it Wagholi') replaces what we had; a question ('is the metro in Wagholi?') only fills a gap
    stating = not is_question(t)
    if found.get("localities"):
        if not d["locality"] or (stating and found["localities"][0] != d["locality"]):
            d["locality"], d["locality_src"] = found["localities"][0], "buyer"
    budget = None
    if d["tx"] == "rent" and (RENT_WORDS.search(low) or asked == "budget") and not _lakh_budget(t):
        budget = _rent_budget(t)
    elif "budget_min_inr" in found or "budget_max_inr" in found:
        budget = (found.get("budget_min_inr"), found.get("budget_max_inr"))
    if budget and (not filled(d, "budget") or stating):
        d["budget_min"], d["budget_max"] = budget
    if found.get("bhk") and d["bhk"] and found["bhk"] != d["bhk"] and (stating or d.get("bhk_src") == "page"):
        d["bhk"], d["bhk_src"] = None, "buyer"
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
        d["locality_src"] = "buyer"
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
    newly = [f for f in ORDER if filled(d, f) and not before[f]]
    if asked and asked != "phone" and not filled(d, asked) and newly and not is_question(t):
        # they told us something else instead (their name, another detail): move on rather than ask the same thing twice in a row
        d.setdefault("asks", {})[asked] = MAX_ASKS
    return newly


def _snooze_phone(d: dict) -> None:
    d["phone_snooze_until"] = d.get("turn_no", 0) + SNOOZE_TURNS + 1


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
    b = _budget_text(d)
    if b:
        bits.append(f"budget {b}")
    if d["timeline"]:
        bits.append(f"timeline {d['timeline'].replace('_', '-')}")
    text = ", ".join(bits) + "."
    if d["questions"]:
        text += " Asked: " + " | ".join(q[:120] for q in d["questions"][-2:])
    return text[:900]


def _budget_text(d: dict, lang: str = "en") -> Optional[str]:
    """'under 80L', '50L-80L', 'under 25,000/month' (and the same in the buyer's language for acknowledgements)."""
    lo, hi = d["budget_min"], d["budget_max"]
    if lo is None and hi is None:
        return None
    rent = d.get("tx") == "rent" and (lo or hi or 0) < rq.LAKH * 5
    f = (lambda n: f"{n:,}") if rent else rq.fmt_inr  # noqa: E731
    if hi is not None and not lo:
        txt = ack_word("under", lang, x=f(hi))
    elif lo is not None and hi is None:
        txt = ack_word("above", lang, x=f(lo))
    else:
        txt = f(lo) if lo == hi else f"{f(lo)}-{f(hi)}"
    return txt + ("/month" if rent else "")


def _ack(new: List[str], d: dict) -> str:
    bits = []
    lang = _lang(d)
    if "tx" in new and d["tx"] in ("buy", "rent"):
        bits.append(ack_word(d["tx"], lang))
    if "locality" in new:
        bits.append(d["locality"])
    if "bhk" in new:
        bits.append(rq.bhk_text(d["bhk"]) or "")
    if "budget" in new:
        bits.append(_budget_text(d, lang) or "")
    if "timeline" in new and d["timeline"] in phrases.ACK:
        bits.append(ack_word(d["timeline"], lang))
    bits = [b for b in bits if b]
    return (say("got_it", lang) + ", ".join(bits) + ".") if bits else ""


def _lang(d: dict) -> str:
    return (d.get("lang") or "en") if d.get("localise") else "en"


def _update_lang(d: dict, text: str) -> None:
    """Keep the conversation's language across short answers ('2 BHK', 'Kharadi'): switch only on a non-English message, or on a clearly
    English sentence of four words or more."""
    if not d.get("localise"):
        return
    found = detect_language(text)
    if found != "en":
        d["lang"] = found
    elif len((text or "").split()) >= 4 and not PHONE_RX.search(text or ""):
        d["lang"] = "en"


def _first_name(d: dict) -> str:
    return (d.get("name") or "").split()[0] if d.get("name") else ""


def _use_name(d: dict) -> str:
    """The buyer's first name at most MAX_NAME_USES times per conversation (warm, not every message)."""
    if not d.get("name") or d.get("name_uses", 0) >= MAX_NAME_USES:
        return ""
    d["name_uses"] = d.get("name_uses", 0) + 1
    return _first_name(d)


def _can_ask_phone(d: dict) -> bool:
    return (not d["phone"] and not d["pending_phone"] and not d["lead_done"] and "phone" not in d["declined"]
            and d.get("phone_asks", 0) < MAX_PHONE_ASKS and d.get("turn_no", 0) >= d.get("phone_snooze_until", 0)
            and (not d.get("phone_asks") or d.get("turn_no", 0) >= d.get("phone_asked_turn", 0) + PHONE_GAP_TURNS))


def _phone_ask(d: dict) -> tuple:
    lang = _lang(d)
    d["phone_asks"] = d.get("phone_asks", 0) + 1
    d["phone_asked_turn"] = d.get("turn_no", 0)
    d["asked"] = "phone"
    if not d["consent_shown"]:
        d["consent_shown"] = True
        return f"{say('ask_phone', lang)} {say('consent', lang)}", [qr("not_now", lang)]
    return say("ask_phone_again", lang), [qr("not_now", lang)]


def _prompt(d: dict, f: str) -> tuple:
    lang = _lang(d)
    d.setdefault("asks", {})[f] = d.get("asks", {}).get(f, 0) + 1
    d["asked"] = f
    text = say("ask_" + f, lang)
    q = list(PROMPTS[f][1])
    if f == "budget" and d.get("tx") == "rent":
        q = list(RENT_BUDGET_QUICK)
    return text, q


def _req_complete(d: dict) -> bool:
    """Area, BHK and budget each known (or the buyer skipped it), and at least one known."""
    keys = ("locality", "bhk", "budget")
    return all(filled(d, f) or _exhausted(d, f) for f in keys) and any(filled(d, f) for f in keys)


def _sig(d: dict) -> list:
    return [d["tx"], d["locality"], d["bhk"], d["budget_min"], d["budget_max"]]


def requirement(d: dict) -> dict:
    """The finder's input, in tracking.matching's shape."""
    return {"bhk": d["bhk"], "budget_min_inr": d["budget_min"], "budget_max_inr": d["budget_max"],
            "localities": [d["locality"]] if d["locality"] and d["locality"] != "Other" else [],
            "transaction": "rent" if d["tx"] == "rent" else "sale"}


def _home_text(page: dict, lang: str) -> str:
    bhk = rq.bhk_text(page.get("bhk")) or "home"
    loc = page.get("locality") or ""
    area = f"{int(page['carpet_sqft']):,} sq ft" if page.get("carpet_sqft") else ""
    if lang == "en":
        return ", ".join(x for x in (f"{bhk} in {loc}" if loc else bhk, area) if x)
    return f"{loc + ' ' if loc else ''}{bhk}{' (' + area + ')' if area else ''}"


def _greeting(d: dict, whatsapp: bool) -> tuple:
    lang, page = _lang(d), d.get("page") or {}
    if page.get("kind") == "listing":
        if page.get("transaction") in ("sale", "rent") and not d["tx"]:
            d["tx"] = "rent" if page["transaction"] == "rent" else "buy"
        # the home's area and size are a soft starting point (the buyer naming others replaces them), so we never ask 'which area?' here
        if page.get("locality") and not d["locality"]:
            d["locality"], d["locality_src"] = page["locality"], "page"
        if page.get("bhk") and not d["bhk"]:
            d["bhk"], d["bhk_src"] = page["bhk"], "page"
        key = "greet_sample" if page.get("sample") else "greet_listing"
        q = [qr("about_it", lang), qr("similar", lang)] + ([WHATSAPP] if whatsapp else [])
        d["asked"] = None
        return say(key, lang, home=_home_text(page, lang)), q
    if page.get("kind") == "area" and page.get("locality"):
        if not d["locality"]:
            d["locality"], d["locality_src"] = page["locality"], "page"
        nf = next_field(d) or "tx"
        p, q = _prompt(d, nf)
        return f"{say('greet_area', lang, area=page['locality'])} {p}", q
    nf = next_field(d) or "tx"
    p, q = _prompt(d, nf)
    return f"{say('greet', lang)} {p}", q


def _about(g) -> Optional[str]:
    """A short description of the home from its vetted facts (the first few sentences: what, where, price, size)."""
    if g is None or not getattr(g, "facts", None):
        return None
    skip = re.compile(r"^(It is located in |Because it is a sample)")
    picked = [f for f in g.facts if not skip.match(f)][:4]
    return " ".join(picked) or None


async def _show_homes(d: dict, finder: Optional[Finder], force: bool) -> tuple:
    """-> (text, cards, shown). Calls the finder at most once per requirement (or when the buyer asks)."""
    if finder is None:
        return "", [], False
    sig = _sig(d)
    if force and not any(filled(d, f) for f in ("locality", "bhk", "budget")):
        return "", [], False
    if not force and (d.get("shown_sig") == sig or not _req_complete(d)):
        return "", [], False
    exclude = (d.get("page") or {}).get("listing_id")
    cards = (await finder(requirement(d), exclude))[:3]
    d["shown_sig"], d["value_given"] = sig, True
    lang = _lang(d)
    if not cards:
        d["want_phone_now"] = True
        return say("no_match", lang), [], True
    d["shown_ids"] = list(dict.fromkeys((d.get("shown_ids") or []) + [c.get("id") for c in cards if c.get("id")]))[-12:]
    samples = [c for c in cards if c.get("sample")]
    if len(samples) == len(cards):
        return say("cards_samples", lang), cards, True
    head = say("cards", lang, n=len(cards)) if len(cards) > 1 else say("cards_one", lang)
    return (head + (" " + say("sample_note", lang) if samples else "")), cards, True


async def turn(d: dict, text: str, llm, grounding=None, finder: Optional[Finder] = None, whatsapp: bool = False) -> Turn:
    """`grounding` (knowledge.Grounding) is what we know about the home, post or area the visitor is looking at; questions about it are answered
    from it, and what it does not cover is said plainly and handed to a person. `finder(requirement, exclude_listing_id)` returns up to three
    home cards from the agent's live listings (None: no homes are shown, e.g. on WhatsApp). `whatsapp` offers 'Continue on WhatsApp'."""
    _upgrade(d)
    text = (text or "").strip()
    first = not d["greeted"]
    d["greeted"] = True
    d["turn_no"] = d.get("turn_no", 0) + 1
    _update_lang(d, text)
    lang = _lang(d)
    if ABUSE.search(text):
        return Turn(say("abuse", lang), needs_human=True)
    if first and GREETING.match(text):
        reply, q = _greeting(d, whatsapp)
        return Turn(reply, q)

    had_name = bool(d["name"])
    was_needed = bool(d["needs_human"])
    asked_before = d["asked"]
    new = extract(d, text)
    lang = _lang(d)
    parts: List[str] = []
    quick: List[str] = []
    cards: List[dict] = []
    lead = None
    needs_human = False
    force_homes = bool(HOMES.search(text))

    if WHATSAPP_RX.match(text):
        parts.append(say("anything_else", lang))
        return Turn(" ".join(parts), [WHATSAPP] if whatsapp else [])
    if HUMAN.search(text):
        d["needs_human"] = needs_human = True
        parts.append(say("team_takes", lang))
    if force_homes and SIMILAR.search(text):
        page = d.get("page") or {}
        if page.get("kind") == "listing":  # 'similar homes' on a listing: its area and BHK, unless the buyer said otherwise
            if not d["locality"] and page.get("locality"):
                d["locality"], d["locality_src"] = page["locality"], "page"
            if not d["bhk"] and page.get("bhk"):
                d["bhk"] = page["bhk"]
    # 'ready' or 'Kharadi' typed straight after we asked about timeline or area is the answer to that, not a question about the home
    short_reply = bool(d["asked"]) and len(text.split()) <= 3 and "?" not in text and set(topics_in(text)) <= {"possession", "price", "location", "size"}
    if grounding is not None and ABOUT.match(text) and _about(grounding):
        parts.append(_about(grounding))
        d["value_given"] = True
    elif force_homes:
        pass
    elif grounding is not None and has_topic(text) and not short_reply and (is_question(text) or len(text.split()) <= 6):
        d["questions"].append(text[:200])
        r = await grounded_answer(text, grounding, "chat", llm)
        parts.append(r.text)
        d["value_given"] = True
        if not r.confident:
            d["needs_human"] = needs_human = True
            d.setdefault("missing", []).append((r.missing or "")[:100])
    elif is_question(text) and not (d["asked"] and not kb.search(text, 1) and len(text.split()) <= 3):
        d["questions"].append(text[:200])
        ans = await answer(text, llm)
        if ans:
            parts.append(ans)
            d["value_given"] = True
        else:
            d["needs_human"] = needs_human = True
            parts.append(say("dont_guess", lang))
    ack = _ack(new, d)
    if ack and not parts:
        parts.append(ack)
    if d["name"] and not had_name:
        parts.insert(0, say("thanks_name", lang, name=_use_name(d) or _first_name(d)))
    if NO.match(text) and asked_before in ("phone", None) and not parts:
        parts.append(say("not_now_ok", lang))
    notify = bool(d["needs_human"]) and not was_needed and not d.get("needs_you_sent")
    if notify:
        d["needs_you_sent"] = True

    if "phone" in new and not d["lead_done"]:
        d["lead_done"] = d["after_lead"] = True
        d["asked"] = None
        lead = {"name": d["name"] or "Website visitor", "phone": d["phone"], "message": summary(d), "bhk": d["bhk"],
                "budget_min_inr": d["budget_min"] if d["tx"] != "rent" else None, "budget_max_inr": d["budget_max"] if d["tx"] != "rent" else None,
                "timeline": d["timeline"], "financing": d["financing"]}
        name = _use_name(d)
        parts.append(say("thanks_lead", lang, name=(", " + name) if name else ""))
        return Turn(" ".join(parts), [WHATSAPP] if whatsapp else [], lead, needs_human, [], notify)

    if d["pending_phone"]:
        p = d["pending_phone"]
        d["consent_shown"] = True
        d["asked"] = "phone"
        parts.append(f"{say('confirm_phone', lang, last4=p[-4:])} {say('consent', lang)}")
        return Turn(" ".join(parts), ["Yes", "No"], None, needs_human, [], notify)

    homes_text, cards, shown = await _show_homes(d, finder, force_homes)
    if homes_text:
        parts.append(homes_text)

    if d["after_lead"]:
        d["asked"] = None
        if not shown:
            parts.append(say("anything_else", lang))
        quick = [WHATSAPP] if whatsapp and (shown or needs_human) else []
        return Turn(" ".join(p for p in parts if p), quick, None, needs_human, cards, notify)

    want_phone = (needs_human or d.pop("want_phone_now", False)) and _can_ask_phone(d)
    nf = None if want_phone else next_field(d)
    if nf == "phone" and not _can_ask_phone(d):
        nf = None
    if want_phone or nf == "phone":
        prompt, quick = _phone_ask(d)
        parts.append(prompt)
    elif nf:
        prompt, quick = _prompt(d, nf)
        parts.append(prompt)
    else:
        d["asked"] = None
        if not shown:
            parts.append(say("anything_else", lang))
    if whatsapp and (shown or needs_human) and WHATSAPP not in quick:
        quick = quick + [WHATSAPP]
    return Turn(" ".join(p for p in parts if p), quick, None, needs_human, cards, notify)
