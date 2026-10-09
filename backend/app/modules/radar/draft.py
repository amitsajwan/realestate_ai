"""Step 8: a reply a person can paste (docs/RADAR.md §5): draft -> guard -> critic. Answer first, then one link; never a phone
number, hype or a promise we cannot check.
  - draft: the model writes from verified facts only (the MahaRERA record line, our matching listings, the area), in the asker's
    language; a writer wired in from outside (`configure`) is tried first; the template is the fallback.
  - guard (rules, blocks): `valid`.
  - critic (model, advises): scores helpfulness, "sounds like a person, not an ad" and whether every fact is in FACTS; a low score
    gets one rewrite with its notes. A rewrite that fails the guard is dropped and the first draft stands."""
import logging
import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable, List, Optional

from . import places
from .models import Intent
from .score import Match
from .verify import Project

PHONE = re.compile(r"(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}")
HYPE = re.compile(r"\b(best|guaranteed|hurry|last few|limited offer|lowest|unbelievable|dream home)\b", re.I)
MAX_LEN = 450

log = logging.getLogger(__name__)
DRAFT_VERSION = 3  # bump when the reply wording changes: unsent leads are drafted again (pipeline.redraft)

Writer = Callable[[str, Intent, List[Match], str, Optional[Project]], Awaitable[Optional[str]]]
_writer: Optional[Writer] = None


def configure(writer: Optional[Writer] = None) -> None:
    global _writer
    _writer = writer


def valid(reply: str, link: str) -> bool:
    return bool(reply) and len(reply) <= MAX_LEN and not PHONE.search(reply) and not HYPE.search(reply) and (not link or link in reply)


def template(intent: Intent, matches: List[Match], link: str, project: Optional[Project] = None) -> str:
    """Verify first: the project's MahaRERA record when we know the project, else how to check any project in the area;
    a listing of ours only when nothing is known about the project."""
    hinglish, marathi = intent.language in ("hi", "hinglish"), intent.language == "mr"
    area = places.get(intent.area or "")
    where = area.name if area else "Pune"
    if project:
        if marathi:
            return f"नमस्कार! भेट देण्यापूर्वी {project.name} चा MahaRERA रेकॉर्ड पहा: {project.line}. पूर्ण रेकॉर्ड, लोकेशन आणि किंमत: {link}"
        if hinglish:
            return f"Hi! Visit se pehle {project.name} ka MahaRERA record dekh lo: {project.line}. Poora record, location aur prices: {link}"
        return f"Hi! Before you visit, here is what {project.name}'s MahaRERA record shows: {project.line}. Full record, location and prices: {link}"
    if matches:
        homes = "; ".join(m.line() for m in matches[:2])
        body = (f"Hi! {where} mein abhi yeh available hai: {homes}. Photos, carpet area aur RERA details yahan: {link}"
                if hinglish else f"Hi! In {where} we have {homes} available right now. Photos, carpet area and RERA details: {link}")
    elif marathi:
        body = f"नमस्कार! {where} मधील कोणत्याही प्रोजेक्टचा MahaRERA रेकॉर्ड (ताबा तारीख, किती बुकिंग झाले) भेटीआधी इथे तपासा: {link}"
    elif hinglish:
        body = (f"Hi! Visit se pehle {where} ke kisi bhi project ka MahaRERA record (possession date, kitne book hue) yahan check "
                f"kar lo: {link}")
    else:
        body = (f"Hi! Before you visit, check any {where} project's MahaRERA record (possession date, how many units are "
                f"booked) here: {link}")
    return body


LANG_NAME = {"en": "English", "hi": "Hinglish (Hindi in Latin letters)", "hinglish": "Hinglish (Hindi in Latin letters)",
             "mr": "Marathi (Devanagari)", "other": "English"}
CRITIC_MIN = 0.65

WRITER = """You write one short public reply to a person who asked about a home in Pune, under a YouTube video or a social post.
You are a local property guide, not a salesperson. Rules:
- Reply in {lang}. 1-3 sentences, under 380 characters, plain words, no emojis except at most one.
- First answer what they asked, using ONLY the FACTS. If FACTS do not answer it, say what to check and where.
- Never invent prices, dates, availability, offers or amenities. No hype words (best, guaranteed, hurry, limited, dream home).
- No phone numbers. End with this exact link once: {link}
Return only the reply text."""

