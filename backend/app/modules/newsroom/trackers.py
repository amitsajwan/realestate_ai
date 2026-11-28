"""Trackers: one durable page per thing in Pune that keeps changing and changes a buyer's decision (an airport, a road, a metro line,
a hospital, a water rule, the repo rate). Decided 2026-10-20 in docs/plan/news-strategy.md: one-day news does not rank and goes
stale; a page that says where a thing stands today, with the dated reports behind it, stays true and is what people search for.

What a tracker is lives in tracker_data/<slug>.json (name, stages, which areas and places it touches, the matching rules, its own
Google News searches, what it means for a buyer, and the dated status history we wrote from the reports). A tracker the owner adds
in Studio from the topic finder (topic_finder.py) has the same shape and lives in Mongo (`definition` on its newsroom_trackers
document); definitions() merges both, and a file wins over a Studio one of the same slug. Three things change at run time and live
in Mongo (store.py):
- reports: every collected report whose headline matches a tracker's rules is attached to it, whatever the news filter decided
  (most were dropped as 'no target area', yet a Purandar airport report is exactly what the airport's page needs). Rules only,
  no model: a wrong match is a cited headline on the wrong page, and the owner can hide it in Studio.
- suggestions: when new reports arrive, a model reads them with the current status and suggests the next line, or says it still
  holds (`suggest_due`). The answer goes through check_suggestion (stages.check.check_status_line: every figure, date and name
  must be in the reports, no copied headline, 'opened' only when a report says so); a failed or missing answer means no suggestion.
- status updates: a checked suggestion becomes the status by itself (`apply_due`, NEWSROOM_TRACKER_AUTO, on by default since
  2026-11-28: until then every tracker's status had stayed as first written, because suggestions only waited in Studio). The old
  line stays in the history. The model never decides that a thing is open: a move to the tracker's last stage, or a line that
  says it opened, was inaugurated, runs or started operations, waits for the owner in Studio (`needs_owner`). The owner can
  still write any line in Studio, and it wins over the model's on the same day.
"""
import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from app.core import areas as core_areas
from app.core import pune_places

from . import presentation as pr
from . import tracker_topics
from .stages.check import check_status_line
from .stages.filter import same_story
from .store import Store

log = logging.getLogger(__name__)

DATA = Path(__file__).with_name("tracker_data")
KINDS = ("project", "rule", "rate")
FIRST_SCAN = timedelta(days=60)  # how far back the first run looks for reports to attach (we keep about this much)
SCAN_LIMIT = 5000
STATUS_MAX = 420
GROUP_DAYS = 2  # reports of the same story this many days apart are one timeline line
PUBLIC_GROUPS = 15
MARK = "trackers"
SUGGEST_PER_RUN = 3  # model calls per newsroom cycle at most
SUGGEST_REPORTS = 12  # newest new reports the model reads
_PUBLISHER_TAIL = re.compile(r"\s+[-|–—]\s+[^-|–—]{2,40}$")  # "... | Hindustan Times"
_CITY_HEAD = re.compile(r"^(pune|pimpri[- ]chinchwad)\s*:\s*", re.I)  # "Pune: ..."


def _utc(d: Optional[datetime]) -> Optional[datetime]:
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


REFRESH_SECONDS = 60  # how long the Studio-added trackers read from Mongo are trusted before they are read again
NEXT_MAX = 160
FAQ_MAX = 8
_DEFINED: Dict[str, dict] = {}
_DEFINED_FOR: List[tuple] = [(None, 0.0)]  # (the db they were read from, until when): a test's fake db is never another's


def prepare(d: dict) -> dict:
    """A tracker definition checked and its rules compiled; raises on a broken one (a slug, a kind, a status history and rules
    that compile are required)."""
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(d.get("slug") or "")), "slug"
    assert d.get("kind") in KINDS and d.get("history") and all(h.get("status") for h in d["history"]), "kind and history are required"
    return {**d, "_rules": tracker_topics.compile_rules(d.get("match", {}))}


