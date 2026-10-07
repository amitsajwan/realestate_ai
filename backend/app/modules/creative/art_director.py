"""Layer 3, the art director: Copy (+ Angle) -> Design (layout id, palette variant, photo, emphasis words).

Picks from the layout library so consecutive posts never look the same: a layout used in the last two posts is avoided when any
alternative exists, and the palette variant rotates with the seed. Pure and deterministic for a given seed.
"""
import re
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from .catalog import layouts_for, palettes_for
from .layouts.base import photo_keys
from .models import SIZES, Angle, Copy, Design

STOP = set("the a an and or of to for in on at is are was be you your we our it this that with from as by do does not no vs how what why who".split())
POWER = ("nobody", "never", "mistake", "myth", "hidden", "skip", "stop", "free", "wrong", "before", "without", "real", "only", "messy", "clean",
         "interested", "lead", "leads", "miss", "lose", "losing", "ready", "check", "sign", "token", "approved", "carpet")


def emphasis_words(hook: str, limit: int = 2) -> Tuple[str, ...]:
    """Words worth colouring: numbers first, then power words, then the longest content word."""
    toks = [t.strip(".,!?:;\"'“”—-()") for t in hook.split()]
    picks: List[str] = [t for t in toks if re.fullmatch(r"\d+[\w%]*", t)]
    picks += [t for t in toks if t.lower() in POWER and t not in picks]
    if not picks:
        rest = sorted((t for t in toks if t and t.lower() not in STOP and len(t) >= 5), key=len, reverse=True)
        picks = rest[:1]
    return tuple(dict.fromkeys(picks))[:limit]


def choose_layout(fmt: str, audience: str, recent: Sequence[str], seed: int) -> str:
    opts = layouts_for(fmt, audience)
    if not opts:
        raise ValueError(f"no layout for format {fmt!r} and audience {audience!r}")
    last2 = list(recent[-2:])
    tiers = [[o for o in opts if o not in last2], [o for o in opts if o != (recent[-1] if recent else None)], opts]
    pool = next(t for t in tiers if t)
    return pool[seed % len(pool)]


def choose_palette(layout: str, recent: Sequence[str], seed: int) -> str:
    opts = palettes_for(layout)
    return opts[(seed + len(recent)) % len(opts)]


def choose_photo(seed: int, preferred: str = "", layout: str = "photo_led") -> str:
    keys = photo_keys()
    if preferred and (preferred in keys or preferred == "none" or Path(preferred).is_file()):
        return preferred  # a bundled key, a real photo file (a listing's own), or "none" (no photo: a plot is not a tower)
    if layout == "product_showcase":  # the phone shows an interior listing photo
        keys = [k for k in keys if k.startswith("living")] or keys
    return keys[seed % len(keys)] if keys else ""


def choose(copy: Copy, angle: Angle, recent_layouts: Sequence[str] = (), seed: int = 0, preferred_photo: str = "") -> Design:
    layout = choose_layout(angle.fmt, angle.audience, recent_layouts, seed)
    palette = choose_palette(layout, recent_layouts, seed)
    photo = choose_photo(seed, preferred_photo, layout) if layout in ("photo_led", "product_showcase") else ""
    hook_for_emphasis = copy.hook
    return Design(layout=layout, palette=palette, photo=photo, emphasis=emphasis_words(hook_for_emphasis), size=SIZES[angle.channel],
                  notes=f"{layout} / {palette} for a {angle.fmt} ({angle.audience}); avoided {list(recent_layouts[-2:])}")
