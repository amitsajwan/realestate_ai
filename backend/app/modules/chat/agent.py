"""The website chat as an LLM sales assistant: the model reads the conversation and writes the reply; our code keeps the facts and the rules.

One turn, when an LLM is configured:
  1. understand: the model reads the buyer's message with the conversation so far and returns what they told us (area, BHK, budget, timeline,
     name...) and what they want (a question, 'you suggest', a skip, homes, a visit, a person). Every value is checked against the message.
  2. homes: the agent's live listings that fit (engine._show_homes, the same finder and matching as before).
  3. reply: the model writes the answer from our vetted knowledge (knowledge/site.py, the area's facts, the page's facts, and the passages a
     search of everything we publish finds: knowledge/vectors.py) and the homes found,
     then the one next question our code chose. The reply is checked before it goes out: no number, price or name that our data does not
     contain, no phone, link, hype or prediction.

Kept in code, never left to the model: the number (asked only when engine._can_ask_phone allows, with the consent line added here), confirming a
number, the lead, abuse, the first greeting. Any failure (no LLM, a provider down, a reply that fails the checks) falls back to the rules engine
(engine.turn) for that turn, on the state as it was, so the chat never breaks.
"""
import copy
import logging
import re
from typing import List, Optional

from app.core import areas as area_registry
from app.core import brand
from app.modules.engage.brain import ABUSE
from app.modules.knowledge import areas as area_kb
from app.modules.knowledge import site, vectors
from app.modules.knowledge.reply import LANG_NAME, _facts_block, _nums, valid_text
from app.modules.tracking import requirement as rq

from . import engine
from .phrases import say

log = logging.getLogger(__name__)

MAX_REPLY = 600
HISTORY_TURNS = 12
INTENTS = ("answer", "question", "suggest", "skip", "homes", "visit", "human", "agent", "chat")
TIMELINES = ("now", "1_3_months", "3_6_months", "exploring")
FINANCING = ("home_loan", "own_funds", "undecided")
FIELD_WORDS = {"tx": "whether they want to buy or rent", "locality": "which area of Pune", "bhk": "how many bedrooms (BHK)",
               "budget": "their budget", "timeline": "when they plan to move", "name": "their name"}
AREA_NAMES = sorted({a.name for a in area_registry.AREAS})

UNDERSTAND = f"""You read one message from a visitor in the {brand.NAME} website chat (a Pune real estate agent's site) and say what it means.
Use the conversation so far to understand short replies: "you tell", "not sure", "10 years", "no name" answer the assistant's last question.

Return ONE JSON object:
{{"intent": one of {list(INTENTS)},
  "tx": "buy" | "rent" | "exploring" | null,
  "locality": the Pune area they name, as written | null,
  "bhk": number of bedrooms as a number (2, 2.5, 3) | null,
  "budget_min_inr": rupees as an integer | null, "budget_max_inr": rupees as an integer | null,
  "timeline": {" | ".join(f'"{t}"' for t in TIMELINES)} | null,
  "financing": {" | ".join(f'"{t}"' for t in FINANCING)} | null,
  "name": their own name exactly as they typed it | null,
  "declined": the detail they will not give ("budget", "timeline", "name", "locality", "bhk", "phone") | null}}

intent:
- answer: they answered the question (fully or partly)
- question: they ask something (about a home, an area, prices, buying, the process)
- suggest: they do not know or want us to propose ("not sure", "you tell", "how much will I get?", "what is the price there?")
- skip: they will not answer this one ("no name", "don't want to say", "skip")
- homes: they want to see homes or options
- visit: they want to see a home or fix a site visit
- human: they want a person, a call, the agent
- agent: they are a real estate agent or ask about {brand.NAME}'s service for agents
- chat: greetings, thanks, anything else

Fill a field ONLY with what the visitor says in THIS message (null for everything else; never copy from the conversation).
Money: 80 lakh = 8000000, 1.2 crore = 12000000, 25k = 25000. "under 80 lakh" -> max only; "80 lakh to 1 crore" -> both; "around 1 crore" -> min 9000000, max 11000000.
timeline: "now/asap/this month", "ready possession", "ready to move", "ready flat" -> now (and intent answer); within 3 months -> 1_3_months; 4-6 months -> 3_6_months; later than 6 months, a year or more, "just looking" -> exploring.
Never guess a name: "no name", "why", "sir" are not names."""

