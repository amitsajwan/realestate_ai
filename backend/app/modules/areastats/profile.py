"""A project's profile for its page: highlights (bullet points), the builder's pictures and floor plans (docs/plan/project-pages.md,
"Project profile", 2026-10-15). One more step of the project-page enrichment (areastats.enrich), after the web facts, and only for
projects still being built: once MahaRERA's filed completion date has passed the profile is no longer read (the page keeps what it
had). Each enrichment round reads it again, so it grows and stays current; hot projects without one are enriched first.

For one project (a tower group is read once, on its primary record):
1. sources: the same pages as the web facts (areastats.webfacts: the builder's own site first, then sites naming the project).
2. highlights: ONE model call per page answers a fixed list of topics (TOPICS), each with the sentence it came from. Kept only when
   the sentence is on the page, every number of the bullet is in that sentence and it has no sales words. Published when the
   builder's site says it, or when two sites state the same topic (the first site's wording, both sites as sources). Never prices,
   possession dates or travel times: MahaRERA's dates win, and distances are measured from the project's own pin.
3. pictures: only from the builder's own site, and only from the project's own page there (its address names the project: a home
   page shows other projects). Each picture is downloaded once, checked (size, shape, not a logo or icon, not a near-duplicate),
   sorted into photo or floor plan by its address and alt text, and kept as WebP under uploads/project_media/<regno>/. Portal
   pictures are never taken (watermarked, theirs). Pages say where each picture came from and that renders are artist's
   impressions.
Stored on the register record as `profile` = {at, highlights: [{topic, text, official, sources: [{site, url, quote}]}],
photos: [...], plans: [...], read: [{site, url, ok, why}]}; a round that finds nothing keeps the last good highlights or pictures.
`public` is what the pages show.
"""
import io
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from PIL import Image

from . import pages, webfacts, websearch

log = logging.getLogger(__name__)

MEDIA_DIR = Path("uploads") / "project_media"
MAX_PAGES = 4                         # pages read for highlights (the same sources as the web facts)
MAX_HIGHLIGHTS = 8
MAX_PHOTOS = 8
MAX_PLANS = 8
MAX_CANDIDATES = 40                   # pictures downloaded per project, at most
MAX_IMAGE_BYTES = 8_000_000
MIN_PHOTO_W, MIN_PHOTO_H = 800, 450
MIN_PLAN_SIDE = 500
KEEP_SIDE = 1600                      # longest side kept
NEAR = 10                             # dHash bits under which two pictures are the same
# topic -> label; the model must use one of these
TOPICS: Dict[str, str] = {
    "homes": "Homes on offer (BHK types, sizes)",
    "amenities": "Amenities",
    "clubhouse": "Clubhouse",
    "open_space": "Land and open space",
    "towers": "Towers and floors",
    "design": "Architect and design partners",
    "specifications": "Specifications (flooring, fittings, kitchen)",
    "green": "Green features and certifications",
    "parking": "Parking",
    "security": "Security",
}
NOT_SAID = re.compile(r"₹|\brs\.?\s*\d|\blakh|\bcrore|\bprice|\bpossession|\bminutes?\b|\bmins?\b|\bkm\b|\bkms\b|\bdrive\b|\baway\b", re.I)
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
PLAN = re.compile(r"floor[-_ ]?plan|unit[-_ ]?plan|typical[-_ ]?floor|\b[1-5](?:\.5)?[-_ ]?bhk\b|master[-_ ]?plan|site[-_ ]?plan|"
                  r"layout|cluster[-_ ]?plan|carpet", re.I)
JUNK = re.compile(r"logo|icon|favicon|sprite|avatar|placeholder|loader|whatsapp|qr[-_]?code|award|certificate|team|director|"
                  r"chairman|testimonial|client|partner[-_]?logo|google[-_]?map|staticmap|badge|arrow|button|flag|blank|pixel|"
                  r"emoji|social|facebook|instagram|youtube|twitter|linkedin", re.I)
EMBEDDED = re.compile(r"""https?://[^\s"'<>()\\]+?\.(?:jpe?g|png|webp)(?=["'?\s\\])""", re.I)
# renders of rooms ("4-bhk-bedroom-1") are photos, not floor plans, unless they say plan or layout
ROOM = re.compile(r"bed\s*room|kitchen|living|foyer|bath|toilet|balcony|dining|lobby|interior", re.I)
SUBPAGE = re.compile(r"gallery|photos?|images|plans?|floor|layout|amenit|walkthrough", re.I)
MAX_SUBPAGES = 3                      # the builder's own gallery / plans pages under the project's page
EXT = re.compile(r"\.(jpe?g|png|webp)(?:$|\?)", re.I)

