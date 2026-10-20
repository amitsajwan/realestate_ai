"""Google's "People also ask" questions about a project, answered from facts we hold (docs/plan/rank-loop.md R4).

The questions come free with our Serper searches (areastats.websearch) and are kept as phrases in `search_demand` (source
"question"). A question belongs to a project when it names the project, or was shown with a search for it. Each question is
matched to a TOPIC by a fixed table of patterns, and each topic has one answer written by code from the record: MahaRERA dates,
registrations, bookings, buildings, promoter, place and pincode; the checked web facts (with their sites).
A question no topic matches, or whose topic has no fact behind it, is skipped: nothing is ever guessed. Price questions are
left to the page itself (an agent's quote), never answered here.

`answers(doc, docs, questions)` -> [{q, a, source, topic}] (at most MAX). Stored on the record as `seo_faq` by the page doctor.
"""
import re
from datetime import datetime, timezone
from typing import List, Optional

from app.modules.areastats import hot
from app.modules.areastats.pages import _long, booked, completion_passed, months_later, names, track_record
from app.modules.areastats.service import _count, _day
from app.modules.areastats.websearch import mentions

MAX = 8
DEMAND = "search_demand"

# topic -> pattern; the first topic that matches wins (order matters: "oc" before "possession")
TOPICS = [
    ("price", re.compile(r"\b(price|cost|rate|rates|budget|lakh|lakhs|crore|cr|emi|per sq)", re.I)),
    ("oc", re.compile(r"\b(oc|occupancy certificate|completion certificate)\b", re.I)),
    ("possession", re.compile(r"\b(possession|completion|complete|completed|ready|handover|hand over|delivery|delayed|delay)\b", re.I)),
    ("rera", re.compile(r"\b(rera|maharera|registration|registered|legal)\b", re.I)),
    ("booked", re.compile(r"\b(booked|sold|sales|bookings|available|availability|inventory)\b", re.I)),
    ("builder", re.compile(r"\b(builder|developer|developed|promoter|who (?:is|built|owns)|group|reputation|trust)\b", re.I)),
    ("size", re.compile(r"\b(towers?|floors?|storey|storeys|units|flats|apartments|homes|how big|acres?|land|open space)\b", re.I)),
    ("location", re.compile(r"\b(where|location|located|address|distance|far|near|nearby|airport|station|metro|school|hospital)\b", re.I)),
]


def topic_of(question: str) -> Optional[str]:
    return next((t for t, rx in TOPICS if rx.search(question or "")), None)


def _web(doc: dict, key: str) -> Optional[dict]:
    return next((f for f in (doc.get("web_facts") or {}).get("facts") or [] if f.get("key") == key), None)


def _sites(f: dict) -> str:
    return ", ".join(s.get("site", "") for s in f.get("sources") or [] if s.get("site"))


