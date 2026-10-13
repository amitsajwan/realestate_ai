"""The builder's brochure on the AI draft: read it (text layer + the vision reader's claims, propertyfacts/files.py), pull
the facts it prints, and match the project in OUR MahaRERA register (never live MahaRERA: too slow for a form).

Everything here is the builder's word or the register's: it fills a DRAFT the agent confirms. Nothing is invented: sizes,
prices and numbers only when printed, a registration number only in MahaRERA's form (P + 11 digits or PR/PP/PM + 13 digits, core/rera.py; "Gat No." is land)."""
import asyncio
import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core import pune_places, rera
from app.modules.propertyfacts import files
from app.modules.propertyfacts.registration import CANDIDATES, _words, core

log = logging.getLogger(__name__)

READ_TIMEOUT = 90.0       # the whole brochure read (render + vision); past it the draft goes on with what was read
TEXT_CHARS = 3000         # brochure text handed to the extractors
HIGHLIGHTS = 6            # About.highlights cap
_URL = re.compile(r"/uploads/documents/([A-Za-z0-9._-]+\.pdf)$", re.I)
RERA = rera.SEARCH         # service.py fullmatches a typed number against it
_SQFT = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(?:-|to)?\s*(?:(\d[\d,]*(?:\.\d+)?)\s*)?"
                   r"(sq\.?\s*ft\.?|sqft|square\s*feet|sq\.?\s*m(?:tr|eter|etre)?s?\.?|sqm|square\s*met(?:er|re)s?)", re.I)
_TALUKAS = {t.lower() for t in pune_places.TALUKA_BY_PIN.values()}
_PIN = re.compile(r"(?<!\d)(4[01]\d{4})(?!\d)")


def resolve(url: Optional[str], uploads_dir: Path) -> Optional[Path]:
    """The uploaded brochure behind a /uploads/documents/<name>.pdf URL, only inside uploads/documents; else None."""
    m = _URL.search((url or "").strip().split("?")[0])
    if not m:
        return None
    root = (Path(uploads_dir) / "documents").resolve()
    p = (root / m.group(1)).resolve()
    return p if p.parent == root and p.is_file() else None


def same_file(a: Optional[str], b: Optional[str]) -> bool:
    ma, mb = _URL.search((a or "").split("?")[0]), _URL.search((b or "").split("?")[0])
    return bool(ma and mb and ma.group(1).lower() == mb.group(1).lower())


async def read(url: str, uploads_dir: Path, timeout: float = READ_TIMEOUT) -> Dict[str, Any]:
    """{"text", "claims", "rera_no", "pages", "error"?}. Never raises."""
    pdf = resolve(url, uploads_dir)
    if pdf is None:
        return {"text": "", "claims": [], "rera_no": None, "pages": 0, "error": "The brochure file was not found."}
    out_dir = Path(uploads_dir) / "drafts" / hashlib.sha1(pdf.name.encode()).hexdigest()[:16]
    try:
        text = await asyncio.wait_for(asyncio.to_thread(files.pdf_text, pdf), 20)
    except Exception:
        text = ""
    out: Dict[str, Any] = {"text": text or "", "claims": [], "rera_no": None, "rera_nos": [], "pages": 0}
    try:
        info = await asyncio.wait_for(files.read_brochure(pdf, out_dir), timeout)
    except asyncio.TimeoutError:
        info = {"error": "Reading the brochure took too long; only its text was used."}
    except Exception as e:
        log.warning("ai_listing brochure read failed: %s", type(e).__name__)
        info = {"error": "The brochure could not be read; only its text was used."}
    out["claims"] = list(info.get("claims") or [])
    out["project_name"] = info.get("project_name")
    out["facts"] = dict(info.get("facts") or {})        # structured selling facts as printed (propertyfacts/points.py)
    out["language"] = info.get("language") or "en"
    out["pages"] = len(info.get("pages") or [])
    if info.get("error"):
        out["error"] = info["error"]
    out["rera_nos"] = rera.find_all(f"{info.get('rera_no') or ''} {out['text']}")   # a phased project prints several
    out["rera_no"] = out["rera_nos"][0] if out["rera_nos"] else None
    return out


