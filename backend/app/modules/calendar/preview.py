"""Owner review material: one contact sheet per plan week (every image of every item, with its slot) and a text file with all captions."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw

from app.modules.marketing.images import load_font

from .schedule import IST

BG = (236, 238, 243)
INK = (24, 30, 44)
THUMB_W = 210
LABEL_W = 330
GAP = 12
MAX_THUMBS = 7
CH = {"instagram": "INSTAGRAM", "facebook_page": "FACEBOOK"}


def ist(d: datetime) -> str:
    d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    return d.astimezone(IST).strftime("%a %d %b, %H:%M IST")


def _wrap(draw, text: str, font, width: int) -> List[str]:
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def _reel_tile(doc: dict, h: int) -> Image.Image:
    w = int(h * 9 / 16)
    im = Image.new("RGB", (w, h), (16, 35, 64))
    d = ImageDraw.Draw(im)
    d.text((14, 14), "REEL " + str((doc.get("creative") or {}).get("template", "")).upper(), font=load_font(15, "bold"), fill=(240, 180, 41))
    y = 54
    for line in ((doc.get("creative") or {}).get("script") or [])[:5]:
        for ln in _wrap(d, line.replace("*", ""), load_font(15, "semibold"), w - 28)[:4]:
            d.text((14, y), ln, font=load_font(15, "semibold"), fill=(255, 255, 255))
            y += 20
        y += 10
    return im


def week_sheet(docs: List[dict], uploads: Path) -> Image.Image:
    rows = []
    for doc in docs:
        thumbs: List[Image.Image] = []
        ims = list(doc.get("images") or [])[:MAX_THUMBS]
        for rel in ims:
            p = Path(uploads) / rel
            if p.is_file():
                with Image.open(p) as im:
                    im = im.convert("RGB")
                    thumbs.append(im.resize((THUMB_W, int(im.height * THUMB_W / im.width)), Image.LANCZOS))
        if doc.get("kind") == "reel":
            thumbs.append(_reel_tile(doc, 340))
        rows.append((doc, thumbs, max([t.height for t in thumbs] or [120])))
    width = LABEL_W + MAX_THUMBS * (THUMB_W + GAP) + GAP
    height = GAP + sum(h + GAP + 6 for _, _, h in rows)
    sheet = Image.new("RGB", (width, max(height, 100)), BG)
    d = ImageDraw.Draw(sheet)
    y = GAP
    for doc, thumbs, h in rows:
        c = doc.get("creative") or {}
        lines = [(CH.get(doc["channel"], doc["channel"]) + "  " + str(doc.get("kind", "post")).upper(), "bold", 17, INK),
                 (ist(doc["due_at"]), "semibold", 16, INK),
                 (doc["slug"], "regular", 14, (70, 76, 92)),
                 (f"layout: {c.get('layout', '-')}  format: {c.get('format') or '-'}", "regular", 14, (70, 76, 92)),
                 (f"made by: {c.get('path', '-')}", "regular", 14, (70, 76, 92)),
                 (f"status: {doc.get('status', '')}", "regular", 14, (70, 76, 92))]
        ly = y
        for text, wt, sz, col in lines:
            for ln in _wrap(d, text, load_font(sz, wt), LABEL_W - 20):
                d.text((GAP, ly), ln, font=load_font(sz, wt), fill=col)
                ly += sz + 6
        hook = c.get("hook")
        if hook:
            for ln in _wrap(d, f"Hook: {hook}", load_font(14, "medium"), LABEL_W - 20)[:4]:
                d.text((GAP, ly + 4), ln, font=load_font(14, "medium"), fill=(150, 90, 0))
                ly += 20
        x = LABEL_W
        for t in thumbs:
            sheet.paste(t, (x, y))
            x += THUMB_W + GAP
        y += h + GAP + 6
    return sheet


def write_preview(docs: List[dict], uploads: Path, out_dir: Path) -> Dict[int, Path]:
    """week-N.jpg per plan week plus captions.txt (all captions, in date order). Returns {week: sheet path}."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_week = defaultdict(list)
    for d in sorted(docs, key=lambda d: (d["due_at"], d["channel"])):
        by_week[d.get("week") or 0].append(d)
    paths = {}
    for week, items in sorted(by_week.items()):
        p = out_dir / f"week-{week}.jpg"
        sheet = week_sheet(items, uploads)
        for q in (82, 74, 66, 58, 50):  # review sheets are kept under 1 MB so they can live in git
            sheet.save(p, "JPEG", quality=q, optimize=True)
            if p.stat().st_size < 950_000:
                break
        paths[week] = p
        with open(out_dir / f"week-{week}-captions.txt", "w", encoding="utf8") as f:
            for d in items:
                f.write(f"===== {ist(d['due_at'])}  {d['channel']}  {d.get('kind', 'post')}  {d['slug']}  [{d.get('status')}] id={d['_id']}\n")
                f.write(f"images: {', '.join(d.get('images') or []) or '-'}\n\n{d['caption']}\n\n")
    return paths
