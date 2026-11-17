"""Gemini vision judges a candidate photo (docs/plan/area-pictures.md step 4, the photo scout). Rules decide what is even
shown to the model (`commons.py`); the model only says what a hard rule cannot: whether this is really a photo of the
place outdoors, what it shows, and whether it is good enough to use. Metered on the enrichment's Gemini budget
(areastats.budget) the way propertyfacts.brochure_once reads a brochure: a call that the day's budget has no room for is
never made, and a candidate with no verdict is never suggested.
"""
import io
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from app.modules.areastats import budget
from app.platform import gemini

log = logging.getLogger(__name__)


@dataclass
class _Cost:
    """One judge call's tokens and rupees, the same shape propertyfacts.brochure_once meters a brochure read with."""
    tokens_in: int = 0
    tokens_out: int = 0
    calls: int = 0
    inr: float = 0.0
    usd_inr: float = field(default_factory=lambda: budget.load().usd_inr)

    def add(self, usage: Dict[str, Any]) -> None:
        self.calls += 1
        self.tokens_in += int(usage.get("tokens_in") or 0)
        self.tokens_out += int(usage.get("tokens_out") or 0)
        self.inr += budget.cost_inr(str(usage.get("model") or ""), int(usage.get("tokens_in") or 0),
                                    int(usage.get("tokens_out") or 0), self.usd_inr)

DOWNSCALE_SIDE = 1024     # sent to the model; the kept photo stays full size
SHOWS = ("main_road", "metro", "office_park", "skyline", "market", "landmark", "residential", "nature", "other")
# variety ranking: a main road or the metro says more to a buyer than another skyline; ties keep the Commons order
SHOWS_RANK = {s: i for i, s in enumerate(("main_road", "metro", "office_park", "skyline", "landmark", "market", "residential"))}
MIN_QUALITY = 3

PROMPT = ("You are judging whether a photo may be shown on a Pune real-estate area guide page. The area is {area}. Answer "
         "ONLY this JSON object, nothing else: {{\"is_outdoor_photo_of_place\": true only when this is a real outdoor photo "
         "of a street, building, road, station or similar place (false for an indoor photo, a map, a document, a drawing, "
         "a close-up of a plant or animal, or a photo that could be anywhere), \"shows\": one or more of "
         "[\"main_road\", \"metro\", \"office_park\", \"skyline\", \"market\", \"landmark\", \"residential\", \"nature\", "
         "\"other\"] naming what is in the photo, \"faces_prominent\": true when a person's face is a main subject of the "
         "photo (small people in the distance on a street do not count), \"watermark_or_text_overlay\": true when any "
         "watermark, logo, caption or text is drawn over the photo, \"interior\": true when the photo is taken indoors, "
         "\"quality\": 1 to 5 for how clear, well-lit and usable the photo is on a real page, \"caption_hint\": a plain "
         "English phrase of at most 12 words saying what the photo shows (no names of people, builders or projects, "
         "nothing not visible in the photo).}}")


@dataclass(frozen=True)
class Verdict:
    ok: bool
    why: str
    shows: Tuple[str, ...] = ()
    quality: int = 0
    caption_hint: str = ""


def _downscale(data: bytes) -> bytes:
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((DOWNSCALE_SIDE, DOWNSCALE_SIDE), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "JPEG", quality=80)
    return out.getvalue()


def _parse(answer: Any) -> Verdict:
    if not isinstance(answer, dict):
        return Verdict(False, "model answered without a usable object")
    if answer.get("is_outdoor_photo_of_place") is not True:
        return Verdict(False, "not an outdoor photo of the place")
    if answer.get("faces_prominent") is True:
        return Verdict(False, "a face is the main subject")
    if answer.get("watermark_or_text_overlay") is True:
        return Verdict(False, "a watermark or text is drawn on it")
    if answer.get("interior") is True:
        return Verdict(False, "taken indoors")
    try:
        quality = int(answer.get("quality") or 0)
    except (TypeError, ValueError):
        quality = 0
    if quality < MIN_QUALITY:
        return Verdict(False, f"quality {quality} of 5")
    shows = tuple(s for s in (answer.get("shows") or []) if s in SHOWS) or ("other",)
    hint = " ".join(str(answer.get("caption_hint") or "").split())[:160]
    return Verdict(True, f"shows {', '.join(shows)}; quality {quality} of 5", shows, quality, hint)


async def judge(db, now, area_name: str, image: bytes, cfg: Optional[budget.Config] = None) -> Tuple[Optional[Verdict], str]:
    """(verdict, "") on a model answer (verdict.ok says whether to use the photo); (None, why) when no model could be
    asked at all (the day's Gemini budget is spent, or no key is set) -- never suggest an unjudged photo."""
    day = await budget.today(db, now, cfg)
    if day["gemini_inr"] >= day["gemini_inr_cap"]:
        return None, "the day's Gemini budget is spent"
    if not gemini.available():
        return None, "no Gemini key is set"
    cost = _Cost(usd_inr=(cfg or budget.load()).usd_inr)
    try:
        small = _downscale(image)
    except Exception as e:
        return None, f"the picture could not be read ({type(e).__name__})"
    try:
        answer, usage = await gemini.read_counted([small], PROMPT.format(area=area_name))
        cost.add(usage)
        return _parse(answer), ""
    except gemini.GeminiError as e:
        return None, f"the model did not answer ({e})"
    finally:
        if cost.calls:
            await budget.spend(db, now, cost.inr, cost.calls, cost.tokens_in, cost.tokens_out, "photo_scout")


def rank_key(verdict: Verdict) -> Tuple[int, int]:
    """Lower sorts first: the best-ranked `shows` tag, then higher quality first."""
    best = min((SHOWS_RANK.get(s, len(SHOWS_RANK)) for s in verdict.shows), default=len(SHOWS_RANK))
    return (best, -verdict.quality)


def pick_variety(judged: List[Tuple[Any, Verdict]], limit: int) -> List[Tuple[Any, Verdict]]:
    """Up to `limit` judged (candidate, verdict) pairs, ranked by `rank_key`, without two photos that show only the same
    one thing once a more varied pick is available (Baner's fifth main-road photo loses to its first market photo)."""
    ordered = sorted(judged, key=lambda cv: rank_key(cv[1]))
    out: List[Tuple[Any, Verdict]] = []
    seen_shows: set = set()
    rest: List[Tuple[Any, Verdict]] = []
    for cv in ordered:
        top = next(iter(cv[1].shows), "other")
        if top not in seen_shows:
            seen_shows.add(top)
            out.append(cv)
        else:
            rest.append(cv)
        if len(out) >= limit:
            return out[:limit]
    return (out + rest)[:limit]
