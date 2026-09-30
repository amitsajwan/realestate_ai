"""Which layout can carry which format and audience. Metadata only (no drawing), so every stage can import it cheaply."""
from typing import Dict, List, Tuple

PALETTE_IDS = ("navy_gold", "navy_teal", "navy_coral", "cream")

# layout id -> (formats it can carry, audiences, palettes allowed)
LAYOUTS: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]] = {
    "big_number": (("stat",), ("buyer", "agent"), PALETTE_IDS),
    "myth_fact": (("myth-vs-fact",), ("buyer", "agent"), PALETTE_IDS),
    "checklist": (("carousel", "checklist"), ("buyer", "agent"), PALETTE_IDS),
    "poll": (("poll",), ("buyer", "agent"), PALETTE_IDS),
    "before_after": (("before-after",), ("buyer", "agent"), PALETTE_IDS),
    "photo_led": (("single",), ("buyer",), ("navy_gold", "navy_teal", "navy_coral")),
    "product_showcase": (("single",), ("agent",), ("navy_gold", "navy_teal", "navy_coral")),
    "quote_tip": (("single",), ("buyer", "agent"), PALETTE_IDS),
}


def layouts_for(fmt: str, audience: str) -> List[str]:
    return [k for k, (fmts, auds, _) in LAYOUTS.items() if fmt in fmts and audience in auds]


def palettes_for(layout: str) -> Tuple[str, ...]:
    return LAYOUTS[layout][2]
