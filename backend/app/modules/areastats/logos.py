"""Builder logos for the project pages (owner 2026-10-31: "at least the builder's logo, the page looks empty without pictures").
299 of 321 enriched projects had no picture of their own that day, and most are small local builders, so the logo is read once per
BUILDER (its brand, else its MahaRERA promoter: pages.builder_key) and shown on every project of that builder.

Once a day (inside the enrichment loop, like the map pins) for up to PER_DAY builders, those with pages but no picture first:
1. the site: the builder's own domain as the project enrichment already found it (an `official` page in a record's profile or
   web facts), else ONE web search for the builder's name, kept only when the domain is the builder's word (webfacts.official)
   and the result names the builder;
2. the logo on its home page (`candidates`): the Organization logo in its structured data, then <img> tags called a logo, named
   after the builder ("Lodha", "VTP Realty") or inside an element called the logo, earliest first; the touch icon last. A home
   page also shows its projects' own logos ("Tej Navya" on tejraj.in), so the builder's name in the picture wins;
3. the picture is checked (`logo_picture`: a logo's size and shape, a few flat colours, not a photo), trimmed and saved as PNG
   under uploads/builder_logos/<builder key>.png, with `tone` ("light" when it is drawn for a dark header, else "dark"). An SVG
   is drawn to PNG here (resvg, with every outside reference taken out first): an SVG served from our uploads could run code.
Every register record of the builder gets `builder_logo` = {status: "found" | "none", at, site, path, ...}; a "none" is tried again
after RETRY_DAYS, a found logo is read again after REFRESH_DAYS. Pages show the first found one among the builder's records
(pages.builder_logo, in the track record).

Tried on 20 Pune builders' home pages on 2026-10-31 before this went live: see tests/modules/areastats/test_logos.py.
"""
import html
import io
import json
import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import resvg_py
from PIL import Image, ImageChops

from app.modules.newsroom.store import Store

from . import brands, profile, webfacts, websearch
from .hubs import _primaries
from .pages import builder_key, shown_pictures
from .text import promoter_key

log = logging.getLogger(__name__)

LOGO_DIR = Path("uploads") / "builder_logos"
MARK = "builder_logos"        # newsroom_status document: when the pass last ran
EVERY = timedelta(hours=24)
PER_DAY = 60                  # builders looked at a day
SEARCHES = 15                 # web searches a day at most (Serper credits), for builders with no site on record
RETRY_DAYS = 30
REFRESH_DAYS = 90
MAX_CANDIDATES = 6
MIN_WIDE = (80, 20)           # a wide logo: at least this wide and high
MIN_SQUARE = 96               # a square mark (aspect under WIDE): a 49 px favicon is too small to show
WIDE = 1.6
MAX_SIDE = (480, 160)         # kept at most this size: the page shows it about 40 px high
SVG_WIDTH = 480
FLAT = 0.6                    # share of a logo's opaque pixels in its 4 commonest colours (16-colour quantising), when its edge is not plain
LOGO = re.compile(r"logo", re.I)
# pictures that are someone else's logo, or an icon, never the builder's
NOT_OURS = re.compile(r"partner|client|award|rera|bank|certif|whatsapp|payment|app[-_ ]?store|google[-_ ]?play|facebook|instagram|"
                      r"twitter|youtube|linkedin|menu|search|close|icon[-_]?\d|arrow|loader", re.I)

FetchBytes = Callable[[str], Awaitable[Optional[bytes]]]


def _attr(tag: str, name: str) -> str:
    return html.unescape(profile._attr(tag, name))


