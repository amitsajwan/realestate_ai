"""Ad-agency reels: every campaign post also goes out as a short reel built like a paid ad, not as a slideshow.

Why: on the Avasetu page 89.9% of views came from the Reels tab and 0.6% from the feed (Meta insights, 2026-10-10), so a post that
is only an image reaches almost nobody.

A reel is a `script` in one of FORMATS (showcase, price reveal, 3 reasons, nearby (pov), myth vs fact, checklist) and is rendered with compose:
  hook     the best picture at once, its line in big type in the middle third (no fade-in, no brand tag: frame one is content)
  beats    one short line per picture, a cut every ~1.5 s (most people watch muted and read)
  payoff   the fact the hook promised (the price, the RERA number), held back to the end so people watch to it
  cta      one action: a comment keyword, so leads per format are countable (calendar.tags reads "Comment WORD")
  loop     the hook picture again with no text, so the replay runs on without a jump (watch-through counts the replays)
  voice    every line is also spoken (reels.voice, Chirp 3 HD en-IN) over the music bed, which steps back under it; a scene lasts
           as long as its line takes to say, so a reel runs 15-20 s. Without a voice (no key, the service down) it is music only.
The words come from the LLM when it keeps to the facts (every number in a line must be in the facts, guards.problems_in finds
hype and predictions), else from the code's own template; the facts are always the code's.

Which format each reel takes: `for_posts` - the one that says what its post says (a price post is a price reveal, a MahaRERA
post a checklist, a nearby post the nearby reel). Only when that format is taken or lacks the facts does `pick` choose: 80% the
formats that brought the most value before (enquiries, then clicks, then views, from content_metrics and the interest links of
earlier ad reels), 20% another one.
"""
import logging
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .campaign import Ctx, _near, _numbers, buyer_place

log = logging.getLogger(__name__)

EXPERIMENT = "ad_reel"
FORMATS = ("showcase", "price_reveal", "three_reasons", "pov", "myth_fact", "checklist")
EXPLORE = 0.2
HOOK_WORDS, LINE_WORDS = 10, 8
HOOK_S, BEAT_S, PAYOFF_S, CTA_S, LOOP_S = 1.9, 1.5, 2.0, 1.8, 0.7   # the least each scene lasts; a spoken line makes it longer
VOICE_PAD_S = 0.45      # after a spoken line, before the next scene's cut
READY = re.compile(r"\bready\b|\bmove[\s-]*in\b|\bpossession\b|\bhanded\s+over\b|\bcompleted\b", re.I)
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
        name = buyer_place(c, key, p)
        if name and name not in seen and p.get("km") is not None:
            seen.add(name)
            out.append(f"{name}: {p['km']:g} km")
        if len(out) == n:
            break
    return out


def _size(c: Ctx) -> str:
    """One unit's size (Ctx.sqft never holds a layout's whole area), or ""."""
    return f"{int(c.sqft):,} sq ft" if c.sqft else ""


def _layout(c: Ctx) -> str:
    """"A 30-acre layout": the project's own area, said as the project's (never as a plot's)."""
    acres = c.v.get("total_acres")
    return f"A {float(acres):g}-acre layout" if c.layout and acres else ""


def _bhk(c: Ctx) -> str:
    b = c.v.get("bhk")
    return f"{float(b):g} BHK" if b and not c.plot else ""


def _amenities(c: Ctx, n: int = 3) -> List[str]:
    """The amenities the agent listed (the listing's own field, never a brochure claim nobody confirmed)."""
    a = c.v.get("amenities")
    return [str(x) for x in a if str(x).strip()][:n] if isinstance(a, list) else []


def _homes(c: Ctx) -> str:
    """"308 homes": MahaRERA's count (all the towers of a marketed project), said with the project's name."""
    u = c.v.get("units_total")
    return f"{int(u)} {'plots' if c.plot else 'homes'}" if u and c.project and c.maharera else ""


def _completion(c: Ctx) -> str:
    from .campaign import day, possession_card_ok
    now = c.v.get("possession_now")
    return f"Completion {day(now)[3:]} on MahaRERA" if now and possession_card_ok(c) else ""


def corpus(c: Ctx) -> str:
    """Every fact a line may state, as text (the guard's corpus: a number not in here is never said)."""
    bits = [c.where, _price(c), _size(c), _layout(c), _bhk(c), *_amenities(c, 8), _homes(c), _completion(c), *_places(c, 6),
            str(c.v.get("rera_no") or ""), str(c.v.get("possession_date") or ""), str(c.v.get("units_total") or ""),
            "1 2 3"]   # list numbers and "3 reasons" are the format's own
    return " | ".join(b for b in bits if b)