@lru_cache(maxsize=1)
def file_definitions() -> Dict[str, dict]:
    """Every tracker file, by slug, in file-name order. A broken file is skipped with a warning, never a crash of the newsroom."""
    out = {}
    for path in sorted(DATA.glob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            assert d.get("slug") == path.stem, "the slug is the file name"
            out[d["slug"]] = prepare(d)
        except Exception as e:
            log.warning("trackers: %s skipped: %s", path.name, e)
    return out


def definitions() -> Dict[str, dict]:
    """Every tracker: the files in file-name order, then the ones the owner added in Studio (as last read by `refresh`)."""
    files = file_definitions()
    return {**files, **{k: v for k, v in _DEFINED.items() if k not in files}}


async def refresh(store: Store, force: bool = False) -> int:
    """Read the Studio-added trackers from Mongo (at most once a minute per database) and hand their rules and searches to
    tracker_topics, so the news filter and the Google News searches know them too. Returns how many there are."""
    db, until = _DEFINED_FOR[0]
    if not force and db is store.db and time.monotonic() < until:
        return len(_DEFINED)
    out: Dict[str, dict] = {}
    for st in await store.tracker_states():
        d = st.get("definition")
        if not isinstance(d, dict):
            continue
        try:
            out[st["_id"]] = prepare({**d, "slug": st["_id"], "from_studio": True})
        except Exception as e:
            log.warning("trackers: Studio tracker %s skipped: %s", st.get("_id"), e)
    _DEFINED.clear()
    _DEFINED.update(out)
    tracker_topics.set_defined(out)
    _DEFINED_FOR[0] = (store.db, time.monotonic() + REFRESH_SECONDS)
    return len(out)


def get(slug: str) -> Optional[dict]:
    return definitions().get(slug)


def matches(defn: dict, title: str) -> bool:
    """The tracker's rules on a headline: every `all` pattern, at least one `any` pattern (when there are any), no `not` pattern."""
    t = pr.one_line(title).lower()
    rules = defn["_rules"]
    return (bool(t) and all(p.search(t) for p in rules["all"]) and (not rules["any"] or any(p.search(t) for p in rules["any"]))
            and not any(p.search(t) for p in rules["not"]))


def clean_headline(title: str) -> str:
    """A publisher's headline as we cite it: one line, without the ' | Publisher' tail or a 'Pune:' lead-in."""
    t = _CITY_HEAD.sub("", _PUBLISHER_TAIL.sub("", pr.one_line(title)))
    return t[:1].upper() + t[1:]


async def attach_new(store: Store, now: datetime) -> int:
    """Attach the reports collected since the last pass to the trackers their headlines match; returns how many were attached.
    A MahaRERA record is a project, never a report about a tracked thing."""
    mark = await store.get_mark(MARK)
    since = _utc(mark.get("scanned_to")) or now - FIRST_SCAN
    added = 0
    for raw in await store.recent_raw("", since, SCAN_LIMIT):
        if (raw.source or "").strip().lower() == "maharera":
            continue
        for slug, defn in definitions().items():
            if matches(defn, raw.title):
                added += await store.add_tracker_report({
                    "_id": f"{slug}|{raw.id}", "slug": slug, "item_id": raw.id, "title": pr.one_line(raw.title)[:300],
                    "source": pr.one_line(raw.source)[:80], "url": raw.url, "date": _utc(raw.published_at or raw.fetched_at), "attached_at": now,
                    "hidden": False})
    await store.set_mark(MARK, scanned_to=now)
    return added


async def attach_past(store: Store, slug: str, now: datetime) -> int:
    """A new tracker (added in Studio) gets the reports of the last FIRST_SCAN days that its rules match, as the first run gave
    the file trackers theirs; returns how many were attached."""
    defn = get(slug)
    if defn is None:
        return 0
    added = 0
    for raw in await store.recent_raw("", now - FIRST_SCAN, SCAN_LIMIT):
        if (raw.source or "").strip().lower() != "maharera" and matches(defn, raw.title):
            added += await store.add_tracker_report({
                "_id": f"{slug}|{raw.id}", "slug": slug, "item_id": raw.id, "title": pr.one_line(raw.title)[:300],
                "source": pr.one_line(raw.source)[:80], "url": raw.url, "date": _utc(raw.published_at or raw.fetched_at), "attached_at": now,
                "hidden": False})
    return added


def _day(d) -> str:
    """A history date ('2026-10-23') or a report datetime, as the ISO day."""
    if isinstance(d, datetime):
        return d.astimezone(timezone(timedelta(hours=5, minutes=30))).date().isoformat() if d.tzinfo else d.date().isoformat()
    return str(d or "")[:10]


def history(defn: dict, state: Optional[dict]) -> List[dict]:
    """The status history, oldest first: what the tracker file says, then the owner's updates from Studio (a same-day update
    comes after the file's line, so it wins)."""
    rows = [{**h, "from": "file"} for h in defn["history"]]
    rows += [{**u, "from": "studio"} for u in (state or {}).get("updates") or []]
    return sorted(rows, key=lambda h: (str(h.get("date") or ""), h["from"] == "studio"))


def _stage(defn: dict, value) -> Optional[int]:
    stages = defn.get("stages") or []
    return value if isinstance(value, int) and 0 <= value < len(stages) else None


def groups(reports: List[dict]) -> List[dict]:
    """Reports newest first, folded into one line per story: the same story from several publishers within GROUP_DAYS days is one
    line with the first report's headline and the others as 'also reported by'. Hidden reports are left out."""
    out: List[dict] = []
    for r in sorted((r for r in reports if not r.get("hidden")), key=lambda r: _utc(r.get("date")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True):
        when = _utc(r.get("date"))
        hit = next((g for g in out if g["_at"] and when and abs(g["_at"] - when) <= timedelta(days=GROUP_DAYS)
                    and same_story(g["_title"], r.get("title", ""))), None)
        link = {"name": r.get("source") or "", "url": r.get("url") or "", "is_redirect": pr.is_google_redirect(r.get("url") or "")}
        if hit is not None:
            if link["name"] not in {hit["source"], *(a["name"] for a in hit["also"])}:
                hit["also"].append(link)
            continue
        out.append({"_at": when, "_title": r.get("title", ""), "date": _day(when), "headline": clean_headline(r.get("title", "")),
                    "source": link["name"], "url": link["url"], "is_redirect": link["is_redirect"], "also": []})
    return [{k: v for k, v in g.items() if not k.startswith("_")} for g in out]


def place_slugs(defn: dict) -> List[str]:
    """The Pune places (app.core.pune_places, the /projects/area/<place> pages) the tracker touches, as page slugs; a key
    ('keshav_nagar') is taken too and an unknown place is dropped."""
    out = []
    for p in defn.get("places") or []:
        found = pune_places.BY_SLUG.get(str(p)) or pune_places.BY_KEY.get(str(p))
        if found and found.slug not in out:
            out.append(found.slug)
    return out


def current_stage(defn: dict, hist: List[dict]) -> Optional[int]:
    """The newest stage the history names (a line without a stage keeps the one before)."""
    return next((_stage(defn, h.get("stage")) for h in reversed(hist) if _stage(defn, h.get("stage")) is not None), None)


def _next(defn: dict, status_day: str) -> Optional[dict]:
    """The next date the file expects ({date: 'YYYY-MM[-DD]', what}), shown only while it is still ahead of the status: once the
    status is newer than it, whatever was expected has happened or slipped, and the status says which."""
    n = defn.get("next")
    if not isinstance(n, dict) or not re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", str(n.get("date") or "")) or not n.get("what"):
        return None
    if str(n["date"]) < status_day[:len(str(n["date"]))]:
        return None
    return {"date": str(n["date"]), "what": pr.one_line(str(n["what"]))[:NEXT_MAX]}


def _faq(defn: dict) -> List[dict]:
    return [{"q": pr.one_line(str(f["q"])), "a": pr.one_line(str(f["a"]))} for f in (defn.get("faq") or [])[:FAQ_MAX]
            if isinstance(f, dict) and f.get("q") and f.get("a")]


def view(defn: dict, state: Optional[dict], reports: List[dict], full: bool = True) -> dict:
    """The public shape of one tracker. `full` adds the history and the timeline the tracker page shows."""
    hist = history(defn, state)
    now_row = hist[-1]
    stage = current_stage(defn, hist)
    tl = groups(reports)
    status_day = _day(now_row.get("date"))
    newer = [g for g in tl if g["date"] > status_day]
    out = {
        "slug": defn["slug"], "name": defn["name"], "title": defn.get("title") or defn["name"], "summary": defn.get("summary", ""),
        "kind": defn["kind"],
        "areas": [{"key": a, "slug": core_areas.BY_KEY[a].slug, "name": core_areas.BY_KEY[a].name} for a in defn.get("areas", []) if a in core_areas.BY_KEY],
        "places": [{"slug": p, "name": pune_places.BY_SLUG[p].name} for p in place_slugs(defn)],
        "stages": list(defn.get("stages") or []), "stage": stage,
        "status": pr.one_line(now_row["status"]), "status_date": status_day, "status_sources": list(now_row.get("sources") or []),
        "next": _next(defn, status_day),
        "means": pr.one_line(defn.get("means", "")),
        "updated": max([status_day] + [g["date"] for g in tl[:1]]),
        "report_count": sum(1 + len(g["also"]) for g in tl), "newer_reports": len(newer),
        "latest": tl[0] if tl else None,
        "checked_at": _day(_utc((state or {}).get("checked_at"))) or None,
    }
    if full:
        out["history"] = [{"date": _day(h.get("date")), "stage": _stage(defn, h.get("stage")), "status": pr.one_line(h["status"]),
                           "sources": list(h.get("sources") or [])} for h in reversed(hist)]
        out["timeline"] = tl[:PUBLIC_GROUPS]
        out["faq"] = _faq(defn)
    return out


async def all_views(store: Store, area: Optional[str] = None, full: bool = False) -> List[dict]:
    """Every tracker, most recently changed first; `area` (a key or page slug) keeps the trackers that name that area plus the
    city-wide rates and rules (a home-loan rate touches every buyer)."""
    key = None
    if area is not None:
        found = core_areas.get(area)
        if not found:
            return []
        key = found.key
    await refresh(store)
    states = {d["_id"]: d for d in await store.tracker_states()}
    out = []
    for slug, defn in definitions().items():
        if key and key not in defn.get("areas", []) and not (defn["kind"] == "rate"):
            continue
        out.append(view(defn, states.get(slug), await store.tracker_reports(slug), full=full))
    return sorted(out, key=lambda v: v["updated"], reverse=True)


async def one_view(store: Store, slug: str) -> Optional[dict]:
    await refresh(store)
    defn = get(slug)
    if defn is None:
        return None
    return view(defn, await store.tracker_state(slug), await store.tracker_reports(slug))


# --- Studio --------------------------------------------------------------------------------------------------------------------

def _since(defn: dict, state: Optional[dict]) -> Optional[datetime]:
    """Reports after this moment are new to the owner: the later of the last check and the day the current status is true from."""
    checked = _utc((state or {}).get("checked_at"))
    day = _day(history(defn, state)[-1].get("date"))
    status_at = datetime.fromisoformat(day).replace(tzinfo=timezone.utc) if day else None
    return max(d for d in (checked, status_at) if d) if (checked or status_at) else None


def new_reports(defn: dict, state: Optional[dict], reports: List[dict]) -> List[dict]:
    """The reports the owner has not seen yet, newest first (hidden ones never count)."""
    since = _since(defn, state)
    rows = sorted(reports, key=lambda r: _utc(r.get("date")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return [r for r in rows if since and _utc(r.get("date")) and _utc(r["date"]) > since and not r.get("hidden")]


def studio_view(defn: dict, state: Optional[dict], reports: List[dict]) -> dict:
    """What the owner sees: the public view, plus every attached report (hidden ones too, so a hide can be undone), the reports
    that came in since the status was last checked, and the model's suggestion for those reports (none when it failed)."""
    v = view(defn, state, reports)
    fresh = {r["item_id"] for r in new_reports(defn, state, reports)}
    rows = sorted(reports, key=lambda r: _utc(r.get("date")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    v["reports"] = [{"id": r["item_id"], "date": _day(_utc(r.get("date"))), "title": clean_headline(r.get("title", "")),
                     "source": r.get("source", ""), "url": r.get("url", ""), "hidden": bool(r.get("hidden")),
                     "new": r["item_id"] in fresh} for r in rows[:80]]
    v["new_count"] = len(fresh)
    sug = (state or {}).get("suggestion") or {}
    # only about reports that are still new: once the owner has dealt with them, the suggestion is gone
    ok = bool(fresh) and bool(sug.get("ok")) and set(sug.get("for_ids") or []) <= fresh
    v["suggestion"] = {k: sug.get(k) for k in ("changed", "status", "stage", "date", "sources", "reason", "held")} if ok else None
    last = ((state or {}).get("updates") or [None])[-1] or {}
    v["auto_updated"] = last.get("by") == AUTO_BY and _day(last.get("date")) == v["status_date"]   # the line on the site is the model's
    v["from_studio"] = bool(defn.get("from_studio"))
    return v


SUGGEST_SYSTEM = """You keep a status page for home buyers in Pune about one thing that keeps changing (a road, a metro line, an
airport, a hospital, a rule or a rate). You get the current status line and the headlines of the reports that came in since. Decide
whether the reports move the status. Answer in JSON only:
{"changed": true or false, "stage": <index from the stage list, or null>, "status": "<the new status line>",
 "date": "YYYY-MM-DD", "sources": ["<publisher>"], "reason": "<one short sentence for the editor>"}
Rules:
- Use only what the headlines and the current status say. No figure, date or name that is not in them.
- Plain English, one or two sentences, at most 60 words, in your own words: never copy a headline.
- Do not write dates or publisher names in the status; the page shows them next to it.
- Approved is not built and built is not open: say opened, inaugurated or running only when a headline says it happened.
- If the reports only repeat or comment on what the status already says, answer changed=false and say why in reason.
- When changed=true: date is the day of the newest report that supports the change, sources are its publishers from the list, and
  the stage moves only when a headline shows it moved."""


def _prompt(defn: dict, state: Optional[dict], fresh: List[dict]) -> str:
    now = history(defn, state)[-1]
    stages = defn.get("stages") or []
    lines = [f"Thing: {defn['name']} ({defn.get('summary', '')})",
             "Stages: " + (", ".join(f"{i}={s}" for i, s in enumerate(stages)) if stages else "none (answer stage null)"),
             f"Current status ({_day(now.get('date'))}, stage {now.get('stage')}): {pr.one_line(now['status'])}",
             "New reports, newest first:"]
    lines += [f"- {_day(_utc(r.get('date')))} | {r.get('source', '')} | {clean_headline(r.get('title', ''))}" for r in fresh]
    return "\n".join(lines)


def check_suggestion(defn: dict, state: Optional[dict], fresh: List[dict], out: Optional[dict], now: datetime) -> Optional[dict]:
    """The model's answer made safe, or None: the shape, a stage the tracker has, a date one of the reports carries, publishers from
    the reports, and the status-line checks against the current status and the headlines."""
    if not isinstance(out, dict) or not isinstance(out.get("changed"), bool):
        return None
    current = history(defn, state)[-1]
    reason = pr.one_line(str(out.get("reason") or ""))[:200]
    if not out["changed"]:
        return {"changed": False, "status": pr.one_line(current["status"]), "stage": _stage(defn, current.get("stage")),
                "date": _day(current.get("date")), "sources": list(current.get("sources") or []), "reason": reason}
    publishers = {r.get("source", "") for r in fresh}
    sources = [x for x in dict.fromkeys(str(x) for x in out.get("sources") or []) if x in publishers][:6]
    stage = out.get("stage")
    if stage is not None and _stage(defn, stage) is None:
        return None
    try:
        row = check_update(defn, str(out.get("status") or ""), stage, str(out.get("date") or ""), now)
    except StatusError:
        return None
    if row["date"] not in {_day(_utc(r.get("date"))) for r in fresh} or not sources:
        return None
    evidence = [pr.one_line(current["status"])] + [clean_headline(r.get("title", "")) for r in fresh]
    allowed = {w for x in [defn["name"], *(defn.get("stages") or []), *publishers] for w in re.findall(r"[A-Za-z]+", x)}
    if check_status_line(row["status"], evidence, allowed):
        return None
    return {**row, "changed": True, "sources": sources, "reason": reason}


async def suggest_due(store: Store, llm, now: datetime) -> int:
    """Ask the model about the trackers whose new reports it has not read yet (at most SUGGEST_PER_RUN a run); returns how many
    suggestions passed. A failed answer is remembered for those reports, so it is not asked again until more arrive."""
    if llm is None:
        return 0
    states = {d["_id"]: d for d in await store.tracker_states()}
    made = asked = 0
    for slug, defn in definitions().items():
        if asked >= SUGGEST_PER_RUN:
            break
        state = states.get(slug)
        fresh = new_reports(defn, state, await store.tracker_reports(slug))[:SUGGEST_REPORTS]
        ids = sorted(r["item_id"] for r in fresh)
        if not fresh or sorted(((state or {}).get("suggestion") or {}).get("for_ids") or []) == ids:
            continue
        asked += 1
        try:
            out = await llm.json(SUGGEST_SYSTEM, _prompt(defn, state, fresh))
        except Exception as e:
            log.warning("trackers: suggestion for %s failed: %s", slug, e)
            out = None
        good = check_suggestion(defn, state, fresh, out, now)
        await store.set_tracker_suggestion(slug, {**(good or {}), "ok": good is not None, "for_ids": ids, "at": now})
        made += good is not None
    return made


AUTO_BY = "auto"  # `by` on a status update that a checked suggestion made by itself
# a line that says the thing opened or runs is for the owner to put on the site: approved is not built and built is not open
_OPEN_CLAIM = re.compile(r"\b(open\w*|inaugurat\w*|running|runs|start(s|ed)?\s+operations?|operational|commissioned)\b", re.I)


def needs_owner(defn: dict, state: Optional[dict], suggestion: dict) -> Optional[str]:
    """Why a checked suggestion still waits for the owner, or None when it may go live by itself: a move to the tracker's last
    stage ('Open'), or a line that says it opened, was inaugurated, runs or started operations."""
    stages = defn.get("stages") or []
    last = len(stages) - 1
    if stages and suggestion.get("stage") == last and current_stage(defn, history(defn, state)) != last:
        return f"moves it to the last stage ({stages[last]})"
    m = _OPEN_CLAIM.search(str(suggestion.get("status") or ""))
    if m:
        return f"says '{m.group(0)}'"
    return None


async def apply_due(store: Store, now: datetime) -> int:
    """Put the checked suggestions live as the trackers' new status (the old line stays in the history), unless `needs_owner`
    holds one back for Studio; returns how many went live. A suggestion goes live only while the reports it read are still new
    (the owner has not dealt with them), once, and never to a date older than the status it replaces."""
    states = {d["_id"]: d for d in await store.tracker_states()}
    applied = 0
    for slug, defn in definitions().items():
        state = states.get(slug)
        sug = (state or {}).get("suggestion") or {}
        if not (sug.get("ok") and sug.get("changed") is True) or sug.get("applied_at") or sug.get("held"):
            continue
        fresh = {r["item_id"] for r in new_reports(defn, state, await store.tracker_reports(slug))}
        if not fresh or not set(sug.get("for_ids") or []) <= fresh:
            continue
        if str(sug.get("date") or "") < _day(history(defn, state)[-1].get("date")):
            continue
        why = needs_owner(defn, state, sug)
        if why:
            await store.set_tracker_suggestion(slug, {**sug, "held": why})
            log.info("trackers: %s suggestion waits for the owner: %s", slug, why)
            continue
        try:
            row = check_update(defn, str(sug.get("status") or ""), sug.get("stage"), str(sug.get("date") or ""), now)
        except StatusError:
            continue
        await store.add_tracker_update(slug, {**row, "sources": list(sug.get("sources") or [])[:6], "at": now, "by": AUTO_BY,
                                              "reason": pr.one_line(str(sug.get("reason") or ""))[:200]})
        await store.set_tracker_suggestion(slug, {**sug, "applied_at": now})
        applied += 1
        log.info("trackers: %s status updated by itself (%s)", slug, row["date"])
    return applied


CHANGES_MAX = 6


async def changes_for_place(db, place: str) -> List[dict]:
    """What is changing near one Pune place, for the neighbourhood pages (wired in app/wiring.py): the trackers whose `places`
    include it, newest status first, at most CHANGES_MAX, as {slug, name, status, date (YYYY-MM-DD), stage (its label, left out
    when the tracker has no stage)}. An unknown place gives []."""
    found = pune_places.BY_SLUG.get(place or "") or pune_places.BY_KEY.get(place or "")
    if found is None:
        return []
    store = Store(db)
    await refresh(store)
    states = {d["_id"]: d for d in await store.tracker_states()}
    rows = []
    for slug, defn in definitions().items():
        if found.slug not in place_slugs(defn):
            continue
        hist = history(defn, states.get(slug))
        row = {"slug": slug, "name": defn["name"], "status": pr.one_line(hist[-1]["status"]), "date": _day(hist[-1].get("date"))}
        stage = current_stage(defn, hist)
        if stage is not None:
            row["stage"] = defn["stages"][stage]
        rows.append(row)
    return sorted(rows, key=lambda r: r["date"], reverse=True)[:CHANGES_MAX]


async def studio_views(store: Store) -> List[dict]:
    await refresh(store)
    states = {d["_id"]: d for d in await store.tracker_states()}
    out = [studio_view(defn, states.get(slug), await store.tracker_reports(slug)) for slug, defn in definitions().items()]
    return sorted(out, key=lambda v: (-v["new_count"], v["name"]))


class StatusError(ValueError):
    """An update the owner has to fix (shown as it is)."""


def check_update(defn: dict, status: str, stage: Optional[int], date: str, now: datetime) -> dict:
    """The owner's new status line, checked: one plain sentence or two (no links, no phone numbers), a stage the tracker has, and a
    date that is not in the future."""
    text = pr.one_line(pr.URL.sub("", status or ""))
    if len(text) < 12:
        raise StatusError("Write the status in a sentence.")
    if len(text) > STATUS_MAX:
        raise StatusError(f"Keep the status under {STATUS_MAX} characters; the timeline below it carries the detail.")
    if stage is not None and _stage(defn, stage) is None:
        raise StatusError("That stage is not one of this tracker's stages.")
    try:
        day = datetime.fromisoformat((date or "")[:10]).date()
    except ValueError:
        raise StatusError("Give the date the status is true from (YYYY-MM-DD).")
    if day > now.date():
        raise StatusError("The date cannot be in the future.")
    return {"date": day.isoformat(), "stage": stage, "status": text}
