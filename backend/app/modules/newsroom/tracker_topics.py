"""Which tracker a headline is about, from the trackers' own `match` rules (tracker_data/<slug>.json), with nothing else loaded.

The news filter needs this and trackers.py imports the filter (`same_story`), so the filter reads the rules here rather than
from trackers.py. The rules are the same hand-written patterns trackers.py attaches reports by: every `all` pattern, at least
one `any` pattern when there are any, no `not` pattern."""
import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

DATA = Path(__file__).with_name("tracker_data")
_SPACE = re.compile(r"\s+")

Rules = Dict[str, List["re.Pattern[str]"]]


@lru_cache(maxsize=1)
def rules() -> Dict[str, Tuple[Rules, List[str]]]:
    """slug -> (compiled rules, the areas it touches), in file-name order. A broken file is skipped, never a crash."""
    out: Dict[str, Tuple[Rules, List[str]]] = {}
    for path in sorted(DATA.glob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            compiled = {k: [re.compile(p, re.I) for p in d.get("match", {}).get(k, [])] for k in ("all", "any", "not")}
            if compiled["all"] or compiled["any"]:   # a tracker without rules matches nothing
                out[d["slug"]] = (compiled, list(d.get("areas") or []))
        except Exception as e:
            log.warning("tracker topics: %s skipped: %s", path.name, e)
    return out


def _hit(r: Rules, t: str) -> bool:
    return all(p.search(t) for p in r["all"]) and (not r["any"] or any(p.search(t) for p in r["any"])) and not any(p.search(t) for p in r["not"])


def topic_of(title: str) -> Optional[Tuple[str, List[str]]]:
    """(slug, areas) of the first tracker whose rules match the headline, or None."""
    t = _SPACE.sub(" ", title or "").strip().lower()
    if not t:
        return None
    for slug, (r, areas) in rules().items():
        if _hit(r, t):
            return slug, areas
    return None
