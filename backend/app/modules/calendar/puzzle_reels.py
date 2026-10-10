"""Puzzle reels: a question about Pune's MahaRERA records, three options, time to answer in the comments, then the answer with its count.

Every answer is a count from `area_stats` (the same numbers the area reels and locality pages show), so the puzzle can be checked by
anyone on MahaRERA. Kinds:
  most_projects  "Which area has the most projects in MahaRERA records?"  options: the trusted areas
  peak_year      "Most <area> projects filed which completion year?"     options: the top year and the next two
  year_count     "How many <area> projects filed a <year> completion date?" options: the count and two others
Only areas whose projects are matched by pincode (newsroom.policy.AREA_PINCODES: Kharadi, Wagholi, Lohegaon) are used: the other
areas are matched by project name only, so their counts are too low and a comparison with them would teach a wrong fact.
A puzzle is made only when its answer is clear: one winner, ahead of the next option (no ties, no near-ties). No prices, no
predictions; the caption never gives the answer away (it is at the end of the reel).

Slides are area_reels.Slide, drawn and checked by area_reels.draw/check/save_slides, played by area_reels.render_video:
  1. the question and options A/B/C   2. "Comment A, B or C" with a countdown   3. the answer and the counts   4. the page link
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

from app.core import areas as _areas
from app.core import brand
from app.modules.newsroom.policy import AREA_PINCODES

from .area_reels import SOURCE, Slide, _day, _n, page_link, site_host, wording_problems

TRUSTED = tuple(dict.fromkeys(AREA_PINCODES.values()))  # areas whose project counts are complete enough to compare
LETTERS = "ABC"
MIN_LEAD = 0.05       # most_projects: the winner has at least 5% more projects than the runner-up
MIN_YEAR_GAP = 1      # peak_year: the top year has at least this many projects more than the next
KINDS = ("most_projects", "peak_year", "year_count")


@dataclass
class PuzzleReel:
    key: str              # 'most_projects' or '<kind>-<area>'
    kind: str
    area: str             # the area the puzzle is about ('' for a comparison)
    as_of: str
    question: str
    options: List[str]
    answer: int           # index into options
    slides: List[Slide]
    caption_ig: str
    caption_fb: str

    @property
    def hook(self) -> str:
        return self.question

    @property
    def name(self) -> str:
        return self.question

    @property
    def script(self) -> List[str]:
        out = []
        for s in self.slides:
            out.append(" ".join(x for x in (s.headline, s.big, s.label) if x))
            out += s.lines
        return out

    def slug(self, day: date) -> str:
        return f"puzzle-{self.key.replace('_', '-')}-{day:%Y%m%d}"


def _usable(stats: Dict[str, dict]) -> Dict[str, dict]:
    return {k: s for k, s in stats.items() if k in TRUSTED and s and int(s.get("projects") or 0) >= 3 and _day(s.get("as_of") or "")}


def _years(s: dict) -> List[Tuple[int, int]]:
    """[(year, projects)] with at least one project, most projects first, earlier year first on a tie."""
    ys = [(int(y["year"]), int(y.get("projects") or 0)) for y in s.get("completing") or []]
    return sorted([y for y in ys if y[1] > 0], key=lambda y: (-y[1], y[0]))


def _as_of(stats: Sequence[dict]) -> str:
    return min(str(s["as_of"])[:10] for s in stats)


def most_projects(stats: Dict[str, dict]) -> Optional[dict]:
    use = _usable(stats)
    if len(use) < 3:
        return None
    ranked = sorted(use, key=lambda k: -int(use[k]["projects"]))[:3]
    top, second = int(use[ranked[0]]["projects"]), int(use[ranked[1]]["projects"])
    if top < second * (1 + MIN_LEAD):
        return None
    names = sorted(ranked, key=lambda k: _areas.get(k).name)   # alphabetical: the order gives nothing away
    return {"key": "most_projects", "kind": "most_projects", "area": "", "as_of": _as_of([use[k] for k in ranked]),
            "question": "Which Pune area has the most projects in MahaRERA records?",
            "options": [_areas.get(k).name for k in names], "answer": names.index(ranked[0]),
            "big": _n(top), "label": f"projects in {_areas.get(ranked[0]).name}",
            "facts": [f"{_areas.get(k).name}: {_n(use[k]['projects'])} projects" for k in ranked[1:]]}


def peak_year(stats: Dict[str, dict], key: str) -> Optional[dict]:
    s = _usable(stats).get(key)
    ys = _years(s) if s else []
    if len(ys) < 3 or ys[0][1] - ys[1][1] < MIN_YEAR_GAP:
        return None
    area = _areas.get(key)
    opts = sorted(ys[:3])                                      # by year: the order gives nothing away
    return {"key": f"peak_year-{key}", "kind": "peak_year", "area": key, "as_of": str(s["as_of"])[:10],
            "question": f"Most {area.name} projects on MahaRERA filed which completion year?",
            "options": [str(y) for y, _ in opts], "answer": opts.index(ys[0]),
            "big": _n(ys[0][1]), "label": f"projects with a {ys[0][0]} completion date",
            "facts": [f"{y}: {_n(n)} projects" for y, n in ys[1:3]]}


def year_count(stats: Dict[str, dict], key: str) -> Optional[dict]:
    """The count for the earliest year with at least 10 projects; the other two options are well below and/or above it."""
    s = _usable(stats).get(key)
    ys = sorted(_years(s)) if s else []
    pick = next(((y, n) for y, n in ys if n >= 10), None)
    if pick is None:
        return None
    year, n = pick
    spread = ((0.5, 1, 2), (1, 1.6, 2.5), (0.4, 0.7, 1))[(n + year) % 3]   # the answer is low, middle or high: not always B
    opts = sorted({max(1, round(n * f)) for f in spread})
    if len(opts) < 3:
        return None
    area = _areas.get(key)
    return {"key": f"year_count-{key}", "kind": "year_count", "area": key, "as_of": str(s["as_of"])[:10],
            "question": f"How many {area.name} projects on MahaRERA filed a {year} completion date?",
            "options": [_n(o) for o in opts], "answer": opts.index(round(n)),
            "big": _n(n), "label": f"{area.name} projects with a {year} completion date",
            "facts": [f"All {area.name} projects in the records: {_n(s['projects'])}"]}


def _slides(p: dict) -> List[Slide]:
    opts = [f"{LETTERS[i]}  {o}" for i, o in enumerate(p["options"])]
    link_area = _areas.get(p["area"]) if p["area"] else None
    link = page_link(link_area) if link_area else f"{site_host()}/localities"
    return [Slide("PUNE PUZZLE", p["question"], lines=opts),
            Slide("LOCK YOUR ANSWER", "Comment A, B or C", "3 · 2 · 1", "the answer is next", opts),
            Slide("ANSWER", f"{LETTERS[p['answer']]}  {p['options'][p['answer']]}", p["big"], p["label"], p["facts"]),
            Slide("CHECK IT YOURSELF", "Every project, with its MahaRERA source", lines=[link])]


def _captions(p: dict) -> Dict[str, str]:
    opts = "\n".join(f"{LETTERS[i]}) {o}" for i, o in enumerate(p["options"]))
    area = _areas.get(p["area"]) if p["area"] else None
    tags = " ".join((list(area.hashtags) if area else ["#KharadiPune", "#WagholiPune"]) + ["#PunePuzzle", "#MahaRERA", "#PuneProperty"])
    source = f"Source: {SOURCE}, as of {_day(p['as_of'])}."
    body = f"Pune puzzle: {p['question']}\n\n{opts}\n\nComment A, B or C. The answer is at the end of the reel.\n\n{source}"
    path = area.page if area else "/localities"
    return {"instagram": f"{body}\n\nCheck it yourself: {site_host()}{path} (link in our bio).\n\n{tags}",
            "facebook_page": f"{body}\n\nCheck it yourself: {brand.SITE}{path}\n\n{tags}"}


def build(p: Optional[dict]) -> Optional[PuzzleReel]:
    if p is None:
        return None
    slides, caps = _slides(p), _captions(p)
    text = "\n".join(list(caps.values()) + [" ".join([s.kicker, s.headline, s.big, s.label] + s.lines) for s in slides])
    if wording_problems(text):
        return None
    return PuzzleReel(p["key"], p["kind"], p["area"], p["as_of"], p["question"], p["options"], p["answer"], slides,
                      caps["instagram"], caps["facebook_page"])


def puzzles(stats: Dict[str, dict]) -> List[PuzzleReel]:
    """Every puzzle the stats support, comparison first, then per area: peak year, year count."""
    found = [most_projects(stats)]
    for k in TRUSTED:
        found += [peak_year(stats, k), year_count(stats, k)]
    return [r for r in (build(p) for p in found) if r is not None]


async def load_stats(db, stats_fn=None) -> Dict[str, dict]:
    if stats_fn is None:
        from app.modules.areastats.service import area_stats as stats_fn
    out = {}
    for k in TRUSTED:
        try:
            out[k] = await stats_fn(db, k)
        except Exception:
            out[k] = None
    return out
