"""Builder brands: the name buyers search ("Godrej Properties projects in Pune"), over the companies MahaRERA files them under.

Owner, 2026-10-20 (learning from housiey.com): builder pages with a delivery record, and they must help search. MahaRERA's
"promoter" is often a company formed for one project or one piece of land: Godrej Ivara is filed by Manjari Housing Projects
LLP, VTP's projects by Ashdan Developers and others. Grouped by that name, a brand splits into small pages nobody searches for.

A record joins a brand when
- its promoter's name says the brand (`promoter`, matched on `text.promoter_key`), or
- its project name starts with the brand word (`name_start`), only for words no other builder uses at the start of a name
  (measured on the register 2026-10-20: "Ganga", "Mantra", "Kumar", "Rohan" and "Marvel" start other builders' names too).
A record with no promoter on MahaRERA never joins by name. Per record, never per company: Manjari Housing Projects LLP's "Sarita Niketan" stays out of Godrej. The brand page lists the
companies it counted, so the grouping can be checked. `search` is what buyers type for the brand: seo.gaps sends those
searches to the brand page.
"""
import re
from dataclasses import dataclass
from typing import List, Optional

from .text import promoter_key


@dataclass(frozen=True)
class Brand:
    slug: str
    name: str
    promoter: re.Pattern
    name_start: Optional[re.Pattern]
    search: re.Pattern


def _b(slug: str, name: str, promoter: str, name_start: Optional[str] = None, search: Optional[str] = None) -> Brand:
    word = search or r"\b" + re.escape(name.split()[0].lower()) + r"\b"
    return Brand(slug, name, re.compile(promoter), re.compile(name_start) if name_start else None, re.compile(word))


BRANDS: List[Brand] = [
    _b("godrej-properties", "Godrej Properties", r"\bgodrej\b", r"^godrej\b"),
    _b("lodha", "Lodha", r"\blodha developers\b|\bmacrotech developers\b", r"^lodha\b"),
    _b("kolte-patil", "Kolte Patil", r"\bkolte\s*patil\b", search=r"\bkolte\b"),
    _b("vtp-realty", "VTP Realty", r"\bvtp\b", r"^vtp\b"),
    _b("panchshil", "Panchshil Realty", r"\bpanchshil\b", r"^panchshil\b"),
    _b("gera-developments", "Gera Developments", r"\bgera (developments|projects|developers)\b", r"^geras?\b", r"\bgeras?\b"),
    _b("rohan-builders", "Rohan Builders", r"\brohan (builders|housing|promoters|lifescapes)\b", search=r"\brohan (builders|lifescapes)\b"),
    _b("pride-group", "Pride Group", r"\bpride (purple|builders|properties)\b", search=r"\bpride (purple|group|builders)\b"),
    _b("kohinoor-group", "Kohinoor Group", r"\bkohinoor\b", r"^kohinoor\b"),
    _b("mahindra-lifespaces", "Mahindra Lifespaces", r"\bmahindra\b", r"^mahindra\b"),
    _b("shapoorji-pallonji", "Shapoorji Pallonji (Joyville)", r"\bshapoorji\b", r"^joyville\b", r"\b(shapoorji|joyville)\b"),
    _b("paranjape-schemes", "Paranjape Schemes", r"\bparanjape\b"),
    _b("majestique", "Majestique Landmarks", r"\bmajestique\b", r"^majestique\b"),
    _b("goel-ganga", "Goel Ganga", r"\bgoel ganga\b", search=r"\bgoel ganga\b"),
    _b("nyati-group", "Nyati Group", r"\bnyati\b", r"^nyati\b"),
    _b("pharande-spaces", "Pharande Spaces", r"\bpharande\b"),
    _b("vilas-javdekar", "Vilas Javdekar Developers", r"\bvilas javdekar\b", search=r"\b(vilas javdekar|vj)\b"),
    _b("kalpataru", "Kalpataru", r"\bkalpataru\b", r"^kalpataru \w"),   # "Kalpataru" alone is also a plain building name
    _b("marvel-realtors", "Marvel Realtors", r"^marvel (sigma|realtors|landmarks|omega)\b", search=r"\bmarvel (realtors|projects)\b"),
    _b("k-raheja-corp", "K Raheja Corp", r"\bk raheja\b", search=r"\b(k raheja|raheja)\b"),
    _b("kasturi", "Kasturi", r"\bkasturi (spaces|developers)\b", search=r"\bkasturi (spaces|developers|projects)\b"),
    _b("sobha", "Sobha", r"\bsobha\b"),
    _b("birla-estates", "Birla Estates", r"\bbirla estates\b", search=r"\bbirla\b"),
    _b("tata-housing", "Tata Housing", r"\btata (value homes|housing)\b", search=r"\btata (housing|value homes|projects)\b"),
    _b("provident-housing", "Provident Housing (Puravankara)", r"\bprovident housing\b|\bpuravankara\b", search=r"\b(provident|puravankara)\b"),
    _b("vascon", "Vascon Engineers", r"\bvascon\b"),
    _b("pegasus-megapolis", "Pegasus (Megapolis)", r"\bpegasus properties\b", r"^megapolis\b", r"\b(megapolis|pegasus)\b"),
    _b("duville-estates", "Duville Estates", r"\bduville\b"),
    _b("ravima", "Ravima", r"\bravima\b"),
]
BY_SLUG = {b.slug: b for b in BRANDS}


def _words(s: object) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(s or "").lower()))


def of(doc: dict) -> Optional[Brand]:
    """The brand a register record is sold under, or None (then its MahaRERA promoter is its builder)."""
    p, n = promoter_key(doc.get("promoter")), _words(doc.get("name"))
    for b in BRANDS:
        # by name only with a promoter on record: an unnamed one could be anyone's
        if (p and b.promoter.search(p)) or (p and b.name_start and b.name_start.search(n)):
            return b
    return None


def for_search(phrase: str) -> Optional[Brand]:
    """The brand a search names ("godrej properties pune", "kolte patil delayed projects"), or None."""
    q = _words(phrase)
    return next((b for b in BRANDS if b.search.search(q)), None)
