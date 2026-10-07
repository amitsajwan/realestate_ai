from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

from app.modules.calendar import library, schedule
from app.modules.calendar.schedule import IST, build_schedule

START = date(2026, 10, 6)
ENTRIES = library.ENTRIES


def by_channel(slots):
    out = defaultdict(list)
    for s in slots:
        out[s.channel].append(s)
    return out


def test_full_weeks_have_four_facebook_and_three_instagram_posts():
    slots = by_channel(build_schedule(ENTRIES, START, 8))
    for ch, n in (("facebook_page", 4), ("instagram", 3)):
        weeks = Counter(s.due_at.astimezone(IST).isocalendar()[:2] for s in slots[ch])
        full = [w for w in sorted(weeks)[1:-1]]  # the first and last week are partial or shifted
        assert full and all(weeks[w] == n for w in full), (ch, weeks)


def test_times_are_10_or_19_ist_and_not_before_the_start():
    for s in build_schedule(ENTRIES, START, 8):
        t = s.due_at.astimezone(IST)
        assert (t.hour, t.minute) in ((10, 0), (19, 0))
        assert t.date() >= START
        assert s.due_at.tzinfo is not None


def test_never_two_posts_on_a_channel_within_12_hours():
    for ch, slots in by_channel(build_schedule(ENTRIES, START, 12)).items():
        times = sorted(s.due_at for s in slots)
        assert all(b - a >= timedelta(hours=12) for a, b in zip(times, times[1:])), ch


def test_weekdays_vary_week_to_week():
    fb = by_channel(build_schedule(ENTRIES, START, 8))["facebook_page"]
    days = {s.due_at.astimezone(IST).weekday() for s in fb}
    assert len(days) >= 6
    weekly = defaultdict(set)
    for s in fb:
        d = s.due_at.astimezone(IST)
        weekly[d.isocalendar()[:2]].add(d.weekday())
    assert len({frozenset(v) for v in weekly.values()}) > 2


def test_no_slug_repeats_on_a_channel_within_60_days():
    for ch, slots in by_channel(build_schedule(ENTRIES, START, 16)).items():
        last = {}
        for s in sorted(slots, key=lambda s: s.due_at):
            if s.slug in last:
                assert s.due_at - last[s.slug] >= timedelta(days=60), (ch, s.slug)
            last[s.slug] = s.due_at


def test_pillars_rotate_and_agent_pitches_stay_rare():
    for ch, slots in by_channel(build_schedule(ENTRIES, START, 8)).items():
        pillars = [library.BY_SLUG[s.slug].pillar for s in sorted(slots, key=lambda s: s.due_at)]
        assert all(not (a == b == c) for a, b, c in zip(pillars, pillars[1:], pillars[2:])), pillars
        assert len(set(pillars)) >= 5
        assert pillars.count("agent") <= max(1, len(pillars) // 6)


def test_is_deterministic_and_idempotent_with_existing_rows():
    first = build_schedule(ENTRIES, START, 8)
    assert first == build_schedule(ENTRIES, START, 8)
    existing = [(s.channel, s.slug, s.due_at) for s in first]
    assert build_schedule(ENTRIES, START, 8, existing=existing) == []


def test_extending_the_window_adds_only_new_slots_without_repeats():
    first = build_schedule(ENTRIES, START, 4)
    existing = [(s.channel, s.slug, s.due_at) for s in first]
    more = build_schedule(ENTRIES, START, 8, existing=existing)
    assert more and all(m.due_at > first[0].due_at for m in more)
    assert not ({(s.channel, s.due_at) for s in first} & {(s.channel, s.due_at) for s in more})
    for ch in ("facebook_page", "instagram"):
        slugs = [s.slug for s in first + more if s.channel == ch]
        assert len(slugs) == len(set(slugs))


def test_existing_posts_keep_new_slots_12_hours_away():
    t = datetime(2026, 10, 7, 13, 30, tzinfo=timezone.utc)  # 19:00 IST on the Wednesday
    slots = build_schedule(ENTRIES, START, 1, existing=[("facebook_page", "carpet-under-rera", t)])
    assert all(abs(s.due_at - t) >= timedelta(hours=12) for s in slots if s.channel == "facebook_page")


def test_small_library_just_yields_fewer_posts_never_repeats():
    slots = build_schedule(ENTRIES[:5], START, 8)
    for ch in ("facebook_page", "instagram"):
        slugs = [s.slug for s in slots if s.channel == ch]
        assert len(slugs) == len(set(slugs)) <= 5


def test_custom_rhythm():
    slots = by_channel(build_schedule(ENTRIES, date(2026, 10, 5), 4, fb_per_week=2, ig_per_week=1))
    assert len(slots["facebook_page"]) == 8 and len(slots["instagram"]) == 4