def _jsonld_logos(raw: str) -> List[str]:
    out: List[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            logo = x.get("logo")
            if isinstance(logo, str):
                out.append(logo)
            elif isinstance(logo, dict) and isinstance(logo.get("url"), str):
                out.append(logo["url"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    for m in re.finditer(r"<script\b[^>]*application/ld\+json[^>]*>(.*?)</script>", raw or "", re.I | re.S):
        try:
            walk(json.loads(m.group(1)))
        except ValueError:
            continue
    return out


def _words(names: Sequence[str]) -> List[str]:
    """The builder's distinctive words ("kolte", "patil", "vtp"): what its own logo's file or alt text says."""
    skip = {"the", "and", "group", "developers", "developer", "properties", "realty", "builders", "constructions", "construction",
            "infra", "estates", "homes", "landmarks", "lifespaces", "projects", "housing", "promoters", "corp", "spaces", "shree", "sri"}
    return list(dict.fromkeys(w for n in names for w in re.findall(r"[a-z0-9]+", (n or "").lower()) if len(w) >= 3 and w not in skip))


def candidates(raw: str, base: str, names: Sequence[str] = ()) -> List[str]:
    """Picture addresses that may be the builder's own logo, most likely first: the structured data's logo, then <img> tags
    (scored: called a logo, named after the builder, inside an element called the logo; earliest first), the touch icon last."""
    raw = raw or ""
    words = _words(names)
    out: List[str] = []

    def add(src: str) -> None:
        src = (src or "").strip()
        if not src or src.startswith("data:"):
            return
        url = urljoin(base, src)
        u = urlparse(url)
        if u.path.endswith("/_next/image") and parse_qs(u.query).get("url"):   # Next.js resizes on request: the file itself
            url = urljoin(url, parse_qs(u.query)["url"][0])
        if url.startswith("http") and url not in out and not NOT_OURS.search(urlparse(url).path):
            out.append(url)

    for u in _jsonld_logos(raw):
        add(u)
    scored = []
    for m in re.finditer(r"<img\b[^>]*>", raw, re.I):
        tag = m.group(0)
        src = (_attr(tag, "data-src") or _attr(tag, "data-lazy-src") or _attr(tag, "src")
               or profile._largest(_attr(tag, "srcset") or _attr(tag, "srcSet")))
        if not src or _attr(tag, "width") == "1" or _attr(tag, "height") == "1":
            continue
        # the file's own name, not its address: every picture on panchshil.com has "panchshil" in its address
        file = unquote(src).split("?")[0].rstrip("/").rsplit("/", 1)[-1] if "/_next/image" not in src else unquote(src).rsplit("/", 1)[-1]
        own = " ".join([file] + [_attr(tag, a) for a in ("alt", "class", "id", "title")]).lower()
        if NOT_OURS.search(own):
            continue
        # the 300 characters before it: <a class="navbar-brand logo"><img src="/wp-content/uploads/2021/03/k.png">
        before = raw[max(0, m.start() - 300):m.start()]
        score = ((2 if LOGO.search(own) else 0) + (1 if re.search(r"(class|id)\s*=\s*[\"'][^\"']*logo", before, re.I) else 0)
                 + (3 if words and any(re.search(r"(?<![a-z0-9])" + re.escape(w), own) for w in words) else 0))
        if score:
            scored.append((-score, m.start(), src))
    for _, _, src in sorted(scored):
        add(src)
    for m in re.finditer(r"<link\b[^>]*>", raw, re.I):
        if "apple-touch-icon" in _attr(m.group(0), "rel").lower():
            add(_attr(m.group(0), "href"))
    return out[:MAX_CANDIDATES]


def is_svg(body: bytes) -> bool:
    head = body[:400].lstrip().lower()
    return head.startswith(b"<svg") or head.startswith(b"<?xml") and b"<svg" in body[:2000].lower()


def svg_png(body: bytes) -> Optional[bytes]:
    """An SVG drawn as PNG, SVG_WIDTH wide. Scripts are never run by resvg; outside references (pictures, fonts, other files
    by href) are taken out first so nothing outside the file is read into the picture."""
    try:
        text = body.decode("utf-8", errors="replace")
        text = re.sub(r"<script\b.*?</script>", "", text, flags=re.I | re.S)
        text = re.sub(r"<(image|use|feImage)\b[^>]*\b(xlink:)?href\s*=\s*[\"'](?!#)[^\"']*[\"'][^>]*/?>", "", text, flags=re.I)
        return bytes(resvg_py.svg_to_bytes(svg_string=text, width=SVG_WIDTH))
    except Exception as e:
        log.info("builder logos: SVG not drawn (%s)", type(e).__name__)
        return None


def _trim(im: Image.Image) -> Image.Image:
    """Without the empty margin: transparent, else the colour of the corner."""
    alpha = im.getchannel("A")
    if alpha.getextrema()[0] < 250:
        box = alpha.point(lambda a: 255 if a > 16 else 0).getbbox()
        return im.crop(box) if box else im
    rgb = im.convert("RGB")
    bg = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
    box = ImageChops.difference(rgb, bg).convert("L").point(lambda v: 255 if v > 24 else 0).getbbox()
    return im.crop(box) if box else im


def plain_border(im: Image.Image) -> bool:
    """The picture's edge is one colour (before trimming): a logo set on a plain background, as a photo never is."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    edge = [rgb.getpixel((x, y)) for x in range(0, w, max(1, w // 40)) for y in (0, h - 1)]
    edge += [rgb.getpixel((x, y)) for y in range(0, h, max(1, h // 20)) for x in (0, w - 1)]
    c = edge[0]
    return sum(1 for p in edge if max(abs(p[i] - c[i]) for i in range(3)) <= 24) >= 0.9 * len(edge)


def flat(im: Image.Image) -> bool:
    """A few flat colours, as a logo is drawn; a photo or a render spreads over many. Transparent pixels are left out."""
    small = im.copy()
    small.thumbnail((64, 64))
    alpha = small.getchannel("A")
    opaque = sum(1 for a in alpha.getdata() if a > 128)
    if not opaque:
        return False
    if opaque < 0.8 * small.size[0] * small.size[1]:
        return True   # a cut-out shape on transparency
    q = small.convert("RGB").quantize(16)
    counts = sorted((c for c, _ in q.getcolors() or []), reverse=True)
    return sum(counts[:4]) / max(1, sum(counts)) >= FLAT


def tone(im: Image.Image) -> str:
    """'light' when the logo is drawn for a dark header (white lettering on transparency: Kohinoor's name, Majestique's): it
    shows on our dark band as it is. 'dark' (shown on white) for everything else, a logo with its own background included."""
    small = im.copy()
    small.thumbnail((96, 96))
    px = [(r, g, b) for r, g, b, a in small.getdata() if a > 128]
    if not px or len(px) == small.size[0] * small.size[1]:
        return "dark"
    white = sum(1 for r, g, b in px if min(r, g, b) > 215)
    return "light" if white >= 0.25 * len(px) else "dark"


def logo_picture(body: bytes) -> Optional[Image.Image]:
    """The logo as RGBA, trimmed and at most MAX_SIDE, when the picture has a logo's size, shape and flat colours; else None."""
    if is_svg(body):
        body = svg_png(body) or b""
    try:
        im = Image.open(io.BytesIO(body))
        im.load()
        im = im.convert("RGBA")
    except Exception:
        return None
    plain = plain_border(im)
    im = _trim(im)
    w, h = im.size
    aspect = w / max(h, 1)
    if not 0.5 <= aspect <= 9:
        return None
    if aspect >= WIDE and (w < MIN_WIDE[0] or h < MIN_WIDE[1]) or aspect < WIDE and min(w, h) < MIN_SQUARE:
        return None
    if not (plain or flat(im)):
        return None
    im.thumbnail(MAX_SIDE)
    return im


async def find_logo(site: str, key: str, names: Sequence[str], page: webfacts.Fetch, fetch: FetchBytes,
                    logo_dir: Path = LOGO_DIR) -> dict:
    """{status, site, page_url, image_url, path, width, height, tone, why} from the builder's home page."""
    # records keep the bare domain ("panchshil.com"), a search gives a whole address
    home = f"https://{websearch.site(site if '//' in site else 'https://' + site)}/"
    raw = await page(home)
    if not raw:
        return {"status": "none", "site": websearch.site(home), "page_url": home, "why": "home page not read"}
    tried = 0
    for url in candidates(raw, home, names):
        tried += 1
        body = await fetch(url)
        im = logo_picture(body) if body else None
        if im is None:
            continue
        logo_dir.mkdir(parents=True, exist_ok=True)
        f = logo_dir / f"{re.sub(r'[^a-z0-9-]', '', key)[:80] or 'builder'}.png"
        im.save(f, "PNG", optimize=True)
        rel = f.relative_to(Path("uploads")).as_posix() if f.is_relative_to(Path("uploads")) else f.as_posix()
        return {"status": "found", "site": websearch.site(home), "page_url": home, "image_url": url, "path": rel,
                "width": im.size[0], "height": im.size[1], "tone": tone(im), "why": f"candidate {tried} of the home page"}
    return {"status": "none", "site": websearch.site(home), "page_url": home,
            "why": f"no candidate looked like a logo ({tried} tried)" if tried else "no logo on the home page"}


def known_site(mine: List[dict]) -> Optional[str]:
    """The builder's own domain as the project enrichment found it on any of its records, the most often seen one."""
    seen: Counter = Counter()
    for d in mine:
        for r in ((d.get("profile") or {}).get("read") or []):
            if r.get("official") and r.get("site"):
                seen[r["site"]] += 1
        for f in ((d.get("web_facts") or {}).get("facts") or []):
            if f.get("official"):
                for s in f.get("sources") or []:
                    if s.get("site"):
                        seen[s["site"]] += 1
    if seen:
        return seen.most_common(1)[0][0]
    # no reading names the site, but a logo already came from one (scripts/builder_logos_by_hand.py): read it there again, or the
    # 90-day refresh would search, may find nothing, and replace a good logo with "none"
    return next((x["site"] for x in (d.get("builder_logo") for d in mine) if isinstance(x, dict) and x.get("status") == "found" and x.get("site")), None)


def names_of(doc: dict) -> List[str]:
    """The builder's names: its brand's, then its MahaRERA promoter's without the legal words."""
    b = brands.of(doc)
    return [n for n in (b.name if b else "", promoter_key(doc.get("promoter"))) if n]


async def search_site(doc: dict, search: websearch.Search) -> Optional[str]:
    """The builder's site from one web search: the first result whose domain is the builder's word and that names the builder."""
    names = names_of(doc)
    if not names:
        return None
    results = await search(f'"{names[0]}" builder Pune official website')
    words = webfacts.builder_words(doc)
    for r in sorted((r for r in results or [] if r.get("link")), key=lambda r: int(r.get("position") or 99)):
        said = f"{r.get('title', '')} {r.get('snippet', '')}"
        if webfacts.official(r["link"], words) and any(websearch.mentions(n, said) for n in names):
            return websearch.site(r["link"])
    return None


def _aware(d: Any) -> Optional[datetime]:
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)) if isinstance(d, datetime) else None


def due(mine: List[dict], now: datetime) -> bool:
    """Not read yet, a found logo older than REFRESH_DAYS, or nothing found RETRY_DAYS ago."""
    last = [x for x in (d.get("builder_logo") for d in mine) if isinstance(x, dict)]
    if any(x.get("status") == "found" and (_aware(x.get("at")) or now) > now - timedelta(days=REFRESH_DAYS) for x in last):
        return False
    return not any((_aware(x.get("at")) or now) > now - timedelta(days=RETRY_DAYS) for x in last)


def pictureless(d: dict) -> bool:
    return not shown_pictures((d.get("profile") or {}).get("photos"), drawn=False)


async def refresh(store: Store, now: datetime, per_day: int = PER_DAY, searches: int = SEARCHES, force: bool = False,
                  page: Optional[webfacts.Fetch] = None, fetch: Optional[FetchBytes] = None,
                  search: Optional[websearch.Search] = None, logo_dir: Path = LOGO_DIR) -> Optional[dict]:
    """Read the logos of up to `per_day` builders, once a day. {found, none, searched} or None when not due."""
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = _aware(mark.get("at"))
    if not force and last and now - last < EVERY:
        return None
    page, fetch = page or webfacts.fetch_page, fetch or profile.fetch_bytes
    search = search if search is not None else websearch.provider()
    every = await store.all_projects()
    by: Dict[str, List[dict]] = {}
    for d in every:
        k = builder_key(d)
        if k:
            by.setdefault(k, []).append(d)
    served = {d["_id"] for d in _primaries(every)}
    # builders with pages that have no pictures first, then those with the most pages
    order = sorted(((k, ds) for k, ds in by.items() if any(d["_id"] in served for d in ds)),
                   key=lambda kv: (-sum(1 for d in kv[1] if d["_id"] in served and pictureless(d)),
                                   -sum(1 for d in kv[1] if d["_id"] in served)))
    out = {"found": 0, "none": 0, "searched": 0}
    for key, mine in order:
        if out["found"] + out["none"] >= per_day:
            break
        if not due(mine, now):
            continue
        first = next(d for d in mine if d["_id"] in served)
        site = known_site(mine)
        if not site:
            if search is None or out["searched"] >= searches:
                continue   # no site on record and no search left today: another day
            out["searched"] += 1
            try:
                site = await search_site(first, search)
            except Exception as e:
                log.info("builder logos: search for %s failed (%s)", key, type(e).__name__)
                continue
        if site:
            try:
                got = await find_logo(site, key, names_of(first), page, fetch, logo_dir)
            except Exception as e:
                log.exception("builder logos: %s failed", key)
                got = {"status": "none", "site": site, "why": f"failed ({type(e).__name__})"}
        else:
            got = {"status": "none", "why": "no site of the builder found"}
        await store.set_projects([d["_id"] for d in mine], builder_logo={**got, "at": now})
        out[got["status"]] += 1
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "done": out}}, upsert=True)
    log.info("builder logos: %s", out)
    return out
