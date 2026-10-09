"""L3: the model reads a comment that passed the rules and says who is asking and what they want (docs/RADAR.md §5).
The answer is checked against `Intent`; one repair retry, then the comment is noise. The model never guesses an area: it must be
named in the comment or its context, and is mapped to our area list here."""
import json
import logging
from typing import Optional, Sequence, Tuple

from pydantic import ValidationError

from . import places
from .models import Intent, RawSignal

log = logging.getLogger(__name__)

AREA_KEYS = ", ".join(places.keys())

SYSTEM = f"""You read public comments under Pune real-estate videos and posts and decide if the writer may want to buy or rent a home or a plot.
Comments can be English, Hindi, Marathi or Hinglish. Return ONLY a JSON object:
{{"role": "buyer|renter|investor|broker|seller|noise",
 "intent": 0.0-1.0 (how likely they want a home soon; 0.9 = asks price/availability/visit for themselves),
 "stage": "exploring|comparing|ready|post_visit|unknown",
 "area": one of [{AREA_KEYS}] or null (only if named in the comment or the context),
 "project": project name if named, else null,
 "property_type": "flat|plot|villa|row_house|shop|office|land" or null (BHK means flat unless the video is about villas),
 "bhk": number or null, "budget_min_inr": integer rupees or null, "budget_max_inr": integer rupees or null,
 "timeline": short text or null,
 "language": "en|hi|mr|hinglish|other",
 "question": what they want to know, one short English line, or null,
 "answered_already": true if the REPLIES already answer them}}
Rules: "60L" = 6000000, "1.2 cr" = 12000000. Brokers advertising their own deals are "broker". Praise, jokes, reviews of the
builder without a home need, and complaints by existing owners are "noise" (intent below 0.2). Never invent facts."""


def _shots(shots: Sequence[Tuple[str, int, str]]) -> str:
    if not shots:
        return ""
    rows = "\n".join(f'- "{t[:160]}" -> ' + (f"home need ({r})" if y else f"not a home need ({r or 'noise'})")
                     for t, y, r in shots)
    return f"LABELLED COMMENTS LIKE THIS ONE (how our team marked them):\n{rows}\n\n"


def _user(sig: RawSignal, shots: Sequence[Tuple[str, int, str]] = ()) -> str:
    replies = "\n".join(f"- {r[:200]}" for r in sig.thread[:5]) or "(none)"
    return (f"{_shots(shots)}CONTEXT (video/post title): {sig.context[:200]}\nAREA OF THIS WATCH: {sig.area_hint or 'unknown'}\n"
            f"COMMENT: {sig.text[:600]}\nREPLIES:\n{replies}")


def _area(intent: Intent, sig: RawSignal) -> Optional[str]:
    if intent.area and places.get(intent.area):
        return places.get(intent.area).key
    named = places.named_in(f"{sig.text} {sig.context}")
    return named.key if named else None


async def classify(sig: RawSignal, llm, shots: Sequence[Tuple[str, int, str]] = ()) -> Optional[Intent]:
    """None when the model is unavailable (the signal waits for the next cycle); an Intent otherwise. `shots` are the most
    similar labelled comments (examples.few_shots)."""
    if llm is None:
        return None
    user = _user(sig, shots)
    for attempt in range(2):
        raw = await llm.json(SYSTEM, user)
        if raw is None:
            return None
        try:
            intent = Intent.model_validate(raw)
            intent.area = _area(intent, sig)
            return intent
        except ValidationError as e:
            log.info("radar: classify output invalid (attempt %s): %s", attempt + 1, str(e)[:200])
            user = f"{_user(sig, shots)}\n\nYour last answer was invalid: {json.dumps(raw)[:300]}\nReturn valid JSON only."
    return Intent(role="noise", intent=0.0)
