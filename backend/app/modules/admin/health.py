"""Health rows for the Admin home: green / amber / red, each with plain-English fix text.

Reads only what the app already records: engage_status (Meta token per channel), calendar_status and newsroom_status (last run),
the environment (enabled and dry-run switches) and a cached AI ping. Never returns tokens or phone numbers.
"""
import time
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Dict, List, Optional

from app.platform import heartbeats

OK, WARN, BAD = "ok", "warn", "bad"
AI_TTL_S = 600  # the AI ping is cached for 10 minutes
_ai_cache: Dict = {}


def _iso(dt) -> Optional[str]:
    if isinstance(dt, datetime):
        return dt.isoformat() + ("Z" if dt.tzinfo is None else "")
    return dt


async def default_ai_ping() -> Dict:
    """One tiny call to the configured provider (default_llm)."""
    from app.platform.llm import default_llm
    llm = default_llm()
    if llm is None:
        return {"ok": False, "configured": False}
    try:
        out = await llm.text("You are a health check. Answer with the single word OK.", "Say OK", 15)
    except Exception:
        out = None
    return {"ok": bool(out), "configured": True}


async def ai_status(ping: Callable[[], Awaitable[Dict]] = default_ai_ping, clock: Callable[[], float] = time.time,
                    ttl: float = AI_TTL_S) -> Dict:
    now = clock()
    if _ai_cache.get("at") is not None and now - _ai_cache["at"] < ttl:
        return _ai_cache["value"]
    try:
        value = await ping()
    except Exception:
        value = {"ok": False, "configured": True}
    value = {**value, "checked_at": _iso(datetime.utcnow())}
    _ai_cache.update(at=now, value=value)
    return value


def _row(key: str, label: str, status: str, text: str, fix: str = "") -> Dict:
    return {"key": key, "label": label, "status": status, "text": text, "fix": fix}


def meta_row(key: str, label: str, configured: bool, state: Optional[dict]) -> Dict:
    if not configured:
        return _row(key, label, WARN, f"{label} is not connected yet", "Run deploy/gcp/meta_connect.ps1 to connect the Page")
    if not state:
        return _row(key, label, WARN, "Connected, not checked yet", "It is checked when the comment assistant runs")
    if state.get("reconnect"):
        return _row(key, label, BAD, f"{label} disconnected: Meta rejected our token",
                    "Run deploy/gcp/meta_connect.ps1 to reconnect (docs/META_SETUP.md)")
    if not state.get("ok"):
        return _row(key, label, BAD, f"{label} check failed (Meta error {state.get('code') or '?'})",
                    "Try again later; if it stays red, run deploy/gcp/meta_connect.ps1")
    return _row(key, label, OK, "Connected")


def seo_rows(*, indexnow_on: bool, gsc_on: bool, indexnow: Optional[dict], coverage: Optional[dict],
             pages: Optional[dict], articles_on: bool = False, articles: Optional[dict] = None) -> List[Dict]:
    """Search engines (IndexNow) and Google's index (Search Console coverage), from the seo loop's marks (docs/plan/seo.md)."""
    rows = []
    n = indexnow or {}
    if not indexnow_on:
        rows.append(_row("indexnow", "Bing and IndexNow", WARN, "Off: Bing learns about new pages only when it next crawls",
                         "Set INDEXNOW_KEY in the server settings (docs/plan/seo.md)"))
    elif n.get("failed_at") and (not n.get("at") or n["failed_at"] > n["at"]):
        rows.append(_row("indexnow", "Bing and IndexNow", BAD, f"IndexNow refused our last send (status {n.get('status')})",
                         "Check that /indexnow-key.txt shows the key; tried again every 30 minutes"))
    elif n.get("at"):
        rows.append({**_row("indexnow", "Bing and IndexNow", OK, f"Sending new and changed pages (last round: {n.get('sent', 0)})"),
                     "last_run_at": _iso(n["at"])})
    else:
        rows.append(_row("indexnow", "Bing and IndexNow", OK, "On, has not run yet"))
    c = coverage or {}
    if not gsc_on:
        rows.append(_row("google_index", "Google index", WARN, "Search Console is not connected",
                         "Add the read-only service account key as GSC_SA_KEY_B64 (docs/plan/seo.md)"))
    elif not c.get("inspected"):
        rows.append(_row("google_index", "Google index", OK, "On, first check runs within a day"))
    else:
        share = c.get("indexed", 0) / c["inspected"]
        near = len((pages or {}).get("near_page_one") or [])
        text = f"{c.get('indexed', 0)} of {c['inspected']} checked sitemap pages are in Google" + (f"; {near} pages just off page one" if near else "")
        missing = c.get("missing_by_state") or {}
        top = max(missing.items(), key=lambda kv: kv[1]) if missing else None
        fix = f'Most common reason: "{top[0]}" ({top[1]} pages)' if top else ""
        rows.append({**_row("google_index", "Google index", OK if share >= 0.7 else WARN, text, fix), "last_run_at": _iso(c.get("at"))})
    a = articles or {}
    if not articles_on:
        rows.append(_row("neighbourhoods", "Neighbourhood articles", WARN, "Off: the bot is not finding or writing neighbourhood pages",
                         "Set COMMUNITY_ARTICLES_ENABLED=true in the server settings (docs/plan/seo.md)"))
    elif not a.get("found"):
        rows.append(_row("neighbourhoods", "Neighbourhood articles", OK, "On, finding neighbourhoods on its first run"))
    else:
        text = f"{a.get('published', 0)} published of {a['found']} neighbourhoods found"
        fix = f"Last one held back: {a['last_note']}" if a.get("last_note") else ""
        rows.append(_row("neighbourhoods", "Neighbourhood articles", OK, text, fix))
    return rows


