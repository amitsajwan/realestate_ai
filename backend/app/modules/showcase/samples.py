"""Sample-home dataset for the showcase posts.

Every home here is an ILLUSTRATION: labelled 'Sample listing' on every image and in every caption, not available for sale,
with stock photos (free licence, credited in docs/brand/photo-credits.md). Numbers are labelled sample figures only.
Real agent listings (future) use the agent's own photos; nothing here ever stands in for one.
"""
from app.core import brand
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.modules.marketing.facts import bhk_label, money, sqft

PHOTO_DIR = Path(__file__).parent / "assets" / "photos"

SAMPLE_LABEL = "Sample listing"
SAMPLE_RIBBON = "SAMPLE HOME"
SAMPLE_NOTE = "Illustrative home, not available for sale; real agent listings coming"
RERA_LINE = "RERA number: shown on real listings"
IG_CTA = "Comment INTERESTED for details on this sample"
AGENTS_CTA = "Agents: list your homes free, link in bio"
BRAND = brand.NAME


@dataclass(frozen=True)
class Photo:
    file: str                      # file name under assets/photos/
    kind: str                      # 'exterior' | 'interior'
    photographer: str
    source_url: str                # the Unsplash page
    focus: Tuple[float, float] = (0.5, 0.5)  # where the subject sits (0..1) so crops keep it

    @property
    def path(self) -> Path:
        return PHOTO_DIR / self.file


def _u(file: str, kind: str, who: str, pid: str, focus=(0.5, 0.5)) -> Photo:
    return Photo(file, kind, who, f"https://unsplash.com/photos/{pid}", focus)


@dataclass(frozen=True)
class Home:
    slug: str
    locality: str
    bhk: int
    carpet_sqft: int
    floor: int
    total_floors: int
    possession: str                # 'Ready to move' or 'Under construction, possession Dec 2027'
    ready: bool
    price_inr: int                 # a labelled SAMPLE figure
    furnishing: str
    amenities: Tuple[str, ...]     # keys of ICON_LABELS
    highlights: Tuple[str, str, str]
    photos: Tuple[Photo, ...]
    facing: str = ""

    @property
    def title(self) -> str:
        return f"{bhk_label(self.bhk)} in {self.locality}"

    @property
    def carpet_text(self) -> str:
        return sqft(self.carpet_sqft)

    @property
    def price_text(self) -> str:
        return money(self.price_inr)

    @property
    def floor_text(self) -> str:
        return f"Floor {self.floor} of {self.total_floors}"

    @property
    def exterior(self) -> Photo:
        return next(p for p in self.photos if p.kind == "exterior")

    @property
    def interiors(self) -> List[Photo]:
        return [p for p in self.photos if p.kind == "interior"]

    @property
    def area_key(self) -> str:
        return self.locality


ICON_LABELS: Dict[str, str] = {
    "parking": "Parking", "lift": "Lift", "gym": "Gym", "pool": "Pool", "clubhouse": "Clubhouse",
    "security": "Security", "garden": "Garden", "power": "Power backup", "play": "Play area",
}

# Two honest, stable lines per locality: facts about where it is, no predictions and no price claims.
AREA_LINES: Dict[str, Tuple[str, str]] = {
    "Kharadi": ("An established IT-office hub on Pune's east side, home to EON IT Park and World Trade Center Pune.",
                "Many residents can walk or take a short ride to work, which can save the long daily commute."),
    "Upper Kharadi": ("Just beyond Kharadi's IT offices, so the same workplaces are a short ride away.",
                      "Newer, quieter residential pockets, with more open space between buildings than central Pune."),
    "Wagholi": ("On the Pune-Nagar road, east of the city, with schools and daily shops inside the locality.",
                "Homes here generally cost less than in Kharadi, so first-time buyers often start their search here."),
}

_T = "Photos: Unsplash"

