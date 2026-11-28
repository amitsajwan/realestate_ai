"""The topic finder: once a week, the reports of the last 30 days that no tracker's rules match are grouped by subject, and a
subject with MIN_REPORTS reports from MIN_PUBLISHERS publishers becomes a "new tracker?" item on Studio's Trackers desk, with a
draft definition the owner adds with one click (pune-intelligence.md A.4, 2026-11-28).

Rules first: reports already on a tracker are left out, and only reports whose headline names Pune or one of its places count.
Grouping is plain code: two reports are one subject when the filter calls them the same story, or when their headlines share two
subject words (generic words like 'Pune' or 'civic' do not count, and at least one shared word must say more than 'road' or
'metro'). The draft (name, kind, stages, searches, rules, a first status line) is a model's guess, each part checked: a name and
searches made of the headlines' own words, rules that compile and match most of the group's headlines, a status line that passes
stages.check.check_status_line. A part that fails falls back to the headlines alone (the shared words as name, rules and search;
no stages; no status, which the owner then writes). Nothing here reaches the site until the owner adds the tracker.

The week's candidates, the dismissed ones and the added ones live in one newsroom_status document (`topic_finder`)."""
import json
import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from . import presentation as pr
from . import tracker_topics, trackers
from .stages.check import check_status_line
from .stages.filter import pune_named, same_story
from .store import Store

log = logging.getLogger(__name__)

MARK = "topic_finder"
WINDOW = timedelta(days=30)
SCAN_LIMIT = 5000
MIN_REPORTS = 3
MIN_PUBLISHERS = 2
CANDIDATES_MAX = 8
DRAFTS_PER_RUN = 3  # model calls a week at most
REPORTS_KEPT = 12
NAME_MAX = 60
STAGES_MAX = 6

_STOP = {"the", "a", "an", "of", "in", "on", "to", "for", "and", "at", "by", "is", "as", "with", "from", "says", "after", "new",
         "its", "it", "be", "are", "was", "will", "may", "into", "over", "under", "this", "that", "than", "not", "but", "has", "have",
         "had", "who", "what", "why", "how", "when", "more", "now", "get", "gets", "set", "sets", "amid", "near", "two", "one"}
# words that say where or who, not what: they never make a subject on their own
_GENERIC = {"pune", "pimpri", "chinchwad", "pcmc", "pmc", "pmrda", "maharashtra", "city", "civic", "body", "corporation",
            "municipal", "state", "government", "govt", "officials", "official", "residents", "citizens", "people", "news", "report",
            "reports", "plan", "plans", "planned", "project", "projects", "work", "works", "move", "moves", "seeks", "likely",
            "expected", "soon", "today", "week", "month", "year", "crore", "lakh", "punekar", "commuters", "traffic", "relief",
            "ease", "boost", "major", "first", "latest", "update", "updates", "details", "check", "inside"}
# subject words too common to tie two headlines together alone
_WEAK = {"road", "roads", "metro", "station", "stations", "bridge", "flyover", "water", "land", "line", "route", "phase",
         "tax", "property", "homes", "housing", "rate", "rates"}
_NAME_EXTRA = {"pune", "status", "project", "plan", "road", "rules", "tracker"}

DRAFT_SYSTEM = """You help an editor in Pune start a status page for home buyers about one thing that keeps changing (a road, a
metro line, a bridge, a rule, a rate). You get the headlines of recent reports about it. Answer in JSON only:
{"name": "<short name of the thing, from the headlines' words>", "kind": "project" or "rule" or "rate",
 "summary": "<one plain sentence: what it is>", "stages": ["<stage>", ...] (2 to 6 for a project, [] for a rule or rate),
 "queries": ["<Google News search>", ...] (2 to 4, a few words each, from the headlines),
 "match": {"all": ["<regex>"], "any": ["<regex>"], "not": ["<regex>"]} (lower-case patterns that match these headlines),
 "status": "<where it stands today, one or two plain sentences>"}
Rules: use only what the headlines say; no figure, date or name that is not in them; never copy a headline; approved is not
built and built is not open."""


