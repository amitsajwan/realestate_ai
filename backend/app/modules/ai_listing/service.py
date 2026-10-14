"""Orchestrates transcription, deterministic + LLM extraction, merge, copy generation -> AIDraft.

From the agent's words only: a builder's brochure is stored with the listing but never read (owner, 2026-10-14: PDF reading
is heavy). A MahaRERA number or project name they give is matched in our register (register.py), and each field says where
it came from (`sources`)."""
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from . import copywriter as copy
from . import register as reg
from .extractor import extract
from .llm import LLMClient, LLM_TIMEOUT, Transcriber, TranscriptionError
from .about import about_from_text
from .merge import merge, sanitise_llm
from .schemas import REQUIRED_TO_PUBLISH, AIDraft, Extraction
from .plausibility import build_warnings

log = logging.getLogger(__name__)

class TranscriberUnavailable(Exception):
    pass


@dataclass
class AudioInput:
    data: bytes
    filename: str
    content_type: str
    language: Optional[str] = None


async def _guard(coro):
    """Any LLM failure or timeout -> None (silent fallback to deterministic)."""
    try:
        return await asyncio.wait_for(coro, LLM_TIMEOUT + 0.5)
    except Exception as e:
        log.info("ai_listing LLM unavailable: %s", type(e).__name__)
        return None


async def project_group(register: Any, rera_no: Optional[str], project_name: Optional[str]) -> Optional[dict]:
    """The marketed project (agentprojects.groups) a registration number is a member of, or (with no number) its name means:
    "Lodha Camelot" is "Kharadi New Project - Tower 1".. on MahaRERA. Read from the register's database; never raises."""
    db = getattr(register, "db", None)
    if db is None:
        return None
    rera = (rera_no or "").strip().upper()
    try:
        from app.modules.agentprojects.groups import Groups
        return await Groups(db).resolve(rera, "" if rera else (project_name or ""))
    except Exception as e:
        log.info("ai_listing project group lookup failed: %s", type(e).__name__)
        return None


def _group_picks(group: dict) -> list:
    """The group's registrations as one-tap picks (same shape as reg.match_register's candidates)."""
    return [{"regno": r["regno"], "name": " ".join(x for x in (group["name"], r.get("tower", ""),
                                                              f"({r['holds']})" if r.get("holds") else "") if x),
             "taluka": ""} for r in group["registrations"]]


class AIListingService:
    def __init__(self, llm: Optional[LLMClient] = None, transcriber: Optional[Transcriber] = None):
        self.llm, self.transcriber = llm, transcriber

    async def create_draft(self, text: Optional[str] = None, audio: Optional[AudioInput] = None,
                           image_count: int = 0, city_hint: Optional[str] = None, register: Any = None) -> AIDraft:
        warnings: list[str] = []
        transcript: Optional[str] = None
        if audio is not None:
            if self.transcriber is None:
                raise TranscriberUnavailable("Voice input is not configured (no speech-to-text key).")
            try:
                transcript = await self.transcriber.transcribe(audio.data, audio.filename, audio.content_type, audio.language)
            except TranscriptionError:
                if not (text or "").strip():
                    raise  # voice was the only input: the caller tells the agent to type instead
                warnings.append("Your voice note could not be turned into text right now, so only the typed details were used.")
                transcript = None
            if audio is not None and transcript is not None and not transcript:
                warnings.append("No speech could be recognised in the audio.")
        combined = "\n".join(p for p in ((text or "").strip(), transcript or "") if p)
        return await self.from_text(combined, image_count, city_hint, transcript, warnings, register=register)

    async def from_text(self, text: str, image_count: int = 0, city_hint: Optional[str] = None,
                        transcript: Optional[str] = None, warnings: Optional[list[str]] = None, register: Any = None) -> AIDraft:
        city_hint = (city_hint or "").strip()[:60] or None
        det, _ = extract(text, city_hint)
        llm_ex = Extraction()
        llm_up = self.llm is not None
        if self.llm is not None and text.strip():
            raw = await _guard(self.llm.extract(text, city_hint))
            llm_up = raw is not None  # if the text AI just failed or timed out, do not make the agent wait for a second call
            llm_ex = sanitise_llm(raw)
        merged = merge(det, llm_ex)
        facts, conf = dict(merged.values), dict(merged.confidence)
        if reg.same_place(facts.get("locality"), facts.get("project_name")):  # a project's name is not its locality
            facts.pop("locality", None)
            conf.pop("locality", None)
        if facts.get("rera_no") and not reg.RERA.fullmatch(str(facts["rera_no"])):  # a gat/survey number is land
            facts.pop("rera_no")
            conf.pop("rera_no", None)
        sources = {k: "agent" for k in facts}
        rera_candidates: list = []
        maharera = None
        by_name = facts.get("project_name")
        if register is not None and (facts.get("rera_no") or by_name):
            m = await reg.match_register(register, facts.get("rera_no"), by_name)
            rera_candidates = m["candidates"]
            if m["record"]:
                maharera = reg.register_fields(m["record"])
                for k, v in (("rera_no", maharera.get("regno")), ("locality", maharera.get("locality")),
                             ("project_name", maharera.get("name"))):
                    if v and (k != "project_name" or not facts.get(k)):
                        facts[k], conf[k], sources[k] = v, 0.95, "maharera"
            group = await project_group(register, facts.get("rera_no"), by_name)
            if group and group["regno"] and group["regno"] == facts.get("rera_no"):
                # a member tower: the project is sold under the group's name and place, not MahaRERA's working name
                for k, v in (("project_name", group["name"]), ("locality", group["locality"])):
                    if v:
                        facts[k], conf[k], sources[k] = v, 0.95, "maharera"
            elif group and not facts.get("rera_no"):
                rera_candidates = _group_picks(group)  # the marketed name alone: pick the tower, never guessed

        draft: dict = dict(facts)
        title = copy.make_title(facts)
        en = copy.make_description_en(facts)
        if title:
            draft["title"] = title
        if en:
            desc = {"en": en}
            if self.llm is not None and llm_up:
                tr = await _guard(self.llm.translate(facts, en))
                if isinstance(tr, dict):
                    desc.update({k: v for k, v in tr.items() if k in ("hi", "mr") and isinstance(v, str) and v.strip()})
            draft["description"] = desc
        about = await about_from_text(text, self.llm if llm_up else None)
        about.pop("project_name", None)  # already a top-level draft field
        if about:
            draft["about"] = about

        present = set(draft) - {"description", "about"} | ({"description.en"} if en else set())
        missing = [k for k in REQUIRED_TO_PUBLISH if k not in present]
        return AIDraft(draft=draft, confidence={k: round(v, 2) for k, v in conf.items()}, missing=missing,
                       transcript=transcript, warnings=(warnings or []) + build_warnings(facts, conf),
                       sources={k: v for k, v in sources.items() if k in draft}, rera_candidates=rera_candidates,
                       maharera=maharera)
