"""Which tracker a headline is about, from the trackers' own `match` rules (tracker_data/<slug>.json), with nothing else loaded.

The news filter needs this and trackers.py imports the filter (`same_story`), so the filter reads the rules here rather than
from trackers.py. The rules are the same hand-written patterns trackers.py attaches reports by: every `all` pattern, at least
one `any` pattern when there are any, no `not` pattern.

Trackers the owner added in Studio from the topic finder live in Mongo (newsroom_trackers, `definition`), not in a file. The
filter is plain code with no database, so trackers.refresh() hands their rules in here (`set_defined`) each cycle; a file's
tracker wins over a Studio one of the same slug."""
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


_DEFINED: Dict[str, Tuple[Rules, List[str]]] = {}


def compile_rules(match: dict) -> Rules:
    """A tracker's `match` block as compiled patterns (raises on a bad pattern)."""
    return {k: [re.compile(p, re.I) for p in (match or {}).get(k, [])] for k in ("all", "any", "not")}


_DEFINED_QUERIES: List[str] = []
QUERIES_MAX = 4  # Google News searches per tracker


@lru_cache(maxsize=1)
def _files() -> Tuple[dict, ...]:
    """The tracker files as read, in file-name order; a file that is not JSON is skipped."""
    out = []
    for path in sorted(DATA.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception as e:
            log.warning("tracker topics: %s skipped: %s", path.name, e)
    return tuple(out)


def _queries_of(d: dict) -> List[str]:
    return [q.strip() for q in (d.get("queries") or []) if isinstance(q, str) and q.strip()][:QUERIES_MAX]


@lru_cache(maxsize=1)
def file_rules() -> Dict[str, Tuple[Rules, List[str]]]:
    """slug -> (compiled rules, the areas it touches) of the tracker files, in file-name order. A broken file is skipped."""
    out: Dict[str, Tuple[Rules, List[str]]] = {}
    for d in _files():
        try:
            compiled = compile_rules(d.get("match", {}))
            if compiled["all"] or compiled["any"]:   # a tracker without rules matches nothing
                out[d["slug"]] = (compiled, list(d.get("areas") or []))
        except Exception as e:
            log.warning("tracker topics: %s skipped: %s", d.get("slug"), e)
    return out


def queries() -> List[str]:
    """Every tracker's own Google News searches (`queries`, 2-4 phrases each), files first, in order: so a tracker's news comes in
    even when the report names none of our areas (before 2026-11-28 only area names and a dozen buyer searches were asked)."""
    out: List[str] = []
    for d in _files():
        out += _queries_of(d)
    return out + _DEFINED_QUERIES


def set_defined(defs: Dict[str, dict]) -> None:
    """The Studio-added trackers' definitions (already checked by trackers.refresh), replacing the ones handed in before."""
    out: Dict[str, Tuple[Rules, List[str]]] = {}
    for slug, d in defs.items():
        try:
            compiled = compile_rules(d.get("match", {}))
        except re.error:
            continue
        if compiled["all"] or compiled["any"]:
            out[slug] = (compiled, list(d.get("areas") or []))
    _DEFINED.clear()
    _DEFINED.update(out)
    files = {d.get("slug") for d in _files()}
    _DEFINED_QUERIES[:] = [q for slug, d in defs.items() if slug not in files for q in _queries_of(d)]


def rules() -> Dict[str, Tuple[Rules, List[str]]]:
    """Every tracker's rules: the files first, then the Studio-added ones whose slug no file has."""
    files = file_rules()
    return {**files, **{k: v for k, v in _DEFINED.items() if k not in files}}


def hit(r: Rules, t: str) -> bool:
    return all(p.search(t) for p in r["all"]) and (not r["any"] or any(p.search(t) for p in r["any"])) and not any(p.search(t) for p in r["not"])


def any_topic(title: str) -> bool:
    """True when some tracker's rules match the headline (the topic finder leaves those out)."""
    return topic_of(title) is not None


def topic_of(title: str) -> Optional[Tuple[str, List[str]]]:
    """(slug, areas) of the first tracker whose rules match the headline, or None."""
    t = _SPACE.sub(" ", title or "").strip().lower()
    if not t:
        return None
    for slug, (r, areas) in rules().items():
        if hit(r, t):
            return slug, areas
    return None
