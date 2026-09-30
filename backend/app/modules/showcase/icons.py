"""Amenity icons drawn with Pillow shapes (supersampled 4x for clean edges). No icon font, no downloads."""
from typing import Tuple

from PIL import Image, ImageDraw

SS = 4  # supersampling factor


def _draw_shape(d: ImageDraw.ImageDraw, key: str, s: int, ink) -> None:
    """Draw the glyph for `key` inside an s x s box (s already supersampled), centred, using ~60% of the box."""
    u = s / 100.0

    def P(*pts):
        return [(x * u, y * u) for x, y in pts]

    w = max(2, int(5 * u))
    if key == "parking":  # a car from the side
        d.rounded_rectangle([18 * u, 46 * u, 82 * u, 66 * u], radius=6 * u, fill=ink)
        d.polygon(P((30, 46), (40, 32), (62, 32), (72, 46)), fill=ink)
        for cx in (34, 66):
            d.ellipse([(cx - 8) * u, 58 * u, (cx + 8) * u, 74 * u], fill=ink)
    elif key == "lift":  # a lift door with up and down arrows
        d.rounded_rectangle([26 * u, 20 * u, 74 * u, 80 * u], radius=5 * u, outline=ink, width=w)
        d.line([50 * u, 22 * u, 50 * u, 78 * u], fill=ink, width=max(2, int(3 * u)))
        d.polygon(P((38, 44), (32, 54), (44, 54)), fill=ink)
        d.polygon(P((62, 56), (56, 46), (68, 46)), fill=ink)
    elif key == "gym":  # dumbbell
        d.rounded_rectangle([30 * u, 46 * u, 70 * u, 54 * u], radius=3 * u, fill=ink)
        d.rounded_rectangle([20 * u, 34 * u, 32 * u, 66 * u], radius=4 * u, fill=ink)
        d.rounded_rectangle([68 * u, 34 * u, 80 * u, 66 * u], radius=4 * u, fill=ink)
        d.rectangle([12 * u, 43 * u, 20 * u, 57 * u], fill=ink)
        d.rectangle([80 * u, 43 * u, 88 * u, 57 * u], fill=ink)
    elif key == "pool":  # two waves over a ladder
        for y in (56, 72):
            d.arc([14 * u, (y - 10) * u, 40 * u, (y + 6) * u], 180, 360, fill=ink, width=w)
            d.arc([38 * u, (y - 10) * u, 62 * u, (y + 6) * u], 0, 180, fill=ink, width=w)
            d.arc([60 * u, (y - 10) * u, 86 * u, (y + 6) * u], 180, 360, fill=ink, width=w)
        d.line([38 * u, 50 * u, 38 * u, 26 * u], fill=ink, width=w)
        d.line([58 * u, 50 * u, 58 * u, 26 * u], fill=ink, width=w)
        d.arc([38 * u, 16 * u, 58 * u, 36 * u], 180, 360, fill=ink, width=w)
    elif key == "clubhouse":  # a little house
        d.polygon(P((50, 18), (16, 46), (84, 46)), fill=ink)
        d.rectangle([24 * u, 46 * u, 76 * u, 80 * u], fill=ink)
        d.rectangle([44 * u, 58 * u, 56 * u, 80 * u], fill=(0, 0, 0, 0))
    elif key == "security":  # a shield with a check
        d.polygon(P((50, 16), (80, 26), (78, 54), (50, 84), (22, 54), (20, 26)), fill=ink)
        d.line(P((37, 50), (47, 60), (65, 38)), fill=(0, 0, 0, 0), width=max(3, int(7 * u)), joint="curve")
    elif key == "garden":  # a tree
        d.ellipse([24 * u, 16 * u, 76 * u, 62 * u], fill=ink)
        d.rectangle([45 * u, 56 * u, 55 * u, 84 * u], fill=ink)
    elif key == "power":  # lightning bolt
        d.polygon(P((56, 14), (28, 54), (46, 54), (40, 86), (72, 42), (54, 42)), fill=ink)
    elif key == "play":  # a seesaw
        d.polygon(P((50, 56), (38, 82), (62, 82)), fill=ink)
        d.polygon(P((16, 44), (22, 38), (84, 62), (78, 68)), fill=ink)
        d.ellipse([10 * u, 24 * u, 28 * u, 42 * u], fill=ink)
        d.ellipse([72 * u, 46 * u, 90 * u, 64 * u], fill=ink)
    else:  # unknown key: a plain dot
        d.ellipse([36 * u, 36 * u, 64 * u, 64 * u], fill=ink)


def icon_tile(key: str, diameter: int, bg=(240, 180, 64), ink=(24, 30, 44)) -> Image.Image:
    """A round badge (`bg`) with the glyph for `key` knocked out in `ink`. RGBA, `diameter` px."""
    s = diameter * SS
    tile = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(tile).ellipse([0, 0, s - 1, s - 1], fill=tuple(bg) + (255,))
    glyph = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    _draw_shape(ImageDraw.Draw(glyph), key, s, tuple(ink) + (255,))
    # glyph cut-outs drawn with alpha 0 must erase the ink only, so composite ink layer then punch holes
    holes = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    hd = ImageDraw.Draw(holes)
    if key == "clubhouse":
        hd.rectangle([44 * s / 100, 58 * s / 100, 56 * s / 100, 80 * s / 100], fill=tuple(bg) + (255,))
    if key == "security":
        hd.line([(37 * s / 100, 50 * s / 100), (47 * s / 100, 60 * s / 100), (65 * s / 100, 38 * s / 100)], fill=tuple(bg) + (255,),
                width=max(3, int(7 * s / 100)), joint="curve")
    # shrink the glyph to ~62% of the badge and centre it
    inner = int(s * 0.62)
    g = Image.alpha_composite(glyph, holes).resize((inner, inner), Image.LANCZOS)
    tile.alpha_composite(g, ((s - inner) // 2, (s - inner) // 2))
    return tile.resize((diameter, diameter), Image.LANCZOS)


def check_tile(diameter: int, bg=(240, 180, 64), ink=(24, 30, 44)) -> Image.Image:
    s = diameter * SS
    tile = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.ellipse([0, 0, s - 1, s - 1], fill=tuple(bg) + (255,))
    u = s / 100.0
    d.line([(29 * u, 52 * u), (44 * u, 66 * u), (71 * u, 35 * u)], fill=tuple(ink) + (255,), width=max(3, int(9 * u)), joint="curve")
    return tile.resize((diameter, diameter), Image.LANCZOS)
