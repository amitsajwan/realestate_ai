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

# moved to inventory (listings.schemas cleans claims on the way in); re-exported for this module's callers
from app.modules.listings.claims import (CLAIM_MAX_CHARS, COMPANY, DISCLAIMER, INVEST, MAX_CLAIMS, OTHER_CITY,  # noqa: F401
                                         PHONE, ROAD, SALES_PROBLEMS, clean_claims)

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
