"""Pure scheduling: lay the library out into a weekly rhythm. No I/O, no clock, no database.

Rules: Facebook 4 posts a week, Instagram 3 (defaults) at 10:00 or 19:00 IST on varied weekdays; never two posts on one channel
within 12 hours; pillars rotate; a slug never repeats on a channel within 60 days.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .library import Entry

IST = timezone(timedelta(hours=5, minutes=30))
CHANNELS = ("facebook_page", "instagram")
HOURS = (10, 19)
MIN_GAP = timedelta(hours=12)
NO_REPEAT = timedelta(days=60)
# One pillar per slot, in turn. Agent pitches come about once in ten slots.
ROTATION = ("explainer", "myth", "checklist", "poll", "explainer", "local", "myth", "checklist", "agent", "local")
OFFSET = {"facebook_page": 0, "instagram": 4}  # start the two channels at different points of the rotation


@dataclass(frozen=True)
class Slot:
    channel: str
    slug: str
    due_at: datetime  # UTC


def _week_days(n: int, k: int, channel: str) -> List[Tuple[int, int]]:
    """(weekday 0=Mon, hour IST) for the n posts of week k: evenly spread, shifted each week so the weekdays vary."""
    n = max(0, min(n, 7))
    shift = (k * 3) % 7 if channel == "facebook_page" else (k * 2 + 1) % 7
    days = sorted({(round(i * 7 / n) + shift) % 7 for i in range(n)}) if n else []
    return [(d, HOURS[(i + k) % 2]) for i, d in enumerate(days)]


def slot_times(start: date, weeks: int, per_week: Dict[str, int]) -> Dict[str, List[datetime]]:
    """Candidate due times (UTC) per channel from the start date (00:00 IST) on, earliest first, at least 12 hours apart."""
    monday = start - timedelta(days=start.weekday())
    floor = datetime.combine(start, time(0, 0), tzinfo=IST)
    out: Dict[str, List[datetime]] = {}
    for ch in CHANNELS:
        found: List[datetime] = []
        for k in range(weeks):
            for d, h in _week_days(per_week.get(ch, 0), k, ch):
                found.append(datetime.combine(monday + timedelta(days=7 * k + d), time(h, 0), tzinfo=IST))
        found.sort()
        kept: List[datetime] = []
        for t in found:
            if t >= floor and (not kept or t - kept[-1] >= MIN_GAP):
                kept.append(t)
        out[ch] = [t.astimezone(timezone.utc) for t in kept]
    return out


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def build_schedule(entries: Sequence[Entry], start: date, weeks: int = 8, fb_per_week: int = 4, ig_per_week: int = 3,
                   existing: Iterable[Tuple[str, str, datetime]] = ()) -> List[Slot]:
    """New slots for [start, start + weeks). `existing` = (channel, slug, due_at) of rows already in the calendar: their times count as
    filled, their slugs as used, and new slots stay 12 hours away from them (so running this twice adds nothing)."""
    used: Dict[str, List[Tuple[str, datetime]]] = {c: [] for c in CHANNELS}
    for ch, slug, due in existing:
        if ch in used:
            used[ch].append((slug, _aware(due)))
    pools: Dict[str, List[Entry]] = {}
    for e in entries:
        pools.setdefault(e.pillar, []).append(e)
    times = slot_times(start, weeks, {"facebook_page": fb_per_week, "instagram": ig_per_week})
    chosen: List[Slot] = []
    for ch in CHANNELS:
        for i, due in enumerate(times[ch]):
            if any(abs(due - t) < MIN_GAP for _, t in used[ch]):  # filled, or too close to an existing post
                continue
            e = _pick(ch, i, due, pools, used[ch], [s for s in chosen if s.channel != ch])
            if e is None:
                continue
            chosen.append(Slot(ch, e.slug, due))
            used[ch].append((e.slug, due))
    return sorted(chosen, key=lambda s: (s.due_at, s.channel))


def _pick(ch: str, i: int, due: datetime, pools: Dict[str, List[Entry]], used: List[Tuple[str, datetime]], other: List[Slot]) -> Optional[Entry]:
    def ok(e: Entry) -> bool:
        return all(s != e.slug or abs(due - t) >= NO_REPEAT for s, t in used)

    order = [ROTATION[(i + OFFSET[ch] + j) % len(ROTATION)] for j in range(len(ROTATION))]
    order += [p for p in pools if p not in order]
    for pillar in order:
        cands = [e for e in pools.get(pillar, []) if ok(e)]
        if cands:
            # Soft preference: not the same post on the other channel within two days.
            fresh = [e for e in cands if not any(s.slug == e.slug and abs(s.due_at - due) < timedelta(days=2) for s in other)]
            return (fresh or cands)[0]
    return None
