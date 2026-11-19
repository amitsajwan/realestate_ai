"""The name and the place a project is sold under, read from the pages that print its MahaRERA number (seo-system.md 8c).

MahaRERA files a project under a legal name and its pincode's village; buyers search the name the builder and the portals print.
"Altamira By VTP Luxe Phase 1", pincode 412207 (Wagholi), is sold everywhere as "VTP Altamira" in Kharadi: on 2026-11-19 five
of the nine pages printing P52100079807 titled it "VTP Altamira" and seven put it in Kharadi, while our page was titled
"Altamira By VTP Luxe Wagholi" and Google showed it for nothing. `seo.targets` learns the searched name from Search Console,
which only knows searches that already show the page, so a page Google never shows never learns it.

Once a day (inside the seo loop) every project page in search reads Google's results for its own MahaRERA number, which
`areastats.webfacts` already stores (`web_search_results`, kind "regno"; no new search is made here):
- `market_name`: the name most sites title the project with, one vote per site, when at least MIN_SITES sites agree and no other
  name has as many. Only the project's own words count (its names, its builder's brand, its promoter): a name adding any other
  word names something else ("VTP Altair 3" is another of VTP's projects), and it must keep a word that is the project's own,
  not the builder's or the place's. The page title and heading lead with it after `search_name`, which is measured on our own
  searches and so wins. Each change is logged as a "name" fix in `seo_actions` and measured and undone like a title.
- `market_place`: the Pune place most of those sites put the project in, when it is not the place our page names (the register's
  pincode). The title then says both ("VTP Altamira Kharadi, Wagholi") and the page says which is which; our place is never
  changed here (areastats.placement moves a project by its position, nothing else).
A page whose sites no longer agree loses both. Read-only on the results; writes only the three fields and the fix log.
"""
import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from app.core import pune_places
from app.core.areas import BY_KEY
from app.modules.areastats import brands, websearch
from app.modules.areastats.pages import _served, brand_word, branded_name, family_name, names, searchable
from app.modules.areastats.webfacts import builder_words, official
from app.modules.newsroom.store import Store

from .actions import REST_DAYS, blocked, log_fix
from .config import load
from .targets import GENERIC, MAX_NAME

log = logging.getLogger(__name__)

MARK = "seo_market_names"
EVERY = timedelta(hours=24)
MIN_SITES = 2
# words that sit between a name's words without being one: kept as written in the name, never voted on
JOINERS = {"by", "of", "the", "and", "at", "de", "la", "le"}
_MARKS = re.compile(r"[®™©]")
# where a page title's name ends: a separator, or " in <place>"/" at <place>"/" near <place>"
_SEGMENT = re.compile(r"\s*[|–—:,]\s*|\s+-\s+|\s+(?:in|at|near)\s+", re.I)
_WORD = re.compile(r"[A-Za-z0-9']+")
_TAIL_WORDS = {"phase", "ph", "part", "tower", "towers", "wing", "block", "building", "bldg", "stage", "sector", "project", "named"}
_PLACE_WORDS = frozenset(w for p in pune_places.PLACES for al in (p.name, *p.aliases) for w in re.findall(r"[a-z0-9]+", al.lower())) \
    | {"pune", "maharashtra", "pcmc", "pmc", "india"}


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def title_name(title: str) -> List[str]:
    """The project's name at the start of a page title, as words: "VTP Altamira Kharadi Pune | Book 3 BHK ..." -> [VTP, Altamira].
    Trailing place words and words saying what a searcher wants ("price", "brochure") are cut; the rest is kept as written."""
    head = _SEGMENT.split(_MARKS.sub("", title or ""), maxsplit=1)[0]
    words = _WORD.findall(head)
    while words and (words[-1].lower() in _PLACE_WORDS or words[-1].lower() in GENERIC or words[-1].lower() in JOINERS):
        words.pop()
    return words


def key(words: List[str]) -> Tuple[str, ...]:
    """What two titles must share to be the same name: the words without joiners or generic words, in order, lower case."""
    return tuple(w.lower() for w in words if w.lower() not in JOINERS and w.lower() not in GENERIC)


def _bare(k: Tuple[str, ...]) -> Tuple[str, ...]:
    """A name's words without place words, numbers, single letters and phase words: two names equal here differ only by what the
    title adds anyway (the place) or what MahaRERA files one registration under ("Phase 1", "A Building")."""
    return tuple(w for w in k if w not in _PLACE_WORDS and not w.isdigit() and len(w) > 1 and w not in _TAIL_WORDS
                 and w not in ("ii", "iii", "iv"))