FRESH_WARN, FRESH_BAD = 0.7, 0.4   # share of our areas' live project pages re-read in the window (to tune on real readings)


def _ago(seconds: float) -> str:
    h = seconds / 3600
    return f"{round(h)} hours" if h < 48 else f"{round(h / 24)} days"


def loop_row(key: str, label: str, beat: Optional[dict], interval_s: Optional[float], now: datetime, off_fix: str,
             what: str) -> Optional[Dict]:
    """A background loop the pages depend on (docs/plan/seo-system.md 8a, step 1), from its heartbeat: a loop that stopped
    fails quietly (pages keep old dates), so it shows here, not only in `python -m app.worker --check` on the VM. None when the
    loop has nothing to do (`interval_s` None and no off_fix)."""
    if interval_s is None:
        return _row(key, label, WARN, f"Off: {what}", off_fix) if off_fix else None
    age = heartbeats.age_s(beat, now)
    log_fix = "Restart the newsroom worker, then read its log: docker logs gcp-newsroom-1 | grep pipeline=" + key
    if heartbeats.stale(beat, interval_s, now):
        text = f"Stopped: no round for {_ago(age)}" if age is not None else "Has not run since the worker started"
        return {**_row(key, label, BAD, f"{text}; {what}", log_fix), "last_run_at": _iso((beat or {}).get("last_ok_at"))}
    err_at, ok_at = heartbeats._aware((beat or {}).get("last_error_at")), heartbeats._aware((beat or {}).get("last_ok_at"))
    if err_at and (not ok_at or err_at > ok_at):
        return {**_row(key, label, WARN, f"Last round had a problem: {str(beat.get('last_error') or '')[:140]}", log_fix),
                "last_run_at": _iso(ok_at)}
    return {**_row(key, label, OK, "Running"), "last_run_at": _iso(ok_at)}


SEARCH_LOW = 500                      # searches left: about a batch of 150 projects


def search_row(on: bool, left: Optional[int]) -> Dict:
    """Serper credits. When they run out nothing fails loudly: projects just look as if no site mentions them."""
    if not on:
        return _row("google_search", "Google search (Serper)", WARN, "No key: builder sites, prices and rank checks stop", "Add SERPER_API_KEY with deploy/gcp/keys.ps1")
    if left is None:
        return _row("google_search", "Google search (Serper)", WARN, "Could not read the credits left")
    if left <= 0:
        return _row("google_search", "Google search (Serper)", BAD, f"Out of credits ({left}): no project can find its sites", "Top up at serper.dev")
    if left < SEARCH_LOW:
        return _row("google_search", "Google search (Serper)", WARN, f"{left} searches left", "Top up at serper.dev")
    return _row("google_search", "Google search (Serper)", OK, f"{left} searches left")


def freshness_row(mark: Optional[dict], window_days: int) -> Dict:
    """How many of our areas' live project pages were re-read lately (seo.freshness): the dated answers that get us cited."""
    m = mark or {}
    label = "Project pages up to date"
    if not m.get("pages"):
        return _row("freshness", label, OK, "First count runs within a day")
    share = m.get("fresh", 0) / m["pages"]
    status = OK if share >= FRESH_WARN else WARN if share >= FRESH_BAD else BAD
    text = f"{m.get('fresh', 0)} of {m['pages']} live project pages in our areas updated in the last {window_days} days ({round(share * 100)}%)"
    old = ", ".join(f"/projects/{o['slug']}" + (f" ({str(o['updated'])[:10]})" if o.get("updated") else " (never)")
                    for o in (m.get("oldest") or [])[:3])
    fix = "" if status == OK else ("Read pipeline=enrich in the newsroom worker's log (MahaRERA down, the model refusing, keys)"
                                   + (f"; oldest: {old}" if old else ""))
    return {**_row("freshness", label, status, text, fix), "last_run_at": _iso(m.get("at"))}


