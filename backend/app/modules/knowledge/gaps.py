"""Answer gaps: the questions buyers asked that our facts could not answer, turned into one clear task for the agent who can fix them,
and closed again by the system itself once the fact is there.

Sources (read only; each module keeps writing its own records): Facebook and Instagram comments (`engage_comments`: gaps, missing,
listing or calendar id), website chats (`chat_sessions`: data.gaps with the question, data.page) and WhatsApp conversations
(`whatsapp_conversations`: data.gaps, context). Older records hold only the `missing` label; it is mapped back to a topic.

One row per home (or post) and topic in `answer_gaps`: {_id, subject {kind, id, title}, agent_id, topic, label, count, questions
(latest 5), channels, first_at, last_at, status open|answered, answered_at, notified_at, notified_count}.

Each cycle (`refresh`):
  1. groups the last GAP_DAYS of unanswered questions by home and topic (questions asked before a gap was answered do not count);
  2. checks every open gap against the home's CURRENT facts: when the lookup now finds the topic (or, for questions with no known
     topic, the home's FAQ shares their words), the gap is closed by itself: nobody has to tick anything;
  3. tells the agent once a gap has been asked MIN_ASKS times (one in-app notification, kind 'answer_gap', with the latest question),
     and again only when the count has doubled and a week has passed. Never a phone number or a buyer's name in the text.
`themes()` sums the open gaps by topic and area: what buyers keep asking, for the content plan.
"""
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Tuple

from .grounding import Ref, facts_for
from .reply import OVERRIDE, TOPICS, _words, plan

log = logging.getLogger(__name__)

COLLECTION = "answer_gaps"
GAP_DAYS = 30
MIN_ASKS = 2
RENOTIFY_AFTER = timedelta(days=7)
INTERVAL_S = 3600
NOTIFY_KIND = "answer_gap"
LABEL_TO_TOPIC = {spec[2][0]: name for name, spec in TOPICS.items()}
LABEL_TO_TOPIC.update({OVERRIDE["distance"]["en"]: "commute", OVERRIDE["amenity"]["en"]: "amenities"})
SAMPLE_QUESTION = {"commute": "How far is the office and how long is the drive?"}   # what the lookup is re-asked with, per topic


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def topics_of(gaps, missing) -> List[str]:
    """Topic names from a record: its structured gaps, else its 'missing' labels mapped back (unknown wording -> 'other')."""
    names = [g for g in (gaps or []) if isinstance(g, str) and (g in TOPICS or g == "other")]
    if names:
        return names
    out = []
    for part in str(missing or "").split(";"):
        part = part.strip()
        if part:
            out.append(LABEL_TO_TOPIC.get(part, "other"))
    return out


def label_of(topic: str) -> str:
    return "something we had no answer to" if topic == "other" else TOPICS[topic][2][0]


# ---- collecting -----------------------------------------------------------------------------------------------------
async def collect(db, since: datetime) -> List[dict]:
    """Every unanswered ask since `since`: {subject (kind, id), agent_id, topic, question, channel, at}."""
    asks: List[dict] = []
    for c in await db.get_collection("engage_comments").find({"needs_human": True}).to_list(20000):
        at = _aware(c.get("processed_at"))
        if not at or at < since or c.get("intent") != "question":
            continue
        subject = ("listing", c["listing_id"]) if c.get("listing_id") else ("calendar", c["calendar_id"]) if c.get("calendar_id") else None
        if subject is None:
            continue
        for t in topics_of(c.get("gaps"), c.get("missing")):
            asks.append({"subject": subject, "agent_id": c.get("agent_id"), "topic": t, "question": (c.get("text") or "")[:200],
                         "channel": c.get("channel") or "facebook", "at": at})
    for coll, channel in (("chat_sessions", "chat"), ("whatsapp_conversations", "whatsapp")):
        for s in await db.get_collection(coll).find({}).to_list(20000):
            at = _aware(s.get("updated_at"))
            data = s.get("data") or {}
            if not at or at < since or not data.get("gaps"):
                continue
            page = data.get("page") or {}
            ctx = s.get("context") or {}
            listing_id = page.get("listing_id") if page.get("kind") == "listing" else ctx.get("listing_id")
            if not listing_id:
                continue   # a question on an agent's home page or a general WhatsApp chat: no single home to add the fact to
            agent_id = page.get("agent_id") or s.get("agent_id")
            for g in data["gaps"]:
                if not isinstance(g, dict):
                    continue
                for t in topics_of(g.get("topics"), None):
                    asks.append({"subject": ("listing", listing_id), "agent_id": agent_id, "topic": t, "question": str(g.get("q") or "")[:200],
                                 "channel": channel, "at": at})
    return asks


def gap_id(subject: Tuple[str, str], topic: str) -> str:
    return hashlib.sha1(f"{subject[0]}|{subject[1]}|{topic}".encode()).hexdigest()[:20]


# ---- is it answered now? ------------------------------------------------------------------------------------------------
def answered_by(grounding, topic: str, questions: List[str]) -> bool:
    """True when the home's current facts answer this gap: the lookup finds the topic, or (no known topic) the FAQ shares the question's words."""
    if grounding is None:
        return False
    if topic == "other":
        faq = grounding.faq + grounding.area_faq
        return any(len(_words(q) & _words(f"{x['q']} {x['a']}")) >= 2 for q in questions for x in faq)
    q = SAMPLE_QUESTION.get(topic) or (questions[-1] if questions else topic)
    return topic not in plan(q, grounding, [topic]).missing