FetchBytes = Callable[[str], Awaitable[Optional[bytes]]]


# ---- highlights ------------------------------------------------------------------------------------------------------------

SYSTEM = ("You read one web page about a housing project in Pune and pick its main highlights for buyers, for THAT project only "
          "(not other projects on the page, not the builder company). One short bullet per topic, plain words, at most 20 "
          "words, no praise words (best, luxury, premium, world-class...). For each give the topic, the bullet and the exact "
          "sentence from the page it comes from, copied word for word. Topics: " + ", ".join(f"{k} ({v})" for k, v in TOPICS.items()) +
          ". Never prices, offers, possession or completion dates, distances or travel times. Leave out any topic the page does "
          'not state. Answer as JSON: {"highlights": [{"topic": "...", "text": "...", "quote": "..."}]}')

HINTS = re.compile(r"\b(bhk|sq\.?\s*ft|carpet|amenit\w*|club\s*house|clubhouse|pool|gym|garden|park|acres?|open\s*space|towers?|"
                   r"floors?|storey\w*|architect|designed|landscape|interiors?|flooring|vitrified|kitchen|modular|fittings|"
                   r"igbc|leed|green|solar|rain\s*water|parking|security|cctv|residences|apartments|homes|jogging|court|"
                   r"play|deck|lounge|spa)\b", re.I)


def relevant(text: str, name: str, limit: int = webfacts.PAGE_CHARS) -> str:
    """The lines that can hold a highlight, in page order, up to `limit` characters."""
    first = (name or "").split()[:1]
    out, size = [], 0
    for ln in text.split("\n"):
        if len(ln) < 8 or len(ln) > 600:
            continue
        if HINTS.search(ln) or (first and first[0].lower() in ln.lower()):
            if size + len(ln) > limit:
                break
            out.append(ln)
            size += len(ln) + 1
    return "\n".join(out)


def bullet_ok(text: str, quote: str, page: str) -> bool:
    """The quote is on the page, every number of the bullet is in the quote, and the bullet has no sales words or banned topics."""
    from .enrich import BANNED   # enrich imports this module
    if not text or len(text) > 160 or BANNED.search(text) or NOT_SAID.search(text) or NOT_SAID.search(quote):
        return False
    if not webfacts.on_page(quote, page):
        return False
    have = {n.replace(",", "") for n in NUM.findall(quote)}
    return all(n.replace(",", "") in have for n in NUM.findall(text))


async def read_highlights(llm, src: dict, name: str, text: str) -> tuple:
    """(readings, why): [{topic, text, quote, site, url, official}] that passed the checks."""
    part = relevant(text, name)
    if not part:
        return [], "no lines with highlights"
    try:
        out = await llm.json(SYSTEM, f"Project: {name}\nPage: {src['url']}\n\n{part}")
    except Exception as e:
        log.exception("profile: model call failed for %s", src["url"])
        return [], f"model call failed ({type(e).__name__})"
    readings, refused = [], 0
    for h in (out or {}).get("highlights") or []:
        topic, bullet, quote = str(h.get("topic") or ""), " ".join(str(h.get("text") or "").split()), str(h.get("quote") or "")
        if topic not in TOPICS:
            continue
        if not bullet_ok(bullet, quote, text):
            refused += 1
            continue
        readings.append({"topic": topic, "text": bullet.rstrip("."), "quote": " ".join(quote.split())[:300],
                         "site": src["site"], "url": src["url"], "official": src["official"]})
    return readings, f"{len(readings)} highlights" + (f", {refused} refused" if refused else "")


def agree(readings: List[dict]) -> List[dict]:
    """One bullet per topic: the builder's site's, else one two sites both state (the first site's wording)."""
    out = []
    for topic in TOPICS:
        rs = [r for r in readings if r["topic"] == topic]
        own = [r for r in rs if r["official"]]
        sites = list(dict.fromkeys(r["site"] for r in rs))
        if own:
            pick, backing = own[0], [own[0]]
        elif len(sites) >= 2:
            pick = rs[0]
            backing = [pick] + [next(r for r in rs if r["site"] == s) for s in sites[1:2]]
        else:
            continue
        out.append({"topic": topic, "text": pick["text"], "official": bool(own),
                    "sources": [{"site": r["site"], "url": r["url"], "quote": r["quote"]} for r in backing]})
    return out[:MAX_HIGHLIGHTS]


# ---- pictures --------------------------------------------------------------------------------------------------------------

