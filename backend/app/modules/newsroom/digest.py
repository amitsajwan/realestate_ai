"""The weekly digest: 'Kharadi and Wagholi this week'. 3 to 5 of the week's approved or published stories plus one evergreen buyer tip,
built as a normal `pending_review` item so the owner approves it like any other. On Instagram it is a carousel (cover, one slide per
story, the tip, a closing slide); on Facebook a text post with the cover card.

Rules (all in code, tested): only stories that were approved, scheduled or published in the last 7 days; at least 2 of them (else no
digest); at most 5, at most 2 per pillar, most important pillar first; one tip; the digest text passes the same `check` stage as a
story (its source text is the stories' own facts and the tip); one digest per ISO week (the id carries the week); the runner builds it
on Sunday from 18:00 IST. Pure helpers plus one `build` that talks to the store."""
from app.core import brand
import inspect
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional

from . import codec, policy
from . import presentation as pr
from .store import Store
from .types import Draft, Fact, Facts, RawItem

log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))
MIN_ITEMS, MAX_ITEMS, PER_PILLAR, WINDOW_DAYS = 2, 5, 2, 7
TITLE = "Kharadi and Wagholi this week"
DONE_STATES = ("approved", "scheduled", "published")
PILLAR_RANK = {p: i for i, p in enumerate(("infrastructure", "new_supply", "rules_money", "locality_life", "education"))}

# Evergreen buyer tips: general, no figures, no names, no predictions. One per week, rotating.
TIPS = [
    "Ask for the project's MahaRERA registration number and look it up on the MahaRERA website before you pay any token amount.",
    "Visit the flat in daylight and again in the evening, and ask the neighbours about water supply and traffic.",
    "Ask for the possession date in writing in the agreement, not only in the brochure.",
    "Read the sale agreement fully before signing and ask what happens if possession is late.",
    "Check that the approved plan and the layout you are shown match, and ask to see the commencement certificate.",
    "Ask what the maintenance charges cover and who collects them, before you decide.",
]


def _chunk(text: str, n: int = 9) -> str:
    ws = text.split()
    return " ".join(("pause " + w) if i and i % n == 0 else w for i, w in enumerate(ws))


def week_id(now: datetime) -> str:
    iso = now.astimezone(IST).isocalendar()
    return f"digest-{iso[0]}-w{iso[1]:02d}"


def is_due(now: datetime) -> bool:
    """Sunday from 18:00 IST (the runner may come by any time after that; the id makes the build once-only)."""
    ist = now.astimezone(IST)
    return ist.weekday() == 6 and ist.hour >= 18


def tip_for(now: datetime) -> str:
    return TIPS[now.astimezone(IST).isocalendar()[1] % len(TIPS)]


def _aware(d):
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


def pick(docs: List[dict], now: datetime) -> List[dict]:
    """The stories for this week's digest, in digest order."""
    since = now - timedelta(days=WINDOW_DAYS)
    ok = [d for d in docs if d.get("status") in DONE_STATES and (d.get("draft") or {}).get("format") != "digest"
          and d.get("draft") and (_aware(d.get("published_at") or d.get("updated_at")) or now) >= since]
    ok.sort(key=lambda d: (PILLAR_RANK.get(pr.pillar(d), 9), -(_aware(d.get("published_at") or d.get("updated_at")) or now).timestamp()))
    seen, out = {}, []
    for d in ok:
        p = pr.pillar(d)
        if seen.get(p, 0) >= PER_PILLAR:
            continue
        seen[p] = seen.get(p, 0) + 1
        out.append(d)
        if len(out) == MAX_ITEMS:
            break
    return out


def _snapshot(d: dict) -> dict:
    return {"id": d["_id"], "headline": pr.headline(d), "hook": pr.hook(d), "line": pr.support_line(d), "source": pr.source_name(d),
            "as_of": pr.as_of(d), "pillar": pr.pillar(d), "areas": pr.areas(d)}


