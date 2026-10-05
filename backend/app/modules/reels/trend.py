"""Trend reels: short explainers about Pune buying that need no property of ours (2026-10-05: no inventory yet).

Rules, the same as every other reel (docs/NEWSROOM_PLAN.md): no invented facts. Every figure on screen comes from FACTS (a dated, sourced
statement) or from a deterministic calculation below (`cost_sheet`, `area_for_budget`), never from a model's memory. `check(reel)` fails a
reel whose screen text has a number that is not in its facts, whose hook is weak, or that has no source line in its caption.

A fact is `official` (a government release) or `secondary` (portals and property-advice sites, which differ from each other and change):
secondary facts are shown on screen as "as listed" and must be confirmed against the official source by a human before approval.
Facts expire (`valid_until`): `check` fails a reel that uses an expired fact, so nothing outlives its date.

The voice-over is optional (it needs GOOGLE_TTS_API_KEY); without it the reel plays with the Avasetu theme music.
"""
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from app.platform.text import hook_problems

from . import director, voice

# ---- facts -------------------------------------------------------------------------------------------------------------------------
OFFICIAL, SECONDARY = "official", "secondary"


@dataclass(frozen=True)
class Fact:
    id: str
    text: str
    source: str          # who says so
    url: str
    as_of: str           # YYYY-MM-DD: the date of the statement or of our reading
    valid_until: str     # YYYY-MM-DD: after this the reel must be re-checked
    kind: str            # OFFICIAL | SECONDARY


FACTS: Dict[str, Fact] = {f.id: f for f in (
    Fact("metro_2b_approved",
         "The Union Cabinet approved the Ramwadi to Wagholi/Vitthalwadi metro corridor (Pune Metro Phase-2, Corridor 2B) on 25 June 2025.",
         "PIB, Union Cabinet release", "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2139488", "2025-06-25", "2027-06-25", OFFICIAL),
    Fact("metro_2b_timeline",
         "The release says the Phase-2 corridors are to be completed within 4 years of approval.",
         "PIB, Union Cabinet release", "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2139488", "2025-06-25", "2027-06-25", OFFICIAL),
    Fact("metro_line4_approved",
         "The Union Cabinet has approved Pune Metro Line 4 (Kharadi to Khadakwasla).",
         "PIB, Union Cabinet release", "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2194691", "2026-10-05", "2027-04-05", OFFICIAL),
    Fact("psf_wagholi",
         "Property portals list new homes in Wagholi from about Rs 5,000 to Rs 6,500 per sq ft.",
         "Property portals (HomeBazaar, PropertyPistol and others), read Oct 2026", "https://www.homebazaar.com/knowledge/latest-property-rates-in-pune/",
         "2026-10-05", "2026-12-05", SECONDARY),
    Fact("psf_kharadi",
         "Property portals list homes in Kharadi at about Rs 8,600 to Rs 10,400 per sq ft.",
         "Property portals (HomeBazaar, PropertyPistol and others), read Oct 2026", "https://www.homebazaar.com/knowledge/latest-property-rates-in-pune/",
         "2026-10-05", "2026-12-05", SECONDARY),
    Fact("stamp_duty_man",
         "Stamp duty for a man buying a home inside Pune's municipal limits is 7% (5% duty, 1% metro cess, 1% local body tax); women pay 6%.",
         "Property-advice sites (Bajaj Finserv, Godrej Properties), read Oct 2026; confirm on igrmaharashtra.gov.in",
         "https://igrmaharashtra.gov.in/", "2026-10-05", "2026-12-05", SECONDARY),
    Fact("registration",
         "Registration is 1% of the value, capped at Rs 30,000.",
         # the table: Rs 100 plus Rs 10 per Rs 1,000 above Rs 10,000, at most Rs 30,000 (conveyance on market value, Article I(3-A))
         "IGR Maharashtra, Table of Fees under the Registration Act (amended 11 Sep 2014), read 5 Oct 2026",
         "https://igrmaharashtra.gov.in/pdf/eodb/3.1Registration%20fee%20table.pdf", "2026-10-05", "2027-04-05", OFFICIAL),
    Fact("gst_under_construction",
         "GST on an under-construction home that is not affordable housing works out to 5% of the price, with no input credit (7.5% on "
         "two-thirds of it; one-third is deemed to be land); none is due when the whole price is paid after the completion certificate "
         "or first occupation.",
         # item (ia) of heading 9954: central tax 3.75% (state tax the same) on the price less a deemed one-third for land, paragraph 2
         "CBIC Notification 03/2019-Central Tax (Rate), 29 Mar 2019 (in the consolidated rate notification on gstcouncil.gov.in), read 5 Oct 2026",
         "https://gstcouncil.gov.in/sites/default/files/2024-02/11-rate_notification-cgst-01.04.2019.pdf", "2026-10-05", "2027-04-05",
         OFFICIAL),
)}


