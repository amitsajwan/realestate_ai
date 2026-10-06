"""Instagram carousels (4:5, 1080x1350) for an agent's projects, in the AGENT's colours, drawn with the creative Canvas.

Per project: cover (area photo, clearly labelled as the area), prices, the MahaRERA check, possession in plain words, who it
suits + how to reach the agent. Plus one comparison carousel for all of an agent's projects. Every fact on a slide comes from
the project record (agent's quote or MahaRERA), and every slide passes the creative safe-area and contrast checks.
"""
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from PIL import Image, ImageOps

from app.core import brand
from app.modules.creative.layouts.base import Canvas, Rendered, gradient, mix, violations
from app.modules.creative.layouts.palette import get as palette

SIZE = (1080, 1350)
PHOTO_H = 600  # cover photo band height
ASSETS = Path(__file__).resolve().parent / "assets"
MIN_CONTRAST = 4.5
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class CardProblem(Exception):
    pass


def agent_palette(primary: str):
    """navy_gold with the agent's primary colour as the background (gold stays the accent)."""
    h = primary.lstrip("#")
    top = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    bottom = mix(top, (0, 0, 0), 0.45)
    return replace(palette("navy_gold"), id="agent", bg_top=top, bg_bottom=bottom, card=mix(top, (255, 255, 255), 0.10),
                   edge=mix(top, (255, 255, 255), 0.30))


def day(iso: Optional[str]) -> str:
    if not iso or len(iso) < 7:
        return ""
    y, m = iso[:4], int(iso[5:7])
    return (f"{int(iso[8:10])} " if len(iso) >= 10 else "") + f"{MONTHS[m - 1]} {y}"


def lakh(n: int) -> str:
    if n >= 10000000:
        return f"₹{n / 10000000:.2f}".rstrip("0").rstrip(".") + " Cr"
    return f"₹{n / 100000:.2f}".rstrip("0").rstrip(".") + " L"


def price_range(p: dict) -> str:
    lo, hi = p.get("price_min"), p.get("price_max")
    if lo is None:
        return ""
    return lakh(lo) if hi in (None, lo) else f"{lakh(lo)} – {lakh(hi)}"


def bhk_range(opts: Sequence[float]) -> str:
    s = [f"{b:g}" for b in opts]
    return (s[0] if len(s) == 1 else ", ".join(s[:-1]) + " & " + s[-1]) + " BHK" if s else ""


def _photo(url: str, size) -> Optional[Image.Image]:
    f = ASSETS / Path(url).name
    if not f.is_file():
        return None
    with Image.open(f) as im:
        return ImageOps.fit(im.convert("RGB"), size, Image.LANCZOS, centering=(0.5, 0.5))


def _footer(c: Canvas, agent: dict, n: int, i: int) -> None:
    """Agent name on the left, slide dots on the right, 'Powered by Avasetu' small. No Avasetu logo: it is his post."""
    y = c.bottom - 80
    c.text(agent["name"], c.left, y, 560, 30, "semibold", c.pal.ink, 1, role="brand", balance=False)
    c.text(f"Powered by {brand.NAME}", c.left, y + 40, 560, 20, "medium", c.pal.muted, 1, role="brand", balance=False)
    if n > 1:
        c.dots(n, i, c.right - 20 - (n - 1) * 13, y + 30)


def _kicker(c: Canvas, s: str, y: int) -> int:
    return c.text(s.upper(), c.left, y, c.right - c.left, 26, "bold", c.pal.accent, 1, role="kicker", balance=False) + 28