def project_page(url: str, name: str) -> bool:
    """The builder's page for this project, not its home page or a list: the address's path names the project."""
    path = re.sub(r"[^a-z0-9]", "", urlparse(url).path.lower())
    skip = {"the", "by", "and", "of", "at", "in", "pune", "phase", "project", "tower", "wing", "building"}
    words = [w for w in re.findall(r"[a-z0-9]+", (name or "").lower()) if w not in skip and not w.isdigit() and len(w) >= 3]
    return bool(words) and all(w in path for w in words[:2])


def _attr(tag: str, name: str) -> str:
    m = re.search(r'\b' + name + r'\s*=\s*("([^"]*)"|\'([^\']*)\')', tag, re.I)
    return (m.group(2) if m.group(2) is not None else m.group(3)) if m else ""


def _largest(srcset: str) -> str:
    best, size = "", -1.0
    for part in srcset.split(","):
        bits = part.strip().split()
        if not bits:
            continue
        w = re.match(r"(\d+(?:\.\d+)?)[wx]$", bits[1]) if len(bits) > 1 else None
        n = float(w.group(1)) if w else 0.0
        if n > size:
            best, size = bits[0], n
    return best


def candidates(raw: str, base: str) -> List[dict]:
    """[{url, alt}] of the pictures a page shows, in page order: og:image first, then <img>/<source> (lazy-load attributes and
    the largest srcset entry too) and links straight to pictures. Logos, icons and other junk are left out."""
    out, seen = [], set()

    def add(src: str, alt: str = "") -> None:
        src = (src or "").strip()
        if not src or src.startswith("data:"):
            return
        url = urljoin(base, src)
        if not url.startswith("http") or not EXT.search(url) or url in seen or JUNK.search(urlparse(url).path + " " + alt):
            return
        seen.add(url)
        out.append({"url": url, "alt": " ".join(alt.split())[:140]})

    for m in re.finditer(r"<meta\b[^>]*>", raw or "", re.I):
        if _attr(m.group(0), "property").lower() in ("og:image", "og:image:url"):
            add(_attr(m.group(0), "content"))
    for m in re.finditer(r"<(img|source)\b[^>]*>", raw or "", re.I):
        tag = m.group(0)
        alt = _attr(tag, "alt") or _attr(tag, "title")
        for a in ("data-src", "data-lazy-src", "data-original", "src"):
            if _attr(tag, a):
                add(_attr(tag, a), alt)
                break
        for a in ("data-srcset", "srcset"):
            if _attr(tag, a):
                add(_largest(_attr(tag, a)), alt)
    for m in re.finditer(r"<a\b[^>]*>", raw or "", re.I):
        add(_attr(m.group(0), "href"), _attr(m.group(0), "title"))
    # pictures a site lists only in its page data and draws by script (godrejproperties.com: one <img> tag, 144 pictures in
    # __NEXT_DATA__, 2026-10-20); named from the file ("1-elevation-view-cmlz..." -> "elevation view")
    for m in EMBEDDED.finditer((raw or "").replace("\\/", "/").replace("\\u002F", "/")):
        url = m.group(0)
        stem = re.sub(r"-[a-z0-9]{20,}.*$", "", urlparse(url).path.rsplit("/", 1)[-1].rsplit(".", 1)[0])
        add(url, " ".join(dict.fromkeys(w for w in re.split(r"[-_]+", stem) if w and not re.fullmatch(r"\d+(x\d+)?", w))))
    return out


def subpages(raw: str, base: str) -> List[str]:
    """Links from the builder's project page to its own gallery or plans pages (lodhagroup.com/.../lodha-camelot-kharadi/plans)."""
    root = urlparse(base)
    stem = root.path.rstrip("/") + "/"
    out = []
    for m in re.finditer(r"<a\b[^>]*>", raw or "", re.I):
        u = urlparse(urljoin(base, _attr(m.group(0), "href")))
        if u.netloc == root.netloc and u.path.startswith(stem) and SUBPAGE.search(u.path[len(stem):]):
            url = f"{u.scheme}://{u.netloc}{u.path}"
            if url not in out:
                out.append(url)
    return out[:MAX_SUBPAGES]


def kind_of(c: dict) -> str:
    where = urlparse(c["url"]).path + " " + c.get("alt", "")
    return "plan" if PLAN.search(where) and not (ROOM.search(where) and not re.search(r"plan|layout", where, re.I)) else "photo"


