"""Brand palettes. The brand is navy and gold; two accent variants and a light "cream" variant keep a feed from looking uniform."""
from dataclasses import dataclass
from typing import Dict, Tuple

RGB = Tuple[int, int, int]


@dataclass(frozen=True)
class Palette:
    id: str
    bg_top: RGB
    bg_bottom: RGB
    ink: RGB            # main text on the background
    muted: RGB          # secondary text on the background
    accent: RGB         # accent used as TEXT / strokes on the background
    accent_fill: RGB    # accent used as a filled shape
    accent_ink: RGB     # text on an accent_fill
    card: RGB           # raised surface
    card_ink: RGB
    card_muted: RGB
    edge: RGB           # hairlines
    glow: RGB
    light: bool = False


GOLD = (240, 180, 64)
MYTH_RED = (196, 48, 52)
FACT_GREEN = (18, 128, 80)

PALETTES: Dict[str, Palette] = {p.id: p for p in (
    Palette("navy_gold", (26, 54, 98), (9, 20, 42), (255, 255, 255), (184, 197, 220), GOLD, GOLD, (24, 30, 44),
            (31, 60, 104), (255, 255, 255), (190, 202, 224), (70, 102, 152), GOLD),
    Palette("navy_teal", (10, 48, 68), (5, 22, 36), (255, 255, 255), (178, 204, 214), (78, 222, 196), (78, 222, 196), (4, 30, 40),
            (16, 66, 88), (255, 255, 255), (184, 210, 220), (52, 112, 134), (78, 222, 196)),
    Palette("navy_coral", (40, 34, 92), (13, 13, 40), (255, 255, 255), (194, 192, 226), (255, 136, 110), (255, 136, 110), (40, 12, 16),
            (52, 46, 112), (255, 255, 255), (204, 202, 232), (96, 88, 166), (255, 136, 110)),
    Palette("cream", (252, 248, 240), (238, 229, 211), (16, 35, 64), (84, 96, 118), (160, 92, 0), GOLD, (24, 30, 44),
            (255, 255, 255), (16, 35, 64), (84, 96, 118), (218, 205, 180), (240, 180, 64), True),
)}


def get(pid: str) -> Palette:
    return PALETTES.get(pid) or PALETTES["navy_gold"]


def luminance(c: RGB) -> float:
    def ch(v: float) -> float:
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(a: RGB, b: RGB) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)
