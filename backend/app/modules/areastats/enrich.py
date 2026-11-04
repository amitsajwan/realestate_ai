"""Steady enrichment of our project pages (docs/plan/project-pages.md): one project every EVERY_MINUTES, urgent ones at once.

Each round picks ONE project (`next_project`): an urgent request first (a campaign about to post), then hot projects (areastats.hot:
selling, in the news, searched for; refreshed every HOT_REFRESH_DAYS), then the pages Google already shows (Search Console
impressions, when that job has stored them; those just off page one first), then records enriched before the checks below (no
`enrichment`), then indexable pages never enriched (newest first), then the rest, then the oldest enrichment once it is
REFRESH_DAYS old (RETRY_DAYS when MahaRERA or the model did not answer: that is the service, not the project; THIN_RETRY_DAYS
for a page kept out of search as thin). Projects whose filed
completion date has passed are skipped (status "finished"; owner 2026-10-21: "projects already completed we should not enrich"),
unless a campaign asks or homes are left on an east Pune Top list; the projects the main pages show (`featured`: the east Pune
Top lists, pricing.on_top, and the owner's banner picks, areastats.spotlight) go with the hot ones (owner 2026-10-26: "if we are
showing some projects on main pages, make sure we enrich it quickly on priority"); projects with 90% or more of their homes booked (pages.nearly_sold) come after all the others; the rest
go area by area outward from Kharadi (areastats.pricing.ORDER: Upper Kharadi, Kharadi, Wagholi, Keshav Nagar, Lohegaon, then the
west side), and in each area new launches and hot projects first (owner 2026-10-21). For that project:
0. MahaRERA, two open reads one after the other (PAUSE apart): the general record (kept only when its regno is the record's)
   and the building/wing summary (kept only when every row's projectId and regno are the record's) -> `buildings`,
   `building_totals`. A record with no pincode or locality gets them from the project's fact sheet (same regno) first.
1. facts: the property-facts gatherer (set at startup in app/wiring.py, `configure(gather=...)`): MahaRERA's full record, the
   place and what is nearby, worked-out numbers, the agent's offer; each with its source. No model here.
2. text: ONE model call writes the page's "About the project" sections ("The project", "Location", "For buyers") and a one-line
   search summary from those facts and what code works out from them (`worked_out`), told what the page already shows.
   `check_text` refuses any number not in the facts, sales words and anything too long, `repeats` a draft that says again what
   the page shows or gives a whole-project count as this registration's, `lifted` one that takes a run of words from its
   fact sheet or from the outside pages read live this round (`outside_pages`) and `alike` one that reads like another page of
   the area; a refused draft goes back once with the reasons, then keeps the code-written paragraph. The model is also given how
   the project sits among its area's (`area_context`) and the questions its facts raise (`worth_asking`), both worked out by
   code. A page in search keeps its text REST_DAYS before a newer writer takes it (`keeps_text`).
2b. web: what the builder's site and the sites ranking for the project say (areastats.webfacts), checked, kept as
   `web_facts` on the group's primary record; the accepted facts are given to the text model too. Not counted in the score.
2c. profile: highlights, the builder's pictures and floor plans (areastats.profile), only while the filed completion date is to
   come; read from the same pages (each fetched once per round), kept as `profile`; the highlights go to the text model too. A
   hot project with no profile yet is enriched at once (after urgent requests). Not counted in the score.
2d. prices: what the builder's site and the property sites ask, per home size (areastats.prices), from the same pages' price
   lines, every amount read by code from a quote; kept as `prices`. Not given to the text model as facts (prices change faster
   than the text is rewritten; it is only told the page shows them, so as not to repeat them) and not counted in the score. Prices also have their own round in this loop (areastats.pricing: one
   project every 15 minutes, Upper Kharadi, Kharadi and Wagholi first), so they do not wait for a rewrite.
3. stored on the register record: `page_text` (the sections' texts joined, when accepted), `page_sections`, `page_summary` (the
   search line), `enriched_at`, `enrich_notes`, `geo` (the gathered position, checked to be within NEAR_KM of the pincode's
   centre) and `enrichment` = {at, steps: {maharera_general, buildings, places,
   text}: each {ok, at, checked...}, score "n/4"}; `status_list` is the owner's view of it (Studio > Newsroom > Project pages).
The flow (owner 2026-11-04: "it should be final step", "stop wasting ai", "first target already enriched page"): code's facts
first; then the model reads the sites, only for a page a buyer can land on (`worth_model`: never a tower, which redirects to its
group, nor offices and shops, which are never in search); the writer last, only with every read done and a fact of the project's
own on the record (`pages.own_facts`). Each day the first REWRITES_PER_DAY rounds go to pages already in search that an older
writer wrote (`rewrite_due`), most seen by Google first: the daily cap, not one wait for all, is what keeps the site from
rewriting itself at once.
Facts often, the model by budget (owner 2026-10-25; docs/plan/enrich-lanes.md). Steps 0, 1, the place check and the pictures
need no model and run every EVERY_MINUTES (5); MahaRERA's general record is not read again while the register's own read
(areastats.refresh) is under DETAILS_FRESH_DAYS old, the buildings while under BUILDINGS_FRESH_DAYS. The model steps (2, 2b, 2c's
highlights, 2d) go through areastats.budget: an answer to the same question (an unchanged page, unchanged facts) is kept and
costs no call; Gemini is metered in rupees a day and spent first on campaigns, hot projects, pages Google shows and the first
areas (`tier_of`); the rest goes to the free tiers. When no model has room (or there is no key) the reading is put off, not
failed: the last results stay and `reading_due` is set; `read_step` takes those projects, premium first, every
READ_EVERY_MINUTES when the budget has room, from the facts the facts round kept (no gathering again).
Nothing runs until PROJECT_ENRICH_ENABLED is on. A campaign calls `enrich_now(db, regno)`; the loop takes it within a minute.
"""
import asyncio
import logging
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from app.core.areas import BY_KEY
from app.modules.agentprojects import maharera as project_api
from app.modules.newsroom import register
from app.modules.newsroom.store import Store
from app.platform import trace

from . import brands, budget, hot, pages, prices, pricing, profile, readings, searchconsole, webfacts
from .websearch import mentions as websearch_mentions
from .service import _day

log = logging.getLogger(__name__)

EVERY_MINUTES = 5                     # a facts round every 5 minutes (urgent campaign requests go first); no model needed
READ_EVERY_MINUTES = 10               # a reading round (model) for a project whose reading was put off, when the budget has room
DETAILS_FRESH_DAYS = 30               # the register's own MahaRERA read (areastats.refresh) this recent is used as it is
BUILDINGS_FRESH_DAYS = 30             # the building/wing summary is read again after this
PAUSE = 2.0                           # seconds between our two MahaRERA reads in a round (one after the other, never parallel)
NEAR_KM = 15.0                        # the located place must be this close to the pincode's centre
STEPS = ("maharera_general", "buildings", "places", "text")
REFRESH_DAYS = 60
RETRY_DAYS = 1                        # a round MahaRERA or the model did not answer is tried again after this
HOT_REFRESH_DAYS = 14                 # a hot project's page is rewritten from fresh facts this often
TOP_RETRY_DAYS = 7                    # a top-list project still missing a stage or pictures is tried again after this
THIN_RETRY_DAYS = 7                   # a page kept out of search as thin (pages.searchable) is tried again after this, not
                                      # REFRESH_DAYS (owner 2026-10-31: "make cycle bit faster", only pages with proper text in search)
POLL_SECONDS = 60
REQUESTS = "enrich_requests"          # {_id: regno, at, by}: urgent enrichments asked for by campaigns
MAX_TEXT = 2600                       # characters, the sections and the search summary together
MAX_SUMMARY = 160                     # the one-line summary search results may show
# 2 (owner 2026-10-17, "more content, good summary, good SEO"): a summary, then sections under fixed headings, then a one-line
# summary for search results. A page whose text an older writer wrote is due for a round again (`priority`).
# 3 (owner 2026-10-20, "paragraph, line or highlights, if they need improvements"): the name as buyers write it (not MahaRERA's
# capitals), the brand beside the filing company, and the highlights (shown as bullets next to the text) not repeated
# 4 (owner 2026-10-25, Park Eden Phase I: "why we have duplicate"; docs/plan/project-page-v2.md): sections only, no summary;
# nothing the page already shows (dates, bookings, prices, highlights), whole-project counts said to be so, the extension
# not called a move. Older pages are rewritten in the BACKFILL group, through the model budget.
# 5 (owner 2026-11-04: "get LLM to write it, but original content"; 245 pages in search had a median of 380 characters): a third
# section on what this project's own facts mean for a buyer, more sentences where the facts carry them, numbers code works out,
# and two checks that the words are our own. Never padding: a short true section beats a long empty one.
TEXT_VERSION = 5
SECTIONS = ("The project", "Location", "For buyers")
# Each reading step has a version (owner 2026-10-20: "enrichment can happen again: we improve it, get more info, a better model").
# Raise a step's number when the step gets better (a new rule, a new source, a better model): every project that step read with
# an older version is read again, in the BACKFILL group, hot ones first. Kept per project in `enrichment.versions`.
# profile 2: the builder's site found through the brand, on the domain's own name (ef886e0b, e1c6adb9)
# profile 3: pictures listed in the page data (sites that draw them by script, godrejproperties.com); room renders are photos
# web 2, profile 4, prices 2: pages found through the MahaRERA number and the builder's whole name (2026-11-03, owner: "rera number
# from maha rera, then map with online data"); of 103 projects on the east Pune Top lists only 10 had text, highlights, prices and photos
VERSIONS = {"web": 2, "profile": 4, "prices": 2}
# fail and move on (owner 2026-10-20: "note it and continue with others, find a solution offline later"): each reading step
# has STEP_SECONDS, the whole round ROUND_SECONDS; a project is not taken again within MIN_GAP (urgent requests aside), and
# after MAX_FAILS failed rounds in a row it is parked for PARK_DAYS with its reason in the owner's list (status "parked")
STEP_SECONDS = 240
ROUND_SECONDS = 15 * 60
MIN_GAP = timedelta(hours=6)
# a page in Google keeps its text this long before a newer writer or reader version takes it again: 87 of 503 searchable
# pages were rewritten in one day (2026-10-27), and a site rewriting itself that fast reads as machine-made
REST_DAYS = 14
REWRITES_PER_DAY = 20                 # pages in search given to a newer writer each day: 240 pages in 12 days
REWRITES = "enrich_rewrites"          # mark: {day, done}
MAX_FAILS = 3
PARK_DAYS = 14
BACKFILL = 7                          # priority group of a rewrite for a newer writer: after everything else
BACKFILL_EVERY = timedelta(minutes=30)   # a rewrite that reads the web pages again (~9 model calls): ~48 a day on the free tiers
# a rewrite whose web pages were read within REFRESH_DAYS only writes (one model call, ~2K tokens): at the loop's own pace
LIFTED_WORDS = 10                     # this many words in a row from the fact sheet is copying, not a shared place name or phrase
ALIKE_WORDS = 6                       # runs of this many words are compared between two pages of an area
OUTSIDE_CHARS = 200_000               # of one outside page, for the word-for-word check
ALIKE_SHARE = 0.25                    # this share of a draft's runs found on one other project's page reads as the same page
BANNED = re.compile(r"\b(best|luxur\w*|premium|world[- ]class|guaranteed?|assured|dream|unmatched|perfect|exclusive|hurry|limited time)\b", re.I)
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
# what gives machine-written text away (owner 2026-11-04: "it should not look like AI content"): a buyer and a search engine both
# learn these fast. Refused in code, because a prompt alone did not hold them back in the trials.
AI_WORDS = re.compile(r"\b(?:furthermore|moreover|additionally|notably|nestled|boasts?|testament|tapestry|vibrant|bustling|"
                      r"seamless(?:ly)?|elevat(?:e|es|ed|ing)|unparalleled|thoughtfully|meticulous\w*|strategically|ideal(?:ly)?|"
                      r"in conclusion|overall|whether you|stands as|serves as|making it|it is worth|worth (?:noting|asking)|"
                      r"important to note|well[- ]connected|sought[- ]after|prime location|a blend of|key (?:feature|factor)s?|"
                      r"convenient(?:ly)?|easy access|within reach|proximity|ensur(?:e|es|ing)|caters? to|designed to|"
                      r"residents (?:can|will|have)|potential (?:buyers|residents)|prospective)\b|\u2014", re.I)