CRITIC = """You check a public reply drafted for a home buyer's comment. Return ONLY JSON:
{"helpful": 0-1 (answers what they asked, or says exactly how to find out),
 "human": 0-1 (sounds like a helpful local person, not an ad),
 "grounded": true|false (every number, date and claim appears in FACTS),
 "language_ok": true|false (written in the asker's language),
 "notes": ["short fix", ...]}"""


RULES: List[str] = []  # learned from the operator's edits (learn.draft_rules), loaded each cycle


def set_rules(rules: List[str]) -> None:
    RULES[:] = list(rules or [])[:5]


@dataclass
class Draft:
    text: str
    origin: str                       # llm | rewrite | writer | template
    critic: Optional[dict] = None
    notes: List[str] = field(default_factory=list)


def facts_block(intent: Intent, matches: List[Match], project: Optional[Project]) -> str:
    area = places.get(intent.area or "")
    rows = [f"Area: {area.name}" if area else "Area: not named"]
    if project:
        rows.append(f"Project {project.name}: {project.line}")
    for m in matches[:3]:
        rows.append(f"Our listing: {m.line()} ({m.locality})")
    if not project and not matches:
        rows.append("The link shows any project's MahaRERA record (filed possession date, units booked) and the area's projects.")
    return "\n".join(rows)


def _critic_ok(c: Optional[dict]) -> bool:
    if not c:
        return True  # no critic available: the guard alone decides
    try:
        return bool(c.get("grounded", True)) and bool(c.get("language_ok", True)) and \
            (float(c.get("helpful", 1)) + float(c.get("human", 1))) / 2 >= CRITIC_MIN
    except (TypeError, ValueError):
        return True


async def _critique(llm, comment: str, facts: str, reply: str, lang: str) -> Optional[dict]:
    try:
        return await llm.json(CRITIC, f"ASKER LANGUAGE: {lang}\nCOMMENT: {comment[:500]}\nFACTS:\n{facts}\nREPLY: {reply}")
    except Exception:
        log.exception("radar: critic failed")
        return None


async def _write(llm, comment: str, intent: Intent, facts: str, link: str, notes: List[str] = (), previous: str = "") -> Optional[str]:
    lang = LANG_NAME.get(intent.language, "English")
    user = f"COMMENT: {comment[:600]}\nWHAT THEY WANT: {intent.question or 'unclear'}\nFACTS:\n{facts}"
    if notes:
        user += f"\n\nYOUR LAST DRAFT: {previous}\nFIX THESE: " + "; ".join(str(n)[:120] for n in notes[:4])
    system = WRITER.format(lang=lang, link=link)
    if RULES:
        system += "\nOur team's own rules (from their edits):\n" + "\n".join(f"- {r}" for r in RULES)
    out = await llm.text(system, user)
    out = (out or "").strip().strip('"').strip()
    if out and link not in out:
        out = f"{out.rstrip()} {link}"
    return out or None


async def compose(text: str, intent: Intent, matches: List[Match], link: str, project: Optional[Project] = None,
                  llm=None) -> Draft:
    """The full step 8. Never raises; the template is always there."""
    if _writer is not None:
        try:
            out = await _writer(text, intent, matches, link, project)
            if out and valid(out, link):
                return Draft(out, "writer")
        except Exception:
            log.exception("radar: wired writer failed")
    if llm is not None:
        try:
            facts = facts_block(intent, matches, project)
            first = await _write(llm, text, intent, facts, link)
            if first and valid(first, link):
                lang = LANG_NAME.get(intent.language, "English")
                c = await _critique(llm, text, facts, first, lang)
                if _critic_ok(c):
                    return Draft(first, "llm", c)
                notes = [str(n) for n in (c or {}).get("notes") or []] or ["more helpful, less like an ad"]
                second = await _write(llm, text, intent, facts, link, notes, first)
                if second and valid(second, link):
                    c2 = await _critique(llm, text, facts, second, lang)
                    if _critic_ok(c2):
                        return Draft(second, "rewrite", c2, notes)
                if (c or {}).get("grounded", True):
                    return Draft(first, "llm", c, notes)  # the critic only advises; an ungrounded draft is never used
        except Exception:
            log.exception("radar: model draft failed")
    return Draft(template(intent, matches, link, project), "template")


async def draft(text: str, intent: Intent, matches: List[Match], link: str, project: Optional[Project] = None) -> str:
    return (await compose(text, intent, matches, link, project)).text
