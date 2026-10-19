"""The campaign's two posts (owner, 2026-10-19: "why that many posts? We need 2: one with multiple pictures, one with full
details"). The reels carry the creative room's ideas; the posts are the property itself.

  gallery   a carousel of the property's own pictures (photos, video stills, the builder's renders marked "Artist's
            impression"): a cover slide with the name, the place, the home types, the "from" price and the payment plan, then
            three of them combined on one slide (collage), the rest one a slide (up to GALLERY_MAX pictures). Pictures are
            cropped where their detail is, phone photos lifted a little, and maps, QR codes, clipart and screenshots left out
            (photo_like)
  details   one card with what a buyer asks first: every home type with its carpet area and price (listing.configurations),
            the payment plan, possession and the MahaRERA number with its QR code; its caption lists the same, the project's
            highlights and the distances

Every word is code-written from the listing and the checked facts (no model writes these two), so nothing on them can be a
number the facts do not hold. English cards; the caption follows the run's language only for its fixed lines (English for now).

    posts = make(listing, ctx, pictures, out_dir, contact=..., link_line=..., brand_name=..., logo=...)
    # [{"angle", "layout", "format", "images": [local paths], "caption", "used_llm": False, "prompts": []}]
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from app.core import brand
from app.modules.marketing.images import LOGO_PATH, load_font
from app.modules.marketing.maharera import badge as maharera_badge

from . import homes
from .campaign import ARTISTS_IMPRESSION, Ctx, _km, _near, buyer_place

log = logging.getLogger(__name__)

W, H = 1080, 1350
PAD = 64
GALLERY_MAX = 8          # pictures, the cover's included (Instagram takes 10 slides)
COLLAGE_FROM = 5         # pictures from which three of them share a slide
NAVY = (16, 35, 64)
GOLD = (240, 177, 59)
WHITE, SOFT, LINE = (255, 255, 255), (206, 214, 228), (58, 78, 110)
ASK = "Comment INFO and we will send you the price sheet and floor plans."
PRICE_NOTE = "Prices as the builder gives them; ask us for today's price sheet, taxes and charges before you book."


# ---- the words -------------------------------------------------------------------------------------------------------------
def _hashtags(c: Ctx) -> str:
    place = "".join(w.capitalize() for w in (c.locality or "Pune").split() if w.isalnum())
    return " ".join(dict.fromkeys(t for t in (f"#{place}" if place else "", "#PuneProperty", "#PuneHomes",
                                                 "#MahaRERA" if c.v.get("rera_no") else "") if t))


def headline(listing: dict, c: Ctx) -> str:
    """'Godrej Ivara, Upper Kharadi: 2, 3 & 4 BHK from ₹1.20 Cr onwards' (one home: '2 BHK at ...: ₹1.29 Cr')."""
    table = homes.rows(listing)
    where = c.where or c.locality or listing.get("locality") or "Pune"
    low = homes.from_price(listing)
    if homes.several(listing):
        what = homes.bhk_range(table) or ("Plots" if listing.get("property_type") == "plot" else "Homes")
        return f"{where}: {what}" + (f" from {homes.short_price(low)} onwards" if low else "")
    what = table[0]["label"] if table else ("Plot" if listing.get("property_type") == "plot" else "Home")
    return f"{what} at {where}" + (f": {homes.short_price(low)}" if low else "")


def _highlights(listing: dict, table: List[dict], limit: int = 5) -> List[str]:
    from .room import STALE
    out = []
    for h in (listing.get("about") or {}).get("highlights") or []:
        h = " ".join(str(h).split()).rstrip(".")
        if not h or STALE.search(h) or (table and "BHK" in h.upper()):   # the price sheet says the home types already
            continue
        out.append(h)
    return out[:limit]


def _nearby(c: Ctx, n: int = 4) -> List[str]:
    out = []
    for k, p in _near(c):
        name = buyer_place(c, k, p)
        if name:
            out.append(f"{name} {_km(p['km'])}")
        if len(out) >= n:
            break
    return out


def _possession(listing: dict, c: Ctx) -> str:
    own = homes.possession(listing)
    if own and own[-4:].isdigit():
        return f"{own} (the builder's date)"
    return own or ("Under construction" if c.v.get("possession_now") else "")


def details_caption(listing: dict, c: Ctx, contact: Sequence[str], link_line: str) -> str:
    table = homes.rows(listing)
    parts = [headline(listing, c)]
    if table and (len(table) > 1 or table[0].get("carpet_sqft")):
        lines = ["🏠 Homes and prices"]
        for r in table:
            lines.append("• " + " · ".join(x for x in (r["label"], f"{int(r['carpet_sqft']):,} sq ft carpet" if r.get("carpet_sqft") else "",
                                                       homes.short_price(r.get("price_inr"))) if x))
        parts.append("\n".join(lines))
    facts = []
    if not table and listing.get("carpet_sqft"):   # a plot (or a home without a BHK): its size
        facts.append(f"📐 Size: {int(listing['carpet_sqft']):,} sq ft")
    if homes.payment_plan(listing):
        facts.append(f"💰 Payment plan: {homes.payment_plan(listing)}")
    if _possession(listing, c):
        facts.append(f"🗓️ Possession: {_possession(listing, c)}")
    facts += [f"✔️ {h}" for h in _highlights(listing, table)]
    near = _nearby(c)
    if near:
        facts.append("📍 " + " · ".join(near) + " (straight line)")
    if c.v.get("rera_no"):
        facts.append(f"✅ MahaRERA: {c.v['rera_no']}")
    if facts:
        parts.append("\n".join(facts))
    if any(r.get("price_inr") for r in table):
        parts.append(PRICE_NOTE)
    parts += [ASK, "\n".join(contact), link_line, _hashtags(c)]
    return "\n\n".join(p for p in parts if p)


def gallery_caption(listing: dict, c: Ctx, contact: Sequence[str], link_line: str, n: int, renders: int) -> str:
    table = homes.rows(listing)
    where = c.where or c.locality or "this property"
    low = homes.from_price(listing)
    what = homes.bhk_range(table) if homes.several(listing) else (table[0]["label"] if table else "")
    line = " · ".join(x for x in ((f"{what} homes" if what else "Plots" if listing.get("property_type") == "plot" else "Homes") + (f" from {homes.short_price(low)} onwards" if low and homes.several(listing)
                                                                         else f" at {homes.short_price(low)}" if low else ""),
                                   f"{homes.payment_plan(listing)} payment plan" if homes.payment_plan(listing) else "") if x)
    looks = [f"✨ {h}" for h in _highlights(listing, table, 3)]
    swipe = f"Swipe through {n - 1} pictures" + (f" (the builder's renders are marked \"{ARTISTS_IMPRESSION}\")" if renders else "") + "."
    parts = [f"A look around {where}.", line, "\n".join(looks), swipe, ASK, "\n".join(contact), link_line, _hashtags(c)]
    return "\n\n".join(p for p in parts if p)


# ---- drawing ---------------------------------------------------------------------------------------------------------------
# ---- the pictures: cropped where the detail is, lifted a little, combined on a grid (deterministic, no model) -------------
def _window(im: Image.Image, aspect: float) -> Tuple[int, int, int, int]:
    """The crop box of `aspect` (w/h) holding the most detail: edge energy summed along the axis that is cut, on a 256 px copy,
    each position weighed a little towards the middle (a building, a pool or a room's centre, not a strip of sky or floor)."""
    w, h = im.size
    if abs(w / h - aspect) < 0.01:
        return (0, 0, w, h)
    small = im.convert("L")
    small.thumbnail((256, 256))
    sw, sh = small.size
    edges = small.filter(ImageFilter.FIND_EDGES)
    px = edges.load()
    if w / h > aspect:    # too wide: slide across
        cw = int(round(h * aspect))
        cols = [sum(px[x, y] for y in range(sh)) for x in range(sw)]
        win = max(1, int(round(sw * cw / w)))
        span, axis = cols, sw
    else:                 # too tall: slide down
        ch = int(round(w / aspect))
        rows = [sum(px[x, y] for x in range(sw)) for y in range(sh)]
        win = max(1, int(round(sh * ch / h)))
        span, axis = rows, sh
    best, at = -1.0, 0
    run = sum(span[:win])
    for i in range(0, axis - win + 1):
        if i:
            run += span[i + win - 1] - span[i - 1]
        mid = (i + win / 2) / axis
        score = run * (1.0 - 0.35 * abs(mid - 0.5))
        if score > best:
            best, at = score, i
    if w / h > aspect:
        x = int(at * w / sw)
        return (min(x, w - cw), 0, min(x, w - cw) + cw, h)
    y = int(at * h / sh)
    return (0, min(y, h - ch), w, min(y, h - ch) + ch)


def _enrich(im: Image.Image) -> Image.Image:
    """A phone photo lifted as an editor would: levels stretched (1% clipped), colour and contrast a touch richer, a light
    sharpen after the resize. A builder's render is left as the builder made it."""
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Color(im).enhance(1.08)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))