def cover(p: dict, agent: dict, n: int) -> Rendered:
    media = next((m for m in p.get("media") or [] if m.get("kind", "image") == "image"), None)
    pal = agent_palette(agent["primary"])
    band = _photo(media["url"], (SIZE[0], PHOTO_H)) if media else None
    bg = None
    if band is not None:  # the area photo as a band on top, fading into the agent's colour; all text sits below it
        bg = gradient(SIZE, pal.bg_top, pal.bg_bottom)
        fade = Image.linear_gradient("L").resize((SIZE[0], PHOTO_H)).point(lambda v: 255 if v < 150 else int(255 * (255 - v) / 105))
        bg.paste(band, (0, 0), fade)
    c = Canvas(SIZE, pal, "project_cover", 0, bg=bg)
    c.chip("Checked on MahaRERA", c.left, c.top + 10, icon="check", size=26)
    y = PHOTO_H - 10 if band is not None else 520
    y = _kicker(c, f"{p['locality']} · Pune", y)
    y = c.text(p["name"], c.left, y, c.right - c.left, 92, "bold", c.pal.ink, 3, min_size=60, role="headline") + 26
    y = c.text(f"{price_range(p)} · {bhk_range(p.get('bhk_options') or [])}", c.left, y, c.right - c.left, 46, "semibold",
               c.pal.accent, 2, min_size=34, role="support") + 22
    if p.get("positioning"):
        y = c.text(p["positioning"], c.left, y, c.right - c.left, 34, "medium", c.pal.ink, 3, min_size=26, role="body") + 18
    if media and media.get("credit"):
        c.text("Area photo, not the project. " + media["credit"], c.left, c.bottom - 120, c.right - c.left, 18, "medium",
               c.pal.muted, 2, min_size=16, role="credit", balance=False)
    _footer(c, agent, n, 0)
    return c.finish()


def prices(p: dict, agent: dict, n: int, i: int) -> Rendered:
    c = Canvas(SIZE, agent_palette(agent["primary"]), "project_prices", i, pattern=None)
    y = _kicker(c, "Prices and sizes", c.top + 10)
    y = c.text(p["name"], c.left, y, c.right - c.left, 60, "bold", c.pal.ink, 2, min_size=44, role="headline") + 40
    confs = p.get("configurations") or []
    row_h = 168 if len(confs) <= 3 else 132
    for conf in confs[:4]:
        c.rrect((c.left, y, c.right, y + row_h - 22), 26, c.pal.card)
        c.text(conf["label"], c.left + 32, y + 30, 380, 40, "bold", c.pal.card_ink, 1, role="body", balance=False, bg_hint=c.pal.card)
        c.text(f"{conf['carpet_sqft']:,} sq ft carpet".replace(",", ","), c.left + 32, y + 86, 420, 28, "medium", c.pal.card_muted, 1,
               role="body", balance=False, bg_hint=c.pal.card)
        c.text(lakh(conf["price_inr"]), c.right - 452, y + 26, 420, 50, "bold", c.pal.card_ink, 1, align="right", role="figure",
               balance=False, bg_hint=c.pal.card)
        c.text(f"₹{conf['price_per_sqft']:,}/sq ft", c.right - 452, y + 90, 420, 26, "medium", c.pal.card_muted, 1, align="right",
               role="body", balance=False, bg_hint=c.pal.card)
        y += row_h
    c.text(f"As quoted by {agent['name']}. Confirm price, floor and extra charges before you book.", c.left, y + 6,
           c.right - c.left, 26, "medium", c.pal.muted, 3, min_size=22, role="body")
    _footer(c, agent, n, i)
    return c.finish()


