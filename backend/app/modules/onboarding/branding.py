"""Agent brand profile: the optional fields an agent can set on his own public site (stored inside the profile's branding_data).

Everything here is additive and optional. Free text is kept plain: no phone numbers, links, e-mail addresses or markup
(the public site sends buyers to the enquiry form, never to a number typed into a tagline).
"""
from app.core import brand
import re
from typing import List, Optional

# name -> colours, hero treatment, button style. Mirrors frontend/lib/site/presets.ts (a jest test pins the colours).
PRESETS = {
    "navy-gold": {"primary": "#102340", "secondary": "#0b1a33", "accent": "#f0b440", "hero": "gradient-skyline", "button": "pill"},
    "emerald": {"primary": "#0b5d46", "secondary": "#083f31", "accent": "#f4c95d", "hero": "gradient-arcs", "button": "rounded"},
    "terracotta": {"primary": "#9c3d1f", "secondary": "#6e2812", "accent": "#f2c46d", "hero": "gradient-sun", "button": "pill"},
    "royal-purple": {"primary": "#4a2a82", "secondary": "#321b5c", "accent": "#f0c75e", "hero": "gradient-diagonal", "button": "square"},
    "slate-teal": {"primary": "#26414d", "secondary": "#182b34", "accent": "#5fd0c2", "hero": "gradient-grid", "button": "rounded"},
    "cream-ink": {"primary": "#2b2118", "secondary": "#1c150f", "accent": "#c8963e", "hero": "cream-ink", "button": "square"},
}
PRESET_NAMES = tuple(PRESETS)

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_RERA = re.compile(r"^A\d{6,18}$")
_URL = re.compile(r"(https?:|www\.|://|\b[\w-]+\.(?:com|in|co|net|org|io|app|me|info|biz|xyz)\b|@[\w.]+\.)", re.I)
_PHONE = re.compile(r"(?:\+?\d[\s\-().]*){7,}")
_MARKUP = re.compile(r"[<>{}\\`]")
_AREA = re.compile(r"^[A-Za-z][A-Za-z ,.'\-/]{1,38}$")
_LANG = re.compile(r"^[A-Za-z][A-Za-z ]{1,19}$")

# Keys in branding_data that only the owner sets (from backend scripts, never from agent input). `demo: true` marks the
# fictional demo agent (scripts/create_demo_agent.py); the public site then shows a DEMO ribbon. SiteCreate/SiteUpdate have
# no such field, so agent requests cannot set it, and update_site keeps it when the agent edits the rest of his brand.
# `preview: true` marks a site the owner prepared for an agent who has not agreed to publish yet: the page is unlisted
# (noindex) and says it is a preview.
OWNER_ONLY_KEYS = ("demo", "preview")

LIMITS = {"business_name": 60, "tagline": 90, "about": 600}
MAX_AREAS = 6
MAX_LANGUAGES = 6

PUNE_LOCALITIES = {
    "aundh", "baner", "balewadi", "bavdhan", "bibwewadi", "bhosari", "camp", "chakan", "chinchwad", "dehu road", "deccan",
    "dhanori", "erandwane", "fc road", "ghorpadi", "hadapsar", "handewadi", "hinjewadi", "kalyani nagar", "kalyaninagar",
    "kharadi", "upper kharadi", "kondhwa", "koregaon park", "kothrud", "lohegaon", "magarpatta", "manjri", "model colony",
    "moshi", "mundhwa", "nibm", "narhe", "pashan", "pimple saudagar", "pimple nilakh", "pimple gurav", "pimpri",
    "pimpri chinchwad", "pcmc", "pune", "pune city", "ravet", "sadashiv peth", "sahakar nagar", "shivajinagar",
    "sinhagad road", "somatane", "sus", "tathawade", "talegaon", "undri", "viman nagar", "vishrantwadi", "wagholi",
    "wakad", "wanowrie", "warje", "yerawada", "yerwada", "akurdi", "nigdi", "wadgaon sheri", "kesnand", "lonikand",
    "ambegaon", "katraj", "dhankawadi", "karve nagar", "karve road", "law college road", "senapati bapat road", "sb road",
    "swargate", "parvati", "navi peth", "kasba peth", "budhwar peth", "lullanagar", "salunke vihar", "nibm road",
    "mohammadwadi", "fursungi", "loni kalbhor", "uruli kanchan", "bopodi", "khadki", "range hills", "pashan sus road",
    "baner pashan link road", "mahalunge", "sus road", "bhugaon", "lavale", "pirangut", "nande", "marunji", "kiwale",
    "punawale", "dighi", "charholi", "chikhali", "alandi", "kalewadi", "rahatani", "sangvi", "new sangvi",
    "shivane", "dhayari", "nanded city", "kirkatwadi", "kopare", "wadgaon budruk", "narayan peth",
}
_PUNE_WORDS = ("pune", "pimpri", "chinchwad", "pcmc")