EVEN_LENGTH = 2.0                     # sentences whose word counts spread less than this read as generated
# what the first trial of writer 5 ended nearly every page with (2026-11-04): one sentence on hundreds of pages is the "scaled
# content" of 2026-10-26, however true it is, and the page's own note already says it
STOCK = re.compile(r"sales? agreement|possession (?:date|timeline)|maharera records?|\badvisable\b|living (?:experience|environment)|"
                   r"specific (?:registration|phase|portion|part)|(?:broader|wider|larger) (?:development|project)|consists? of|"
                   r"takes shape|boutique|footprint|solitary|ventures?\b|true low-rise|the structures? (?:is|are)", re.I)

Gather = Callable[..., Awaitable[Optional[dict]]]   # gather(db, regno, name, locality, city="Pune", now=None) -> {"view", "notes", ...}
PincodeCentre = Callable[..., Awaitable[Optional[tuple]]]   # centre(db, pincode) -> (lat, lon) or None
SheetOf = Callable[..., Awaitable[Optional[dict]]]          # sheet(db, regno) -> the kept property-facts document or None
KeptView = Callable[..., Awaitable[Optional[dict]]]         # view(db, regno) -> the public view of the kept facts sheet, or None
Shown = Callable[..., Awaitable[set]]                       # shown(db) -> page slugs the owner picked for the banner (spotlight)
_deps: Dict[str, Any] = {"gather": None, "pincode_centre": None, "sheet": None, "view": None, "shown": None,
                         "general": project_api.make_fetch(), "buildings": project_api.make_fetch_buildings()}


# fn(store, now): a pass run on every turn of the loop that keeps its own pace (the area maps' pins, areastats.mappins); added
# by wiring.py, since those modules sit on top of this one (mappins -> areamap -> hubs -> enrich)
Daily = Callable[[Store, datetime], Awaitable[Any]]
_daily: List[Tuple[str, Daily]] = []


def add_daily(name: str, fn: Daily) -> None:
    _daily.append((name, fn))


def configure(gather: Optional[Gather] = None, pincode_centre: Optional[PincodeCentre] = None, sheet: Optional[SheetOf] = None,
              general: Optional[project_api.Fetch] = None, buildings: Optional[project_api.Fetch] = None,
              view: Optional[KeptView] = None, shown: Optional[Shown] = None) -> None:
    for k, v in (("gather", gather), ("pincode_centre", pincode_centre), ("sheet", sheet), ("general", general),
                 ("buildings", buildings), ("view", view), ("shown", shown)):
        if v is not None:
            _deps[k] = v


@dataclass(frozen=True)
class Config:
    enabled: bool = False
    every: timedelta = timedelta(minutes=EVERY_MINUTES)
    read_every: timedelta = timedelta(minutes=READ_EVERY_MINUTES)


def load() -> Config:
    on = (os.environ.get("PROJECT_ENRICH_ENABLED") or "").strip().lower() in ("1", "true", "yes", "on")
    mins = int(os.environ.get("PROJECT_ENRICH_EVERY_MINUTES") or EVERY_MINUTES)
    read = int(os.environ.get("PROJECT_READ_EVERY_MINUTES") or READ_EVERY_MINUTES)
    return Config(enabled=on, every=timedelta(minutes=max(1, mins)), read_every=timedelta(minutes=max(1, read)))


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _ours(d: dict) -> bool:
    return bool(d.get("page_slug")) and (d.get("locality") in BY_KEY or bool(d.get("watched_by")))


# "no LLM key" is not among them: a round without a model puts its reading off (reading_due) instead of failing
_UNANSWERED = ("did not answer", "model call failed", "no model answer")


def unanswered(d: dict) -> bool:
    """The last round failed a step because a service did not answer (MahaRERA busy, model down), not because of the project."""
    for st in ((d.get("enrichment") or {}).get("steps") or {}).values():
        why = " ".join([str(st.get("checked") or "")] + [str(r) for r in st.get("refused_reasons") or []])
        if not st.get("ok") and any(w in why for w in _UNANSWERED):
            return True
    return False


def featured(d: dict, now: datetime, shown: frozenset = frozenset()) -> bool:
    """On a page every visitor sees first: an east Pune Top list (pricing.on_top) or the owner's banner pick (`shown`, page slugs)."""
    return d.get("page_slug") in shown or pricing.on_top(d, now)


def priority(d: dict, urgent: set, now: datetime, shown: frozenset = frozenset(), rewrite: bool = False) -> Optional[tuple]:
    """Sort key (lower first) for a project that needs enriching, or None when it does not need it now. `rewrite`: today's
    rewrites of pages in search are not used up, and they go first, most seen by Google first."""
    regno = d.get("regno") or d["_id"]
    if regno in urgent:
        return (-1,)                                            # a campaign asked: first, completed or not
    if rewrite and rewrite_due(d, now):
        return (0, -1, -int(d.get("gsc_impressions") or 0))
    if pages.completion_passed(d, now.date()) and not featured(d, now, shown):
        return None                                             # completed: MahaRERA facts only, unless a campaign asks or homes are left
    key = _priority(d, now, shown)
    if key is None:
        return None
    # east Pune's hot projects first, with its top lists and the owner's banner picks (owner 2026-10-27: "for now just
    # concentrate on east Pune"; until then hot projects went first in every area); then nearly sold out after every other
    # project; then our areas outward from Kharadi, a hot project elsewhere waiting for its area's turn; in each, new launches
    # and hot projects first
    east_hot = int(d.get("hot_score") or 0) >= hot.HOT_MIN and pricing.area_rank(d) < len(pricing.EAST)
    hot_first = 0 if east_hot or featured(d, now, shown) else 1
    return (hot_first, 1 if pages.nearly_sold(d) else 0, pricing.area_rank(d), 0 if pricing.new_or_hot(d, now) else 1, *key)


def complete(d: dict) -> bool:
    """Every stage of the last round passed (score 4/4) and the page shows real pictures. Pictures it does not show do not count:
    with them 143 of 211 hot and Top-list projects counted as complete while 12 showed a photo, and the queue stood empty (2026-11-03)."""
    e = d.get("enrichment") or {}
    if not e or any(not ((e.get("steps") or {}).get(k) or {}).get("ok") for k in STEPS):
        return False
    return bool(d.get("cluster_primary") or pages.shown_pictures((d.get("profile") or {}).get("photos"), drawn=False))


def worth_model(d: dict) -> bool:
    """A page a buyer can land on and search can show. 45 of 140 rounds on 2026-11-04 paid for towers (they redirect to their
    group, so their text is read by nobody) or offices and shops (never in search); their facts rounds need no model."""
    return not d.get("cluster_primary") and pages.homes(d)


def rewrite_due(d: dict, now: datetime) -> bool:
    """A page in search that an older writer wrote and whose last draft was not refused lately (a refused draft is two model
    calls, and the same facts would be refused again)."""
    if not worth_model(d) or not pages.searchable(d) or int(d.get("page_text_version") or 1) >= TEXT_VERSION or parked(d, now):
        return False
    done, no = d.get("enriched_at"), d.get("text_refused_at")
    return (not (isinstance(done, datetime) and now - _aware(done) < MIN_GAP)
            and not (isinstance(no, datetime) and now - _aware(no) < timedelta(days=THIN_RETRY_DAYS)))


async def rewrites_left(store: Store, now: datetime) -> int:
    mark = await store.get_mark(REWRITES)
    return REWRITES_PER_DAY - (int(mark.get("done") or 0) if mark.get("day") == budget.day_of(now) else 0)


async def count_rewrite(store: Store, now: datetime) -> None:
    await store.set_mark(REWRITES, day=budget.day_of(now), done=REWRITES_PER_DAY - await rewrites_left(store, now) + 1)