def rera(p: dict, agent: dict, n: int, i: int) -> Rendered:
    r = p.get("rera") or {}
    c = Canvas(SIZE, agent_palette(agent["primary"]), "project_rera", i, pattern=None)
    y = _kicker(c, "Checked on MahaRERA", c.top + 10)
    y = c.text("What the public record says", c.left, y, c.right - c.left, 60, "bold", c.pal.ink, 2, min_size=44, role="headline") + 44
    if p.get("booked_pct") is not None:
        c.text(f"{p['booked_pct']}%", c.left, y, 420, 150, "bold", c.pal.accent, 1, role="figure", balance=False)
        c.text(f"of {r.get('units_total')} homes already booked, as reported to MahaRERA", c.left + 430, y + 18, c.right - c.left - 430,
               32, "medium", c.pal.ink, 3, min_size=26, role="body")
        y += 196
    rows = [("Registration no.", p["rera_no"]), ("Name on MahaRERA", r.get("name", "")),
            ("Completion date filed", day(r.get("completion_now"))), ("Promoter", r.get("promoter", ""))]
    for k, v in rows:
        if not v:
            continue
        c.text(k, c.left, y, c.right - c.left, 26, "medium", c.pal.muted, 1, role="body", balance=False)
        y = c.text(v, c.left, y + 38, c.right - c.left, 38, "semibold", c.pal.ink, 2, min_size=28, role="body") + 30
    c.text(f"Read from maharera.maharashtra.gov.in on {day(r.get('checked_at'))}.", c.left, y + 4, c.right - c.left, 24,
           "medium", c.pal.muted, 2, min_size=20, role="body")
    _footer(c, agent, n, i)
    return c.finish()


def possession(p: dict, agent: dict, n: int, i: int) -> Rendered:
    r = p.get("rera") or {}
    c = Canvas(SIZE, palette("cream"), "project_possession", i, pattern=None, glow_at=None)
    y = _kicker(c, "When could you move in?", c.top + 10)
    y = c.text("Two dates. Plan around the MahaRERA one.", c.left, y, c.right - c.left, 66, "bold", c.pal.ink, 3, min_size=46,
               role="headline") + 50
    half = (c.right - c.left - 32) // 2
    for k, (label, value, note) in enumerate((
            ("Builder's target", day(p.get("possession_target")), f"as quoted by {agent['name']}"),
            ("Filed with MahaRERA", day(r.get("completion_now")), "the date the builder committed to"))):
        x = c.left + k * (half + 32)
        c.rrect((x, y, x + half, y + 300), 30, c.pal.card, outline=c.pal.edge, width=2)
        c.text(label, x + 30, y + 34, half - 60, 28, "semibold", c.pal.card_muted, 2, role="body", bg_hint=c.pal.card)
        c.text(value or "—", x + 30, y + 112, half - 60, 56, "bold", c.pal.card_ink, 1, min_size=40, role="figure", bg_hint=c.pal.card)
        c.text(note, x + 30, y + 200, half - 60, 24, "medium", c.pal.card_muted, 3, min_size=20, role="body", bg_hint=c.pal.card)
    y += 350
    if r.get("completion_at_registration") and r.get("completion_now") and r["completion_at_registration"] != r["completion_now"]:
        y = c.text(f"At registration MahaRERA showed {day(r['completion_at_registration'])}; it now shows {day(r['completion_now'])}.",
                   c.left, y, c.right - c.left, 32, "medium", c.pal.ink, 3, min_size=26, role="body") + 26
    c.text("Ask for the possession date in writing in your agreement for sale. Under RERA, delay beyond it can earn you interest or a refund.",
           c.left, y, c.right - c.left, 30, "medium", c.pal.muted, 4, min_size=24, role="body")
    _footer(c, agent, n, i)
    return c.finish()


def closing(p: dict, agent: dict, n: int, i: int) -> Rendered:
    c = Canvas(SIZE, agent_palette(agent["primary"]), "project_closing", i)
    y = _kicker(c, "Who it suits", c.top + 10)
    for w in (p.get("who_it_suits") or [])[:3]:
        c.circle((c.left + 14, y + 22), 10, c.pal.accent_fill)
        y = c.text(w, c.left + 44, y, c.right - c.left - 44, 40, "semibold", c.pal.ink, 2, min_size=30, role="body") + 34
    y = max(y + 40, 700)
    c.rrect((c.left, y, c.right, y + 330), 34, c.pal.accent_fill)
    c.text("Want prices for your floor and a site visit?", c.left + 40, y + 44, c.right - c.left - 80, 50, "bold", c.pal.accent_ink, 2,
           min_size=36, role="headline", bg_hint=c.pal.accent_fill)
    c.text("Comment PRICE, or WhatsApp", c.left + 40, y + 190, c.right - c.left - 80, 32, "medium", c.pal.accent_ink, 1, min_size=26,
           role="body", bg_hint=c.pal.accent_fill, balance=False)
    c.text(f"{agent['name']} · {agent['phone_display']}", c.left + 40, y + 240, c.right - c.left - 80, 40, "bold", c.pal.accent_ink, 1,
           min_size=30, role="body", bg_hint=c.pal.accent_fill, balance=False)
    _footer(c, agent, n, i)
    return c.finish()


