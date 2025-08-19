from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import logging
import random

from core.config import settings

try:
    from groq import Groq
    HAS_GROQ = True
except Exception:
    HAS_GROQ = False

router = APIRouter(prefix="/api/branding", tags=["Branding"])
logger = logging.getLogger(__name__)


class BrandingRequest(BaseModel):
    business_name: str = Field(..., min_length=2, description="Agent or brand name")
    tags: Optional[List[str]] = Field(default=None, description="Keywords or positioning tags")
    tone: Optional[str] = Field(default="premium, trustworthy, modern", description="Desired brand tone")
    market: Optional[str] = Field(default="India", description="Geographic market focus")


class BrandingResponse(BaseModel):
    brand_name_options: List[str]
    tagline: str
    colors: Dict[str, str]  # {primary, secondary, accent}
    notes: Optional[str] = None


def _fallback_palette() -> Dict[str, str]:
    palettes = [
        {"primary": "#0ea5e9", "secondary": "#0f172a", "accent": "#f59e0b"},  # Sky Blue / Slate / Amber
        {"primary": "#4f46e5", "secondary": "#1f2937", "accent": "#06b6d4"},  # Indigo / Gray / Cyan
        {"primary": "#16a34a", "secondary": "#111827", "accent": "#f97316"},  # Green / Gray-900 / Orange
        {"primary": "#e11d48", "secondary": "#0b1021", "accent": "#06b6d4"},  # Rose / Navy / Cyan
    ]
    return random.choice(palettes)


def _fallback_branding(req: BrandingRequest) -> BrandingResponse:
    primary, secondary, accent = _fallback_palette().values()
    return BrandingResponse(
        brand_name_options=[
            f"{req.business_name} Realty",
            f"{req.business_name} Estates",
            f"{req.business_name} Properties",
        ],
        tagline=f"{req.business_name}: Trusted Property Partner",
        colors={"primary": primary, "secondary": secondary, "accent": accent},
        notes="Fallback branding used because GROQ_API_KEY missing or LLM unavailable.")


def _build_prompt(req: BrandingRequest) -> str:
    tags_str = ", ".join(req.tags or [])
    return (
        "You are a world-class brand strategist for real estate agents. "
        "Return STRICT JSON with keys: brand_name_options (array of 3), tagline (string), "
        "colors (object with hex strings: primary, secondary, accent). No prose.\n\n"
        f"Business Name: {req.business_name}\n"
        f"Tags: {tags_str or 'real estate, property, trust'}\n"
        f"Tone: {req.tone}\n"
        f"Market: {req.market}\n"
        "Constraints:\n"
        "- Use accessible contrast (WCAG AA)\n"
        "- Prefer modern, premium palette suitable for India market\n"
        "- Only output valid JSON"
    )


@router.post("/suggest", response_model=BrandingResponse)
def suggest_branding(payload: BrandingRequest) -> Any:
    if not settings.GROQ_API_KEY or not HAS_GROQ:
        return _fallback_branding(payload)

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        prompt = _build_prompt(payload)

        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You output only JSON; no code fences, no extra text."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=512,
        )

        content = completion.choices[0].message.content if completion.choices else "{}"
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Attempt to extract JSON block
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                data = json.loads(content[start:end + 1])
            else:
                logger.warning("LLM returned non-JSON; using fallback")
                return _fallback_branding(payload)

        brand_name_options = data.get("brand_name_options") or []
        tagline = data.get("tagline") or f"{payload.business_name}: Property Partner"
        colors = data.get("colors") or _fallback_palette()

        # Normalize color keys and hex format
        def _hex(x: str) -> str:
            x = x.strip()
            return x if x.startswith('#') else f"#{x}"

        normalized_colors = {
            "primary": _hex(colors.get("primary", _fallback_palette()["primary"])),
            "secondary": _hex(colors.get("secondary", _fallback_palette()["secondary"])),
            "accent": _hex(colors.get("accent", _fallback_palette()["accent"]))
        }

        # Ensure we have exactly 3 options
        if not isinstance(brand_name_options, list):
            brand_name_options = [str(brand_name_options)]
        brand_name_options = [str(x) for x in brand_name_options if x][:3]
        if len(brand_name_options) < 3:
            brand_name_options += [
                f"{payload.business_name} Realty",
                f"{payload.business_name} Estates",
                f"{payload.business_name} Properties",
            ][: 3 - len(brand_name_options)]

        return BrandingResponse(
            brand_name_options=brand_name_options,
            tagline=tagline,
            colors=normalized_colors,
            notes="LLM-generated"
        )
    except Exception as e:
        logger.error(f"Branding suggestion failed: {e}")
        raise HTTPException(status_code=500, detail="Branding suggestion failed")