def text_resting(d: dict, now: datetime) -> bool:
    """A page in search whose text was written under REST_DAYS ago."""
    written = d.get("page_text_at")
    return pages.searchable(d) and isinstance(written, datetime) and now - _aware(written) < timedelta(days=REST_DAYS)


def keeps_text(d: dict, now: datetime) -> bool:
    """A newer writer leaves a resting page alone, whatever else its round reads: a hot or Top-list page comes round weekly, and
    every one rewritten at once would be the 87 of 503 of 2026-10-27 again. Same-version rounds still write, on fresh facts."""
    return text_resting(d, now) and int(d.get("page_text_version") or 1) < TEXT_VERSION


def _priority(d: dict, now: datetime, shown: frozenset = frozenset()) -> Optional[tuple]:
    done, heat = d.get("enriched_at"), int(d.get("hot_score") or 0)
    if parked(d, now) or isinstance(done, datetime) and now - _aware(done) < MIN_GAP:
        return None                                             # failing again and again, or just done: the others go first
    if not worth_model(d):                                      # facts only, after everything else
        return None if isinstance(done, datetime) and now - _aware(done) < timedelta(days=REFRESH_DAYS) else (BACKFILL + 1, 0)
    is_hot = heat >= hot.HOT_MIN
    top = not is_hot and featured(d, now, shown)                # treated as hot, after the hot ones, retried less often
    seen = int(d.get("gsc_impressions") or 0)
    legacy = isinstance(done, datetime) and not d.get("enrichment")   # enriched before buildings and checks: redo
    resting = text_resting(d, now)
    # read by an older version of a step; a page buyers see first does not wait out its rest (owner 2026-11-03: main pages by area need full data)
    stale = isinstance(done, datetime) and bool(outdated(d)) and (not resting or is_hot or top)
    if stale:   # hot: with the hot ones (after those never given a profile); the rest after everything else, Google's first
        if not is_hot and not top and pages.searchable(d):      # what is already in search is improved first
            return (2, 1, -seen, _aware(done).timestamp())
        return (1, 1, -heat) if is_hot or top else (BACKFILL, 1, 1, -seen, _aware(done).timestamp())
    # hot pages are rewritten every HOT_REFRESH_DAYS anyway
    old_writer = (not is_hot and not top and not resting and isinstance(done, datetime) and pages.own_facts(d)
                  and int(d.get("page_text_version") or 1) < TEXT_VERSION)
    if (is_hot or top) and needs_profile(d, now):
        return (1, -heat)                                       # hot and still being built, no profile yet: first
    # a hot page that has not got everything is tried again after TOP_RETRY_DAYS, not after HOT_REFRESH_DAYS; the next day only
    # when a service did not answer (no builder's site found today is not found tomorrow either, and a round costs model calls)
    days = RETRY_DAYS if unanswered(d) else (HOT_REFRESH_DAYS if complete(d) else TOP_RETRY_DAYS) if is_hot else \
        (HOT_REFRESH_DAYS if complete(d) else TOP_RETRY_DAYS) if top else \
        THIN_RETRY_DAYS if pages.indexable(d) and not pages.searchable(d) else REFRESH_DAYS
    if isinstance(done, datetime) and unread_by_family(d):
        return (2, 0, -seen)                                    # with the pages Google shows: it decides whether this page may join them
    if not legacy and not old_writer and isinstance(done, datetime) and now - _aware(done) < timedelta(days=days):
        return None
    if is_hot or top:
        return (1, -heat)                                       # people are buying, searching or talking about it now: hottest first
    if legacy:
        return (3, -seen, _aware(done).timestamp())             # after Google's pages, before the never-enriched ones
    if old_writer and now - _aware(done) < timedelta(days=days):
        return (BACKFILL, 0 if sources_fresh(d, now) else 1, -seen, _aware(done).timestamp())   # cheap rewrites first
    if isinstance(done, datetime):
        return (6, _aware(done).timestamp())                   # due for a refresh, oldest first
    if seen:   # Google already shows it: just off page one first, then most impressions first
        return (2, 0 if searchconsole.near_page_one(d.get("gsc_position"), seen) else 1, -seen)
    return (4 if pages.indexable(d) else 5, -pages.recency(d), -(int(d.get("units_total") or 0)))   # newest first, then bigger


def unread_by_family(d: dict) -> bool:
    """No fact of its own, and its last reading looked for the exact registration's name, which most pages do not print
    (webfacts.gather, 2026-11-02): read once more under the whole project's name instead of waiting THIN_RETRY_DAYS. The round
    records the name it read under whatever it finds, so this comes up once. Towers are read on their group's primary."""
    family = pages.family_name(d)
    return (family != pages.names(d)[0] and d.get("web_read_as") != family and not d.get("cluster_primary")
            and not pages.own_facts(d))


def outdated(d: dict) -> List[str]:
    """The reading steps this project's last round ran with an older version than VERSIONS (a step that never ran is not)."""
    e = d.get("enrichment") or {}
    steps, had = e.get("steps") or {}, e.get("versions") or {}
    return [k for k, v in VERSIONS.items() if (steps.get(k) or {}).get("at") and int(had.get(k) or 1) < v]


def parked(d: dict, now: datetime) -> bool:
    until = d.get("enrich_parked_until")
    return isinstance(until, datetime) and _aware(until) > now


def sources_fresh(d: dict, now: datetime) -> bool:
    """The web facts and profile were read within REFRESH_DAYS: a rewrite for a newer writer uses what they found."""
    at = (((d.get("enrichment") or {}).get("steps") or {}).get("web") or {}).get("at")
    return isinstance(at, datetime) and now - _aware(at) < timedelta(days=REFRESH_DAYS)


def needs_profile(d: dict, now: datetime) -> bool:
    """Still being built and never given a profile round (areastats.profile); towers are read on their group's primary. A round
    that found nothing (no web results name the project) counts: the project then waits for its refresh like any other, or it
    stayed first and was read again every minute (Hollyhock City, 2026-10-20)."""
    tried = (((d.get("enrichment") or {}).get("steps") or {}).get("profile") or {}).get("at")
    return (not d.get("profile") and not tried and not d.get("cluster_primary")
            and (not pages.completion_passed(d, now.date()) or featured(d, now)))


async def next_project(store: Store, now: datetime) -> Optional[dict]:
    urgent = {r["_id"] for r in await store.db.get_collection(REQUESTS).find({}).to_list(200)}
    shown = frozenset(await _deps["shown"](store.db)) if _deps["shown"] else frozenset()
    rewrite = await rewrites_left(store, now) > 0
    ranked = []
    for d in await store.all_projects():
        # an asked-for project is taken even outside our areas (a campaign's project with no locality): skipped, its request
        # stayed and kept the loop running every minute
        if not _ours(d) and (d.get("regno") or d["_id"]) not in urgent:
            continue
        key = priority(d, urgent, now, shown, rewrite)
        if key is not None:
            ranked.append((key, d))
    ranked.sort(key=lambda x: x[0])
    return ranked[0][1] if ranked else None


def _int(v: Any) -> Optional[int]:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    return int(n) if n.is_integer() and n > 0 else None


def whole_project_counts(doc: dict, web: Optional[dict]) -> List[Tuple[dict, int]]:
    """[(web fact, this registration's count)]: the towers or homes the builder's or a property site gives that are more than
    MahaRERA registers under this number. Those describe the whole marketed project (its other phases are other registrations),
    not this page's registration."""
    t = doc.get("building_totals") or {}
    mine = {"towers": _int(t.get("towers")), "homes_total": _int(doc.get("units_total")) or _int(t.get("units_total"))}
    out = []
    for f in (web or {}).get("facts") or []:
        theirs, ours = _int(f.get("value")), mine.get(f.get("key"))
        if theirs and ours and theirs > ours:
            out.append((f, ours))
    return out


def worked_out(doc: dict) -> List[str]:
    """What code works out from the MahaRERA record, as fact lines: the model cannot do this sum itself (`check_text` refuses a
    number not in the facts), and it is what no portal page says. Only this registration's own counts."""
    t = doc.get("building_totals") or {}
    towers, floors, total = _int(t.get("towers")), _int(t.get("max_floors")), _int(doc.get("units_total"))
    lines = []
    if towers and towers > 1 and total and total >= towers:
        lines.append(f"Worked out: about {round(total / towers)} homes per building on average in this registration")
    if floors:
        rise = "low-rise" if floors <= 4 else "mid-rise" if floors <= 14 else "high-rise"
        lines.append(f"Worked out: a {rise} project, going by its tallest building")
    return lines


def area_context(doc: dict, others: Optional[List[dict]]) -> List[str]:
    """How the project sits among the others still being built in its area, as fact lines, from the register alone. No portal
    prints this and no other page of ours can say the same, so it is what makes a page its own. From pages.COMPARE_MIN projects."""
    area = BY_KEY.get(doc.get("locality") or "")
    rest = [o for o in others or [] if o.get("_id") != doc.get("_id") and pages.homes(o) and not o.get("cluster_primary")
            and not pages.completion_passed(o)]
    if not area or len(rest) < pages.COMPARE_MIN:
        return []
    lines = []

    def beside(what: str, mine: Optional[int], theirs: List[Optional[int]]) -> None:
        known = [n for n in theirs if n]
        if mine and len(known) >= pages.COMPARE_MIN:
            lines.append(f"Compared with other projects still being built in {area.name}: {what} {sum(1 for n in known if n < mine)} of {len(known)}")

    beside("its tallest building is higher than that of", _int((doc.get("building_totals") or {}).get("max_floors")),
           [_int((o.get("building_totals") or {}).get("max_floors")) for o in rest])
    beside("this registration has more homes than", _int(doc.get("units_total")), [_int(o.get("units_total")) for o in rest])
    same = sum(1 for o in rest if doc.get("promoter") and o.get("promoter") == doc["promoter"])
    if same:
        lines.append(f"The same filing company has {same} other project{'s' if same > 1 else ''} still being built in {area.name}")
    return lines


