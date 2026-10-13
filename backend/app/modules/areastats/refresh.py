"""Keeps the project register complete for the area stats, a little at a time (one `step` per newsroom cycle).

The newsroom reads only the newest Pune projects, so on its own the register never holds the older projects in our areas, nor
their completion dates. Each step:
1. sweep: reads `pages` pages of one of our pincodes' MahaRERA listing (policy.AREA_PINCODES and SHARED_PINCODES), in turn, so
   every project in our areas reaches the register and its Last Modified date stays fresh (about 250 pages in all on
   2026-10-04: a full round in about 10 days at 3 pages a cycle, 8 cycles a day);
2. relabel: records whose area changed with the rules get the new one (411047 projects were Wagholi, are Lohegaon);
   discover: one project number seen in Google results that we lack is looked up on MahaRERA by name (areastats.discover);
   a found one joins the watch list in the next part;
3. details: reads MahaRERA's project API for up to `details` records: completion dates and homes booked, again every
   DETAILS_MAX_AGE_DAYS because builders file updates. A changed homes-booked count is also kept, dated, in `booked_history`
   (how fast a project sells: areastats.hot).
Requests are spaced by PAUSE seconds: MahaRERA is a public service and must not feel us.

It catches up on its own: while the first sweep round is not done, or more records wait for details than one step reads, a step
uses the bigger CATCHUP_* batches (still PAUSE apart), then drops back to the gentle sizes. The sweep's place is kept in the
database, so a deploy or restart only pauses it; nothing has to be started by hand (scripts/area_backfill.py stays for a
one-off full run). Watched projects outside our areas (areastats.watch) get their details refreshed too.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.core.areas import BY_KEY
from app.modules.agentprojects import maharera as project_api
from app.modules.newsroom import register
from app.modules.newsroom.policy import AREA_PINCODES, SHARED_PINCODES
from app.modules.newsroom.sources import maharera as search
from app.modules.newsroom.store import Store
from app.platform import trace

from . import discover
from . import pages as project_pages  # not `pages`: step() takes a `pages` batch size
from . import watch as watchlist

log = logging.getLogger(__name__)

SWEEP_PAGES = 3
DETAILS_PER_STEP = 15
CATCHUP_PAGES = 10              # while behind: about 10 x 2 s of searches and 50 x 2 s of project reads per step
CATCHUP_DETAILS = 50
DETAILS_MAX_AGE_DAYS = 30
DETAILS_RETRY_DAYS = 1  # after a failed read
PAUSE = 2.0  # seconds between MahaRERA requests; tests set it to 0
SKIP_AFTER_MISSES = 3  # a sweep page still empty after this many steps is skipped until the next round
MARK = "area_sweep"  # newsroom_status document: where the sweep is
BOOKED_HISTORY = 24  # dated homes-booked readings kept per project (about two years at one read a month)
DETAIL_FIELDS = ("project_type", "registered_on", "completion_at_registration", "completion_now", "units_total", "units_booked")


def pincodes() -> List[str]:
    return sorted(set(AREA_PINCODES) | set(SHARED_PINCODES))


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


async def sweep(store: Store, get, now: datetime, pages: int = SWEEP_PAGES) -> dict:
    """Read the next `pages` pages of the pincode sweep into the register. Returns counts; `round_done` when it wrapped."""
    mark, pins = await store.get_mark(MARK), pincodes()
    pin = mark.get("pincode") if mark.get("pincode") in pins else pins[0]
    page, last, misses = int(mark.get("page") or 1), int(mark.get("last") or 0), int(mark.get("misses") or 0)
    out = {"pages": 0, "empty": 0, "new": 0, "updated": 0, "round_done": False}
    for i in range(max(0, pages)):
        if i:
            await asyncio.sleep(PAUSE)
        total, projects = await search.read_pincode_page(get, pin, page)
        out["pages"] += 1
        if not projects:  # the site's flaky "No Records Found", after retries: it is struggling, so stop for this step
            out["empty"] += 1
            misses += 1
            if misses < SKIP_AFTER_MISSES:
                break  # the same page next step
            misses, last = 0, last or page  # a page that keeps failing is skipped; the next round reads it again
        else:
            misses = 0
            got = await store.record_projects(register.records(projects, now))
            out["new"], out["updated"] = out["new"] + got["new"], out["updated"] + got["updated"]
            last = search.last_page(total) if total else max(last, page)
        if page >= last:
            nxt = pins[(pins.index(pin) + 1) % len(pins)]
            if nxt == pins[0]:
                out["round_done"] = True
                await store.set_mark(MARK, round_done_at=now)
            pin, page, last = nxt, 1, 0
        else:
            page += 1
        if not projects:
            break
    await store.set_mark(MARK, pincode=pin, page=page, last=last, misses=misses, at=now)
    return out


async def relabel(store: Store, docs: Optional[List[dict]] = None) -> int:
    """Give each record the area the current rules say (None when it is no longer ours); returns how many changed."""
    changed = 0
    for d in docs if docs is not None else await store.all_projects():
        where = register.locality_of(d.get("name", ""), d.get("pincode", ""))
        area, how = (where or (None, "not in our areas"))
        if d.get("locality") != area or d.get("locality_from") != how:
            await store.set_project(d["_id"], locality=area, locality_from=how)
            changed += 1
    return changed


def _due(d: dict, now: datetime) -> bool:
    at = d.get("details_checked_at")
    if not isinstance(at, datetime):
        return True
    wait = DETAILS_MAX_AGE_DAYS if d.get("details_ok") else DETAILS_RETRY_DAYS
    return now - _aware(at) >= timedelta(days=wait)


def _wanted(d: dict) -> bool:
    """A record whose details we keep: one in our areas, or one a source watches."""
    return d.get("locality") in BY_KEY or watchlist.is_watched(d)


async def behind(store: Store, now: datetime, docs: Optional[List[dict]] = None) -> bool:
    """True while the register is still filling: the first sweep round is not done, or more records wait for details than a
    gentle step reads."""
    if not (await store.get_mark(MARK)).get("round_done_at"):
        return True
    docs = docs if docs is not None else await store.all_projects()
    return sum(1 for d in docs if _wanted(d) and _due(d, now)) > DETAILS_PER_STEP


async def details(store: Store, fetch: project_api.Fetch, now: datetime, limit: int = DETAILS_PER_STEP,
                  docs: Optional[List[dict]] = None) -> dict:
    """Fill completion dates and homes from MahaRERA's project API for the records that need it most (never read first)."""
    docs = docs if docs is not None else await store.all_projects()
    due = [d for d in docs if _wanted(d) and _due(d, now)]
    due.sort(key=lambda d: (isinstance(d.get("details_checked_at"), datetime),
                            _aware(d["details_checked_at"]) if isinstance(d.get("details_checked_at"), datetime) else now))
    out = {"read": 0, "failed": 0}
    for i, d in enumerate(due[:max(0, limit)]):
        if i:
            await asyncio.sleep(PAUSE)
        mid, regno = register.maharera_id(d.get("source_url", "")), d.get("regno") or d["_id"]
        fields = None
        if mid is not None:
            body = await fetch(mid)
            try:
                got = project_api.parse_general(body, regno, mid) if body is not None else None
                fields = {k: got[k] for k in DETAIL_FIELDS} if got else None
            except project_api.MahaReraError as e:
                log.warning("areastats: MahaRERA project %s (%s): %s", mid, regno, e)
        if fields is None:
            out["failed"] += 1
            await store.set_project(d["_id"], details_checked_at=now, details_ok=False)
            continue
        out["read"] += 1
        await store.set_project(d["_id"], **fields, details_checked_at=now, details_ok=True, **_booked(d, fields, now))
    return out


