"""POST /ai/draft (mounted under /listings): typed and/or spoken text -> AIDraft. Persists nothing."""
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth_backend import current_active_user
from app.models.user import User

from .llm import LLMClient, Transcriber, TranscriptionError, default_listing_llm, default_transcriber
from .about import suggest_about
from .schemas import AIDraft
from .service import AIListingService, AudioInput, TranscriberUnavailable

router = APIRouter()

MAX_AUDIO_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARS = 6000
MAX_IMAGES = 50
ALLOWED_AUDIO = {
    "audio/webm", "video/webm", "audio/ogg", "video/ogg", "application/ogg", "audio/opus", "audio/mpeg",
    "audio/mp3", "audio/mp4", "audio/m4a", "audio/x-m4a", "audio/wav", "audio/x-wav", "audio/wave", "audio/vnd.wave",
}
ALLOWED_EXT = {".webm", ".ogg", ".oga", ".opus", ".mp3", ".m4a", ".mp4", ".wav"}


def voice_enabled() -> bool:
    """Voice listings are a Premium feature: off unless VOICE_LISTINGS_ENABLED=true (read per request)."""
    return (os.environ.get("VOICE_LISTINGS_ENABLED") or "").strip().lower() in ("1", "true", "yes", "on")


def get_llm() -> Optional[LLMClient]:
    return default_listing_llm()


def get_transcriber() -> Optional[Transcriber]:
    return default_transcriber()


async def _read_audio(f: UploadFile, language: Optional[str]) -> AudioInput:
    ctype = (f.content_type or "").split(";")[0].strip().lower()
    ext = os.path.splitext(f.filename or "")[1].lower()
    if ctype not in ALLOWED_AUDIO and not (ctype in ("", "application/octet-stream") and ext in ALLOWED_EXT):
        raise HTTPException(status_code=415, detail="Unsupported audio type; use webm, ogg, mp3, m4a or wav.")
    data = bytearray()
    while chunk := await f.read(1024 * 1024):
        data += chunk
        if len(data) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Audio file too large (max 10 MB).")
    if not data:
        raise HTTPException(status_code=400, detail="Audio file is empty.")
    return AudioInput(bytes(data), f.filename or "audio" + (ext or ".webm"), ctype or "application/octet-stream",
                      (language or "").strip()[:8] or None)


@router.post("/ai/draft", response_model=AIDraft)
async def ai_draft(
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    image_count: int = Form(0),
    city_hint: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    user: User = Depends(current_active_user),
    llm: Optional[LLMClient] = Depends(get_llm),
    transcriber: Optional[Transcriber] = Depends(get_transcriber),
):
    if text and len(text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail=f"Text too long (max {MAX_TEXT_CHARS} characters).")
    has_audio = audio is not None and audio.filename != ""
    if has_audio and not voice_enabled():
        raise HTTPException(status_code=403, detail="Voice listings are a Premium feature. You can still type the details.")
    audio_in = await _read_audio(audio, language) if has_audio else None
    svc = AIListingService(llm=llm, transcriber=transcriber)
    try:
        return await svc.create_draft(text=text, audio=audio_in, image_count=max(0, min(image_count, MAX_IMAGES)),
                                      city_hint=city_hint)
    except TranscriberUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e) + " You can still send the details as text.")
    except TranscriptionError:
        raise HTTPException(status_code=502, detail="Voice could not be turned into text right now. Please type the details instead.")


class AboutSuggestRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    locality: Optional[str] = Field(None, max_length=120)
    project_name: Optional[str] = Field(None, max_length=120)
    bhk: Optional[float] = Field(None, ge=0.5, le=20)
    description: str = Field("", max_length=MAX_TEXT_CHARS)


@router.post("/ai/about-suggest")
async def ai_about_suggest(body: AboutSuggestRequest, user: User = Depends(current_active_user),
                           llm: Optional[LLMClient] = Depends(get_llm)):
    """DRAFT `about` for the agent to confirm. Agent lines come from their own words (source 'agent'); connectivity and
    nearby offices only from curated area facts (source 'area_guide'). Persists nothing."""
    return await suggest_about(body.locality, body.project_name, body.bhk, body.description, llm)