def _utc(d: Optional[datetime]) -> Optional[datetime]:
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


def _day(d: Optional[datetime]) -> str:
    d = _utc(d)
    return d.astimezone(timezone(timedelta(hours=5, minutes=30))).date().isoformat() if d else ""


def week_of(now: datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


def subject_words(title: str) -> List[str]:
    """The words of a headline that can say what it is about, in order, once each."""
    words = re.findall(r"[a-z]+", trackers.clean_headline(title).lower())
    return list(dict.fromkeys(w for w in words if len(w) >= 3 and w not in _STOP and w not in _GENERIC))


def _ties(a: set, b: set) -> bool:
    shared = a & b
    return len(shared) >= 2 and any(w not in _WEAK for w in shared)


def group(rows: List[dict]) -> List[List[dict]]:
    """Reports ({title, source, date, url}) grouped by subject: a report joins the first group holding the same story or a
    headline it shares two subject words with. Groups keep the reports' order (pass them newest first)."""
    groups: List[List[dict]] = []
    for r in rows:
        words = set(subject_words(r.get("title", "")))
        hit = next((g for g in groups if any(same_story(m["title"], r["title"]) or _ties(set(subject_words(m["title"])), words)
                                             for m in g)), None)
        if hit is None:
            groups.append([r])
        else:
            hit.append(r)
    return groups


def core_words(rows: List[dict]) -> List[str]:
    """The subject words in at least half of the group's headlines, most common first, ties by their place in the newest one."""
    counts = Counter(w for r in rows for w in subject_words(r["title"]))
    order: Dict[str, int] = {}
    for w in (w for r in rows for w in subject_words(r["title"])):
        order.setdefault(w, len(order))
    keep = [w for w, n in counts.items() if n * 2 >= len(rows)]
    return sorted(keep, key=lambda w: (-counts[w], order[w]))


def _slugify(text: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", (text or "").lower()))[:60].strip("-")


def _matches_most(match: dict, titles: List[str]) -> bool:
    try:
        rules = tracker_topics.compile_rules(match)
    except (re.error, TypeError, AttributeError):
        return False
    if not (rules["all"] or rules["any"]):
        return False
    hits = sum(tracker_topics.hit(rules, pr.one_line(t).lower()) for t in titles)
    return hits * 2 >= len(titles) and hits > 0


def fallback_draft(rows: List[dict]) -> Optional[dict]:
    """The draft from the headlines alone: the two or three shared subject words as the name, the rule and the search."""
    core = core_words(rows)
    if len(core) < 2 or all(w in _WEAK for w in core[:2]):
        return None
    top = core[:2]
    return {"name": " ".join(w.title() for w in core[:3]), "kind": "project", "summary": "", "stages": [],
            "queries": ["Pune " + " ".join(top)], "match": {"all": [rf"\b{re.escape(w)}" for w in top], "any": [], "not": []},
            "status": None, "by": "rules"}


def check_draft(out, rows: List[dict], base: dict, now: datetime) -> dict:
    """The model's draft made safe part by part; each part that fails keeps the headline-only fallback in `base`."""
    if not isinstance(out, dict):
        return base
    titles = [r["title"] for r in rows]
    text = " ".join(trackers.clean_headline(t) for t in titles).lower()
    words = set(re.findall(r"[a-z]+", text)) | _NAME_EXTRA
    d = dict(base)
    took = False
    name = pr.one_line(str(out.get("name") or ""))
    if 3 <= len(name) <= NAME_MAX and all(w in words for w in re.findall(r"[a-z]+", name.lower()) if len(w) >= 3):
        d["name"], took = name, True
    if out.get("kind") in trackers.KINDS:
        d["kind"] = out["kind"]
    stages = out.get("stages")
    if isinstance(stages, list) and len(stages) <= STAGES_MAX and all(isinstance(s, str) and 2 <= len(s.strip()) <= 40 for s in stages):
        d["stages"] = [pr.one_line(s) for s in stages] if d["kind"] == "project" else []
    qs = out.get("queries")
    if isinstance(qs, list) and 1 <= len(qs) <= 4 and all(
            isinstance(q, str) and len(q.split()) <= 6 and all(w in words for w in re.findall(r"[a-z]+", q.lower()) if len(w) >= 3)
            for q in qs):
        d["queries"] = [pr.one_line(q) for q in qs]
    match = out.get("match")
    if isinstance(match, dict) and all(isinstance(match.get(k, []), list) for k in ("all", "any", "not")):
        clean = {k: [str(p) for p in match.get(k, [])][:6] for k in ("all", "any", "not")}
        if _matches_most(clean, titles):
            d["match"] = clean
    allowed = set(re.findall(r"[A-Za-z]+", " ".join([d["name"], *d["stages"], *(r.get("source", "") for r in rows)])))
    status = pr.one_line(str(out.get("status") or ""))
    if 12 <= len(status) <= trackers.STATUS_MAX and not check_status_line(status, titles, allowed):
        d["status"] = status
    summary = pr.one_line(str(out.get("summary") or ""))
    if summary and len(summary) <= 200 and not check_status_line(summary, titles, allowed):
        d["summary"] = summary
    if took or d["status"]:
        d["by"] = "model"
    return d


async def _unmatched(store: Store, now: datetime) -> List[dict]:
    """The last WINDOW's collected reports about Pune that no tracker matches, newest first, one per headline."""
    rows, seen = [], set()
    for raw in await store.recent_raw("", now - WINDOW, SCAN_LIMIT):
        title = pr.one_line(raw.title)
        if (raw.source or "").strip().lower() == "maharera" or not title or title.lower() in seen:
            continue
        if tracker_topics.any_topic(title) or not pune_named(title):
            continue
        seen.add(title.lower())
        rows.append({"title": title, "source": pr.one_line(raw.source)[:80], "url": raw.url, "date": _utc(raw.published_at or raw.fetched_at)})
    return sorted(rows, key=lambda r: r["date"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)


async def find_due(store: Store, llm, now: datetime) -> int:
    """Once an ISO week: group the unmatched reports and keep the subjects big enough as this week's candidates (dismissed and
    added ones never come back). Returns how many candidates there are; 0 when it already ran this week."""
    mark = await store.get_mark(MARK)
    week = week_of(now)
    if mark.get("week") == week:
        return 0
    await trackers.refresh(store)
    gone = set(mark.get("dismissed") or []) | set(mark.get("added") or [])
    taken = set(trackers.definitions())
    found: List[dict] = []
    asked = 0
    for g in group(await _unmatched(store, now)):
        publishers = {r["source"] for r in g if r["source"]}
        if len(g) < MIN_REPORTS or len(publishers) < MIN_PUBLISHERS:
            continue
        base = fallback_draft(g)
        if base is None:
            continue
        key = "-".join(sorted(core_words(g)[:2]))
        if key in gone or any(c["key"] == key for c in found):
            continue
        draft = base
        if llm is not None and asked < DRAFTS_PER_RUN:
            asked += 1
            try:
                out = await llm.json(DRAFT_SYSTEM, "Headlines, newest first:\n" + "\n".join(
                    f"- {_day(r['date'])} | {r['source']} | {trackers.clean_headline(r['title'])}" for r in g[:REPORTS_KEPT]))
            except Exception as e:
                log.warning("topic finder: draft failed: %s", e)
                out = None
            draft = check_draft(out, g, base, now)
        slug = _slugify(draft["name"])
        if not slug or slug in taken:
            continue
        found.append({**draft, "key": key, "slug": slug, "status_date": _day(g[0]["date"]),
                      "sources": list(dict.fromkeys(r["source"] for r in g[:3] if r["source"])),
                      "report_count": len(g), "publishers": len(publishers),
                      "reports": [{"date": _day(r["date"]), "title": trackers.clean_headline(r["title"]), "source": r["source"],
                                   "url": r["url"]} for r in g[:REPORTS_KEPT]], "found_at": now})
        if len(found) >= CANDIDATES_MAX:
            break
    await store.set_mark(MARK, week=week, candidates=found, at=now)
    log.info("topic finder: %d new tracker candidates for %s", len(found), week)
    return len(found)


async def candidates(store: Store) -> List[dict]:
    """This week's candidates the owner has not added or dismissed, biggest first."""
    mark = await store.get_mark(MARK)
    gone = set(mark.get("dismissed") or []) | set(mark.get("added") or [])
    rows = [{k: v for k, v in c.items() if k != "found_at"} for c in mark.get("candidates") or [] if c.get("key") not in gone]
    return sorted(rows, key=lambda c: -c.get("report_count", 0))


async def _remember(store: Store, field: str, key: str) -> None:
    mark = await store.get_mark(MARK)
    await store.set_mark(MARK, **{field: list(dict.fromkeys([*(mark.get(field) or []), key]))})


async def dismiss(store: Store, key: str) -> bool:
    if not any(c["key"] == key for c in await candidates(store)):
        return False
    await _remember(store, "dismissed", key)
    return True


async def add(store: Store, key: str, edits: Dict, now: datetime) -> str:
    """Save a candidate as a tracker in Mongo, with the owner's edits (name, status, date, stage, stages, kind, places, means),
    and attach its reports of the last weeks; returns its slug. Raises trackers.StatusError with a message for the owner."""
    cand = next((c for c in await candidates(store) if c["key"] == key), None)
    if cand is None:
        raise trackers.StatusError("That suggestion is gone: it was added or dismissed already.")
    name = pr.one_line(str(edits.get("name") or cand["name"]))[:NAME_MAX]
    slug = _slugify(name)
    await trackers.refresh(store, force=True)
    if not slug or slug in trackers.definitions():
        raise trackers.StatusError("A tracker with that name exists already: give it another name.")
    kind = edits.get("kind") if edits.get("kind") in trackers.KINDS else cand.get("kind", "project")
    stages = [pr.one_line(str(s))[:40] for s in (edits.get("stages") if isinstance(edits.get("stages"), list) else cand.get("stages") or [])
              if str(s).strip()][:STAGES_MAX] if kind == "project" else []
    stub = {"stages": stages}
    stage = edits.get("stage")
    row = trackers.check_update(stub, str(edits.get("status") or cand.get("status") or ""), stage if isinstance(stage, int) else None,
                                str(edits.get("date") or cand.get("status_date") or ""), now)
    definition = {
        "slug": slug, "name": name, "title": f"{name}: status and timeline", "summary": pr.one_line(str(edits.get("summary") or cand.get("summary") or "")),
        "kind": kind, "areas": [], "places": [str(p) for p in edits.get("places") or []][:12], "stages": stages,
        "match": cand["match"], "queries": cand.get("queries") or [], "means": pr.one_line(str(edits.get("means") or "")),
        "history": [{**{k: v for k, v in row.items() if k != "stage" or v is not None}, "sources": list(cand.get("sources") or [])}],
    }
    try:
        trackers.prepare(definition)
    except Exception:
        raise trackers.StatusError("The draft's matching rules do not work; dismiss it and add the tracker as a file.")
    if not await store.add_tracker_definition(slug, json.loads(json.dumps(definition)), now):
        raise trackers.StatusError("A tracker with that name exists already: give it another name.")
    await _remember(store, "added", key)
    await trackers.refresh(store, force=True)
    await trackers.attach_past(store, slug, now)
    return slug