def extraction_text(agent_text: str, b: Dict[str, Any]) -> str:
    """The agent's words first (they win), then the builder's claims, then the brochure's text layer."""
    parts = [(agent_text or "").strip()]
    if b.get("claims"):
        parts.append("Builder brochure (new project for sale): " + " ".join(c.rstrip(".") + "." for c in b["claims"]))
    if (b.get("text") or "").strip():
        parts.append(re.sub(r"\s+", " ", b["text"]).strip()[:TEXT_CHARS])
    return "\n".join(p for p in parts if p)


def sizes(text: str) -> tuple[Optional[int], Optional[int]]:
    """Smallest and largest printed size in sq ft (sq m converted), plausible plot/flat sizes only."""
    vals: List[int] = []
    for m in _SQFT.finditer(text or ""):
        unit = m.group(3).lower()
        for g in (m.group(1), m.group(2)):
            if not g:
                continue
            try:
                v = float(g.replace(",", ""))
            except ValueError:
                continue
            if "m" in unit.replace("sq", "", 1) and "ft" not in unit:
                v *= 10.764
            if 150 <= v <= 200_000:
                vals.append(int(round(v)))
    return (min(vals), max(vals)) if vals else (None, None)


def in_pune_district(text: str) -> bool:
    low = " " + re.sub(r"[^a-z0-9]+", " ", (text or "").lower()) + " "
    if " pune " in low or any(p in pune_places.TALUKA_BY_PIN for p in _PIN.findall(text or "")):
        return True
    return any(f" {t} " in low for t in _TALUKAS) or bool(place_in(text))


def place_in(text: str) -> Optional[str]:
    """A known Pune place named in the text (the longest name wins), or None."""
    low = pune_places._norm(text)
    best = max(((pune_places._named(p, low), p.name) for p in pune_places.PLACES), default=(0, None))
    return best[1] if best[0] else None


def _rec(d: dict) -> Dict[str, Any]:
    return {"regno": d.get("regno") or d.get("_id"), "name": d.get("name", ""), "taluka": d.get("taluka") or ""}


async def match_register(register: Any, rera_no: Optional[str], project_name: Optional[str]) -> Dict[str, Any]:
    """{"record": register doc | None, "candidates": [{regno, name, taluka}]}. Only a registration number is a confident
    match; a name (exact or close) is offered for a one-tap pick. Never raises."""
    out: Dict[str, Any] = {"record": None, "candidates": []}
    if register is None:
        return out
    try:
        if rera_no:
            d = await register.project(rera_no.strip().upper())
            if d:
                out["record"] = d
                return out
        name = (project_name or "").strip()
        if not name:
            return out
        everything = await register.all_projects()
        exact = [d for d in everything if _words(d.get("name", "")) == _words(name)]
        close = [d for d in everything if d not in exact and core(name) and core(d.get("name", "")) == core(name)]
        out["candidates"] = [_rec(d) for d in (exact + close)[:CANDIDATES]]
    except Exception as e:
        log.info("ai_listing register match failed: %s", type(e).__name__)
    return out


def register_fields(d: dict) -> Dict[str, Any]:
    """What the draft takes from a register record."""
    loc = d.get("pune_place_name") or d.get("locality")
    if not loc and d.get("pincode"):
        loc = pune_places.place_name(d.get("name", ""), d.get("pincode", ""), d.get("taluka", ""), d.get("regno", ""))
    return {k: v for k, v in {
        "regno": d.get("regno") or d.get("_id"), "name": d.get("name"), "locality": loc, "taluka": d.get("taluka"),
        "pincode": d.get("pincode"), "promoter": d.get("promoter"),
        "completion_at_registration": d.get("completion_at_registration"), "completion_now": d.get("completion_now"),
    }.items() if v not in (None, "")}


def same_place(locality: Optional[str], project: Optional[str]) -> bool:
    """True when the 'locality' is really the project's name ("Gulmohar City" / "Gulmohar City Plots")."""
    if not locality or not project:
        return False
    a, b = _words(locality), _words(project)
    return bool(a) and (a == b or bool(core(locality)) and core(locality) == core(project))