HOMES: List[Home] = [
    Home("kharadi-2bhk-ready", "Kharadi", 2, 780, 7, 22, "Ready to move", True, 9_800_000, "Semi-furnished",
         ("parking", "lift", "gym", "security", "power"), ("Sunlit living room", "Semi-furnished", "Covered parking"),
         (_u("uRUOLhYJF75w.jpg", "exterior", "Jacob Vathikulam", "RUOLhYJF75w", (0.55, 0.35)),
          _u("uQGxBeUDkeWk.jpg", "interior", "Huy Nguyen", "QGxBeUDkeWk", (0.5, 0.6)),
          _u("u0tVimluL_ls.jpg", "interior", "Spl Interiors", "0tVimluL_ls", (0.5, 0.6))), "East"),
    Home("kharadi-3bhk-ready", "Kharadi", 3, 1050, 12, 25, "Ready to move", True, 14_500_000, "Furnished",
         ("parking", "lift", "gym", "pool", "clubhouse", "security"), ("Fully furnished", "Three bedrooms", "Modular kitchen"),
         (_u("u7Cwct_F0Gbs.jpg", "exterior", "Parth Savani", "7Cwct-F0Gbs", (0.6, 0.35)),
          _u("uAgK_XAqSbfk.jpg", "interior", "Danilo Rios", "AgK_XAqSbfk", (0.45, 0.55)),
          _u("uAgHJm3uKr4U.jpg", "interior", "Anand Kumar", "AgHJm3uKr4U", (0.5, 0.5)),
          _u("ub0DHABrkRcM.jpg", "interior", "Naksha Banwao", "b0DHABrkRcM", (0.5, 0.6))), "North-east"),
    Home("kharadi-2bhk-under-construction", "Kharadi", 2, 820, 15, 28, "Under construction, possession Dec 2027", False,
         10_800_000, "Unfurnished", ("parking", "lift", "pool", "clubhouse", "security", "play"),
         ("Large living room", "Two balconies", "Podium amenities"),
         (_u("u2EmCXrpIKA0.jpg", "exterior", "Parth Savani", "2EmCXrpIKA0", (0.5, 0.45)),
          _u("uAB_q9lwCVv8.jpg", "interior", "Huy Nguyen", "AB-q9lwCVv8", (0.5, 0.55))), "East"),
    Home("upper-kharadi-2bhk-ready", "Upper Kharadi", 2, 720, 4, 14, "Ready to move", True, 7_800_000, "Semi-furnished",
         ("parking", "lift", "garden", "security", "power"), ("Bright, airy rooms", "Semi-furnished", "Garden view"),
         (_u("uPuB5jXhFz5c.jpg", "exterior", "Jakub Pabis", "PuB5jXhFz5c", (0.55, 0.5)),
          _u("uxtDpXi_a_YQ.jpg", "interior", "Med Badr Chemmaoui", "xtDpXi_a-YQ", (0.5, 0.55)),
          _u("u1jy1WNfqHos.jpg", "interior", "Medea Dzagnidze", "1jy1WNfqHos", (0.5, 0.5))), "West"),
    Home("upper-kharadi-3bhk-ready", "Upper Kharadi", 3, 1000, 9, 18, "Ready to move", True, 11_200_000, "Semi-furnished",
         ("parking", "lift", "gym", "garden", "power", "play"), ("Three bedrooms", "Semi-furnished", "Open views"),
         (_u("uNEgt3edkuR4.jpg", "exterior", "Jayanth Muppaneni", "NEgt3edkuR4", (0.5, 0.3)),
          _u("uVZ2z8ozzy10.jpg", "interior", "Prydumano Design", "VZ2z8ozzy10", (0.5, 0.6)),
          _u("umfFyocD9ttI.jpg", "interior", "Anisha Deb", "mfFyocD9ttI", (0.5, 0.55))), "South"),
    Home("upper-kharadi-2bhk-under-construction", "Upper Kharadi", 2, 700, 6, 16, "Under construction, possession Jun 2028",
         False, 7_400_000, "Unfurnished", ("parking", "lift", "garden", "security"),
         ("Wide balcony", "Natural light", "Low-density tower"),
         (_u("uzc5B3H1W1E8.jpg", "exterior", "Parth Savani", "zc5B3H1W1E8", (0.45, 0.4)),
          _u("u2cfj0Y5ch00.jpg", "interior", "Puscas Adryan", "2cfj0Y5ch00", (0.5, 0.6)),
          _u("uKAXJqMoe8OI.jpg", "interior", "Pyx Photography", "KAXJqMoe8OI", (0.5, 0.5))), "East"),
    Home("wagholi-2bhk-under-construction", "Wagholi", 2, 640, 3, 12, "Under construction, possession Dec 2027", False,
         5_500_000, "Unfurnished", ("parking", "lift", "security", "garden", "play"),
         ("Compact, practical layout", "Two bedrooms", "Play area in the society"),
         (_u("u4453DIQWtsQ.jpg", "exterior", "Tobias Wilden", "4453DIQWtsQ", (0.72, 0.5)),
          _u("uGu4R_0lwXVk.jpg", "interior", "Francesca Tosolini", "Gu4R-0lwXVk", (0.5, 0.55)),
          _u("uf9O_1eKGlQM.jpg", "interior", "Amira Aboalnaga", "f9O-1eKGlQM", (0.5, 0.6))), "East"),
    Home("wagholi-3bhk-ready", "Wagholi", 3, 920, 6, 15, "Ready to move", True, 8_200_000, "Semi-furnished",
         ("parking", "lift", "gym", "clubhouse", "security", "power"), ("Three bedrooms", "Semi-furnished", "Clubhouse access"),
         (_u("ulqu_NESnqfc.jpg", "exterior", "Prathamesh Andhale", "lqu-NESnqfc", (0.5, 0.4)),
          _u("uSrioT6tdWII.jpg", "interior", "Collov Home Design", "SrioT6tdWII", (0.5, 0.55)),
          _u("u_TiONiwniJs.jpg", "interior", "Zac Gudakov", "-TiONiwniJs", (0.5, 0.55))), "North"),
    Home("wagholi-2bhk-ready", "Wagholi", 2, 680, 5, 13, "Ready to move", True, 6_200_000, "Unfurnished",
         ("parking", "lift", "security", "garden", "power"), ("Move-in ready", "Two bedrooms", "Gated society"),
         (_u("uIjccw_xakzY.jpg", "exterior", "Md. Ashraful Kabir", "Ijccw_xakzY", (0.6, 0.5)),
          _u("uOhezdWyzXTI.jpg", "interior", "Parth Savani", "OhezdWyzXTI", (0.5, 0.55)),
          _u("ubFfeA69crLc.jpg", "interior", "sarah birasa", "bFfeA69crLc", (0.5, 0.55))), "South"),
]

BY_SLUG: Dict[str, Home] = {h.slug: h for h in HOMES}


def get(slug: str) -> Home:
    try:
        return BY_SLUG[slug]
    except KeyError:
        raise KeyError(f"unknown showcase slug {slug!r}; known: {', '.join(BY_SLUG)}")


def area_lines(h: Home) -> Tuple[str, str]:
    return AREA_LINES[h.locality]


def label_text(h: Home) -> str:
    return f"{SAMPLE_LABEL}: {h.title}"
