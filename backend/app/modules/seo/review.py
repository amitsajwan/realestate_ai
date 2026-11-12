"""The daily page check: a finished project page read as Google reads it and compared with its sources (docs/plan/seo-system.md).

Why: each step of the enrichment checks its own answer, but nothing looked at the finished page. Owner, 2026-11-02: "every page
we show is it verified, do we check page and analyse". Reports only: it changes no page and no record.

Once a day, inside the seo loop, up to PER_DAY pages in search (never read first, then pages the model could not read, then pages
rewritten since, then any read over AGAIN ago; our areas, hot and seen on Google first) are read live, and:
- rules, always: the page answers 200 and is not noindex; the MahaRERA number, completion date, homes booked and place on the page
  are the record's; the written text is on the page; the text names no other project of the area and no place an unlikely way off;
  a rate per sq ft is believable; the page is not thin (under `THIN_WORDS` words and one kind of fact of its own at most);
- the model, while the enrichment's budget has room (areastats.budget, step "review"): the words we wrote, against the same fact
  sheet the writer was given (enrich.facts_text). An answer counts only with a quote that is really on the page; a number that is
  in the sources is not called wrong. No model or no room: the rules' answer stands and the page is read again the next day.
The page cache may hand a reader the copy from before a change and refresh behind it, so a page that disagrees with its record is
read once more after STALE_WAIT_S. Pages changed within CHANGED_WAIT wait for the next day.
Kept in `seo_page_reviews`, one row per page per day, with the day's count on the `seo_review` mark: Insights → Rankings, the owner's
weekly note and Admin → Health read them.
"""
import asyncio
import html
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import httpx

from app.core.areas import BY_KEY
from app.modules.areastats import budget, enrich, pages, pricing, profile
from app.modules.newsroom.store import Store

from .config import load

log = logging.getLogger(__name__)

MARK = "seo_review"
COLLECTION = "seo_page_reviews"
EVERY = timedelta(hours=24)
PER_DAY = 20
AGAIN = timedelta(days=30)
CHANGED_WAIT = timedelta(hours=2)
STALE_WAIT_S = 5.0
TIME_CAP_S = 600.0     # the seo loop's other steps wait for this one: pages not reached are read tomorrow
SHOWN_DAYS = 14
SHOWN = 40
THIN_WORDS = 60
FAR_KM = 25            # as areastats.pagefacts COMMUTE_KM: nobody calls a place this far "nearby"
RATE_MIN, RATE_MAX = 2500, 70000   # rupees per sq ft: outside this, a price and a size were paired wrongly
SOURCES_CHARS = 9000
PROBLEMS_MAX = 5
MODEL_KINDS = ("number", "wrong_project", "location", "unsupported")
# As audit.AGENT: "-Google" is served the page as Google is, and "AvasetuSeoAudit" stays out of our own AI visit log.
AGENT = "AvasetuSeoAudit-Google/1.0 (+https://github.com/amitsajwan/realestate_ai)"

SYSTEM = """You check one page of a real estate website against the sources it was written from. Find only real errors:
- number: a figure or date on the page that differs from the sources, or is not in them;
- wrong_project: a detail that belongs to another project or another builder;
- location: a place or distance that does not fit where the sources put this project;
- unsupported: a factual claim the sources do not contain.
Do not report style, wording, repetition, opinions, general advice about buying, or anything the sources say.
Reply with JSON only: {"problems": [{"kind": "number|wrong_project|location|unsupported", "quote": "the exact words copied from PAGE",
"why": "one short sentence", "source": "the exact words from SOURCES it differs from, or none"}]}. No errors: {"problems": []}."""


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _squash(text: str) -> str:
    """Words as a reader sees them, to compare two copies: one case, one space, typographic marks and thousands commas gone."""
    text = text.replace("’", "'").replace("‑", "-").replace("–", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", re.sub(r"(?<=\d),(?=\d)", "", text)).strip().casefold()


def plain(raw: str) -> str:
    """A page's visible words (a title stays out: the head is not what a reader sees on the page)."""
    body = re.sub(r"(?is)<(script|style|head|noscript)\b.*?</\1>", " ", raw)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))).strip()


def quoted(raw: str) -> List[str]:
    """What search engines and AI answers quote from a page's head, each apart: its title, its description and its structured
    data (JSON-LD). Not Next's data payload, which carries every registration's raw figures for the page to draw."""
    parts = re.findall(r"(?is)<title[^>]*>(.*?)</title>", raw)
    parts += re.findall(r"""(?is)<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)""", raw)
    parts += re.findall(r"""(?is)<script[^>]+type=["']application/ld\+json["'][^>]*>(.*?)</script>""", raw)
    return [html.unescape(x) for x in parts]


