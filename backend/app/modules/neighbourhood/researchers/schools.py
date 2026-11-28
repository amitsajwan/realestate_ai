"""Researcher: schools. A stub laid down with the module (docs/plan/pune-intelligence.md); its workstream fills it in."""
from datetime import timedelta
from typing import Any, Optional

from .base import Context, Found, Researcher, ViewContext


async def _run(ctx: Context, place: str) -> Optional[Found]:
    return None


def _present(data: Any, view: ViewContext) -> Optional[dict]:
    return None


RESEARCHER = Researcher(kind="schools", every=timedelta(days=30), run=_run, present=_present)
