"""PF-1: readings from sources -> facts with a trust level. Pure: no I/O.

A reading is one source's value for one key. A fact is the decision over all readings of that key:

    official      a MahaRERA reading, or the agent's own listing (their offer) -> usable
    measured      computed by our code (OSM distance, price per sq ft, EMI)  -> usable
    corroborated  two independent sources give the same value                -> usable
    single        one source only                                            -> stored, not posted
    conflict      sources disagree and nothing official settles it          -> not posted; raise an issue

An official or measured value wins over portals; portal readings that disagree with it are kept in `disagree` so the
mismatch can be shown (a portal saying "Dec 2028" when MahaRERA now says 2029-04-30)."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

OFFICIAL = frozenset({"maharera", "listing"})  # "listing": the agent's own offer (their asking price is the price)
MEASURED = frozenset({"osm", "calc"})
USABLE = ("official", "measured", "corroborated")
NUMBER_TOLERANCE = 0.05  # two numbers within 5% of each other are the same reading (portals round differently)


@dataclass(frozen=True)
class Reading:
    key: str            # "possession_now", "price_min_inr", "nearby.hospital"
    value: Any          # str, int, float or a short list
    source: str         # "maharera", "osm", "calc", "99acres", "magicbricks", "housing", "listing"
    url: str = ""
    fetched_at: Optional[datetime] = None


@dataclass
class Fact:
    key: str
    value: Any
    level: str
    readings: List[Reading] = field(default_factory=list)   # the readings that agree with `value`
    disagree: List[Reading] = field(default_factory=list)   # readings that say something else

    @property
    def usable(self) -> bool:
        return self.level in USABLE

    @property
    def sources(self) -> List[str]:
        return sorted({r.source for r in self.readings})


def _norm(v: Any) -> Any:
    if isinstance(v, str):
        return " ".join(v.lower().split())
    if isinstance(v, dict):
        return tuple(sorted((k, repr(_norm(x))) for k, x in v.items()))
    if isinstance(v, (list, tuple)):
        return tuple(sorted((_norm(x) for x in v), key=repr))
    return v


def same(a: Any, b: Any) -> bool:
    """Equal after normalising text; numbers within NUMBER_TOLERANCE of each other."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b  # True == 1 in Python; not here
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if a == b:
            return True
        return abs(a - b) <= NUMBER_TOLERANCE * max(abs(a), abs(b))
    return _norm(a) == _norm(b)


def _groups(readings: List[Reading]) -> List[List[Reading]]:
    out: List[List[Reading]] = []
    for r in readings:
        for g in out:
            if same(g[0].value, r.value):
                g.append(r)
                break
        else:
            out.append([r])
    return out


def _settled(key: str, trusted: List[Reading], others: List[Reading], level: str) -> Fact:
    groups = _groups(trusted)
    if len(groups) > 1:  # two official (or two measured) readings disagree: nothing settles it
        return Fact(key, groups[0][0].value, "conflict", groups[0], [r for g in groups[1:] for r in g] + others)
    value = groups[0][0].value
    agree = groups[0] + [r for r in others if same(r.value, value)]
    return Fact(key, value, level, agree, [r for r in others if not same(r.value, value)])


def decide(key: str, readings: Iterable[Reading]) -> Optional[Fact]:
    rs = [r for r in readings if r.key == key and r.value not in (None, "", [], ())]
    if not rs:
        return None
    official = [r for r in rs if r.source in OFFICIAL]
    if official:
        return _settled(key, official, [r for r in rs if r.source not in OFFICIAL], "official")
    measured = [r for r in rs if r.source in MEASURED]
    if measured:
        return _settled(key, measured, [r for r in rs if r.source not in MEASURED], "measured")
    groups = sorted(_groups(rs), key=lambda g: -len({r.source for r in g}))
    if len(groups) > 1:
        return Fact(key, groups[0][0].value, "conflict", groups[0], [r for g in groups[1:] for r in g])
    level = "corroborated" if len({r.source for r in groups[0]}) >= 2 else "single"
    return Fact(key, groups[0][0].value, level, groups[0], [])


def sheet(readings: Iterable[Reading]) -> Dict[str, Fact]:
    """Every key's decision, in first-seen order."""
    rs = list(readings)
    keys = list(dict.fromkeys(r.key for r in rs))
    out = {}
    for k in keys:
        f = decide(k, rs)
        if f is not None:
            out[k] = f
    return out


def usable(facts: Dict[str, Fact]) -> Dict[str, Fact]:
    return {k: f for k, f in facts.items() if f.usable}


def conflicts(facts: Dict[str, Fact]) -> List[Fact]:
    """Facts to raise as issues: outright conflicts, and usable facts some source contradicts."""
    return [f for f in facts.values() if f.level == "conflict" or f.disagree]
