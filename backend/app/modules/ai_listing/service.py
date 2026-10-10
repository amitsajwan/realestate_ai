"""Orchestrates transcription, deterministic + LLM extraction, merge, copy generation -> AIDraft.

With a builder's brochure (brochure.py) its claims and text join the agent's words for the same extraction, the project is
matched in our MahaRERA register, and each field says where it came from (`sources`)."""
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from . import brochure as bro
from . import copywriter as copy
from .extractor import extract
from .llm import LLMClient, LLM_TIMEOUT, Transcriber, TranscriptionError
from .about import about_from_text
from .merge import merge, sanitise_llm
from .schemas import REQUIRED_TO_PUBLISH, AIDraft, Extraction
from .plausibility import build_warnings
from app.modules.propertyfacts import points as selling

log = logging.getLogger(__name__)

BROCHURE_HINT = ("\n\n(This is a builder's brochure for a new project on sale. locality is the village or area where the "
                 "project is, never the project's own name. A Gat or survey number is not a RERA number.)")


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


HALF_ACRE_SQFT = 21780  # a plot or flat this big is a layout's land, not one unit


class AIListingService:
    def __init__(self, llm: Optional[LLMClient] = None, transcriber: Optional[Transcriber] = None):
        self.llm, self.transcriber = llm, transcriber

    async def create_draft(self, text: Optional[str] = None, audio: Optional[AudioInput] = None,
                           image_count: int = 0, city_hint: Optional[str] = None, brochure_url: Optional[str] = None,
                           uploads_dir: Optional[Path] = None, register: Any = None) -> AIDraft:
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
        if not (brochure_url or "").strip():
            return await self.from_text(combined, image_count, city_hint, transcript, warnings, register=register)
        try:
            b = await bro.read(brochure_url, Path(uploads_dir or "uploads"))
        except Exception as e:  # never a 500 for a brochure: the agent's own words still make a draft
            log.warning("ai_listing brochure failed: %s", type(e).__name__)
            b = {"text": "", "claims": [], "rera_no": None, "pages": 0, "error": "The brochure could not be read."}
        return await self.from_text(bro.extraction_text(combined, b), image_count, city_hint, transcript, warnings,
                                    brochure=b, agent_text=combined, register=register)

    async def from_text(self, text: str, image_count: int = 0, city_hint: Optional[str] = None,
                        transcript: Optional[str] = None, warnings: Optional[list[str]] = None,
                        brochure: Optional[dict] = None, agent_text: Optional[str] = None, register: Any = None) -> AIDraft:
        city_hint = (city_hint or "").strip()[:60] or None
        det, _ = extract(text, city_hint)
        llm_ex = Extraction()
        llm_up = self.llm is not None
        if self.llm is not None and text.strip():
            hint = BROCHURE_HINT if brochure is not None else ""
            raw = await _guard(self.llm.extract(text + hint, city_hint))
            llm_up = raw is not None  # if the text AI just failed or timed out, do not make the agent wait for a second call
            llm_ex = sanitise_llm(raw)
        merged = merge(det, llm_ex)
        facts, conf = dict(merged.values), dict(merged.confidence)
        if bro.same_place(facts.get("locality"), facts.get("project_name")):  # a project's name is not its locality
            facts.pop("locality", None)
            conf.pop("locality", None)
        sources = {k: "agent" for k in facts}
        selling_points: list = []
        selling_warnings: list = []
        if brochure is not None:
            sources = self._brochure_facts(facts, conf, brochure, agent_text or "", city_hint)
            selling_points, selling_warnings = self._selling(facts, conf, sources, brochure)
        rera_candidates: list = []
        maharera = None
        if register is not None and (facts.get("rera_no") or (brochure is not None and facts.get("project_name"))):
            by_name = facts.get("project_name") if brochure is not None else None
            m = await bro.match_register(register, facts.get("rera_no"), by_name)
            rera_candidates = m["candidates"]
            if m["record"]:
                maharera = bro.register_fields(m["record"])
                for k, v in (("rera_no", maharera.get("regno")), ("locality", maharera.get("locality")),
                             ("project_name", maharera.get("name"))):
                    if v and (k != "project_name" or not facts.get(k)):
                        facts[k], conf[k], sources[k] = v, 0.95, "maharera"

        draft: dict = dict(facts)
        title = copy.make_title(facts)
        en = copy.make_description_en(facts)
        if title:
            draft["title"] = title
        if en and brochure is not None:
            en = self._brochure_description(en, facts, brochure)
        if en:
            desc = {"en": en}
            if self.llm is not None and llm_up:
                tr = await _guard(self.llm.translate(facts, en))
                if isinstance(tr, dict):
                    desc.update({k: v for k, v in tr.items() if k in ("hi", "mr") and isinstance(v, str) and v.strip()})
            draft["description"] = desc
        about = await about_from_text(agent_text if brochure is not None else text, self.llm if llm_up else None)
        about.pop("project_name", None)  # already a top-level draft field
        if brochure is not None and brochure.get("claims"):
            about["highlights"] = self._highlights(about.get("highlights") or [], brochure["claims"])
        if about:
            draft["about"] = about

        present = set(draft) - {"description", "about"} | ({"description.en"} if en else set())
        missing = [k for k in REQUIRED_TO_PUBLISH if k not in present]
        if brochure is not None:
            sources.update({k: "brochure" for k in ("title", "description") if k in draft})
            if brochure.get("claims") and "about" in draft:
                sources["about"] = "brochure"
        return AIDraft(draft=draft, confidence={k: round(v, 2) for k, v in conf.items()}, missing=missing,
                       transcript=transcript, warnings=(warnings or []) + build_warnings(facts, conf) + selling_warnings,
                       selling_points=selling_points,
                       sources={k: v for k, v in sources.items() if k in draft}, rera_candidates=rera_candidates,
                       brochure=self._brochure_out(brochure), maharera=maharera)

    @staticmethod
    def _brochure_facts(facts: dict, conf: dict, b: dict, agent_text: str, city_hint: Optional[str]) -> dict:
        """Brochure-only rules on the merged facts; returns field -> source ("agent" where the agent's words say it)."""
        printed = " ".join(b.get("claims") or []) + "\n" + (b.get("text") or "")
        rera = facts.get("rera_no")
        if not (rera and bro.RERA.fullmatch(rera)):  # a gat/survey number is land, not a registration
            facts.pop("rera_no", None)
            conf.pop("rera_no", None)
        if b.get("rera_no") and not facts.get("rera_no"):
            facts["rera_no"], conf["rera_no"] = b["rera_no"], 0.95
        if b.get("project_name") and not facts.get("project_name"):  # from the logo or title page
            facts["project_name"], conf["project_name"] = b["project_name"], 0.8
        if not facts.get("transaction"):  # a builder's brochure is a new project on sale
            facts["transaction"], conf["transaction"] = "sale", 0.9
        facts["listing_scope"], conf["listing_scope"] = "layout", 0.8
        lo, hi = bro.sizes(printed)
        if lo:
            facts["size_min_sqft"], facts["size_max_sqft"] = lo, hi
            conf["size_min_sqft"] = conf["size_max_sqft"] = 0.8
        if not facts.get("locality"):
            place = bro.place_in(printed)
            if place and not bro.same_place(place, facts.get("project_name")):
                facts["locality"], conf["locality"] = place, 0.6
        if not facts.get("city") and bro.in_pune_district(printed):
            facts["city"], conf["city"] = "Pune", 0.8
        agent = extract(agent_text, city_hint)[0] if agent_text.strip() else Extraction()
        out = {}
        for k, v in facts.items():
            av = agent.values.get(k)
            out[k] = "agent" if av is not None and str(av).lower() == str(v).lower() else "brochure"
        return out

    @staticmethod
    def _selling(facts: dict, conf: dict, sources: dict, b: dict) -> tuple:
        """(selling_points, warnings) from the brochure's structured facts; the draft takes its price (the starting price),
        land area and village from them when the agent's words did not give them."""
        sf = dict(b.get("facts") or {})
        if not sf:
            return [], []
        for key, val, c in (("price_inr", sf.get("starting_price_inr"), 0.8), ("total_acres", sf.get("total_acres"), 0.7),
                            ("locality", sf.get("village"), 0.7)):
            if val and not facts.get(key):
                facts[key], conf[key], sources[key] = val, c, "brochure"
        if facts.get("listing_scope") == "layout" or facts.get("total_acres"):  # the layout's land is never one plot's size
            for k in ("carpet_sqft", "builtup_sqft", "super_builtup_sqft", "plot_sqft", "size_min_sqft", "size_max_sqft"):
                if (facts.get(k) or 0) >= HALF_ACRE_SQFT:
                    facts.pop(k, None), conf.pop(k, None), sources.pop(k, None)
        pts = selling.selling_points(sf, b.get("language") or "en", facts.get("property_type") or "plot")
        return pts, selling.warnings(sf, facts.get("price_inr"))

    @staticmethod
    def _brochure_description(en: str, facts: dict, b: dict) -> str:
        """The facts description plus the builder's own claims, said as theirs (claims are already hype-checked)."""
        extra = []
        lo, hi = facts.get("size_min_sqft"), facts.get("size_max_sqft")
        if lo:
            extra.append(f"Sizes from {copy.format_inr(lo)}" + (f" to {copy.format_inr(hi)}" if hi and hi != lo else "")
                         + " sq ft.")
        claims = [c.rstrip(".") for c in (b.get("claims") or [])[:4]]
        if claims:
            extra.append("The builder's brochure mentions: " + "; ".join(claims) + ".")
        return " ".join([en] + extra)[:4900]

    @staticmethod
    def _highlights(have: list, claims: list) -> list:
        from app.modules.listings.about import clean_text
        out = list(have)
        for c in claims:
            if len(out) >= bro.HIGHLIGHTS:
                break
            try:
                c = clean_text(c, "highlight")
            except ValueError:
                continue
            if c and c not in out:
                out.append(c)
        return out[:bro.HIGHLIGHTS]

    @staticmethod
    def _brochure_out(b: Optional[dict]) -> Optional[dict]:
        if b is None:
            return None
        out = {"claims": list(b.get("claims") or []), "rera_no": b.get("rera_no"), "pages": int(b.get("pages") or 0),
               "facts": dict(b.get("facts") or {}), "language": b.get("language") or "en"}
        if b.get("error"):
            out["error"] = b["error"]
        return out