# ---- deterministic calculations --------------------------------------------------------------------------------------------------------
def lakh(rupees: float) -> str:
    """4_20_000 -> 'Rs 4.2 lakh'; 30_000 -> 'Rs 30,000'; trailing '.0' dropped."""
    if rupees >= 100_000:
        v = round(rupees / 100_000, 2)
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return f"Rs {s} lakh"
    return f"Rs {int(round(rupees)):,}"


def cost_sheet(base_inr: int, *, stamp_pct: float = 7.0, gst_pct: float = 7.5, under_construction: bool = True) -> Dict[str, int]:
    """What a flat advertised at `base_inr` costs once the taxes in FACTS are added (not parking, deposits, maintenance or other charges,
    which differ by project and must be asked for in writing). Whole rupees."""
    stamp = round(base_inr * stamp_pct / 100)
    registration = min(round(base_inr / 100), 30_000)
    gst = round(base_inr * 2 / 3 * gst_pct / 100) if under_construction else 0   # 7.5% on two-thirds = 5% of the price
    return {"base": base_inr, "stamp_duty": stamp, "registration": registration, "gst": gst,
            "extra": stamp + registration + gst, "total": base_inr + stamp + registration + gst}


def area_for_budget(budget_inr: int, psf_low: int, psf_high: int) -> tuple:
    """(smallest, largest) sq ft the budget buys at the dearest and the cheapest rate, rounded to the nearest 10."""
    return (int(round(budget_inr / psf_high / 10)) * 10, int(round(budget_inr / psf_low / 10)) * 10)


# ---- the reels -----------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class TrendReel:
    slug: str
    experiment: str      # one idea, several hooks: the reels that share it are compared with each other
    variant: str
    hook_type: str       # price_reveal | question | myth_bust | explainer ...
    engine: str          # the blueprint's engine, for the table in Studio later
    locality: str
    price_band: str
    facts: Sequence[str]            # FACTS ids this reel may use
    derived: Sequence[str]          # sentences computed above, shown as facts
    beats: Sequence[Dict[str, str]]  # {"screen", "voice"}: the hook and up to 4 more
    cta: Dict[str, str]
    caption: str                     # first line = the hook; sources are appended by `captions`
    tags: Sequence[str] = field(default_factory=tuple)


_C60 = cost_sheet(60 * 100_000)
_C60_READY = cost_sheet(60 * 100_000, under_construction=False)
_W_LOW, _W_HIGH = area_for_budget(50 * 100_000, 5_000, 6_500)   # Wagholi: 770 to 1,000 sq ft
_K_LOW, _K_HIGH = area_for_budget(50 * 100_000, 8_600, 10_400)  # Kharadi: 480 to 580 sq ft


def _n(x: int) -> str:
    return f"{x:,}"


