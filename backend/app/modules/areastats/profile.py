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
   impressions. When the builder's site has none (owner 2026-10-22): pictures from other sites' pages about the project (source
   "web", shown as not checked by us), else illustrations drawn by AI (source "ai", shown as such; never floor plans).
Stored on the register record as `profile` = {at, highlights: [{topic, text, official, sources: [{site, url, quote}]}],
photos: [...], plans: [...], read: [{site, url, ok, why}]}; a round that finds nothing keeps the last good highlights or pictures.
`public` is what the pages show.
"""
import base64
import io
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from PIL import Image

from app.core.areas import BY_KEY
from app.modules.newsroom.store import PROJECTS

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
JUNK = re.compile(r"project[-_]?map|compare[-_]?modal|recommendation|"   # a portal's own page furniture (squareyards /assets/images)
                  r"logo|icon|favicon|sprite|avatar|placeholder|loader|whatsapp|qr[-_]?code|award|certificate|team|director|"
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
                   media_dir: Path = MEDIA_DIR, page: Optional[webfacts.Fetch] = None, builder: bool = True) -> tuple:
    """(photos, plans, why): saved pictures from the builder's own project page(s) and its gallery / plans pages, or with
    `builder=False` from other sites' pages about the project (source "web": shown as not checked by us)."""
    pages_ = [s for s in sources if bool(s["official"]) == builder and raw_of.get(s["url"])
              and (s.get("pinned") or project_page(s["url"], name))]
    if not pages_:
        return [], [], "no builder page for the project" if builder else "no other page about the project"
    if page is not None and builder:   # its own gallery and plans pages first: the main page spends the budget on icons
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
            room.append({"file": file, "width": im.size[0], "height": im.size[1],
                         "alt": _caption(c, kind, name) if builder else f"{name}, from {src['site']}",
                         "image_url": c["url"], "page_url": src["url"], "site": src["site"],
                         "source": "builder" if builder else "web"})
    if not photos and not plans:
        shutil.rmtree(tmp, ignore_errors=True)
        return [], [], f"no usable pictures ({tried} tried)"
    shutil.rmtree(folder, ignore_errors=True)   # the new set replaces the old one
    tmp.rename(folder)
    rel = folder.relative_to(Path("uploads")).as_posix() if folder.is_relative_to(Path("uploads")) else folder.as_posix()
    for p in photos + plans:
        p["path"] = f"{rel}/{p.pop('file')}"
    return photos, plans, f"{len(photos)} photos, {len(plans)} floor plans ({tried} tried)"


# ---- the builder's brochure, uploaded by an agent (propertyfacts.brochure) -------------------------------------------------
UPLOADS = Path("uploads")
BROCHURE_PLAN_KINDS = ("floor_plan", "master_plan")


def _safe(s: str) -> str:   # as propertyfacts.brochure names a listing's folder
    return re.sub(r"[^A-Za-z0-9_-]", "", str(s))[:64] or "x"


