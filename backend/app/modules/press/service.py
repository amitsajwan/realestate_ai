"""Press agent service: builds the month's story, finds journalists and drafts their pitches, and the owner's status
changes on a pitch. CLAUDE.md rule 6: no AI agent ever publishes or sends; nothing here calls a mail client or an SMTP
library, and no draft leaves `status: draft` except by the owner's own `update_pitch` call."""
import logging
from datetime import datetime
from typing import Optional

from app.platform.llm import gemini_llm

from . import draft as draft_mod
from . import outlets
from .config import Config, load
from .facts import build_story
from .store import Store

log = logging.getLogger(__name__)


async def monthly_run(db, now: datetime, cfg: Optional[Config] = None, search=None, fetch=None, llm=None) -> dict:
    """This month's story and pitches, stored. Returns a short summary for the loop's log and the health row."""
    cfg = cfg or load()
    store = Store(db)
    story = await build_story(db, now)
    await store.save_story(story["month"], story["facts"], story["headline_facts"], now)
    if not story["headline_facts"]:
        log.info("press: no headline facts this month, no journalists searched")
        return {"month": story["month"], "facts": len(story["facts"]), "pitches": 0, "pruned": 0}
    journalists = await outlets.find_journalists(cfg, now, search=search, fetch=fetch)
    model = llm if llm is not None else gemini_llm()
    month_label = now.strftime("%B %Y")
    saved = 0
    for j in journalists:
        d = await draft_mod.draft_pitch(model, j, story["headline_facts"], month_label, cfg)
        await store.save_pitch(story["month"], j, d, now)
        saved += 1
    pruned = await store.prune_old(now, cfg.pitch_ttl_days)
    log.info("press: %s, %d journalists found, %d pruned", story["month"], saved, pruned)
    return {"month": story["month"], "facts": len(story["facts"]), "pitches": saved, "pruned": pruned}


class PitchError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


STATUSES = ("draft", "sent", "skipped")


async def set_status(db, pitch_id: str, status: str, now: datetime) -> dict:
    if status not in STATUSES:
        raise PitchError(f"unknown status {status!r}")
    store = Store(db)
    if await store.pitch(pitch_id) is None:
        raise PitchError("no such pitch", 404)
    return await store.update_pitch(pitch_id, status=status, status_at=now)


async def set_reply(db, pitch_id: str, replied: bool, now: datetime) -> dict:
    store = Store(db)
    if await store.pitch(pitch_id) is None:
        raise PitchError("no such pitch", 404)
    return await store.update_pitch(pitch_id, replied=replied, replied_at=now if replied else None)


async def set_link(db, pitch_id: str, url: Optional[str], now: datetime) -> dict:
    store = Store(db)
    if await store.pitch(pitch_id) is None:
        raise PitchError("no such pitch", 404)
    return await store.update_pitch(pitch_id, link_won_url=url or None, link_won_at=now if url else None)


async def edit_draft(db, pitch_id: str, subject: Optional[str], body: Optional[str]) -> dict:
    store = Store(db)
    doc = await store.pitch(pitch_id)
    if doc is None:
        raise PitchError("no such pitch", 404)
    fields = {}
    if subject is not None:
        fields["subject"] = subject
    if body is not None:
        fields["body"] = body
    return await store.update_pitch(pitch_id, **fields) if fields else doc
