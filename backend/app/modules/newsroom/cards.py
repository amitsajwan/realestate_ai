"""News cards for social: a designed 1080x1350 (Instagram) and 1080x1080 (Facebook) image per item, and the digest carousel;
and since 2026-11-15 a 1200x675 (16:9) one for the site itself: the article page, link previews and Google Discover, which only
shows a story as a large card when its picture is at least 1200 px wide.

One of the two files in the newsroom that may import `creative` (the other is adapters.py). It uses creative's drawing kit
(Canvas, palettes, bundled photos) so the cards share the brand look; the news layouts themselves live here because a news card needs
what the generic layouts have no room for: a NEWS chip with the pillar, and the source name and 'as of' date at the bottom.

Everything printed on a card is cut from the checked draft and its facts (`presentation`): the hook is the headline, at most 12 words,
the supporting line is another checked fact, the figure variant only enlarges a figure already in the hook. Nothing is added.
Three looks, chosen by a small rule (`choose_variant`):  figure (a rupee amount in the hook), photo (infrastructure, on a bundled dark
photo, labelled 'Illustrative photo'), headline (everything else, a typographic card)."""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image

from app.core import brand

from app.modules.creative.layouts.base import Canvas, Rendered, gradient, photo, scrim, violations
from app.modules.creative.layouts.palette import Palette, get as get_palette

from . import presentation as pr

log = logging.getLogger(__name__)

SIZES = {"ig": (1080, 1350), "fb": (1080, 1080), "web": (1200, 675)}
SOCIAL = ("ig", "fb")  # the channels a story is posted to; "web" is the site's own picture
MAX_BYTES = 380_000
DARK_PHOTOS = ("glass-dusk", "tower-low")  # bundled photos that are dark enough for white text
PALETTE_BY_PILLAR = {"infrastructure": "navy_gold", "new_supply": "navy_teal", "rules_money": "cream", "locality_life": "navy_coral",
                     "education": "cream", "digest": "navy_gold"}
RIGHT_CUE = {"ig": "Link in our bio", "fb": "More on our site"}
VARIANTS = ("figure", "photo", "headline")


DL_H = 62  # height reserved for the dateline


def _dateline(doc: dict) -> str:
    names = pr.area_names(doc)
    return (" · ".join(names) + ", PUNE").upper() if names else "PUNE"


class CardError(Exception):
    pass


def choose_variant(doc: dict) -> str:
    """figure when the hook carries a rupee amount, photo for infrastructure, else the typographic headline card."""
    if pr.figure(doc):
        return "figure"
    if pr.pillar(doc) == "infrastructure":
        return "photo"
    return "headline"


def _meta_line(doc: dict) -> str:
    src, when = pr.source_name(doc), pr.as_of_label(doc)
    return " · ".join(x for x in (f"Source: {src}" if src else "", f"As of {when}" if when else "") if x)


def _emph(text: str) -> List[str]:
    return [w for w in text.split() if any(ch.isdigit() for ch in w) or "₹" in w]


class _Frame:
    """The chrome every news card shares: NEWS chip, source and date line, brand bar. Returns the free vertical band for the content."""

    def __init__(self, c: Canvas, pal: Palette, kicker: str, meta: str, cue: str, dark: bool, dateline: str = "", counter: str = ""):
        self.c, self.pal, self.place = c, pal, dateline
        chip = c.chip(kicker, c.left, c.top, icon="bolt")
        if counter:  # 'Story 2 of 4' on carousel slides
            c.text(counter, c.right - 240, c.top + 10, 240, 30, "semibold", pal.muted, 1, align="right", min_size=24, balance=False, role="meta")
        c.brand_bar(right=cue, dark_bg=dark)
        brand_top = c.bottom - 64
        rule_y = brand_top - 30
        c.rrect((c.left, rule_y, c.right, rule_y + 2), 1, pal.edge)
        meta_y = rule_y - 20 - 28
        if meta:
            fs, _, _, trunc = c.fit(meta, c.right - c.left, 30, "medium", 1, 24, balance=False)
            if trunc:  # long source name: drop the label
                meta = meta.replace("Source: ", "")
            c.text(meta, c.left, meta_y, c.right - c.left, 30, "medium", pal.muted, 1, min_size=24, balance=False, role="meta")
        self.top, self.bottom = chip[3] + 56, meta_y - 44

    def dateline(self, y: int) -> int:
        """The place line of a news story, in the accent colour ('KHARADI · WAGHOLI, PUNE'). Returns the y below it."""
        if self.place:
            c = self.c
            c.text(self.place, c.left, y, c.right - c.left, 28, "semibold", self.pal.accent, 1, min_size=24, balance=False, role="meta")
        return y + DL_H