async def brochure_pictures(db, regno: str, name: str, media_dir: Path = MEDIA_DIR, uploads: Path = UPLOADS) -> tuple:
    """(photos, plans, why) from the latest read brochure whose MahaRERA number is this project's (MahaRERA returned it), or one
    of its group's registrations. Floor and master plans become plans, renders photos (labelled
    artist's impressions); pages the agent dropped are left out. Source "brochure"."""
    q = {"status": "done", "registration.status": "verified",
         "$or": [{"registration.rera_no": regno}, {"registration.group.registrations": regno}]}
    kits = await db.get_collection("brochures").find(q).sort("uploaded_at", -1).limit(3).to_list(3)
    for kit in kits:
        src = uploads / "brochures" / _safe(kit["listing_id"]) / str(kit.get("sha256") or "")
        out = media_dir / (re.sub(r"[^A-Za-z0-9]", "", regno).lower() + "-brochure")
        photos, plans = [], []
        for im in kit.get("images") or []:
            kind = im.get("kind")
            f = src / f"{_safe(im.get('id'))}.jpg"
            if im.get("state") == "dropped" or kind not in BROCHURE_PLAN_KINDS + ("render",) or not f.is_file():
                continue
            room = plans if kind in BROCHURE_PLAN_KINDS else photos
            if len(room) >= (MAX_PLANS if room is plans else MAX_PHOTOS):
                continue
            try:
                pic = Image.open(f)
                pic.load()
                pic = pic.convert("RGB")
            except Exception:
                continue
            pic.thumbnail((KEEP_SIDE, KEEP_SIDE))
            out.mkdir(parents=True, exist_ok=True)
            file = f"{_safe(im.get('id'))}.webp"
            pic.save(out / file, "WEBP", quality=82, method=4)
            configs = " / ".join(im.get("configs") or [])
            alt = (f"{name} {configs} floor plan" if configs and kind == "floor_plan" else f"{name} master plan" if kind == "master_plan"
                   else f"{name} floor plan" if kind == "floor_plan" else f"{name}, artist's impression")
            rel = out.relative_to(Path("uploads")).as_posix() if out.is_relative_to(Path("uploads")) else out.as_posix()
            room.append({"path": f"{rel}/{file}", "width": pic.size[0], "height": pic.size[1],
                         "alt": f"{alt} (page {im.get('page')} of the builder's brochure)", "site": None, "page_url": None,
                         "source": "brochure"})
        if photos or plans:
            return photos, plans, f"brochure: {len(photos)} renders, {len(plans)} plans"
    return [], [], "no brochure" if not kits else "brochure has no plans or renders"


# ---- illustrations: when no site has pictures of the project ---------------------------------------------------------------
# Owner 2026-10-22: "if we don't find images, add illustrative images". Drawn by Cloudflare's FLUX (free tier, ~2 s a picture),
# never called the project: source "ai", and the page says each one is an illustration made by AI. Never drawn as floor plans
# (a made-up layout of a real registered project would mislead); plans are asked for through the page's form instead.
CF_IMAGE_URL = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/black-forest-labs/flux-1-schnell"
NO_TEXT = "Photorealistic architectural visualisation, no text, no letters, no logos, no watermarks, no people's faces in close-up."
Draw = Callable[[str], Awaitable[Optional[bytes]]]


