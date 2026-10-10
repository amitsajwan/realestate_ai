"""The listing's project files (an agent's own: the builder's brochure PDF and walkthrough video) read into pictures and
claims, during 'Start marketing' (jobs.MarketingRuns).

    brochure  pages -> JPEGs under <run>/brochure/ (they join the post cards' picture pool, blurred like video stills);
              the vision model reads the first pages into short claims
    video     the presenter's words (video_director.transcribe) -> short claims by the LLM

Claims are the BUILDER's, never our facts: they are stored on the listing as `file_claims` and the assistant states them as
"the builder's brochure says ..." (knowledge.grounding.listing_grounding). Hype, phone numbers and invented numbers are
dropped by the post checks; a brochure without a MahaRERA number is flagged for Studio."""
import asyncio
import base64
import io
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)

MAX_PAGES = 10          # pages rendered into pictures
READ_PAGES = 4          # pages the vision model reads for claims (each page costs ~2k tokens)
PAGE_W = 1080
MAX_CLAIMS = 25        # a 4-page brochure: travel times alone fill a dozen
CLAIM_MAX_CHARS = 160
RERA = re.compile(r"\bP\d{11}\b", re.I)
PHONE = re.compile(r"(?:\d[\s-]?){8,}")
SALES_PROBLEMS = ("hype word", "prediction", "promise", "claim not in facts")
INVEST = re.compile(r"\b(investment|returns?|appreciation|profit|earning)\b|गुंतवणूक|गुंतवणुकी|कमाई|परतावा|निवेश|मुनाफ", re.I)

READ_PROMPT = (
    "These are pages of a real-estate project brochure (India). List what the BUILDER claims about the project, one short "
    "plain sentence each, in English: location and distances, land area, plot or flat sizes, roads, water, power, amenities, "
    "approvals, prices or offers as written. Copy numbers exactly as printed. Text may be in Marathi or Hindi: write "
    "place names as they are known in English, for example शिक्रापूर Shikrapur, मळठण Malthan, रांजणगाव Ranjangaon, चाकण "
    "Chakan, शिरूर Shirur, लोणी काळभोर Loni Kalbhor, राजगुरूनगर Rajgurunagar, वाघोली Wagholi, सणसवाडी Sanaswadi; a name "
    "you cannot read, leave out rather than guess. Leave out slogans and adjectives (dream, best, "
    "safe investment, high returns). Copy any MahaRERA registration number (P followed by 11 digits) exactly, or \"\". Reply "
    'with JSON only: {"claims": ["..."], "rera_no": "..."}'
)
VIDEO_SYSTEM = (
    "You summarise what a presenter says in a real-estate site video, as the builder's claims. Reply with JSON only."
)
VIDEO_USER = (
    "Transcript (may have speech-to-text errors; Marathi/Hindi/English):\n{text}\n\nList what is claimed about the project, "
    "one short plain sentence each, in English: location and distances, plot sizes, roads, water, power, security, "
    "amenities, paperwork. Copy numbers as spoken. Leave out offers tied to a festival or date, slogans, adjectives, phone "
    'numbers. Reply: {{"claims": ["..."]}}'
)


# ---- the brochure -------------------------------------------------------------------------------------------------------
def pdf_pages(pdf: Path, out_dir: Path, max_pages: int = MAX_PAGES) -> List[str]:
    """Each page (up to max_pages) as a JPEG PAGE_W wide in out_dir/pageNN.jpg (earlier pages there are cleared)."""
    import pypdfium2 as pdfium
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("page*.jpg"):
        old.unlink(missing_ok=True)
    doc = pdfium.PdfDocument(str(pdf))
    out = []
    try:
        for i in range(min(len(doc), max_pages)):
            page = doc[i]
            scale = PAGE_W / max(1.0, page.get_width())
            img = page.render(scale=scale).to_pil().convert("RGB")
            p = out_dir / f"page{i:02d}.jpg"
            img.save(p, "JPEG", quality=85)
            out.append(str(p))
    finally:
        doc.close()
    return out


def pdf_text(pdf: Path, max_pages: int = MAX_PAGES) -> str:
    """The text layer (often thin in designed brochures: most words are drawn as pictures)."""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf))
    try:
        return "\n".join(doc[i].get_textpage().get_text_range() for i in range(min(len(doc), max_pages)))
    finally:
        doc.close()