async def fetch_bytes(url: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[bytes]:
    try:
        async with httpx.AsyncClient(timeout=webfacts.TIMEOUT, follow_redirects=True, transport=transport,
                                     headers={"User-Agent": webfacts.UA, "Accept": "image/*"}) as c:
            async with c.stream("GET", url) as r:
                if r.status_code != 200 or not (r.headers.get("content-type") or "").startswith("image/"):
                    return None
                body = b""
                async for chunk in r.aiter_bytes():
                    body += chunk
                    if len(body) > MAX_IMAGE_BYTES:
                        return None
                return body
    except Exception as e:
        log.info("profile: picture %s not read (%s)", url, type(e).__name__)
        return None


def _dhash(im: Image.Image) -> int:
    g = im.convert("L").resize((9, 8), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for r in range(8):
        for c in range(8):
            bits = (bits << 1) | (px[r * 9 + c] > px[r * 9 + c + 1])
    return bits


def picture(body: bytes, kind: str) -> Optional[tuple]:
    """(RGB image at most KEEP_SIDE, hash) when it is big enough and of a picture's shape, else None."""
    try:
        im = Image.open(io.BytesIO(body))
        im.load()
        im = im.convert("RGB")
    except Exception:
        return None
    w, h = im.size
    if kind == "plan":
        if min(w, h) < MIN_PLAN_SIDE:
            return None
    elif w < MIN_PHOTO_W or h < MIN_PHOTO_H or not 1.0 <= w / h <= 2.6:   # landscape photos and renders; banners strips out
        return None
    im.thumbnail((KEEP_SIDE, KEEP_SIDE))
    return im, _dhash(im)


def _caption(c: dict, kind: str, name: str) -> str:
    alt = c.get("alt") or ""
    if kind == "plan":   # the file's name says which plan more often than the alt text does
        f = urlparse(c["url"]).path.rsplit("/", 1)[-1]
        if re.search(r"master[-_ ]?pa?la?n", f, re.I):
            return f"{name} master plan"
        m = re.search(r"(\d(?:\.5)?)[-_ ]?bhk([-_ ]?with[-_ ]?study)?", f, re.I)
        if m:
            return f"{name} {m.group(1)} BHK{' with study' if m.group(2) else ''} floor plan"
    if len(alt) >= 4 and not re.fullmatch(r"(?i)(image|img|photo|banner|slide)?[\s_-]*\d*", alt) and alt.lower() != name.lower():
        return alt
    return f"{name} floor plan" if kind == "plan" else f"{name}, from the builder's website"


async def pictures(sources: List[dict], raw_of: Dict[str, str], name: str, regno: str, fetch: FetchBytes,
                   media_dir: Path = MEDIA_DIR, page: Optional[webfacts.Fetch] = None) -> tuple:
    """(photos, plans, why): saved pictures from the builder's own project page(s) and its gallery / plans pages."""
    pages_ = [s for s in sources if s["official"] and raw_of.get(s["url"]) and project_page(s["url"], name)]
    if not pages_:
        return [], [], "no builder page for the project"
    if page is not None:   # its own gallery and plans pages first: the main page spends the budget on icons
        subs = []
        for sub in subpages(raw_of[pages_[0]["url"]], pages_[0]["url"]):
            raw = await page(sub)
            if raw:
                raw_of[sub] = raw
                subs.append({**pages_[0], "url": sub})
        pages_ = subs + pages_
    folder = media_dir / re.sub(r"[^A-Za-z0-9]", "", regno).lower()
    tmp = folder.with_name(folder.name + ".new")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    photos, plans, hashes, tried = [], [], [], 0
    for src in pages_:
        for c in candidates(raw_of[src["url"]], src["url"]):
            kind = kind_of(c)
            room = (plans if kind == "plan" else photos)
            if tried >= MAX_CANDIDATES or len(photos) >= MAX_PHOTOS and len(plans) >= MAX_PLANS:
                break
            if len(room) >= (MAX_PLANS if kind == "plan" else MAX_PHOTOS):
                continue
            tried += 1
            body = await fetch(c["url"])
            got = picture(body, kind) if body else None
            if got is None:
                continue
            im, h = got
            if any(bin(h ^ x).count("1") < NEAR for x in hashes):
                continue
            hashes.append(h)
            file = f"{h:016x}.webp"
            im.save(tmp / file, "WEBP", quality=82, method=4)
            room.append({"file": file, "width": im.size[0], "height": im.size[1], "alt": _caption(c, kind, name),
                         "image_url": c["url"], "page_url": src["url"], "site": src["site"]})
    if not photos and not plans:
        shutil.rmtree(tmp, ignore_errors=True)
        return [], [], f"no usable pictures ({tried} tried)"
    shutil.rmtree(folder, ignore_errors=True)   # the new set replaces the old one
    tmp.rename(folder)
    rel = folder.relative_to(Path("uploads")).as_posix() if folder.is_relative_to(Path("uploads")) else folder.as_posix()
    for p in photos + plans:
        p["path"] = f"{rel}/{p.pop('file')}"
    return photos, plans, f"{len(photos)} photos, {len(plans)} floor plans ({tried} tried)"


# ---- the step --------------------------------------------------------------------------------------------------------------

async def gather(store, doc: dict, llm, now: datetime, fetch: Optional[webfacts.Fetch] = None,
                 image: Optional[FetchBytes] = None, search: Optional[websearch.Search] = None,
                 media_dir: Path = MEDIA_DIR) -> tuple:
    """(step, register fields) for areastats.enrich."""
    if doc.get("cluster_primary"):
        return {"ok": True, "at": now, "checked": "read on the group's primary record"}, {}
    if pages.completion_passed(doc):
        return {"ok": True, "at": now, "checked": "completion date passed: profile no longer read"}, {}
    if llm is None:
        return {"ok": False, "at": now, "checked": "no LLM key"}, {}
    name = pages.names(doc)[0]
    results = await webfacts.results_for(store, doc, name, search if search is not None else websearch.provider(), now)
    sources = webfacts.pick_sources(results, name, webfacts.builder_words(doc), limit=webfacts.MAX_TRIES)
    if not sources:
        return {"ok": False, "at": now, "checked": "no web results name the project"}, {}
    fetch = fetch or webfacts.fetch_page
    readings, read, raw_of = [], [], {}
    for src in sources:
        if sum(1 for r in read if r["why"] != "page not read") >= MAX_PAGES:
            break
        raw = await fetch(src["url"])
        if not raw:
            read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": False, "why": "page not read"})
            continue
        text = webfacts.page_text(raw)
        if not websearch.mentions(name, text):
            read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": False,
                         "why": "page does not name the project"})
            continue
        raw_of[src["url"]] = raw
        got, why = await read_highlights(llm, src, name, text)
        readings += got
        read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": bool(got), "why": why})
    highlights = agree(readings)
    regno = doc.get("regno") or doc["_id"]
    try:
        photos, plans, why = await pictures(sources, raw_of, name, regno, image or fetch_bytes, media_dir, page=fetch)
    except Exception as e:
        log.exception("profile: pictures failed for %s", regno)
        photos, plans, why = [], [], f"pictures failed ({type(e).__name__})"
    old = doc.get("profile") or {}
    profile = {"at": now, "name": name, "read": read, "pictures": why,
               # a round that finds nothing keeps the last good ones (a builder's site that is down for a day)
               "highlights": highlights or old.get("highlights") or [],
               "photos": photos or old.get("photos") or [], "plans": plans or old.get("plans") or []}
    checked = f"{len(highlights)} highlights from {sum(1 for r in read if r['ok'])} of {len(read)} sites; {why}"
    return {"ok": bool(highlights or photos or plans), "at": now, "checked": checked}, {"profile": profile}


