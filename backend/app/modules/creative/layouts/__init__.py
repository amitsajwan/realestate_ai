"""The layout library. Each layout module exposes render(copy, design) -> list[Rendered] (one image, or a carousel)."""
from importlib import import_module
from typing import Dict, List

from ..catalog import LAYOUTS
from ..models import Copy, Design
from .base import Rendered, card, violations  # noqa: F401


def render_layout(copy: Copy, design: Design) -> List[Rendered]:
    if design.layout not in LAYOUTS:
        raise ValueError(f"unknown layout {design.layout!r}")
    with card(language=copy.language, card_brand=design.brand):
        return import_module(f"{__name__}.{design.layout}").render(copy, design)


def all_layouts() -> List[str]:
    return list(LAYOUTS)
