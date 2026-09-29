"""Injectable LLM + speech-to-text clients (Groq). Tests inject fakes; no network is touched by default paths."""
import json
import logging
import os
from typing import Any, Optional, Protocol

import httpx

log = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
LLM_MODEL = os.environ.get("AI_LISTING_LLM_MODEL", "llama-3.1-8b-instant")
STT_MODEL = os.environ.get("AI_LISTING_STT_MODEL", "whisper-large-v3")
LLM_TIMEOUT = 8.0
STT_TIMEOUT = 30.0


def groq_api_key() -> Optional[str]:
    key = os.environ.get("GROQ_API_KEY")
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


class GroqLLM:
    def __init__(self, api_key: str, model: str = LLM_MODEL, timeout: float = LLM_TIMEOUT,
                 client: Optional[httpx.AsyncClient] = None):
        self.api_key, self.model, self.timeout, self._client = api_key, model, timeout, client

    async def _chat(self, system: str, user: str) -> Optional[dict[str, Any]]:
        body = {"model": self.model, "temperature": 0, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            if self._client:
                r = await self._client.post(GROQ_CHAT_URL, json=body, headers=headers, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as c:
                    r = await c.post(GROQ_CHAT_URL, json=body, headers=headers)
            r.raise_for_status()
            data = json.loads(r.json()["choices"][0]["message"]["content"])
            return data if isinstance(data, dict) else None
        except Exception as e:  # timeout, HTTP, bad JSON: caller falls back silently
            log.info("ai_listing LLM call failed: %s", type(e).__name__)
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


def default_llm() -> Optional[LLMClient]:
    key = groq_api_key()
    return GroqLLM(key) if key else None


def default_transcriber() -> Optional[Transcriber]:
    key = groq_api_key()
    return GroqTranscriber(key) if key else None