def _canvas(variant: str, channel: str, doc: dict, bg: Optional[Image.Image] = None) -> Tuple[Canvas, Palette]:
    pal = get_palette(PALETTE_BY_PILLAR.get(pr.pillar(doc), "navy_gold"))
    if variant == "photo" and pal.light:
        pal = get_palette("navy_gold")
    return Canvas(SIZES[channel], pal, f"news_{variant}", bg=bg, pattern="rings" if variant == "figure" else "dots",
                  glow_at=(0.5, 0.34) if variant == "figure" else (0.9, 0.06)), pal


def _kicker(doc: dict) -> str:
    return f"NEWS · {pr.pillar_label(doc).upper()}"


def _render_headline(doc: dict, channel: str, hook: str, support: str, counter: str = "", over: Optional[dict] = None) -> Rendered:
    """The typographic card. `over` (digest slides) replaces the kicker, source line, dateline, palette or right-hand cue."""
    over = over or {}
    c, pal = _canvas("headline", channel, doc)
    if over.get("pal"):
        pal = get_palette(over["pal"])
        c = Canvas(SIZES[channel], pal, "news_headline", pattern="dots", glow_at=(0.9, 0.06))
    tall = SIZES[channel][1] > SIZES[channel][0]
    f = _Frame(c, pal, over.get("kicker", _kicker(doc)), over.get("meta", _meta_line(doc)), over.get("cue", RIGHT_CUE[channel]),
               not pal.light, over.get("place", _dateline(doc)), counter)
    w = c.right - c.left
    size, lines, floor = over.get("size", 104 if tall else 92), over.get("lines", 5), over.get("min", 64)
    sh = c.measure(support, w, 40, "medium", 3, pitch=1.3, balance=False) if support else 0
    room = f.bottom - f.top - DL_H - 50 - (44 + sh if sh else 0)  # what is left for the headline
    hh = c.measure(hook, w, size, "bold", lines, pitch=1.08, min_size=floor, h=room)
    sh = c.measure(support, w, 40, "medium", 3, pitch=1.3, balance=False) if support else 0
    total = DL_H + 10 + 40 + hh + (44 + sh if sh else 0)
    y = f.dateline(f.top + max(0, (f.bottom - f.top - total) // 2))
    c.rrect((c.left, y, c.left + 130, y + 10), 5, pal.accent_fill)
    y = c.text(hook, c.left, y + 10 + 40, w, size, "bold", pal.ink, lines, pitch=1.08, min_size=floor, h=room, emph=_emph(hook), role="hook")
    if support:
        c.text(support, c.left, y + 44, w, 40, "medium", pal.muted, 3, pitch=1.3, balance=False, role="support")
    return c.finish()


def _render_figure(doc: dict, channel: str, value: str, label: str, support: str) -> Rendered:
    c, pal = _canvas("figure", channel, doc)
    tall = SIZES[channel][1] > SIZES[channel][0]
    f = _Frame(c, pal, _kicker(doc), _meta_line(doc), RIGHT_CUE[channel], not pal.light, _dateline(doc))
    w = c.right - c.left
    num_size = 240 if tall else 200
    nfs, _, nh, _ = c.fit(value, w, num_size, "bold", 1, 110, balance=False)
    lab_size = 66 if tall else 56
    sh = c.measure(support, w, 36, "medium", 2, pitch=1.3, balance=False) if support else 0
    gap = 34
    room = f.bottom - f.top - DL_H - nh - 36 - 10 - gap - (gap + sh if sh else 0)
    lh = c.measure(label, w, lab_size, "bold", 4, pitch=1.12, min_size=44, h=room)
    total = DL_H + nh + 36 + 10 + gap + lh + (gap + sh if sh else 0)
    y = f.dateline(f.top + max(0, (f.bottom - f.top - total) // 2))
    c.glow((c.W // 2, y + nh // 2), 460, pal.glow, 0.28 if not pal.light else 0.4)
    y = c.text(value, c.left, y, w, nfs, "bold", pal.accent, 1, min_size=110, balance=False, role="hero")
    c.rrect((c.left, y + 36, c.left + 150, y + 46), 5, pal.accent_fill)
    y = c.text(label, c.left, y + 36 + 10 + gap, w, lab_size, "bold", pal.ink, 4, pitch=1.12, min_size=44, h=room, emph=_emph(label), role="hook")
    if support:
        c.text(support, c.left, y + gap, w, 36, "medium", pal.muted, 2, pitch=1.3, balance=False, role="support")
    return c.finish()


def _photo_key(doc: dict) -> str:
    n = int(doc.get("_id", "0")[:6] or "0", 16) if all(ch in "0123456789abcdef" for ch in (doc.get("_id") or "0")[:6]) else 0
    return DARK_PHOTOS[n % len(DARK_PHOTOS)]


def _render_photo(doc: dict, channel: str, hook: str, support: str) -> Rendered:
    size = SIZES[channel]
    img = photo(_photo_key(doc), size, centering=(0.5, 0.4))
    img = scrim(img if img is not None else gradient(size, (26, 54, 98), (9, 20, 42)), 0.30, 0.94)
    img = scrim(img, 0.50, 0.60, top=True)
    c, pal = _canvas("photo", channel, doc, bg=img)
    tall = size[1] > size[0]
    f = _Frame(c, pal, _kicker(doc), _meta_line(doc), "Illustrative photo", True, _dateline(doc))
    w = c.right - c.left
    hs = 100 if tall else 88
    sh = c.measure(support, w, 40, "medium", 3, pitch=1.3, balance=False) if support else 0
    room = f.bottom - f.top - 38 - DL_H - (sh + 30 if sh else 0)
    hh = c.measure(hook, w, hs, "bold", 5, pitch=1.06, min_size=60, h=room)
    y = f.bottom - hh - (sh + 30 if sh else 0)
    f.dateline(y - 38 - DL_H)
    c.rrect((c.left, y - 38, c.left + 120, y - 28), 5, pal.accent_fill)
    y = c.text(hook, c.left, y, w, hs, "bold", (255, 255, 255), 5, pitch=1.06, min_size=60, h=room, emph=_emph(hook), role="hook")
    if support:
        c.text(support, c.left, y + 30, w, 40, "medium", (222, 228, 240), 3, pitch=1.3, balance=False, role="support")
    return c.finish()


def _render_wide(doc: dict, hook: str, support: str, variant: str, over: Optional[dict] = None) -> Rendered:
    """The 16:9 card for the site (1200x675). Shorter than the social cards, so its chrome is tighter: chip, the place on its
    own line, the headline (with a figure in the hook lit in the accent colour: there is no room for the big figure layout),
    the source and date line, the brand bar. `photo` sits the words on the same bundled dark photo as the Instagram card;
    anything else is the typographic card. `over` (the digest's cover) replaces the kicker, source line or place."""
    over = over or {}
    size = SIZES["web"]
    bg = None
    if variant == "photo":
        img = photo(_photo_key(doc), size, centering=(0.5, 0.4))
        bg = scrim(scrim(img if img is not None else gradient(size, (26, 54, 98), (9, 20, 42)), 0.30, 0.94), 0.50, 0.60, top=True)
    c, pal = _canvas(variant, "web", doc, bg=bg)
    if over.get("pal"):
        pal = get_palette(over["pal"])
        c = Canvas(size, pal, "news_headline", pattern="dots", glow_at=(0.9, 0.06))
    dark = variant == "photo" or not pal.light
    w = c.right - c.left
    chip = c.chip(over.get("kicker", _kicker(doc)), c.left, c.top, icon="bolt")
    c.brand_bar(right="Illustrative photo" if variant == "photo" else "", dark_bg=dark)
    meta = over.get("meta", _meta_line(doc))
    meta_y = c.bottom - 64 - 18 - 30
    if meta:
        fs, _, _, trunc = c.fit(meta, w, 30, "medium", 1, 24, balance=False)
        if trunc:  # long source name: drop the label
            meta = meta.replace("Source: ", "")
        c.text(meta, c.left, meta_y, w, 30, "medium", pal.muted, 1, min_size=24, balance=False, role="meta")
    y = chip[3] + 22
    place = over.get("place", _dateline(doc))
    if place:
        c.text(place, c.left, y, w, 28, "semibold", pal.accent, 1, min_size=24, balance=False, role="meta")
        y += 50
    top, bottom = y, meta_y - 28
    sh = c.measure(support, w, 30, "medium", 2, pitch=1.3, balance=False) if support else 0
    room = bottom - top - 10 - 24 - (24 + sh if sh else 0)  # what is left for the headline under the accent bar
    hh = c.measure(hook, w, 72, "bold", 3, pitch=1.08, min_size=50, h=room)
    total = 10 + 24 + hh + (24 + sh if sh else 0)
    y = top + max(0, (bottom - top - total) // 2)
    c.rrect((c.left, y, c.left + 130, y + 10), 5, pal.accent_fill)
    ink = (255, 255, 255) if variant == "photo" else pal.ink
    y = c.text(hook, c.left, y + 10 + 24, w, 72, "bold", ink, 3, pitch=1.08, min_size=50, h=room, emph=_emph(hook), role="hook")
    if support:
        c.text(support, c.left, y + 24, w, 30, "medium", (222, 228, 240) if variant == "photo" else pal.muted, 2, pitch=1.3,
               balance=False, role="support")
    return c.finish()


def problems(r: Rendered) -> List[str]:
    """Margin violations (nothing outside the 84 px safe area, so Instagram's 3:4 grid crop cannot cut anything) and text that did not fit."""
    out = violations(r)
    out += [f"text does not fit: '{i.text[:30]}'" for i in r.items if i.truncated]
    out += [f"text too small: '{i.text[:30]}' {i.size}px" for i in r.items if i.size < 24 and i.role not in ("brand", "chip", "meta")]
    for n, a in enumerate(r.items):  # two texts drawn over each other
        for b in r.items[n + 1:]:
            if min(a.box[2], b.box[2]) - max(a.box[0], b.box[0]) > 4 and min(a.box[3], b.box[3]) - max(a.box[1], b.box[1]) > 4:
                out.append(f"texts overlap: '{a.text[:20]}' and '{b.text[:20]}'")
    return out


def render_card(doc: dict, channel: str, variant: Optional[str] = None, counter: str = "", over: Optional[dict] = None) -> Tuple[Image.Image, Rendered, str]:
    """One card. Tries the full hook first, then shorter ones, until every line fits. Returns (image, layout record, variant)."""
    variant = variant or choose_variant(doc)
    # the subtitle is another checked fact; only when there is none does the fixed buyer line take the slot (dropped if it does not fit)
    base_hook, support = pr.hook(doc), pr.support_line(doc) or pr.buyer_line(doc)
    fig = pr.figure(doc) if variant == "figure" else None
    if variant == "figure" and not fig:
        variant = "headline"
    last: Optional[Rendered] = None
    for limit in (12, 10, 8):
        hook = pr._cut_clause(base_hook, limit)
        for sup in ([support, ""] if support else [""]):
            if channel == "web":
                r = _render_wide(doc, hook, sup, "photo" if variant == "photo" else "headline", over)
            elif variant == "figure":
                value, label = fig
                r = _render_figure(doc, channel, value, pr._cut_clause(label, limit), sup)  # label is the hook
            elif variant == "photo":
                r = _render_photo(doc, channel, hook, sup)
            else:
                r = _render_headline(doc, channel, hook, sup, counter, over)
            last = r
            if not problems(r):
                return r.img, r, variant
    raise CardError("card does not fit: " + "; ".join(problems(last))[:200])


def save(img: Image.Image, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = img.convert("RGB")
    for q in (88, 84, 80, 74, 68, 60):
        img.save(path, "JPEG", quality=q, optimize=True, progressive=True)
        if path.stat().st_size <= MAX_BYTES:
            break
    return path.stat().st_size


def render_item(doc: dict, uploads: Path, variant: Optional[str] = None) -> Dict[str, Optional[str]]:
    """Render and save every size for one item. Returns paths relative to `uploads`: {"ig": "news/<id>-ig.jpg", "fb": ...,
    "web": ..., "variant": ...}. The social cards must fit (a CardError stops the item); the site's wide card is extra, so when
    it alone does not fit the item keeps "web": None and the site shows the square card instead."""
    out: Dict[str, Optional[str]] = {}
    for ch in SOCIAL:
        img, _, used = render_card(doc, ch, variant)
        rel = f"news/{doc['_id']}-{ch}.jpg"
        save(img, Path(uploads) / rel)
        out[ch], out["variant"] = rel, used
    out["web"] = render_web(doc, uploads, variant)
    return out


def render_web(doc: dict, uploads: Path, variant: Optional[str] = None) -> Optional[str]:
    """Save the 1200x675 card of a story or the digest's cover; the path relative to `uploads`, or None when it cannot be drawn."""
    rel = f"news/{doc['_id']}-web.jpg"
    try:
        if (doc.get("draft") or {}).get("format") == "digest":
            img = digest_cover_wide(doc.get("digest") or {})
        else:
            img = render_card(doc, "web", variant)[0]
    except CardError as e:
        log.warning("newsroom: wide card for %s not drawn: %s", doc.get("_id"), e)
        return None
    save(img, Path(uploads) / rel)
    return rel


# ---- the weekly digest: cover, one slide per story, the tip, a closing slide (Instagram); the cover alone for Facebook ----------------------

def _story_doc(it: dict) -> dict:
    """A story snapshot stored in the digest, shaped like an item so the same renderer draws it."""
    return {"_id": it["id"], "draft": {"title": it["headline"], "text": "", "source_names": [it.get("source", "")]},
            "facts": {"facts": [{"text": it.get("line") or "", "quote": ""}] if it.get("line") else [], "as_of": it.get("as_of")},
            "relevance": {"pillar": it.get("pillar"), "areas": it.get("areas", [])}, "raw": {"source": it.get("source", "")}}


def _digest_over(kicker: str, place: str = "KHARADI · WAGHOLI, PUNE", pal: str = "navy_gold", meta: str = "", cue: Optional[str] = None, **extra) -> dict:
    d = {"kicker": kicker, "place": place, "pal": pal, "meta": meta, **extra}
    if cue is not None:
        d["cue"] = cue
    return d


def _hl(*args, **kw) -> Image.Image:
    r = _render_headline(*args, **kw)
    if problems(r):
        raise CardError("digest slide does not fit: " + "; ".join(problems(r))[:200])
    return r.img


def _digest_cover(dg: dict) -> Tuple[dict, str, str, str, str]:
    """What every size of the digest's cover prints: the stand-in doc, the cover line, its supporting line, the kicker, the meta line."""
    when = dg.get("as_of")
    as_of = f"{when.day} {pr.MONTHS[when.month - 1]} {when.year}" if when else ""
    meta = dg.get("meta") or "Our summaries of local reports" + (f" · As of {as_of}" if as_of else "")
    base = {"_id": "digest", "relevance": {"pillar": "digest", "areas": ["kharadi", "wagholi"]}, "draft": {"format": "digest"}}
    n = len(dg.get("items", []))
    cover_sup = dg.get("cover_line") or f"{n} local updates and one buyer tip"
    return base, dg.get("cover") or dg.get("title", "Kharadi and Wagholi this week"), cover_sup, dg.get("kicker") or "NEWS · THIS WEEK", meta


def digest_cover_wide(dg: dict) -> Image.Image:
    """The digest's cover at 1200x675 for the site; shorter supporting lines tried until it fits."""
    base, cover, sup, kicker, meta = _digest_cover(dg)
    last: Optional[Rendered] = None
    for s in (sup, ""):
        last = _render_wide(base, cover, s, "headline", _digest_over(kicker, meta=meta))
        if not problems(last):
            return last.img
    raise CardError("digest cover does not fit: " + "; ".join(problems(last))[:200])


def digest_slides(dg: dict, channel: str = "ig") -> List[Image.Image]:
    """Cover, one slide per story, the tip, and a closing slide (Instagram); just the cover for Facebook.
    A digest of another kind (New on MahaRERA) brings its own kicker, meta, cover line and closing words."""
    base, cover, cover_sup, kicker, meta = _digest_cover(dg)
    items = dg.get("items", [])
    n = len(items)
    cover_sup += ". Swipe." if channel == "ig" else ""
    slides = [_hl(base, channel, cover, cover_sup, "", _digest_over(kicker, meta=meta))]
    if channel != "ig":
        return slides
    for i, it in enumerate(items, 1):
        slides.append(render_card(_story_doc(it), channel, "headline", counter=f"{i} of {n}")[0])
    slides.append(_hl(base, channel, dg.get("tip", ""), "", "", _digest_over(
        "NEWS · BUYER TIP", place="BEFORE YOU DECIDE", pal="cream", meta="General information, not investment or legal advice",
        size=80, lines=8, min=48)))
    slides.append(_hl(base, channel, dg.get("closing_title") or "Every story, with its source, on our site",
                      dg.get("closing_line") or "Tap the link in our bio and open News.", "",
                                   _digest_over("NEWS · " + brand.NAME.upper(), place="", meta="", cue="Link in our bio")))
    return slides


def render_digest(doc: dict, uploads: Path) -> dict:
    """Save the digest cards. Paths relative to `uploads`: {"ig": [cover, ..., closing], "fb": cover, "web": the wide cover (or
    None), "variant": "digest"}."""
    dg = doc.get("digest") or {}
    stem = f"news/{doc['_id']}"
    ig = []
    for i, img in enumerate(digest_slides(dg, "ig"), 1):
        rel = f"{stem}-ig-{i}.jpg"
        save(img, Path(uploads) / rel)
        ig.append(rel)
    fb = f"{stem}-fb.jpg"
    save(digest_slides(dg, "fb")[0], Path(uploads) / fb)
    return {"ig": ig, "fb": fb, "web": render_web(doc, uploads), "variant": "digest"}


def render_doc(doc: dict, uploads: Path) -> dict:
    """Cards for any newsroom item (a story or the digest)."""
    if (doc.get("draft") or {}).get("format") == "digest":
        return render_digest(doc, uploads)
    return render_item(doc, uploads)
