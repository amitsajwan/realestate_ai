"""One project under several MahaRERA registrations, proved from the web, and the name the web calls it.

The name rule (clusters.cluster_key) merges towers only when MahaRERA files a promoter for them; Sonigara The Unicorn in Ravet
(three registrations, no promoter) stayed three pages, none with the name buyers search, while a portal ranked its one page
(docs/plan/rival-housiey-ravet.md). The owner asked for an algorithm that does it without a hand check (2026-11-06).

Rules, not a model: a merge moves a page (301) and must be provable.
- Candidates are clusters.split_candidates: the same name before the tower label, the same pincode, at most one promoter.
- Two of them are one project when a page Google returns for one's MahaRERA number also prints the other's number (`linked`):
  a builder's or a project's own page lists its phases' numbers. A page printing more than MAX_REGNOS numbers is a list of
  projects and proves nothing (as webfacts.prints_regno). Pages are the ones already stored for the numbers' searches
  (webfacts.regno_results, kind "regno"): no new searches here.
- Never merged: two promoters (split_candidates already), or both pins measured on the projects and more than FAR_KM apart.
- Linked pairs join into groups (one link is enough for each member).

The group's page name is what the web calls it (`web_name`): the first part of the titles of pages that print a member's number,
from at least two sites, containing every word of the shared name, without the place, the city or a portal's tail words
("Sonigara The Unicorn Ravet - Brochure, Pros&Cons, PriceSheet" -> "Sonigara The Unicorn"). None when two sites do not agree:
the group keeps the name its registrations share. A model is not needed for either step, and no page names itself.
"""
import re
import unicodedata
from typing import Dict, Iterable, List, Optional, Set

from app.modules.newsroom.register import regnos_in

from .pagefacts import km_between
from .text import cased, words

MAX_REGNOS = 8          # as webfacts.MAX_REGNOS: more numbers on one page is a list of projects
FAR_KM = 1.5            # two pins measured on the projects this far apart are two places
MIN_SITES = 2           # a name two sites print is the project's, not one site's spelling
NOT_A_SOURCE = ("maharera.maharashtra.gov.in", "maharera.mahaonline.gov.in", "maharerait.maharashtra.gov.in")
# a title's tail after the project's name: what the page offers, not what the project is called
TAIL_WORDS = {"price", "prices", "pricesheet", "brochure", "brochures", "floor", "plan", "plans", "plan's", "pros", "cons",
              "review", "reviews", "rera", "maharera", "details", "location", "possession", "status", "new", "launch",
              "project", "projects", "flats", "flat", "apartments", "apartment", "bhk", "sale", "for", "in", "at", "by",
              "sq", "ft", "sqft", "and", "amp", "pune", "pcmc", "pimpri", "chinchwad", "maharashtra", "india", "west", "east"}
SPLIT = re.compile(r"\s+[-–|:]\s+|\s*\|\s*|,|\(|\s+-\s*|\s+by\s+", re.I)


def _site(link: str) -> str:
    m = re.match(r"https?://([^/]+)", link or "")
    host = (m.group(1) if m else "").lower()
    return host[4:] if host.startswith("www.") else host


def _text(r: dict) -> str:
    return " ".join(str(r.get(k) or "") for k in ("title", "snippet", "link")).upper()


def _pin(d: dict) -> Optional[tuple]:
    """The pin measured on the project itself (pages.own_position), or None: an area's centre says nothing about two towers."""
    g = d.get("geo") or {}
    checked = (((d.get("enrichment") or {}).get("steps") or {}).get("places") or {}).get("ok")
    if checked and g.get("located_from") == "google" and g.get("lat") is not None and g.get("lon") is not None:
        return float(g["lat"]), float(g["lon"])
    return None


def apart(a: dict, b: dict) -> bool:
    """Both pins measured on the projects and more than FAR_KM apart: two places, whatever the pages say."""
    pa, pb = _pin(a), _pin(b)
    return bool(pa and pb) and km_between(*pa, *pb) > FAR_KM


def linked(regnos: List[str], results: Dict[str, List[dict]]) -> List[tuple]:
    """Pairs (a, b) where a page returned for a's number prints b's number too, on a page that is not a list of projects."""
    want, out = set(regnos), []
    for a in regnos:
        for r in results.get(a) or []:
            if _site(r.get("link", "")) in NOT_A_SOURCE:
                continue
            found = set(regnos_in(_text(r)))
            if a not in found or len(found) > MAX_REGNOS:
                continue
            out += [(a, b) for b in sorted(found & want) if b != a]
    return out


def groups(members: List[dict], results: Dict[str, List[dict]]) -> List[List[str]]:
    """The groups the links prove among one candidate's registrations: each a sorted list of 2+ numbers. A link between two
    registrations whose pins are far apart does not count."""
    by = {str(m.get("regno") or m["_id"]): m for m in members}
    parent = {r: r for r in by}

    def root(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in linked(list(by), results):
        if not apart(by[a], by[b]):
            parent[root(a)] = root(b)
    out: Dict[str, List[str]] = {}
    for r in by:
        out.setdefault(root(r), []).append(r)
    return sorted(sorted(g) for g in out.values() if len(g) >= 2)


def _head(title: str) -> str:
    """The title's first part, the project's name on most pages: "Sonigara The Unicorn Ravet - Brochure, ..." -> "Sonigara The
    Unicorn Ravet"."""
    plain = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode()
    return SPLIT.split(plain.strip(), maxsplit=1)[0].strip()


def web_name(members: List[dict], results: Dict[str, List[dict]], shared: str, place_words: Iterable[str] = ()) -> Optional[str]:
    """The name at least MIN_SITES sites give the project in the titles of pages printing a member's number, containing every
    word of `shared` (the name the registrations share), without the place or tail words. None when they do not agree."""
    need = set(w.lower() for w in words(shared))
    if not need:
        return None
    drop = TAIL_WORDS | {w.lower() for p in place_words for w in words(p)}
    sites: Dict[str, Set[str]] = {}
    spelt: Dict[str, str] = {}
    for m in members:
        regno = str(m.get("regno") or m["_id"])
        for r in results.get(regno) or []:
            site = _site(r.get("link", ""))
            if site in NOT_A_SOURCE or regno not in set(regnos_in(_text(r))):
                continue
            toks = _head(r.get("title") or "").split()
            while toks and re.sub(r"[^a-z0-9]", "", toks[-1].lower()) in drop | {""}:
                toks.pop()
            low = [re.sub(r"[^a-z0-9]", "", t.lower()) for t in toks]
            if not toks or not need <= set(low) or len(toks) > 8:
                continue
            key = " ".join(low)
            sites.setdefault(key, set()).add(site)
            spelt.setdefault(key, " ".join(toks))
    agreed = [k for k, s in sites.items() if len(s) >= MIN_SITES]
    if not agreed:
        return None
    best = max(agreed, key=lambda k: (len(sites[k]), len(k.split()), k))
    return " ".join(cased(spelt[best].split()))
