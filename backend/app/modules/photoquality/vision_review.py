"""AI visual review of a finished post or card: legibility, cut-off text, crop, clutter, professional look, and whether the
text matches the picture. Advice only: it never blocks approval and never invents facts.

    res = await review(["uploads/calendar/w1/x-1.jpg"], {"caption": "...", "critic": pack.report})
    # {"score": 82, "verdict": "good", "notes": [...], "source": "ai" | "rules", "ai_available": bool, "model": "..."}

Provider chain (all OpenAI-compatible chat with image_url parts):
  1. AI_VISION_MODEL (default qwen/qwen3.8-27b, Groq's vision model as of 2026-09) at AI_VISION_BASE_URL or AI_LLM_BASE_URL with
     AI_VISION_API_KEY or AI_LLM_API_KEY / GROQ_API_KEY. Groq takes at most 3 images per request.
  2. AI_VISION_FALLBACK_MODEL (e.g. an OpenRouter ':free' vision model) at AI_VISION_FALLBACK_BASE_URL or AI_LLM_FALLBACK_BASE_URL
     with AI_VISION_FALLBACK_API_KEY or AI_LLM_FALLBACK_API_KEY. Only used when a model id is configured.
  3. None reachable: a rule-only score from the photo analysis and the creative critic, with the note 'AI review unavailable'.
AI_VISION_REVIEW=off turns the AI step off everywhere (rules only).

Results are cached per (file content hash, context hash, model) in memory and as JSON under QUALITY_CACHE_DIR
(default <UPLOAD_DIRECTORY>/quality_reviews), so reviewing the same card twice costs nothing.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence

import cv2
import httpx

from .analysis import analyze, downscale, label, load_bgr

log = logging.getLogger(__name__)

DEFAULT_VISION_MODEL = "qwen/qwen3.8-27b"
MAX_IMAGES = 3            # Groq's per-request image limit
REVIEW_SIDE = 1024        # images are downscaled to this long side before sending (keeps base64 well under 4 MB)
TIMEOUT = 25.0
GOOD, FIX = 75, 50        # score >= GOOD: good; >= FIX: fix; else redo
MAX_NOTES = 4
RETRY_WAIT = 12.0          # seconds to wait once after a 429 before giving up on that provider
UNAVAILABLE = "AI review unavailable"

SYSTEM = (
    "You are a strict art director checking a finished social media image for an Indian real-estate brand before it is "
    "posted. Judge ONLY what you can see in the image(s) and the text you are given. Check: is all text legible (size, "
    "contrast), is any text cut off at an edge, is the crop sensible (nothing important cut, no awkward empty areas), is "
    "it cluttered, does it look professional, and does the caption or headline match what the image shows. Do NOT invent "
    "facts, prices, places or features and do not suggest adding any. Do not comment on the property itself or its price. "
    'Reply with ONE JSON object only: {"score": integer 0-100, "verdict": "good"|"fix"|"redo", '
    '"notes": [at most 4 short, concrete strings, e.g. "text cut at the bottom"]}. Use "redo" only for a clear defect '
    "(cut-off or unreadable text, broken layout), \"fix\" for small issues, \"good\" when it is ready to post. "
    "These are designed cards: panels, boxes, badges, flat or dark backgrounds, placeholder bars and struck-through text "
    "(a myth shown crossed out next to the fact) are deliberate and are not defects. Judge the image as a whole; never "
    "describe it as zoomed, cropped from a larger image or a composite unless text is visibly cut at the frame edge."
)


class VisionClient(Protocol):
    model: str

    async def review(self, images: List[bytes], prompt: str) -> Optional[Dict[str, Any]]: ...


# ---- helpers ------------------------------------------------------------------------------------------
def verdict_for(score: int) -> str:
    return "good" if score >= GOOD else "fix" if score >= FIX else "redo"


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _context_text(context: Dict[str, Any]) -> str:
    parts = []
    for k in ("kind", "headline", "caption", "text"):
        v = context.get(k)
        if isinstance(v, str) and v.strip():
            parts.append(f"{k}: {v.strip()[:900]}")
    return "\n".join(parts)


def jpeg_for_review(path: Path) -> bytes:
    img = downscale(load_bgr(path), REVIEW_SIDE)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if not ok:
        raise ValueError("encode failed")
    return buf.tobytes()


def parse_reply(text: str) -> Optional[Dict[str, Any]]:
    """The first JSON object in a reply (reasoning models may wrap it in <think> blocks or code fences)."""
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def clean_ai(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        score = int(round(float(data.get("score"))))
    except (TypeError, ValueError):
        return None
    score = max(0, min(100, score))
    verdict = data.get("verdict") if data.get("verdict") in ("good", "fix", "redo") else verdict_for(score)
    notes = [re.sub(r"\s+", " ", str(n)).strip()[:140] for n in (data.get("notes") or []) if isinstance(n, (str, int, float))]
    return {"score": score, "verdict": verdict, "notes": [n for n in notes if n][:MAX_NOTES]}


# ---- clients ------------------------------------------------------------------------------------------
class OpenAIVision:
    """OpenAI-compatible chat completions with image parts (Groq, OpenRouter, Gemini's OpenAI endpoint)."""

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float = TIMEOUT, client: Optional[httpx.AsyncClient] = None):
        self.api_key, self.model, self.timeout, self._client = api_key, model, timeout, client
        self.url = f"{base_url.rstrip('/')}/chat/completions"

    async def review(self, images: List[bytes], prompt: str) -> Optional[Dict[str, Any]]:
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        for b in images[:MAX_IMAGES]:
            content.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}})
        body = {"model": self.model, "temperature": 0, "max_completion_tokens": 600,
                "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            for attempt in (1, 2):
                if self._client:
                    r = await self._client.post(self.url, json=body, headers=headers, timeout=self.timeout)
                else:
                    async with httpx.AsyncClient(timeout=self.timeout) as c:
                        r = await c.post(self.url, json=body, headers=headers)
                if r.status_code != 429 or attempt == 2:
                    break
                try:  # rate limited (images cost ~2k tokens each): wait as asked, at most RETRY_WAIT, then try once more
                    wait = min(float(r.headers.get("retry-after") or RETRY_WAIT), RETRY_WAIT)
                except ValueError:
                    wait = RETRY_WAIT
                await asyncio.sleep(wait)
            r.raise_for_status()
            return parse_reply(r.json()["choices"][0]["message"]["content"] or "")
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            log.info("vision review via %s failed: %s%s", self.model, type(e).__name__, f" (HTTP {status})" if status else "")
            return None


def default_clients() -> List[VisionClient]:
    if (os.environ.get("AI_VISION_REVIEW") or "on").strip().lower() == "off":
        return []
    out: List[VisionClient] = []
    key = os.environ.get("AI_VISION_API_KEY")
    if not key:
        from app.modules.ai_listing.llm import groq_api_key
        key = groq_api_key()
    base = os.environ.get("AI_VISION_BASE_URL") or os.environ.get("AI_LLM_BASE_URL") or "https://api.groq.com/openai/v1"
    if key:
        for model in [m.strip() for m in (os.environ.get("AI_VISION_MODEL") or DEFAULT_VISION_MODEL).split(",") if m.strip()]:
            out.append(OpenAIVision(key, model, base))
    fb_model = os.environ.get("AI_VISION_FALLBACK_MODEL")
    fb_key = os.environ.get("AI_VISION_FALLBACK_API_KEY") or os.environ.get("AI_LLM_FALLBACK_API_KEY")
    fb_base = os.environ.get("AI_VISION_FALLBACK_BASE_URL") or os.environ.get("AI_LLM_FALLBACK_BASE_URL")
    if fb_model and fb_key and fb_base:
        out.append(OpenAIVision(fb_key, fb_model, fb_base))
    return out


# ---- rule score ---------------------------------------------------------------------------------------
_PROMISE = re.compile(r"(?<![\d,.])(\d{1,2})(?!\s*bhk)\s+(?:\w+\s+){0,2}?(details|questions|tips|things|steps|ways|mistakes|signs|"
                      r"reasons|checks|documents|points|rules|myths|facts|items|papers|costs|charges|sawaal)(?!\w)", re.I)
_LIST_LINE = re.compile("^\\s*(?:[-•*▪✅✔☑]|\\d{1,2}[.)]|\\d️?⃣|\U0001F51F)\\s*\\S")


def promise_gap(context: Dict[str, Any]) -> Optional[str]:
    """'3 tips ...' in the headline but fewer than 3 listed in the caption: the post does not deliver what it promises."""
    head = str(context.get("headline") or "")
    caption = str(context.get("caption") or "")
    first = caption.strip().splitlines()[0] if caption.strip() else ""
    m = _PROMISE.search(head) or _PROMISE.search(first)
    if not m:
        return None
    want = int(m.group(1))
    if want < 2 or want > 12:
        return None
    have = sum(1 for line in caption.splitlines()
               if _LIST_LINE.match(line) and "#" not in line[:3] and "avasetu team" not in line.lower())  # not the sign-off
    if have >= want:
        return None
    return f"Headline promises {want} {m.group(2).lower()} but the caption lists {have}"


def rule_review(paths: Sequence[Path], context: Dict[str, Any]) -> Dict[str, Any]:
    """Score from the photo analysis of each image and the creative critic report (if the context carries one)."""
    notes: List[str] = []
    scores = []
    for p in paths:
        try:
            q = analyze(p)
        except Exception:
            continue
        # rendered cards are designed graphics: dark navy or light cream backgrounds and flat colour areas are intended,
        # so only blur and size count here (the photos inside were checked for exposure when they were uploaded)
        issues = [i for i in q["issues"] if i in ("blurry", "small")]
        s = 100 - 18 * len(issues)
        scores.append(s)
        if issues:
            notes.append(f"{Path(p).name}: {label({'issues': issues}).replace('Check: ', '')}")
    score = sum(scores) / len(scores) if scores else 70.0
    hard = bool(scores) and min(scores) < 100  # a blurred or tiny image
    gap = promise_gap(context)
    if gap:
        notes.insert(0, gap)
        score -= 30
        hard = True
    critic = context.get("critic") or {}
    for prob in (critic.get("problems") or []) if isinstance(critic, dict) else []:
        sev = prob.get("severity") if isinstance(prob, dict) else None
        msg = prob.get("message") if isinstance(prob, dict) else None
        score -= 10 if sev == "error" else 3 if sev == "warn" else 0
        if sev == "error" and msg:
            notes.append(str(msg)[:140])
        if sev == "error":
            hard = True
    if hard:
        score = min(score, GOOD - 1)  # a measurable failure is never 'good'
    s = int(round(max(0, min(100, score))))
    return {"score": s, "verdict": verdict_for(s), "notes": notes[:MAX_NOTES], "hard": hard}


# ---- cache --------------------------------------------------------------------------------------------
_MEM: Dict[str, Dict[str, Any]] = {}


def cache_dir() -> Path:
    d = os.environ.get("QUALITY_CACHE_DIR")
    return Path(d) if d else Path(os.environ.get("UPLOAD_DIRECTORY", "uploads")) / "quality_reviews"


def _cache_get(key: str, directory: Optional[Path]) -> Optional[Dict[str, Any]]:
    if key in _MEM:
        return _MEM[key]
    if directory is not None:
        f = directory / f"{key}.json"
        try:
            if f.is_file():
                data = json.loads(f.read_text("utf8"))
                _MEM[key] = data
                return data
        except (OSError, ValueError):
            return None
    return None


def _cache_put(key: str, value: Dict[str, Any], directory: Optional[Path]) -> None:
    if len(_MEM) > 2000:
        _MEM.clear()
    _MEM[key] = value
    if directory is not None:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{key}.json").write_text(json.dumps(value), "utf8")
        except OSError:
            pass


# ---- the review ---------------------------------------------------------------------------------------
async def review(image_paths: Sequence[Any], context: Optional[Dict[str, Any]] = None,
                 clients: Optional[Sequence[VisionClient]] = None, cache: Optional[Path] = None,
                 use_cache: bool = True) -> Dict[str, Any]:
    """Review finished images. Never raises. `clients=None` uses the configured provider chain; `[]` means rules only."""
    context = dict(context or {})
    paths = [Path(p) for p in image_paths if p and Path(p).is_file()][:MAX_IMAGES]
    chain = list(default_clients() if clients is None else clients)
    directory = cache if cache is not None else (cache_dir() if clients is None and chain else None)
    if not paths:
        return {"score": 0, "verdict": "fix", "notes": ["No image to review yet"], "source": "rules", "ai_available": False, "model": None}
    try:
        hashes = [file_hash(p) for p in paths]
    except OSError:
        hashes = [str(p) for p in paths]
    ctx_hash = hashlib.sha256(json.dumps({"t": _context_text(context), "c": context.get("critic")}, sort_keys=True, default=str).encode()).hexdigest()[:16]
    models = ",".join(getattr(c, "model", "?") for c in chain) or "rules"
    models += hashlib.sha256(SYSTEM.encode()).hexdigest()[:8]  # a new prompt or rule set is a new review
    key = hashlib.sha256(("|".join(hashes) + ctx_hash + models).encode()).hexdigest()[:40]
    if use_cache:
        hit = _cache_get(key, directory)
        if hit:
            return {**hit, "cached": True}

    rules = rule_review(paths, context)
    result: Optional[Dict[str, Any]] = None
    if chain:
        try:
            images = [jpeg_for_review(p) for p in paths]
        except Exception:
            images = []
        prompt = ("Review this finished post image" + ("s (slides in order)" if len(images) > 1 else "") + ".\n"
                  + (_context_text(context) or "No caption given."))
        for c in chain if images else []:
            try:
                data = await c.review(images, prompt)
            except Exception:
                log.info("vision client %s raised", getattr(c, "model", "?"), exc_info=True)
                data = None
            ai = clean_ai(data) if data else None
            if ai:
                # the AI judges the look; hard rule failures (critic errors, a dark or blurred photo) still pull the score down
                score = int(round(0.75 * ai["score"] + 0.25 * rules["score"]))
                verdict = ai["verdict"]
                if verdict == "good" and score < FIX:
                    verdict = "fix"
                if rules.get("hard") and verdict == "good":  # a measured failure (promise gap, critic error) outranks the look
                    verdict, score = "fix", min(score, GOOD - 1)
                if verdict == "redo" and not rules.get("hard"):
                    # the vision model sometimes calls a clean designed card 'corrupted' or 'cropped'; without a measured
                    # failure an AI 'redo' is a 'check', so a person looks rather than the item being regenerated
                    verdict, score = "fix", max(score, FIX)
                notes = [n for n in rules["notes"] if n.startswith("Headline promises")] + ai["notes"]
                notes += [n for n in rules["notes"] if n not in notes]
                result = {"score": score, "verdict": verdict, "notes": notes[:MAX_NOTES], "source": "ai", "ai_available": True,
                          "model": getattr(c, "model", None)}
                break
    if result is None:
        result = {**rules, "notes": (rules["notes"] + [UNAVAILABLE])[:MAX_NOTES + 1], "source": "rules", "ai_available": False, "model": None}
    if result["source"] == "ai" or not chain:
        _cache_put(key, result, directory)   # a failed AI call is not cached: it is retried next time
    return result


def summary(res: Dict[str, Any]) -> str:
    """'Quality 82/100 · Good' or 'Quality 54 · Check: text cut at the bottom' (same wording as the app's chip)."""
    s = res.get("score", 0)
    if res.get("verdict") == "good":
        return f"Quality {s}/100 · Good"
    first = next((n for n in res.get("notes") or [] if n != UNAVAILABLE), "")
    return f"Quality {s} · Check" + (f": {first}" if first else "")