def _sections(doc: dict) -> List[str]:
    """The written text a page shows. Text from before the writer's sections stays on the record but is on no page."""
    if not doc.get("page_text"):
        return []
    return [str(s.get("text") or "") for s in doc.get("page_sections") or []]


def prose(doc: dict) -> List[str]:
    """What we wrote for this page and what we took from sites, as the page shows them."""
    faq = [str(f.get("a") or "") for f in doc.get("seo_faq") or []]
    highlights = [str(h.get("text") or "") for h in profile.shown_highlights(doc.get("profile"), doc)]
    return [t for t in _sections(doc) + highlights + faq if t.strip()]


def _problem(kind: str, detail: str, **more) -> dict:
    return {"kind": kind, "detail": detail, **more}


def against_record(doc: dict, text: str, scope: Optional[dict] = None) -> List[dict]:
    """Where the live words differ from the record: what a page cache can cause, so `check` reads twice before it reports.
    `scope` (pages.project_scope): the page stands for several registrations, so it must say the whole project's bookings."""
    seen, out = _squash(text), []
    regno = str(doc.get("regno") or doc.get("_id") or "")
    if regno and regno.casefold() not in seen:
        out.append(_problem("record", f"MahaRERA number {regno} is not on the page"))
    day = pages._long(pages._day(doc.get("completion_now"))) if doc.get("completion_now") else None
    if day and _squash(day) not in seen:
        out.append(_problem("record", f"Completion date {day} is not on the page"))
    booked, total = pages.booked(doc), pages._count(doc.get("units_total"))
    if scope:
        booked, total = scope["units_booked"], scope["booked_of"]
    if isinstance(booked, int) and isinstance(total, int) and total > 0 and _squash(f"{booked:,} of {total:,}".replace(",", "")) not in seen.replace(",", ""):
        out.append(_problem("record", f"{booked} of {total} homes booked is not on the page"))
    missing = [t for t in _sections(doc) if t.strip() and _squash(t)[:80] not in seen]
    if missing:
        out.append(_problem("record", f"Written text is not on the page: \"{missing[0][:80]}\""))
    return out


SCOPE_REACH = 90   # characters either side of a count within which its registration must be named


def scope_problems(doc: dict, text: str, scope: Optional[dict]) -> List[dict]:
    """On a page that stands for several registrations, the main registration's own home count said without its registration
    beside it: one part's figure read as the project's (2026-11-12: 85 of 88 such pages did, Venkatesh Vanaya 168 of 745).
    The towers table and the record's notes name the registration, so they pass."""
    total = pages._count(doc.get("units_total"))
    if not scope or not total or total == scope["units_total"] or total == scope["booked_of"]:
        return []
    regno = str(doc.get("regno") or doc.get("_id") or "").casefold()
    flat = " ".join(text.split())
    for m in re.finditer(rf"(?<![\d,]){total}(?![\d,])", flat):
        around = flat[max(0, m.start() - SCOPE_REACH):m.end() + SCOPE_REACH].casefold()
        if regno not in around and "registration" not in around:
            return [_problem("scope", f"{total}, one registration's homes, is said without naming the registration: "
                                      f"\"{flat[max(0, m.start() - 60):m.end() + 30]}\"")]
    return []


def _place(doc: dict) -> Optional[str]:
    area = BY_KEY.get(doc.get("locality") or "")
    return doc.get("pune_place_name") or (area.name if area else None)


def rule_problems(doc: dict, raw: str, others: List[str], scope: Optional[dict] = None) -> List[dict]:
    """Everything the rules see on one page that answered 200. `others` are other projects' names in its area; `scope`
    (pages.project_scope) when the page stands for several registrations."""
    out, text = [], plain(raw)
    if re.search(r"""(?i)<meta[^>]+name=["']robots["'][^>]+noindex""", raw):
        out.append(_problem("not_in_search", "The page says noindex, though its record counts as in search"))
    out += against_record(doc, text, scope)
    # the head's title, description and structured data are what search and AI answers quote: each is checked on its own, so
    # a registration named at the end of one does not excuse a count at the start of the next
    for part in [text, *quoted(raw)]:
        found = scope_problems(doc, part, scope)
        if found:
            out += found
            break
    place = _place(doc)
    if place and _squash(place) not in _squash(text):
        out.append(_problem("location", f"The page does not name {place}"))
    written = " ".join(prose(doc))
    for km in re.findall(r"(\d+(?:\.\d+)?)\s*km away", written):
        if float(km) > FAR_KM:
            out.append(_problem("location", f"A place called nearby is {km} km away"))
            break
    own = [_squash(n) for n in (pages.names(doc)[0], pages.family_name(doc))]
    found = _squash(written)
    named = next((n for n in others if re.search(rf"\b{re.escape(_squash(n))}\b", found)
                  and not any(_squash(n) in o or o in _squash(n) for o in own)), None)
    if named:
        out.append(_problem("wrong_project", f"The text names another project: {named}"))
    for rate in re.findall(r"₹\s?([\d,]+)\s*/\s*sq\s?ft", text):
        if not RATE_MIN <= int(rate.replace(",", "") or 0) <= RATE_MAX:
            out.append(_problem("number", f"A rate of ₹{rate}/sq ft is not believable"))
            break
    kinds = sum(bool(k) for k in ((doc.get("prices") or {}).get("rows"), (doc.get("web_facts") or {}).get("facts"),
                                  (doc.get("profile") or {}).get("highlights")))
    words = len(" ".join(_sections(doc)).split())
    if words < THIN_WORDS and kinds < 2:   # short text is fine beside facts: the writer leaves out what the page already says
        out.append(_problem("thin", f"{words} written words and {kinds} of 3 kinds of own facts (prices, web facts, highlights)"))
    return out


