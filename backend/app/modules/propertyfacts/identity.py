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


WA_MARK = "\U0001F4AC"   # the speech bubble that starts the WhatsApp line of a caption (calendar.adapters finds it)


def posts_whatsapp_number() -> Optional[str]:
    """The WhatsApp number public posts show, as wa.me digits: WHATSAPP_PUBLIC_NUMBER only (never the website chat's
    NEXT_PUBLIC_WHATSAPP_NUMBER, which may be a test number that answers only allowed phones). None: posts carry only the
    tracked link."""
    d = re.sub(r"\D", "", os.environ.get("WHATSAPP_PUBLIC_NUMBER") or "")
    if re.fullmatch(r"[6-9]\d{9}", d):
        d = "91" + d
    return d if 11 <= len(d) <= 15 else None


def whatsapp_label() -> str:
    """Our public WhatsApp number as '+91 98765 43210', or '' when none is configured (then captions carry only the link)."""
    num = posts_whatsapp_number()
    return phone_label("+" + num) if num else ""


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
    # Buyers reach the agent through OUR WhatsApp number, never the agent's own phone: the chat carries the post's code, so our
    # bot routes it to this agent and the lead is counted for that post (calendar.adapters puts the code link in at publish).
    phone = whatsapp_label()
    logo = bd.get("logo") or ""
    logo_file = str(uploads_dir / logo[len("/uploads/"):]) if logo.startswith("/uploads/") else ""
    call, web, ours = CONTACT_LABELS.get(language, CONTACT_LABELS["en"])
    contact = [f"{WA_MARK} WhatsApp: {phone}"] if phone else []
    if bd.get("website"):
        contact.append(f"\U0001F310 {web}: {bare_url(bd['website'])}")
    contact.append(f"\U0001F3E0 {ours}: {bare_url(site)}/agent/{profile['slug']}")
    return Identity(voice=Voice(name=name, team=f"{name} team"),
                    card_brand=CardBrand(name=name, line=f"WhatsApp {phone}" if phone else "",   # a long tagline overflows the footer
                                         logo=logo_file, phone=phone),
                    contact=contact)
