"""Area-insight reels: a short slide reel (1080x1920, navy and gold) about one area, made only from MahaRERA public records.

Input is `area_stats(db, key)` (app.modules.areastats, contract in docs/plan/pune-areas.md). Slides, in order:
  1. "<Area> in MahaRERA records" and the project count
  2. projects by the year of their filed completion date (when any)
  3. homes booked of homes registered (only when both numbers are known)
  4. projects recently listed or updated on MahaRERA (names only; never "newly registered")
  5. where to see every project: <site>/localities/<slug>
Every slide cites "Source: MahaRERA public records, as of <date>". No prices, predictions or "best". An area with fewer than
MIN_PROJECTS projects, or with too few facts for MIN_SLIDES slides, gets no reel (None): we never pad.

The slides are drawn with the creative Canvas, so `check()` can prove every text is inside the Reels safe zone, readable
(contrast >= 4.5) and not cut short. The video plays the slides with cross-fades through reels.compose.encode.
"""
import importlib
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Sequence

from PIL import Image

from app.core import areas as _areas
from app.core import brand
from app.modules.creative.layouts.base import Canvas, Rendered, violations
from app.modules.creative.layouts.palette import get as palette
from app.modules.newsroom.policy import MAHARERA_PHRASE
from app.modules.reels import compose as _compose
from app.modules.reels import slides as _slides
from app.platform.text import HYPE, PHONE

from .guards import PREDICT, PRICE

SIZE = _compose.W, _compose.H                     # 1080 x 1920
TOP, BOTTOM = _compose.TEXT_TOP, _compose.TEXT_BOTTOM  # no text above the top bar or below the caption line
LEFT, RIGHT = 84, _compose.TEXT_RIGHT             # 84 = the creative margin; right stops short of the like/share column
MIN_PROJECTS = 3
MIN_SLIDES = 4
MIN_CONTRAST = 4.5
MIN_FONT = 24
SECONDS_PER_SLIDE = 3.4
XFADE = 0.2  # a short blend into each slide (slides.py moved to plain cuts; area reels keep a soft change)
SOURCE = "MahaRERA public records"
SUBDIR = "calendar/areareels"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
# Wording the area reels must never use: claims about newness, rank or the future that the records do not make.
BANNED = re.compile(r"\b(newly registered|new launch\w*|launch\w*|upcoming|hot ?spot|must[- ]buy|invest now|top \d+)\b", re.I)


def _day(iso: str) -> str:
    try:
        d = date.fromisoformat(str(iso)[:10])
    except ValueError:
        return ""
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def _n(x: int) -> str:
    """Indian digit grouping is not needed for these sizes; a plain thousands comma reads the same everywhere."""
    return f"{int(x):,}"


def site_host() -> str:
    return re.sub(r"^https?://", "", brand.SITE)


def page_link(area: _areas.Area) -> str:
    """'avasetu.in/localities/wagholi': plain text, readable on a slide and in a caption."""
    return f"{site_host()}{area.page}"


def wording_problems(text: str) -> List[str]:
    """Why `text` may not appear on an area reel or its caption (empty list = fine)."""
    out = []
    for name, rx in (("hype", HYPE), ("price", PRICE), ("prediction", PREDICT), ("banned", BANNED), ("phone", PHONE)):
        m = rx.search(text or "")
        if m:
            out.append(f"{name} wording '{m.group(0)}'")
    return out


# ---- facts (pure) ---------------------------------------------------------------------------------------------------
@dataclass
class Slide:
    kicker: str
    headline: str
    big: str = ""             # a large number, gold
    label: str = ""           # what the number counts
    lines: List[str] = field(default_factory=list)


@dataclass
class AreaReel:
    key: str
    name: str
    as_of: str
    slides: List[Slide]
    caption_ig: str
    caption_fb: str
    hook: str

    @property
    def script(self) -> List[str]:
        out = []
        for s in self.slides:
            out.append(" ".join(x for x in (s.headline, s.big, s.label) if x))
            out += s.lines
        return out


def _safe_names(recent: Sequence[dict], n: int = 3) -> List[str]:
    """Project names as filed, dropping any name that trips a wording rule (a project called 'Best Homes' is left out, not reworded)."""
    out = []
    for r in recent or []:
        name = " ".join(str(r.get("name") or "").split())
        if name and not wording_problems(name) and name not in out:
            out.append(name)
        if len(out) == n:
            break
    return out