def _cover(path: str, size: Tuple[int, int], render: bool = False) -> Image.Image:
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im = im.crop(_window(im, size[0] / size[1])).resize(size, Image.LANCZOS)
    return im if render else _enrich(im)


MIN_SIDE = 380          # px: a smaller picture (a QR code, a thumbnail) is blurred mush at slide size
MIN_COLOURS = 4000      # distinct colours on a 96 px copy: photos and renders measured 5,700-8,800; clipart, maps and
                        # screenshots of a price sheet 1,300-3,100 (Godrej Ivara's uploads, 2026-10-19)
PAPER = 0.5             # share of near-white pixels above which it is a page of text, not a place


def photo_like(path: str) -> bool:
    """A picture a gallery slide may show: readable, big enough, and a photo or render rather than an illustration, a map,
    a QR code or a screenshot of text (all of which agents upload among the photos)."""
    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            if min(im.size) < MIN_SIDE:
                return False
            t = im.resize((96, 96))
    except Exception:
        return False
    if len(set(t.getdata())) < MIN_COLOURS:
        return False
    grey = t.convert("L").histogram()
    return sum(grey[235:]) / (96 * 96) <= PAPER


GAP = 10


def _landscape(path: str) -> bool:
    with Image.open(path) as im:
        w, h = ImageOps.exif_transpose(im).size
    return w >= h