async def model_question(db, doc: dict) -> Optional[tuple]:
    """(sources, the question) for this page; None when we wrote nothing for the model to check."""
    written = prose(doc)
    if not written:
        return None
    sources = await enrich.sources_text(db, doc)
    head = f"Project: {pages.names(doc)[0]}. MahaRERA number: {doc.get('regno') or doc.get('_id')}. Area: {_place(doc) or '-'}."
    return sources, f"{head}\n\nSOURCES:\n{sources[:SOURCES_CHARS]}\n\nPAGE:\n" + "\n".join(written)


def checked_answer(answer: Optional[dict], text: str, sources: str) -> List[dict]:
    """The model's problems that pass: a known kind, a quote that is on the page, and no figure the sources already hold. A model
    is as able to invent an error as a fact, and a false alarm a day would stop this report being read."""
    seen, known, out = _squash(text), _squash(sources), []
    for p in (answer or {}).get("problems") or []:
        if not isinstance(p, dict):
            continue
        kind, quote, why = p.get("kind"), str(p.get("quote") or "").strip(), str(p.get("why") or "").strip()
        if kind not in MODEL_KINDS or len(quote) < 3 or not why or _squash(quote) not in seen:
            continue
        figures = re.findall(r"\d+(?:\.\d+)?", _squash(quote))
        if kind == "number" and figures and all(re.search(rf"(?<![\d.]){re.escape(f)}(?!\d)", known) for f in figures):
            continue
        out.append(_problem(kind, why[:240], quote=quote[:240], source=str(p.get("source") or "")[:240], by="model"))
    return out[:PROBLEMS_MAX]


async def check(db, doc: dict, url: str, others: List[str], http: httpx.AsyncClient, ask, wait_s: float = STALE_WAIT_S,
                scope: Optional[dict] = None) -> dict:
    """{problems, model}: one page. A read that fails altogether raises, and the page stays due: a restart is not the page's fault."""
    headers = {"User-Agent": AGENT}
    r = await http.get(url, headers=headers)
    if r.status_code == 200 and against_record(doc, plain(r.text), scope):
        await asyncio.sleep(wait_s)
        r = await http.get(url, headers=headers)
    if r.status_code != 200:
        return {"problems": [_problem("not_in_search", f"The page answered {r.status_code}")], "model": False}
    problems = rule_problems(doc, r.text, others, scope)
    question = await model_question(db, doc)
    if question is None:
        return {"problems": problems, "model": True}   # nothing written: nothing for the model to read, so no reason to come back
    answer = await ask.json(SYSTEM, question[1]) if ask is not None else None
    if not isinstance(answer, dict):
        return {"problems": problems, "model": False}
    return {"problems": problems + checked_answer(answer, plain(r.text), question[0]), "model": True}


def pick(docs: List[dict], latest: Dict[str, dict], now: datetime, n: int = PER_DAY) -> List[dict]:
    """Up to n pages due, most worth reading first (see the module note)."""
    due = []
    for d in docs:
        slug = d.get("page_slug")
        if not slug or d.get("cluster_primary") or not pages.searchable(d):
            continue
        changed = max((t for t in map(_aware, (d.get("page_text_at"), d.get("enriched_at"), d.get("details_checked_at"))) if t),
                      default=None)
        if changed and now - changed < CHANGED_WAIT:
            continue
        row = latest.get(slug)
        at = _aware((row or {}).get("at"))
        if at is None:
            turn = 0
        elif not row.get("model"):
            turn = 1
        elif changed and changed > at:
            turn = 2
        elif now - at >= AGAIN:
            turn = 3
        else:
            continue
        due.append(((turn, d.get("locality") not in BY_KEY, -float(d.get("hot_score") or 0), -int(d.get("gsc_impressions") or 0), slug), d))
    return [d for _, d in sorted(due, key=lambda x: x[0])[:n]]


