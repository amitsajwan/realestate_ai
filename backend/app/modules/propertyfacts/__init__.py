"""Property facts gathered automatically for a listing (docs/CONTENT_PLATFORM.md, property campaign track PF-1 to PF-7).

Every fact keeps where it came from; code decides how far it can be trusted (`facts.decide`). Only usable facts reach posts, and
facts the agent confirmed from the builder's brochure (`brochure`, level builder_claim) only with "as per the builder's brochure".

Public API: the brochure kit (`Brochures`, `BrochureError`, `kit_out`, `read_pdf`) and the fact levels (`Fact`, `Reading`,
`decide`, `sheet`)."""
from .brochure import BrochureError, Brochures, kit_out, read_pdf
from .facts import Fact, Reading, decide, sheet

__all__ = ["BrochureError", "Brochures", "Fact", "Reading", "decide", "kit_out", "read_pdf", "sheet"]
