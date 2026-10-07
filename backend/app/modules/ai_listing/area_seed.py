"""Curated, stable area statements for the 'about' suggestion. Nothing here is invented: every line is either
general wording about a corridor or traceable to the source listed beside it. No prices, no predictions, no
distances or travel times. Metro wording is always 'approved is not running'.

Kept in step with frontend/lib/marketing/localities.ts (the public area guides).
"""
from typing import Optional

_L4 = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2194691&reg=48&lang=2"
_2B = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2139488&reg=48&lang=2"
_WTC = "https://www.wtca.org/world-trade-center-pune"

METRO_L4 = "Metro Line 4 (Kharadi to Khadakwasla) is approved, not running yet. Check the latest status with Maha-Metro."
METRO_2B = "Metro Corridor 2B (Ramwadi to Wagholi) is approved, not running yet. Check the latest status with Maha-Metro."

AREA_SEED: dict[str, dict] = {
    "kharadi": {
        "name": "Kharadi",
        "connectivity": [
            {"text": "On Pune's eastern IT corridor, close to large office campuses.", "source_url": _WTC},
            {"text": METRO_L4, "source_url": _L4},
        ],
        "nearby": [
            {"type": "office", "name": "EON Free Zone", "source_url": _WTC},
            {"type": "office", "name": "World Trade Center Pune", "source_url": _WTC},
        ],
    },
    "upper_kharadi": {
        "name": "Upper Kharadi",
        "connectivity": [
            {"text": "On the same eastern corridor as Kharadi and Wagholi.", "source_url": _L4},
            {"text": METRO_L4, "source_url": _L4},
            {"text": METRO_2B, "source_url": _2B},
        ],
        "nearby": [],
    },
    "wagholi": {
        "name": "Wagholi",
        "connectivity": [
            {"text": "On the eastern corridor of Pune, further out than Kharadi.", "source_url": _2B},
            {"text": METRO_2B, "source_url": _2B},
        ],
        "nearby": [],
    },
}


def area_key(locality: Optional[str]) -> Optional[str]:
    k = " ".join((locality or "").lower().replace("-", " ").replace("_", " ").split())
    k = k.replace(" ", "_")
    return k if k in AREA_SEED else None
