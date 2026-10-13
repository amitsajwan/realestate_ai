"""The brochure document: every brochure PDF read ONCE into one JSON every reader uses (the AI draft, Start marketing).

    pages   -> each page's words: the PDF's own text layer, or, for a page drawn as a picture (big builders' brochures are
               mostly pictures: Lodha Camelot has text on 1 page of 35), the words OCR finds on it (tesseract, on this
               server, no model and no network). OCR words below MIN_CONF are dropped: a photo gives noise, not text.
    kind    -> what is on offer, by rules on those words: flats ("3 Bed Residence", "2 BHK", "typical floor plan") or plots
               ("NA plots", "guntha"), with the line that says it. None when the words do not say it plainly.

Kept as <uploads>/brochure_docs/<sha256>.json, so one file is read once whatever listing or run asks. Reading takes a
minute or two for a picture brochure (2 pages at a time, at low CPU priority), so it starts in the background when the PDF
is uploaded (start); a reader that needs it waits a bounded time (get) and goes on with the text layer when it is not ready.
The PDF is untrusted input: pdfium reads it without forms; its words are data, never instructions."""
import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import brochure_parse as bp

log = logging.getLogger(__name__)

VERSION = 1
FOLDER = "brochure_docs"
MAX_PAGES = 40
OCR_LONG_SIDE = 2000          # px: small print (addresses, MahaRERA numbers, room sizes) needs it
OCR_LANGS = os.environ.get("BROCHURE_OCR_LANGS", "eng+mar")   # Marathi plot brochures are all Devanagari; "eng" is twice as fast
OCR_WORKERS = 2
OCR_PAGE_TIMEOUT = 60
READ_BUDGET_S = 420.0         # past it the pages not yet read stay without words
MIN_CONF = 60                 # tesseract's word confidence (0-100); picture noise scores lower
STALE_S = 900                 # a ".reading" marker older than this is a reader that died
_tasks: set = set()

_FLAT = re.compile(r"\b\d(?:\.5)?\s*(?:BHK|B\.H\.K)\b|\b\d\s*bed(?:room)?s?\s+(?:residence|apartment|home|flat)s?\b|"
                   r"\b(?:apartments?|flats?|penthouses?)\b|\btypical\s+floor\s+plan\b|\b(?:tower|wing)\s+[A-Z0-9IVX]{1,3}\b", re.I)
_PLOT = re.compile(r"\b(?:NA\s+|bungalow\s+|residential\s+)?plots?\b(?!\s+(?:no|area\s+statement|boundary))|\bplotted\b|"
                   r"\bguntha\b|\bगुंठा\b|\bप्लॉट\b", re.I)


def ocr_ready() -> bool:
    return shutil.which("tesseract") is not None


def folder(uploads_dir: Any) -> Path:
    return Path(uploads_dir) / FOLDER


