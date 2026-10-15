"""Number of the week: one number from Pune's MahaRERA records that a home buyer in our areas would stop scrolling for, as a
Wednesday reel. Facts only, from the register; planned by the system itself (`autoplan`, once a day by the calendar loop) as a
PLANNED row the owner approves.

Relatable first. A number is not posted because it is true, but because someone in Kharadi or Wagholi would say "that is about
me". So every candidate carries, before anything is drawn:
  audience  who it is for, in their words      ("you have booked, or are about to book, in Wagholi")
  question  what they are already asking       ("Will my flat be ready on the date I was told?")
  stake     what it touches in their life      time (when can I move in), risk (will the date hold), choice (how much is
                                               still open), demand (are people buying here)
and `relate()` scores it (stake, counted in homes = families rather than projects, a clear effect, the festive season, not shown
lately). Below MIN_RELATE there is no reel that week: never filler. The score and its reasons go on the row, so the owner sees
why this number was picked.

Kinds (each per area; only the areas matched by pincode, newsroom.policy.AREA_PINCODES, whose counts are complete):
  soon    projects with a completion date filed for the next 12 months, and how many of their homes are not yet booked
  moved   of the projects where homes are already booked, how many moved their filed completion date later (net of MahaRERA's
          COVID extension) by MIN_MOVED_MONTHS or more
  open    homes not yet booked in projects whose filed completion date is still ahead
  pace    homes booked in the last 90 days (from the dated readings areastats.refresh keeps)
Wording: the records' own terms ("filed completion date", "booked", "moved later"); never "delayed", "stuck", "selling fast",
prices or predictions. Slides are area_reels.Slide, drawn and checked by area_reels.save_slides.
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from app.core import areas as _areas
from app.core import brand
from app.modules.areastats.hot import bookings as _bookings
from app.modules.areastats.pages import booked as _booked
from app.modules.areastats.pages import months_later
from app.modules.areastats.service import _count, _day as _iso

from .area_reels import SOURCE, Slide, _day, _n, page_link, save_slides, site_host, wording_problems
from .delay_reels import covid_months, residential
from .puzzle_reels import TRUSTED

log = logging.getLogger(__name__)

PREFIX = "number"
SUBDIR = "calendar/numbers"
WEEKDAY = 2                 # Wednesday: between the Monday date board and Thursday's moves
AT = time(21, 0)            # IST: buyers scroll after work
CHANNELS = ("instagram", "facebook_page")
SOON_DAYS = 365
MIN_PROJECTS = 3            # soon: fewer projects than this is not a pattern
MIN_BASE = 5                # moved: projects with homes booked, at least
MIN_MOVED = 2               # moved: and at least this many moved
MIN_MOVED_MONTHS = 6        # a move shorter than this is paperwork, not a story
MIN_OPEN = 100              # open: homes
MIN_PACE = 20               # pace: homes booked in 90 days
MIN_RELATE = 4
REPEAT_KIND_DAYS = 28       # the same kind for the same area is not shown again within four weeks
FESTIVE_MONTHS = (10, 11)   # Navratri to Diwali: when families in Pune most often decide to buy
STAKE_WEIGHT = {"time": 3, "risk": 3, "choice": 2, "demand": 2}

# Who each kind speaks to, what they already ask, and what is at stake for them. Fixed here, never generated.
FRAMES = {
    "soon": {"stake": "time", "audience": "families who want to move in soon rather than wait years",
             "question": "Want a home sooner, not in 2030?",
             "check": ["Ask for the occupancy certificate (OC) date in writing", "Match the agreement's possession date to MahaRERA"],
             "prompt": "Would you pay more for a home that is ready sooner? Tell us in the comments."},
    "moved": {"stake": "risk", "audience": "anyone who has booked, or is about to book, an under-construction flat",
              "question": "Will your flat be ready on the date you were told?",
              "check": ["Compare the date at registration with the date filed now", "Read the builder's quarterly updates on MahaRERA"],
              "prompt": "Has your possession date moved? Tell us in the comments."},
    "open": {"stake": "choice", "audience": "buyers comparing projects in the area",
             "question": "Still looking? This is how much is not yet booked",
             "check": ["Check how many homes are booked in the project you like", "Visit more than one project before you pay a booking amount"],
             "prompt": "How many projects did you visit before deciding? Tell us in the comments."},
    "pace": {"stake": "demand", "audience": "buyers wondering whether people are actually buying here",
             "question": "Are people actually booking homes here?",
             "check": ["Ask which towers are being booked now", "Check the project's booked count on MahaRERA yourself"],
             "prompt": "Did you book here this year? Tell us in the comments."},
}


def _name(doc: dict) -> str:
    return " ".join(str(doc.get("name") or "").split())


def _ahead(doc: dict, today: date) -> Optional[str]:
    now = _iso(doc.get("completion_now"))
    return now if now and now > today.isoformat() else None


def _area_docs(docs: Iterable[dict], key: str) -> List[dict]:
    return [d for d in docs if d.get("locality") == key and residential(d)]


def _base(kind: str, area: _areas.Area, big: str, label: str, value: int, homes: bool, strong: bool, facts: List[str],
          regnos: List[str]) -> dict:
    return {"kind": kind, "area": area.key, "area_name": area.name, "big": big, "label": label, "value": value, "homes": homes,
            "strong": strong, "facts": facts, "regnos": regnos, **FRAMES[kind]}


# ---- candidates (pure) ------------------------------------------------------------------------------------------------------
def soon(docs: Sequence[dict], area: _areas.Area, today: date) -> Optional[dict]:
    end = (today + timedelta(days=SOON_DAYS)).isoformat()
    rows = [d for d in _area_docs(docs, area.key) if (n := _ahead(d, today)) and n <= end]
    if len(rows) < MIN_PROJECTS:
        return None
    facts = [f"{_n(len(rows))} {area.name} projects have a completion date filed for the next 12 months"]
    total = [_count(d.get("units_total")) for d in rows]
    sold = [_booked(d) for d in rows]
    if all(t for t in total) and all(s is not None for s in sold) and sum(sold) <= sum(total):
        facts.append(f"{_n(sum(total) - sum(sold))} of their {_n(sum(total))} homes are not yet booked")
    return _base("soon", area, _n(len(rows)), "projects with a completion date filed for the next 12 months", len(rows),
                 False, len(rows) >= 2 * MIN_PROJECTS, facts, [d.get("regno") or d["_id"] for d in rows])


def moved(docs: Sequence[dict], area: _areas.Area, today: date) -> Optional[dict]:
    base = [d for d in _area_docs(docs, area.key) if _ahead(d, today) and _iso(d.get("completion_at_registration"))
            and (_booked(d) or 0) > 0]
    late = [d for d in base if max(0, (months_later(d) or 0) - covid_months(d)) >= MIN_MOVED_MONTHS]
    if len(base) < MIN_BASE or len(late) < MIN_MOVED:
        return None
    families = sum(_booked(d) or 0 for d in late)
    facts = [f"{_n(len(base))} {area.name} projects have homes booked and a completion date still ahead",
             f"{_n(len(late))} of them moved their filed completion date later by {MIN_MOVED_MONTHS} months or more",
             f"{_n(families)} homes are booked in those {_n(len(late))} projects"]
    return _base("moved", area, f"{_n(len(late))} of {_n(len(base))}", "projects with homes booked moved their completion date later",
                 len(late), False, len(late) * 10 >= len(base) * 3, facts, [d.get("regno") or d["_id"] for d in late])


def open_homes(docs: Sequence[dict], area: _areas.Area, today: date) -> Optional[dict]:
    rows = []
    for d in _area_docs(docs, area.key):
        t, s = _count(d.get("units_total")), _booked(d)
        if _ahead(d, today) and t and s is not None and s <= t:
            rows.append((d, t, s))
    left = sum(t - s for _, t, s in rows)
    if left < MIN_OPEN:
        return None
    facts = [f"At least {_n(left)} homes are not yet booked in {_n(len(rows))} {area.name} projects with a completion date ahead",
             f"Out of {_n(sum(t for _, t, _ in rows))} homes registered in those projects"]
    return _base("open", area, _n(left), "homes not yet booked in projects still being built", left, True, left >= 10 * MIN_OPEN,
                 facts, [d.get("regno") or d["_id"] for d, _, _ in rows])


def pace(docs: Sequence[dict], area: _areas.Area, now: datetime) -> Optional[dict]:
    rows = [(d, int(b["value"])) for d in _area_docs(docs, area.key) if (b := _bookings(d, now))]
    sold = sum(n for _, n in rows)
    if sold < MIN_PACE:
        return None
    facts = [f"At least {_n(sold)} homes were booked in {_n(len(rows))} {area.name} projects in the last 90 days",
             "Counted from the booked homes each project reports to MahaRERA"]
    return _base("pace", area, _n(sold), "homes booked in the last 90 days", sold, True, sold >= 5 * MIN_PACE, facts,
                 [d.get("regno") or d["_id"] for d, _ in rows])


def candidates(docs: Sequence[dict], now: datetime, today: date) -> List[dict]:
    out = []
    for key in TRUSTED:
        area = _areas.get(key)
        if area is None:
            continue
        for c in (soon(docs, area, today), moved(docs, area, today), open_homes(docs, area, today), pace(docs, area, now)):
            if c:
                out.append(c)
    return out


# ---- will people relate? ----------------------------------------------------------------------------------------------------
def relate(c: dict, today: date, shown: Dict[str, str]) -> dict:
    """{'score', 'reasons'}: how likely a buyer in the area is to stop for this number. `shown` maps "<kind>-<area>" and
    "area-<area>" to the last day (YYYYMMDD) a number reel about it was planned."""
    reasons = [f"speaks to {c['audience']}", f"answers '{c['question']}'", f"stake: {c['stake']}"]
    score = STAKE_WEIGHT[c["stake"]]
    if c["homes"]:
        score += 1
        reasons.append("counted in homes (families), not projects")
    if c["strong"]:
        score += 1
        reasons.append("a clear effect, not a rounding")
    if today.month in FESTIVE_MONTHS and c["stake"] in ("time", "choice"):
        score += 1
        reasons.append("festive season: families are deciding now")
    last = shown.get(f"{c['kind']}-{c['area']}", "")
    if last and last >= (today - timedelta(days=REPEAT_KIND_DAYS)).strftime("%Y%m%d"):
        score -= 3
        reasons.append("same number shown in the last four weeks")
    if shown.get(f"area-{c['area']}", "") >= (today - timedelta(days=7)).strftime("%Y%m%d"):
        score -= 1
        reasons.append("same area last week")
    return {"score": score, "reasons": reasons}


def pick(cands: Sequence[dict], today: date, shown: Dict[str, str]) -> Optional[dict]:
    """The candidate people are most likely to relate to, with its `relate` result; None when none reaches MIN_RELATE."""
    scored = [{**c, "relate": relate(c, today, shown)} for c in cands]
    scored = [c for c in scored if c["relate"]["score"] >= MIN_RELATE]
    if not scored:
        return None
    # a tie goes to the bigger stake (whether the date holds beats how many homes are open), then the area shown longest ago;
    # raw values are never compared across kinds (480 homes is not "more" than 3 of 6 projects)
    return max(scored, key=lambda c: (c["relate"]["score"], STAKE_WEIGHT[c["stake"]], -int(shown.get(f"area-{c['area']}", "0") or 0)))


# ---- the reel -----------------------------------------------------------------------------------------------------------------
@dataclass
class NumberReel:
    key: str              # '<kind>-<area>'
    kind: str
    area: str
    as_of: str
    hook: str
    slides: List[Slide]
    caption_ig: str
    caption_fb: str
    regnos: List[str]
    relate: dict

    @property
    def script(self) -> List[str]:
        out = []
        for s in self.slides:
            out.append(" ".join(x for x in (s.headline, s.big, s.label) if x))
            out += s.lines
        return out

    def slug(self, day: date) -> str:
        return f"{PREFIX}-{self.key}-{day:%Y%m%d}"


def build(c: dict, as_of: str) -> Optional[NumberReel]:
    """The reel for a picked candidate, or None when any of its words trips a wording rule."""
    area = _areas.get(c["area"])
    slides = [Slide(f"{area.name.upper()} · NUMBER OF THE WEEK", c["question"], c["big"], c["label"]),
              Slide("WHAT THE RECORDS SAY", f"{area.name}, as filed on MahaRERA", lines=c["facts"][:3]),
              Slide("BEFORE YOU DECIDE", "Two things to check", lines=c["check"]),
              Slide("SEE EVERY PROJECT", f"Every {area.name} project, with its source", lines=[page_link(area)])]
    hook = f"{c['question']} {area.name}: {c['big']} {c['label']}."
    facts = "\n".join(f"• {f}." for f in c["facts"])
    check = "Before you decide:\n" + "\n".join(f"• {x}." for x in c["check"])
    source = f"Source: {SOURCE}, as of {_day(as_of)}."
    body = "\n\n".join([hook, facts, check, source, c["prompt"]])
    tags = " ".join(list(area.hashtags) + ["#MahaRERA", "#PuneProperty"])
    caps = {"instagram": f"{body}\n\nEvery project: {page_link(area)} (link in our bio).\n\n{tags}",
            "facebook_page": f"{body}\n\nEvery project: {brand.SITE}{area.page}\n\n{tags}"}
    text = "\n".join(list(caps.values()) + [" ".join([s.kicker, s.headline, s.big, s.label] + s.lines) for s in slides])
    problems = wording_problems(text)
    if problems:
        log.warning("number: %s-%s dropped: %s", c["kind"], c["area"], problems)
        return None
    return NumberReel(f"{c['kind']}-{c['area']}", c["kind"], c["area"], as_of, hook, slides, caps["instagram"],
                      caps["facebook_page"], c["regnos"][:50], c["relate"])


# ---- planning (the system does it itself) --------------------------------------------------------------------------------------
def _next(today: date, weekday: int) -> date:
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)


def _rows_of(existing: Sequence[dict]) -> List[dict]:
    return [d for d in existing if str(d.get("slug", "")).startswith(PREFIX + "-")]


def shown_map(existing: Sequence[dict]) -> Dict[str, str]:
    """'<kind>-<area>' and 'area-<area>' -> the latest day (YYYYMMDD) a number reel about it was planned for."""
    out: Dict[str, str] = {}
    for d in _rows_of(existing):
        ref, day = (d.get("creative") or {}).get("ref", ""), d["slug"][-8:]
        area = ref.split("-", 1)[1] if "-" in ref else ""
        for k in (ref, f"area-{area}"):
            if k and day > out.get(k, ""):
                out[k] = day
    return out


async def autoplan(db, store, today: date, uploads: Path, channels: Sequence[str] = CHANNELS, at: time = AT,
                   say: Callable[[str], None] = lambda s: None, now: Optional[datetime] = None) -> int:
    """Plan next Wednesday's number reel when it is not planned yet. Idempotent; rows are PLANNED (the owner approves each in
    Studio). Returns how many rows were added."""
    from app.modules.newsroom.store import Store as Register

    from .schedule import IST
    wednesday = _next(today, WEEKDAY)
    existing = await store.all()
    if any(d["slug"].endswith(f"{wednesday:%Y%m%d}") for d in _rows_of(existing)):
        return 0
    docs = await Register(db).all_projects()
    now = now or datetime.now(timezone.utc)
    best = pick(candidates(docs, now, today), today, shown_map(existing))
    if best is None:
        say("number: no number people would relate to this week")
        return 0
    as_of = max((_iso(d.get("details_checked_at")) or "" for d in docs), default="") or today.isoformat()
    reel = build(best, as_of)
    if reel is None:
        return 0
    slug = reel.slug(wednesday)
    have = {(ch, s) for ch, s, _ in await store.existing()}
    todo = [ch for ch in channels if (ch, slug) not in have]
    if not todo:
        return 0
    images = [p.resolve().relative_to(Path(uploads).resolve()).as_posix() for p in save_slides(reel, Path(uploads) / SUBDIR / slug)]
    due = datetime.combine(wednesday, at, IST)
    for ch in todo:
        creative = {"role": "number", "source": "number_reels", "template": "number", "reel_key": slug, "ref": reel.key,
                    "path": "number_reels", "layout": "reel", "ok": True, "hook": reel.hook, "hook_type": "number",
                    "slides": images, "script": reel.script, "as_of": reel.as_of, "regnos": reel.regnos, "area": reel.area,
                    "relate": reel.relate}
        await store.add(slug, ch, reel.caption_ig if ch == "instagram" else reel.caption_fb, images[0], due, kind="reel",
                        status="planned", images=images, creative=creative, extra={"area": reel.area})
        say(f"{slug} {ch}: planned for {due.isoformat()[:16]} IST (relate {reel.relate['score']})")
    return len(todo)
