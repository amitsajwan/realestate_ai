"""Gemini's generateContent with pictures: a picture drawn from a picture and a prompt, and pictures read into JSON.

The text gateway (platform.llm) speaks Gemini's OpenAI-compatible API, which takes no picture out; this is the native API for the
callers that need one (areastats.plans3d). The key is the paid GEMINI_API_KEY, sent in a header so it never lands in a URL or log.
Each call tries the models in order and raises GeminiError when none answers (a spending cap, no key, no picture back)."""
import base64
import json
import logging
import os
from typing import List, Sequence

import httpx

log = logging.getLogger(__name__)

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
IMAGE_MODELS = ("gemini-3.1-flash-image", "gemini-2.5-flash-image")
READ_MODELS = ("gemini-3-flash-preview", "gemini-flash-latest")


class GeminiError(Exception):
    pass


def available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def mime_of(data: bytes) -> str:
    if data[:4] == b"\x89PNG":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _picture(data: bytes) -> dict:
    return {"inlineData": {"mimeType": mime_of(data), "data": base64.b64encode(data).decode()}}


async def _generate(model: str, body: dict, timeout: float) -> dict:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise GeminiError("GEMINI_API_KEY is not set")
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.post(URL.format(model=model), headers={"x-goog-api-key": key}, json=body)
    except Exception as e:
        raise GeminiError(f"{model} unreachable ({type(e).__name__})")
    if r.status_code >= 400:
        raise GeminiError(f"{model} HTTP {r.status_code}: {r.text[:160]}".replace(key, "[redacted]"))
    return r.json()


def _parts(answer: dict) -> list:
    return ((answer.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []


async def _post(model: str, body: dict, timeout: float) -> list:
    return _parts(await _generate(model, body, timeout))


async def draw_from(image: bytes, prompt: str, aspect: str = "16:9", models: Sequence[str] = IMAGE_MODELS,
                    timeout: float = 180.0) -> bytes:
    """A picture (PNG or JPEG bytes) drawn from `image` as `prompt` asks. Raises GeminiError when no model draws one."""
    body = {"contents": [{"parts": [_picture(image), {"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}}
    why = "no model answered"
    for model in models:
        try:
            parts = await _post(model, body, timeout)
        except GeminiError as e:
            why = str(e)
            continue
        for p in parts:
            data = (p.get("inlineData") or {}).get("data")
            if data:
                return base64.b64decode(data)
        why = f"{model} answered without a picture"
    raise GeminiError(why)


async def read_counted(images: List[bytes], prompt: str, models: Sequence[str] = READ_MODELS, timeout: float = 90.0,
                       thinking: str = "") -> tuple:
    """(answer, {model, tokens_in, tokens_out}) for a caller that keeps its own spending limit. Gemini bills thinking as output.
    `thinking`: "low" stops a dense page taking over a minute (brochure pilot, 2026-11-07). Raises GeminiError like `read`."""
    config: dict = {"responseMimeType": "application/json", "temperature": 0}
    if thinking:
        config["thinkingConfig"] = {"thinkingLevel": thinking}
    body = {"contents": [{"parts": [*(_picture(i) for i in images), {"text": prompt}]}], "generationConfig": config}
    why = "no model answered"
    for model in models:
        try:
            answer = await _generate(model, body, timeout)
            out = json.loads("".join(p.get("text", "") for p in _parts(answer)))
        except (GeminiError, ValueError) as e:
            why = str(e)
            continue
        out = out[0] if isinstance(out, list) and len(out) == 1 and isinstance(out[0], dict) else out
        used = answer.get("usageMetadata") or {}
        return out, {"model": model, "tokens_in": int(used.get("promptTokenCount") or 0),
                     "tokens_out": int(used.get("candidatesTokenCount") or 0) + int(used.get("thoughtsTokenCount") or 0)}
    raise GeminiError(why)


async def read(images: List[bytes], prompt: str, models: Sequence[str] = READ_MODELS, timeout: float = 90.0) -> dict:
    """`images` read as `prompt` asks, answered as a JSON object. Raises GeminiError when no model gives one."""
    body = {"contents": [{"parts": [*(_picture(i) for i in images), {"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    why = "no model answered"
    for model in models:
        try:
            parts = await _post(model, body, timeout)
            out = json.loads("".join(p.get("text", "") for p in parts))
            if isinstance(out, list) and len(out) == 1:   # gemini-3-flash wraps a JSON object in a list (brochure pilot, 2026-11-07)
                out = out[0]
        except (GeminiError, ValueError) as e:
            why = str(e)
            continue
        if isinstance(out, dict):
            return out
        why = f"{model} did not answer an object"
    raise GeminiError(why)