def collage(pics: Sequence[Tuple[str, bool]], size: Tuple[int, int] = (W, H)) -> Image.Image:
    """Three or four pictures on one slide, the first the biggest: wide pictures stack (the first across the top, the rest side
    by side under it); tall ones stand (the first down the left, the rest stacked on the right). Navy gaps."""
    w, h = size
    img = Image.new("RGB", size, NAVY)
    pics = list(pics)[:4]
    rest = pics[1:]
    if sum(_landscape(p) for p, _ in pics) * 2 >= len(pics):
        top = int(h * 0.56)
        boxes = [(0, 0, w, top)]
        cw = (w - GAP * (len(rest) - 1)) // len(rest)
        boxes += [(i * (cw + GAP), top + GAP, i * (cw + GAP) + cw, h) for i in range(len(rest))]
    else:
        left = int(w * 0.6)
        boxes = [(0, 0, left, h)]
        rh = (h - GAP * (len(rest) - 1)) // len(rest)
        boxes += [(left + GAP, i * (rh + GAP), w, i * (rh + GAP) + rh) for i in range(len(rest))]
    for (p, render), (x0, y0, x1, y1) in zip(pics, boxes):
        img.paste(_cover(p, (x1 - x0, y1 - y0), render), (x0, y0))
    return img


def _scrim(img: Image.Image, start: float, top: bool = False, strength: float = 0.92) -> Image.Image:
    """The picture darkened towards its bottom (or top) from `start` (share of the height), so white text reads."""
    w, h = img.size
    mask = Image.new("L", (1, h), 0)
    for y in range(h):
        t = (1 - y / h) if top else y / h
        a = 0 if t < start else (t - start) / (1 - start)
        mask.putpixel((0, y), int(255 * strength * min(1.0, a * 1.35)))
    shade = Image.new("RGB", (w, h), NAVY)
    return Image.composite(shade, img, mask.resize((w, h)))


