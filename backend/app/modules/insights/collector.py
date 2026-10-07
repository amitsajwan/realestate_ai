"""The insights collector: reads what Meta reports for every published calendar post at 1 h, 24 h, 72 h and 7 days, by itself.

Nobody has to run anything:
  * it finds out which metric names work for each kind of post (Instagram reel and post, Facebook reel and post) by asking for
    each candidate alone (graph.probe), remembers the answer in `insights_capabilities` and asks again a week later, or at once
    when a known-good request starts failing (Meta renamed or retired a metric);
  * each snapshot is one new row in `content_metrics` (never updated): {post_id, channel, slug, target, external_id, age_label,
    due_at, at, metrics, tags}. The row's tags (calendar/tags.py) come along, so results group by format and hook at once;
  * a snapshot is taken only inside its window (GRACE): a "1h" number read a day late would be a different number, so a missed
    window is left empty rather than mislabelled;
  * when a person is needed (the token lacks a permission, or no metric works at all) the owners get ONE in-app notification
    per kind of post and reason, not one per cycle.
Read-only towards Meta: it never posts, edits or deletes. Off in dry run (nothing real was published) and while posting is paused.
"""
import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Tuple

from . import graph

log = logging.getLogger(__name__)

CALENDAR = "content_calendar"
METRICS = "content_metrics"
CAPS = "insights_capabilities"
AGES: Tuple[Tuple[str, timedelta], ...] = (("1h", timedelta(hours=1)), ("24h", timedelta(hours=24)), ("72h", timedelta(hours=72)),
                                            ("7d", timedelta(days=7)))
GRACE = {"1h": timedelta(hours=2), "24h": timedelta(hours=12), "72h": timedelta(hours=24), "7d": timedelta(hours=48)}
RECHECK = timedelta(days=7)
INTERVAL_S = 900
NOTIFY_KIND = "content_needs_you"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def owner_ids() -> Tuple[str, ...]:
    """Who hears about problems: INSIGHTS_OWNER_IDS, else the calendar's owners, else the concierge's."""
    for name in ("INSIGHTS_OWNER_IDS", "CALENDAR_OWNER_IDS", "CONCIERGE_OWNER_IDS"):
        ids = tuple(s.strip() for s in (os.environ.get(name) or "").split(",") if s.strip())
        if ids:
            return ids
    return ()


def due_snapshots(rows: List[dict], taken: set, now: datetime) -> List[Tuple[dict, str, datetime]]:
    """(row, age label, due time) for every snapshot whose window is open now and that was not taken yet. Pure."""
    out = []
    for r in rows:
        ext = str(r.get("external_id") or "")
        pub = _aware(r.get("published_at"))
        if r.get("status") != "published" or not ext or ext.startswith("dryrun_") or pub is None or graph.target_of(r) is None:
            continue
        for label, age in AGES:
            due = pub + age
            if due <= now < due + GRACE[label] and (r["_id"], label) not in taken:
                out.append((r, label, due))
    return out


