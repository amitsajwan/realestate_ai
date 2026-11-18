"""The Lead Brief: the deep mind's reading of one lead, for the agent (docs/plan/buyer-mind.md step 3).

The model thinks as a good sales assistant would: who is this, what do they really want, what must I find out, look it up, does
it answer them, is anything wrong they did not ask about, what next. It may only say what the lead card or a lookup says, and
`checked` holds it to that before anyone sees it:
  - the draft reply is dropped (the rest of the brief kept, with the reasons) when it has a number, price, builder name, phone,
    link, hype or prediction the facts do not carry (platform.guards, the same checks as every copy we write);
  - a flag or price idea with a figure no lookup gave is dropped;
  - an alternative whose slug no lookup returned is dropped.
When the model gives nothing usable, `fallback` builds the brief from the card alone, as the lead page shows it today.
Nothing here sends anything: the agent reads the draft, edits it and taps Send (CLAUDE.md rule 6).
"""
from typing import Any, Optional

from app.core import brand
from app.platform import guards

from . import profile

TEMPERATURES = ("hot", "warm", "cold")
CONFIDENCE = ("high", "medium", "low")
MAX_DRAFT = 900
MAX_ITEMS = 5
MAX_TEXT = 300

SYSTEM = f"""You are the {brand.NAME} team's sales assistant for new homes in Pune. A buyer has enquired. Think as an experienced,
honest property adviser would, then prepare a brief for the agent who will call them.

How to think:
1. Understand: who is this buyer, what did they say, and what does it suggest (family, investor, first home, urgency)? Use the
   pages they read and when they wrote.
2. Plan: what must you know before replying? Usually the project they asked about, and whether its possession date, prices and
   homes fit what they said.
3. Look it up with the tools. Look up a project before saying anything about it. Look up an alternative before suggesting it.
4. Reflect: does your answer give them what they asked for? Is there something they did not ask about but must know (possession
   later than they want to move, budget below the published prices, sold out, offices not homes)? Say it kindly and plainly.
5. Decide the next step and write a short reply the agent can send on WhatsApp.

Rules:
- Use only facts from the buyer's card and from your lookups. Never invent a price, date, size, count, name or amenity.
- A price is a range with where and when it was published, and it is indicative, never a quote. No range if no lookup gave one.
- A project's counts and dates are said as the tool gives them (whole project, or one registration named by its number).
- The reply: in the buyer's language (as they wrote), under 120 words, warm and plain, no hype, no prediction of prices rising,
  no phone numbers or links, addressed by first name with "ji" if a name is known, signed "{brand.NAME} team".
- The reply is checked by code and dropped if it has any of: best, perfect, dream, guaranteed, lowest, luxurious, only, just,
  affordable, value, investment, convenient, assured, "your new home", "peace of mind", a ready-to-move claim the facts do not
  make, or a number, price or builder name not in the facts. Write around them.
- If you cannot answer what they asked (for example floor plans we do not have), the reply says the team is getting it.
- If you are not sure, say so in "why" and set confidence low.

Answer with one JSON object and nothing else:
{{"buyer": "one line: who they are and what they want",
 "implied": ["what their words and actions suggest, each a short sentence"],
 "unknown": ["what we still need to ask"],
 "asked_for": "what they asked for", "can_answer": "yes | partly | no",
 "flags": ["problems the agent must know or tell them"],
 "alternatives": [{{"slug": "a slug a lookup returned", "name": "...", "why": "why it fits"}}],
 "price_idea": "a range with its source and date, or null",
 "next_step": "what the agent should do", "when": "today | tomorrow | this week",
 "temperature": "hot | warm | cold",
 "draft": "the reply",
 "why": "two or three sentences: why this reply and next step",
 "confidence": "high | medium | low"}}"""


