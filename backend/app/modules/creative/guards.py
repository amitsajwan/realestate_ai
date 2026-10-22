"""Moved to app.platform.guards (copy guards are platform code, used by inventory too: docs/ARCHITECTURE.md §3). This path is kept, as the same module, until nothing imports it (docs/MODERNIZATION.md rule 3)."""
import sys

from app.platform import guards as _moved

sys.modules[__name__] = _moved
