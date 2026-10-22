"""Moved to app.modules.listings.points (a listing's selling points are inventory's: listings.schemas checks them). This path is kept, as the same module, until nothing imports it (docs/MODERNIZATION.md rule 3)."""
import sys

from app.modules.listings import points as _moved

sys.modules[__name__] = _moved