def _booked(d: dict, fields: dict, now: datetime) -> dict:
    """A dated reading of homes booked when it changed (or is the first): how areastats.hot sees which projects are selling."""
    hist = list(d.get("booked_history") or [])
    n = fields.get("units_booked")
    if not isinstance(n, int) or (hist and hist[-1].get("booked") == n):
        return {}
    return {"booked_history": (hist + [{"at": now, "booked": n}])[-BOOKED_HISTORY:]}


async def step(store: Store, get, fetch: project_api.Fetch, now: datetime, pages: Optional[int] = None,
               limit: Optional[int] = None) -> dict:
    """One round: sweep, relabel, the watch list, details, page slugs for new records. Batch sizes follow `behind` unless given. A failing part is logged
    and never stops the others."""
    catching_up = (pages is None or limit is None) and await behind(store, now)
    pages = pages if pages is not None else (CATCHUP_PAGES if catching_up else SWEEP_PAGES)
    limit = limit if limit is not None else (CATCHUP_DETAILS if catching_up else DETAILS_PER_STEP)
    out: dict = {"mode": "catch-up" if catching_up else "steady"}
    for name, part in (("sweep", lambda: sweep(store, get, now, pages)), ("relabel", lambda: relabel(store)),
                       ("discover", lambda: discover.resolve(store, get, now)), ("watch", lambda: watchlist.sync(store, now)), ("details", lambda: details(store, fetch, now, limit)),
                       ("pages", lambda: project_pages.assign_all(store))):
        try:
            out[name] = await part()
        except Exception as e:
            log.exception("areastats: %s failed", name)
            trace.event(log, "rera", "register", name, trace.FAILED, reason=f"{type(e).__name__}: {e}")
            out[name] = None
            continue
        trace.event(log, "rera", "register", name, _outcome(name, out[name]), mode=out["mode"], **_counts(out[name]))
    return out