class Collector:
    def __init__(self, db, get: graph.Get, base: str, token: str, owners: Tuple[str, ...] = (), notify: Optional[Callable] = None,
                 clock: Callable[[], datetime] = _utcnow):
        self.db, self.get, self.base, self.token, self.owners = db, get, base, token, owners
        self.notify, self.clock = notify, clock
        self.caps = db.get_collection(CAPS)
        self.metrics = db.get_collection(METRICS)

    async def _alert(self, target: str, reason: str) -> None:
        """One notification per kind of post and reason; the same problem is not repeated every cycle."""
        key = hashlib.sha1(f"{target}|{reason}".encode()).hexdigest()[:12]
        doc = await self.caps.find_one({"_id": target}) or {}
        if key in (doc.get("alerted") or []):
            return
        await self.caps.update_one({"_id": target}, {"$push": {"alerted": key}})
        summary = f"Post results: Meta does not let us read {target} numbers ({reason}). Check the Page token's permissions."
        log.warning("insights: %s", summary)
        if self.notify:
            for owner in self.owners:
                await self.notify(self.db, owner, NOTIFY_KIND, summary, {"target": target})

    async def working_metrics(self, target: str, row: dict) -> List[str]:
        """The metric names that work for `target`, checked against this post when unknown or older than RECHECK."""
        now = self.clock()
        doc = await self.caps.find_one({"_id": target})
        checked = _aware((doc or {}).get("checked_at"))
        if doc and doc.get("working") and checked and now - checked < RECHECK:
            return list(doc["working"])
        res = await graph.probe(self.get, self.base, row["external_id"], target, self.token)
        working = [r["metric"] for r in res if r["ok"]]
        fields = {"working": working, "failed": {r["metric"]: r["reason"] for r in res if not r["ok"]}, "checked_at": now,
                  "checked_on": row.get("slug")}
        if doc:
            await self.caps.update_one({"_id": target}, {"$set": fields})
        else:
            await self.caps.insert_one({"_id": target, "alerted": [], **fields})
        blocked = [r for r in res if r.get("permission")]
        if blocked:
            await self._alert(target, blocked[0]["reason"])
        elif not working:
            await self._alert(target, "no metric name worked")
        return working

    async def collect_once(self) -> Dict[str, int]:
        now = self.clock()
        counts = {"taken": 0, "failed": 0, "no_metrics": 0}
        rows = await self.db.get_collection(CALENDAR).find({"status": "published"}).to_list(5000)
        recent = [r for r in rows if (_aware(r.get("published_at")) or now) >= now - timedelta(days=10)]
        ids = [r["_id"] for r in recent]
        taken = {(m["post_id"], m["age_label"]) for m in await self.metrics.find({"post_id": {"$in": ids}}).to_list(100000)} if ids else set()
        for row, label, due in due_snapshots(recent, taken, now):
            target = graph.target_of(row)
            names = await self.working_metrics(target, row)
            if not names:
                counts["no_metrics"] += 1
                continue
            vals, err = await graph.fetch(self.get, self.base, row["external_id"], target, names, self.token)
            if err:
                counts["failed"] += 1
                if err["permission"]:
                    await self._alert(target, err["reason"])
                else:  # a name that worked stopped working: check every name again next cycle
                    await self.caps.update_one({"_id": target}, {"$set": {"checked_at": None}})
                continue
            try:
                await self.metrics.insert_one({"_id": uuid.uuid4().hex, "post_id": row["_id"], "channel": row["channel"],
                                               "slug": row.get("slug"), "target": target, "external_id": row["external_id"],
                                               "age_label": label, "due_at": due, "at": now, "metrics": vals, "tags": row.get("tags") or {}})
            except Exception as e:  # the unique (post_id, age_label) index: another process took this snapshot a moment ago
                if "duplicate" not in str(e).lower():
                    raise
                continue
            counts["taken"] += 1
        return counts


async def loop() -> None:
    """Worker loop (app/worker.py). Runs only when posts really go out (not dry run) and posting is not paused."""
    import asyncio

    import httpx

    from app.core.database import get_database
    from app.modules.notifications.service import notify
    from app.platform.controls import is_paused
    from app.platform.heartbeats import heartbeat
    from app.platform.meta_graph.config import load as load_social

    log.info("insights: loop started")
    while True:
        social = load_social()
        on = enabled(social)
        try:
            async with heartbeat("insights", get_database, on=on):
                if on and not await is_paused(get_database(), "posting_paused"):
                    async with httpx.AsyncClient(timeout=20) as c:
                        async def get(url, params):
                            r = await c.get(url, params=params)
                            try:
                                return r.status_code, r.json()
                            except ValueError:
                                return r.status_code, {}
                        base = f"https://graph.facebook.com/{social.graph_version}"
                        counts = await Collector(get_database(), get, base, social.page_token, owner_ids(), notify).collect_once()
                    if any(counts.values()):
                        log.info("insights: cycle done %s", counts)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("insights: cycle failed")
        await asyncio.sleep(INTERVAL_S)


def enabled(social) -> bool:
    """On when real posts go out with a token (not dry run), unless INSIGHTS_ENABLED=off."""
    if (os.environ.get("INSIGHTS_ENABLED") or "on").strip().lower() in ("0", "false", "no", "off"):
        return False
    return bool(social.page_token) and not social.dry_run
