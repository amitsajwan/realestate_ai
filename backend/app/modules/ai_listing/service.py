"""Orchestrates transcription, deterministic + LLM extraction, merge, copy generation -> AIDraft."""
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from . import copywriter as copy
from .extractor import extract
from .llm import LLMClient, LLM_TIMEOUT, Transcriber, TranscriptionError
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


class AIListingService:
    def __init__(self, llm: Optional[LLMClient] = None, transcriber: Optional[Transcriber] = None):
        self.llm, self.transcriber = llm, transcriber

    async def create_draft(self, text: Optional[str] = None, audio: Optional[AudioInput] = None,
                           image_count: int = 0, city_hint: Optional[str] = None) -> AIDraft:
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
        return await self.from_text(combined, image_count, city_hint, transcript, warnings)

    async def from_text(self, text: str, image_count: int = 0, city_hint: Optional[str] = None,
                        transcript: Optional[str] = None, warnings: Optional[list[str]] = None) -> AIDraft:
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

        present = set(draft) - {"description"} | ({"description.en"} if en else set())
        missing = [k for k in REQUIRED_TO_PUBLISH if k not in present]
        return AIDraft(draft=draft, confidence={k: round(v, 2) for k, v in conf.items()}, missing=missing,
                       transcript=transcript, warnings=(warnings or []) + build_warnings(facts, conf))
