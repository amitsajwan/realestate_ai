"""The layout library. Each layout module exposes render(copy, design) -> list[Rendered] (one image, or a carousel)."""
from importlib import import_module
from pathlib import Path
from typing import Dict, List

from ..catalog import LAYOUTS
from ..models import Copy, Design
from .base import Rendered, card, card_photo, violations  # noqa: F401


OWN_PHOTO_LAYOUTS = ("photo_led", "product_showcase")   # they place the photo themselves


def render_layout(copy: Copy, design: Design) -> List[Rendered]:
    if design.layout not in LAYOUTS:
        raise ValueError(f"unknown layout {design.layout!r}")
    backdrop = design.photo if design.layout not in OWN_PHOTO_LAYOUTS and design.photo and Path(design.photo).is_file() else None
    with card(language=copy.language, card_brand=design.brand), card_photo(backdrop):
        return import_module(f"{__name__}.{design.layout}").render(copy, design)


def all_layouts() -> List[str]:
    return list(LAYOUTS)
