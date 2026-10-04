"""The weekly content rhythm. Pure: no I/O, no clock, no network. Decides WHAT goes WHERE and WHEN; the builder makes the creative.

Per week (default 4 weeks), 10:00 or 19:00 IST on varied days:
  Instagram (5): a showcase carousel, a checklist carousel, a myth / poll / big-number card, an agent product card, the week's reel
  Facebook  (5): two educational posts, a showcase card, an agent post or a poll (alternating), the same reel
Reel templates alternate tip, tour, pitch. A library slug is never reused within 60 days (on either channel). Showcase homes rotate through
Kharadi, Upper Kharadi and Wagholi. Hindi and Marathi agent posts are left out unless include_local is set.

The daily reel rhythm (`build_daily_plan`, opt-in: CALENDAR_DAILY_REELS) is separate: 2 reels a day (3 later) on both channels,
a morning area insight and an evening real project (consented agents only) or buyer-guide reel.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .adapters import AGENT_POOL, AREAS, STAT_SLUGS, homes_in
from .library import ENTRIES, Entry
from .schedule import CHANNELS, IST, MIN_GAP, NO_REPEAT, slot_times

PER_WEEK = 5
IG_ROLES = ("showcase", "checklist", "mythpoll", "agent", "reel")
FB_ROLES = ("edu_a", "edu_b", "showcase", "agentpoll", "reel")
REEL_TEMPLATES = ("tip", "tour", "pitch")
MYTHPOLL_CYCLE = ("myth", "poll", "stat")
# Agent posts, most "product card" first (single image = the phone mock layout).
AGENT_ORDER = ("agent-lead-cards", "agent-consistent-posting", "agent-buyer-summary", "agent-post-to-lead", "agent-comment-not-lead",
               "agent-three-details", "agent-notebook-vs-cards", "agent-poll-tracking")
LOCAL_AGENT_SLUGS = ("agent-hindi", "agent-marathi")


@dataclass(frozen=True)
class Item:
    channel: str            # facebook_page | instagram
    kind: str               # post | showcase | reel
    due_at: datetime        # UTC
    week: int               # 1-based
    role: str
    source: str             # library | agent | home | reel
    ref: str                # library slug, agent slug, home slug, or for a reel the reel key
    prefer: str = ""        # creative format wanted
    template: str = ""      # reel: tip | tour | pitch
    reel_ref: str = ""      # reel: entry slug (tip), home slug (tour), area key (area) or project slug (project)
    area: str = ""          # app.core.areas key the item is about, when it is about one area
    agent_id: str = ""      # project reel: the agent whose project it is (and who consented)

    @property
    def slug(self) -> str:
        return self.ref


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


class _Picker:
    """Least-recently-used choice from pools, honouring the 60 day no-repeat rule and rows that already exist."""

    def __init__(self, entries: Sequence[Entry], include_local: bool, existing: Iterable[Tuple[str, str, datetime]]):
        self.by_pillar: Dict[str, List[str]] = defaultdict(list)
        for e in entries:
            if e.pillar == "agent":
                if e.slug in LOCAL_AGENT_SLUGS and not include_local:
                    continue
            self.by_pillar[e.pillar].append(e.slug)
        self.entries = {e.slug: e for e in entries}
        self.used: Dict[str, List[datetime]] = defaultdict(list)
        self.home_uses: Dict[str, int] = defaultdict(int)
        for _, slug, due in existing:
            self.used[slug].append(_aware(due))
            self.home_uses[slug] += 1

    def _ok(self, slug: str, due: datetime) -> bool:
        return all(abs(due - t) >= NO_REPEAT for t in self.used[slug])

    def _last(self, slug: str) -> datetime:
        return max(self.used[slug], default=datetime(1970, 1, 1, tzinfo=timezone.utc))

    def take(self, pool: Sequence[str], due: datetime) -> Optional[str]:
        free = [s for s in pool if self._ok(s, due)]
        if not free:
            return None
        pick = min(free, key=lambda s: (self._last(s), pool.index(s)))  # never used first, then the longest ago
        self.used[pick].append(due)
        return pick

    def take_first(self, pillars: Sequence[str], due: datetime, only: Optional[Sequence[str]] = None) -> Optional[Tuple[str, str]]:
        for p in pillars:
            pool = [s for s in self.by_pillar.get(p, []) if only is None or s in only]
            s = self.take(pool, due)
            if s:
                return p, s
        return None

    def agent(self, due: datetime) -> Optional[Tuple[str, str]]:
        local = [s for s in self.by_pillar.get("agent", [])]
        pool = [s for s in AGENT_ORDER if s in AGENT_POOL or s in local] + [s for s in local if s not in AGENT_ORDER]
        s = self.take(pool, due)
        if not s:
            return None
        return ("agent" if s in AGENT_POOL else "library"), s

    def home(self, area: str, due: datetime) -> Optional[str]:
        pool = [h.slug for h in homes_in(area)]
        if not pool:
            return None
        # Sample homes are labelled illustrations, so they may come round again: least used first, never the same one twice in a row.
        pick = min(pool, key=lambda s: (self.home_uses[s], self._last(s), pool.index(s)))
        self.home_uses[pick] += 1
        self.used[pick].append(due)
        return pick


def _week_groups(times: Sequence[datetime]) -> List[List[datetime]]:
    groups: Dict[Tuple[int, int], List[datetime]] = defaultdict(list)
    for t in times:
        groups[t.astimezone(IST).isocalendar()[:2]].append(t)
    return [groups[k] for k in sorted(groups)]


def build_plan(start: date, weeks: int = 4, include_local: bool = False, existing: Iterable[Tuple[str, str, datetime]] = (),
               entries: Sequence[Entry] = ENTRIES) -> List[Item]:
    """New items for [start, start + weeks). `existing` = (channel, slug, due_at) of rows already in the calendar: their slots count as
    filled and their slugs as used. Start on a Monday for full weeks."""
    existing = list(existing)
    picker = _Picker(entries, include_local, existing)
    times = slot_times(start, weeks, {c: PER_WEEK for c in CHANNELS})
    taken = {c: [_aware(d) for ch, _, d in existing if ch == c] for c in CHANNELS}
    items: List[Item] = []
    counters = defaultdict(int)
    reels: Dict[int, Tuple[str, str, str]] = {}   # week -> (template, reel key, reel_ref) so Instagram and Facebook share one reel
    monday0 = start - timedelta(days=start.weekday())
    for ch in ("instagram", "facebook_page"):
        roles, shift = (IG_ROLES, 2) if ch == "instagram" else (FB_ROLES, 3)
        free = [t for t in times[ch] if all(abs(t - u) >= timedelta(hours=12) for u in taken[ch])]
        for group in _week_groups(free):
            first = group[0].astimezone(IST).date()
            k = (first - timedelta(days=first.weekday()) - monday0).days // 7
            n = len(group)
            for i, due in enumerate(group):
                pos = PER_WEEK - n + i
                role = roles[(pos + shift * k + (1 if ch == "facebook_page" else 0)) % PER_WEEK]
                it = _make(ch, role, due, k, picker, counters, reels, include_local)
                if it:
                    items.append(it)
    return sorted(items, key=lambda i: (i.due_at, i.channel))


def _make(ch: str, role: str, due: datetime, k: int, p: _Picker, counters, reels, include_local: bool) -> Optional[Item]:
    wk = k + 1
    ig = ch == "instagram"
    if role == "showcase":
        area = AREAS[k % 3] if ig else AREAS[(k + 1) % 3]
        slug = p.home(area, due)
        return Item(ch, "showcase", due, wk, role, "home", slug) if slug else None
    if role == "reel":
        if wk not in reels:
            tpl = REEL_TEMPLATES[k % 3]
            ref = ""
            if tpl == "tip":
                got = p.take_first(("checklist", "explainer"), due)
                ref = got[1] if got else ""
                tpl = tpl if ref else "pitch"
            elif tpl == "tour":
                ref = p.home(AREAS[(k + 2) % 3], due) or ""
                tpl = tpl if ref else "pitch"
            reels[wk] = (tpl, f"reel-w{wk}-{tpl}", ref)
        tpl, key, ref = reels[wk]
        return Item(ch, "reel", due, wk, role, "reel", key, template=tpl, reel_ref=ref)
    if role == "checklist":
        got = p.take_first(("checklist", "local", "explainer"), due)
        return Item(ch, "post", due, wk, role, "library", got[1], "carousel") if got else None
    if role == "mythpoll":
        n = counters["mythpoll"]
        counters["mythpoll"] += 1
        kind = MYTHPOLL_CYCLE[n % 3]
        order = {"myth": (("myth", None, "myth-vs-fact"), ("poll", None, "")), "poll": (("poll", None, ""), ("myth", None, "myth-vs-fact")),
                 "stat": (("explainer", STAT_SLUGS, "stat"), ("myth", STAT_SLUGS, "stat"), ("myth", None, "myth-vs-fact"))}[kind]
        for pillar, only, prefer in order:
            got = p.take_first((pillar,), due, only)
            if got:
                return Item(ch, "post", due, wk, role, "library", got[1], prefer)
        return None
    if role == "agent" or (role == "agentpoll" and k % 2 == 0):
        got = p.agent(due)
        if not got:
            return None
        src, slug = got
        prefer = "single" if not ig or slug in ("agent-lead-cards", "agent-consistent-posting", "agent-buyer-summary") else ""
        return Item(ch, "post", due, wk, "agent", src, slug, prefer)
    if role == "agentpoll":
        got = p.take_first(("poll", "myth"), due)
        return Item(ch, "post", due, wk, "poll", "library", got[1], "poll" if got and got[0] == "poll" else "myth-vs-fact") if got else None
    # Facebook educational posts
    if role == "edu_a":
        got = p.take_first(("explainer", "checklist"), due)
    else:
        got = p.take_first(("local", "checklist") if k % 2 == 0 else ("checklist", "local"), due)
    if not got:
        return None
    return Item(ch, "post", due, wk, role, "library", got[1], "stat" if got[1] in STAT_SLUGS else "single")


# ---- the daily reel rhythm ----------------------------------------------------------------------------------------------------------------
# Hours (IST) per number of reels a day. Two reels 12 hours apart keep the existing minimum gap (MIN_GAP) on a channel; a third reel
# needs a 6 hour gap, so it is only planned when the caller passes that smaller gap on purpose.
DAILY_HOURS = {1: (8,), 2: (8, 20), 3: (8, 14, 20)}
DAILY_ROLES = {1: ("area",), 2: ("area", "evening"), 3: ("area", "guide", "evening")}
# Morning area tiers, by day: the affordable belt (first homes, budget buyers) gets two mornings in three.
TIER_CYCLE = ("affordable", "it", "affordable")
GUIDE_PILLARS = ("checklist", "explainer", "local", "myth")


def area_reel_slug(key: str, day: date) -> str:
    return f"area-{key}-{day:%Y%m%d}"


def area_of_slug(slug: str) -> Optional[str]:
    """'area-upper_kharadi-20261012' -> 'upper_kharadi'."""
    if not slug.startswith("area-") or len(slug) < 15:
        return None
    return slug[5:-9]


def project_reel_slug(project_slug: str) -> str:
    """'<project slug>-reel': knowledge.grounding.project_slug_of strips '-reel', so comment replies find the project record."""
    return f"{project_slug}-reel"


def daily_gap(per_day: int) -> timedelta:
    return MIN_GAP if per_day <= 2 else timedelta(hours=6)


def build_daily_plan(start: date, days: int = 7, areas: Sequence[str] = (), projects: Sequence[dict] = (), per_day: int = 2,
                     existing: Iterable[Tuple[str, str, datetime]] = (), entries: Sequence[Entry] = ENTRIES,
                     now: Optional[datetime] = None, min_gap: Optional[timedelta] = None) -> List[Item]:
    """Reels for [start, start + days), the same reel on Instagram and the Facebook Page.

    `areas`: keys of the areas that have an area reel today (the caller drops areas whose stats are too thin); `projects`: dicts with
    slug, agent_id and area of live projects whose agent has consented (the caller checks consent). `existing` = (channel, slug,
    due_at) of rows already in the calendar: a slot within the gap of one of them is left free on that channel, their slugs count
    as used (60 day no-repeat for guides and projects; least recently shown first for areas). Slots before `now` are skipped."""
    from app.core import areas as _areas
    per_day = max(1, min(3, per_day))
    gap = min_gap or daily_gap(per_day)
    existing = list(existing)
    taken = {c: [_aware(d) for ch, _, d in existing if ch == c] for c in CHANNELS}
    picker = _Picker(entries, False, existing)
    area_last: Dict[str, datetime] = {}
    for _, slug, due in existing:
        k = area_of_slug(slug)
        if k:
            area_last[k] = max(area_last.get(k, _aware(due)), _aware(due))
    usable = [a for a in _areas.AREAS if a.key in set(areas)]
    proj_pool = [p for p in projects if p.get("slug") and p.get("agent_id")]
    items: List[Item] = []
    for d in range(days):
        day = start + timedelta(days=d)
        week = d // 7 + 1
        for hour, role in zip(DAILY_HOURS[per_day], DAILY_ROLES[per_day]):
            due = datetime.combine(day, time(hour, 0), tzinfo=IST).astimezone(timezone.utc)
            if now is not None and due <= now:
                continue
            chans = [c for c in ("instagram", "facebook_page") if all(abs(due - t) >= gap for t in taken[c])]
            if not chans:
                continue
            made = _daily(role, day, due, week, usable, area_last, proj_pool, picker)
            if not made:
                continue
            for c in chans:
                items.append(Item(c, "reel", due, week, made["role"], made["source"], made["ref"], template=made["template"],
                                  reel_ref=made["reel_ref"], area=made.get("area", ""), agent_id=made.get("agent_id", "")))
                taken[c].append(due)
    return sorted(items, key=lambda i: (i.due_at, i.channel))


def _daily(role: str, day: date, due: datetime, week: int, usable, area_last: Dict[str, datetime], projects: Sequence[dict],
           picker: _Picker) -> Optional[dict]:
    if role == "area":
        a = _next_area(day, usable, area_last)
        if a is None:
            return None
        area_last[a.key] = due
        return {"role": "area", "source": "area_insight", "ref": area_reel_slug(a.key, day), "template": "area", "reel_ref": a.key,
                "area": a.key}
    if role == "evening" and projects:
        pool = [project_reel_slug(p["slug"]) for p in projects]
        got = picker.take(pool, due)
        if got:
            p = projects[pool.index(got)]
            return {"role": "project", "source": "agentprojects", "ref": got, "template": "project", "reel_ref": p["slug"],
                    "area": p.get("area") or "", "agent_id": p["agent_id"]}
    got = picker.take_first(GUIDE_PILLARS, due)  # buyer guide: the entry slug is the row slug, so the 60 day rule holds across runs
    if not got:
        return None
    return {"role": "guide", "source": "reel", "ref": got[1], "template": "tip", "reel_ref": got[1]}


def _next_area(day: date, usable, area_last: Dict[str, datetime]):
    """The tier of the day (TIER_CYCLE by calendar day, so reruns agree), then the area of that tier shown longest ago."""
    if not usable:
        return None
    tier = TIER_CYCLE[day.toordinal() % len(TIER_CYCLE)]
    pool = [a for a in usable if a.tier == tier] or list(usable)
    never = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return min(pool, key=lambda a: (area_last.get(a.key, never), usable.index(a)))
