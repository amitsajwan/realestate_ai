"""Health rows for the Admin home: green / amber / red, each with plain-English fix text.

Reads only what the app already records: engage_status (Meta token per channel), calendar_status and newsroom_status (last run),
the environment (enabled and dry-run switches) and a cached AI ping. Never returns tokens or phone numbers.
"""
import time
from datetime import datetime
from typing import Awaitable, Callable, Dict, List, Optional

OK, WARN, BAD = "ok", "warn", "bad"
AI_TTL_S = 600  # the AI ping is cached for 10 minutes
_ai_cache: Dict = {}


def _iso(dt) -> Optional[str]:
    if isinstance(dt, datetime):
        return dt.isoformat() + ("Z" if dt.tzinfo is None else "")
    return dt


async def default_ai_ping() -> Dict:
    """One tiny call to the configured provider (default_llm)."""
    from app.modules.ai_listing.llm import default_llm
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


def build_health(*, social, wa, engage, calendar, newsroom, meta: Dict[str, Optional[dict]], cal_run: dict, news_run: dict,
                 controls: dict, ai: dict) -> List[Dict]:
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
