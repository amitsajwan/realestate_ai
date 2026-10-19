"""Date-watch reels: MahaRERA completion dates that moved, for projects where homes are already booked. Facts only, from the register.

Two kinds, both planned by the system itself (`autoplan`, called once a day by the calendar loop) as PLANNED rows the owner approves:
  board  (Monday)    "<Area>: booked homes, completion dates moved the most": the top projects of one area (or all of Pune the
                     first time), rotating so every area gets its turn. Ranked by months moved, net of MahaRERA's COVID extension.
  moved  (Thursday)  "New completion dates filed": projects whose filed date changed since the last week (register
                     `completion_history`, written by areastats.refresh). Nothing changed means no reel, never filler.

Who is in (all automatic, `candidate`): in one of our areas, a residential project, at least one home booked, the filed completion
date still ahead (families waiting), and for the board at least MIN_NET_MONTHS moved after the COVID extension and MIN_BOOKED homes booked. A move above
REVIEW_OVER_MONTHS is held back for the owner to look at (often a phase renamed or re-registered, not a real move); a project is
not shown again within REPEAT_DAYS. Names that trip a wording rule are left out, not reworded.

Wording: the slides and captions state the two filed dates, homes booked and the RERA number, with the source and its date. Never
"delayed by", "stuck", "scam" or any word about the builder: the record says the date moved, and that is all we say.
Slides are area_reels.Slide, drawn and checked by area_reels.save_slides, played by area_reels.render_video.
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from app.core import areas as _areas
from app.core import brand
from app.modules.areastats.pages import booked as _booked
from app.modules.areastats.pages import EXTENSION_MONTHS, months_later
from app.modules.areastats.service import _count, _day as _iso

from .area_reels import SOURCE, Slide, _day, _n, save_slides, site_host, wording_problems

log = logging.getLogger(__name__)

PREFIX = "datewatch"
SUBDIR = "calendar/datewatch"
MIN_NET_MONTHS = 12        # board: moved at least a year, after the COVID extension
MIN_BOOKED = 10            # board: enough homes booked for "families are waiting" to be the story
REVIEW_OVER_MONTHS = 72    # moves above six years go to the owner first (phase renames, re-registrations)
COVID_MONTHS = 9           # MahaRERA's force majeure extensions (6 + 3 months) for projects live in 2020-21
COVID_FIRST_DATE = "2020-03-15"
COVID_REGISTERED_BEFORE = "2021-07-01"
REPEAT_DAYS = 60
BOARD_SIZE = 4
MIN_BOARD = 3
MOVED_MAX = 4
BOARD_WEEKDAY, MOVED_WEEKDAY = 0, 3   # Monday, Thursday
AT = time(21, 0)                      # IST: buyers scroll after work
CHANNELS = ("instagram", "facebook_page")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _month(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.year}"


def covid_months(doc: dict) -> int:
    """The extension MahaRERA gave every project whose completion fell in the pandemic: counted out of the move."""
    first = _iso(doc.get("completion_at_registration"))
    reg = _iso(doc.get("registered_on")) or first
    return COVID_MONTHS if first and first >= COVID_FIRST_DATE and reg and reg < COVID_REGISTERED_BEFORE else 0


def residential(doc: dict) -> bool:
    t = str(doc.get("project_type") or "").lower()
    return not t or "resid" in t


def _name(doc: dict) -> str:
    return " ".join(str(doc.get("name") or "").split())


def candidate(doc: dict, today: date) -> Optional[dict]:
    """The facts of one project for a date-watch reel, or None when it does not qualify (any board threshold aside)."""
    area = _areas.get(str(doc.get("locality") or ""))
    first, now = _iso(doc.get("completion_at_registration")), _iso(doc.get("completion_now"))
    sold, total = _booked(doc), _count(doc.get("units_total"))
    name = _name(doc)
    if area is None or not residential(doc) or not first or not now or now <= today.isoformat():
        return None
    if not sold or not total or sold > total or not name or wording_problems(name):
        return None
    moved = months_later(doc) or 0
    covid = covid_months(doc)
    return {"regno": doc.get("regno") or doc["_id"], "name": name, "area": area.key, "area_name": area.name,
            "first": first, "now": now, "booked": sold, "total": total, "moved": moved, "covid": covid,
            "net": max(0, moved - covid), "slug": doc.get("page_slug") or "", "review": moved > REVIEW_OVER_MONTHS,
            "history": list(doc.get("completion_history") or [])}


def candidates(docs: Iterable[dict], today: date) -> List[dict]:
    """Every qualifying project, most moved first (net of COVID), then most homes booked."""
    out = [c for c in (candidate(d, today) for d in docs) if c]
    return sorted(out, key=lambda c: (-c["net"], -c["booked"], c["name"]))


def board_rows(cands: Sequence[dict], area: str = "", skip: Iterable[str] = ()) -> List[dict]:
    skip = set(skip)
    return [c for c in cands if (not area or c["area"] == area) and c["net"] >= MIN_NET_MONTHS and not c["review"]
            and c["booked"] >= MIN_BOOKED and c["regno"] not in skip][:BOARD_SIZE]


def held_for_review(cands: Sequence[dict]) -> List[dict]:
    return [c for c in cands if c["review"] and c["net"] >= MIN_NET_MONTHS]


def recent_moves(cands: Sequence[dict], since: datetime) -> List[dict]:
    """Projects whose filed completion date moved LATER since `since`, with that move as `last` ({from, to, seen_at})."""
    out = []
    for c in cands:
        moves = [m for m in c["history"] if isinstance(m.get("seen_at"), datetime) and _aware(m["seen_at"]) >= since
                 and str(m.get("to")) > str(m.get("from"))]
        if moves and not c["review"]:
            out.append({**c, "last": moves[-1]})
    return sorted(out, key=lambda c: (-c["booked"], c["name"]))[:MOVED_MAX]


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


# ---- the reel ------------------------------------------------------------------------------------------------------
@dataclass
class DateWatchReel:
    key: str              # 'board-wagholi', 'board-pune', 'moved'
    kind: str
    area: str
    as_of: str
    hook: str
    slides: List[Slide]
    caption_ig: str
    caption_fb: str
    regnos: List[str]

    @property
    def script(self) -> List[str]:
        out = []
        for s in self.slides:
            out.append(" ".join(x for x in (s.headline, s.big, s.label) if x))
            out += s.lines
        return out

    def slug(self, day: date) -> str:
        return f"{PREFIX}-{self.key}-{day:%Y%m%d}"


def _project_slide(c: dict, kicker: str, was: Optional[str] = None) -> Slide:
    # three short lines: a fourth runs into the source line (the COVID note is in the caption)
    lines = [f"{'Was' if was else 'First filed'}: {_month(was or c['first'])}", f"{_n(c['booked'])} of {_n(c['total'])} homes booked",
             f"RERA {c['regno']}"]
    return Slide(kicker, c["name"], _month(c["now"]), "completion date filed now", lines)


def _check_slide() -> Slide:
    return Slide("CHECK YOUR PROJECT", "Every project's dates, with its MahaRERA source", lines=[f"{site_host()}/projects"])


def _captions(hook: str, rows: Sequence[dict], as_of: str, tags: Sequence[str], was_key: Optional[str] = None) -> Dict[str, str]:
    facts = []
    for c in rows:
        was = c["last"]["from"] if was_key else c["first"]
        facts.append(f"• {c['name']} ({c['area_name']}, RERA {c['regno']}): {_month(was)} → {_month(c['now'])}. "
                     f"{_n(c['booked'])} of {_n(c['total'])} homes booked.")
    note = ("Dates as filed on MahaRERA. Moves of projects live in 2020-21 include MahaRERA's COVID extension of up to "
            f"{COVID_MONTHS} months; most dates also carry the {EXTENSION_MONTHS} months MahaRERA added in August 2026.")
    source = f"Source: {SOURCE}, as of {_day(as_of)}."
    body = "\n\n".join([hook, "\n".join(facts), note, source, "Booked here? Check your project's dates:"])
    tagline = " ".join(list(tags) + ["#MahaRERA", "#PuneProperty", "#HomeBuyers"])
    return {"instagram": f"{body} {site_host()}/projects (link in our bio).\n\n{tagline}",
            "facebook_page": f"{body} {brand.SITE}/projects\n\n{tagline}"}


def _finish(key: str, kind: str, area: str, as_of: str, hook: str, slides: List[Slide], caps: Dict[str, str],
            rows: Sequence[dict]) -> Optional[DateWatchReel]:
    text = "\n".join(list(caps.values()) + [" ".join([s.kicker, s.headline, s.big, s.label] + s.lines) for s in slides])
    problems = wording_problems(text)
    if problems:
        log.warning("datewatch: %s dropped: %s", key, problems)
        return None
    return DateWatchReel(key, kind, area, as_of, hook, slides, caps["instagram"], caps["facebook_page"], [c["regno"] for c in rows])


def board(cands: Sequence[dict], area: str, as_of: str, skip: Iterable[str] = ()) -> Optional[DateWatchReel]:
    """The board for one area ('' = all of Pune), or None with fewer than MIN_BOARD projects."""
    rows = board_rows(cands, area, skip)
    if len(rows) < MIN_BOARD:
        return None
    a = _areas.get(area) if area else None
    place = a.name if a else "Pune"
    hook = f"{place}: homes already booked, and these completion dates moved the most on MahaRERA."
    slides = [Slide(f"{place.upper()} · RERA DATE WATCH", "Booked a home here? These completion dates moved the most",
                    str(len(rows)), "projects, homes already booked", ["Dates as filed on MahaRERA"])]
    slides += [_project_slide(c, f"#{i} · {c['area_name'].upper()}") for i, c in enumerate(rows, 1)]
    slides.append(_check_slide())
    tags = list(a.hashtags) if a else ["#Pune", "#PuneRealEstate"]
    return _finish(f"board-{area or 'pune'}", "board", area, as_of, hook, slides, _captions(hook, rows, as_of, tags), rows)


def moved(cands: Sequence[dict], since: datetime, as_of: str) -> Optional[DateWatchReel]:
    """'New completion dates filed' for the moves seen since `since`, or None when there were none."""
    rows = recent_moves(cands, since)
    if not rows:
        return None
    hook = "New completion dates filed on MahaRERA this week, for projects where homes are already booked."
    slides = [Slide("PUNE · RERA DATE WATCH", "New completion dates filed this week", str(len(rows)),
                    "projects, homes already booked", ["Dates as filed on MahaRERA"])]
    slides += [_project_slide(c, c["area_name"].upper(), was=c["last"]["from"]) for c in rows]
    slides.append(_check_slide())
    tags = list(dict.fromkeys(t for c in rows for t in _areas.get(c["area"]).hashtags[:1]))
    return _finish("moved", "moved", "", as_of, hook, slides, _captions(hook, rows, as_of, tags, was_key="last"), rows)


# ---- planning (the system does it itself) --------------------------------------------------------------------------
def _next(today: date, weekday: int) -> date:
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)


def _rows_of(existing: Sequence[dict]) -> List[dict]:
    return [d for d in existing if str(d.get("slug", "")).startswith(PREFIX + "-")]


def pick_area(cands: Sequence[dict], existing: Sequence[dict], skip: Iterable[str]) -> Optional[str]:
    """'' (all of Pune) for the very first board; then the area with a full board whose last board is oldest (never shown first)."""
    mine = _rows_of(existing)
    if not any("-board-" in d["slug"] for d in mine) and len(board_rows(cands, "", skip)) >= MIN_BOARD:
        return ""
    last: Dict[str, str] = {}
    for d in mine:
        k = (d.get("creative") or {}).get("ref", "")
        if k.startswith("board-"):
            last[k[6:]] = max(last.get(k[6:], ""), d["slug"][-8:])
    ready = [a.key for a in _areas.AREAS if len(board_rows(cands, a.key, skip)) >= MIN_BOARD]
    if not ready:
        return None
    return min(ready, key=lambda k: (last.get(k, ""), -len(board_rows(cands, k, skip))))


def shown_lately(existing: Sequence[dict], today: date) -> set:
    cut = (today - timedelta(days=REPEAT_DAYS)).strftime("%Y%m%d")
    return {r for d in _rows_of(existing) if d["slug"][-8:] >= cut for r in (d.get("creative") or {}).get("regnos") or []}


async def _plan_one(store, reel: DateWatchReel, day: date, uploads: Path, channels: Sequence[str], at: time, say) -> int:
    from .schedule import IST
    slug = reel.slug(day)
    have = {(ch, s) for ch, s, _ in await store.existing()}
    todo = [ch for ch in channels if (ch, slug) not in have]
    if not todo:
        return 0
    images = [p.resolve().relative_to(Path(uploads).resolve()).as_posix() for p in save_slides(reel, Path(uploads) / SUBDIR / slug)]
    due = datetime.combine(day, at, IST)
    for ch in todo:
        creative = {"role": "datewatch", "source": "delay_reels", "template": "delay", "reel_key": slug, "ref": reel.key,
                    "path": "delay_reels", "layout": "reel", "ok": True, "hook": reel.hook, "hook_type": "datewatch",
                    "slides": images, "script": reel.script, "as_of": reel.as_of, "regnos": reel.regnos,
                    **({"area": reel.area} if reel.area else {})}
        await store.add(slug, ch, reel.caption_ig if ch == "instagram" else reel.caption_fb, images[0], due, kind="reel",
                        status="planned", images=images, creative=creative, extra={"area": reel.area} if reel.area else None)
        say(f"{slug} {ch}: planned for {due.isoformat()[:16]} IST")
    return len(todo)


async def autoplan(db, store, today: date, uploads: Path, channels: Sequence[str] = CHANNELS, at: time = AT,
                   say: Callable[[str], None] = lambda s: None) -> int:
    """Plan next Monday's board and next Thursday's 'moved' reel when they are not planned yet. Idempotent; rows are PLANNED
    (the owner approves each in Studio). Returns how many rows were added."""
    from app.modules.newsroom.store import Store as Register
    docs = await Register(db).all_projects()
    cands = candidates(docs, today)
    as_of = max((_iso(d.get("details_checked_at")) or "" for d in docs), default="") or today.isoformat()
    existing = await store.all()
    skip = shown_lately(existing, today)
    n = 0
    monday = _next(today, BOARD_WEEKDAY)
    if not any(d["slug"].startswith(f"{PREFIX}-board-") and d["slug"].endswith(f"{monday:%Y%m%d}") for d in _rows_of(existing)):
        area = pick_area(cands, existing, skip)
        reel = board(cands, area, as_of, skip) if area is not None else None
        if reel:
            n += await _plan_one(store, reel, monday, uploads, channels, at, say)
        else:
            say("datewatch: no area has a full board this week")
    thursday = _next(today, MOVED_WEEKDAY)
    if not any(d["slug"] == f"{PREFIX}-moved-{thursday:%Y%m%d}" for d in _rows_of(existing)):
        since = datetime.combine(thursday - timedelta(days=7), time(0), timezone.utc)
        reel = moved([c for c in cands if c["regno"] not in skip], since, as_of)
        if reel:
            n += await _plan_one(store, reel, thursday, uploads, channels, at, say)
    return n