def _outcome(part: str, got) -> str:
    """ok, or fallback when MahaRERA gave empty sweep pages or project reads failed (the next step tries them again)."""
    if part == "sweep" and isinstance(got, dict) and got.get("empty"):
        return trace.FALLBACK
    if part == "details" and isinstance(got, dict) and got.get("failed"):
        return trace.FALLBACK
    return trace.OK


def _counts(got) -> dict:
    return dict(got) if isinstance(got, dict) else {"changed": got} if isinstance(got, int) else {}


async def status(store: Store, now: datetime) -> List[str]:
    """Is the register being kept up? Lines for `python -m app.worker --check` (WARN marks something to look at)."""
    from . import enrich
    docs = await store.all_projects()
    ours = [d for d in docs if d.get("locality") in BY_KEY]
    wanted = [d for d in docs if _wanted(d)]
    mark = await store.get_mark(MARK)
    lines = []
    at, done = mark.get("at"), mark.get("round_done_at")
    if isinstance(at, datetime):
        hours = (now - _aware(at)).total_seconds() / 3600
        lines.append(f"{'WARN ' if hours > 24 else 'OK   '}rera sweep: at pincode {mark.get('pincode')} page {mark.get('page')}, "
                     f"moved {hours:.1f}h ago" + (f"; last full round {(now - _aware(done)).days}d ago" if isinstance(done, datetime)
                                                   else "; first round not finished"))
    else:
        lines.append("WARN rera sweep: never ran (it runs inside the newsroom cycle: NEWSROOM_ENABLED with the maharera source)")
    ok = sum(1 for d in wanted if d.get("details_ok"))
    failed = sum(1 for d in wanted if d.get("details_ok") is False)
    never = sum(1 for d in wanted if not isinstance(d.get("details_checked_at"), datetime))
    due = sum(1 for d in wanted if _due(d, now))
    lines.append(f"{'WARN ' if failed > ok else 'OK   '}rera details: {len(ours)} projects in our areas, {len(wanted) - len(ours)} watched; "
                 f"details ok {ok}, last read failed {failed}, never read {never}, due now {due}")
    with_page = [d for d in docs if d.get("page_slug")]
    lines.append(f"{'WARN ' if len(with_page) < len(wanted) else 'OK   '}rera pages: {len(with_page)} of {len(wanted)} kept projects have a page")
    targets = [d for d in docs if enrich._ours(d)]
    enriched = [d for d in targets if isinstance(d.get("enriched_at"), datetime)]
    texts = sum(1 for d in targets if d.get("page_text"))
    urgent = await store.db.get_collection(enrich.REQUESTS).count_documents({})
    last = max((_aware(d["enriched_at"]) for d in enriched), default=None)
    on = enrich.load().enabled
    lines.append(f"{'OK   ' if on else 'OFF  '}enrichment: {len(enriched)} of {len(targets)} pages enriched, {texts} with model text, "
                 f"{urgent} urgent waiting" + (f", last {(now - last).total_seconds() / 3600:.1f}h ago" if last else ", none yet")
                 + ("" if on else " (PROJECT_ENRICH_ENABLED is off)"))
    if on and urgent and last and (now - last) > timedelta(hours=1):
        lines[-1] = "WARN " + lines[-1][5:] + " — urgent requests are waiting and nothing was enriched in the last hour"
    return lines
