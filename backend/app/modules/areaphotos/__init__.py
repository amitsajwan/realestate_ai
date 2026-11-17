"""Area photos: real photos of each area we cover, shown at the top of its guide (/localities/<slug>), docs/plan/area-pictures.md
step 4. Owns the collection `area_photos` (only writer).

Two kinds only, both saying who took them and when: our own (the team or a local agent shot it) and free-licensed ones entered
by hand (Wikimedia Commons and the like: author, licence, link). Never an AI picture, never a copy from a portal or a builder's
site. Agents upload in Studio; a photo waits (`pending`) until the owner publishes it, and the owner may hide it again.

The photo scout (`scout.py`, loop in `runner.py`, AREA_PHOTO_SCOUT) finds free-licensed Commons photos itself, judges them with
Gemini vision, and keeps up to 8 per area as `suggested` -- still the owner's tap to publish (rule 6: no AI agent publishes).
"""
from .service import COLLECTION, LICENCES, AreaPhotos, PhotoRefused

__all__ = ["COLLECTION", "LICENCES", "AreaPhotos", "PhotoRefused"]