def _text(d: ImageDraw.ImageDraw, xy, text: str, font, fill, shadow: bool = True) -> None:
    if shadow:
        d.text((xy[0] + 2, xy[1] + 3), text, font=font, fill=(0, 0, 0))
    d.text(xy, text, font=font, fill=fill)


def _wrap(d: ImageDraw.ImageDraw, text: str, font, width: int, lines: int) -> List[str]:
    out, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if d.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    return out[:lines]


def _fit_font(d: ImageDraw.ImageDraw, text: str, weight: str, start: int, width: int, lines: int = 1, least: int = 30):
    """The biggest size from `start` down at which `text` fits `width` in `lines` lines."""
    size = start
    while size > least:
        f = load_font(size, weight)
        if len(_wrap(d, text, f, width, 99)) <= lines:
            return f
        size -= 4
    return load_font(least, weight)


def _pill(img: Image.Image, x: int, y: int, text: str, font, bg, ink, pad=(26, 12)) -> int:
    """A rounded chip at (x, y); returns its right edge."""
    d = ImageDraw.Draw(img)
    tw = int(d.textlength(text, font=font))
    asc, desc = font.getmetrics()
    h = asc + desc + pad[1] * 2
    d.rounded_rectangle([x, y, x + tw + pad[0] * 2, y + h], radius=h // 2, fill=bg)
    d.text((x + pad[0], y + pad[1]), text, font=font, fill=ink)
    return x + tw + pad[0] * 2


def _footer(img: Image.Image, name: str, logo: str = "") -> None:
    """The brand's mark and name at the bottom left (an agent's logo when the cards are theirs)."""
    d = ImageDraw.Draw(img)
    f = load_font(30, "semibold")
    y = H - 84
    x = PAD
    src = logo if logo and Path(logo).is_file() else (str(LOGO_PATH) if Path(LOGO_PATH).is_file() else "")
    if src:
        try:
            with Image.open(src) as m:
                m = ImageOps.contain(m.convert("RGBA"), (52, 52))
                img.paste(m, (x, y - 4), m)
                x += 64
        except Exception:
            log.info("listing posts: logo %s not drawn", src, exc_info=True)
    _text(d, (x, y + 6), name, f, WHITE)


def _badge(img: Image.Image, c: Ctx, x_right: int, y: int) -> None:
    reg = c.registration
    if reg is None:
        return
    b = maharera_badge(reg, qr_px=118, text_px=22)
    img.paste(b.img, (x_right - b.img.size[0], y), b.img)


def gallery_cover(picture: str, render: bool, listing: dict, c: Ctx, brand_name: str, logo: str, dest: Path) -> str:
    img = _scrim(_cover(picture, (W, H), render), 0.34, strength=0.97)   # a builder's creative can carry its own small print
    d = ImageDraw.Draw(img)
    table = homes.rows(listing)
    width = W - 2 * PAD
    y = H - 140
    pills = []
    low = homes.from_price(listing)
    what = homes.bhk_range(table) if homes.several(listing) else (table[0]["label"] if table else "")
    if what or low:
        pills.append((" · ".join(x for x in (what, (("from " if homes.several(listing) else "") + homes.short_price(low)) if low else "") if x),
                      GOLD, NAVY))
    if homes.payment_plan(listing):
        pills.append((f"{homes.payment_plan(listing)} payment plan", WHITE, NAVY))
    pf = load_font(40, "bold")
    ph = sum(pf.getmetrics()) + 24
    for text, bg, ink in reversed(pills):
        y -= ph + 16
        _pill(img, PAD, y, text, pf, bg, ink)
    place = c.locality or listing.get("locality") or ""
    if place:
        lf = load_font(46, "semibold")
        y -= 70
        _text(d, (PAD, y), place, lf, GOLD)
    name = c.project or listing.get("project_name") or headline(listing, c)
    nf = _fit_font(d, name, "bold", 104, width, 2, 56)
    lines = _wrap(d, name, nf, width, 2)
    step = int(nf.size * 1.12)
    y -= step * len(lines) + 8
    for i, ln in enumerate(lines):
        _text(d, (PAD, y + i * step), ln, nf, WHITE)
    if render:
        _pill(img, PAD, PAD, ARTISTS_IMPRESSION, load_font(24, "medium"), (0, 0, 0), WHITE, pad=(18, 8))
    _badge(img, c, W - PAD // 2, PAD // 2)
    _footer(img, brand_name, logo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "JPEG", quality=90)
    return str(dest)


def gallery_slide(picture: Any, render: bool, i: int, n: int, brand_name: str, logo: str, dest: Path) -> str:
    """One picture full bleed, or a collage when `picture` is a list of (path, render)."""
    base = collage(picture) if isinstance(picture, list) else _cover(picture, (W, H), render)
    img = _scrim(base, 0.78, strength=0.85)
    _pill(img, W - PAD - 110, PAD, f"{i}/{n}", load_font(28, "semibold"), (0, 0, 0), WHITE, pad=(22, 8))
    if render:
        _pill(img, PAD, PAD, ARTISTS_IMPRESSION, load_font(24, "medium"), (0, 0, 0), WHITE, pad=(18, 8))
    _footer(img, brand_name, logo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "JPEG", quality=90)
    return str(dest)


def details_card(listing: dict, c: Ctx, picture: Optional[str], brand_name: str, logo: str, dest: Path) -> str:
    """The price sheet: the picture across the top with the name and place, then a row a home type (BHK, carpet, price), the
    payment plan and possession chips, the MahaRERA badge and the footer."""
    img = Image.new("RGB", (W, H), NAVY)
    band = 430
    if picture:
        top = _scrim(_cover(picture, (W, band)), 0.25, strength=0.95)
        img.paste(top, (0, 0))
    d = ImageDraw.Draw(img)
    width = W - 2 * PAD
    name = c.project or listing.get("project_name") or "This property"
    nf = _fit_font(d, name, "bold", 92, width, 1, 52)
    place = ", ".join(x for x in (c.locality or listing.get("locality") or "", "Pune") if x)
    _text(d, (PAD, band - 172), name, nf, WHITE)
    _text(d, (PAD, band - 172 + int(nf.size * 1.15)), place, load_font(42, "semibold"), GOLD)
    table = homes.rows(listing)
    y = band + 36
    cols = (PAD, PAD + 330, W - PAD)   # home | carpet | price (right-aligned)
    n = max(1, len(table))
    row_h = max(58, min(82, (H - band - 360) // (n + 1)))
    size = 40 if row_h >= 70 else 34
    hf, rf, pf = load_font(28, "semibold"), load_font(size, "medium"), load_font(size, "bold")
    if table:
        d.text((cols[0], y), "HOME", font=hf, fill=SOFT)
        d.text((cols[1], y), "CARPET AREA", font=hf, fill=SOFT)
        d.text((cols[2] - d.textlength("PRICE", font=hf), y), "PRICE", font=hf, fill=SOFT)
        y += 48
        for r in table:
            d.line([PAD, y, W - PAD, y], fill=LINE, width=2)
            ty = y + (row_h - sum(rf.getmetrics())) // 2
            d.text((cols[0], ty), r["label"], font=rf, fill=WHITE)
            if r.get("carpet_sqft"):
                d.text((cols[1], ty), f"{int(r['carpet_sqft']):,} sq ft", font=rf, fill=WHITE)
            price = homes.short_price(r.get("price_inr")) or "Ask us"
            d.text((cols[2] - d.textlength(price, font=pf), ty), price, font=pf, fill=GOLD)
            y += row_h
        d.line([PAD, y, W - PAD, y], fill=LINE, width=2)
    y += 34
    chip = load_font(34, "bold")
    x = PAD
    for text, bg, ink in ((f"{homes.payment_plan(listing)} payment plan" if homes.payment_plan(listing) else "", GOLD, NAVY),
                          (f"Possession {homes.possession(listing)}" if homes.possession(listing) else "", WHITE, NAVY)):
        if not text:
            continue
        tw = d.textlength(text, font=chip) + 52
        if x > PAD and x + tw > W - PAD:   # no room beside the first chip: the next line
            x, y = PAD, y + sum(chip.getmetrics()) + 40
        x = _pill(img, x, y, text, chip, bg, ink) + 16
    if any(r.get("price_inr") for r in table):   # under the chips, clear of the badge
        d.text((PAD, y + sum(chip.getmetrics()) + 44), "Prices as the builder gives them. Taxes and charges extra.",
               font=load_font(24, "regular"), fill=SOFT)
    _badge(img, c, W - PAD // 2, H - 158)   # beside the footer, clear of the price note
    _footer(img, brand_name, logo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "JPEG", quality=92)
    return str(dest)


# ---- another language ------------------------------------------------------------------------------------------------------
LANGS = {"mr": "Marathi", "hi": "Hindi"}
TRANSLATE = ("Translate this Instagram caption about a home for sale into {lang}, in Devanagari, as Pune buyers write it. Keep "
             "every number, ₹ amount, 'BHK', 'sq ft', the MahaRERA number, the emoji and the line breaks exactly as they are; keep "
             "project, builder and place names and the word INFO as written. Add nothing. Reply JSON only: {{\"text\": \"...\"}}")


async def localize(caption: str, lang: str, llm: Any) -> str:
    """A Marathi or Hindi run's caption: the words down to the ask translated (the contact block, link line and hashtags after
    it are code-written per language or left as they are); kept in English when the model is missing, drops INFO or changes
    a number."""
    if lang not in LANGS or llm is None or ASK not in caption:
        return caption
    from app.modules.creative.translate import _same_numbers
    body, tail = caption.split(ASK, 1)
    body += ASK
    for _ in range(2):
        try:
            out = await llm.json(TRANSLATE.format(lang=LANGS[lang]), body.strip())
        except Exception:
            log.info("listing posts: translation failed", exc_info=True)
            continue
        text = str((out or {}).get("text") or "").strip()
        if text and "INFO" in text and _same_numbers(text, body):
            return text + tail
    return caption


# ---- the two posts ---------------------------------------------------------------------------------------------------------
def make(listing: dict, c: Ctx, pictures: Sequence[Tuple[str, bool]], out_dir: Path, contact: Sequence[str] = (),
         link_line: str = "", brand_name: str = "", logo: str = "") -> List[Dict[str, Any]]:
    """The gallery (when there are 2 pictures or more) and the details post. `pictures`: (path, is a builder's render), best
    first. A post that cannot be drawn is left out (logged); the other still comes."""
    name = brand_name or brand.NAME
    pics = [(p, r) for p, r in pictures if p and Path(p).is_file() and photo_like(p)][:GALLERY_MAX]
    out: List[Dict[str, Any]] = []
    if len(pics) >= 2:
        try:
            # the cover; with COLLAGE_FROM pictures or more the next three share one slide (each picture shown once); then
            # the rest one a slide
            slides: List[Tuple[Any, bool]] = [(p, r) for p, r in pics[1:]]
            if len(pics) >= COLLAGE_FROM:
                slides = [(list(pics[1:4]), any(r for _, r in pics[1:4]))] + slides[3:]
            n = len(slides) + 1
            images = [gallery_cover(pics[0][0], pics[0][1], listing, c, name, logo, out_dir / "gallery" / "slide1.jpg")]
            images += [gallery_slide(p, r, i + 2, n, name, logo, out_dir / "gallery" / f"slide{i + 2}.jpg")
                       for i, (p, r) in enumerate(slides)]
            out.append({"angle": "gallery", "layout": "gallery", "format": "carousel", "images": images,
                        "caption": gallery_caption(listing, c, contact, link_line, len(pics) + 1, sum(1 for _, r in pics if r)),
                        "used_llm": False, "prompts": []})
        except Exception:
            log.warning("listing posts: gallery not drawn", exc_info=True)
    try:
        # the band is wide: the first wide picture after the cover (the cover may be a builder's creative with its own print)
        own = next((p for p, _ in pics[1:] if _landscape(p)), pics[0][0] if pics else None)
        card = details_card(listing, c, own, name, logo, out_dir / "details" / "card.jpg")
        out.append({"angle": "details", "layout": "price_sheet", "format": "single", "images": [card],
                    "caption": details_caption(listing, c, contact, link_line), "used_llm": False, "prompts": []})
    except Exception:
        log.warning("listing posts: details card not drawn", exc_info=True)
    return out