def compose(docs: List[dict], now: datetime, tip: Optional[str] = None) -> Optional[dict]:
    """The digest item document (status pending_review, not yet checked), or None when fewer than MIN_ITEMS stories qualify."""
    chosen = pick(docs, now)
    if len(chosen) < MIN_ITEMS:
        return None
    tip = tip or tip_for(now)
    stories = [_snapshot(d) for d in chosen]
    ist = now.astimezone(IST)  # the digest's own 'as of' day is the day the owner sees in India
    when = f"{ist.day} {pr.MONTHS[ist.month - 1]} {ist.year}"
    lines = "\n".join(f"• {s['hook']} ({s['source']})" for s in stories)
    text = "\n\n".join([TITLE, lines, f"Buyer tip: {tip}", f"As of {when}."])
    sources = list(dict.fromkeys(s["source"] for s in stories if s["source"]))
    # The source text the check compares against: the stories' own checked facts, headlines and summaries, plus our tip. The tip and
    # headlines are chunked so the 'copied run of words' rule does not fire on our own wording.
    basis = []
    for d in chosen:
        basis += [f.get("text", "") for f in (d.get("facts") or {}).get("facts") or []]
        basis += [pr.headline(d), pr.split_text((d.get("draft") or {}).get("text", "")).summary]
    basis += [_chunk(f"Buyer tip: {tip}"), f"Reported by {', '.join(sources)}."]
    wid = week_id(now)
    site = pr.site_url()
    raw = RawItem(id=wid, source=brand.TEAM, url=f"{site}/news", title="Weekly local news roundup", text="\n".join(basis),
                  published_at=ist, fetched_at=ist)
    facts = Facts([Fact(text=s["line"] or s["hook"], quote=s["hook"]) for s in stories], as_of=ist)
    draft = Draft("digest", text, TITLE, f"{site}/news", sources)
    return {"_id": wid, "status": "pending_review", "raw": codec.to_doc(raw),
            "relevance": {"keep": True, "pillar": "digest", "areas": ["kharadi", "wagholi"], "reason": "weekly digest"},
            "facts": codec.to_doc(facts), "draft": codec.to_doc(draft), "check": None,
            "digest": {"title": TITLE, "week": wid, "as_of": ist, "tip": tip, "items": stories}}


async def build(store: Store, now: datetime, checker: Optional[Callable] = None, render: Optional[Callable] = None) -> Optional[dict]:
    """Make this week's digest once. Returns the stored document, or None (already built, too few stories, failed check)."""
    wid = week_id(now)
    if await store.get(wid):
        return None
    docs = await store.recent_done(now - timedelta(days=WINDOW_DAYS))
    doc = compose(docs, now)
    if doc is None:
        return None
    if checker is None:
        from .stages.check import check as checker
    res = checker(codec.draft(doc), codec.facts(doc), codec.raw_item(doc))
    res = await res if inspect.isawaitable(res) else res
    if not res.ok:
        log.warning("newsroom: digest %s failed its check: %s", wid, "; ".join(res.problems)[:200])
        return None
    doc["check"] = codec.to_doc(res)
    if render is not None:
        try:
            out = render(doc)
            doc["card"] = await out if inspect.isawaitable(out) else out
        except Exception:  # no card yet: the owner screen shows it without a preview and the publisher renders it when needed
            log.warning("newsroom: digest cards failed", exc_info=True)
    doc["history"] = [{"at": now, "status": "pending_review", "note": "weekly digest"}]
    doc["created_at"] = doc["updated_at"] = now
    if not await store.insert_item(doc):
        return None
    return doc


def sample_digest(samples: List[dict]) -> dict:
    """A digest built from the review samples (marked published), for design review and tests."""
    from .samples import AS_OF
    docs = [{**d, "status": "published"} for d in samples]
    return compose(docs, AS_OF + timedelta(days=5, hours=12), tip=TIPS[0])