REPLY = f"""You are the {brand.NAME} assistant in the chat on a Pune real estate agent's website. You talk like a good local property advisor:
warm, short, honest, helpful before anything else, never pushy. You work for the agent: your aim is to understand what the buyer needs, show
them fitting homes, and when the moment is right get their number so the agent can help.

How to reply:
1. First respond to what they just said. Answer a question from KNOWLEDGE or HOMES. If they do not know their budget or ask what homes cost,
   tell them what the HOMES cost. If they skip a question, accept it lightly ("No problem") and move on. If they gave a detail, do not repeat
   it back word by word.
2. Use ONLY what KNOWLEDGE, HOMES and BUYER contain. Never invent or estimate prices, price trends, rates per sq ft, distances, travel times,
   schools, hospitals, malls, amenities, possession dates, approvals or availability. Prices come only from HOMES. If you cannot answer from
   them, say honestly that you do not have that and the agent will confirm it, and set "needs_team": true.
   We find and show homes; we do not give home loans, legal work, discounts, offers or anything KNOWLEDGE does not describe: never offer,
   promise or say we can arrange one (for a loan: the buyer's bank decides; the agent can tell them which banks the project works with).
3. HOMES are shown as cards right under your message: point to them ("the home below", "these two"), do not list every detail again.
   A home marked SAMPLE is an illustration, never for sale. Do not repeat a price or detail you already said in CONVERSATION unless asked.
4. Put the next step in "question": exactly the one thing NEXT asks for, in your own natural words, or "" when NEXT is none. "reply"
   itself contains no question. Never ask anything else, never ask again for something in BUYER or something they skipped.
5. Write in {{lang}}. 1 to 3 short sentences in "reply" (under 300 characters), "question" one short sentence. No links, phone numbers,
   emojis, or words like best, perfect, dream, guaranteed, luxurious; no predictions.

Return ONE JSON object: {{"reply": "...", "question": "...", "needs_team": true | false}}"""


def _plain(v) -> str:
    """Model typography to plain text: narrow and no-break spaces, non-breaking hyphens, curly quotes."""
    t = str(v or "").translate(str.maketrans({" ": " ", " ": " ", "‑": "-", "‐": "-", "’": "'", "‘": "'"}))
    return " ".join(t.split())


def _rules_only(d: dict, text: str) -> bool:
    """Turns the rules handle better than a model: the first hello, abuse, anything about the phone number, 'Continue on WhatsApp'."""
    return bool((not d.get("greeted") and engine.GREETING.match(text)) or ABUSE.search(text) or engine.PHONE_RX.search(text)
                or d.get("pending_phone") or engine.WHATSAPP_RX.match(text)
                or (d.get("asked") == "phone" and (engine.YES.match(text) or engine.NO.match(text))))


async def turn(d: dict, text: str, llm, grounding=None, finder: Optional[engine.Finder] = None, whatsapp: bool = False,
               history: Optional[List[dict]] = None) -> engine.Turn:
    engine._upgrade(d)
    text = (text or "").strip()
    if llm is None or not hasattr(llm, "json") or _rules_only(d, text):
        return await engine.turn(d, text, llm, grounding, finder, whatsapp)
    work = copy.deepcopy(d)
    try:
        t = await _turn(work, text, llm, grounding, finder, whatsapp, history or [])
    except Exception:
        log.exception("chat agent turn failed, the rules answer")
        t = None
    if t is None:
        return await engine.turn(d, text, llm, grounding, finder, whatsapp)
    d.clear()
    d.update(work)
    return t


# ---- 1. understand ---------------------------------------------------------------------------------------------------------------------