def lines(profile: Optional[dict]) -> List[str]:
    """The highlights as labelled lines for the page-text model (areastats.enrich.facts_text)."""
    return [f"{TOPICS.get(h['topic'], h['topic'])}: {h['text']} (from {', '.join(s['site'] for s in h['sources'])})"
            for h in (profile or {}).get("highlights") or []]


def public(profile: Optional[dict]) -> Optional[dict]:
    """What a project page shows: highlights with their sources, pictures with where they came from; None when there is nothing."""
    if not profile or not (profile.get("highlights") or profile.get("photos") or profile.get("plans")):
        return None
    at = profile.get("at")

    def pic(p: dict) -> dict:
        return {"url": "/uploads/" + p["path"], "width": p.get("width"), "height": p.get("height"), "alt": p.get("alt") or "",
                "site": p.get("site"), "page_url": p.get("page_url")}
    return {"read_at": at.date().isoformat() if isinstance(at, datetime) else None,
            "highlights": [{"topic": h["topic"], "text": h["text"], "official": h.get("official", False),
                            "sources": [{"site": s["site"], "url": s["url"]} for s in h.get("sources") or []]}
                           for h in profile.get("highlights") or []],
            "photos": [pic(p) for p in profile.get("photos") or [] if p.get("path")],
            "plans": [pic(p) for p in profile.get("plans") or [] if p.get("path")]}