TRENDS: List[TrendReel] = [
    TrendReel(
        slug="trend-50l-kharadi-wagholi", experiment="EXP-001", variant="B", hook_type="question", engine="PRICE_REVEAL",
        locality="Kharadi / Wagholi", price_band="50L", facts=("psf_wagholi", "psf_kharadi"),
        derived=(f"At those rates Rs 50 lakh buys roughly {_n(_W_LOW)} to {_n(_W_HIGH)} sq ft in Wagholi and {_n(_K_LOW)} to {_n(_K_HIGH)} sq ft in "
                 "Kharadi, before taxes and extras.",),
        beats=(
            {"screen": "₹50 lakh: *Kharadi* or *Wagholi*?", "voice": "You have fifty lakh rupees. Kharadi or Wagholi?"},
            {"screen": "Wagholi: ₹5,000 to ₹6,500 per sq ft", "voice": "Property portals list Wagholi at about five to six and a half thousand rupees a square foot."},
            {"screen": "Kharadi: ₹8,600 to ₹10,400 per sq ft", "voice": "Kharadi, at about eighty-six hundred to ten thousand four hundred."},
            {"screen": f"₹50L buys {_n(_W_LOW)}–{_n(_W_HIGH)} sq ft in *Wagholi*",
             "voice": f"At those rates, fifty lakh buys roughly {_n(_W_LOW)} to {_n(_W_HIGH)} square feet in Wagholi."},
            {"screen": f"And {_n(_K_LOW)}–{_n(_K_HIGH)} sq ft in *Kharadi*",
             "voice": f"And roughly {_n(_K_LOW)} to {_n(_K_HIGH)} in Kharadi. Before taxes and extras."},
        ),
        cta={"screen": "Save this. Send it to someone buying.", "voice": "Save this, and send it to someone who is buying in Pune."},
        caption=("₹50 lakh in Pune: Kharadi or Wagholi?\n\nProperty portals list Wagholi at about ₹5,000–6,500 per sq ft and Kharadi at about "
                 f"₹8,600–10,400 (Oct 2026). At those rates ₹50 lakh buys roughly {_n(_W_LOW)}–{_n(_W_HIGH)} sq ft in Wagholi and "
                 f"{_n(_K_LOW)}–{_n(_K_HIGH)} sq ft in Kharadi, before taxes and extras. Rates differ by project and by what the area figure "
                 "counts (carpet or saleable): always compare the price per sq ft of carpet area."),
        tags=("#PuneProperty", "#KharadiPune", "#WagholiPune", "#PuneHomes"),
    ),
    TrendReel(
        slug="trend-wagholi-metro", experiment="EXP-002", variant="A", hook_type="question", engine="LOCALITY_INTEL",
        locality="Wagholi", price_band="", facts=("metro_2b_approved", "metro_2b_timeline", "metro_line4_approved"), derived=(),
        beats=(
            {"screen": "Is the metro to *Wagholi* built yet?", "voice": "Is the metro to Wagholi built yet? Short answer: no."},
            {"screen": "*Approved* by the Union Cabinet, June 2025",
             "voice": "The Union Cabinet approved the Ramwadi to Wagholi line in June twenty twenty-five."},
            {"screen": "The release says: done within 4 years", "voice": "The release says the work is to be completed within four years of approval."},
            {"screen": "Kharadi to Khadakwasla (Line 4) is approved too",
             "voice": "The Kharadi to Khadakwasla line has been approved as well."},
            {"screen": "*Approved* is not *running*", "voice": "But approved is not the same as running. Check the Maha-Metro site before you pay extra for a station."},
        ),
        cta={"screen": "Save this before you book.", "voice": "Save this before you book a flat near a planned station."},
        caption=("Is the metro to Wagholi built yet? No: approved, not running.\n\nThe Union Cabinet approved the Ramwadi to Wagholi/Vitthalwadi "
                 "corridor on 25 June 2025 and the release says the work is to be completed within 4 years of approval. The Kharadi to Khadakwasla "
                 "line (Line 4) is also approved. Approved is not the same as running: check the current status on the Maha-Metro website and do "
                 "not pay extra for a station that does not exist yet."),
        tags=("#PuneMetro", "#WagholiPune", "#KharadiPune", "#PuneProperty"),
    ),
    TrendReel(
        slug="trend-60l-flat-real-cost", experiment="EXP-003", variant="A", hook_type="price_reveal", engine="PROPERTY_TRUTHS",
        locality="Pune", price_band="60L", facts=("stamp_duty_man", "registration", "gst_under_construction"),
        derived=(f"On a Rs 60 lakh under-construction flat a man pays {lakh(_C60['stamp_duty'])} stamp duty, {lakh(_C60['registration'])} registration "
                 f"and {lakh(_C60['gst'])} GST: {lakh(_C60['extra'])} more, so {lakh(_C60['total'])} before parking, deposits and other charges. "
                 f"A ready home with an occupancy certificate has no GST: {lakh(_C60_READY['total'])}.",),
        beats=(
            {"screen": f"A ₹60 lakh flat costs *{lakh(_C60['total']).replace('Rs ', '₹')}*?",
             "voice": "Why does a sixty lakh flat cost about sixty-seven and a half lakh?"},
            {"screen": f"Stamp duty 7%: {lakh(_C60['stamp_duty']).replace('Rs ', '₹')}", "voice": "Stamp duty at seven percent is about four point two lakh."},
            {"screen": f"Registration: {lakh(_C60['registration']).replace('Rs ', '₹')}", "voice": "Registration is capped at thirty thousand rupees."},
            {"screen": f"GST, under construction: {lakh(_C60['gst']).replace('Rs ', '₹')}", "voice": "GST on an under-construction flat adds about three lakh."},
            {"screen": "Parking and deposits: *extra*", "voice": "Parking and deposits come on top. Ask for the all-in cost sheet first."},
        ),
        cta={"screen": "Save this before you book.", "voice": "Save this before you book."},
        caption=("A ₹60 lakh flat in Pune can cost about ₹66.5 lakh. Here is the sum.\n\nExample: a man buying an under-construction flat advertised at "
                 f"₹60 lakh, inside Pune's municipal limits. Stamp duty 7% = {lakh(_C60['stamp_duty'])}. Registration = {lakh(_C60['registration'])} "
                 f"(1%, capped). GST 5% on two-thirds of the price = {lakh(_C60['gst'])}. Total {lakh(_C60['total'])}, before parking, maintenance "
                 f"deposit and other charges. A ready home with an occupancy certificate has no GST ({lakh(_C60_READY['total'])}). Women pay 1% less "
                 "stamp duty. Ask the builder for an all-in cost sheet in writing."),
        tags=("#PuneProperty", "#HomeBuyingTips", "#PuneHomes", "#MahaRERA"),
    ),
]
BY_SLUG = {t.slug: t for t in TRENDS}


