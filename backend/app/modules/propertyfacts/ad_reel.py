"""Ad-agency reels: every campaign post also goes out as a short reel built like a paid ad, not as a slideshow.

Why: on the Avasetu page 89.9% of views came from the Reels tab and 0.6% from the feed (Meta insights, 2026-10-10), so a post that
is only an image reaches almost nobody.

A reel is a `script` in one of FORMATS (price reveal, 3 reasons, POV, myth vs fact, checklist) and is rendered with compose:
  hook     the best picture at once, its line in big type in the middle third (no fade-in, no brand tag: frame one is content)
  beats    one short line per picture, a cut every ~1.5 s (most people watch muted and read)
  payoff   the fact the hook promised (the price, the RERA number), held back to the end so people watch to it
  cta      one action: a comment keyword, so leads per format are countable (calendar.tags reads "Comment WORD")
  loop     the hook picture again with no text, so the replay runs on without a jump (watch-through counts the replays)
The words come from the LLM when it keeps to the facts (every number in a line must be in the facts, guards.problems_in finds
hype and predictions), else from the code's own template; the facts are always the code's.

Which formats a campaign makes: `pick` - 80% the formats that brought the most value before (enquiries, then clicks, then
views, from content_metrics and the interest links of earlier ad reels), 20% another one, so nothing goes stale.
"""
import logging
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .campaign import Ctx, _near, _numbers

log = logging.getLogger(__name__)

EXPERIMENT = "ad_reel"
FORMATS = ("price_reveal", "three_reasons", "pov", "myth_fact", "checklist")
EXPLORE = 0.2
HOOK_WORDS, LINE_WORDS = 10, 8
HOOK_S, BEAT_S, PAYOFF_S, CTA_S, LOOP_S = 1.9, 1.5, 2.0, 1.8, 0.7
CTA_WORD = "VISIT"


@dataclass
class Script:
    format: str
    hook: str
    beats: List[str]
    payoff: str
    cta: str
    by: str = "template"   # template | llm
    hook_type: str = "statement"
    extra: Dict[str, Any] = field(default_factory=dict)

    def lines(self) -> List[str]:
        return [self.hook, *self.beats, self.payoff, self.cta]

    def out(self) -> Dict[str, Any]:
        return {"format": self.format, "hook": self.hook, "beats": self.beats, "payoff": self.payoff, "cta": self.cta,
                "by": self.by, "hook_type": self.hook_type}


# ---- the facts a reel may say ---------------------------------------------------------------------------------------------
def _price(c: Ctx) -> str:
    from app.modules.creative.listing_brief import price_label
    p = c.v.get("price_inr")
    return ("from " if c.layout else "") + price_label(int(p)) if p else ""


def _places(c: Ctx, n: int = 3) -> List[str]:
    out, seen = [], set()
    for key, p in _near(c):
        name = c.place(key, p)
        if name and name not in seen and p.get("km") is not None:
            seen.add(name)
            out.append(f"{name}: {p['km']:g} km")
        if len(out) == n:
            break
    return out


MAX_PLOT_SQFT = 20_000   # half an acre: a bigger "plot size" is the whole layout's area typed in the size field


def _size(c: Ctx) -> str:
    """One unit's size, or "" when unsure: a layout's size only from size_min_sqft (its carpet/plot field is often the whole
    layout - live 2026-10-10, Gulmohar City: 1,306,800 sq ft = its 30 acres, said as the plot size)."""
    sqft = c.v.get("size_min_sqft") if c.layout else c.sqft
    if not sqft or (c.plot or c.layout) and float(sqft) > MAX_PLOT_SQFT:
        return ""
    return f"{int(sqft):,} sq ft"


def corpus(c: Ctx) -> str:
    """Every fact a line may state, as text (the guard's corpus: a number not in here is never said)."""
    bits = [c.where, _price(c), _size(c), *_places(c, 6), str(c.v.get("rera_no") or ""), str(c.v.get("possession_date") or ""),
            str(c.v.get("units_total") or ""), "1 2 3"]   # list numbers and "3 reasons" are the format's own
    return " | ".join(b for b in bits if b)


def eligible(c: Ctx) -> List[str]:
    """The formats this property has the facts for."""
    places = _places(c)
    ok = []
    if _price(c) and (places or _size(c)):
        ok.append("price_reveal")
    if len([x for x in (_price(c), _size(c), c.registered, *places) if x]) >= 3:
        ok.append("three_reasons")
    if places:
        ok += ["pov", "myth_fact"]
    if c.registered:
        ok.append("checklist")
    return ok or ["three_reasons"]