def eligible(c: Ctx) -> List[str]:
    """The formats this property has the facts for."""
    places = _places(c)
    ok = []
    if c.project and _price(c) and (_amenities(c) or _homes(c) or _bhk(c)):   # the project itself sells first
        ok.append("showcase")
    if _price(c) and (places or _size(c) or _layout(c) or c.registered):
        ok.append("price_reveal")
    if len([x for x in (_price(c), _size(c), _layout(c), c.registered, *places) if x]) >= 2:
        ok.append("three_reasons")
    if places:
        ok += ["pov", "myth_fact"]
    if c.registered:
        ok.append("checklist")
    return ok or ["three_reasons"]


# ---- the code's own scripts (always correct; the LLM only rewrites their words) ----------------------------------------------
def template(fmt: str, c: Ctx) -> Script:
    place = (c.locality or c.project or "Pune").split(",")[0].strip()   # "Malthan village", not "..., Shirur taluka"
    what = "plot" if c.plot else "home"
    price, size, places = _price(c), _size(c), _places(c)
    rera = f"MahaRERA {c.v['rera_no']}" if c.registered and c.v.get("rera_no") else ""
    cta = f"Comment {CTA_WORD} for a site visit"
    facts = [x for x in (size, _layout(c), *places, "MahaRERA registered" if c.registered else "") if x]
    if fmt == "showcase":
        lead = " ".join(x for x in (_bhk(c), "at" if _bhk(c) else "", c.project) if x)
        amen = _amenities(c)
        beats = [x for x in (
            (", ".join(amen[:-1]) + " and " + amen[-1] if len(amen) > 1 else (amen[0] if amen else "")),
            (f"{_homes(c)}, MahaRERA registered" if _homes(c) else ("MahaRERA registered" if c.registered else "")),
            size, _completion(c), *(places[:1])) if x][:4]
        return Script(fmt, f"{lead}, {place}", beats or facts[:3], f"*{price}*" if price else rera, cta)
    if fmt == "price_reveal":
        return Script(fmt, f"Guess the price of this {what} in {place}", facts[:3], f"*{price}*" if price else rera, cta)
    if fmt == "pov":   # the nearby reel (the id stays: earlier reels' scores are kept under it)
        return Script(fmt, f"What is near {c.project or place}?", places[:3] or facts[:3], price or rera, cta)
    if fmt == "myth_fact":
        return Script(fmt, f"Is {place} too far? Check the facts", places[:3], f"*{c.where or place}*", cta)
    if fmt == "checklist":
        return Script(fmt, f"Before you book a {what} in {place}, check 3 things",
                      ["1. The MahaRERA number", "2. The real plot size" if c.plot else "2. The real carpet area", "3. The distance to your work"],
                      f"*{c.v['rera_no']}* · {size}".strip(" ·") if size else f"*{c.v['rera_no']}*", cta)
    reasons = [x for x in ((f"{price}" if price else ""), size, _layout(c), *(places[:2]), "MahaRERA registered" if c.registered else "") if x][:3]
    reasons += ["Photos and location inside", "Ask us anything in the comments"][:max(0, 2 - len(reasons))]
    return Script("three_reasons", f"3 reasons buyers look at {place}", [f"{i + 1}. {r}" for i, r in enumerate(reasons)],
                  f"*{c.where or place}*", cta)