def _history_text(history: List[dict]) -> str:
    lines = []
    for m in history[-HISTORY_TURNS:]:
        who = "Visitor" if m.get("role") == "user" else "Assistant"
        lines.append(f"{who}: {(m.get('text') or '')[:400]}")
    return "\n".join(lines) or "(this is the first message)"


def _buyer_text(d: dict) -> str:
    bits = []
    if d.get("tx"):
        bits.append(f"wants to: {d['tx']}")
    if d.get("locality"):
        bits.append(f"area: {d['locality']}")
    if d.get("bhk"):
        bits.append(f"size: {rq.bhk_text(d['bhk'])}")
    b = engine._budget_text(d)
    if b:
        bits.append(f"budget: {b}")
    if d.get("timeline"):
        bits.append(f"moving: {rq.TIMELINE_LABEL.get(d['timeline'], d['timeline'])}")
    if d.get("financing"):
        bits.append(f"financing: {d['financing'].replace('_', ' ')}")
    if d.get("name"):
        bits.append(f"name: {d['name']}")
    if d.get("phone"):
        bits.append("has shared their number (the agent will contact them)")
    if d.get("visit_wanted"):
        bits.append("wants a site visit")
    skipped = [f for f in engine.ORDER if f in d.get("declined", []) or (engine._exhausted(d, f) and not engine.filled(d, f))]
    if skipped:
        bits.append("did not give (do not ask again): " + ", ".join(skipped))
    return "; ".join(bits) or "nothing yet"


def _int(v) -> Optional[int]:
    try:
        n = int(float(v))
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _apply(d: dict, u: dict, text: str, rules_new: List[str]) -> None:
    """Take what the model read from the message, each value checked against the message itself (the rules' own finds win)."""
    low = text.lower()
    if u.get("tx") in ("buy", "rent", "exploring") and "tx" not in rules_new:
        if not d.get("tx") or u["tx"] != "exploring":
            d["tx"] = u["tx"]
    loc = u.get("locality")
    if isinstance(loc, str) and loc.strip() and "locality" not in rules_new:
        loc = " ".join(loc.split())
        known = area_kb.area_facts(loc)
        if known or loc.lower() in low:
            d["locality"], d["locality_src"] = (known.name if known else loc.title()), "buyer"
    bhk = u.get("bhk")
    if isinstance(bhk, (int, float)) and 0.5 <= bhk <= 10 and "bhk" not in rules_new and re.search(r"\d|one|two|three|four|five|ek|do|teen|char", low):
        d["bhk"], d["bhk_src"] = float(bhk), "buyer"
    lo, hi = _int(u.get("budget_min_inr")), _int(u.get("budget_max_inr"))
    if (lo or hi) and "budget" not in rules_new and re.search(r"\d", text):
        if all(3_000 <= n <= 1_000_000_000 for n in (lo, hi) if n) and (not lo or not hi or lo <= hi):
            d["budget_min"], d["budget_max"] = lo, hi
    if u.get("timeline") in TIMELINES and "timeline" not in rules_new:
        d["timeline"] = u["timeline"]
    if u.get("financing") in FINANCING and not d.get("financing"):
        d["financing"] = u["financing"]
    name = u.get("name")
    if isinstance(name, str) and not d.get("name") and name.strip() and name.strip().lower() in low:
        clean = engine._clean_name(name.split())
        if clean and len(clean.split()) == len(name.split()):
            d["name"] = clean
    dec = u.get("declined")
    if dec in engine.ORDER and not engine.filled(d, dec):
        if dec == "phone":
            engine._snooze_phone(d)
        elif dec not in d["declined"]:
            d["declined"].append(dec)


# ---- 2 + 3. homes and the reply --------------------------------------------------------------------------------------------------------

SEARCH_INTENTS = ("question", "suggest", "agent", "chat")
PASSAGES = 6


