"""Whose posts a campaign makes: from the listing owner's public profile, the voice the prompts speak in, the card footer
(logo, name, phone) and the contact block code adds to every caption. Our own page (slug OFFICIAL_SLUG) and an agent with no
profile keep the brand's defaults. Pure: profile dict in, values out."""
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from app.modules.creative import i18n
from app.modules.creative.models import CardBrand, Voice

OFFICIAL_SLUG = os.environ.get("INTEREST_OWNER_SLUG") or "avasetu"
CONTACT_LABELS = {
    "en": ("Call or WhatsApp", "Website", "On Avasetu"),
    "mr": ("कॉल / WhatsApp", "वेबसाइट", "Avasetu वर"),
    "hi": ("कॉल / WhatsApp", "वेबसाइट", "Avasetu पर"),
}


@dataclass
class Identity:
    voice: Optional[Voice] = None              # None: the brand's own
    card_brand: Optional[CardBrand] = None
    contact: List[str] = field(default_factory=list)


def phone_label(raw: str) -> str:
    """'+919921993099' -> '+91 99219 93099'; anything else is returned trimmed."""
    d = re.sub(r"\D", "", raw or "")
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    return f"+91 {d[:5]} {d[5:]}" if len(d) == 10 else (raw or "").strip()


def bare_url(u: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", (u or "").strip()).rstrip("/")


def identity(profile: Optional[dict], site: str, uploads_dir: Path, language: str = "en") -> Identity:
    if not profile or profile.get("slug") in (None, "", OFFICIAL_SLUG):
        return Identity()
    bd = profile.get("branding_data") or {}
    name = (bd.get("business_name") or profile.get("agent_name") or "").strip()
    if not name:
        return Identity()
    phone = phone_label(profile.get("phone") or "")
    logo = bd.get("logo") or ""
    logo_file = str(uploads_dir / logo[len("/uploads/"):]) if logo.startswith("/uploads/") else ""
    call, web, ours = CONTACT_LABELS.get(language, CONTACT_LABELS["en"])
    contact = [f"\U0001F4DE {call}: {phone}"] if phone else []
    if bd.get("website"):
        contact.append(f"\U0001F310 {web}: {bare_url(bd['website'])}")
    contact.append(f"\U0001F3E0 {ours}: {bare_url(site)}/agent/{profile['slug']}")
    return Identity(voice=Voice(name=name, team=f"{name} team"),
                    card_brand=CardBrand(name=name, line=f"{i18n.ui('call', language)} {phone}" if phone else (bd.get("tagline") or ""),
                                         logo=logo_file, phone=phone),
                    contact=contact)