def slides_for(stats: Optional[dict]) -> Optional[List[Slide]]:
    """The slides for one area's stats, or None when the data is too thin for a reel."""
    if not stats:
        return None
    area = _areas.get(str((stats.get("area") or {}).get("key") or ""))
    projects = int(stats.get("projects") or 0)
    as_of = _day(stats.get("as_of") or "")
    if area is None or projects < MIN_PROJECTS or not as_of:
        return None
    kicker = f"{area.name.upper()} · PUNE"
    out = [Slide(kicker, f"{area.name} in MahaRERA records", _n(projects), "projects")]
    years = sorted((y for y in stats.get("completing") or [] if int(y.get("projects") or 0) > 0), key=lambda y: int(y["year"]))
    if years:
        top = max(years, key=lambda y: (int(y["projects"]), -int(y["year"])))
        rest = [f"{y['year']}: {_n(y['projects'])} project{'s' if int(y['projects']) != 1 else ''}" for y in years if y is not top][:2]
        out.append(Slide("COMPLETION DATES FILED", "Projects by filed completion year", _n(top["projects"]),
                         f"with a completion date in {top['year']}", rest))
    total, booked = stats.get("units_total"), stats.get("units_booked")
    if total is not None and booked is not None and 0 < int(total) and 0 <= int(booked) <= int(total):
        out.append(Slide("HOMES BOOKED", "Homes booked, as filed", f"{_n(booked)} of {_n(total)}", "homes in these projects"))
    names = _safe_names(stats.get("recent") or [])
    if names:
        out.append(Slide(MAHARERA_PHRASE.upper(), f"Recently {MAHARERA_PHRASE}", lines=names))
    out.append(Slide("SEE EVERY PROJECT", f"Every {area.name} project, with its source", lines=[page_link(area)]))
    return out if len(out) >= MIN_SLIDES else None


def captions(stats: dict, slides: List[Slide]) -> Dict[str, str]:
    """{'instagram': ..., 'facebook_page': ...}: one plain hook line, the facts, the source, the page link, the area's hashtags."""
    area = _areas.get(stats["area"]["key"])
    hook = f"{area.name} in MahaRERA records: {_n(stats['projects'])} projects."
    facts = []
    years = sorted((y for y in stats.get("completing") or [] if int(y.get("projects") or 0) > 0), key=lambda y: int(y["year"]))
    if years:
        facts.append("• Completion dates filed: " + ", ".join(f"{_n(y['projects'])} in {y['year']}" for y in years[:4]) + ".")
    if any(s.kicker == "HOMES BOOKED" for s in slides):
        facts.append(f"• Homes booked: {_n(stats['units_booked'])} of {_n(stats['units_total'])}.")
    names = _safe_names(stats.get("recent") or [])
    if names:
        facts.append(f"• Recently {MAHARERA_PHRASE}: " + ", ".join(names) + ".")
    source = f"Source: {SOURCE}, as of {_day(stats['as_of'])}."
    tags = " ".join(list(area.hashtags) + ["#MahaRERA", "#PuneProperty"])
    body = "\n\n".join([hook, "\n".join(facts), source]).strip()
    return {"instagram": f"{body}\n\nSee every project: {page_link(area)} (link in our bio).\n\n{tags}",
            "facebook_page": f"{body}\n\nSee every project: {brand.SITE}{area.page}\n\n{tags}"}


def reel_from_stats(stats: Optional[dict]) -> Optional[AreaReel]:
    slides = slides_for(stats)
    if slides is None:
        return None
    caps = captions(stats, slides)
    text = "\n".join([caps["instagram"], caps["facebook_page"]] + [" ".join([s.kicker, s.headline, s.big, s.label] + s.lines) for s in slides])
    if wording_problems(text):  # the stats themselves carried a word we may not say: no reel rather than a wrong one
        return None
    area = _areas.get(stats["area"]["key"])
    return AreaReel(area.key, area.name, str(stats["as_of"])[:10], slides, caps["instagram"], caps["facebook_page"],
                    caps["instagram"].splitlines()[0])


async def area_reel(db, key: str, stats_fn: Optional[Callable] = None) -> Optional[AreaReel]:
    """The reel for one area, or None (unknown area, no stats, thin data). `stats_fn` defaults to areastats.service.area_stats,
    imported here so the calendar loads even where that module is not deployed yet."""
    if stats_fn is None:
        try:  # by name: the areastats module (W1) may land after this one
            stats_fn = importlib.import_module("app.modules.areastats.service").area_stats
        except (ImportError, AttributeError):
            return None
    try:
        stats = await stats_fn(db, key)
    except Exception:
        return None
    return reel_from_stats(stats)


# ---- slides (drawn) -----------------------------------------------------------------------------------------------
def _source_line(as_of: str) -> str:
    return f"Source: {SOURCE}, as of {_day(as_of)}"


