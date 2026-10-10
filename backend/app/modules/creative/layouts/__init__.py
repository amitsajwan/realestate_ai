"""The layout library. Each layout module exposes render(copy, design) -> list[Rendered] (one image, or a carousel)."""
from importlib import import_module
from pathlib import Path
from typing import Dict, List

from ..catalog import LAYOUTS
from ..models import Copy, Design
from .base import Rendered, card, card_photo, photo_pass, violations  # noqa: F401


OWN_PHOTO_LAYOUTS = ("photo_led", "product_showcase")   # they place the photo themselves


def render_layout(copy: Copy, design: Design) -> List[Rendered]:
    if design.layout not in LAYOUTS:
        raise ValueError(f"unknown layout {design.layout!r}")
    backdrop = design.photo if design.layout not in OWN_PHOTO_LAYOUTS and design.photo and Path(design.photo).is_file() else None
    layout = import_module(f"{__name__}.{design.layout}")
    with card(language=copy.language, card_brand=design.brand), card_photo(backdrop):
        if not backdrop:
            return layout.render(copy, design)
        with photo_pass("measure") as state:   # where the text goes, then one soft band behind all of it
            layout.render(copy, design)
        with photo_pass("draw", state):
            return layout.render(copy, design)


def all_layouts() -> List[str]:
    return list(LAYOUTS)