# ---- the LLM's wording, kept only when it keeps to the facts -------------------------------------------------------------
SYSTEM = (
    "You write a 15-20 second Instagram/Facebook Reel for an Indian property listing, like a top ad agency that sells homes. "
    "Every line is shown on screen AND spoken by a voice-over, so it must sound natural said aloud. "
    "Rules: the hook stops the scroll in under 1 second (at most 10 words: a question, a number, or a specific buyer fact); each beat is "
    "at most 8 words, one idea per picture; the payoff is the fact the hook promised; the cta asks to 'Comment " + CTA_WORD +
    "'. Sell the project first: its name, the configuration (BHK), the price, its amenities and its size or number of homes; "
    "a distance is a supporting beat, and do not use a hospital, school, market, bank or temple as the hook. "
    "No 'POV:' openers; it should sound like a Pune agent talking, not a list read from a database. "
    "Use ONLY the facts given: never a number, price, distance or name that is not in them, never a forecast of prices or "
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
    ready = bool(READY.search(facts))
    for line in s.lines():
        if set(_numbers(line)) - known:
            out.append(f"number not in facts: {line}")
        if READY.search(line) and not ready:   # "Your home is ready" for a project completing in 2030
            out.append(f"ready-to-move not in facts: {line}")
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


# the reel formats that say what a post of each campaign angle says, best first
FOR_ANGLE: Dict[str, Sequence[str]] = {
    "overview": ("showcase", "three_reasons"),
    "price_reveal": ("price_reveal",), "offer": ("price_reveal",), "emi": ("price_reveal",), "rate_per_sqft": ("price_reveal",),
    "rera_check": ("checklist",), "possession": ("checklist",), "plot_checklist": ("checklist",),
    "nearby": ("pov", "myth_fact"), "near_work": ("myth_fact", "pov"),
    "plot_myth": ("myth_fact",), "plot_or_flat": ("myth_fact",),
}
SHOWS_THE_PLACE = ("showcase", "three_reasons")   # amenities, plans, sizes, renders: the project itself


def for_posts(angles: Sequence[str], allowed: Sequence[str], scores: Dict[str, float],
              rng: Optional[random.Random] = None) -> List[Optional[str]]:
    """A format per post angle, never one twice: the first of FOR_ANGLE[angle] this property has the facts for; else the
    scored pick among those left; None when none is left (that post gets no ad reel)."""
    out: List[Optional[str]] = []
    for a in angles:
        left = [f for f in allowed if f not in out]
        fit = next((f for f in FOR_ANGLE.get(a, SHOWS_THE_PLACE) if f in left), None)
        out.append(fit or (pick(left, 1, scores, rng) or [None])[0])
    return out


def pick(allowed: Sequence[str], n: int, scores: Dict[str, float], rng: Optional[random.Random] = None) -> List[str]:
    """Up to n formats, never one twice (five checklist reels of one property say the same thing five times): each slot is the best-scoring format not used yet with 80% chance, a
    random other one with 20% (and unscored formats count as untried, so they are tried first)."""
    rng = rng or random.Random()
    out: List[str] = []
    for _ in range(min(n, len(allowed))):
        left = [f for f in allowed if f not in out]
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


XFADE = 0.25
_REGNO = re.compile(r"\b(?:P\d{11}|P[RPM]\d{13})\b", re.I)


def _distance(m: "re.Match") -> str:
    km = float(m.group(1))
    if km < 1:
        return "less than a kilometre"
    n = round(km)
    return "about 1 kilometre" if n == 1 else f"about {n} kilometres"


def spoken(line: str) -> str:
    """A screen line as the voice says it: no emphasis marks, no 15-character registration number read out, units in words."""
    t = line.replace("*", "").replace("·", ",")
    if _REGNO.search(t):
        t = re.sub(r"\(\s*\)", "", _REGNO.sub("", t)).strip(" ,.") or "MahaRERA registered"
    t = t.replace("₹", "rupees ")
    t = re.sub(r"\bsq\.?\s*ft\b", "square feet", t, flags=re.I)
    t = re.sub(r"(?:\babout\s+)?\b(\d+(?:\.\d+)?)\s*km\b", _distance, t)   # as people say it: "less than a kilometre", "about 4 kilometres"
    t = re.sub(r"\bkm\b", "kilometres", t)
    t = re.sub(r"^\d{1,2}\.\s+(?!\d)", "", t)   # "1. The MahaRERA number": the list number is for the eye ("0.9 km" was said "9 km")
    return " ".join(t.split()).strip(" ,") or "MahaRERA registered"


def render(s: Script, pictures: Sequence, dest: Path, kicker: Optional[str] = None, voiced: bool = True,
           lang: str = "en") -> Dict[str, Any]:
    """The reel at `dest`: each line on screen and spoken (when the voice service answers), a scene as long as its line.
    {"path", "voice": "take"|"lines"|"off"|"failed", "seconds"}."""
    import shutil
    import tempfile

    from app.modules.reels import ffmpeg, narration, voice
    from app.modules.reels.compose import make_reel, plan
    from app.modules.reels.music import write as write_music

    sc = scenes(s, pictures, kicker)
    lines = s.lines()   # hook, beats, payoff, cta: scenes 0..len(lines)-1; the last scene (the loop) is silent
    work = Path(tempfile.mkdtemp(prefix="ad-reel-"))
    audio, how = None, "off"
    try:
        if voiced and voice.available():
            try:
                clips, how = narration.voice_lines([spoken(x) for x in lines], lang, work)
                for i, clip in enumerate(clips):
                    sc[i].seconds = max(sc[i].seconds or 0.0, ffmpeg.probe(clip).duration + VOICE_PAD_S)
                tl = plan([x.seconds for x in sc], XFADE)
                audio = narration.mix(work, clips, tl.starts[:len(clips)], tl.total,
                                      write_music(work / "bed.wav", seconds=tl.total + 1.0))
            except voice.VoiceError as e:
                log.warning("ad reel: no voice-over (%s); music only", e)
                how, audio = "failed", None
                for x, d in zip(sc, (HOOK_S, *[BEAT_S] * len(s.beats), PAYOFF_S, CTA_S, LOOP_S)):
                    x.seconds = d
        make_reel(sc, dest, music=audio, xfade=XFADE, progress=False, end_card=False, hook_tag=False)
        return {"path": dest, "voice": how, "seconds": round(plan([x.seconds for x in sc], XFADE).total, 1)}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def caption(s: Script, post_caption: str) -> str:
    """The post's caption under the reel's hook, with the comment keyword asked for (so leads per format are counted)."""
    body = post_caption.strip()
    ask = f"Comment {CTA_WORD} and we will share the details and a site-visit slot."
    return f"{s.hook.replace('*', '')}\n\n{body}" + ("" if CTA_WORD in body else f"\n\n{ask}")
