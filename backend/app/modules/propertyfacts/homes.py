"""Moved to app.modules.listings.homes (a listing's home types are inventory's: marketing and the posts read them). This path is kept, as the same module, until nothing imports it (docs/MODERNIZATION.md rule 3)."""
import sys

from app.modules.listings import homes as _moved

sys.modules[__name__] = _moved
