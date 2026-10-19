"""The MahaRERA badge on project ads: a QR code, "MahaRERA: P5..." and the regulator's website (docs/MARKETING.md, "MahaRERA
on our ads"; MahaRERA Order 46C/2025 of 8 Apr 2025, after Orders 46/2023, 46A/2023 and 46B/2023).

Drawn only for a PROJECT registration we trust (a "P5" number; propertyfacts.advert decides which), never for the agent's own
registration (an "A5" number, shown as "Listed by ... · RERA ..."). Exempt, unknown and unverified projects get no badge.

The QR encodes the most specific official page we can name:
    the project's public record  https://maharerait.maharashtra.gov.in/public/project/view/<MahaRERA id>  when we know its id
                                 (the page MahaRERA's own search links each project to; verified 2026-10-03)
    otherwise the MahaRERA site  https://maharera.maharashtra.gov.in/  where the number under the code is searched
Any other URL is refused, so a badge can never send a buyer anywhere else.

Pure drawing (segno + Pillow), no I/O. `configure(resolve=...)` (app/wiring.py) lets the pack and the walkthrough reel ask
propertyfacts for the registration (the brochure kit and the fact sheet); without it the listing's own number is used."""
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Awaitable, Callable, List, Optional, Tuple

import segno
from PIL import Image, ImageDraw, ImageFont

SITE = "maharera.maharashtra.gov.in"
HOME_URL = f"https://{SITE}/"
PROJECT_VIEW = "https://maharerait.maharashtra.gov.in/public/project/view/"
_VIEW_RE = re.compile(r"^https://maharerait\.maharashtra\.gov\.in/public/project/view/(\d{1,12})$")
_PROJECT_RE = re.compile(r"P5\d{10}|PR\d{13}")   # a MahaRERA project number (PR + 13 digits since 2025); "A5..." is an agent's
QUIET = 4                                    # modules of white around the code (the QR standard's quiet zone)
PANEL = (255, 255, 255)
INK = (16, 35, 64)                           # brand navy on the white panel
INK_SOFT = (60, 72, 96)
EDGE = (196, 204, 218)
FONT_DIR = Path(__file__).parent / "fonts"   # the cards' Poppins (images.py draws with the same files)
FONTS = {"bold": "Poppins-Bold.ttf", "semibold": "Poppins-SemiBold.ttf"}


def project_regno(value: Any) -> str:
    """'P 52100 076768' -> 'P52100076768'; '' for anything that is not a MahaRERA project number (an agent's A5..., junk)."""
    v = re.sub(r"[\s-]", "", str(value or "")).upper()
    return v if _PROJECT_RE.fullmatch(v) else ""


def view_url(url: Any) -> str:
    """The project's own MahaRERA page when `url` is one (any other link: '')."""
    m = _VIEW_RE.match(str(url or "").strip())
    return f"{PROJECT_VIEW}{int(m.group(1))}" if m else ""


@dataclass(frozen=True)
class ProjectRegistration:
    """A project registration we trust, ready to print: the number and where its QR code leads."""
    regno: str
    url: str = HOME_URL

    @property
    def line(self) -> str:
        return f"MahaRERA: {self.regno}"


def registration(regno: Any, url: Any = "") -> Optional[ProjectRegistration]:
    """A badge for this number, its QR leading to the project's own page when `url` is it, else to the MahaRERA site; None when
    `regno` is not a project number."""
    reg = project_regno(regno)
    return ProjectRegistration(reg, view_url(url) or HOME_URL) if reg else None


# ---- where the pack and the reel ask (wired at startup) ----------------------------------------------------------------
Resolve = Callable[[Any, dict], Awaitable[Optional[ProjectRegistration]]]
_resolve: Optional[Resolve] = None


def configure(resolve: Optional[Resolve] = None) -> None:
    """`resolve(db, listing)`: propertyfacts' answer from the listing, its brochure kit and its fact sheet (app/wiring.py)."""
    global _resolve
    _resolve = resolve


def _sample(listing: dict) -> bool:
    return (listing.get("title") or "").strip().lower().startswith("sample")


def from_listing(listing: dict) -> Optional[ProjectRegistration]:
    """The listing's own project number (the agent's listing data); a sample listing never carries one."""
    return None if _sample(listing) else registration(listing.get("rera_no"))


