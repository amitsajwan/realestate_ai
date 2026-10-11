"""Which listing photos to use, and in what order: pixel checks only (no AI, no paid service).

    rank_photos(paths, min_keep=2)   # duplicates dropped, weak photos dropped or moved back, the hero first
    pick_hero(paths)                 # the photo for the reel's first scene and the cover card

Rules, in order:
1. Near-identical photos (the same shot twice, a re-sent copy, a burst) form a duplicate group: a perceptual hash (dHash)
   within DUP_BITS bits AND a similar colour thumbnail. The best-scoring photo of a group is kept, at the place of the
   group's first photo.
2. A photo with a serious issue (SERIOUS: blurry, dark, mostly sky or floor, small) is left out. Weak photos and then
   duplicates come back, best first and at the end, only when fewer than `min_keep` photos would remain.
3. Otherwise the agent's upload order stands; the hero (pick_hero) moves to the front.

The paths passed in are the copies that will be shown (the enhanced one when the agent kept it on), so the scores are of
what the buyer sees. Each file is analysed once per content: results are cached by a hash of its bytes.
"""
from __future__ import annotations

import hashlib
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import cv2
import numpy as np

from .analysis import ImageLike, analyze, downscale, load_bgr

log = logging.getLogger(__name__)

SERIOUS = ("blurry", "dark", "mostly_sky_or_floor", "small")
HERO_SKIP = SERIOUS + ("bright",)
DUP_BITS = 6            # dHash bits (of 64) that may differ between two copies of the same shot
DUP_TONE = 24.0         # mean difference (0-255) of the 8x8 colour thumbnails above which two photos are not copies
HERO_BAND = 10          # scores in the same 10-point band count as equal for the hero, so the agent's order decides
CACHE_SIZE = 1024

PathLike = Union[str, Path]
_cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()


def dhash(src: ImageLike) -> int:
    """64-bit difference hash: a 9x8 grey thumbnail, one bit per pair of neighbours (is the left one brighter)."""
    gray = cv2.cvtColor(downscale(load_bgr(src), 256), cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA).astype(np.int16)
    bits = (small[:, :-1] > small[:, 1:]).flatten()
    return int(sum(1 << i for i, b in enumerate(bits) if b))


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _thumb(img: np.ndarray) -> np.ndarray:
    return cv2.resize(downscale(img, 256), (8, 8), interpolation=cv2.INTER_AREA).astype(np.float32)


def photo_facts(path: PathLike) -> Optional[Dict[str, Any]]:
    """{score, issues, width, height, dhash, thumb} for a photo file, or None when it cannot be read. Cached by content."""
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    key = hashlib.sha1(data).hexdigest()
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]
    try:
        img = load_bgr(Path(path))
        q = analyze(img)
        facts = {"score": q["score"], "issues": list(q["issues"]), "width": q["width"], "height": q["height"],
                 "dhash": dhash(img), "thumb": _thumb(img)}
    except Exception:
        log.info("photoquality: could not rank %s", Path(path).name, exc_info=True)
        return None
    _cache[key] = facts
    while len(_cache) > CACHE_SIZE:
        _cache.popitem(last=False)
    return facts


def is_duplicate(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    """Two photo_facts describe the same shot: close perceptual hashes and similar colours."""
    return (hamming(a["dhash"], b["dhash"]) <= DUP_BITS
            and float(np.abs(a["thumb"] - b["thumb"]).mean()) <= DUP_TONE)


def _facts(paths: Sequence[PathLike]) -> List[Optional[Dict[str, Any]]]:
    return [photo_facts(p) for p in paths]


def _groups(facts: List[Optional[Dict[str, Any]]]) -> List[List[int]]:
    """Indexes grouped by duplicates, groups in order of their first photo; the best photo (score, then order) first."""
    group_of: List[int] = []
    groups: List[List[int]] = []
    for i, f in enumerate(facts):
        g = next((group_of[j] for j in range(i) if f and facts[j] and is_duplicate(f, facts[j])), None)
        if g is None:
            g = len(groups)
            groups.append([])
        group_of.append(g)
        groups[g].append(i)
    return [sorted(g, key=lambda i: (-_score(facts[i]), i)) for g in groups]


def _score(f: Optional[Dict[str, Any]]) -> int:
    return f["score"] if f else 0


def _weak(f: Optional[Dict[str, Any]]) -> bool:
    return f is None or any(i in SERIOUS for i in f["issues"])


def duplicate_groups(paths: Sequence[PathLike]) -> List[List[Path]]:
    """The photos grouped by near-identical shots, in the agent's order; within a group the one to keep comes first."""
    return [[Path(paths[i]) for i in g] for g in _groups(_facts(paths))]


def _hero(order: List[int], facts: List[Optional[Dict[str, Any]]]) -> Optional[int]:
    cands = [i for i in order if facts[i] and not any(x in HERO_SKIP for x in facts[i]["issues"])]
    if not cands:
        return None
    return min(cands, key=lambda i: (facts[i]["width"] < facts[i]["height"], -(facts[i]["score"] // HERO_BAND), order.index(i)))


def pick_hero(paths: Sequence[PathLike]) -> Optional[Path]:
    """The first photo of a reel and the cover card. Among the photos with no serious issue that are not over-exposed:
    landscape (or square) before portrait, then the higher score in 10-point bands, then the agent's order. None when no
    photo qualifies (the caller keeps its own first photo)."""
    facts = _facts(paths)
    i = _hero(list(range(len(paths))), facts)
    return None if i is None else Path(paths[i])


def rank_photos(paths: Sequence[PathLike], min_keep: int = 0) -> List[Path]:
    """The photos to use, best first: duplicates and weak photos out (back in, at the end, only to reach `min_keep`),
    the agent's order otherwise, the hero first. See the module docstring for the rules."""
    paths = [Path(p) for p in paths]
    facts = _facts(paths)
    groups = _groups(facts)
    keep = [g[0] for g in groups]
    good = [i for i in keep if not _weak(facts[i])]
    spare = (sorted((i for i in keep if _weak(facts[i])), key=lambda i: (-_score(facts[i]), i))
             + sorted((i for g in groups for i in g[1:]), key=lambda i: (-_score(facts[i]), i)))
    first = {g[0]: min(g) for g in groups}
    order = sorted(good, key=first.__getitem__)
    order += spare[:max(0, min_keep - len(order))]
    hero = _hero(order, facts)
    if hero is not None:
        order.remove(hero)
        order.insert(0, hero)
    return [paths[i] for i in order]