def answer(topic: str, doc: dict, docs: List[dict], shown: str) -> Optional[tuple]:
    """(answer, source) for a topic from the record's facts, or None when we hold nothing for it."""
    regno = doc.get("regno") or doc["_id"]
    now, first = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))
    if topic == "possession" and now:
        moved = months_later(doc)
        extra = f" At registration it was {_long(first)}, {moved} months earlier." if moved else ""
        passed = " That date has passed: ask the builder for the occupancy certificate (OC)." if completion_passed(doc) else ""
        return (f"The completion date {shown} filed with MahaRERA is {_long(now)}.{extra}{passed} "
                "Ask for the possession date in your agreement, in writing.", "MahaRERA")
    if topic == "oc" and now:
        if completion_passed(doc):
            return (f"The completion date filed with MahaRERA ({_long(now)}) has passed. MahaRERA's record does not tell us whether an "
                    "occupancy certificate was issued: ask the builder for a copy of the OC before you book.", "MahaRERA")
        return (f"The filed completion date is {_long(now)}, so an occupancy certificate is not due yet. Ask for the OC at possession.",
                "MahaRERA")
    if topic == "rera":
        return (f"{shown} is registered with MahaRERA as {regno}. Check the registration on the MahaRERA website before you book.",
                "MahaRERA")
    if topic == "booked":
        total, sold = _count(doc.get("units_total")), booked(doc)
        if total and sold is not None and sold <= total:
            b = hot.bookings(doc, datetime.now(timezone.utc))
            lately = f" {b['evidence'][0].upper() + b['evidence'][1:]}." if b else ""
            return (f"MahaRERA shows {sold} of {total} homes booked.{lately} Ask the builder which homes are still available.", "MahaRERA")
        return None
    if topic == "builder" and doc.get("promoter"):
        t = track_record(doc, docs)
        more = ""
        if t and t["count"] > 1:
            more = f" Our MahaRERA register has {t['count']} Pune projects by {t['name']}"
            more += (f"; {t['moved_later']} of {t['with_dates']} moved their completion date 3 months or more later." if t["record_ok"] else ".")
        return (f"The promoter registered with MahaRERA for {shown} is {doc['promoter']}.{more}", "MahaRERA")
    if topic == "size":
        bits, srcs = [], []
        t = doc.get("building_totals") or {}
        units = _count(doc.get("units_total")) or t.get("units_total")
        if t.get("towers"):
            bits.append(f"{t['towers']} building{'s' if t['towers'] != 1 else ''}" + (f", the tallest with {t['max_floors']} floors" if t.get("max_floors") else ""))
            srcs.append("MahaRERA")
        if units:
            bits.append(f"{units} units")
            srcs.append("MahaRERA")
        for key in ("land_acres", "open_space_pct"):
            f = _web(doc, key)
            if f:
                bits.append(f"{f['label'].lower()} {f['text']} (from {_sites(f)})")
                srcs.append(_sites(f))
        if not bits:
            return None
        return (f"{shown}: " + "; ".join(bits) + ".", ", ".join(dict.fromkeys(s for s in srcs if s)))
    if topic == "location":
        where = doc.get("place_locality") or doc.get("pune_place_name") or ""
        if not (where or doc.get("pincode")):
            return None
        return (f"{shown} is in {where + ', ' if where else ''}Pune" + (f" (pincode {doc['pincode']})" if doc.get("pincode") else "")
                + ", as filed with MahaRERA. The map and distances to nearby places are on this page.", "MahaRERA")
    return None


def as_written(question: str, doc: dict, shown: str) -> str:
    """The stored (lower-case) question with the project's name as we write it, and a capital first letter."""
    text = question
    for a in sorted({a for a in names(doc)[1] + [hot.search_name(doc.get("name", ""))] if a}, key=len, reverse=True):
        words = re.findall(r"[a-z0-9]+", a.lower())
        if words:
            rx = re.compile(r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(map(re.escape, words)) + r"(?![a-z0-9])", re.I)
            if rx.search(text):
                text = rx.sub(lambda _: shown, text, count=1)
                break
    text = re.sub(r"\b(rera|maharera|bhk|oc)\b",lambda m: "MahaRERA" if m.group(1).lower() == "maharera" else m.group(1).upper(), text,
                  flags=re.I)
    return text[0].upper() + text[1:]


def belongs(question: str, seen_in: List[str], doc: dict) -> bool:
    """A question about this project: it names the project, or Google showed it with a search for the project."""
    aliases = [a for a in names(doc)[1] + [hot.search_name(doc.get("name", "")), doc.get("search_name") or ""] if a]
    if any(mentions(a, question) for a in aliases):
        return True
    return any(any(mentions(a, q) for a in aliases) for q in seen_in or [])


def answers(doc: dict, docs: List[dict], questions: List[dict]) -> List[dict]:
    """Questions [{phrase, seen_in}] answered from facts: one per topic (the most-seen phrasing first), at most MAX."""
    shown = doc.get("search_name") or names(doc)[0]
    out, topics = [], set()
    for qd in questions:
        q = (qd.get("phrase") or "").strip()
        if not q or not belongs(q, qd.get("seen_in") or [], doc):
            continue
        t = topic_of(q)
        if t is None or t == "price" or t in topics:
            continue
        got = answer(t, doc, docs, shown)
        if got is None:
            continue
        topics.add(t)
        text = as_written(q, doc, shown)
        out.append({"q": text if text.endswith("?") else text + "?", "a": got[0], "source": got[1], "topic": t})
        if len(out) >= MAX:
            break
    return out


async def questions_for(db, doc: dict) -> List[dict]:
    """Stored "People also ask" phrases that may be about this project (filtered by `belongs` in `answers`)."""
    regno = doc.get("regno") or doc["_id"]
    docs = await db.get_collection(DEMAND).find({"sources": "question"}).to_list(20000)
    mine = [d for d in docs if d.get("regno") == regno or belongs(d.get("phrase", ""), d.get("seen_in") or [], doc)]
    mine.sort(key=lambda d: (-len(d.get("seen_in") or []), d.get("phrase", "")))
    return mine
