"""Layer 2, the copywriter: Angle -> Copy (cover hook, slide texts, caption with a strong first line, body, question CTA, hashtags).

Channel rules are enforced in code: Instagram captions carry no URL (the caption() helper says "link in our bio") and 3 to 8
hashtags; Facebook may link. Slides are at most 14 words, one idea each. Every number must appear in the brief's facts and the
HYPE / PHONE guards run on every field; a field that fails is replaced by its deterministic draft, so the result is always clean.
English first; Hinglish and Marathi caption variants only when asked and only with an LLM.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Sequence

from .guards import filler_hits, problems_in, tidy, word_count
from .models import Angle, Brief, Copy

log = logging.getLogger(__name__)

SLIDE_MAX_WORDS = 14
FIRST_LINE_MAX = 125      # what Instagram shows before "more"
BODY_MAX = 900
SIGN_OFF = "PUNE Property team"
TAG = re.compile(r"^#[A-Za-z][A-Za-z0-9_]{2,30}$")

BUYER_TAGS = ["#PuneProperty", "#Kharadi", "#HomeBuyingTips", "#PuneRealEstate", "#UpperKharadi", "#Wagholi", "#FirstHomeBuyer"]
AGENT_TAGS = ["#PuneRealEstate", "#RealEstateAgent", "#PropertyAgentIndia", "#LeadGeneration", "#PuneProperty", "#RealEstateMarketing"]

QUESTION = {
    "stat": "How many did you do before you booked? Tell us below.",
    "myth-vs-fact": "Did you believe this one? Tell us below.",
    "poll": "Your pick? Tell us in the comments.",
    "before-after": "Which side does your paperwork look like? Tell us below.",
    "checklist": "Which one would you check first? Tell us below.",
    "carousel": "Which one surprised you most? Tell us below.",
    "single": "What would you add? Tell us below.",
}
QUESTION_AGENT = {
    "poll": "Your pick? Tell us in the comments.",
    "myth-vs-fact": "Which side are you on? Tell us below.",
    "before-after": "Which column is your week? Tell us below.",
}
AGENT_DEFAULT_Q = "How do you follow up on comments today? Tell us below."
INTRO = {
    "stat": "One number worth remembering.", "myth-vs-fact": "A belief that costs people time and money.",
    "poll": "Two honest options. Pick one.", "before-after": "The same job, done two ways.",
    "checklist": "Save this list.", "carousel": "Swipe through. One idea per slide.", "single": "",
}
CARD_CTA = {"stat": "Save this", "myth-vs-fact": "Share with a buyer", "poll": "Vote in the comments", "before-after": "Save this",
            "checklist": "Save this list", "carousel": "Swipe", "single": "Save this"}

SYSTEM = (
    "You are the copywriter of PUNE Property, an Indian real-estate brand (home buyers and property agents in Kharadi, "
    "Upper Kharadi and Wagholi, Pune). Write the post copy for the given angle.\n"
    "Rules: plain, warm, direct English; brand voice 'PUNE Property team'. Use ONLY the supplied facts: no prices, no "
    "predictions, no invented numbers or claims, no phone numbers, no personal or builder names, no superlatives (best, "
    "perfect, dream, guaranteed). Avoid filler such as 'in today's world', 'unlock', 'game changer'. Each slide is at most "
    "14 words and carries ONE idea. The caption's first line is the only line visible before 'more': make it concrete and "
    "curious, at most 120 characters. The caption never contains a URL or a phone number. End with a question to the reader.\n"
    'Reply with ONE JSON object: {"support": str (one line, at most 14 words, may be empty), "slides": [str] (3 to 5, only '
    'when the format is carousel or checklist), "first_line": str, "body": str (2 to 4 short lines), "question": str, '
    '"hashtags": [str] (3 to 6, each starting with #)}'
)
VARIANT_SYSTEM = (
    "You translate a social-media caption for an Indian real-estate brand. Keep every number and fact exactly; add nothing; "
    "no prices, phone numbers, URLs or superlatives. Keep it short and natural, the way a Pune agent would speak. "
    "Output ONLY the caption text."
)
VARIANT_LANG = {"hinglish": "Hinglish (Hindi written in Roman letters, mixed with English)", "marathi": "Marathi (Devanagari script)"}


KICKER = {"stat": "WORTH REMEMBERING", "myth-vs-fact": "MYTH VS FACT", "poll": "THIS OR THAT", "before-after": "SIDE BY SIDE",
          "checklist": "SAVE THIS", "carousel": "SWIPE THROUGH", "single": "BUYER NOTE"}


def _payload(brief: Brief, angle: Angle) -> Dict[str, object]:
    f = angle.fmt
    kicker = "FOR AGENTS" if angle.audience == "agent" and f == "single" else KICKER.get(f, "PUNE PROPERTY")
    base: Dict[str, object] = {"kicker": kicker, "audience": angle.audience, "fmt": f}
    if f == "stat":
        base.update(value=brief.stat_value, label=brief.stat_label)
    elif f == "myth-vs-fact":
        base.update(myth=brief.myth, truth=brief.truth)
    elif f == "poll":
        base.update(question=brief.question, options=list(brief.options))
    elif f == "before-after":
        base.update(messy=list(brief.messy[:4]), clean=list(brief.clean[:4]), compare=list(brief.compare))
    elif f in ("carousel", "checklist"):
        base.update(steps=list(brief.steps[:5]))
    else:
        base.update(tip=brief.tip)
    return base


def _tags(brief: Brief, audience: str, channel: str) -> List[str]:
    tags = [t if t.startswith("#") else "#" + t for t in brief.hashtags] or list(AGENT_TAGS if audience == "agent" else BUYER_TAGS)
    tags = [t for t in dict.fromkeys(tags) if TAG.match(t)]
    return tags[:6] if channel == "instagram" else tags[:3]


def _first_line(angle: Angle) -> str:
    h = angle.hook.strip()
    if angle.pattern == "question" and not h.endswith("?"):
        h += "?"
    elif h[-1] not in ".?!:”\"'":
        h += "."
    return h


def _support(brief: Brief, angle: Angle) -> str:
    cands = []
    if angle.fmt == "stat":
        cands = [brief.tip, *brief.facts]
    elif angle.fmt in ("single",):
        cands = [brief.tip, *brief.facts]
    elif angle.fmt == "myth-vs-fact":
        cands = []
    for c in cands:
        if c and word_count(c) <= SLIDE_MAX_WORDS and c.strip().lower() != angle.hook.strip().lower():
            return c.strip()
    return ""


def _body(brief: Brief, angle: Angle) -> str:
    lines = []
    intro = INTRO.get(angle.fmt, "")
    if intro:
        lines.append(intro)
    if angle.fmt == "myth-vs-fact":
        lines += [f"Myth: {brief.myth.rstrip('.')}.", f"Fact: {brief.truth.rstrip('.')}."]
    elif angle.fmt in ("carousel", "checklist"):
        lines += [f"{i}. {s.rstrip('.')}" for i, s in enumerate(brief.steps[:5], 1)]
    elif angle.fmt == "before-after":
        lines += [f"Messy: {'; '.join(x.rstrip('.') for x in brief.messy[:3])}.", f"Clean: {'; '.join(x.rstrip('.') for x in brief.clean[:3])}."]
    elif angle.fmt == "poll":
        lines += [f"A: {brief.options[0]}", f"B: {brief.options[1]}"]
    else:
        lines += [f"• {p}" for p in angle.proof[:3]]
    lines.append(f"- {SIGN_OFF}")
    return "\n".join(lines)


def rule_copy(angle: Angle, brief: Brief) -> Copy:
    audience_q = QUESTION_AGENT if angle.audience == "agent" else QUESTION
    q = audience_q.get(angle.fmt) or (AGENT_DEFAULT_Q if angle.audience == "agent" else QUESTION[angle.fmt])
    cta = "Comment INTERESTED" if angle.audience == "agent" else CARD_CTA.get(angle.fmt, "Save this")
    if brief.cta:
        cta = brief.cta
    if angle.audience == "agent":
        q = f"{q} Or comment INTERESTED to see how it works." if angle.fmt not in ("poll",) else q
    return Copy(hook=angle.hook, support=_support(brief, angle),
                slides=list(brief.steps[:5]) if angle.fmt in ("carousel", "checklist") else [],
                caption_first_line=_first_line(angle), body=_body(brief, angle), cta_question=q,
                hashtags=_tags(brief, angle.audience, angle.channel), card_cta=cta,
                payload=_payload(brief, angle), source="rules")


def build_user(angle: Angle, brief: Brief, feedback: Optional[str]) -> str:
    lines = [f"Audience: {angle.audience}. Channel: {angle.channel}. Format: {angle.fmt}.",
             f"Audience pain or desire: {angle.pain}", f"The one idea: {angle.idea}", f"Hook (keep it as the cover line): {angle.hook}",
             "Facts you may use:", *[f"- {f}" for f in (brief.facts or angle.proof)]]
    if angle.fmt in ("carousel", "checklist"):
        lines += ["Slide material (one idea per slide, rewrite tighter if you can, keep the facts):", *[f"- {s}" for s in brief.steps[:5]]]
    lines.append(f"Call to action: {angle.cta}")
    if angle.channel == "instagram":
        lines.append("Instagram: no URLs at all. 3 to 6 hashtags.")
    if feedback:
        lines.append(f"A reviewer rejected the last attempt: {feedback}. Fix that.")
    return "\n".join(lines)


def _clean_str(v: Any, corpus: str, max_words: Optional[int] = None, max_chars: Optional[int] = None) -> Optional[str]:
    if not isinstance(v, str) or not v.strip():
        return None
    s = tidy(v).strip()
    if max_words and word_count(s) > max_words:
        return None
    if max_chars and len(s) > max_chars:
        return None
    return None if problems_in(s, corpus) else s


async def write(angle: Angle, brief: Brief, llm: Any = None, languages: Sequence[str] = (), feedback: Optional[str] = None) -> Copy:
    base = rule_copy(angle, brief)
    corpus = brief.corpus()
    copy = base
    if llm is not None:
        try:
            data = await llm.json(SYSTEM, build_user(angle, brief, feedback))
        except Exception:
            log.warning("copywriter LLM failed; using rules", exc_info=True)
            data = None
        if isinstance(data, dict):
            copy = _merge(base, data, angle, corpus)
    if llm is not None and languages:
        for lang in languages:
            v = await _variant(llm, lang, copy, corpus)
            if v:
                copy.variants[lang] = v
    return copy


def _merge(base: Copy, data: dict, angle: Angle, corpus: str) -> Copy:
    support = _clean_str(data.get("support"), corpus, SLIDE_MAX_WORDS) if data.get("support") else None
    slides = base.slides
    raw = data.get("slides")
    if angle.fmt in ("carousel", "checklist") and isinstance(raw, list) and 3 <= len(raw) <= 5:
        cleaned = [_clean_str(s, corpus, SLIDE_MAX_WORDS) for s in raw]
        if all(cleaned):
            slides = cleaned  # type: ignore[assignment]
    first = _clean_str(data.get("first_line"), corpus, max_chars=FIRST_LINE_MAX)
    body = _clean_str(data.get("body"), corpus, max_chars=BODY_MAX)
    if body and SIGN_OFF not in body:
        body = f"{body}\n- {SIGN_OFF}"
    question = _clean_str(data.get("question"), corpus, max_chars=140)
    if question and "?" not in question and "comment" not in question.lower():
        question = None
    tags = [t for t in (data.get("hashtags") or []) if isinstance(t, str) and TAG.match(t.strip())] if isinstance(data.get("hashtags"), list) else []
    lo = 3
    tags = list(dict.fromkeys(t.strip() for t in tags))
    tags = tags[:6] if angle.channel == "instagram" else tags[:3]
    llm_used = any([support, first, body, question, slides is not base.slides])
    return Copy(hook=base.hook, support=support if support is not None else base.support, slides=slides,
                caption_first_line=first or base.caption_first_line, body=body or base.body,
                cta_question=question or base.cta_question, hashtags=tags if len(tags) >= lo else base.hashtags,
                card_cta=base.card_cta, payload=base.payload, source="llm" if llm_used else "rules")


async def _variant(llm: Any, lang: str, copy: Copy, corpus: str) -> Optional[str]:
    if lang not in VARIANT_LANG:
        return None
    src = "\n\n".join(p for p in (copy.caption_first_line, copy.body, copy.cta_question) if p)
    try:
        out = await llm.text(VARIANT_SYSTEM, f"Language: {VARIANT_LANG[lang]}\n\nCAPTION:\n{src}")
    except Exception:
        return None
    if not out or len(out) > 1200:
        return None
    from .guards import HYPE, PHONE, URL, unsupported_numbers
    if PHONE.search(out) or HYPE.search(out) or URL.search(out) or unsupported_numbers(out, corpus):
        return None
    return out.strip() + "\n\n" + " ".join(copy.hashtags)


def review_copy(copy: Copy, corpus: str, channel: str) -> List[str]:
    """Every reason the copy breaks a rule (empty list = good). Used by the critic."""
    out: List[str] = []
    fields = {"hook": copy.hook, "support": copy.support, "first line": copy.caption_first_line, "body": copy.body,
              "question": copy.cta_question, **{f"slide {i + 1}": s for i, s in enumerate(copy.slides)}}
    for name, text in fields.items():
        if text:
            out += [f"{name}: {p}" for p in problems_in(text, corpus)]
    if len(copy.caption_first_line) > FIRST_LINE_MAX:
        out.append("first line too long for the preview")
    if channel == "instagram" and not 3 <= len(copy.hashtags) <= 8:
        out.append("Instagram needs 3 to 8 hashtags")
    if filler_hits(copy.hook):
        out.append("generic hook")
    return out