def sha256_of(pdf: Path) -> str:
    h = hashlib.sha256()
    with open(pdf, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ocr_words(tsv: str) -> str:
    """Tesseract TSV -> the confident words, one line per text line it found."""
    lines: Dict[Tuple[str, str, str], List[str]] = {}
    for row in tsv.splitlines()[1:]:
        c = row.split("\t")
        if len(c) < 12 or not c[11].strip():
            continue
        try:
            conf = float(c[10])
        except ValueError:
            continue
        word = c[11].strip()
        if conf >= MIN_CONF and re.search(r"[A-Za-z0-9ऀ-ॿ]", word):
            lines.setdefault((c[2], c[3], c[4]), []).append(word)
    out = []
    for words in lines.values():
        line = " ".join(words)
        # a line of one- and two-letter scraps is a photo's texture, not words
        if sum(len(w) >= 3 for w in words) >= max(1, len(words) // 2):
            out.append(line)
    return "\n".join(out)


def _ocr_page(png: Path) -> str:
    nice = ["nice", "-n", "10"] if shutil.which("nice") else []
    r = subprocess.run(nice + ["tesseract", str(png), "-", "-l", OCR_LANGS, "--psm", "11", "tsv"],
                       capture_output=True, text=True, timeout=OCR_PAGE_TIMEOUT,
                       env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    return _ocr_words(r.stdout) if r.returncode == 0 else ""


def read(pdf: Path) -> Dict[str, Any]:
    """The document of one PDF (blocking: run it in a thread). Never raises: `error` says what went wrong."""
    import pypdfium2 as pdfium

    from .brochure import _pdfium_lock

    start = time.monotonic()
    doc: Dict[str, Any] = {"version": VERSION, "pages": [], "ocr": ocr_ready(), "error": None}
    todo: List[Tuple[int, Path]] = []
    tmp = Path(tempfile.mkdtemp(prefix="brochure-"))
    try:
        with _pdfium_lock:
            try:
                pdf_doc = pdfium.PdfDocument(str(pdf))
            except Exception:
                doc["error"] = "The PDF could not be opened."
                return doc
            try:
                for i in range(min(len(pdf_doc), MAX_PAGES)):
                    page = pdf_doc[i]
                    try:
                        tp = page.get_textpage()
                        text = bp.clean(tp.get_text_range())
                        tp.close()
                        entry = {"n": i + 1, "source": "pdf", "text": text}
                        if bp.image_only(text):
                            entry.update(source="none", text="")
                            if doc["ocr"]:
                                w, h = page.get_size()
                                png = tmp / f"p{i + 1}.png"
                                page.render(scale=OCR_LONG_SIDE / max(w, h, 1.0), may_draw_forms=False).to_pil() \
                                    .convert("L").save(png)
                                todo.append((i + 1, png))
                        doc["pages"].append(entry)
                    finally:
                        page.close()
            finally:
                pdf_doc.close()
        if todo:
            with ThreadPoolExecutor(OCR_WORKERS) as pool:
                futures = {n: pool.submit(_ocr_page, png) for n, png in todo}
                for n, fut in futures.items():
                    left = READ_BUDGET_S - (time.monotonic() - start)
                    try:
                        text = fut.result(timeout=max(left, 1.0))
                    except Exception as e:
                        log.info("brochure doc: page %s not read (%s)", n, type(e).__name__)
                        continue
                    if not bp.image_only(text):
                        doc["pages"][n - 1].update(source="ocr", text=text)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    doc["kind"] = offer_kind(doc)
    doc["seconds"] = round(time.monotonic() - start, 1)
    return doc


def offer_kind(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """{"kind": "apartment"|"plot", "quote", "page", "flat_pages", "plot_pages"} when the brochure's words say plainly what
    is on offer (one side on 2+ pages and at least 3 times the other's), else None."""
    flat: Dict[int, str] = {}
    plot: Dict[int, str] = {}
    for p in (doc or {}).get("pages") or []:
        text = p.get("text") or ""
        for rx, hits in ((_FLAT, flat), (_PLOT, plot)):
            m = rx.search(text)
            if m:
                hits[p["n"]] = _line(text, m.start())
    for kind, mine, other in (("apartment", flat, plot), ("plot", plot, flat)):
        if len(mine) >= 2 and len(mine) >= 3 * len(other):
            first = min(mine)
            return {"kind": kind, "quote": mine[first], "page": first, "flat_pages": sorted(flat), "plot_pages": sorted(plot)}
    return None


def _line(text: str, at: int) -> str:
    s, e = text.rfind("\n", 0, at) + 1, text.find("\n", at)
    return text[s:e if e >= 0 else len(text)].strip()[:200]


def page_texts(doc: Optional[Dict[str, Any]]) -> List[str]:
    return [p.get("text") or "" for p in (doc or {}).get("pages") or []]


def full_text(doc: Optional[Dict[str, Any]]) -> str:
    return "\n".join(t for t in page_texts(doc) if t)


def candidates(doc: Optional[Dict[str, Any]]) -> List[bp.Candidate]:
    """The brochure_parse rules over every page with words (text layer or OCR). OCR pages are prose broken into scraps, so
    their amenities are only the known names (bp.KNOWN_AMENITIES) and their lines are never taken as specifications; a
    project name the rules miss (it is the cover's logo) is the name the pages repeat."""
    pages = [(p["n"], p["text"]) for p in (doc or {}).get("pages") or [] if p.get("text")]
    ocr = {p["n"]: p["text"] for p in (doc or {}).get("pages") or [] if p.get("source") == "ocr"}
    out: List[bp.Candidate] = []
    for c in bp.extract(pages):
        if c.page in ocr and c.key == "specifications":
            continue
        if c.page in ocr and c.key == "project_name" and (   # a cover's slogan word ("उत्तम") or a plan's heading
                len(str(c.value).split()) < 2 or sum(bp.norm(str(c.value)) in bp.norm(t) for _, t in pages) < 2):
            continue
        if c.page in ocr and c.key == "amenities":
            c = bp._amenities(c.page, ocr[c.page], "other")
            if c is None:
                continue
        out.append(c)
    if not any(c.key == "project_name" for c in out):
        name = repeated_name(pages)
        if name:
            out.insert(0, bp.Candidate("project_name", name[0], name[1], name[2]))
    return out


def claims(doc: Optional[Dict[str, Any]]) -> List[str]:
    """Plain claims from the rules' findings, for when no vision model read the brochure (files.read_brochure): what is on
    offer, its configurations, land, amenities and site address, in the builder's own values."""
    out: List[str] = []
    found = {c.key: c for c in candidates(doc)}
    kind = ((doc or {}).get("kind") or {}).get("kind")
    configs = found.get("configurations")
    if configs and configs.value:
        v = list(configs.value)
        out.append("The project offers " + (v[0] if len(v) == 1 else ", ".join(v[:-1]) + " and " + v[-1])
                   + (" apartments." if kind == "apartment" else " homes."))
    elif kind == "plot":
        out.append("The project offers plots.")
    if found.get("land_area"):
        out.append(f"The project is spread over {found['land_area'].value}.")
    if found.get("amenities") and found["amenities"].value:
        out.append("Amenities include " + ", ".join(str(x) for x in found["amenities"].value[:8]) + ".")
    if found.get("address"):
        out.append(f"The site address is {found['address'].value}.")
    return out


def project_name(doc: Optional[Dict[str, Any]]) -> Optional[str]:
    return next((str(c.value) for c in candidates(doc) if c.key == "project_name"), None)


_PHRASE = re.compile(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,2})\b")
_NOT_NAME = {"plan", "floor", "tower", "address", "bedroom", "master", "residence", "residences", "typical", "unit", "road",
             "main", "pune", "maharashtra", "india", "lawn", "track", "sports", "design", "site", "corporate", "legend",
             "artist", "impression", "landscape", "architectural", "club", "house", "kids", "pool", "staff", "room", "deck",
             "living", "dining", "kitchen", "toilet", "study", "foyer", "global", "science", "estate", "real"}


def repeated_name(pages: List[Tuple[int, str]]) -> Optional[Tuple[str, int, str]]:
    """(name, first page, its line): a capitalised two- or three-word phrase on 3+ pages that is no heading word or Pune
    place ("Lodha Camelot", repeated through the prose), or None."""
    from app.core import pune_places

    where: Dict[str, List[Tuple[int, str]]] = {}
    for n, text in pages:
        for m in _PHRASE.finditer(text):
            phrase = m.group(1)
            if any(w.lower() in _NOT_NAME for w in phrase.split()):
                continue
            hits = where.setdefault(phrase, [])
            if not any(h[0] == n for h in hits):
                hits.append((n, _line(text, m.start())))
    best = max(where.items(), key=lambda kv: len(kv[1]), default=None)
    if not best or len(best[1]) < 3:
        return None
    low = pune_places._norm(best[0])
    if any(pune_places._named(p, low) for p in pune_places.PLACES):
        return None
    return best[0], best[1][0][0], best[1][0][1]


# ---- the cache ----------------------------------------------------------------------------------------------------------
def _paths(pdf: Path, uploads_dir: Any) -> Tuple[Path, Path]:
    base = folder(uploads_dir)
    sha = sha256_of(pdf)
    return base / f"{sha}.json", base / f"{sha}.reading"


def cached(pdf: Path, uploads_dir: Any) -> Optional[Dict[str, Any]]:
    try:
        path, _ = _paths(pdf, uploads_dir)
        doc = json.loads(path.read_text("utf-8")) if path.is_file() else None
    except Exception:
        return None
    return doc if doc and doc.get("version") == VERSION else None


def _read_and_keep(pdf: Path, uploads_dir: Any) -> Optional[Dict[str, Any]]:
    path, marker = _paths(pdf, uploads_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(str(time.time()))
    try:
        doc = read(pdf)
        doc["sha256"] = path.stem
        if not doc.get("error"):
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(doc, ensure_ascii=False), "utf-8")
            tmp.replace(path)
        log.info("brochure doc %s: %s pages, %s by OCR, kind %s, %ss", path.stem[:12], len(doc["pages"]),
                 sum(p["source"] == "ocr" for p in doc["pages"]), (doc.get("kind") or {}).get("kind"), doc.get("seconds"))
        return doc
    finally:
        marker.unlink(missing_ok=True)


def _someone_reading(pdf: Path, uploads_dir: Any) -> bool:
    try:
        _, marker = _paths(pdf, uploads_dir)
        return marker.is_file() and time.time() - marker.stat().st_mtime < STALE_S
    except Exception:
        return False


def start(pdf: Path, uploads_dir: Any) -> None:
    """Read the PDF in the background (at upload): the draft and Start marketing then find it ready."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    task = loop.create_task(get(pdf, uploads_dir, wait=READ_BUDGET_S + 60))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def get(pdf: Path, uploads_dir: Any, wait: float = 120.0) -> Optional[Dict[str, Any]]:
    """The PDF's document: kept, or read now (or by the process already reading it), waiting at most `wait` seconds.
    None when it is not ready in time (a read started here goes on and is kept for the next reader). Never raises."""
    try:
        doc = await asyncio.to_thread(cached, pdf, uploads_dir)
        if doc:
            return doc
        deadline = time.monotonic() + wait
        if await asyncio.to_thread(_someone_reading, pdf, uploads_dir):
            while time.monotonic() < deadline:
                await asyncio.sleep(3)
                doc = await asyncio.to_thread(cached, pdf, uploads_dir)
                if doc or not await asyncio.to_thread(_someone_reading, pdf, uploads_dir):
                    return doc
            return None
        task = asyncio.ensure_future(asyncio.to_thread(_read_and_keep, pdf, uploads_dir))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
        return await asyncio.wait_for(asyncio.shield(task), max(wait, 0.1))
    except asyncio.TimeoutError:
        return None
    except Exception:
        log.warning("brochure doc: %s could not be read", Path(pdf).name, exc_info=True)
        return None
