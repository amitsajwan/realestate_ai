"""What each page of a designed brochure shows, labelled by the vision model from numbered contact sheets.

Big builders' brochures are pictures with no text layer, and the useful pages are rarely the first: Lodha Camelot opens with
the company, its other projects (Altamount, World Towers, London), awards and lifestyle stock photos; the location map,
master plan, floor plans and the RERA page come at pages 25-34. Reading every page with the vision model costs ~2k tokens a
page, so the pages are first laid out small on one or two contact sheets (a big page number drawn on each) and the model
labels every page on a sheet in one request. The readers then read the pages worth reading (`read_order`) and the picture
pool can leave out the developer's portfolio and stock photos.

    triage(page_jpgs) -> {page (from 1): {"kind": KIND, "other_project": bool, "cgi": bool, "note": str}}

`kind` is one of KINDS; `other_project` the page shows a different project or the developer's portfolio; `cgi` the page is
labelled CGI / artist's impression or is clearly a render. Saved as triage.json beside the page JPEGs (`save` / `load`).
Never raises; with no vision model (or none answering) it returns {} and the callers keep the first pages, as before."""
import asyncio
import io
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

log = logging.getLogger(__name__)

KINDS = ("cover", "corporate", "lifestyle", "render", "master_plan", "floor_plan", "location_map", "amenities", "specs",
         "price", "legal", "text", "other")
SHEET_MAX = 18          # pages on one contact sheet (35 pages: two sheets)
SHEET_W = 1200          # contact sheet width in pixels; its height stays under SHEET_H_MAX
SHEET_H_MAX = 1100
GAP = 6
LABEL_PX = 44           # the page number's font size
REPLY_TOKENS = 1600     # ~40 tokens a page, with room for a reasoning model's preamble
FILE = "triage.json"
NOTE_MAX = 80

# what to read for facts, best first; never corporate or lifestyle pages, never another project's page
READ_RANK = ("legal", "price", "floor_plan", "master_plan", "location_map", "amenities", "specs", "text", "cover", "other")
NEVER_READ = ("corporate", "lifestyle")

SYSTEM = "You label the pages of a real-estate brochure from a contact sheet. Reply with JSON only."
PROMPT = (
    "This contact sheet shows pages {first}-{last} of an Indian real-estate project brochure, each small, with its page number "
    "in a yellow box at its top-left corner. Label EVERY page {first} to {last}. kind is one of: cover (title page of THIS "
    "project), corporate (the developer's company, history, awards, sustainability, management, other cities), lifestyle "
    "(stock photos where a person, hands or an object fill the picture, or a city view that does not show the project), "
    "render (a picture of this project's building, facade, lobby, clubhouse, pool, or a furnished flat interior or balcony: "
    "brochures caption these small \"(CGI)\"; a polished interior of a home is a render even with a person in it), "
    "master_plan (site layout of the whole project), floor_plan (typical floor or unit "
    "plans with room sizes), location_map (map, connectivity, distances or travel minutes), amenities (list or legend of "
    "amenities), specs (specifications: flooring, fittings), price (prices, payment plan, offer), legal (RERA registration "
    "numbers, disclaimer, small print), text (other text about this project), other. other_project: true when the page shows "
    "a DIFFERENT project or the developer's portfolio (other buildings, other cities, \"our landmarks\"). cgi: true when the "
    "page is labelled CGI, artist's impression or render, or is clearly a computer render. note: at most 8 words on what "
    "the page shows. Reply: {{\"pages\": [{{\"page\": {first}, \"kind\": \"cover\", \"other_project\": false, \"cgi\": false, "
    "\"note\": \"...\"}}]}}"
)


# ---- the contact sheets ---------------------------------------------------------------------------------------------------
def _font(size: int):
    from PIL import ImageFont
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow before 10.1: the small bitmap font
        return ImageFont.load_default()


def batches(n: int, per: int = SHEET_MAX) -> List[List[int]]:
    """Page numbers (from 1) split into even sheets of at most `per`: 35 -> 1-18, 19-35."""
    if n <= 0:
        return []
    k = math.ceil(n / per)
    size = math.ceil(n / k)
    return [list(range(a, min(a + size, n + 1))) for a in range(1, n + 1, size)]