def brand_ok(doc: dict, k: Tuple[str, ...]) -> bool:
    """The brand whole or not at all, and kept when the record's name has it: "Kolte The Reserve" (half of Kolte Patil) and
    "Vilas 38K Inclusive Housing" (Vilas Javdekar's, without Javdekar) are names cut short, not names people use."""
    b = brands.of(doc)
    if not b:
        return True
    want = re.findall(r"[a-z0-9]+", brand_word(b).lower())
    has = [w for w in want if w in k]
    if has and len(has) < len(want):
        return False
    base = set(re.findall(r"[a-z0-9]+", names(doc)[0].lower()))
    return not (set(want) <= base) or len(has) == len(want)


def _brand_words(doc: dict) -> set:
    b = brands.of(doc)
    return set(re.findall(r"[a-z0-9]+", b.name.lower())) if b else set()


def distinctive(doc: dict) -> set:
    """The project's own words: in its names, and not its builder's, its promoter's, a place's, or a generic one."""
    words = set(re.findall(r"[a-z0-9']+", " ".join(names(doc)[1]).lower()))
    builder = _brand_words(doc) | set(re.findall(r"[a-z0-9]+", str(doc.get("promoter") or "").lower()))
    return {w for w in words if w not in GENERIC and w not in JOINERS and w not in _PLACE_WORDS and w not in builder
            and not w.isdigit() and len(w) > 1}


def _casing(doc: dict) -> Dict[str, str]:
    """How the record writes each word ("VTP", not "Vtp"): the marketed name first, then the other names and the brand. A word only
    ever written in capitals (MahaRERA's legal name) is capitalised, unless it is three letters or fewer (an initialism)."""
    out: Dict[str, str] = {}
    b = brands.of(doc)
    for text in [*names(doc)[1], b.name if b else ""]:
        for w in _WORD.findall(text or ""):
            low = w.lower()
            if low in out:
                continue
            if w.isupper() and len(w) > 3:
                continue          # a capitals-only spelling waits for a better one
            out[low] = w
    return out


def shown(doc: dict, words: List[str]) -> str:
    case = _casing(doc)
    return " ".join(case.get(w.lower()) or (w.lower() if w.lower() in JOINERS else w.upper() if len(w) <= 3 and w.isupper() else w.capitalize())
                    for w in words)


def organic(results: List[dict]) -> List[dict]:
    """One result per site, the first one, from the sites that market projects (never ours, MahaRERA's or a directory)."""
    seen, out = set(), []
    for r in results or []:
        link = r.get("link") or ""
        if r.get("type") in websearch.PHRASE_TYPES or r.get("ad") or not link or not websearch.marketer(link):
            continue
        site = websearch.site(link)
        if site in seen:
            continue
        seen.add(site)
        out.append(r)
    return out


def place_named(r: dict) -> Optional[pune_places.Place]:
    """The Pune place a result's title or address names, the most specific one ("Upper Kharadi" over "Kharadi")."""
    path = re.sub(r"[^a-z0-9]+", " ", (r.get("link") or "").lower().split("?")[0])
    text = pune_places._norm(f"{r.get('title') or ''} {path}")
    best, size = None, 0
    for p in pune_places.PLACES:
        n = pune_places._named(p, text)
        if n > size:
            best, size = p, n
    return best


def nearby(doc: dict, p: pune_places.Place) -> bool:
    """The place the sites name is next to ours: it shares the project's pincode or lies in the same part of Pune. A far one
    (Talegaon sold as "Hinjawadi", 2026-11-19 dry run) is a marketer's pull, not where the project is."""
    ours = next((x for x in pune_places.PLACES if x.key == (doc.get("pune_place") or doc.get("locality"))), None)
    return str(doc.get("pincode") or "") in p.pincodes or (ours is not None and ours.zone == p.zone)


