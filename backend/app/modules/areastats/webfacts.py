"""Facts about a project from the web: the builder's own site and the sites that rank for the project on Google
(docs/plan/project-pages.md, "From the web"). One more step of the project-page enrichment (areastats.enrich).

For one project (a tower group is read once, on its primary record):
1. sources: the Google results stored for the project (areastats.websearch, `web_search_results`); when there are none and a
   results provider is configured, ONE search "<name buyers use> <area> Pune" is made and stored. The builder's own site comes
   first (`official`: its domain is the builder's word, alone or with "group", "developers", ...; a microsite such as
   "lodhacamelot.in" is not), then other sites whose result names the project, in Google's order: up to MAX_SOURCES pages that
   answer, out of MAX_TRIES.
2. each page is read once (plain GET, size and time capped) and cut to the lines that can hold a fact (`relevant`).
3. ONE model call per page answers a fixed list of facts (KEYS), each with the sentence it came from.
4. checks: the sentence must be on the page (`on_page`) and the value must be in that sentence. A fact is published when the
   builder's site says it, or when two sites agree (`agree`; numbers within 5%). Sites that disagree publish nothing and the
   disagreement is kept for the owner. Text facts (architect, partners) need the builder's site. MahaRERA's record always wins:
   nothing here touches its dates, bookings or registration numbers, and possession dates are not read at all.
Stored on the register record as `web_facts` = {at, facts: [{key, label, value, text, official, sources: [{site, url, quote}]}],
disagree: [{key, readings}], read: [{site, url, ok, why}]}; `pages.web_public` is what the pages show.
"""
import html
import logging
import re
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx

from app.core.areas import BY_KEY

from . import pages, websearch

log = logging.getLogger(__name__)

MAX_SOURCES = 4                       # pages read per project
MAX_TRIES = 8                         # pages tried (portals often refuse a reader): the next result is tried instead
MAX_BYTES = 2_000_000
PAGE_CHARS = 9000                     # what one model call reads from a page
TIMEOUT = 15
UA = "Mozilla/5.0 (compatible; AvasetuBot/1.0; +https://avasetu.in)"
# key -> (label, kind): "int" and "num" are compared within TOLERANCE, "text" needs the builder's own site
KEYS: Dict[str, tuple] = {
    "towers": ("Towers", "int"),
    "floors": ("Floors per tower (highest)", "int"),
    "land_acres": ("Land", "num"),
    "open_space_pct": ("Open space", "num"),
    "homes_total": ("Homes in the project", "int"),
    "clubhouse_sqft": ("Clubhouse", "int"),
    "architect": ("Architect", "text"),
    "partners": ("Design and service partners", "text"),
}
TOLERANCE = 0.05
OFFICIAL_SUFFIXES = ("", "group", "developers", "developer", "realty", "homes", "properties", "builders", "corp", "constructions",
                     "infra", "estates", "living", "lifespaces", "landmarks")
# words a line must have (one of) to be read: the facts in KEYS, and the project's own name
HINTS = re.compile(r"\b(towers?|acres?|floors?|storey|storeys|stories|g\s*\+\s*\d+|open\s*space|club\s*house|clubhouse|sq\.?\s*ft|"
                   r"square\s*feet|units|apartments|homes|residences|architect|designed\s*by|landscape|interiors?|partner)\b", re.I)

Fetch = Callable[[str], Awaitable[Optional[str]]]   # url -> page HTML, or None