# ---- checks --------------------------------------------------------------------------------------------------------------------------
def fact_text(reel: TrendReel) -> str:
    return "\n".join([FACTS[i].text for i in reel.facts if i in FACTS] + list(reel.derived))


def script_of(reel: TrendReel) -> Dict:
    return {"beats": [dict(b) for b in reel.beats], "cta_screen": reel.cta["screen"], "cta_voice": reel.cta["voice"]}


def check(reel: TrendReel, today: Optional[date] = None) -> List[str]:
    """Why this reel must not go out as it is (empty = fine). The human still approves it."""
    today = today or date.today()
    problems: List[str] = []
    for i in reel.facts:
        f = FACTS.get(i)
        if f is None:
            problems.append(f"unknown fact {i}")
        elif date.fromisoformat(f.valid_until) < today:
            problems.append(f"fact {i} expired on {f.valid_until}: re-check it")
    if not director.valid_script(script_of(reel), fact_text(reel)):
        problems.append("a screen line or voice line has a number that is not in the facts, or is too long, or is not 3-5 beats plus a call to action")
    first = reel.caption.splitlines()[0]
    problems += [f"hook: {p}" for p in hook_problems(first)]
    if reel.beats[0]["screen"].split()[0].lower() in ("don't", "never"):
        problems.append("a scare hook ('don't buy ...') is advice we cannot back")
    return problems


def secondary_facts(reel: TrendReel) -> List[Fact]:
    """Facts a human must confirm against the official source before approving the reel."""
    return [FACTS[i] for i in reel.facts if FACTS[i].kind == SECONDARY]


def captions(reel: TrendReel) -> Dict[str, str]:
    """Instagram and Facebook captions: the text, a source line per fact (dated), and the standard disclaimer."""
    src = "\n".join(f"Source: {FACTS[i].source}, {FACTS[i].as_of}" for i in reel.facts)
    body = f"{reel.caption}\n\n{src}\n\nGeneral information, not investment, tax or legal advice."
    return {"instagram": f"{body}\n\n{' '.join(reel.tags)} #Avasetu", "facebook": body}


# ---- render --------------------------------------------------------------------------------------------------------------------------
def render(reel: TrendReel, out_path: Path, lang: str = "en", voiced: Optional[bool] = None, today: Optional[date] = None) -> Path:
    """The mp4 (and its cover next to it). Narrated when a TTS key is set (or `voiced=True`), else the Avasetu theme music alone.
    Refuses a reel that fails `check` (as of `today`, default the real date)."""
    problems = check(reel, today)
    if problems:
        raise ValueError(f"{reel.slug}: " + "; ".join(problems))
    voiced = voice.available() if voiced is None else voiced
    return director.build(script_of(reel), [], lang, Path(out_path), kicker="PUNE PROPERTY, PLAINLY", voiced=voiced)
