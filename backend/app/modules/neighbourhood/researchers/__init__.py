"""The registry: every kind of fact the module keeps. Add a researcher here and the loop runs it and the views show it."""
from typing import Dict, Tuple

from . import being_built, commute, jobs, profile, rent, schools
from .base import Context, Found, Researcher, ViewContext

REGISTRY: Tuple[Researcher, ...] = (commute.RESEARCHER, schools.RESEARCHER, rent.RESEARCHER, profile.RESEARCHER,
                                    being_built.RESEARCHER, jobs.RESEARCHER)
BY_KIND: Dict[str, Researcher] = {r.kind: r for r in REGISTRY}

__all__ = ["REGISTRY", "BY_KIND", "Context", "Found", "Researcher", "ViewContext"]