def contact_sheet(paths: Sequence[str], numbers: Sequence[int]) -> Optional[bytes]:
    """The pages as one JPEG grid with their numbers drawn on, or None when no page opens."""
    from PIL import Image, ImageDraw
    thumbs = []
    for p, n in zip(paths, numbers):
        try:
            im = Image.open(p)
            im.draft("RGB", (600, 600))   # a JPEG decodes small: fast for a 35-page brochure
            thumbs.append((n, im.convert("RGB")))
        except Exception:
            continue
    if not thumbs:
        return None
    aspect = max(0.3, min(3.0, sum(im.height / max(1, im.width) for _, im in thumbs) / len(thumbs)))  # height / width
    cols = len(thumbs)
    for c in range(2, len(thumbs) + 1):   # the fewest columns (largest pages) that keep the sheet under SHEET_H_MAX
        cw = (SHEET_W - GAP * (c + 1)) / c
        if math.ceil(len(thumbs) / c) * (cw * aspect + GAP) + GAP <= SHEET_H_MAX:
            cols = c
            break
    cw = int((SHEET_W - GAP * (cols + 1)) / cols)
    ch = int(cw * aspect)
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (SHEET_W, rows * (ch + GAP) + GAP), (40, 40, 40))
    draw = ImageDraw.Draw(sheet)
    font = _font(max(20, min(LABEL_PX, cw // 4)))
    for i, (n, im) in enumerate(thumbs):
        im.thumbnail((cw, ch))
        x = GAP + (i % cols) * (cw + GAP)
        y = GAP + (i // cols) * (ch + GAP)
        sheet.paste(im, (x + (cw - im.width) // 2, y + (ch - im.height) // 2))
        label = str(n)
        box = draw.textbbox((0, 0), label, font=font)
        w, h = box[2] - box[0], box[3] - box[1]
        draw.rectangle((x, y, x + w + 12, y + h + 12), fill=(255, 221, 0), outline=(0, 0, 0), width=2)
        draw.text((x + 6 - box[0], y + 6 - box[1]), label, fill=(0, 0, 0), font=font)
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=82)
    return buf.getvalue()


# ---- the labels ----------------------------------------------------------------------------------------------------------
def _flag(v: Any) -> bool:
    return v is True or (isinstance(v, str) and v.strip().lower() in ("true", "yes"))


def clean(data: Any, allowed: Iterable[int]) -> Dict[int, Dict[str, Any]]:
    """The model's labels for pages on the sheet, in the contract's shape; anything else is dropped."""
    allowed = set(allowed)
    items = data.get("pages") if isinstance(data, dict) else None
    out: Dict[int, Dict[str, Any]] = {}
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        try:
            n = int(it.get("page"))
        except (TypeError, ValueError):
            continue
        if n not in allowed or n in out:
            continue
        kind = str(it.get("kind") or "").strip().lower().replace(" ", "_").replace("-", "_")
        kind = {"specifications": "specs", "pricing": "price", "floorplan": "floor_plan", "masterplan": "master_plan",
                "map": "location_map", "disclaimer": "legal"}.get(kind, kind)
        out[n] = {"kind": kind if kind in KINDS else "other", "other_project": _flag(it.get("other_project")),
                  "cgi": _flag(it.get("cgi")), "note": " ".join(str(it.get("note") or "").split())[:NOTE_MAX]}
    return out


async def _ask(client: Any, image: bytes, prompt: str) -> Optional[Dict[str, Any]]:
    ask = getattr(client, "ask", None)
    if ask is None:
        return None
    return await ask([image], prompt, SYSTEM, max_tokens=REPLY_TOKENS, retry=True)


async def triage(page_jpgs: List[str]) -> Dict[int, Dict[str, Any]]:
    """{page: {"kind", "other_project", "cgi", "note"}} for the pages the model labelled; {} without a model. Never raises."""
    try:
        from app.modules.photoquality.vision_review import default_clients
        clients = default_clients()
    except Exception:
        return {}
    if not clients or not page_jpgs:
        return {}
    out: Dict[int, Dict[str, Any]] = {}
    for nums in batches(len(page_jpgs)):
        try:
            sheet = await asyncio.to_thread(contact_sheet, [page_jpgs[n - 1] for n in nums], nums)
        except Exception as e:
            log.info("brochure triage: contact sheet failed (%s)", type(e).__name__)
            continue
        if not sheet:
            continue
        prompt = PROMPT.format(first=nums[0], last=nums[-1])
        for client in clients:   # in order until one answers; a busy key passes to the next
            try:
                labels = clean(await _ask(client, sheet, prompt), nums)
            except Exception as e:
                log.info("brochure triage via %s failed (%s)", getattr(client, "model", "?"), type(e).__name__)
                continue
            if len(labels) >= max(1, len(nums) // 2):   # a reply that skips most pages is not trusted; try the next reader
                out.update(labels)
                break
    return out


# ---- kept beside the pages -----------------------------------------------------------------------------------------------
def save(out_dir: Path, triage: Dict[int, Dict[str, Any]], source: str = "") -> None:
    """triage.json in the brochure's page directory (`source`: e.g. the PDF's hash, checked by `load`). Never raises."""
    try:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        body = {"source": source, "pages": {str(k): v for k, v in sorted(triage.items())}}
        (Path(out_dir) / FILE).write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as e:
        log.info("brochure triage: not saved (%s)", type(e).__name__)


def load(out_dir: Path, source: str = "") -> Dict[int, Dict[str, Any]]:
    """The saved labels, {} when there are none (or, with `source`, when they were made from another file)."""
    try:
        body = json.loads((Path(out_dir) / FILE).read_text(encoding="utf-8"))
        if source and body.get("source") != source:
            return {}
        pages = body.get("pages") or {}
        return {int(k): v for k, v in pages.items() if isinstance(v, dict) and v.get("kind") in KINDS}
    except Exception:
        return {}


def read_order(triage: Dict[int, Dict[str, Any]], n_pages: int) -> List[int]:
    """Pages worth reading for facts, best first: one page of each useful kind in READ_RANK order (so a budget of a few pages
    still covers the RERA page, a floor plan, the master plan and the map), then the rest of them, then pages the model did
    not label, then this project's renders. Never corporate or lifestyle pages, never another project's. Without labels:
    every page in order (the first pages, as before)."""
    if not triage:
        return list(range(1, n_pages + 1))
    ranked: Dict[str, List[int]] = {k: [] for k in READ_RANK}
    renders, unknown = [], []
    for n in range(1, n_pages + 1):
        t = triage.get(n)
        if t is None:
            unknown.append(n)
            continue
        if t.get("other_project") or t.get("kind") in NEVER_READ:
            continue
        if t.get("kind") == "render":
            renders.append(n)
        else:
            ranked.get(t.get("kind"), ranked["other"]).append(n)
    first = [ranked[k][0] for k in READ_RANK if ranked[k]]
    rest = [n for k in READ_RANK for n in ranked[k][1:]]
    return first + rest + unknown + renders