async def read_pages(pages: List[str]) -> Dict[str, Any]:
    """{"claims": [...], "rera_no": str} read by the vision model from the first READ_PAGES pages, or {} without one."""
    from app.modules.photoquality.vision_review import default_clients, parse_reply
    from PIL import Image
    if not pages:
        return {}
    images: List[Dict[str, Any]] = []
    for p in pages[:READ_PAGES]:
        im = Image.open(p).convert("RGB")
        im.thumbnail((900, 1400))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        images.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}})
    # One page per request: a page is ~2k tokens and a free key allows ~7k a minute, so several pages in one request fail
    # even on a fresh key. Each page goes to the readers in order until one answers; a busy key passes to the next.
    clients = default_clients()
    claims: List[str] = []
    rera_no = None
    weak = False
    for page in images:
        for client in clients:
            body = {"model": client.model, "temperature": 0, "max_completion_tokens": 1200,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": READ_PROMPT}, page]}]}
            try:
                async with httpx.AsyncClient(timeout=60.0) as c:
                    r = await c.post(client.url, json=body, headers={"Authorization": f"Bearer {client.api_key}"})
                r.raise_for_status()
                data = parse_reply(r.json()["choices"][0]["message"]["content"] or "") or {}
            except Exception as e:
                resp = getattr(e, "response", None)
                log.info("project files: brochure read via %s failed (%s%s)", client.model, type(e).__name__,
                         f" HTTP {resp.status_code}: {resp.text[:200]}" if resp is not None else "")
                continue
            trusted = getattr(client, "trusted", True)
            claims += [x for x in data.get("claims") or [] if x not in claims]
            if trusted:  # a small model makes up registration numbers: only a trusted reader's is kept
                rera_no = rera_no or data.get("rera_no")
            weak = weak or not trusted
            break
    if claims:
        return {"claims": claims, "rera_no": rera_no, "weak": weak}
    return {}


# ---- the video ----------------------------------------------------------------------------------------------------------
async def video_claims(speech: List[Dict[str, Any]], llm) -> List[str]:
    text = " ".join(s.get("text", "") for s in speech).strip()
    if not text or llm is None:
        return []
    try:
        data = await llm.json(VIDEO_SYSTEM, VIDEO_USER.format(text=text[:4000])) or {}
    except Exception:
        return []
    return clean_claims(data.get("claims"))


# ---- shared -------------------------------------------------------------------------------------------------------------
def clean_claims(raw) -> List[str]:
    """Short, plain claims only: no phone numbers, no hype (the post checks), no duplicates."""
    from app.modules.creative.guards import problems_in
    out: List[str] = []
    for c in raw or []:
        c = re.sub(r"\s+", " ", str(c or "")).strip().strip('"')
        if not c or len(c) > CLAIM_MAX_CHARS or PHONE.search(c) or INVEST.search(c):
            continue
        # sales claims ("safe investment", "assured", "high returns") and hype are dropped; the builder's own numbers stay
        # (they are claims by definition, so the number check against our facts does not apply)
        if any(p.startswith(SALES_PROBLEMS) for p in problems_in(c, "")):
            continue
        if c.lower() not in (x.lower() for x in out):
            out.append(c)
        if len(out) >= MAX_CLAIMS:
            break
    return out


def brochure_pdf(listing: dict, uploads_dir: Path) -> Optional[Path]:
    """The listing's first uploaded brochure (media kind 'document', a PDF under <uploads>/documents), or None."""
    root = (Path(uploads_dir) / "documents").resolve()
    docs = sorted(((m.get("order") or 0, i, m) for i, m in enumerate(listing.get("media") or []) if m.get("kind") == "document"),
                  key=lambda t: (t[0], t[1]))
    for _, _, m in docs:
        mm = re.search(r"/uploads/documents/([A-Za-z0-9._-]+\.pdf)$", str(m.get("url") or ""), re.I)
        p = (root / mm.group(1)).resolve() if mm else None
        if p and p.parent == root and p.is_file():
            return p
    return None


def brochure_url(listing: dict, pdf: Path) -> Optional[str]:
    """The media URL of the brochure `pdf` on the listing (for matching claims already read to the file)."""
    for m in listing.get("media") or []:
        if m.get("kind") == "document" and str(m.get("url") or "").split("?")[0].lower().endswith("/" + pdf.name.lower()):
            return m.get("url")
    return None


def claims_for(listing: dict, pdf: Path) -> Optional[Dict[str, Any]]:
    """The claims already kept on the listing for this very brochure file (read by the AI draft or an earlier run)."""
    fc = listing.get("file_claims") if isinstance(listing.get("file_claims"), dict) else {}
    url = str(fc.get("brochure_url") or "").split("?")[0]
    if not fc.get("brochure") or not url.lower().endswith("/" + pdf.name.lower()):
        return None
    rera = fc.get("rera_on_brochure")
    return {"claims": list(fc["brochure"]), "rera_no": rera, "rera_missing": not rera, "read_by_ai": True, "weak": False}


async def read_brochure(pdf: Path, out_dir: Path) -> Dict[str, Any]:
    """{"pages": [jpg...], "claims": [...], "rera_no": str|None, "rera_missing": bool}. Never raises."""
    try:
        pages = await asyncio.to_thread(pdf_pages, pdf, out_dir)
    except Exception as e:
        log.warning("project files: could not render the brochure (%s)", type(e).__name__)
        return {"pages": [], "claims": [], "rera_no": None, "rera_missing": False, "error": "The PDF could not be read."}
    read = await read_pages(pages)
    try:
        text = await asyncio.to_thread(pdf_text, pdf)
    except Exception:
        text = ""
    found = RERA.search(f"{read.get('rera_no') or ''} {text}")
    return {"pages": pages, "claims": clean_claims(read.get("claims")), "rera_no": found.group(0).upper() if found else None,
            "rera_missing": not found, "read_by_ai": bool(read), "weak": bool(read.get("weak"))}


async def save_claims(listings, listing_id: str, *, brochure: Optional[List[str]] = None, video: Optional[List[str]] = None,
                      rera_on_brochure: Optional[str] = None, now: Optional[datetime] = None,
                      brochure_url: Optional[str] = None) -> None:
    """Keep what was read on the listing (`file_claims`), for the assistant and for Studio. Only the parts given change."""
    changes: Dict[str, Any] = {"file_claims.updated_at": now or datetime.utcnow()}
    if brochure is not None:
        changes["file_claims.brochure"] = brochure
        changes["file_claims.rera_on_brochure"] = rera_on_brochure
        changes["file_claims.brochure_url"] = brochure_url
    if video is not None:
        changes["file_claims.video"] = video
    await listings.update_one({"_id": listing_id}, {"$set": changes})
