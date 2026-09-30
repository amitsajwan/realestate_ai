"""Injectable LLM + speech-to-text clients (Groq). Tests inject fakes; no network is touched by default paths."""
import asyncio
import base64
import json
import logging
import os
import time
from typing import Any, Optional, Protocol

import httpx

log = logging.getLogger(__name__)

# Any OpenAI-compatible provider works: set AI_LLM_BASE_URL + AI_LLM_API_KEY + AI_LISTING_LLM_MODEL.
# Defaults target Groq (its llama-3.1-8b-instant was retired 2026-08-16; free tier serves gpt-oss-120b).
# Examples: Google Gemini  https://generativelanguage.googleapis.com/v1beta/openai  (model gemini-2.5-flash)
#           OpenRouter     https://openrouter.ai/api/v1  (a ":free" model id, e.g. a Qwen or DeepSeek variant)
LLM_BASE_URL = os.environ.get("AI_LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
STT_BASE_URL = os.environ.get("AI_STT_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
GROQ_CHAT_URL = f"{LLM_BASE_URL}/chat/completions"
GROQ_STT_URL = f"{STT_BASE_URL}/audio/transcriptions"
LLM_MODEL = os.environ.get("AI_LISTING_LLM_MODEL", "openai/gpt-oss-120b")
STT_MODEL = os.environ.get("AI_LISTING_STT_MODEL", "whisper-large-v3")
LLM_TIMEOUT = 20.0  # total budget for one text-AI call, all failover attempts included
STT_TIMEOUT = 30.0
STT_BUDGET = 45.0   # total budget for one transcription, all failover attempts included


def groq_api_key() -> Optional[str]:
    key = os.environ.get("AI_LLM_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not key:
        try:
            from app.core.config import settings
            key = getattr(settings, "GROQ_API_KEY", None) or getattr(settings, "groq_api_key", None)
        except Exception:  # settings unavailable -> deterministic only
            key = None
    return key or None


class LLMClient(Protocol):
    async def extract(self, text: str, city_hint: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Return a JSON object with listing fact fields, or None."""

    async def translate(self, facts: dict[str, Any], description_en: str) -> Optional[dict[str, str]]:
        """Return {'hi': ..., 'mr': ...} (either may be missing), or None."""


class TranscriptionError(Exception):
    pass


class Transcriber(Protocol):
    async def transcribe(self, data: bytes, filename: str, content_type: str, language: Optional[str] = None) -> str: ...


_EXTRACT_SYSTEM = (
    "You extract real-estate listing facts from an Indian property agent's message (English, Hindi, Marathi or "
    "Hinglish). Reply with ONE JSON object using only these keys and omit any key you are not sure about: "
    "transaction (sale|rent), property_type (apartment|villa|house|plot|commercial|office|shop), "
    "price_inr (integer rupees; 85 lakh = 8500000, 1.25 crore = 12500000; rent is per month), city, locality, "
    "project_name, bhk (number), carpet_sqft (integer), super_built_up_sqft (integer), floor (integer), "
    "total_floors (integer), furnishing (unfurnished|semi|furnished), possession (ready|under_construction|YYYY-MM), "
    "rera_no, amenities (array of short English names). Never guess or invent values that are not in the message."
)
_TRANSLATE_SYSTEM = (
    "You translate a short real-estate description. Reply with ONE JSON object with keys 'hi' (Hindi, Devanagari) "
    "and 'mr' (Marathi, Devanagari). Translate faithfully: keep every number, price and name exactly; add nothing."
)


FAILOVER_STATUS = (404, 429, 500, 503)  # model retired, daily quota used up, provider error, busy: try the next model


def model_order(spec: str) -> list[str]:
    """'a,b,c' -> tried in that order (free tiers give every model its own daily quota); a single model gets one retry."""
    models = [m.strip() for m in (spec or "").split(",") if m.strip()]
    return models * 2 if len(models) == 1 else models


async def post_with_failover(order: list[str], send, per_attempt: float, budget: float) -> httpx.Response:
    """send(model, timeout) -> Response. Moves to the next model on FAILOVER_STATUS or a timeout/connection error
    (a busy provider can take 20 s just to say 503) and stops when the overall budget is spent."""
    start = time.monotonic()
    r: Optional[httpx.Response] = None
    last_exc: Optional[Exception] = None
    for i, model in enumerate(order):
        remaining = budget - (time.monotonic() - start)
        if i > 0 and remaining < 1.0:
            break
        try:
            r = await send(model, min(per_attempt, max(remaining, 1.0)))
            last_exc = None
        except httpx.TransportError as e:
            r, last_exc = None, e
            continue
        if r.status_code in FAILOVER_STATUS and i < len(order) - 1:
            await asyncio.sleep(1.0 if order[i + 1] == model else 0)
            continue
        return r
    if r is not None:
        return r
    raise last_exc if last_exc else httpx.ConnectError("no model configured")


class GroqLLM:
    """OpenAI-compatible chat client (Groq, Gemini's OpenAI endpoint, OpenRouter...). `model` may be a comma-separated failover list."""

    def __init__(self, api_key: str, model: str = LLM_MODEL, timeout: float = LLM_TIMEOUT,
                 client: Optional[httpx.AsyncClient] = None):
        self.api_key, self.model, self.timeout, self._client = api_key, model, timeout, client

    async def _chat(self, system: str, user: str) -> Optional[dict[str, Any]]:
        order = model_order(self.model)
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async def send(model: str, timeout: float) -> httpx.Response:
            body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            if self._client:
                return await self._client.post(GROQ_CHAT_URL, json=body, headers=headers, timeout=timeout)
            async with httpx.AsyncClient(timeout=timeout) as c:
                return await c.post(GROQ_CHAT_URL, json=body, headers=headers)

        try:
            r = await post_with_failover(order, send, per_attempt=self.timeout / 2 if len(set(order)) > 1 else self.timeout,
                                         budget=self.timeout)
            r.raise_for_status()
            data = json.loads(r.json()["choices"][0]["message"]["content"])
            return data if isinstance(data, dict) else None
        except Exception as e:  # timeout, HTTP, bad JSON: caller falls back silently
            status = getattr(getattr(e, "response", None), "status_code", None)
            log.info("ai_listing LLM call failed: %s%s", type(e).__name__, f" (HTTP {status})" if status else "")
            return None

    async def extract(self, text: str, city_hint: Optional[str] = None) -> Optional[dict[str, Any]]:
        user = text[:4000] + (f"\n\n(City hint: {city_hint})" if city_hint else "")
        return await self._chat(_EXTRACT_SYSTEM, user)

    async def translate(self, facts: dict[str, Any], description_en: str) -> Optional[dict[str, str]]:
        out = await self._chat(_TRANSLATE_SYSTEM, description_en)
        if not out:
            return None
        return {k: v.strip() for k, v in out.items() if k in ("hi", "mr") and isinstance(v, str) and v.strip()} or None


class GroqTranscriber:
    def __init__(self, api_key: str, model: str = STT_MODEL, timeout: float = STT_TIMEOUT,
                 client: Optional[httpx.AsyncClient] = None):
        self.api_key, self.model, self.timeout, self._client = api_key, model, timeout, client

    async def transcribe(self, data: bytes, filename: str, content_type: str, language: Optional[str] = None) -> str:
        form = {"model": self.model, "response_format": "json", "temperature": "0"}
        if language:
            form["language"] = language
        files = {"file": (filename or "audio", data, content_type or "application/octet-stream")}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            if self._client:
                r = await self._client.post(GROQ_STT_URL, data=form, files=files, headers=headers, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as c:
                    r = await c.post(GROQ_STT_URL, data=form, files=files, headers=headers)
            r.raise_for_status()
            return (r.json().get("text") or "").strip()
        except Exception as e:
            raise TranscriptionError(f"transcription failed ({type(e).__name__})") from e


GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_GEMINI_STT_PROMPT = (
    "Analyse this voice note. First decide whether a human is clearly speaking intelligible words (not silence, noise, hum or music). "
    "If not, set speech_detected to false and transcript to an empty string. If yes, set speech_detected to true and give the exact "
    "transcript of the words spoken. The speaker is Indian and may use Hindi, Marathi, English or a mix: write Hindi and Marathi in "
    "Devanagari, English in Latin letters, and every number as digits. No commentary or translation. Never guess or invent words."
)
# Asking for a flag first is what stops the model from inventing sentences for silence (a plain "transcribe" prompt does that).
_GEMINI_STT_SCHEMA = {"type": "OBJECT", "properties": {"speech_detected": {"type": "BOOLEAN"}, "transcript": {"type": "STRING"}},
                      "required": ["speech_detected", "transcript"]}


class GeminiTranscriber:
    """Speech-to-text through Gemini's audio understanding (generateContent with inline audio). Free tier via Google AI Studio.
    `model` (or AI_GEMINI_STT_MODEL) may be a comma-separated failover list: each model has its own free daily quota."""

    def __init__(self, api_key: str, model: Optional[str] = None, timeout: float = STT_TIMEOUT,
                 client: Optional[httpx.AsyncClient] = None):
        self.api_key = api_key
        self.model = model or os.environ.get("AI_GEMINI_STT_MODEL") or "gemini-3.5-flash"
        self.timeout, self._client = timeout, client

    async def transcribe(self, data: bytes, filename: str, content_type: str, language: Optional[str] = None) -> str:
        mime = (content_type or "").split(";")[0].strip().lower()
        if mime in ("", "application/octet-stream"):
            mime = {".mp3": "audio/mp3", ".wav": "audio/wav", ".ogg": "audio/ogg", ".m4a": "audio/mp4"}.get(
                os.path.splitext(filename or "")[1].lower(), "audio/webm")
        if mime == "audio/x-m4a":
            mime = "audio/mp4"
        prompt = _GEMINI_STT_PROMPT + (f" The spoken language is probably '{language}'." if language else "")
        body = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": _GEMINI_STT_SCHEMA}}
        headers = {"x-goog-api-key": self.api_key}  # header, not ?key=, so the key never lands in a URL or log line
        order = model_order(self.model)

        async def send(model: str, timeout: float) -> httpx.Response:
            url = f"{GEMINI_BASE_URL}/models/{model}:generateContent"
            if self._client:
                return await self._client.post(url, json=body, headers=headers, timeout=timeout)
            async with httpx.AsyncClient(timeout=timeout) as c:
                return await c.post(url, json=body, headers=headers)

        try:
            r = await post_with_failover(order, send, per_attempt=min(self.timeout, 20.0), budget=max(self.timeout, STT_BUDGET))
            r.raise_for_status()
            parts = (r.json().get("candidates") or [{}])[0].get("content", {}).get("parts") or []
            out = json.loads("".join(p.get("text", "") for p in parts))
            if not (isinstance(out, dict) and out.get("speech_detected") is True):
                return ""
            return str(out.get("transcript") or "").strip()
        except Exception as e:
            raise TranscriptionError(f"transcription failed ({type(e).__name__})") from e


def default_llm() -> Optional[LLMClient]:
    key = groq_api_key()
    return GroqLLM(key) if key else None


def default_transcriber() -> Optional[Transcriber]:
    """AI_STT_PROVIDER=gemini uses Gemini audio (key: AI_STT_API_KEY or GEMINI_API_KEY); anything else uses Groq Whisper."""
    if (os.environ.get("AI_STT_PROVIDER") or "").strip().lower() == "gemini":
        gkey = os.environ.get("AI_STT_API_KEY") or os.environ.get("GEMINI_API_KEY")
        return GeminiTranscriber(gkey) if gkey else None
    key = groq_api_key()
    return GroqTranscriber(key) if key else None