async def for_listing(listing: dict, db: Any = None) -> Optional[ProjectRegistration]:
    """The registration to print on this listing's ads. With a database the wired resolver decides (an `exempt` answer or a
    number MahaRERA contradicts gives None); if it fails or is not wired, the listing's own number."""
    if _resolve is not None and db is not None and not _sample(listing):
        try:
            return await _resolve(db, listing)
        except Exception:
            pass
    return from_listing(listing)


# ---- drawing ----------------------------------------------------------------------------------------------------------
@lru_cache(maxsize=16)
def _font(size: int, weight: str):
    try:
        return ImageFont.truetype(str(FONT_DIR / FONTS[weight]), size)
    except OSError:
        return ImageFont.load_default(size=size)


@lru_cache(maxsize=32)
def qr_image(url: str, px: int) -> Image.Image:
    """The QR code for `url` (an official MahaRERA URL only) as a crisp black-on-white square of about `px` pixels (whole pixels
    per module, so the nearest whole size), quiet zone included. Error correction M survives JPEG and a phone camera."""
    if not (view_url(url) or url == HOME_URL):
        raise ValueError("the MahaRERA QR code only leads to MahaRERA")
    code = segno.make(url, error="m", micro=False)
    n = len(code.matrix) + 2 * QUIET
    small = Image.new("L", (n, n), 255)
    pix = small.load()
    for y, row in enumerate(code.matrix):
        for x, dark in enumerate(row):
            if dark:
                pix[x + QUIET, y + QUIET] = 0
    scale = max(2, round(px / n))
    return small.resize((n * scale, n * scale), Image.NEAREST)


@dataclass
class Badge:
    """The badge as an RGBA image and what it says (for the margin, contrast and no-phone checks)."""
    img: Image.Image
    texts: List[str]
    qr_box: Tuple[int, int, int, int]                          # where the code sits inside img
    text_boxes: List[Tuple[int, int, int, int]]
    text_px: int
    ink: Tuple[int, int, int] = INK
    panel: Tuple[int, int, int] = PANEL

    @property
    def size(self) -> Tuple[int, int]:
        return self.img.size


def badge(reg: ProjectRegistration, qr_px: int = 156, text_px: int = 28, pad: Optional[int] = None) -> Badge:
    """A white rounded panel: the QR code on the left, "MahaRERA: P5..." (bold) and the website on the right. Navy on white, so
    it reads on any photo. The website and the number are drawn at the same size (the order asks both to be no smaller than
    the ad's contact details)."""
    code = qr_image(reg.url, qr_px)
    q = code.size[0]
    pad = pad if pad is not None else max(6, q // 24)   # the code brings its own white quiet zone
    gap = max(14, text_px // 2)
    bold, semi = _font(text_px, "bold"), _font(text_px, "semibold")
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    lines = [(reg.line, bold, INK), (SITE, semi, INK_SOFT)]
    tw = int(max(probe.textlength(t, font=f) for t, f, _ in lines)) + 2
    pitch = int(text_px * 1.32)
    th = pitch * (len(lines) - 1) + int(text_px * 1.05)
    w, h = pad + q + gap + tw + pad + 4, pad + q + pad
    s = 3                                                      # supersampled panel edge
    mask = Image.new("L", (w * s, h * s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=max(12, pad + 6) * s, fill=255)
    img = Image.new("RGBA", (w, h), PANEL + (0,))
    img.putalpha(mask.resize((w, h), Image.LANCZOS))
    ring = Image.new("L", (w * s, h * s), 0)        # a thin grey edge, so the panel still reads on a white wall or sky
    ImageDraw.Draw(ring).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=max(12, pad + 6) * s, outline=255, width=2 * s)
    img.paste(EDGE + (255,), (0, 0), ring.resize((w, h), Image.LANCZOS))
    img.paste(code.convert("RGBA"), (pad, pad))
    d = ImageDraw.Draw(img)
    x, y = pad + q + gap, pad + (q - th) // 2
    boxes = []
    for i, (t, f, ink) in enumerate(lines):
        d.text((x, y + i * pitch), t, font=f, fill=ink + (255,))
        boxes.append(tuple(int(v) for v in d.textbbox((x, y + i * pitch), t, font=f)))
    return Badge(img, [t for t, _, _ in lines], (pad, pad, pad + q, pad + q), boxes, text_px)