async def _found(d: dict, text: str, intent: str) -> List[vectors.Passage]:
    """Passages from everything we publish (knowledge/index.py) that may answer this message; [] when the search is off or fails.
    site.ENTRIES are already given whole, so their passages are left out."""
    if intent not in SEARCH_INTENTS or len(text.split()) < 2:
        return []
    q = text if not d.get("locality") or d["locality"].lower() in text.lower() else f"{text} ({d['locality']})"
    return [p for p in await vectors.search(q, PASSAGES + 2) if p.kind != "site"][:PASSAGES]


def _knowledge(d: dict, grounding, found: Optional[List[vectors.Passage]] = None) -> str:
    out = ["About us and buying in Pune:"]
    out += [f"- {e.answer}" for e in site.ENTRIES]
    af = area_kb.area_facts(d.get("locality"))
    if af:
        out.append(f"About {af.name}:")
        out += [f"- {f}" for f in af.facts]
        out += [f"- Q: {q} A: {a}" for q, a in af.faq]
    if grounding is not None:
        out.append("The page the visitor is looking at:")
        out.append(_facts_block(grounding))
    out.append("Areas we cover: " + ", ".join(AREA_NAMES))
    return "\n".join(out)


def _homes_text(cards: List[dict], searched: bool, d: dict) -> str:
    if not cards:
        if searched:
            return f"No listed home matches right now ({engine._budget_text(d) or 'any budget'}). The agent can look for more."
        return "(none shown this turn)"
    lines = []
    for i, c in enumerate(cards, 1):
        facts = [c.get("title") or "Home"]
        if c.get("carpet_sqft"):
            facts.append(f"{int(c['carpet_sqft']):,} sq ft carpet")
        facts.append("SAMPLE, an illustration, not for sale" if c.get("sample") else (f"price {c['price_text']}" if c.get("price_text") else "price on request"))
        lines.append(f"{i}. " + ", ".join(facts))
    return "\n".join(lines)


def _next(d: dict, intent: str, needs_human: bool) -> str:
    """The one next step, chosen by code: a missing detail in order, or the number when it is allowed and useful."""
    if d.get("after_lead") or intent == "agent":
        return "none"
    want_phone = needs_human or d.get("want_phone_now") or intent in ("visit", "human")
    nf = engine.next_field(d)
    if (want_phone or nf == "phone") and engine._can_ask_phone(d) and d.get("value_given"):
        return "phone"
    if intent == "visit" and not d.get("phone") and d.get("phone_asks", 0) < engine.MAX_PHONE_ASKS and "phone" not in d["declined"]:
        return "phone"   # a visit needs a number: the warmest moment to ask, even soon after the last ask
    if nf and nf != "phone":
        return nf
    return "none"


def _next_text(nxt: str, d: dict) -> str:
    if nxt == "none":
        return "none (offer help, ask nothing)"
    if nxt == "phone":
        why = "so the agent can arrange the visit" if d.get("visit_wanted") else \
            "so the agent can send new matching homes when they come up" if d.get("timeline") == "exploring" else \
            "so the agent can send matching options and answer what you could not"
        return f"ask if they would like to share their mobile number, {why} (optional; do not write a consent sentence, it is added)"
    return f"ask {FIELD_WORDS[nxt]}"


