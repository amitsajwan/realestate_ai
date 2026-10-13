"""Which of a listing's pictures go on its post cards, and in what order: one ranked pool of the agent's photos, the stills
of its video and the pages of its brochure. Clear, sharp, colourful place shots (site, road, building, plot) first; a
presenter filling the frame, burned-in captions or phone numbers, and text-heavy pages last; near-duplicates (perceptual
hash) of a picture already chosen left out, so neighbouring cards never show the same scene. Pillow only, on thumbnails:
fast, and every failure falls back to a neutral score. Which brochure pages may join the pool at all: brochure_photos."""
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from PIL import Image, ImageFilter, ImageStat

NEAR = 10          # dHash bits (of 64) under which two pictures count as the same scene
PLACE = re.compile(r"plot|site|road|gate|entrance|building|tower|facade|layout|boundary|stones?|green|garden|tree|land|"
                   r"aerial|drone|view|amenit|club|pool|street|signboard|park|open space|construction|interior|room|kitchen",
                   re.I)
PERSON = re.compile(r"presenter|person|man |woman|talking|speaking|selfie|face|host|agent", re.I)
SHOTS_FILE = "shots.json"


def shot_notes(frames_dir: Path) -> Dict[str, dict]:
    """{still file name: what the vision model saw in it} written by video_director.best_frames, or {}."""
    try:
        return json.loads((Path(frames_dir) / SHOTS_FILE).read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _dhash(im: Image.Image) -> int:
    g = im.convert("L").resize((9, 8), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for r in range(8):
        for c in range(8):
            bits = (bits << 1) | (px[r * 9 + c] > px[r * 9 + c + 1])
    return bits


def _measure(path: str) -> Optional[dict]:
    """Sharpness, colourfulness, page-likeness (share of near-white paper) and the perceptual hash of one picture."""
    try:
        with Image.open(path) as im:
            im.draft("RGB", (256, 256))
            im = im.convert("RGB")
            im.thumbnail((192, 192))
    except Exception:
        return None
    g = im.convert("L")
    sharp = ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0] ** 0.5          # ~0 (blurred) .. 60+ (crisp)
    r, gg, b = [list(c.getdata()) for c in im.split()]
    rg = [abs(x - y) for x, y in zip(r, gg)]
    yb = [abs((x + y) / 2 - z) for x, y, z in zip(r, gg, b)]
    n = len(rg) or 1

    def ms(v):
        m = sum(v) / n
        return m, (sum((x - m) ** 2 for x in v) / n) ** 0.5
    (mrg, srg), (myb, syb) = ms(rg), ms(yb)
    colour = (srg ** 2 + syb ** 2) ** 0.5 + 0.3 * (mrg ** 2 + myb ** 2) ** 0.5           # Hasler-Suesstrunk, ~0..100
    hist = g.histogram()
    paper = sum(hist[235:]) / n                                                          # brochure text pages are mostly paper
    busy = sum(1 for v in g.filter(ImageFilter.FIND_EDGES).getdata() if v > 40) / n       # line drawings, plans, tables
    blobs = _text_blobs(path) if paper > 0.15 else 0
    return {"sharp": sharp, "colour": colour, "paper": paper, "busy": busy, "blobs": blobs, "hash": _dhash(im)}


def _text_blobs(path: str) -> int:
    """Small dark connected shapes on a light page (letters), counted on a 384 px copy: many of them is printed text,
    without OCR. Only asked of pictures that are partly white paper (in a photo, leaves and windows look the same)."""
    try:
        with Image.open(path) as im:
            im.draft("L", (512, 512))
            g = im.convert("L")
            g.thumbnail((384, 384))
    except Exception:
        return 0
    w, h = g.size
    dark = bytes(1 if v < 100 else 0 for v in g.getdata())
    seen, count = bytearray(w * h), 0
    for i in range(w * h):
        if dark[i] and not seen[i]:
            stack, seen[i], size = [i], 1, 0
            while stack:
                j = stack.pop()
                size += 1
                x = j % w
                for k in (j - 1 if x > 0 else -1, j + 1 if x < w - 1 else -1, j - w, j + w):
                    if 0 <= k < w * h and dark[k] and not seen[k]:
                        seen[k] = 1
                        stack.append(k)
            if 3 <= size <= 120:
                count += 1
    return count


def score(path: str, m: dict, own: bool, note: Optional[dict]) -> float:
    """Higher is a better card picture."""
    s = min(m["sharp"], 40) / 40 * 3 + min(m["colour"], 60) / 60 * 3
    s -= 10 * max(0.0, m["paper"] - 0.25)                    # a page that is mostly white paper is text, not a place
    s -= 20 * max(0.0, m.get("busy", 0) - 0.22)              # a plan, a line drawing or a table: no card text reads on it
    s -= min(5.0, m.get("blobs", 0) / 60)                    # a page of printed text
    p = Path(path)
    if own:
        s += 2                                               # the agent's own photo of the property
    if p.parent.name == "brochure":
        s -= 1                                               # a brochure page usually carries the builder's words
    if note:
        what = str(note.get("what") or "")
        if PLACE.search(what):
            s += 2
        if note.get("person_on_screen") or (PERSON.search(what) and not PLACE.search(what)):
            s -= 4
        if note.get("text_on_screen"):
            s -= 2
        if note.get("phone_on_screen"):
            s -= 6
        try:
            s += (float(note.get("score") or 5) - 5) * 0.3
        except (TypeError, ValueError):
            pass
    return s


def _far(h: int, chosen: Iterable[int]) -> bool:
    return all(bin(h ^ c).count("1") > NEAR for c in chosen)


def rank(pool: Sequence[str], own: Iterable[str] = (), notes: Optional[Dict[str, dict]] = None) -> List[str]:
    """`pool` best first, near-duplicates of an earlier pick left out (a picture that cannot be read keeps its place at the
    end). Order of equal scores: the given order."""
    own, notes = set(map(str, own)), notes or {}
    scored, unread = [], []
    for i, p in enumerate(pool):
        m = _measure(p)
        if m is None:
            unread.append(p)
            continue
        note = notes.get(Path(p).name) if Path(p).parent.name == "frames" else None
        scored.append((-score(p, m, p in own, note), i, p, m["hash"]))
    scored.sort()
    out, hashes = [], []
    for _, _, p, h in scored:
        if _far(h, hashes):
            out.append(p)
            hashes.append(h)
    return out + unread


# ---- which brochure pages may be card photos ---------------------------------------------------------------------------
# A big builder's brochure is mostly pages that must never stand for this project on a post: the builder's other projects,
# corporate and award pages, lifestyle stock photos (a model by a pool, a butler, a handshake), legal text. Its renders
# (CGI) may only be shown labelled "Artist's impression", which a photo card cannot do: they reach posts only through the
# brochure kit (brochure.py: kind "render", pending until the agent says "use", then campaign.first_look labels them).
# Plans and the location map go the same way as kit images. So a page is a card photo only when the vision triage
# (brochure_triage, triage.json next to the pages) calls it something else and not CGI, not another project.
PHOTO_KINDS = ("amenities", "other")                        # triage kinds a brochure page may be a card photo as
KIT_KINDS = ("floor_plan", "master_plan", "location_map")   # triage kinds that become kit images (with "render")
NEVER_KINDS = ("cover", "corporate", "lifestyle", "legal", "text", "price", "specs")
MOSTLY_IMAGES = 0.5    # share of image-only pages above which, without triage, no page of a brochure is a card photo
NO_PAGES_NOTE = ("Most pages of this brochure are pictures without text, and they could not be checked one by one, so none "
                 "of them is used as a photo on your posts or reels: a builder's brochure mixes in its other projects and "
                 "stock photos. Posts use your own photos and video. Floor plans and renders appear only when you choose "
                 "\"use\" on them here.")
TRIAGE_NOTE = ("Pages were sorted by what they show: the builder's other projects, company pages, stock lifestyle photos and "
               "text pages are never used on posts. Renders are shown only labelled \"Artist's impression\", and plans and "
               "maps only when you choose \"use\".")


def load_triage(*dirs: Any) -> Dict[int, dict]:
    """{page number (from 1): {kind, other_project, cgi, note}} from brochure_triage (triage.json in the first of `dirs`
    that has one), or {} when there is none or the triage module is not deployed."""
    try:
        from . import brochure_triage
    except ImportError:
        return {}
    for d in dirs:
        if not d:
            continue
        try:
            got = brochure_triage.load(Path(d)) or {}
        except Exception:
            got = {}
        if got:
            out = {}
            for k, v in got.items():
                try:
                    out[int(k)] = dict(v or {})
                except (TypeError, ValueError):
                    continue
            if out:
                return out
    return {}


def page_use(entry: Optional[dict]) -> str:
    """What a triaged brochure page may be: "photo" (a card photo), "render" (a kit image, always labelled "Artist's
    impression"), "plan" (a kit image: floor plan, master plan, location map) or "none". An untriaged page is "none"."""
    if not entry or entry.get("other_project"):
        return "none"
    kind = str(entry.get("kind") or "other")
    if kind in KIT_KINDS:
        return "plan"
    if kind in NEVER_KINDS:
        return "none"
    if kind == "render" or entry.get("cgi"):
        return "render"
    return "photo" if kind in PHOTO_KINDS else "none"


def page_number(path: Any) -> Optional[int]:
    """The brochure page (from 1) a page picture shows: files.pdf_pages' pageNN.jpg counts from 0, the kit's pN.jpg / iN.jpg
    from 1."""
    name = Path(str(path)).name
    m = re.fullmatch(r"page(\d+)\.jpe?g", name, re.I)
    if m:
        return int(m.group(1)) + 1
    m = re.fullmatch(r"[pi](\d+)\.jpe?g", name, re.I)
    return int(m.group(1)) if m else None


def image_only_share(pdf: Any) -> float:
    """The share of a PDF's pages without a text layer (brochure_parse.image_only); 1.0 when it cannot be read."""
    try:
        import pypdfium2 as pdfium

        from . import brochure_parse as bp
        from .brochure import _pdfium_lock
        with _pdfium_lock:
            doc = pdfium.PdfDocument(str(pdf))
            try:
                n = len(doc)
                if not n:
                    return 1.0
                empty = 0
                for i in range(n):
                    page = doc[i]
                    try:
                        tp = page.get_textpage()
                        empty += bp.image_only(bp.clean(tp.get_text_range()))
                        tp.close()
                    finally:
                        page.close()
                return empty / n
            finally:
                doc.close()
    except Exception:
        return 1.0


def brochure_photos(pages: Sequence[Any], triage: Dict[int, dict], image_share: float) -> tuple:
    """(the brochure page pictures that may be card photos, a note for the agent or ""). With triage: only pages it calls
    "photo" (page_use). Without: none from a brochure that is mostly image-only pages (it could not be checked), every page
    from a text brochure (its text pages are ranked last by `rank`, as before)."""
    pages = [str(p) for p in pages]
    if triage:
        return [p for p in pages if page_use(triage.get(page_number(p) or 0)) == "photo"], TRIAGE_NOTE
    if image_share > MOSTLY_IMAGES:
        return [], NO_PAGES_NOTE
    return pages, ""


def walkthrough_pictures(pool: Sequence[str], keep: int = 5) -> List[str]:
    """Pictures from a run's ranked pool fit for a walkthrough reel when the listing has fewer than 2 photos: readable files,
    text pages left out (a reel scene shows a picture for seconds, full screen)."""
    out = []
    for p in pool:
        if not Path(p).is_file():
            continue
        m = _measure(p)
        if m is None or m["paper"] > 0.55 or m["busy"] > 0.3 or m["blobs"] > 150:
            continue
        out.append(p)
        if len(out) >= keep:
            break
    return out