def worth_asking(doc: dict, web: Optional[dict]) -> List[str]:
    """The questions this project's own record raises, decided by code: asked to think of some, the model wrote one line for
    every page, and told a builder with no brand to explain its brand (2026-11-04, Alfa Premio)."""
    out = []
    if pages.completion_passed(doc):
        out.append("Worth asking: the filed completion date has passed, so has the occupancy certificate been given")
    b = brands.of(doc)
    if b and doc.get("promoter"):
        out.append(f"Worth asking: it is sold as {b.name} and filed by {doc['promoter']}, so who is building it")
    if whole_project_counts(doc, web):
        out.append("Worth asking: this registration is part of a bigger project, so which part is being bought")
    return out


async def outside_pages(web: Optional[dict], fetch) -> List[Tuple[str, str]]:
    """(site, visible text) of the outside pages the web facts read, fetched now (a page read this round comes from the round's
    memo): the live check that a draft is not their words. Plain reads, no search and no model; a page that does not answer is
    left out and costs the draft nothing."""
    out: List[Tuple[str, str]] = []
    for r in (web or {}).get("read") or []:
        if len(out) >= webfacts.MAX_SOURCES:
            break
        try:
            raw = await fetch(r["url"])
        except Exception:
            log.info("enrich: outside page %s not read", r.get("url"))
            continue
        if raw:
            out.append((str(r.get("site") or r["url"]), webfacts.page_text(raw)[:OUTSIDE_CHARS]))
    return out


def facts_text(doc: dict, gathered: Optional[dict], web: Optional[dict] = None, prof: Optional[dict] = None,
               pinned: bool = False, others: Optional[List[dict]] = None) -> str:
    """Everything the model may use, as plain labelled lines: the register record (dates spelt out with what they are), then the
    gathered sheet. Nearby places only when they were measured from the project's own Google pin (`pinned`): from a locality's
    centre they would put the project somewhere it is not."""
    lines = [pages.paragraph(doc)]
    b = brands.of(doc)
    if b and doc.get("promoter"):
        lines.append(f"Sold under the brand {b.name}; the company filed with MahaRERA is {doc['promoter']}")
    now, first = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))
    if now:
        lines.append(f"Completion date filed with MahaRERA now: {pages._long(now)}")
    if first and first != now:
        lines.append(f"Completion date filed when the project was registered: {pages._long(first)} (this is a completion date, not the registration date)")
        if pages.extension_months(doc) and pages.months_later(doc) == 0:
            lines.append(f"{pages.EXTENSION_NOTE}: that is the whole difference between the two dates; the builder did not move it")
    t = doc.get("building_totals") or {}
    if t.get("towers"):
        lines.append(f"Buildings registered with MahaRERA: {t['towers']}" + (f", up to {t['max_floors']} floors" if t.get("max_floors") else ""))
    lines += worked_out(doc) + area_context(doc, others) + worth_asking(doc, web)
    g = gathered or {}
    for k, v in (g.get("numbers") or {}).items():
        if isinstance(v, (int, float)):
            lines.append(f"{k.replace('_', ' ')}: {v}")
    m = g.get("maharera") or {}
    if m.get("project_type"):
        lines.append(f"MahaRERA project type: {m['project_type']}")
    o = g.get("offer") or {}
    if o.get("price_inr"):
        lines.append(f"Price on the agent's listing: Rs {o['price_inr']:,} ({o.get('source') or 'agent listing'})")
    scoped = {f["key"]: mine for f, mine in whole_project_counts(doc, web)}
    for f, line in zip((web or {}).get("facts") or [], webfacts.lines(web)):
        if f.get("key") in scoped:   # Park Eden Phase I: "five towers" (the builder's site) beside MahaRERA's two buildings
            where = "the builder's site" if f.get("official") else "property sites"
            sites = ", ".join(s["site"] for s in f.get("sources") or [])
            line = (f"{f['label']}: {f['text']} for the whole project, from {where} ({sites}); this registration has "
                    f"{scoped[f['key']]} with MahaRERA")
        lines.append(line)
    lines += [f"Highlight, {x}" for x in profile.lines(prof, doc)]
    if pinned:
        lines += [f"Nearby {str(x.get('label') or 'place').lower()}: {x['name']}, {x['km']} km in a straight line from the project's pin"
                  for x in (g.get("nearby") or [])[:10] if x.get("name") and isinstance(x.get("km"), (int, float))]
    return "\n".join(lines)


def _numbers(text: str) -> set:
    return {n.replace(",", "") for n in NUM.findall(text)}


def check_text(text: str, facts: str) -> List[str]:
    """Problems with a drafted page text; [] means it may be shown."""
    problems = []
    if not text or len(text) < 120:
        problems.append("too short")
    if len(text) > MAX_TEXT:
        problems.append("too long")
    if BANNED.search(text or ""):
        problems.append("sales words")
    extra = _numbers(text or "") - _numbers(facts)
    if extra:
        problems.append("numbers not in the facts: " + ", ".join(sorted(extra)[:5]))
    if re.search(r"https?://|www\.|\+?91[\s-]?\d{5}|\b\d{10}\b", text or ""):
        problems.append("links or phone numbers")
    return problems


SYSTEM = ("You write the \"About the project\" part of a property website's page about one housing project in Pune, for home "
          "buyers. Use ONLY the facts given. Write as a local property researcher who has read the record and tells a friend what "
          "stands out: plain English, your own words, concrete nouns and numbers. Some sentences short, some longer, never all "
          "the same length, and do not start them all the same way. No warming up and no summing up at the end. It must not read "
          "as machine-written: never use furthermore, moreover, additionally, notably, overall, nestled, boasts, vibrant, seamless, "
          "ideal, convenient, proximity, ensures, caters to, designed to, making it, serves as, stands as, residents can, "
          "potential buyers, consists of, takes shape, boutique, footprint, solitary, venture, specific registration, specific "
          "part, specific phase, broader, wider or larger development, the structure is, or a dash in place of a comma. Never give the number of homes in this registration, only the average per building. Never copy a phrase from the facts' lines. No set formula: each page "
          "must read as written for this one project. "
          "The page already shows, above your text, everything listed under ALREADY ON THE PAGE: do not repeat any of it. No "
          "completion date and no word on whether it changed, no count of homes, bookings or homes left, no price, no list of "
          "BHK types, no highlight. Say what those parts of the page cannot. "
          "sections: up to three, each with one of these headings exactly and 3 to 6 sentences, as many as the facts carry; never "
          "pad, a short true section is better than a long empty one: "
          + "; ".join(f'"{h}"' for h in SECTIONS) + ". "
          "\"The project\": name the project once in the first sentence, then its layout (towers or buildings, floors, land, open "
          "space), how this MahaRERA registration sits in the whole marketed project (one phase, some of its towers) when the "
          "facts say, and what is distinctive about it (architect, partners, clubhouse) when the facts say. "
          "\"Location\": the area and the nearby places given, with their distances as given (straight line); when no nearby "
          "places are given, leave the section out. "
          "\"For buyers\": what sets this project apart from others around it, for someone choosing a home here. Lead with the "
          "lines starting \"Compared with\" (say what they mean, in words: one of the taller projects of the area, one of the "
          "smaller) and \"Worked out\", then which of the nearby places given matter to whom. Put a question to the builder only "
          "from a line starting \"Worth asking\", in your own words, and never any other question. Never mention a brand unless "
          "the facts name one, the sale agreement, the possession date or checking MahaRERA's records. Do not explain what "
          "high-rise or mid-rise means, no picture words (skyline, setting, community), do not call a place convenient, and "
          "nothing that would fit any project; no advice to buy or not to buy. When the facts give nothing particular, leave the "
          "section out. "
          "Start each section from what is most particular to this project, not with \"The project consists of\". "
          "Never write a section that only says the facts do not tell. "
          "A count given \"for the whole project\" is the whole marketed project's, not this registration's: when you use it, "
          "say so in the same sentence (\"the whole project has five towers; this phase has two\"). "
          "Write the project's name and the brand as the first two lines give them (not in capital letters). "
          f"search_summary: one line under {MAX_SUMMARY} characters for search results: name, area, what is on offer, completion. "
          "Keep each date with its label. No adjectives of praise, no advice to buy, no numbers that are not in the facts, no "
          "facts about other projects. "
          'Answer as JSON: {"sections": [{"heading": "...", "text": "..."}], "search_summary": "..."}')


def on_page(doc: dict, prof: Optional[dict] = None) -> List[str]:
    """What the page shows outside the writer's sections (hero, answer paragraph, prices, highlights), for the prompt's
    ALREADY ON THE PAGE list: the writer is to add to these, not say them again."""
    name = pages.names(doc)[0]
    area = BY_KEY.get(doc.get("locality") or "")
    b = brands.of(doc)
    builder = ", ".join(x for x in (b.name if b else None, doc.get("promoter")) if x)
    out = [f"Name: {name}" + (f" (MahaRERA: {doc['name']})" if doc.get("name") and doc["name"] != name else ""),
           f"Builder: {builder}" if builder else "",
           f"Area: {area.name if area else doc.get('pune_place_name') or doc.get('place_locality') or 'Pune district'}",
           f"MahaRERA number: {doc.get('regno') or doc['_id']}"]
    now, first = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))
    if now:
        line = f"Completion date filed with MahaRERA: {pages._long(now)}"
        if first and first != now:
            line += f" (at registration {pages._long(first)})"
            if pages.extension_months(doc) and pages.months_later(doc) == 0:
                line += "; it changed only by MahaRERA's order (Order 66/2026), the builder did not move it"
        out.append(line)
    total, sold = _int(doc.get("units_total")), pages.booked(doc)
    if total:
        out.append(f"Homes: {total} in this registration" + (f", {sold} booked" if sold is not None else ""))
    rows = [r for r in (doc.get("prices") or {}).get("rows") or [] if isinstance(r, dict)]
    if rows:
        out.append("Prices: " + "; ".join(f"{r.get('bhk')} from Rs {r['from_inr']:,}" for r in rows
                                          if isinstance(r.get("from_inr"), int)))
        out.append("BHK types: " + ", ".join(dict.fromkeys(str(r["bhk"]) for r in rows if r.get("bhk"))))
    out += [f"Highlight, {x}" for x in profile.lines(prof, doc)]
    return [x for x in out if x]