def _others(doc: dict, docs: List[dict]) -> List[str]:
    """Other projects' names in its area, of two words or more: one word ("Vista") is too often an ordinary word."""
    names = {pages.names(d)[0] for d in docs if d.get("locality") == doc.get("locality") and d.get("page_slug")
             and d.get("page_slug") != doc.get("page_slug") and d.get("cluster_primary") != doc.get("_id")}
    return sorted((n for n in names if len(n.split()) >= 2 and len(n) >= 8), key=len, reverse=True)


async def _latest(rows) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    async for r in rows.find({}, {"page_slug": 1, "at": 1, "model": 1}):
        have = _aware((out.get(r.get("page_slug")) or {}).get("at"))
        if have is None or (_aware(r.get("at")) or have) > have:
            out[r.get("page_slug")] = r
    return out


async def run_once(store: Store, now: datetime, http: Optional[httpx.AsyncClient] = None, wait_s: float = STALE_WAIT_S) -> Optional[dict]:
    """Today's pages. None when switched off, already run in the last EVERY, or nothing is due."""
    cfg = load()
    last = _aware((await store.get_mark(MARK)).get("at"))
    if not cfg.review_on or (last is not None and now - last < EVERY):
        return None
    rows = store.db.get_collection(COLLECTION)
    docs = await store.shared_projects()
    chosen = pick(docs, await _latest(rows), now)
    if not chosen:
        return None
    reader = await budget.reader(store.db, now)
    client = http or httpx.AsyncClient(timeout=60, follow_redirects=False)
    started, out = time.monotonic(), {"read": 0, "flagged": 0, "model": 0, "unread": 0}
    kinds: Dict[str, int] = {}
    try:
        for doc in chosen:
            if time.monotonic() - started > TIME_CAP_S:
                break
            slug, url = doc["page_slug"], f"{cfg.site}/projects/{doc['page_slug']}"
            ask = reader.ask(pricing.tier_of(doc, now), "review") if reader else None
            try:
                res = await check(store.db, doc, url, _others(doc, docs), client, ask, wait_s,
                                  pages.project_scope(doc, docs, pages.load_index(docs)))
            except asyncio.CancelledError:
                raise
            except Exception as e:   # one page must not stop the others; it is still due tomorrow
                log.warning("seo: page check of %s failed: %s", slug, type(e).__name__)
                out["unread"] += 1
                continue
            await rows.update_one({"_id": f"{slug}:{budget.day_of(now)}"},
                                  {"$set": {"page_slug": slug, "regno": doc.get("regno") or doc["_id"], "name": pages.names(doc)[0],
                                            "url": url, "at": now, **res}}, upsert=True)
            out["read"] += 1
            out["flagged"] += bool(res["problems"])
            out["model"] += bool(res["model"])
            for p in res["problems"]:
                kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    finally:
        if http is None:
            await client.aclose()
    await store.set_mark(MARK, at=now, kinds=kinds, **out)
    return out


async def summary(store: Store, now: datetime) -> dict:
    """{at, read, flagged, model, week, week_flagged, items}: the last run, the week's count, and each page's latest read if it
    has problems (a page read clean since is off the list)."""
    mark = await store.get_mark(MARK)
    latest: Dict[str, dict] = {}
    week, week_flagged = 0, 0
    since = now - timedelta(days=SHOWN_DAYS)
    async for r in store.db.get_collection(COLLECTION).find({}):
        at = _aware(r.get("at"))
        if at is None or at < since:
            continue
        if now - at <= timedelta(days=7):
            week += 1
            week_flagged += bool(r.get("problems"))
        have = _aware((latest.get(r.get("page_slug")) or {}).get("at"))
        if have is None or at > have:
            latest[r.get("page_slug")] = r
    flagged = sorted((r for r in latest.values() if r.get("problems")), key=lambda r: _aware(r["at"]), reverse=True)
    at = _aware(mark.get("at"))
    return {"at": at.isoformat() if at else None, "read": mark.get("read", 0), "flagged": mark.get("flagged", 0),
            "model": mark.get("model", 0), "week": week, "week_flagged": week_flagged,
            "items": [{"slug": r["page_slug"], "name": r.get("name"), "url": r.get("url"), "at": _aware(r["at"]).isoformat(),
                       "problems": r["problems"]} for r in flagged[:SHOWN]]}


def week_line(s: dict) -> str:
    """The owner's weekly note (note.py)."""
    if not s.get("week"):
        return ""
    return f"Page check, 7 days: {s['week']} pages read against their sources, {s['week_flagged']} with something to look at: Insights → Rankings."