def _clean_text(value: Optional[str], field: str, limit: int) -> Optional[str]:
    if value is None:
        return None
    s = re.sub(r"\s+", " ", str(value)).strip()
    if not s:
        return None
    label = field.replace("_", " ")
    if len(s) > limit:
        raise ValueError(f"Keep {label} within {limit} characters")
    if _MARKUP.search(s):
        raise ValueError(f"Please remove special characters from {label}")
    if _URL.search(s):
        raise ValueError(f"Please do not put links or e-mail addresses in {label}")
    if _PHONE.search(s) or len(re.sub(r"\D", "", s)) >= 8:
        raise ValueError(f"Please do not put phone numbers in {label}: buyers reach you through your site")
    return s


def clean_business_name(v):
    s = _clean_text(v, "business_name", LIMITS["business_name"])
    if s is not None and len(s) < 2:
        raise ValueError("Business name is too short")
    return s


def clean_tagline(v):
    return _clean_text(v, "tagline", LIMITS["tagline"])


def clean_about(v):
    return _clean_text(v, "about", LIMITS["about"])


def clean_preset(v):
    if v is None or v == "":
        return None
    if v not in PRESETS:
        raise ValueError("Choose one of: " + ", ".join(PRESET_NAMES))
    return v


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    chans = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        chans.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def contrast_ratio(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def clean_custom_primary(v):
    if v is None or v == "":
        return None
    s = str(v).strip()
    if not _HEX.match(s):
        raise ValueError("Colour must look like #1a2b3c")
    s = s.lower()
    if contrast_ratio(s, "#ffffff") < 4.5:
        raise ValueError("That colour is too light for white text. Choose a darker shade.")
    return s


def clean_rera_agent_no(v):
    if v is None:
        return None
    s = re.sub(r"[\s\-]", "", str(v)).upper()
    if not s:
        return None
    if len(s) > 20 or not _RERA.match(s):
        raise ValueError("Enter your MahaRERA agent registration number, like A52100012345")
    return s


def clean_areas(v) -> Optional[List[str]]:
    if v is None:
        return None
    if not isinstance(v, (list, tuple)):
        raise ValueError("areas must be a list")
    out: List[str] = []
    for raw in v:
        s = re.sub(r"\s+", " ", str(raw)).strip()
        if not s:
            continue
        if not _AREA.match(s) or _URL.search(s):
            raise ValueError("Use plain locality names, like Baner or Kharadi")
        key = s.lower()
        if key not in PUNE_LOCALITIES and not any(w in key for w in _PUNE_WORDS):
            raise ValueError(f"'{s}' is outside Pune. {brand.NAME} covers Pune localities for now.")
        if key not in [x.lower() for x in out]:
            out.append(s)
    if len(out) > MAX_AREAS:
        raise ValueError(f"Pick up to {MAX_AREAS} areas")
    return out


def clean_languages(v) -> Optional[List[str]]:
    if v is None:
        return None
    if not isinstance(v, (list, tuple)):
        raise ValueError("languages must be a list")
    out: List[str] = []
    for raw in v:
        s = re.sub(r"\s+", " ", str(raw)).strip()
        if not s:
            continue
        if not _LANG.match(s):
            raise ValueError("Use plain language names, like Hindi")
        if s.lower() not in [x.lower() for x in out]:
            out.append(s)
    if len(out) > MAX_LANGUAGES:
        raise ValueError(f"Pick up to {MAX_LANGUAGES} languages")
    return out


def clean_years(v):
    if v is None or v == "":
        return None
    n = int(v)
    if not 0 <= n <= 60:
        raise ValueError("Years of experience must be between 0 and 60")
    return n


def theme_for(preset: Optional[str], custom_primary: Optional[str]) -> dict:
    """The {primary, secondary, accent} colours legacy consumers (site_config.theme, branding_data.colors) should see."""
    base = PRESETS.get(preset or "navy-gold", PRESETS["navy-gold"])
    colors = {k: base[k] for k in ("primary", "secondary", "accent")}
    if custom_primary:
        colors["primary"] = custom_primary
    return colors
