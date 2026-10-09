"""Step 8: a reply a person can paste (docs/RADAR.md §5). Answer first, then one link; never a phone number, hype or a promise
we cannot check. A grounded writer from conversations/knowledge can be wired in (`configure`); the template is the fallback."""
import re
from typing import Awaitable, Callable, List, Optional

from app.core import areas

from .models import Intent
from .score import Match

PHONE = re.compile(r"(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}")
HYPE = re.compile(r"\b(best|guaranteed|hurry|last few|limited offer|lowest|unbelievable|dream home)\b", re.I)
MAX_LEN = 450

Writer = Callable[[str, Intent, List[Match], str], Awaitable[Optional[str]]]
_writer: Optional[Writer] = None


def configure(writer: Optional[Writer] = None) -> None:
    global _writer
    _writer = writer


def valid(reply: str, link: str) -> bool:
    return bool(reply) and len(reply) <= MAX_LEN and not PHONE.search(reply) and not HYPE.search(reply) and (not link or link in reply)


def template(intent: Intent, matches: List[Match], link: str) -> str:
    hinglish = intent.language in ("hi", "hinglish")
    area = areas.get(intent.area or "")
    where = area.name if area else "Pune"
    if matches:
        homes = "; ".join(m.line() for m in matches[:2])
        body = (f"Hi! {where} mein abhi yeh available hai: {homes}. Photos, carpet area aur RERA details yahan: {link}"
                if hinglish else f"Hi! In {where} we have {homes} available right now. Photos, carpet area and RERA details: {link}")
    else:
        body = (f"Hi! {where} ke verified homes aur prices yahan dekh sakte ho, aur apna budget bataoge to matching options bhejenge: {link}"
                if hinglish else f"Hi! Verified homes and current prices in {where} are here, and if you share your budget we'll send matching options: {link}")
    return body


async def draft(text: str, intent: Intent, matches: List[Match], link: str) -> str:
    if _writer is not None:
        try:
            out = await _writer(text, intent, matches, link)
            if out and valid(out, link):
                return out
        except Exception:
            pass
    return template(intent, matches, link)
