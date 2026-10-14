"""The listing's project files (an agent's own: the builder's brochure PDF and the walkthrough video).

    brochure  stored with the listing and never read: opening a PDF (its pages, OCR, a vision pass) is the heavy part of
              listing work (owner, 2026-10-14). `brochure_pdf` finds the file the listing points at, and `claims_for` reads
              back what an earlier read left on the listing as `file_claims`, so a run still has those words. A listing
              posted from now on gets none: its posts come from the agent's own facts and pictures.
    video     the presenter's words (video_director.transcribe) -> short claims by the LLM

Claims are the BUILDER's, never our facts: the assistant states them as "the builder's brochure says ..."
(knowledge.grounding.listing_grounding), and `clean_claims` drops phone numbers, hype and sales promises on the way in."""
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import points

MAX_CLAIMS = 25        # a 4-page brochure: travel times alone fill a dozen
CLAIM_MAX_CHARS = 160
PHONE = re.compile(r"(?:\d[\s-]?){8,}")
SALES_PROBLEMS = ("hype word", "prediction", "promise", "claim not in facts")
INVEST = re.compile(r"\b(investment|returns?|appreciation|profit|earning)\b|गुंतवणूक|गुंतवणुकी|कमाई|परतावा|निवेश|मुनाफ", re.I)
# the developer's company, not this project (the reader is told to leave these out and still copied Lodha's Mumbai corporate
# address from the small print): its offices, portfolio, awards and company-wide figures
COMPANY = re.compile(r"\b(?:corporate|head|registered)\s+(?:office|address)\b|\bportfolio\b|\bawards?\b|\baward[- ]winning\b|"
                     r"\bother\s+projects?\b|\bmillion\s+sq|\bm(?:n|sf)\b|\bsbti\b|\bdjsi\b|science[- ]based\s+targets|"
                     r"dow\s+jones|\byears\s+of\s+(?:legacy|experience|excellence)\b|\bsince\s+(?:19|20)\d\d\b", re.I)
# a city that is not Pune: a claim naming one is about the developer's other work ("landmarks in Mumbai and London"), unless
# it is a road to it ("20 min to the Pune-Mumbai Expressway")
OTHER_CITY = re.compile(r"\b(?:mumbai|thane|london|dubai|bengaluru|bangalore|hyderabad|delhi|gurugram|gurgaon|chennai|"
                        r"kolkata)\b", re.I)
ROAD = re.compile(r"\b(?:expressway|highway|road|rd)\b|pune\s*-\s*\w+|\w+\s*-\s*pune", re.I)
# the small print of a legal page, read as claims once the page is sharp: not something the builder says about the project
DISCLAIMER = re.compile(r"\bindicative\b|\b(?:does|shall)\s+not\s+constitute\b|\bnot\s+an?\s+(?:offer|contract)\b|"
                        r"\breserves?\s+the\s+right\b|\bsubject\s+to\s+change\b|\bequivalent\s+or\s+better\b|\bvariance\b|"
                        r"\bpolyline\b|\bunfinished\s+(?:surfaces|dimensions)\b|\bat\s+an?\s+additional\s+(?:price|cost)\b|"
                        r"\bfinished\s+floor\s+level\b|\bartist'?s\s+impression\b|\bdisclaimer\b", re.I)
VIDEO_SYSTEM = (
    "You summarise what a presenter says in a real-estate site video, as the builder's claims. Reply with JSON only."
)
VIDEO_USER = (
    "Transcript (may have speech-to-text errors; Marathi/Hindi/English):\n{text}\n\nList what is claimed about the project, "
    "one short plain sentence each, in English: location and distances, plot sizes, roads, water, power, security, "
    "amenities, paperwork. Copy numbers as spoken. Leave out offers tied to a festival or date, slogans, adjectives, phone "
    'numbers. Reply: {{"claims": ["..."]}}'
)


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
        if not c or len(c) > CLAIM_MAX_CHARS or PHONE.search(c) or INVEST.search(c) or points.PRELAUNCH.search(c):
            continue
        if COMPANY.search(c) or (OTHER_CITY.search(c) and not ROAD.search(c)):   # the developer's, not this project's
            continue
        if DISCLAIMER.search(c):
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


def claims_for(listing: dict, pdf: Path) -> Optional[Dict[str, Any]]:
    """The claims already kept on the listing for this very brochure file: read before a brochure was ever opened here, and
    never again. Nothing writes them now."""
    fc = listing.get("file_claims") if isinstance(listing.get("file_claims"), dict) else {}
    url = str(fc.get("brochure_url") or "").split("?")[0]
    if not fc.get("brochure") or not url.lower().endswith("/" + pdf.name.lower()):
        return None
    rera = fc.get("rera_on_brochure")
    return {"claims": list(fc["brochure"]), "rera_no": rera, "rera_missing": not rera, "read_by_ai": True, "weak": False,
            "facts": dict(fc.get("brochure_facts") or {}), "language": fc.get("language") or "en"}


async def save_claims(listings, listing_id: str, *, video: Optional[List[str]] = None,
                      now: Optional[datetime] = None) -> None:
    """Keep what the video's words gave on the listing (`file_claims.video`), for the assistant and for Studio."""
    if video is None:
        return
    await listings.update_one({"_id": listing_id}, {"$set": {"file_claims.video": video,
                                                             "file_claims.updated_at": now or datetime.utcnow()}})
