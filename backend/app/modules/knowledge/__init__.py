"""Knowledge: what we may say about a home, a post or an area, and grounded replies built only from that.
Public API: area_facts (areas.py), facts_for / Ref / Grounding (grounding.py), answer / Reply / has_topic (reply.py)."""
from .areas import AREAS, AreaFacts, area_facts
from .grounding import Grounding, Ref, facts_for
from .reply import Reply, answer, has_topic

__all__ = ["AREAS", "AreaFacts", "area_facts", "Grounding", "Ref", "facts_for", "Reply", "answer", "has_topic"]