SLIDES = (prices, rera, possession, closing)


def project_carousel(p: dict, agent: dict) -> List[Rendered]:
    """`p` is a PublicProject as a dict; `agent` = {name, phone_display, primary}. Raises CardProblem if a slide fails a check."""
    if not p.get("rera"):
        raise CardProblem(f"{p['slug']}: no MahaRERA reading yet")
    n = 1 + len(SLIDES)
    out = [cover(p, agent, n)] + [f(p, agent, n, i) for i, f in enumerate(SLIDES, 1)]
    check(out)
    return out


def compare_carousel(projects: List[dict], agent: dict, area: str) -> List[Rendered]:
    """Cover with the price span, one slide per project (price, homes, MahaRERA date, booked), and a closing slide."""
    ps = [p for p in projects if p.get("rera") and p.get("price_min") is not None]
    if len(ps) < 2:
        raise CardProblem("a comparison needs at least two checked projects")
    n = len(ps) + 2
    pal = agent_palette(agent["primary"])
    lo, hi = min(p["price_min"] for p in ps), max(p["price_max"] or p["price_min"] for p in ps)
    c = Canvas(SIZE, pal, "compare_cover", 0)
    c.chip("Checked on MahaRERA", c.left, c.top + 10, icon="check", size=26)
    y = _kicker(c, area, 520)
    y = c.text(f"{len(ps)} projects, {lakh(lo)} to {lakh(hi)}", c.left, y, c.right - c.left, 96, "bold", c.pal.ink, 3,
               min_size=64, role="headline", emph=(lakh(lo).split()[0], lakh(hi).split()[0])) + 30
    c.text("Prices, MahaRERA dates and how many homes are booked, side by side. Swipe.", c.left, y, c.right - c.left, 38,
           "medium", c.pal.muted, 3, min_size=28, role="support")
    _footer(c, agent, n, 0)
    out = [c.finish()]
    for i, p in enumerate(ps, 1):
        r = p["rera"]
        c = Canvas(SIZE, pal, "compare_item", i, pattern=None)
        y = _kicker(c, f"{i} of {len(ps)} · {p['locality']}", c.top + 10)
        y = c.text(p["name"], c.left, y, c.right - c.left, 74, "bold", c.pal.ink, 2, min_size=50, role="headline") + 16
        y = c.text(f"by {p['builder']}", c.left, y, c.right - c.left, 32, "medium", c.pal.muted, 1, role="support", balance=False) + 50
        facts = [("Price", price_range(p)), ("Homes", bhk_range(p.get("bhk_options") or [])),
                 ("MahaRERA date", day(r.get("completion_now"))),
                 ("Booked", f"{p['booked_pct']}% of {r.get('units_total')}" if p.get("booked_pct") is not None else "—")]
        for k, v in facts:
            c.rrect((c.left, y, c.right, y + 132), 24, c.pal.card)
            c.text(k, c.left + 30, y + 30, 360, 28, "medium", c.pal.card_muted, 1, role="body", balance=False, bg_hint=c.pal.card)
            c.text(v, c.left + 30, y + 72, c.right - c.left - 60, 40, "bold", c.pal.card_ink, 1, min_size=30, role="figure",
                   balance=False, bg_hint=c.pal.card)
            y += 150
        c.text(f"MahaRERA {p['rera_no']} · prices as quoted by {agent['name']}", c.left, y + 8, c.right - c.left, 22, "medium",
               c.pal.muted, 2, min_size=18, role="body")
        _footer(c, agent, n, i)
        out.append(c.finish())
    c = Canvas(SIZE, palette("cream"), "compare_closing", n - 1, pattern=None, glow_at=None)
    y = _kicker(c, "Before you decide", c.top + 10)
    y = c.text("Which one fits your budget and your move-in date?", c.left, y, c.right - c.left, 74, "bold", c.pal.ink, 3,
               min_size=50, role="headline") + 44
    for tip in ("Plan around the MahaRERA date, not the brochure date.", "Ask which building or phase your home is in.",
                "Confirm price, floor and extra charges in writing."):
        c.circle((c.left + 14, y + 22), 10, c.pal.accent_fill)
        y = c.text(tip, c.left + 44, y, c.right - c.left - 44, 36, "semibold", c.pal.ink, 2, min_size=28, role="body") + 30
    c.text(f"Comment the project name, or WhatsApp {agent['name']} · {agent['phone_display']}", c.left, y + 30, c.right - c.left, 34,
           "bold", c.pal.ink, 3, min_size=28, role="body")
    _footer(c, agent, n, n - 1)
    out.append(c.finish())
    check(out)
    return out