# ---- the code's own scripts (always correct; the LLM only rewrites their words) ----------------------------------------------
def template(fmt: str, c: Ctx) -> Script:
    place = c.locality or c.project or "Pune"
    what = "plot" if c.plot else "home"
    price, size, places = _price(c), _size(c), _places(c)
    rera = f"MahaRERA {c.v['rera_no']}" if c.registered else ""
    cta = f"Comment {CTA_WORD} for a site visit"
    facts = [x for x in (size, *places, "MahaRERA registered" if c.registered else "") if x]
    if fmt == "price_reveal":
        return Script(fmt, f"Guess the price of this {what} in {place}", facts[:3], f"*{price}*" if price else rera, cta)
    if fmt == "pov":
        first = places[0].split(":")[0] if places else place
        return Script(fmt, f"POV: {first} is minutes from your new {what}", places[:3] or facts[:3], price or rera, cta)
    if fmt == "myth_fact":
        return Script(fmt, f"Is {place} too far? Check the facts", places[:3], f"*{c.where or place}*", cta)
    if fmt == "checklist":
        return Script(fmt, f"Before you book a {what} in {place}, check 3 things",
                      ["1. The MahaRERA number", "2. The real carpet area", "3. The distance to your work"],
                      f"*{c.v['rera_no']}* · {size}".strip(" ·") if size else f"*{c.v['rera_no']}*", cta)
    reasons = [x for x in ((f"{price}" if price else ""), size, *(places[:2]), "MahaRERA registered" if c.registered else "") if x][:3]
    reasons += ["Photos and location inside", "Ask us anything in the comments"][:max(0, 2 - len(reasons))]
    return Script("three_reasons", f"3 reasons buyers look at {place}", [f"{i + 1}. {r}" for i, r in enumerate(reasons)],
                  f"*{c.where or place}*", cta)


# ---- the LLM's wording, kept only when it keeps to the facts -------------------------------------------------------------
SYSTEM = (
    "You write the on-screen text of a 12-second Instagram/Facebook Reel for an Indian property listing, like a top ad agency. "
    "Rules: the hook stops the scroll in under 1 second (at most 10 words: a question, a number, or 'POV: ...'); each beat is "
    "at most 8 words, one idea per picture; the payoff is the fact the hook promised; the cta asks to 'Comment " + CTA_WORD +
    "'. Use ONLY the facts given: never a number, price, distance or name that is not in them, never a forecast of prices or "
    "returns, no hype words (best, luxurious, dream, guaranteed). Plain English a Pune buyer speaks. "
    "Reply with JSON only: {\"hook\": \"...\", \"beats\": [\"...\", \"...\", \"...\"], \"payoff\": \"...\", \"cta\": \"...\"}")


def hook_type(hook: str) -> str:
    h = hook.lower()
    if h.startswith("pov"):
        return "pov"
    if "guess" in h or "price" in h and "?" in h:
        return "price_reveal"
    if "?" in hook:
        return "question"
    return "number" if re.search(r"\d", hook) else "statement"


def check(s: Script, facts: str) -> List[str]:
    """Why a script must not be used ([] = fine): too long, a number not in the facts, or a guard problem."""
    from app.modules.creative.guards import problems_in
    out: List[str] = []
    if not s.hook or len(s.hook.split()) > HOOK_WORDS or not 2 <= len(s.beats) <= 5:
        out.append("shape")
    if any(len(b.replace("*", "").split()) > LINE_WORDS + 2 for b in [*s.beats, s.payoff]):
        out.append("long line")
    known = set(_numbers(facts))
    for line in s.lines():
        if set(_numbers(line)) - known:
            out.append(f"number not in facts: {line}")
        out += problems_in(line.replace("*", ""), facts)
    return out


async def write(fmt: str, c: Ctx, llm: Any = None) -> Script:
    """The script for `fmt`: the LLM's when it passes `check`, else the template's."""
    base = template(fmt, c)
    base.hook_type = hook_type(base.hook)
    if llm is None:
        return base
    facts = corpus(c)
    try:
        r = await llm.json(SYSTEM, f"Format: {fmt.replace('_', ' ')}\nFacts: {facts}\nA plain version to beat:\n"
                                   + "\n".join(base.lines())) or {}
        s = Script(fmt, str(r.get("hook") or "").strip(), [str(b).strip() for b in r.get("beats") or [] if str(b).strip()][:5],
                   str(r.get("payoff") or "").strip(), str(r.get("cta") or base.cta).strip(), by="llm")
    except Exception:
        log.info("ad reel: LLM script failed for %s", fmt, exc_info=True)
        return base
    if CTA_WORD not in s.cta:
        s.cta = base.cta
    problems = check(s, facts)
    if problems:
        log.info("ad reel: LLM script for %s dropped: %s", fmt, problems[:3])
        return base
    s.hook_type = hook_type(s.hook)
    return s