def draw(reel: AreaReel) -> List[Rendered]:
    """Each slide as a 1080x1920 Canvas: brand mark at the top of the text zone, the fact in the middle, the source at the bottom."""
    pal = palette("navy_gold")
    out = []
    w = RIGHT - LEFT
    for i, s in enumerate(reel.slides):
        c = Canvas(SIZE, pal, "area_insight", i, pattern="dots" if i % 2 == 0 else "rings")
        c.logo(LEFT, TOP, 64)
        c.text(brand.NAME, LEFT + 82, TOP + 14, 400, 34, "semibold", pal.ink, 1, role="brand", balance=False)
        y = TOP + 190
        c.chip(s.kicker, LEFT, y, size=28)
        y += 104
        y = c.text(s.headline, LEFT, y, w, 84, "bold", pal.ink, 3, min_size=52, role="hook" if i == 0 else "title") + 64
        if s.big:
            y = c.text(s.big, LEFT, y, w, (180 if s.lines else 260) if len(s.big) <= 6 else 128, "bold", pal.accent, 2, min_size=72, role="numeral") + 28
        if s.label:
            y = c.text(s.label, LEFT, y, w, 54, "semibold", pal.ink, 2, min_size=36) + 44
        for line in s.lines:
            if y > BOTTOM - 150:
                break
            c.rrect((LEFT, y - 4, LEFT + 10, y + 40), 5, pal.accent_fill)
            y = c.text(line, LEFT + 36, y, w - 36, 48, "semibold", pal.ink, 2, min_size=34) + 34
        c.text(_source_line(reel.as_of), LEFT, BOTTOM - 80, w, 30, "medium", pal.muted, 2, min_size=24, role="meta")
        out.append(c.finish())
    return out


def check(rendered: Sequence[Rendered]) -> List[str]:
    """Problems with drawn slides (empty = fine): creative safe area, the Reels text zone, contrast >= 4.5, no text cut short,
    no text below MIN_FONT."""
    out = []
    for r in rendered:
        tag = f"slide {r.index + 1}"
        out += [f"{tag}: {v}" for v in violations(r)]
        for it in r.items:
            if it.truncated:
                out.append(f"{tag}: '{it.text[:30]}' was cut short")
            if it.contrast < MIN_CONTRAST:
                out.append(f"{tag}: '{it.text[:30]}' contrast {it.contrast:.1f}")
            if it.size < MIN_FONT:
                out.append(f"{tag}: '{it.text[:30]}' is {it.size}px")
            x0, y0, x1, y1 = it.box
            if y0 < TOP or y1 > BOTTOM or x1 > RIGHT + 1:
                out.append(f"{tag}: '{it.text[:30]}' box {it.box} outside the Reels text zone")
    return out


def save_slides(reel: AreaReel, folder: Path) -> List[Path]:
    """Draw, check and save the slides as <folder>/<n>.jpg. Raises ValueError when a slide fails `check`."""
    rendered = draw(reel)
    problems = check(rendered)
    if problems:
        raise ValueError("; ".join(problems)[:600])
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for k, r in enumerate(rendered, 1):
        p = folder / f"{k}.jpg"
        r.img.convert("RGB").save(p, "JPEG", quality=90, optimize=True, progressive=True)
        paths.append(p)
    return paths


# ---- video ----------------------------------------------------------------------------------------------------------
def _frames(imgs: List[Image.Image], starts: List[float], seconds: float, total: float) -> Iterator[bytes]:
    """Each slide whole (its text is already inside the safe zone, so no zoom), cross-faded into the next."""
    for k in range(int(round(total * _compose.FPS))):
        t = k / _compose.FPS
        i = max(j for j in range(len(imgs)) if starts[j] <= t)
        img = imgs[i]
        if i > 0 and t < starts[i] + XFADE:
            img = Image.blend(imgs[i - 1], img, _compose.ease_in_out_cubic((t - starts[i]) / XFADE))
        yield img.tobytes()


def render_video(slide_paths: Sequence, out_path, music=None, encode: Callable = _compose.encode) -> Path:
    """The MP4 of the slides (reels.compose.encode: H.264 1080x1920 with the brand music) and its cover (slide 1) next to it."""
    imgs = []
    for p in slide_paths:
        with Image.open(p) as im:
            imgs.append(im.convert("RGB").resize(SIZE))
    if len(imgs) < 2:
        raise ValueError("an area reel needs at least two slides")
    starts, seconds, total = _slides.timeline(len(imgs), SECONDS_PER_SLIDE)
    out = encode(_frames(imgs, starts, seconds, total), total, out_path, music=music)
    imgs[0].save(_compose.cover_path(out), "JPEG", quality=86, optimize=True, progressive=True)
    return Path(out)
