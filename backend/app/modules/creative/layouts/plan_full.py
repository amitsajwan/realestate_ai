"""Layout 9, plan card: one image from the builder's brochure shown big (a floor plan whole, a render filling the frame),
the headline above it and the image's label drawn on it ("Floor plan from the builder's brochure", "Artist's impression").

The image runs edge to edge across the card; a plan sits on white so its lines read, and is never cropped. The label is
code-written (Brief.plan_label) and always drawn: a render never appears without "Artist's impression" on it."""
from pathlib import Path
from typing import List

from PIL import Image, ImageOps

from ..models import Copy, Design
from .base import Canvas, Rendered, footer_h, known
from .palette import get

LABEL_FILL = (17, 24, 39)
PAPER = (255, 255, 255)
INSET = 24  # white space kept around a plan inside its frame


def _image(path: str, box_w: int, box_h: int, fit: str, reserve: int = 0) -> Image.Image:
    """The image for a box_w x box_h frame: the whole image on white ("contain", keeping `reserve` px free at the bottom for
    its label), or the frame filled ("cover"). A missing file gives a plain white frame."""
    frame = Image.new("RGB", (box_w, box_h), PAPER)
    p = Path(path) if path else None
    if p is None or not p.is_file():
        return frame
    with Image.open(p) as im:
        im = im.convert("RGB")
        if fit == "cover":
            return ImageOps.fit(im, (box_w, box_h), Image.LANCZOS, centering=(0.5, 0.45))
        room = max(1, box_h - 2 * INSET - reserve)
        inner = ImageOps.contain(im, (max(1, box_w - 2 * INSET), room), Image.LANCZOS)
    frame.paste(inner, ((box_w - inner.width) // 2, INSET + (room - inner.height) // 2))
    return frame


def render(copy: Copy, design: Design) -> List[Rendered]:
    pal, (W, H) = get(design.palette), design.size
    if pal.light:
        pal = get("navy_gold")
    tall = H > W
    p = copy.payload
    c = Canvas(design.size, pal, "plan_full", pattern=None, glow_at=(0.9, 0.05))
    w = c.right - c.left
    chip = c.chip(str(p.get("kicker", "FLOOR PLAN")), c.left, c.top, icon="home")
    rera_y = c.maharera_badge(beside=chip)  # top right; the headline starts below it
    hook_size = 66 if tall else 54
    y = c.text(copy.hook, c.left, max(chip[3], rera_y or 0) + 30, w, hook_size, "bold", pal.ink, 2, pitch=1.08, min_size=40, emph=design.emphasis,
               role="hook", balance=False)
    top = y + 34
    bottom = c.bottom - footer_h() - 30
    label = str(p.get("image_label") or "")
    fit = str(p.get("fit") or "contain")
    size = 26
    label_h = int(size * 1.95) if label else 0
    # a plan keeps its label below it (nothing covers a line of the plan); a render carries it on the picture itself
    frame = _image(str(p.get("image") or ""), W, bottom - top, fit, reserve=label_h + 14 if fit == "contain" else 0)
    c.img.paste(frame, (0, top))           # full bleed across the card
    c.shapes.append((c.left, top, c.right, bottom))  # what the critic measures (the image fills the safe area's width)
    if label:
        c.chip(label, c.left, bottom - 22 - label_h, fill=LABEL_FILL, ink=(255, 255, 255), size=size)
    c.brand_bar(right=known(copy.card_cta or "Save this"), dark_bg=True)
    return [c.finish()]
