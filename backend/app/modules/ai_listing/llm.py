"""Listing extraction and translation on top of the AI gateway (app.platform.llm).

The gateway knows providers, models and failover; this module knows the listing prompts. `ListingLLM` gives the listing service
`extract` and `translate` on any gateway client; with a FallbackLLM each provider is tried in turn, exactly as before the split.
"""
from typing import Any, Optional, Protocol

from app.platform.llm import LLM, LLM_TIMEOUT, Transcriber, TranscriptionError, default_llm, default_transcriber

__all__ = ["LLMClient", "ListingLLM", "default_listing_llm", "LLM_TIMEOUT", "Transcriber", "TranscriptionError",
           "default_transcriber"]

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


class LLMClient(Protocol):
    async def extract(self, text: str, city_hint: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Return a JSON object with listing fact fields, or None."""

    async def translate(self, facts: dict[str, Any], description_en: str) -> Optional[dict[str, str]]:
        """Return {'hi': ..., 'mr': ...} (either may be missing), or None."""


def _providers(llm: LLM) -> list:
    return list(getattr(llm, "providers", None) or [llm])


class ListingLLM:
    """The listing prompts on a gateway client (`json(system, user)`), plus that client's own json and text, so it can be
    used wherever the gateway client was. For extract and translate the first usable answer wins."""

    def __init__(self, llm: LLM):
        self.llm = llm

    # the gateway's own calls pass straight through (the about-suggest endpoint uses json on the same client)
    async def json(self, system: str, user: str) -> Optional[dict[str, Any]]:
        return await self.llm.json(system, user)

    async def text(self, system: str, user: str, timeout: Optional[float] = None) -> Optional[str]:
        return await self.llm.text(system, user, timeout)

    async def extract(self, text: str, city_hint: Optional[str] = None) -> Optional[dict[str, Any]]:
        user = text[:4000] + (f"\n\n(City hint: {city_hint})" if city_hint else "")
        for p in _providers(self.llm):
            out = await p.json(_EXTRACT_SYSTEM, user)
            if out:
                return out
        return None

    async def translate(self, facts: dict[str, Any], description_en: str) -> Optional[dict[str, str]]:
        for p in _providers(self.llm):
            out = await p.json(_TRANSLATE_SYSTEM, description_en)
            res = {k: v.strip() for k, v in (out or {}).items() if k in ("hi", "mr") and isinstance(v, str) and v.strip()} or None
            if res:
                return res
        return None


def default_listing_llm() -> Optional[LLMClient]:
    gateway = default_llm()
    return ListingLLM(gateway) if gateway else None