def check(slides: List[Rendered]) -> None:
    problems = []
    for k, r in enumerate(slides, 1):
        problems += [f"slide {k}: {v}" for v in violations(r)]
        problems += [f"slide {k}: '{it.text[:30]}' contrast {it.contrast:.1f}" for it in r.items if it.contrast < MIN_CONTRAST]
        problems += [f"slide {k}: '{it.text[:30]}' was cut short" for it in r.items if it.truncated]
    if problems:
        raise CardProblem("; ".join(problems)[:600])


def caption(p: dict, agent: dict, page_url: str = "") -> str:
    r = p.get("rera") or {}
    lines = [f"{p['name']}, {p['locality']}: {price_range(p)}, {bhk_range(p.get('bhk_options') or [])}.",
             p.get("positioning", ""),
             f"MahaRERA {p['rera_no']}: completion date filed {day(r.get('completion_now'))}"
             + (f", {p['booked_pct']}% of {r.get('units_total')} homes booked" if p.get("booked_pct") is not None else "")
             + f" (read on {day(r.get('checked_at'))}).",
             f"Builder's target: {day(p.get('possession_target'))}. Plan around the MahaRERA date." if p.get("possession_target") else "",
             f"Prices as quoted by {agent['name']}; confirm before booking.",
             f"Comment PRICE or WhatsApp {agent['phone_display']} for a site visit.",
             f"Every fact with its source: {page_url}" if page_url else "",
             "#Pune #" + p["locality"].replace(" ", "") + " #NewProjects #MahaRERA"]
    return "\n\n".join(x for x in lines if x)


def save_all(slides: List[Rendered], folder: Path, stem: str) -> List[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for k, r in enumerate(slides, 1):
        f = folder / f"{stem}-{k}.jpg"
        r.img.convert("RGB").save(f, "JPEG", quality=88, optimize=True, progressive=True)
        out.append(f)
    return out


def contact_sheet(files: List[Path], out: Path, cols: int = 5, w: int = 324) -> Path:
    ims = [Image.open(f).convert("RGB") for f in files]
    h = int(w * SIZE[1] / SIZE[0])
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * 12, rows * h + (rows + 1) * 12), (230, 232, 236))
    for k, im in enumerate(ims):
        sheet.paste(im.resize((w, h), Image.LANCZOS), (12 + (k % cols) * (w + 12), 12 + (k // cols) * (h + 12)))
    sheet.save(out, "JPEG", quality=85)
    return out


def area_label(projects: List[dict]) -> str:
    names: Dict[str, None] = {}
    for p in projects:
        names.setdefault(p["locality"], None)
    return " & ".join(names) + " · Pune"