def read(doc: dict, results: List[dict]) -> dict:
    """{name, place, sites, name_sites, place_sites, official} from the results for the project's MahaRERA number. `name` and
    `place` are None when the sites do not agree enough, or say what the page already says."""
    rows = organic(results)
    # the record's own names and a known brand only: portals put the promoter's first word before a name ("Highspot Maitri
    # Meadows", "Virkar Seven") and add words ("One Pirangut Residential Building"), which nobody searches (dry run 2026-11-19)
    allowed = set(re.findall(r"[a-z0-9']+", " ".join(names(doc)[1]).lower())) | _brand_words(doc)
    mine = distinctive(doc)
    words_of = builder_words(doc)
    votes: Counter = Counter()
    first: Dict[Tuple[str, ...], List[str]] = {}
    official_keys = set()
    for r in rows:
        words = title_name(r.get("title") or "")
        k = key(words)
        if len(k) < 2 or not set(k) <= allowed or not set(k) & mine or len(" ".join(words)) > MAX_NAME                 or set(k) & _TAIL_WORDS or not brand_ok(doc, k):
            continue
        votes[k] += 1
        first.setdefault(k, words)
        if official(r.get("link") or "", words_of):
            official_keys.add(k)
    name = None
    ranked = sorted(votes.items(), key=lambda kv: (-kv[1], kv[0] not in official_keys))
    # a page with a name measured on our own searches (seo.targets) keeps it: Google already shows it under that name
    if not doc.get("search_name") and ranked and ranked[0][1] >= MIN_SITES and (len(ranked) == 1 or ranked[1][1] < ranked[0][1]):
        best = ranked[0][0]
        if not any(_bare(best) == _bare(key(_WORD.findall(n))) for n in (branded_name(doc), names(doc)[0], family_name(doc)) if n):
            name = shown(doc, first[best])
    places: Counter = Counter()
    named: Dict[str, pune_places.Place] = {}
    for r in rows:
        p = place_named(r)
        if p is not None:
            places[p.key] += 1
            named[p.key] = p
    place = None
    if places:
        top, n = places.most_common(1)[0]
        ours = doc.get("pune_place") or doc.get("locality") or ""
        our_name = (BY_KEY[ours].name if ours in BY_KEY else doc.get("pune_place_name") or "").lower()
        if n >= MIN_SITES and n * 2 > sum(places.values()) and top != ours and named[top].name.lower() not in our_name                 and nearby(doc, named[top]):
            place = named[top].name
    return {"name": name, "place": place, "sites": len(rows), "name_sites": int(ranked[0][1]) if ranked else 0,
            "place_sites": int(places.most_common(1)[0][1]) if places else 0, "official": bool(ranked and ranked[0][0] in official_keys)}


def all_reads(docs: List[dict], kept: Dict[str, List[dict]], now: datetime) -> List[Tuple[dict, dict]]:
    """[(record, read)] for every project page in search with a search for its number. A name two pages would share is given to
    neither: Raheja Vistas' three tower pages would all be titled "Raheja Vistas" and compete for one search (they want merging,
    seo.targets R2, not one title)."""
    out = []
    for doc in docs:
        if not _served(doc) or doc.get("cluster_primary") or not searchable(doc, now):
            continue
        regno = str(doc.get("regno") or doc["_id"])
        if regno in kept:
            out.append((doc, read(doc, kept[regno])))
    return dedupe(out)


def dedupe(reads: List[Tuple[dict, dict]]) -> List[Tuple[dict, dict]]:
    """The reads with every name more than one page would carry (in the same place) taken away."""
    def at(doc: dict, g: dict) -> tuple:
        return (g["name"].lower(), g["place"] or doc.get("pune_place") or "")
    count = Counter(at(doc, g) for doc, g in reads if g["name"])
    return [(doc, {**g, "name": None} if g["name"] and count[at(doc, g)] > 1 else g) for doc, g in reads]


async def run_once(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    """Read every page in search; write the names and places that changed. None when done today already."""
    if not load().market_names_on:
        return None
    last = _aware((await store.get_mark(MARK)).get("at"))
    if not force and last is not None and now - last < EVERY:
        return None
    coll = store.db.get_collection(websearch.RESULTS)
    kept = {d["_id"]: d.get("results") or [] for d in await coll.find({"kind": "regno"}, {"results": 1}).to_list(None)}
    named = placed = 0
    reads = all_reads(await store.all_projects(), kept, now)
    if not reads:            # no page has a search for its number yet (webfacts makes them): nothing to do this round
        return None
    for doc, got in reads:
        fields: dict = {}
        new_name = got["name"]
        if new_name != doc.get("market_name") and not blocked(doc, "name", new_name):
            since = _aware(doc.get("page_fix_at"))
            if new_name is None or since is None or now - since >= timedelta(days=REST_DAYS) or doc.get("page_fix") == "name":
                await log_fix(store, doc, "name", now, old=doc.get("market_name"), new=new_name, phrase=new_name,
                              note=f"{got['name_sites']} of {got['sites']} sites printing the MahaRERA number"
                                   + (", the builder's among them" if got["official"] else ""))
                fields["market_name"] = new_name
                named += 1
        if got["place"] != doc.get("market_place"):
            fields["market_place"] = got["place"]
            placed += 1
        info = {k: got[k] for k in ("sites", "name_sites", "place_sites", "official")}
        if fields or (doc.get("market_read") or {}).get("sites") != info["sites"]:
            await store.set_project(doc["_id"], **fields, market_read={**info, "at": now})
    await store.set_mark(MARK, at=now, read=len(reads), names=named, places=placed)
    log.info("market names: %d pages read, %d names and %d places changed", len(reads), named, placed)
    return {"read": len(reads), "names": named, "places": placed}