# a section that only says there is nothing to say, or repeats the warning every page carries (2026-10-22: "No specific
# clubhouse, amenities, or specifications are mentioned in the provided facts.", "Location: Kharadi, Pune.")
NOTHING = re.compile(r"provided facts|not (?:mentioned|specified|available|stated)|no (?:specific|information|details)|"
                     r"check the maharera record before you book", re.I)


# a draft saying the filed date moved; "has not moved" / "not been moved" are fine. Park Eden Phase I (2026-10-25): "an
# increase from 31 Oct 2030", for MahaRERA's own extension
MOVED = re.compile(r"(?<!not )(?<!never )(?<!not been )(?<!no )\b(?:moved|pushed|postponed|delayed|revised|shifted|deferred|"
                   r"rescheduled|increased?|later than (?:the|its) (?:original|first|earlier))\b", re.I)
# "extended" is MahaRERA's own word for its order; said of the builder, or with no MahaRERA in the sentence, it is a move
EXTENDED = re.compile(r"\bextend(?:ed|s)?\b|\bextension\b", re.I)
# the words that put a count on the whole marketed project, not this registration. "Project" alone does not: "the project has
# five towers" is what the Park Eden page said wrongly, and every sentence of the section is about the project
WHOLE = re.compile(r"\b(?:whole|entire|overall|wider|marketed|altogether|in all|project-wide|across the project|"
                   r"(?:all|other|later|future|more|each|every|several|both) (?:the )?phases?|phases)\b", re.I)
BOOKED_WORDS = re.compile(r"\b(?:book\w*|sold|unsold|taken|available|left|remain\w*)\b", re.I)
PRICE = re.compile(r"(?:₹|\bRs\.?|\bINR)\s*\d|\b\d[\d,.]*\s*(?:lakhs?|lacs?|crores?|cr)\b", re.I)
WORDS = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
         "eighteen nineteen twenty").split()


def _sentences(text: str) -> List[str]:
    return [s for s in re.split(r"(?<=[.!?;])\s+|\n+", text) if s.strip()]


def _without_names(doc: dict, text: str) -> str:
    """The text with the project's names taken out: "Rohan Abhilasha 4" and "Park Eden Phase I" carry a number and a phase."""
    for n in sorted(pages.names(doc)[1], key=len, reverse=True):
        text = re.sub(re.escape(n), " ", text, flags=re.I)
    return text


def _says(sentence: str, n: int) -> bool:
    return str(n) in _numbers(sentence) or (n < len(WORDS) and re.search(rf"\b{WORDS[n]}\b", sentence, re.I) is not None)


def _date_said(day: str, text: str) -> bool:
    """The date in any common spelling: "31 Oct 2030", "October 31, 2030", "Oct 2030", "2030-10-31", "31/10/2030"."""
    y, m, d = (int(x) for x in day.split("-"))
    mon = pages._MONTHS[m - 1]
    return bool(re.search(rf"\b{mon}[a-z]*\.?,?\s+(?:\d{{1,2}}(?:st|nd|rd|th)?,?\s+)?{y}\b", text, re.I)
                or re.search(rf"\b{y}-{m:02d}-{d:02d}\b|\b0?{d}[/.-]0?{m}[/.-]{y}\b", text))


def repeats(doc: dict, web: Optional[dict], text: str) -> List[str]:
    """What a draft's sections say that the page already shows (bookings, the homes total, the completion dates, prices), or a
    whole-project count given as this registration's; [] when none."""
    problems = []
    plain = _without_names(doc, text)
    total, sold = _int(doc.get("units_total")), pages.booked(doc)
    if total and str(total) in _numbers(plain):
        problems.append(f"repeats the homes total ({total})")
    left = total - sold if total and sold is not None and sold <= total else None
    for what, n in (("the booking count", sold), ("the homes left", left)):
        if n and any(_says(s, n) and BOOKED_WORDS.search(s) for s in _sentences(plain)):
            problems.append(f"repeats {what} ({n})")
    for day in dict.fromkeys(x for x in (_day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))) if x):
        if _date_said(day, text):
            problems.append(f"repeats the completion date ({pages._long(day)})")
    if PRICE.search(text):
        problems.append("gives a price (the page shows the prices)")
    for f, mine in whole_project_counts(doc, web):
        n = _int(f.get("value"))
        if any(_says(s, n) and not WHOLE.search(s) for s in _sentences(plain)):
            problems.append(f"gives the whole project's {f['label'].lower()} ({n}) as this registration's ({mine})")
    return problems


def says_moved(text: str) -> bool:
    """The draft says the filed completion date was moved (or extended by anyone but MahaRERA)."""
    for s in _sentences(text):
        if MOVED.search(s):
            return True
        if EXTENDED.search(s) and (not re.search(r"maharera", s, re.I) or re.search(r"\b(?:builder|developer|promoter)\b", s, re.I)):
            return True
    return False


def empty_section(text: str) -> bool:
    return bool(NOTHING.search(text)) or len(text) < 60


def sounds_generated(body: str) -> List[str]:
    """What makes a draft read as machine-written: its stock words, every sentence the same length, or one opening word."""
    problems = []
    tell = AI_WORDS.search(body)
    if tell:
        problems.append(f'reads as AI text ("{tell.group(0)}")')
    said = [s for s in _sentences(body) if s.strip()]
    if len(said) >= 5:   # fewer say nothing about rhythm
        sizes = [len(s.split()) for s in said]
        mean = sum(sizes) / len(sizes)
        if (sum((n - mean) ** 2 for n in sizes) / len(sizes)) ** 0.5 < EVEN_LENGTH:
            problems.append("every sentence is the same length")
    if len(said) >= 4:
        first = Counter(s.split()[0].lower() for s in said)
        word, n = first.most_common(1)[0]
        if n >= 3 and n * 2 > len(said):
            problems.append(f'most sentences start with "{word}"')
    return problems