# ---- the cycle ----------------------------------------------------------------------------------------------------------
class Gaps:
    def __init__(self, db, notify: Optional[Callable] = None, clock: Callable[[], datetime] = _utcnow,
                 grounding_for: Optional[Callable] = None):
        self.db, self.notify, self.clock = db, notify, clock
        self.col = db.get_collection(COLLECTION)
        self.grounding_for = grounding_for or (lambda subject: facts_for(Ref(subject[0], subject[1]), db))

    async def _title(self, subject: Tuple[str, str]) -> str:
        if subject[0] == "listing":
            doc = await self.db.get_collection("listings").find_one({"_id": subject[1]}) or {}
            return str(doc.get("title") or "your listing")[:80]
        doc = await self.db.get_collection("content_calendar").find_one({"_id": subject[1]}) or {}
        return str(doc.get("slug") or "our post")[:80]

    async def refresh(self) -> Dict[str, int]:
        now = self.clock()
        counts = {"open": 0, "answered": 0, "notified": 0}
        groups: Dict[str, dict] = {}
        for a in await collect(self.db, now - timedelta(days=GAP_DAYS)):
            g = groups.setdefault(gap_id(a["subject"], a["topic"]), {"subject": a["subject"], "topic": a["topic"], "asks": []})
            g["asks"].append(a)
        for gid, g in groups.items():
            row = await self.col.find_one({"_id": gid})
            answered_at = _aware((row or {}).get("answered_at"))
            asks = sorted((a for a in g["asks"] if not answered_at or a["at"] > answered_at), key=lambda a: a["at"])
            if not asks:
                continue   # every ask came before the fact was added
            subject, topic = g["subject"], g["topic"]
            questions = list(dict.fromkeys(a["question"] for a in asks if a["question"]))[-5:]
            fields = {"subject": {"kind": subject[0], "id": subject[1], "title": await self._title(subject)},
                      "agent_id": next((a["agent_id"] for a in reversed(asks) if a.get("agent_id")), None), "topic": topic,
                      "label": label_of(topic), "count": len(asks), "questions": questions,
                      "channels": sorted({a["channel"] for a in asks}), "first_at": asks[0]["at"], "last_at": asks[-1]["at"], "status": "open"}
            if row:
                await self.col.update_one({"_id": gid}, {"$set": fields})
            else:
                await self.col.insert_one({"_id": gid, "answered_at": None, "notified_at": None, "notified_count": 0, **fields})
        # every open gap: closed by itself when the facts now answer it, else the agent is told (once, then on doubling)
        for row in await self.col.find({"status": "open"}).to_list(5000):
            subject = (row["subject"]["kind"], row["subject"]["id"])
            try:
                grounding = await self.grounding_for(subject)
            except Exception:
                grounding = None
            if answered_by(grounding, row["topic"], row.get("questions") or []):
                await self.col.update_one({"_id": row["_id"]}, {"$set": {"status": "answered", "answered_at": now}})
                counts["answered"] += 1
                continue
            counts["open"] += 1
            if await self._maybe_notify(row, now):
                counts["notified"] += 1
        return counts

    async def _maybe_notify(self, row: dict, now: datetime) -> bool:
        n, last = row.get("count") or 0, _aware(row.get("notified_at"))
        due = n >= MIN_ASKS and (last is None or (n >= 2 * (row.get("notified_count") or 0) and now - last >= RENOTIFY_AFTER))
        if not due or not row.get("agent_id") or self.notify is None:
            return False
        title, latest = row["subject"]["title"], (row.get("questions") or [""])[-1]
        if row["topic"] == "other":
            text = (f"Buyers asked {n} times about \"{title}\" and we had no answer. Latest: \"{latest[:120]}\". "
                    "Add the answer to this home's FAQ and the assistant will use it from then on.")
        else:
            text = (f"Buyers asked {n} times about {row['label']} for \"{title}\" and we had no answer. Latest: \"{latest[:120]}\". "
                    "Add it to this home's details and the assistant will answer it from then on.")
        await self.notify(self.db, row["agent_id"], NOTIFY_KIND, text, {"gap_id": row["_id"], "listing_id": row["subject"]["id"]
                                                                       if row["subject"]["kind"] == "listing" else None})
        await self.col.update_one({"_id": row["_id"]}, {"$set": {"notified_at": now, "notified_count": n}})
        return True


async def themes(db, days: int = GAP_DAYS, now: Optional[datetime] = None) -> List[dict]:
    """What buyers keep asking that we cannot answer, summed by topic and area (the home's locality): ideas for posts and reels."""
    since = (now or _utcnow()) - timedelta(days=days)
    out: Dict[Tuple[str, str], int] = {}
    for row in await db.get_collection(COLLECTION).find({"status": "open"}).to_list(5000):
        if (_aware(row.get("last_at")) or since) < since or row.get("topic") == "other":
            continue
        area = ""
        if row["subject"]["kind"] == "listing":
            doc = await db.get_collection("listings").find_one({"_id": row["subject"]["id"]}) or {}
            area = str(doc.get("locality") or "")
        key = (row["topic"], area)
        out[key] = out.get(key, 0) + int(row.get("count") or 0)
    return [{"topic": t, "area": a, "asks": n} for (t, a), n in sorted(out.items(), key=lambda kv: -kv[1])]


async def loop() -> None:
    """Worker loop (app/worker.py): one refresh an hour. Reads and notifies only; never changes a listing or sends a reply."""
    import asyncio

    from app.core.database import get_database
    from app.modules.notifications.service import notify
    from app.platform.heartbeats import heartbeat

    log.info("answer gaps: loop started")
    while True:
        try:
            async with heartbeat("answer_gaps", get_database):
                counts = await Gaps(get_database(), notify).refresh()
                if counts["answered"] or counts["notified"]:
                    log.info("answer gaps: %s", counts)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("answer gaps: cycle failed")
        await asyncio.sleep(INTERVAL_S)