def user_prompt(card_text: str, project_slug: Optional[str]) -> str:
    where = (f"They enquired on the project page with slug '{project_slug}'." if project_slug
             else "They did not enquire on a project page.")
    return f"The buyer's card:\n{card_text}\n\n{where}\nThink it through, use the tools, then answer with the JSON object."


def _text(v: Any, limit: int = MAX_TEXT) -> Optional[str]:
    s = " ".join(str(v).split())[:limit] if isinstance(v, (str, int, float)) and not isinstance(v, bool) else ""
    return s or None


def _items(v: Any) -> list[str]:
    return [t for t in (_text(x) for x in (v if isinstance(v, list) else [])) if t][:MAX_ITEMS]


def _choice(v: Any, allowed: tuple, default: str) -> str:
    s = str(v or "").strip().lower()
    return s if s in allowed else default


def checked(answer: dict, corpus: str) -> dict:
    """The model's answer, shaped and held to the facts (`corpus`: the card and every lookup's result). `problems` says what was
    dropped and why, for the agent and for us."""
    problems: list[str] = []

    def supported(t: str) -> bool:
        return not guards.unsupported_numbers(t, corpus) and not guards.unsupported_orgs(t, corpus)

    flags = []
    for f in _items(answer.get("flags")):
        if supported(f):
            flags.append(f)
        else:
            problems.append(f"flag dropped, figure or name not in the facts: {f[:80]}")
    price = _text(answer.get("price_idea"))
    if price and price.lower() in ("null", "none", "n/a"):
        price = None
    if price and not supported(price):
        problems.append("price idea dropped: a figure no lookup gave")
        price = None
    alternatives = []
    for a in (answer.get("alternatives") if isinstance(answer.get("alternatives"), list) else [])[:3]:
        slug = _text((a or {}).get("slug"), 120) if isinstance(a, dict) else None
        if slug and f'"{slug}"' in corpus:
            alternatives.append({"slug": slug, "name": _text(a.get("name"), 120), "why": _text(a.get("why"))})
        elif slug:
            problems.append(f"alternative dropped, never looked up: {slug}")
    draft = _text(answer.get("draft"), MAX_DRAFT * 2)
    if draft:
        bad = guards.problems_in(draft, corpus)
        if len(draft) > MAX_DRAFT:
            bad.append("too long")
        if bad:
            problems.append("draft dropped: " + "; ".join(dict.fromkeys(bad)))
            draft = None
    return {
        "buyer": _text(answer.get("buyer")),
        "implied": _items(answer.get("implied")),
        "unknown": _items(answer.get("unknown")),
        "asked_for": _text(answer.get("asked_for")),
        "can_answer": _choice(answer.get("can_answer"), ("yes", "partly", "no"), "partly"),
        "flags": flags,
        "alternatives": alternatives,
        "price_idea": price,
        "next_step": _text(answer.get("next_step")),
        "when": _choice(answer.get("when"), ("today", "tomorrow", "this week"), "today"),
        "temperature": _choice(answer.get("temperature"), TEMPERATURES, "warm"),
        "draft": draft,
        "why": _text(answer.get("why"), 600),
        "confidence": _choice(answer.get("confidence"), CONFIDENCE, "low"),
        "problems": problems,
        "by": "mind",
    }


def fallback(card: dict) -> dict:
    """The brief without the model: the card's facts and gaps, and a call today. The same as the lead page shows now."""
    lines = profile.rows(card)
    wants = lines.get("Wants")
    who = " · ".join(v for v in (lines.get("Home"), lines.get("Budget"), lines.get("Buying when"), lines.get("Areas")) if v)
    return {"buyer": who or None, "implied": [], "unknown": [str(m) for m in card.get("missing") or []],
            "asked_for": wants, "can_answer": "partly", "flags": [], "alternatives": [], "price_idea": None,
            "next_step": "Call them and ask what is not known yet", "when": "today", "temperature": "warm", "draft": None,
            "why": None, "confidence": "low", "problems": [], "by": "rules"}