async def fetch_page(url: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[str]:
    """The page's HTML (at most MAX_BYTES), or None when it is not an HTML page that answered 200."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, transport=transport,
                                     headers={"User-Agent": UA, "Accept": "text/html", "Accept-Language": "en-IN,en"}) as c:
            async with c.stream("GET", url) as r:
                if r.status_code != 200 or "html" not in (r.headers.get("content-type") or ""):
                    return None
                body = b""
                async for chunk in r.aiter_bytes():
                    body += chunk
                    if len(body) > MAX_BYTES:
                        break
                return body.decode(r.charset_encoding or "utf-8", errors="replace")
    except Exception as e:
        log.info("webfacts: %s not read (%s)", url, type(e).__name__)
        return None


def memo(fetch: Fetch) -> Fetch:
    """`fetch` that reads each address once (one enrichment round reads the same pages for web facts and the profile)."""
    got: Dict[str, Optional[str]] = {}

    async def once(url: str) -> Optional[str]:
        if url not in got:
            got[url] = await fetch(url)
        return got[url]
    return once


def page_text(raw: str) -> str:
    """Visible text, one block per line."""
    s = re.sub(r"(?is)<(script|style|noscript|svg|template)\b.*?</\1>", " ", raw or "")
    s = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr|section|article|td|th)>", "\n", s)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    lines = (re.sub(r"[ \t\r\f\v ]+", " ", ln).strip() for ln in s.split("\n"))
    return "\n".join(ln for ln in lines if ln)


def relevant(text: str, name: str, limit: int = PAGE_CHARS) -> str:
    """The lines that can hold a fact in KEYS (or name the project), in page order, up to `limit` characters."""
    first = (name or "").split()[:1]
    out, size = [], 0
    for ln in text.split("\n"):
        if len(ln) < 8 or len(ln) > 600:
            continue
        if HINTS.search(ln) or (first and first[0].lower() in ln.lower() and re.search(r"\d", ln)):
            if size + len(ln) > limit:
                break
            out.append(ln)
            size += len(ln) + 1
    return "\n".join(out)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[‘’“”]", "'", s or "")).strip().lower()


def on_page(quote: str, text: str) -> bool:
    q = _norm(quote)
    return len(q) >= 12 and q in _norm(text)


def number(v: Any) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"\d[\d,]*(?:\.\d+)?", str(v or ""))
    return float(m.group(0).replace(",", "")) if m else None


def value_in_quote(kind: str, value: Any, quote: str) -> bool:
    """A number must be written in its sentence ("24" for G+24, "30,000" for 30000); text must share a word of 4+ letters."""
    if kind == "text":
        words = {w for w in re.findall(r"[a-z]{4,}", _norm(str(value)))}
        return bool(words) and any(w in _norm(quote) for w in words)
    n = number(value)
    if n is None:
        return False
    found = {float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", quote)}
    return n in found


def official(link: str, builder_word: str) -> bool:
    """The builder's own site: its domain name is the builder's word, alone or with a company suffix (lodhagroup.com)."""
    host = websearch.site(link)
    label = host.split(".")[0] if host else ""
    w = re.sub(r"[^a-z0-9]", "", (builder_word or "").lower())
    return bool(w) and len(w) >= 3 and any(label == w + s for s in OFFICIAL_SUFFIXES)


def builder_word(promoter: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", promoter or "")
    return words[0].lower() if words else ""


def pick_sources(results: List[dict], name: str, word: str, limit: int = MAX_SOURCES) -> List[dict]:
    """[{url, site, official}]: the builder's own site first, then other sites whose result names the project; one per site."""
    organic = sorted((r for r in results if r.get("type", "organic") == "organic" and r.get("link")),
                     key=lambda r: int(r.get("position") or 99))
    out, seen = [], set()
    for want_official in (True, False):
        for r in organic:
            s, is_official = websearch.site(r["link"]), official(r["link"], word)
            if s in seen or is_official != want_official or len(out) >= limit:
                continue
            if not is_official and (not websearch.marketer(r["link"]) or not websearch.mentions(name, r.get("title", "") + " " + r.get("snippet", ""))):
                continue
            seen.add(s)
            out.append({"url": r["link"], "site": s, "official": is_official})
    return out


SYSTEM = ("You read one web page about a housing project in Pune and pick out facts about THAT project only (not other projects "
          "on the page, not the builder company in general). For each key give the value and the exact sentence from the page "
          "it comes from, copied word for word. Leave out any key the page does not state for this project. Keys: "
          "towers (number of towers or buildings), floors (highest number of floors in a tower: 24 for G+24), land_acres "
          "(land area in acres), open_space_pct (open space as a percent), homes_total (total homes or units in the project), "
          "clubhouse_sqft (clubhouse size in sq ft), architect (the architect firm's name), partners (named design, landscape, "
          "interiors or hospitality partners, comma-separated). Do not guess, do not convert units except G+N -> N. "
          'Answer as JSON: {"facts": [{"key": "...", "value": ..., "quote": "..."}]}')


async def read_source(llm, src: dict, name: str, fetch: Fetch) -> tuple:
    """(readings, why): readings are [{key, value, quote, site, url, official}] that passed the page checks."""
    raw = await fetch(src["url"])
    if not raw:
        return [], "page not read"
    text = page_text(raw)
    if not websearch.mentions(name, text):
        return [], "page does not name the project"
    part = relevant(text, name)
    if not part:
        return [], "no lines with facts"
    try:
        out = await llm.json(SYSTEM, f"Project: {name}\nPage: {src['url']}\n\n{part}")
    except Exception as e:
        log.exception("webfacts: model call failed for %s", src["url"])
        return [], f"model call failed ({type(e).__name__})"
    readings, refused = [], 0
    for f in (out or {}).get("facts") or []:
        key, quote, value = str(f.get("key") or ""), str(f.get("quote") or ""), f.get("value")
        if key not in KEYS or value in (None, "", []):
            continue
        kind = KEYS[key][1]
        if not on_page(quote, text) or not value_in_quote(kind, value, quote):
            refused += 1
            continue
        if kind != "text":
            value = number(value)
            if value is None or value <= 0:
                continue
            if kind == "int":
                value = int(value)
        else:
            value = " ".join(str(value).split())[:160]
        readings.append({"key": key, "value": value, "quote": " ".join(quote.split())[:300], "site": src["site"],
                         "url": src["url"], "official": src["official"]})
    return readings, f"{len(readings)} facts" + (f", {refused} refused (not on the page)" if refused else "")


def _same(kind: str, a: Any, b: Any) -> bool:
    if kind == "text":
        return _norm(str(a)) == _norm(str(b))
    return abs(float(a) - float(b)) <= TOLERANCE * max(abs(float(a)), abs(float(b)))


def agree(readings: List[dict]) -> tuple:
    """(facts, disagree): a key is published from the builder's site, or when two different sites agree; sites that disagree
    publish nothing for that key."""
    facts, disagree = [], []
    for key, (label, kind) in KEYS.items():
        rs = [r for r in readings if r["key"] == key]
        if not rs:
            continue
        own = [r for r in rs if r["official"]]
        if own:
            value = own[0]["value"]
            backing = [r for r in rs if _same(kind, r["value"], value)]
            if len({websearch.site(r["url"]) for r in own}) == 1 and all(_same(kind, r["value"], value) for r in own):
                facts.append(_fact(key, label, kind, value, True, backing))
            else:
                disagree.append({"key": key, "readings": _brief(rs)})
            continue
        if kind == "text":
            continue                                    # names only from the builder's own site
        groups: List[List[dict]] = []
        for r in rs:
            g = next((g for g in groups if _same(kind, g[0]["value"], r["value"])), None)
            g.append(r) if g is not None else groups.append([r])
        sized = sorted(groups, key=lambda g: -len({x["site"] for x in g}))
        best = sized[0]
        if len({x["site"] for x in best}) >= 2 and (len(sized) == 1 or len({x["site"] for x in sized[1]}) < len({x["site"] for x in best})):
            facts.append(_fact(key, label, kind, best[0]["value"], False, best))
        elif len(groups) > 1:
            disagree.append({"key": key, "readings": _brief(rs)})
    return facts, disagree


def _brief(rs: List[dict]) -> List[dict]:
    return [{"site": r["site"], "url": r["url"], "value": r["value"], "quote": r["quote"]} for r in rs]


def show(key: str, value: Any) -> str:
    """How a fact reads on the page."""
    if key == "land_acres":
        return f"{value:g} acres"
    if key == "open_space_pct":
        return f"{value:g}%"
    if key == "clubhouse_sqft":
        return f"{int(value):,} sq ft"
    if key == "floors":
        return f"up to {int(value)} floors"
    return f"{value:g}" if isinstance(value, float) else str(value)


def _fact(key: str, label: str, kind: str, value: Any, is_official: bool, backing: List[dict]) -> dict:
    srcs, seen = [], set()
    for r in sorted(backing, key=lambda r: not r["official"]):
        if r["site"] not in seen:
            seen.add(r["site"])
            srcs.append({"site": r["site"], "url": r["url"], "quote": r["quote"]})
    return {"key": key, "label": label, "value": value, "text": show(key, value), "official": is_official, "sources": srcs}


async def results_for(store, doc: dict, name: str, search: Optional[websearch.Search], now: datetime) -> List[dict]:
    """The stored Google results for this project (newest search first), from searches made under the name buyers use (a search
    under MahaRERA's legal name, "Kharadi New Project - Tower 1", finds other pages); one new search when there are none."""
    coll = store.db.get_collection(websearch.RESULTS)
    regno = doc.get("regno") or doc["_id"]
    docs = [d for d in await coll.find({"kind": "project"}).sort("at", -1).to_list(500)
            if websearch.mentions(name, d["_id"]) and d.get("regno") in (regno, None)][:3]
    if docs:
        return [r for d in docs for r in d.get("results") or []]
    if search is None:
        return []
    area = BY_KEY.get(doc.get("locality") or "")
    q = " ".join(x for x in (name, doc.get("pune_place_name") or (area.name if area else ""), "Pune") if x)
    try:
        results = await search(q)
    except Exception:
        log.exception("webfacts: search failed: %s", q)
        return []
    body = {"kind": "project", "area": doc.get("locality"), "regno": regno, "at": now, "results": results[:websearch.KEEP_RESULTS]}
    if await coll.find_one({"_id": q}):
        await coll.update_one({"_id": q}, {"$set": body})
    else:
        await coll.insert_one({"_id": q, **body})
    return results


async def gather(store, doc: dict, llm, now: datetime, fetch: Optional[Fetch] = None,
                 search: Optional[websearch.Search] = None) -> tuple:
    """(step, register fields) for areastats.enrich. Nothing is stored for a tower that is not its group's primary record."""
    if doc.get("cluster_primary"):
        return {"ok": True, "at": now, "checked": "read on the group's primary record"}, {}
    if llm is None:
        return {"ok": False, "at": now, "checked": "no LLM key"}, {}
    name = pages.names(doc)[0]
    results = await results_for(store, doc, name, search if search is not None else websearch.provider(), now)
    sources = pick_sources(results, name, builder_word(doc.get("promoter") or ""), limit=MAX_TRIES)
    if not sources:
        return {"ok": False, "at": now, "checked": "no web results name the project"}, {}
    readings, read = [], []
    for src in sources:
        if sum(1 for r in read if r["why"] != "page not read") >= MAX_SOURCES:
            break
        got, why = await read_source(llm, src, name, fetch or fetch_page)
        readings += got
        read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": bool(got), "why": why})
    facts, disagree = agree(readings)
    web = {"at": now, "name": name, "facts": facts, "disagree": disagree, "read": read}
    checked = f"{len(facts)} facts from {sum(1 for r in read if r['ok'])} of {len(read)} sites" + \
              (f", {len(disagree)} where sites disagree" if disagree else "")
    return {"ok": bool(facts), "at": now, "checked": checked}, {"web_facts": web}


def lines(web: Optional[dict]) -> List[str]:
    """The published facts as labelled lines for the page-text model (areastats.enrich.facts_text)."""
    return [f"{f['label']}: {f['text']} (from {', '.join(s['site'] for s in f['sources'])})" for f in (web or {}).get("facts") or []]