async def cf_draw(prompt: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[bytes]:
    token, account = os.environ.get("CLOUDFLARE_API_TOKEN"), os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        return None
    try:
        async with httpx.AsyncClient(timeout=120, transport=transport) as c:
            r = await c.post(CF_IMAGE_URL.format(account=account), headers={"Authorization": f"Bearer {token}"},
                             json={"prompt": f"{prompt} {NO_TEXT}", "steps": 6})
        if r.status_code != 200:
            log.info("profile: illustration not drawn (HTTP %s)", r.status_code)
            return None
        return base64.b64decode(((r.json() or {}).get("result") or {}).get("image") or "") or None
    except Exception as e:
        log.info("profile: illustration not drawn (%s)", type(e).__name__)
        return None


def place_of(doc: dict) -> str:
    area = BY_KEY.get(doc.get("locality") or "")
    return area.name if area else doc.get("place_locality") or doc.get("taluka") or "Pune"


def scenes(doc: dict, place: str) -> List[tuple]:
    """(caption, prompt) for each illustration, from MahaRERA's facts (towers, floors, homes or offices)."""
    t = doc.get("building_totals") or {}
    homes = bool(t.get("units_residential")) or not t.get("units_other")
    floors = t.get("max_floors")
    tall = f"{floors}-storey " if floors and floors > 2 else ""
    many = f"{t['towers']} " if (t.get("towers") or 0) > 1 else "a "
    if not homes:
        return [("Illustration: an office building of this kind",
                 f"Exterior of {many}modern {tall}glass office building in {place}, Pune, India, daytime, street level view."),
                ("Illustration: an office floor of this kind", "Bright modern open-plan office interior in Pune, India, daylight.")]
    return [("Illustration: towers of this kind", f"Exterior of {many}modern {tall}residential apartment tower"
             f"{'s' if (t.get('towers') or 0) > 1 else ''} in {place}, Pune, India, landscaped entrance, golden hour."),
            ("Illustration: a living room of this kind", "Living room of a new Indian apartment, vitrified tile floor, balcony door, "
             "daylight, simple modern furniture."),
            ("Illustration: amenities of this kind", "Rooftop swimming pool and garden deck of a residential tower in Pune, India, "
             "evening, city view.")]


async def illustrations(doc: dict, name: str, regno: str, place: str, draw: Optional[Draw] = None,
                        media_dir: Path = MEDIA_DIR) -> List[dict]:
    """Drawn pictures saved under uploads/project_media/<regno>-ai, [] when none could be drawn."""
    folder = media_dir / (re.sub(r"[^A-Za-z0-9]", "", regno).lower() + "-ai")
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for caption, prompt in scenes(doc, place):
        body = await (draw or cf_draw)(prompt)
        got = picture(body, "photo") if body else None
        if got is None:
            continue
        im, h = got
        file = f"{h:016x}.webp"
        im.save(folder / file, "WEBP", quality=80, method=4)
        rel = folder.relative_to(Path("uploads")).as_posix() if folder.is_relative_to(Path("uploads")) else folder.as_posix()
        out.append({"path": f"{rel}/{file}", "width": im.size[0], "height": im.size[1], "alt": f"{caption} (made by AI, not {name})",
                    "site": None, "page_url": None, "source": "ai"})
    return out


# ---- the step --------------------------------------------------------------------------------------------------------------

async def gather(store, doc: dict, llm, now: datetime, fetch: Optional[webfacts.Fetch] = None,
                 image: Optional[FetchBytes] = None, search: Optional[websearch.Search] = None,
                 media_dir: Path = MEDIA_DIR, draw: Optional[Draw] = None) -> tuple:
    """(step, register fields) for areastats.enrich."""
    if doc.get("cluster_primary"):
        return {"ok": True, "at": now, "checked": "read on the group's primary record"}, {}
    if pages.completion_passed(doc):
        return {"ok": True, "at": now, "checked": "completion date passed: profile no longer read"}, {}
    if llm is None:
        return {"ok": False, "at": now, "checked": "no LLM key"}, {}
    name = pages.names(doc)[0]
    results = await webfacts.results_for(store, doc, name, search if search is not None else websearch.provider(), now)
    sources = webfacts.sources_for(doc, results, name, limit=webfacts.MAX_TRIES)
    regno = doc.get("regno") or doc["_id"]
    old = doc.get("profile") or {}
    try:   # an agent's uploaded brochure of this project (or of its group): the builder's own plans and renders
        b_photos, b_plans, b_why = await brochure_pictures(store.db, regno, name, media_dir)
    except Exception as e:
        log.exception("profile: brochure pictures failed for %s", regno)
        b_photos, b_plans, b_why = [], [], f"brochure failed ({type(e).__name__})"
    readings, read, raw_of = [], [], {}
    photos, plans, why = [], [], "no web results name the project"
    if sources:
        fetch = fetch or webfacts.fetch_page
        for src in sources:
            if sum(1 for r in read if r["why"] != "page not read") >= MAX_PAGES:
                break
            raw = await fetch(src["url"])
            if not raw:
                read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": False, "why": "page not read"})
                continue
            text = webfacts.page_text(raw)
            ok, not_ok = webfacts.about_project(doc, name, text, src)
            if not ok:
                read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": False, "why": not_ok})
                continue
            raw_of[src["url"]] = raw
            got, why_ = await read_highlights(llm, src, name, text)
            readings += got
            read.append({"site": src["site"], "url": src["url"], "official": src["official"], "ok": bool(got), "why": why_})
        try:
            photos, plans, why = await pictures(sources, raw_of, name, regno, image or fetch_bytes, media_dir, page=fetch)
        except Exception as e:
            log.exception("profile: pictures failed for %s", regno)
            photos, plans, why = [], [], f"pictures failed ({type(e).__name__})"
    highlights = agree(readings)
    shared = await others_pictures(store.db, doc)
    plans = [x for x in plans if not generic(x, shared)]
    photos = [x for x in photos if not generic(x, shared)]
    # the builder's site, then the brochure (its plans first: they are the builder's own), then other sites, then illustrations
    plans = (b_plans + plans)[:MAX_PLANS]
    photos = photos or b_photos
    why = f"{why}; {b_why}"
    if sources and not photos and not plans:   # owner 2026-10-22: "or best we can find, unverified, from the web"
        try:
            photos, plans, also = await pictures(sources, raw_of, name, regno, image or fetch_bytes, media_dir, builder=False)
            n = len(photos) + len(plans)
            photos, plans = [x for x in photos if not generic(x, shared)], [x for x in plans if not generic(x, shared)]
            why = f"{why}; web: {also}" + (f", {n - len(photos) - len(plans)} on other projects too (dropped)" if n > len(photos) + len(plans) else "")
        except Exception as e:
            log.exception("profile: web pictures failed for %s", regno)
            why = f"{why}; web pictures failed ({type(e).__name__})"
    if not photos and not old.get("photos"):
        try:   # nothing real ever found: illustrations, drawn once
            photos = await illustrations(doc, name, regno, place_of(doc), draw, media_dir)
            why += f"; {len(photos)} illustrations drawn"
        except Exception as e:
            log.exception("profile: illustrations failed for %s", regno)
            why += f"; illustrations failed ({type(e).__name__})"
    profile = {"at": now, "name": name, "read": read, "pictures": why,
               # a round that finds nothing keeps the last good ones (a builder's site that is down for a day)
               "highlights": highlights or old.get("highlights") or [],
               "photos": photos or kept(old.get("photos")), "plans": plans or kept(old.get("plans"))}
    checked = f"{len(highlights)} highlights from {sum(1 for r in read if r['ok'])} of {len(read)} sites; {why}"
    return {"ok": bool(highlights or photos or plans), "at": now, "checked": checked}, {"profile": profile}


def _hash_of(pic: dict) -> Optional[int]:
    """The picture's dHash: its saved file is named by it (pictures, brochure and AI files are not)."""
    m = re.fullmatch(r"([0-9a-f]{16})\.webp", str(pic.get("path") or pic.get("file") or "").rsplit("/", 1)[-1])
    return int(m.group(1), 16) if m else None


async def others_pictures(db, doc: dict) -> List[int]:
    """The hashes of the pictures other projects show (not this project's tower group)."""
    me = {doc.get("regno") or doc["_id"], doc.get("cluster_primary") or doc.get("regno") or doc["_id"]}
    out = []
    async for d in db.get_collection(PROJECTS).find(
            {"$or": [{"profile.photos.0": {"$exists": True}}, {"profile.plans.0": {"$exists": True}}]},
            {"regno": 1, "cluster_primary": 1, "profile.photos.path": 1, "profile.plans.path": 1}):
        if {d.get("regno"), d.get("cluster_primary")} & me:
            continue
        out += [h for x in (d.get("profile") or {}).get("photos", []) + (d.get("profile") or {}).get("plans", [])
                if (h := _hash_of(x)) is not None]
    return out


def generic(pic: dict, shared: List[int]) -> bool:
    """A web picture another project shows too is a portal's or a builder's stock picture, not this project (2026-10-22:
    magicbricks' "created by AI" banners on ten projects, Ekaanta's three photos among them)."""
    h = _hash_of(pic)
    return pic.get("source") == "web" and h is not None and any(bin(h ^ x).count("1") < NEAR for x in shared)


def kept(pics: Optional[List[dict]]) -> List[dict]:
    """Last round's pictures kept when this round found none, except the brochure's: those are read from the kit every round,
    so a page the agent dropped leaves the project page."""
    return [p for p in pics or [] if p.get("source") != "brochure"]


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
                "site": p.get("site"), "page_url": p.get("page_url"), "source": p.get("source") or "builder"}
    return {"read_at": at.date().isoformat() if isinstance(at, datetime) else None,
            "highlights": [{"topic": h["topic"], "text": h["text"], "official": h.get("official", False),
                            "sources": [{"site": s["site"], "url": s["url"]} for s in h.get("sources") or []]}
                           for h in profile.get("highlights") or []],
            "photos": [pic(p) for p in profile.get("photos") or [] if p.get("path")],
            "plans": [pic(p) for p in profile.get("plans") or [] if p.get("path")]}