def _words(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _runs(text: str, n: int) -> set:
    w = _words(text)
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def lifted(doc: dict, text: str, facts: str) -> Optional[str]:
    """A run of LIFTED_WORDS words the draft takes from its fact sheet, which carries what the builder's and other sites say:
    a section copied from them is their text, not ours. Names do not count; a builder's filed name alone can run that long."""
    return next(iter(sorted(_runs(_without_names(doc, text), LIFTED_WORDS) & _runs(_without_names(doc, facts), LIFTED_WORDS))), None)


def alike(doc: dict, text: str, others: List[dict]) -> Optional[str]:
    """The name of another project of the area whose page reads like this draft (ALIKE_SHARE of its runs of words). Pages that
    differ only by name are what "scaled content" means, and our 13,000 such pages sank the site on 2026-10-26. Phases of one
    project may well read alike, so only other projects count."""
    mine = _runs(_without_names(doc, text), ALIKE_WORDS)
    family = pages.family_name(doc)
    for o in others:
        if mine and o.get("_id") != doc.get("_id") and o.get("page_text") and pages.family_name(o) != family:
            if len(mine & _runs(_without_names(o, o["page_text"]), ALIKE_WORDS)) / len(mine) >= ALIKE_SHARE:
                return pages.names(o)[0]
    return None


def draft_of(out: Any) -> dict:
    """{text, sections, summary} from the model's answer; `text` is the sections' texts joined (what `page_text` keeps).
    Sections under other headings are dropped; an empty one is kept, for `refused` to refuse. An answer in an older writer's
    shape ({"text"} or {"summary"}: a kept answer) has no sections, and is refused, not shown."""
    out = out if isinstance(out, dict) else {}

    def tidy(v: Any) -> str:   # one line, plain hyphens (models write U+2011 "MahaRERA‑filed")
        return " ".join(str(v or "").replace("‑", "-").replace("‐", "-").split())

    sections: List[dict] = []
    raw = out.get("sections")
    for sec in raw if isinstance(raw, list) else []:
        said = tidy(sec.get("heading")).lower() if isinstance(sec, dict) else ""
        heading = next((h for h in SECTIONS if h.lower() == said), None)
        if heading and heading not in {x["heading"] for x in sections}:
            sections.append({"heading": heading, "text": tidy(sec.get("text"))})
    summary = tidy(out.get("search_summary"))
    return {"text": "\n\n".join(x["text"] for x in sections if x["text"]), "sections": sections,
            "summary": summary if 40 <= len(summary) <= MAX_SUMMARY else None}


def refused(doc: dict, web: Optional[dict], draft: dict, facts: str, others: Optional[List[dict]] = None,
            outside: Optional[List[Tuple[str, str]]] = None) -> List[str]:
    """Why a draft may not be shown; [] when it may."""
    problems: List[str] = []
    if SECTIONS[0] not in [x["heading"] for x in draft["sections"]]:
        problems.append(f'no "{SECTIONS[0]}" section')
    for x in draft["sections"]:
        if empty_section(x["text"]):
            problems.append(f'the "{x["heading"]}" section is empty or says nothing')
    body = draft["text"]
    whole = "\n\n".join([body, draft["summary"] or ""])
    problems += check_text(body, facts) + [p for p in check_text(whole, facts) if p != "too short"]
    problems += repeats(doc, web, body)
    problems += sounds_generated(body)
    if STOCK.search(body):
        problems.append(f'a stock line ("{STOCK.search(body).group(0)}")')
    copied = lifted(doc, body, facts)
    if copied:
        problems.append(f'copies its sources word for word ("{copied}")')
    for site, text in outside or []:
        copied = lifted(doc, body, text)
        if copied:
            problems.append(f'copies {site} word for word ("{copied}")')
    if not worth_asking(doc, web) and re.search(r"\b(?:ask|clarify|inquire|enquire)\b", body, re.I):
        problems.append("puts a question the record does not raise")
    if not brands.of(doc) and re.search(r"\bbrand\b", body, re.I):
        problems.append("speaks of a brand, and the project has none")
    twin = alike(doc, body, others or [])
    if twin:
        problems.append(f"reads like the page of {twin}")
    # the name as the page shows it, in the sections and the search line (2026-10-22: "Prusin Adara" for Prasun Adara); a kept
    # text that does not name the project is dropped by the next round (enrich_one)
    name = pages.names(doc)[0]
    if body and not websearch_mentions(name, body):
        problems.append(f"the sections do not name {name}")
    if draft["summary"] and not websearch_mentions(name, draft["summary"]):
        problems.append(f"the summary does not name {name}")
    # 2026-10-22: "Godrej Ivara Godrej Properties Godrej Ivara, developed by ..." opened a live page
    for x in draft["sections"]:
        first_sentence = re.split(r"(?<=[.!?])\s", x["text"], maxsplit=1)[0]
        if name and first_sentence.lower().count(name.lower()) > 1:
            problems.append(f"the first sentence names {name} twice")
    # MahaRERA's own 2026 extension is not the builder moving the date (2026-10-22: "was moved from 16 Aug 2032 to 16 Dec 2032";
    # 2026-10-25, Park Eden Phase I: "an increase from 31 Oct 2030")
    if pages.extension_months(doc) and pages.months_later(doc) == 0 and says_moved(whole):
        problems.append("says the date moved, but the only change is MahaRERA's 2026 extension")
    return list(dict.fromkeys(problems))


async def sources_text(db, doc: dict) -> str:
    """The fact sheet as the writer is given it, for reading the finished page against it (seo.review)."""
    view = _deps.get("view")
    gathered = await view(db, doc["_id"]) if view else None
    return facts_text(doc, gathered, doc.get("web_facts"), doc.get("profile"),
                      (doc.get("geo") or {}).get("located_from") == "google",
                      await Store(db).projects_in([doc["locality"]]) if doc.get("locality") else [])


async def write_text(llm, doc: dict, gathered: Optional[dict], web: Optional[dict] = None, prof: Optional[dict] = None,
                     pinned: bool = False, others: Optional[List[dict]] = None,
                     outside: Optional[List[Tuple[str, str]]] = None) -> tuple:
    """({text, sections, summary} or None, why it was refused: [] when accepted). A refused draft goes back to the model once with
    the reasons (half of writer 5's first trial was refused over one phrase, and those pages would have stayed short). A refused
    answer is forgotten by a budgeted client (areastats.budget), so the next round asks the model again instead of reading the
    same refused answer back."""
    if llm is None:
        return None, ["no LLM key"]
    facts = facts_text(doc, gathered, web, prof, pinned, others)
    user = "Facts:\n" + facts + "\n\nALREADY ON THE PAGE (do not repeat):\n" + "\n".join(f"- {x}" for x in on_page(doc, prof))
    problems: List[str] = []
    for ask in (user, None):
        ask = ask or f"{user}\n\nYour last draft was refused: {'; '.join(problems)}. Write it again without that."
        try:
            out = await llm.json(SYSTEM, ask)
        except Exception as e:
            log.exception("enrich: model call failed for %s", doc.get("_id"))
            return None, problems or [f"model call failed ({type(e).__name__})"]
        if out is None:
            return None, problems or ["no model answer"]
        draft = draft_of(out)
        problems = refused(doc, web, draft, facts, others, outside)
        if not problems:
            return draft, []
        log.info("enrich: draft for %s refused: %s", doc.get("_id"), "; ".join(problems))
        if hasattr(llm, "forget"):
            try:
                await llm.forget(SYSTEM, ask)
            except Exception:
                log.exception("enrich: forgetting a refused answer failed for %s", doc.get("_id"))
    return None, problems


def sheet_value(sheet: Optional[dict], key: str) -> Any:
    """A usable fact's value from a kept property-facts document (facts are stored as a list of {key, value, usable})."""
    for f in (sheet or {}).get("facts") or []:
        if f.get("key") == key and f.get("usable") and f.get("value") not in (None, ""):
            return f["value"]
    return None


def km_between(a: tuple, b: tuple) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def place_fill(doc: dict, sheet: Optional[dict]) -> dict:
    """Fields the register record lacks and the project's fact sheet (same regno) has: pincode, the place's own name and taluka
    (Gulmohar City P52100076768 came with neither locality nor pincode). `locality` stays our area key, so the place's name goes
    to `place_locality`."""
    if not sheet or str(sheet.get("rera_no") or "").upper() != str(doc.get("regno") or doc["_id"]).upper():
        return {}
    out = {}
    pin = str(sheet_value(sheet, "pincode") or "").strip()
    if not doc.get("pincode") and re.fullmatch(r"\d{6}", pin):
        out["pincode"] = pin
    where = str(sheet.get("locality") or sheet_value(sheet, "locality") or "").strip()
    if not doc.get("locality") and not doc.get("place_locality") and where:
        out["place_locality"] = where
    taluka = str(sheet_value(sheet, "taluka") or "").strip()
    if not doc.get("taluka") and taluka:
        out["taluka"] = taluka
    return out


def _step(ok: bool, now: datetime, **more) -> dict:
    return {"ok": bool(ok), "at": now, **more}


async def check_general(doc: dict, regno: str, mid: Optional[int], now: datetime) -> tuple:
    """(step, register fields): MahaRERA's general record, accepted only when its registration number is this record's."""
    if mid is None:
        return _step(False, now, checked="no MahaRERA id in the record's link"), {}
    body = await _deps["general"](mid)
    if body is None:
        return _step(False, now, checked="MahaRERA did not answer"), {}
    try:
        got = project_api.parse_general(body, regno, mid)
    except project_api.MahaReraError as e:
        return _step(False, now, checked=str(e)), {}
    fields = {k: got[k] for k in ("project_type", "registered_on", "completion_at_registration", "completion_now",
                                  "units_total", "units_booked") if got.get(k) is not None}
    return _step(True, now, checked="regno matches"), {**fields, "details_checked_at": now, "details_ok": True}


async def check_buildings(regno: str, mid: Optional[int], now: datetime) -> tuple:
    """(step, register fields): the building/wing summary, kept only when every row is this project's (projectId and regno)."""
    if mid is None:
        return _step(False, now, count=0, checked="no MahaRERA id in the record's link"), {}
    body = await _deps["buildings"](mid)
    if body is None:
        return _step(False, now, count=0, checked="MahaRERA did not answer"), {}
    try:
        rows = project_api.parse_buildings(body, regno, mid)
    except project_api.MahaReraError as e:
        return _step(False, now, count=0, checked=str(e)), {}
    # a plotted layout has no buildings: that is an answer, not a failure; nothing is stored
    fields = {"buildings": rows, "building_totals": project_api.building_totals(rows)} if rows else {"buildings": [], "building_totals": None}
    return _step(True, now, count=len(rows), checked="projectId and regno match" if rows else "no buildings (plotted?)"), fields


async def check_places(store: Store, doc: dict, sheet: Optional[dict], located_from: str, now: datetime) -> tuple:
    """(step, register fields): where the gathered sheet put the project, checked against the pincode's centre."""
    lat, lon = sheet_value(sheet, "lat"), sheet_value(sheet, "lon")
    if sheet_value(sheet, "located_at") == "project":
        located_from = "google"                                    # the project's own pin (propertyfacts.pin)
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return _step(False, now, located_from=located_from or None, checked="no position found"), {}
    fields = {"geo": {"lat": float(lat), "lon": float(lon), "located_from": located_from}}
    pin, centre = doc.get("pincode"), None
    if pin and _deps["pincode_centre"] is not None:
        try:
            centre = await _deps["pincode_centre"](store.db, pin)
        except Exception:
            log.exception("enrich: pincode centre failed for %s", pin)
    if not centre:
        return _step(False, now, located_from=located_from, checked="no pincode centre to check against"), fields
    km = round(km_between((float(lat), float(lon)), centre), 1)
    ok = km <= NEAR_KM and bool(doc.get("locality") or doc.get("place_locality"))
    why = f"{km} km from pincode {pin}'s centre" + ("" if km <= NEAR_KM else f" (more than {NEAR_KM:g} km)")
    if not (doc.get("locality") or doc.get("place_locality")):
        why += "; locality missing"
    fields["geo"]["km_from_pincode"] = km
    return _step(ok, now, located_from=located_from, checked=f"within {NEAR_KM:g} km of the project's pincode area: {why}"), fields


def score(steps: dict) -> str:
    return f"{sum(1 for k in STEPS if (steps.get(k) or {}).get('ok'))}/{len(STEPS)}"


def tier_of(doc: dict, urgent: bool = False, now: Optional[datetime] = None) -> str:
    """How much a project's reading may spend (areastats.budget.route): a campaign about to post, then the premium ones (hot,
    shown by Google, the first areas: pricing.tier_of), then the rest."""
    return budget.URGENT if urgent else pricing.tier_of(doc, now)


def _ask(llm, tier: str, step: str):
    """The client one step uses: the budgeted Reader's view for that step, or a plain client as it is (tests, scripts)."""
    return llm.ask(tier, step) if hasattr(llm, "ask") else llm


def can_read(llm, tier: str) -> bool:
    """A model may be asked this round: there is one, and (budgeted) today's pools have room for a project of this tier."""
    if llm is None:
        return False
    return llm.can_read(tier) if hasattr(llm, "can_read") else True


def _deferred(llm) -> int:
    return int(getattr(llm, "deferred", 0) or 0)


def details_fresh(doc: dict, now: datetime) -> bool:
    """The register's own details read (areastats.refresh) is recent and good: the round uses it instead of reading MahaRERA's
    general record again."""
    at = doc.get("details_checked_at")
    return bool(doc.get("details_ok")) and isinstance(at, datetime) and now - _aware(at) < timedelta(days=DETAILS_FRESH_DAYS)


def buildings_fresh(doc: dict, now: datetime) -> bool:
    st = (((doc.get("enrichment") or {}).get("steps") or {}).get("buildings") or {})
    return bool(st.get("ok")) and isinstance(st.get("at"), datetime) and now - _aware(st["at"]) < timedelta(days=BUILDINGS_FRESH_DAYS)


async def enrich_one(store: Store, doc: dict, llm, now: datetime, reread: bool = True, facts: bool = True,
                     urgent: bool = False, rewrite: bool = False) -> dict:
    """One round for one project. `facts`: the steps that need no model (MahaRERA, the gatherer, the place, the pictures); a
    reading round (`facts=False`, read_step) uses what the last facts round kept. The model steps (web facts, highlights,
    prices, the page text) run when a model may be asked (`can_read`); otherwise, or when today's budget runs out half way
    (areastats.budget), they are put off: the last round's results stay, `reading_due` says the reading waits, and nothing
    counts as failed. `reread=False` (a rewrite for a newer writer, sources_fresh): the web facts and profile kept from the
    last round are used as they are, and their steps are carried over. `rewrite`: one of the day's rewrites of a page in search,
    which does not wait out its rest."""
    regno = doc.get("regno") or doc["_id"]
    gather = _deps["gather"]
    gathered, notes, steps, placed = None, [], {}, {}
    kept_steps = (doc.get("enrichment") or {}).get("steps") or {}
    kept_versions = (doc.get("enrichment") or {}).get("versions") or {}
    mid = register.maharera_id(doc.get("source_url", ""))
    sheet_of = _deps["sheet"]
    tier = tier_of(doc, urgent)
    reading = can_read(llm, tier)
    spends = urgent or worth_model(doc)

    async def sheet() -> Optional[dict]:
        if sheet_of is None:
            return None
        try:
            return await sheet_of(store.db, regno)
        except Exception:
            log.exception("enrich: fact sheet read failed for %s", regno)
            return None

    if facts:
        fill = place_fill(doc, await sheet())
        if fill:
            await store.set_project(doc["_id"], **fill)
            doc = {**doc, **fill}
        # MahaRERA, one read after the other (it is a public service); the register's own recent read is used as it is
        read_maharera = False
        if not urgent and details_fresh(doc, now):
            steps["maharera_general"] = _step(True, now, checked="regno matches (the register's read of "
                                              f"{_aware(doc['details_checked_at']).date().isoformat()})")
        else:
            steps["maharera_general"], general = await check_general(doc, regno, mid, now)
            read_maharera = mid is not None
            if general:
                # this read refreshes details_checked_at, so the register refresh skips the record: the readings it would have
                # kept (homes booked, a moved date) are kept here, by the same rule, or a hot project's history is lost
                move = readings.date_move(doc, general, now)
                if move:
                    await store.add_date_move(doc["_id"], move)
                general = {**general, **readings.booked(doc, general, now)}
                await store.set_project(doc["_id"], **general)
                doc = {**doc, **general}
        if not urgent and buildings_fresh(doc, now):
            steps["buildings"] = kept_steps["buildings"]
        else:
            if read_maharera:
                await asyncio.sleep(PAUSE)
            steps["buildings"], built = await check_buildings(regno, mid, now)
            if built:
                await store.set_project(doc["_id"], **built)
                doc = {**doc, **built}
        area = BY_KEY.get(doc.get("locality") or "")
        where, located_from = ((area.name, "locality") if area else (doc["place_locality"], "listing") if doc.get("place_locality")
                               else (doc["pincode"], "pincode") if doc.get("pincode") else (None, ""))
        if gather is not None:
            try:
                got = await gather(store.db, regno, doc.get("name", ""), where, now=now) or {}
                # propertyfacts.enrich.gather_project: {"key", "view" (the public facts view), "notes", "match"}; a plain view is accepted too
                gathered = got.get("view") if "view" in got else (got or None)
                notes += [str(n) for n in got.get("notes") or []][:5]
            except Exception as e:
                log.exception("enrich: gathering failed for %s", regno)
                notes.append(f"gathering failed ({type(e).__name__})")
        else:
            notes.append("no gatherer configured")
        steps["places"], placed = await check_places(store, doc, await sheet(), located_from, now)
    else:
        for k in ("maharera_general", "buildings", "places"):
            steps[k] = kept_steps.get(k) or {}
        if _deps["view"] is not None:
            try:
                gathered = await _deps["view"](store.db, regno)
            except Exception:
                log.exception("enrich: kept facts read failed for %s", regno)
    fetch = webfacts.memo(webfacts.fetch_page)   # the web facts and the profile read the same pages: each once
    web, prof, put_off = {}, {}, []
    ran = set()

    async def model_step(key: str, run) -> dict:
        """Run a model step; a step whose questions were put off for the budget keeps the last round's result."""
        ask = _ask(llm, tier, key)
        before = _deferred(ask)
        try:
            st, fields = await asyncio.wait_for(run(ask), STEP_SECONDS)
        except Exception as e:
            log.exception("enrich: %s failed for %s", key, regno)
            st, fields = _step(False, now, checked=f"failed ({type(e).__name__})"), {}
        if _deferred(ask) > before:
            put_off.append(key)
            if key != "profile":   # the profile keeps its new pictures and its last highlights itself
                steps[key] = kept_steps.get(key) or {}
                return {}
        steps[key] = st
        ran.add(key)
        if fields:
            await store.set_project(doc["_id"], **fields)
        return fields

    if not reread or not spends:
        steps["web"], steps["profile"] = kept_steps.get("web") or {}, kept_steps.get("profile") or {}
        steps["prices"] = kept_steps.get("prices") or {}
    elif reading:
        web = await model_step("web", lambda a: webfacts.gather(store, doc, a, now, fetch=fetch))
        prof = await model_step("profile", lambda a: profile.gather(store, doc, a, now, fetch=fetch))
        await model_step("prices", lambda a: prices.gather(store, doc, a, now, fetch=fetch))
    else:   # no model may be asked: the pictures are still read (code), the rest waits
        put_off += ["web", "prices"]
        steps["web"], steps["prices"] = kept_steps.get("web") or {}, kept_steps.get("prices") or {}
        if facts:
            prof = await model_step("profile", lambda a: profile.gather(store, doc, None, now, fetch=fetch))
        else:
            steps["profile"] = kept_steps.get("profile") or {}
    pinned = ((placed or {}).get("geo") or doc.get("geo") or {}).get("located_from") == "google"
    draft, text, turned_down = None, None, False
    # the writer is the last step: only with every read done, and something of the project's own to write from
    writable = urgent or pages.own_facts(await store.project(doc["_id"]) or doc)
    if not spends or reading and not put_off and not writable or reading and not urgent and not rewrite and keeps_text(doc, now):
        steps["text"] = kept_steps.get("text") or {}
        if spends and not writable:
            notes.append("no text written: no fact of its own yet")
    elif reading and not put_off:
        ask = _ask(llm, tier, "text")
        before = _deferred(ask)
        web_now = (web or {}).get("web_facts") or doc.get("web_facts")
        draft, refused = await write_text(ask, doc, gathered, web_now, (prof or {}).get("profile") or doc.get("profile"), pinned,
                                          await store.projects_in([doc["locality"]]) if doc.get("locality") else [],
                                          await outside_pages(web_now, fetch))
        if _deferred(ask) > before:
            put_off.append("text")
            steps["text"] = kept_steps.get("text") or {}
        else:
            text = (draft or {}).get("text")
            steps["text"] = _step(bool(text), now, refused_reasons=refused)
            ran.add("text")
            if text is None:
                turned_down = True
                notes.extend(refused)
                notes.append("kept the code-written paragraph")
    else:
        put_off.append("text")
        steps["text"] = kept_steps.get("text") or {}
    if put_off:
        why = "no LLM key" if llm is None else "the model budget for today is spent"
        notes.append(f"reading put off ({why}): {', '.join(dict.fromkeys(put_off))}")
    # the versions the reading steps ran with (a carried-over step keeps the version it was read with)
    versions = {k: (VERSIONS[k] if k in ran else int(kept_versions.get(k) or 1)) for k in VERSIONS}
    enrichment = {"at": now, "steps": steps, "score": score(steps), "versions": versions}
    trace.event(log, "enrich", regno, "done", trace.OK if text and gathered else trace.FALLBACK, text="model" if text else "code",
                facts="gathered" if gathered else "none", score=enrichment["score"], notes="; ".join(notes) or None)
    fields = {"enrich_notes": notes, "enrichment": enrichment, **placed, "reading_due": bool(put_off),
              "enrich_fails": 0, "enrich_error": None, "enrich_parked_until": None}
    if facts:
        fields.update(enriched_at=now, enrich_gathered=bool(gathered))
    if not put_off:
        fields["read_at"] = now
    if "web" in ran:
        fields["web_read_as"] = pages.family_name(doc)
    if turned_down:
        fields["text_refused_at"] = now
    if text:
        fields.update(page_text=text, page_text_version=TEXT_VERSION, page_sections=draft["sections"], page_summary=draft["summary"])
        if text != doc.get("page_text") or draft["summary"] != doc.get("page_summary"):
            fields["page_text_at"] = now   # the page's date moves only when what a reader sees changed
    elif "text" in ran and doc.get("page_text") and not websearch_mentions(pages.names(doc)[0], doc["page_text"]):
        # a kept text that does not name the project (a model's misspelling) gives way to the code-written paragraph
        fields.update(page_text=None, page_sections=None, page_summary=None)
        notes.append("old text dropped: it does not name the project")
    await store.set_project(doc["_id"], **fields)
    if rewrite and text:
        await count_rewrite(store, now)
    if facts:
        await store.db.get_collection(REQUESTS).delete_one({"_id": regno})
    return {"regno": regno, "text": bool(text), "gathered": bool(gathered), "notes": notes, "score": enrichment["score"],
            "reading_due": bool(put_off)}


# ---- the owner's view: what is enriched and checked ------------------------------------------------------------------------

STATUSES = ("ok", "partial", "failed", "parked", "waiting", "finished")


def status_of(d: dict, today=None) -> str:
    if parked(d, datetime.now(timezone.utc)):
        return "parked"
    e = d.get("enrichment")
    if not e:
        return "finished" if pages.completion_passed(d, today) else "waiting"   # completed: never enriched, MahaRERA facts only
    n = sum(1 for k in STEPS if ((e.get("steps") or {}).get(k) or {}).get("ok"))
    return "ok" if n == len(STEPS) else "failed" if n <= 1 else "partial"


def _iso(v: Any) -> Optional[str]:
    return _aware(v).isoformat() if isinstance(v, datetime) else None


async def status_list(store: Store, status: Optional[str] = None, limit: int = 300) -> dict:
    """{counts: {ok, partial, failed, waiting, finished}, items: [...]} over the project pages we enrich, newest enrichment first."""
    docs = [d for d in await store.all_projects() if _ours(d)]
    counts = {s: 0 for s in STATUSES}
    items = []
    for d in docs:
        s = status_of(d)
        counts[s] += 1
        if status and s != status:
            continue
        e = d.get("enrichment") or {}
        area = BY_KEY.get(d.get("locality") or "")
        items.append({
            "regno": d.get("regno") or d["_id"], "name": d.get("name", ""), "status": s,
            "area": area.name if area else (d.get("place_locality") or d.get("taluka") or None),
            "enriched_at": _iso(d.get("enriched_at")), "score": e.get("score"),
            "failed": [k for k in STEPS if not ((e.get("steps") or {}).get(k) or {}).get("ok")] if e else [],
            "checks": {k: ((e.get("steps") or {}).get(k) or {}).get("checked") or (((e.get("steps") or {}).get(k) or {}).get("refused_reasons") or None)
                       for k in STEPS + ("web", "profile", "prices")} if e else {},
            "page": f"/projects/{d['page_slug']}" if d.get("page_slug") else None,
            "error": d.get("enrich_error"), "fails": int(d.get("enrich_fails") or 0),
            "parked_until": _iso(d.get("enrich_parked_until")), "outdated": outdated(d),
            "reading_due": bool(d.get("reading_due")), "read_at": _iso(d.get("read_at")),
        })
    items.sort(key=lambda x: x["enriched_at"] or "", reverse=True)
    now = datetime.now(timezone.utc)
    waiting = sum(1 for d in docs if reading_key(d, now) is not None)
    return {"counts": counts, "items": items[:max(1, limit)], "reading_waiting": waiting,
            "budget": await budget.today(store.db, now)}


async def enrich_now(db, regno: str, by: str = "campaign") -> bool:
    """Ask for a project's enrichment at once (the loop takes it within POLL_SECONDS). False when the register lacks it."""
    store = Store(db)
    regno = (regno or "").strip().upper()
    doc = await store.project(regno)
    if doc is None:
        return False
    if not doc.get("page_slug"):
        await pages.assign_slug(store, doc)
    reqs = db.get_collection(REQUESTS)
    if await reqs.find_one({"_id": regno}) is None:
        await reqs.insert_one({"_id": regno, "at": datetime.now(timezone.utc), "by": by})
    return True


busy = budget.busy   # moved to areastats.budget; kept here for callers of the old name


async def step(store: Store, llm, now: datetime, last_regular: Optional[datetime], every: timedelta) -> Optional[dict]:
    """The facts turn: urgent requests always; otherwise one project when `every` has passed since the last regular one. Its
    reading runs in the same round when a model may be asked, else it is put off (read_step takes it later)."""
    urgent = await store.db.get_collection(REQUESTS).count_documents({})
    if not urgent and last_regular is not None and now - _aware(last_regular) < every:
        return None
    doc = await next_project(store, now)
    if doc is None:
        return None
    reread = True
    is_urgent = bool(urgent) and (doc.get("regno") or doc["_id"]) in await _urgent(store)
    rewrite = not is_urgent and rewrite_due(doc, now) and await rewrites_left(store, now) > 0
    if rewrite:                                                 # the writer alone when what the sites say is recent
        reread = not sources_fresh(doc, now) or bool(outdated(doc))
    elif not is_urgent and (_priority(doc, now) or (0,))[0] == BACKFILL:   # the group of the key before the area and launch order
        reread = not sources_fresh(doc, now) or bool(outdated(doc))
        if reread and last_regular is not None and now - _aware(last_regular) < BACKFILL_EVERY:
            return None
        if not can_read(llm, tier_of(doc)) or busy(llm):   # a rewrite is reading only: it waits for a model with room
            log.info("enrich: rewrite for %s waits: no model has room", doc.get("_id"))
            return None
    try:
        out = await asyncio.wait_for(enrich_one(store, doc, llm, now, reread=reread, urgent=is_urgent, rewrite=rewrite), ROUND_SECONDS)
    except asyncio.CancelledError:
        raise
    except Exception as e:   # noted on the record and the next project goes on; the request does not keep the loop busy
        out = await failed_round(store, doc, now, e)
    out["urgent"] = bool(urgent)
    return out


async def _urgent(store: Store) -> set:
    return {r["_id"] for r in await store.db.get_collection(REQUESTS).find({}).to_list(200)}


def reading_key(d: dict, now: datetime) -> Optional[tuple]:
    """Sort key (lower first) for a project whose reading was put off, or None when it has none waiting: premium projects
    first (hot, then Google's), then our areas outward from Kharadi, oldest wait first."""
    if not d.get("reading_due") or not worth_model(d) or parked(d, now) or pages.completion_passed(d, now.date()) and not pricing.on_top(d, now):
        return None
    failed = d.get("read_failed_at")
    if isinstance(failed, datetime) and now - _aware(failed) < MIN_GAP:
        return None
    tier = tier_of(d, now=now)
    return (0 if tier == budget.PREMIUM else 1, -int(d.get("hot_score") or 0), -int(d.get("gsc_impressions") or 0),
            pricing.area_rank(d), _aware(d["enriched_at"]).timestamp() if isinstance(d.get("enriched_at"), datetime) else 0)


async def read_step(store: Store, llm, now: datetime, last_read: Optional[datetime], every: timedelta) -> Optional[dict]:
    """The reading turn: one project whose reading was put off (no model, or the day's budget was spent), the most valuable
    first, when `every` has passed and today's budget has room for it. Uses the facts the last facts round kept."""
    if llm is None or last_read is not None and now - _aware(last_read) < every:
        return None
    ranked = sorted(((k, d) for d in await store.all_projects() if _ours(d) and (k := reading_key(d, now)) is not None),
                    key=lambda x: x[0])
    doc = next((d for _, d in ranked if can_read(llm, tier_of(d))), None)
    if doc is None:
        return None
    try:
        out = await asyncio.wait_for(enrich_one(store, doc, llm, now, facts=False), ROUND_SECONDS)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.exception("enrich: reading round failed for %s", doc.get("regno") or doc["_id"])
        await store.set_project(doc["_id"], read_failed_at=now, enrich_error=f"reading failed ({type(e).__name__})")
        out = {"regno": doc.get("regno") or doc["_id"], "text": False, "notes": [f"reading failed ({type(e).__name__})"],
               "score": None, "reading_due": True}
    out["reading"] = True
    return out


async def failed_round(store: Store, doc: dict, now: datetime, e: Exception) -> dict:
    """A round that crashed or ran past ROUND_SECONDS: noted on the record (enrich_fails, enrich_error), the project waits MIN_GAP
    like any other, and after MAX_FAILS in a row it is parked for PARK_DAYS, for a fix offline (owner's list: status "parked")."""
    regno = doc.get("regno") or doc["_id"]
    why = "round took longer than %d min" % (ROUND_SECONDS // 60) if isinstance(e, asyncio.TimeoutError) else f"round failed ({type(e).__name__}: {e})"[:300]
    if not isinstance(e, asyncio.TimeoutError):
        log.error("enrich: round failed for %s", regno, exc_info=e)
    fails = int(doc.get("enrich_fails") or 0) + 1
    fields = {"enriched_at": now, "enrich_fails": fails, "enrich_error": why}
    if fails >= MAX_FAILS:
        fields["enrich_parked_until"] = now + timedelta(days=PARK_DAYS)
    await store.set_project(doc["_id"], **fields)
    await store.db.get_collection(REQUESTS).delete_one({"_id": regno})
    trace.event(log, "enrich", regno, "done", trace.FALLBACK, notes=why, fails=fails, parked=fails >= MAX_FAILS)
    return {"regno": regno, "text": False, "gathered": False, "notes": [why], "score": None}


async def loop() -> None:
    from app.core.database import get_database
    from app.platform.heartbeats import heartbeat

    log.info("enrich: loop started")
    last_regular: Optional[datetime] = None
    last_read: Optional[datetime] = None
    last_prices: Optional[datetime] = None
    pruned_day: Optional[str] = None
    while True:
        cfg = load()
        try:
            async with heartbeat("project_enrich", get_database, on=cfg.enabled):
                if cfg.enabled:
                    now = datetime.now(timezone.utc)
                    try:  # what Google shows of our project pages, once a day, so those are enriched first
                        seen = await searchconsole.refresh(Store(get_database()), now)
                        if seen:
                            log.info("enrich: Search Console %s", seen)
                    except Exception:
                        log.exception("enrich: Search Console read failed")
                    try:  # which projects are hot today, so they are enriched first
                        scored = await hot.refresh(Store(get_database()), now)
                        if scored:
                            log.info("enrich: hot projects %s", scored)
                    except Exception:
                        log.exception("enrich: hot projects scoring failed")
                    for name, daily in _daily:   # passes other parts of areastats add (each keeps its own once-a-day mark)
                        try:
                            await daily(Store(get_database()), now)
                        except Exception:
                            log.exception("enrich: %s round failed", name)
                    if pruned_day != budget.day_of(now):
                        try:   # kept model answers nobody asked for in a long while
                            await budget.prune(get_database(), now)
                            pruned_day = budget.day_of(now)
                        except Exception:
                            log.exception("enrich: pruning kept answers failed")
                    # today's model budget (areastats.budget): None when no model key is set at all
                    llm = await budget.reader(get_database(), now)
                    out = await step(Store(get_database()), llm, now, last_regular, cfg.every)
                    if out:   # enrich_one logged it (pipeline=enrich)
                        if not out["urgent"]:
                            last_regular = now
                    try:   # a project whose reading was put off, when today's budget has room
                        if await read_step(Store(get_database()), llm, datetime.now(timezone.utc), last_read, cfg.read_every):
                            last_read = now
                    except Exception:
                        log.exception("enrich: reading round failed")
                    try:   # prices on their own turn, Upper Kharadi, Kharadi and Wagholi first (areastats.pricing)
                        if await pricing.step(Store(get_database()), llm, datetime.now(timezone.utc), last_prices):
                            last_prices = now
                    except Exception:
                        log.exception("enrich: prices round failed")
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("enrich: cycle failed")
        await asyncio.sleep(POLL_SECONDS)