# ---- which formats: 80% what worked, 20% something else ------------------------------------------------------------------
def value(m: Dict[str, Any]) -> float:
    """What one reel brought: an enquiry is worth far more than a view."""
    return 50.0 * m.get("interests", 0) + 5.0 * m.get("clicks", 0) + m.get("views", 0) / 100.0


def pick(allowed: Sequence[str], n: int, scores: Dict[str, float], rng: Optional[random.Random] = None) -> List[str]:
    """n formats (repeats allowed when n > len(allowed)): each slot is the best-scoring format not used yet with 80% chance, a
    random other one with 20% (and unscored formats count as untried, so they are tried first)."""
    rng = rng or random.Random()
    out: List[str] = []
    for _ in range(n):
        left = [f for f in allowed if f not in out] or list(allowed)
        untried = [f for f in left if f not in scores]
        if untried:
            out.append(untried[0])
        elif rng.random() < EXPLORE and len(left) > 1:
            out.append(rng.choice(sorted(left, key=lambda f: -scores[f])[1:]))
        else:
            out.append(max(left, key=lambda f: scores[f]))
    return out


async def scores(db) -> Dict[str, float]:
    """Mean value per format over earlier ad reels that have results: enquiries and clicks from their interest links, views
    from their latest insights snapshot. {} when nothing has run yet (every format is then untried)."""
    from app.modules.interest.store import Store as InterestStore
    links = InterestStore(db)
    per: Dict[str, List[float]] = {}
    try:
        rows = await db.get_collection("content_calendar").find({"creative.experiment": EXPERIMENT, "status": "published"}).to_list(500)
        for row in rows:
            fmt = (row.get("creative") or {}).get("variant")
            if fmt not in FORMATS:
                continue
            channel = "instagram" if row["channel"] == "instagram" else "facebook"
            link = await links.find_link("post", row["slug"], channel)
            snap = await db.get_collection("content_metrics").find({"post_id": row["_id"]}).sort("at", -1).limit(1).to_list(1)
            mets = (snap[0].get("metrics") if snap else None) or {}
            views = max([v for k, v in mets.items() if isinstance(v, (int, float)) and k in ("views", "plays", "reach", "ig_reels_aggregated_all_plays_count", "post_video_views")] or [0])
            per.setdefault(fmt, []).append(value({
                "interests": await links.count(link["code"], "interest") if link else 0,
                "clicks": await links.count(link["code"], "click") if link else 0, "views": views}))
    except Exception:
        log.warning("ad reel: scores unavailable, every format counts as untried", exc_info=True)
        return {}
    return {f: sum(v) / len(v) for f, v in per.items() if v}


# ---- the video -----------------------------------------------------------------------------------------------------------
def scenes(s: Script, pictures: Sequence, kicker: Optional[str] = None) -> list:
    """compose scenes for a script: hook, one beat per picture, payoff, cta, then the hook picture again (the loop)."""
    from app.modules.reels.compose import Scene, TextLine
    pics = list(pictures) or [None]
    at = lambda i: pics[i % len(pics)]   # noqa: E731
    out = [Scene(image=at(0), lines=[TextLine(s.hook, size=108, max_lines=4)], kicker=kicker, seconds=HOOK_S, seed="ad-hook")]
    for i, b in enumerate(s.beats):
        out.append(Scene(image=at(i + 1), lines=[TextLine(b, size=86, max_lines=3)], seconds=BEAT_S, seed=f"ad-beat-{i}"))
    out.append(Scene(image=at(len(s.beats) + 1), lines=[TextLine(s.payoff, size=112, max_lines=3)], seconds=PAYOFF_S, seed="ad-payoff"))
    out.append(Scene(image=None, lines=[TextLine(s.cta, size=84, max_lines=3)], kicker=kicker, seconds=CTA_S, seed="ad-cta"))
    out.append(Scene(image=at(0), lines=[], seconds=LOOP_S, seed="ad-hook"))
    return out


def render(s: Script, pictures: Sequence, dest: Path, kicker: Optional[str] = None) -> Path:
    from app.modules.reels.compose import make_reel
    return make_reel(scenes(s, pictures, kicker), dest, xfade=0.25, progress=False, end_card=False, hook_tag=False)


def caption(s: Script, post_caption: str) -> str:
    """The post's caption under the reel's hook, with the comment keyword asked for (so leads per format are counted)."""
    body = post_caption.strip()
    ask = f"Comment {CTA_WORD} and we will share the details and a site-visit slot."
    return f"{s.hook.replace('*', '')}\n\n{body}" + ("" if CTA_WORD in body else f"\n\n{ask}")