async def _turn(d: dict, text: str, llm, grounding, finder, whatsapp: bool, history: List[dict]) -> Optional[engine.Turn]:
    d["greeted"] = True
    d["turn_no"] = d.get("turn_no", 0) + 1
    engine._update_lang(d, text)
    lang = engine._lang(d)
    was_needed = bool(d.get("needs_human"))
    asked_before = d.get("asked")

    rules_new = engine.extract(d, text)   # exact for what it catches ('3 BHK', '80 lakh', a name after 'my name is')
    d.pop("price_hint", None)
    d.pop("skipped", None)
    u = await llm.json(UNDERSTAND, f"ASSISTANT'S LAST QUESTION: {FIELD_WORDS.get(asked_before or '', asked_before or 'none')}\n"
                                   f"WHAT WE KNOW: {_buyer_text(d)}\nCONVERSATION:\n{_history_text(history)}\n\nMESSAGE:\n{text[:500]}")
    if not isinstance(u, dict) or u.get("intent") not in INTENTS:
        return None
    intent = u["intent"]
    _apply(d, u, text, rules_new)
    if asked_before and asked_before != "phone" and not engine.filled(d, asked_before) and intent in ("suggest", "skip", "chat", "question"):
        d.setdefault("asks", {})[asked_before] = engine.MAX_ASKS   # never the same question twice in a row
    if intent == "question":
        d["questions"].append(text[:200])
    needs_human = intent == "human"
    if intent == "visit" and not d.get("lead_done"):
        d["visit_wanted"] = d["value_given"] = True
        d["want_phone_now"] = True

    same = d.get("shown_sig") == engine._sig(d) and d.get("shown_brief")
    force = (intent == "homes" or bool(engine.HOMES.search(text))) or (intent == "suggest" and not same)
    _, cards, shown = await engine._show_homes(d, finder, force)
    if cards:
        d["shown_brief"] = _homes_text(cards, True, d)
    if intent in ("question", "suggest"):
        d["value_given"] = True

    nxt = _next(d, intent, needs_human)
    knowledge = _knowledge(d, grounding, await _found(d, text, intent))
    homes = _homes_text(cards, shown, d) if cards or shown or not d.get("shown_brief") else \
        "No cards this turn (say 'the home I showed you', never 'below'). Shown earlier in the chat:\n" + d["shown_brief"]
    buyer = _buyer_text(d)
    user = (f"KNOWLEDGE:\n{knowledge}\n\nHOMES (shown under your message):\n{homes}\n\nBUYER: {buyer}\n\nNEXT: {_next_text(nxt, d)}\n\n"
            f"CONVERSATION:\n{_history_text(history)}\n\nVISITOR NOW: {text[:500]}")
    r = await llm.json(REPLY.replace("{lang}", LANG_NAME.get(lang, "English")), user)
    if not isinstance(r, dict):
        return None
    reply, question = _plain(r.get("reply")), _plain(r.get("question"))
    # the visitor's own words count as a source here (a 1:1 chat may say back '10 years' or '80 lakh'); phones and links are still refused
    source = " ".join([knowledge, homes, buyer, brand.NAME, " ".join(AREA_NAMES), text])
    for part, limit in ((reply, MAX_REPLY), (question, 300)):
        if part and not valid_text(part, source, "chat", limit):
            log.info("chat agent reply failed the checks (numbers not in our data: %s): %r", sorted(_nums(part) - _nums(source)), part[:300])
            return None
    if question:  # the model sometimes asks in the reply too: the question is said once, at the end
        reply = " ".join(x for x in re.split(r"(?<=[.!?।])\s+", reply) if not x.rstrip().endswith("?")).strip() or reply
    if not reply:
        return None
    if nxt == "none":
        question = ""
    if r.get("needs_team") is True:
        needs_human = True
        d.setdefault("missing", []).append(text[:100])
        d["gaps"] = (d.get("gaps") or [])[-19:] + [{"q": text[:200], "topics": ["other"]}]
    if needs_human:
        d["needs_human"] = True
    notify = bool(d.get("needs_human")) and not was_needed and not d.get("needs_you_sent")
    if notify:
        d["needs_you_sent"] = True

    quick: List[str] = []
    if nxt == "phone" and question:
        first = not d.get("consent_shown")
        _, quick = engine._phone_ask(d)          # counts the ask, shows consent once
        d.pop("want_phone_now", None)
        if first:
            question = f"{question} {say('consent', lang)}"
    elif nxt not in ("none", "phone") and question:
        _, quick = engine._prompt(d, nxt)        # counts the ask; its quick replies
    else:
        d["asked"] = None
    if whatsapp and (shown or needs_human) and engine.WHATSAPP not in quick:
        quick = quick + [engine.WHATSAPP]
    if cards and question:
        return engine.Turn(reply, quick, None, needs_human, cards, notify, question)
    return engine.Turn(" ".join(x for x in (reply, question) if x), quick, None, needs_human, cards, notify)