def page_check_row(mark: Optional[dict], now: datetime) -> Dict:
    """The daily page check (seo.review): it fails quietly when it stops, or when the model has no room and only the rules read."""
    m, label = mark or {}, "Page check against sources"
    at = m.get("at")
    if not at:
        return _row("page_check", label, OK, "First check runs within a day")
    at = at if at.tzinfo else at.replace(tzinfo=timezone.utc)
    text = f"{m.get('read', 0)} pages read, {m.get('flagged', 0)} with something to look at, {m.get('model', 0)} read by the model"
    if now - at > timedelta(days=3):
        return {**_row("page_check", label, WARN, text, "No check in 3 days: read pipeline=seo step=review in the newsroom worker's log"),
                "last_run_at": _iso(at)}
    fix = "" if m.get("model") else "The model read none of them: the enrichment's budget is spent or its providers are resting"
    return {**_row("page_check", label, OK if m.get("model") else WARN, text, fix), "last_run_at": _iso(at)}


def build_health(*, social, wa, engage, calendar, newsroom, meta: Dict[str, Optional[dict]], cal_run: dict, news_run: dict,
                 controls: dict, ai: dict, dm=None) -> List[Dict]:
    rows = [
        meta_row("facebook", "Facebook", social.configured("facebook_page"), meta.get("facebook")),
        meta_row("instagram", "Instagram", social.configured("instagram"), meta.get("instagram")),
    ]
    if not wa.enabled:
        rows.append(_row("whatsapp", "WhatsApp", WARN, "WhatsApp replies are off", "Run deploy/gcp/whatsapp_connect.ps1 when ready"))
    elif wa.dry_run:
        rows.append(_row("whatsapp", "WhatsApp", WARN, "On, in practice mode: replies are worked out but not sent",
                         "Set WHATSAPP_DRY_RUN=false on the server to send replies"))
    elif not wa.can_send:
        rows.append(_row("whatsapp", "WhatsApp", BAD, "On, but no access token", "Run deploy/gcp/whatsapp_connect.ps1"))
    else:
        rows.append(_row("whatsapp", "WhatsApp", OK, "On and sending replies"))
    if dm is not None:
        if not dm.enabled:
            rows.append(_row("messenger", "Messenger and Instagram DMs", WARN, "DM replies are off",
                             "Subscribe the Page and Instagram to the /messenger/webhook, then set MESSENGER_ENABLED=true"))
        elif dm.dry_run:
            rows.append(_row("messenger", "Messenger and Instagram DMs", WARN, "On, in practice mode: replies are worked out but not sent",
                             "Set MESSENGER_DRY_RUN=false on the server to send replies"))
        elif not dm.can_send:
            rows.append(_row("messenger", "Messenger and Instagram DMs", BAD, "On, but no Page token", "Set META_PAGE_ACCESS_TOKEN"))
        else:
            rows.append(_row("messenger", "Messenger and Instagram DMs", OK, "On and sending replies"))

    if not ai.get("configured", True):
        rows.append(_row("ai", "AI", BAD, "No AI provider is set up", "Run deploy/gcp/ai_connect.ps1 to add an AI key"))
    elif ai.get("ok"):
        rows.append(_row("ai", "AI", OK, "Answering"))
    else:
        rows.append(_row("ai", "AI", BAD, "Not answering right now", "Check the key and the daily limit (deploy/gcp/ai_connect.ps1); checked again in 10 minutes"))

    def runner(key, label, enabled, paused, run, off_fix, extra=""):
        last = run.get("last_run_at")
        if paused:
            return _row(key, label, WARN, "Paused by you", "Use the switch under Controls to resume")
        if not enabled:
            return _row(key, label, WARN, "Switched off on the server", off_fix)
        if run.get("last_error"):
            return _row(key, label, BAD, f"Last run had a problem: {str(run['last_error'])[:140]}", "Open the screen to see which item failed")
        return _row(key, label, OK, ("Running" + extra) if last else "On, has not run yet")

    dry = " (practice mode: nothing is sent)" if social.dry_run else ""
    rows.append(runner("posting", "Posting", calendar.enabled, controls.get("posting_paused"), cal_run,
                       "Set CALENDAR_ENABLED=true on the server", dry))
    engage_run = {"last_run_at": max([s.get("checked_at") for s in meta.values() if s and s.get("checked_at")], default=None)}
    rows.append(runner("comments", "Comments", engage.enabled and bool(engage.page_id), controls.get("comments_paused"), engage_run,
                       "Set ENGAGE_ENABLED=true on the server", " (practice mode: replies not posted)" if engage.dry_run else ""))
    rows.append(runner("news", "News", newsroom.enabled, controls.get("news_paused"), news_run, "Set NEWSROOM_ENABLED=true on the server"))
    for r, run in zip(rows[-3:], (cal_run, engage_run, news_run)):
        r["last_run_at"] = _iso(run.get("last_run_at"))
    return rows
