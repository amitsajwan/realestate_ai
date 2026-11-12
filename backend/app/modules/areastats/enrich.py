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
   `points_of` drops a point with a number its facts do not say, stock words, an overclaim, a question the facts do not raise or
   another site's words (`outside_pages`), and `alike` refuses what reads like another page of the area; a refused answer goes
   back once with the reasons, and a page with no text then gets plain points from code (`code_points`). The model is also given
   how the project sits among its area's (`area_context`) and the questions its facts raise (`worth_asking`), both worked out
   by code. A page in search keeps its text REST_DAYS before a newer writer takes it (`keeps_text`).
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
own on the record (`pages.own_facts`). A page in search keeps its model-written text while the fact sheet's lines about the
project itself stand (`settled`, `own_facts_key`; the area's lines and the questions to ask move with other projects and do
not count), and no page in search goes to a newer writer for that alone (REWRITES_PER_DAY 0, owner 2026-11-05,
docs/plan/search-recovery.md R1). After each round the page's place in or out of search is stored (`pages.search_state`) and
held SEARCH_HOLD_DAYS.
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
import hashlib
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
from app.modules.newsroom.policy import AREA_PINCODES, SHARED_PINCODES, UPPER_KHARADI_PINCODES
from app.modules.newsroom.store import Store
from app.platform import trace

from . import brands, budget, hot, launches, pagefacts, pages, prices, pricing, profile, readings, searchconsole, webfacts, websearch
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
LAUNCH_RETRY_DAYS = 1                 # a new launch with too little to show is read again this soon: the sites are filling in now
THIN_RETRY_DAYS = 7                   # a page kept out of search as thin (pages.searchable) is tried again after this, not
                                      # REFRESH_DAYS (owner 2026-10-31: "make cycle bit faster", only pages with proper text in search)
POLL_SECONDS = 60
REQUESTS = "enrich_requests"          # {_id: regno, at, by}: urgent enrichments asked for by campaigns
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
# 6 (owner 2026-11-04: "dont you think points would have been better using AI"): the page opens with 3 to 5 points the model picks
# from the stored fact sheet (`fact_sheet`, `write_points`), each naming the facts it used, in place of the written sections, which
# said again what the page shows.
# 7 (the first 170 pages read back, 2026-11-04): a part of a project is not called small, no superlatives, a label says the finding
# with its number, and a label already on other pages of the area goes back.
TEXT_VERSION = 7
MIN_POINTS = 2                        # fewer say nothing a buyer cannot see at a glance
MAX_POINTS = 5
MAX_POINT = 240                       # characters
LABEL_REPEATS = 2                     # a point's label on this many other pages of the area is a template, not a finding
OVERCLAIM = re.compile(r"\b(?:the\s+)?(?:largest|biggest|tallest|smallest|strongest|best|reliable|trusted)\b|\bthe (?:highest|lowest)\b(?! building| floor)|"
                       r"\b(?:the|an?) average\b|\d+% average|middle (?:figure|booking|rate)|the middle of", re.I)
PART_OF_PROJECT = re.compile(r"\b(?:phase|part|tower|wing|building|bldg|block)\b", re.I)
# Each reading step has a version (owner 2026-10-20: "enrichment can happen again: we improve it, get more info, a better model").
# Raise a step's number when the step gets better (a new rule, a new source, a better model): every project that step read with
# an older version is read again, in the BACKFILL group, hot ones first. Kept per project in `enrichment.versions`.
# profile 2: the builder's site found through the brand, on the domain's own name (ef886e0b, e1c6adb9)
# profile 3: pictures listed in the page data (sites that draw them by script, godrejproperties.com); room renders are photos
# web 2, profile 4, prices 2: pages found through the MahaRERA number and the builder's whole name (2026-11-03, owner: "rera number
# from maha rera, then map with online data"); of 103 projects on the east Pune Top lists only 10 had text, highlights, prices and photos
# web 3, profile 5, prices 3: the builder's site looked for on its own, sites that never give anything left out, and an address
# landing on another site read as nothing (2026-11-04)
VERSIONS = {"web": 3, "profile": 5, "prices": 3}
# fail and move on (owner 2026-10-20: "note it and continue with others, find a solution offline later"): each reading step
# has STEP_SECONDS, the whole round ROUND_SECONDS; a project is not taken again within MIN_GAP (urgent requests aside), and
# after MAX_FAILS failed rounds in a row it is parked for PARK_DAYS with its reason in the owner's list (status "parked")
STEP_SECONDS = 240
ROUND_SECONDS = 15 * 60
MIN_GAP = timedelta(hours=6)
# a page in Google keeps its text this long before a newer writer or reader version takes it again: 87 of 503 searchable
# pages were rewritten in one day (2026-10-27), and a site rewriting itself that fast reads as machine-made
REST_DAYS = 14
AI_FROM = "2027-01-01"                # a filed completion date before this gets no model (owner 2026-11-05: "possession 2027 and afterward,
                                      # this is not priority to spend on old projects"; 65 of 432 pages in search, 17 of 195 clicks)
# pages in search given to a newer writer each day: none from 2026-11-05 (docs/plan/search-recovery.md R1: a newer writer is
# not a reason to change a page Google shows; its own facts changing is, `settled`). Was 20.
WIDER_PER_DAY = 60                    # pages outside our areas read a day (owner 2026-11-08), a limit set by Serper: a read takes ~3
WIDER_KEEP_CREDITS = 500              # Serper searches kept back: a spent account reads as "no site mentions this project"
WIDER = "enrich_wider"                # mark: {day, done, credits}
BIG_PROJECT = 100                     # homes, for the wider read's order
REWRITES_PER_DAY = 0
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
ASKS = re.compile(r"\b(?:ask|clarify|inquire|enquire)\b", re.I)
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
    wider_per_day: int = WIDER_PER_DAY


def load() -> Config:
    on = (os.environ.get("PROJECT_ENRICH_ENABLED") or "").strip().lower() in ("1", "true", "yes", "on")
    mins = int(os.environ.get("PROJECT_ENRICH_EVERY_MINUTES") or EVERY_MINUTES)
    read = int(os.environ.get("PROJECT_READ_EVERY_MINUTES") or READ_EVERY_MINUTES)
    return Config(enabled=on, every=timedelta(minutes=max(1, mins)), read_every=timedelta(minutes=max(1, read)),
                  wider_per_day=int(os.environ.get("PROJECT_WIDER_PER_DAY") or WIDER_PER_DAY))


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _ours(d: dict) -> bool:
    """Kept fresh on our areas' timetable: in our areas, an agent's project, or a watched page already in search. Any other watched
    page is not: a first read puts every page on the watch list (`pages.marketed`), and 3,700 pages read again each week would
    spend Serper's balance in days."""
    if not d.get("page_slug"):
        return False
    if d.get("locality") in BY_KEY or pages.marketed(d):
        return True
    return bool(d.get("watched_by")) and (d.get("search_state") or {}).get("in") is True


def wider(d: dict, now: datetime) -> bool:
    """A page outside our areas worth its first read (owner 2026-11-08): filed for 2027 or later, never read, and listable."""
    return (not _ours(d) and bool(d.get("page_slug")) and not d.get("enriched_at") and bool(_day(d.get("completion_now")))
            and worth_model(d) and pages.indexable(d) and not pages.is_old(d) and not parked(d, now))


def wider_key(d: dict) -> tuple:
    """After everything in our areas: big projects before small, homes before offices and shops, the newest registered first."""
    kind = (0 if launches.home_count(d) >= BIG_PROJECT else 1) if pages.homes(d) else 2
    day = pages._day(d.get("registered_on")) or ""
    return (5, kind, -int(day.replace("-", "") or 0), d.get("_id") or "")


async def wider_left(store: Store, now: datetime) -> int:
    """First reads of pages outside our areas left today. Serper's balance is read once a day; at WIDER_KEEP_CREDITS they stop, so
    the daily rank checks and our own areas keep their searches. An unknown balance stops them too: a spent account looks the same."""
    mark, day = await store.get_mark(WIDER), budget.day_of(now)
    if mark.get("day") == day:
        return 0 if mark.get("stopped") else load().wider_per_day - int(mark.get("done") or 0)
    left = await websearch.credits()
    stopped = left is None or left <= WIDER_KEEP_CREDITS
    await store.set_mark(WIDER, day=day, done=0, credits=left, stopped=stopped)
    if stopped:
        log.warning("enrich: wider reads stopped, Serper balance %s", left)
    return 0 if stopped else load().wider_per_day


async def count_wider(store: Store, now: datetime) -> None:
    mark = await store.get_mark(WIDER)
    await store.set_mark(WIDER, day=budget.day_of(now), done=int(mark.get("done") or 0) + 1, credits=mark.get("credits"), stopped=False)


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
    if launch_due(d, now):                                      # never read first, then the biggest
        return (0, -2, 1 if isinstance(d.get("enriched_at"), datetime) else 0, -launches.home_count(d))
    key = _priority(d, now, shown)
    if key is None:
        return None
    # east Pune's hot projects first, with its top lists and the owner's banner picks (owner 2026-10-27: "for now just
    # concentrate on east Pune"; until then hot projects went first in every area); then nearly sold out after every other
    # project; then our areas outward from Kharadi, a hot project elsewhere waiting for its area's turn; in each, new launches
    # and hot projects first
    east_hot = int(d.get("hot_score") or 0) >= hot.HOT_MIN and pricing.area_rank(d) < len(pricing.EAST)
    hot_first = 0 if east_hot or featured(d, now, shown) else 1
    # offices and shops after the homes of their area, most seen first among themselves through `key`
    turn = 2 if not pages.homes(d) else 0 if pricing.new_or_hot(d, now) else 1
    return (hot_first, 1 if pages.nearly_sold(d) else 0, pricing.area_rank(d), turn, *key)


def launch_due(d: dict, now: datetime) -> bool:
    """A new launch anywhere in Pune (areastats.launches) not yet in search, unread or not read in LAUNCH_RETRY_DAYS. Once in
    search it goes back to the common order."""
    if not launches.fresh(d, now) or not worth_model(d) or parked(d, now) or pages.searchable(d, now):
        return False
    done = d.get("enriched_at")
    return not isinstance(done, datetime) or now - _aware(done) >= timedelta(days=LAUNCH_RETRY_DAYS)


def complete(d: dict) -> bool:
    """Every stage of the last round passed (score 4/4) and the page shows real pictures. Pictures it does not show do not count:
    with them 143 of 211 hot and Top-list projects counted as complete while 12 showed a photo, and the queue stood empty (2026-11-03)."""
    e = d.get("enrichment") or {}
    if not e or any(not ((e.get("steps") or {}).get(k) or {}).get("ok") for k in STEPS):
        return False
    return bool(d.get("cluster_primary") or pages.shown_pictures((d.get("profile") or {}).get("photos"), drawn=False))


def kept_line(d: dict) -> Optional[str]:
    """The search line a page keeps when no new one passes, unless it calls offices homes: AP4 Tech Park's "offers residential
    units" outlived its rewrite and held the page out of search."""
    line = d.get("page_summary")
    return None if not pages.homes(d) and pages.says_homes(line) else line


def worth_model(d: dict) -> bool:
    """A page a buyer can land on and search can show, of a project still some way off, offices and shops included (2026-11-08).
    Never a tower: it redirects to its group, so its text is read by nobody. Projects finishing before AI_FROM keep their page as
    it is; their facts rounds need no model."""
    return not d.get("cluster_primary") and (_day(d.get("completion_now")) or AI_FROM) >= AI_FROM


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


# fact-sheet lines about the project's surroundings, not the project: they move whenever another project of the area does
AROUND_KEYS = ("area", "ask", "builder_record")
FORECAST = re.compile(r"\b(?:will|likely|expected to|should (?:meet|finish|deliver)|on track|suggests? (?:they|it)|strong|solid|impressive|excellent)\b", re.I)
VISITED = re.compile(r"\b(?:visited|site visit|we saw|on the ground|in person|our team)\b", re.I)   # no one went: never say or suggest it


def own_facts_key(sheet: List[dict]) -> str:
    """A fingerprint of the sheet's lines about the project itself (`AROUND_KEYS` left out): what decides a rewrite."""
    lines = sorted(f"{f['key']}={f['text']}" for f in sheet if not str(f.get("key") or "").startswith(AROUND_KEYS))
    return hashlib.sha1("\n".join(lines).encode()).hexdigest()


def settled(d: dict, own: str, now: datetime) -> bool:
    """A page in search with text keeps it while its own facts stand (owner 2026-11-05, R1). A page written before the key was
    kept (`page_facts_key` missing) keeps its text too, and the key is stored, so the next change of its facts rewrites it.
    Points written by code when a draft was refused (`page_text_by` "code") are a stopgap and give way to the model's."""
    return (bool(d.get("page_text")) and d.get("page_text_by") != "code" and pages.searchable(d, now)
            and d.get("page_facts_key") in (None, own))


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


def backfill(d: dict, now: datetime, urgent: bool = False, rewrite: bool = False) -> bool:
    """A rewrite for a newer writer (BACKFILL): it goes once per BACKFILL_EVERY and only when a model has room."""
    return not urgent and not rewrite and not launch_due(d, now) and (_priority(d, now) or (0,))[0] == BACKFILL


async def next_project(store: Store, now: datetime, backfills: bool = True) -> Optional[dict]:
    """The project the facts turn takes. `backfills=False`: the best one that is not a backfill rewrite, for when the backfill
    at the head must wait (on 2026-11-08 one waiting at the head held the loop to a round every 30 minutes from 02:00 to 07:20)."""
    urgent = {r["_id"] for r in await store.db.get_collection(REQUESTS).find({}).to_list(200)}
    shown = frozenset(await _deps["shown"](store.db)) if _deps["shown"] else frozenset()
    rewrite = await rewrites_left(store, now) > 0
    room = await wider_left(store, now) > 0
    ranked = []
    for d in await store.all_projects():
        # an asked-for project is taken even outside our areas (a campaign's project with no locality): skipped, its request
        # stayed and kept the loop running every minute
        if not _ours(d) and (d.get("regno") or d["_id"]) not in urgent and not launch_due(d, now):
            if room and wider(d, now):
                ranked.append((wider_key(d), d))
            continue
        key = priority(d, urgent, now, shown, rewrite)
        if key is not None and (backfills or not backfill(d, now, (d.get("regno") or d["_id"]) in urgent, rewrite and rewrite_due(d, now))):
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
    where = area.name if area else doc.get("pune_place_name")
    rest = [o for o in others or [] if o.get("_id") != doc.get("_id") and pages.homes(o) and not o.get("cluster_primary")
            and not pages.completion_passed(o)]
    if not where or len(rest) < pages.COMPARE_MIN:
        return []
    lines = []

    def beside(what: str, mine: Optional[int], theirs: List[Optional[int]]) -> None:
        known = [n for n in theirs if n]
        if mine and len(known) >= pages.COMPARE_MIN:
            lines.append(f"Compared with other projects still being built in {where}: {what} {sum(1 for n in known if n < mine)} of {len(known)}")

    beside("its tallest building is higher than that of", _int((doc.get("building_totals") or {}).get("max_floors")),
           [_int((o.get("building_totals") or {}).get("max_floors")) for o in rest])
    if not PART_OF_PROJECT.search(str(doc.get("name") or "")) and not doc.get("cluster_id"):   # "only 4 homes" of Lodha Camelot's tower
        beside("this registration has more homes than", _int(doc.get("units_total")), [_int(o.get("units_total")) for o in rest])
    same = sum(1 for o in rest if doc.get("promoter") and o.get("promoter") == doc["promoter"])
    if same:
        lines.append(f"The same filing company has {same} other project{'s' if same > 1 else ''} still being built in {where}")
    return lines


def worth_asking(doc: dict, web: Optional[dict]) -> List[str]:
    """The questions this project's own record raises, decided by code: asked to think of some, the model wrote one line for
    every page, and told a builder with no brand to explain its brand (2026-11-04, Alfa Premio)."""
    out = []
    if pages.completion_passed(doc):
        out.append("Worth asking: the filed completion date has passed, so has the occupancy certificate been given")
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




def _numbers(text: str) -> set:
    return {n.replace(",", "") for n in NUM.findall(text)}










# a draft saying the filed date moved; "has not moved" / "not been moved" are fine. Park Eden Phase I (2026-10-25): "an
# increase from 31 Oct 2030", for MahaRERA's own extension
MOVED = re.compile(r"(?<!not )(?<!never )(?<!not been )(?<!no )\b(?:moved|pushed|postponed|delayed|revised|shifted|deferred|"
                   r"rescheduled|increased?|later than (?:the|its) (?:original|first|earlier))\b", re.I)
# "extended" is MahaRERA's own word for its order; said of the builder, or with no MahaRERA in the sentence, it is a move
EXTENDED = re.compile(r"\bextend(?:ed|s)?\b|\bextension\b", re.I)


def _sentences(text: str) -> List[str]:
    return [s for s in re.split(r"(?<=[.!?;])\s+|\n+", text) if s.strip()]


def _without_names(doc: dict, text: str) -> str:
    """The text with the project's names taken out: "Rohan Abhilasha 4" and "Park Eden Phase I" carry a number and a phase."""
    for n in sorted(pages.names(doc)[1], key=len, reverse=True):
        text = re.sub(re.escape(n), " ", text, flags=re.I)
    return text








def says_moved(text: str) -> bool:
    """The draft says the filed completion date was moved (or extended by anyone but MahaRERA)."""
    for s in _sentences(text):
        if MOVED.search(s):
            return True
        if EXTENDED.search(s) and (not re.search(r"maharera", s, re.I) or re.search(r"\b(?:builder|developer|promoter)\b", s, re.I)):
            return True
    return False








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






async def sources_text(db, doc: dict) -> str:
    """The fact sheet the page was written from, for reading the finished page against it (seo.review)."""
    sheet = (doc.get("fact_sheet") or {}).get("facts")
    if not sheet:   # a page last written before the sheet was kept
        view = _deps.get("view")
        sheet = fact_sheet(doc, await view(db, doc["_id"]) if view else None, doc.get("web_facts"), doc.get("profile"),
                           (doc.get("geo") or {}).get("located_from") == "google")
    return "\n".join(f["text"] for f in sheet)




# ---- the fact sheet and the points (owner 2026-11-04: "facts needs to be stored, out of the facts we create the page") ---------

def _money(n: int) -> str:
    return f"₹{n / 10000000:.2f} Cr".replace(".00 Cr", " Cr") if n >= 10000000 else f"₹{round(n / 100000)} L"


def size_kind(quote: str) -> str:
    """What kind of area a price line gives: sites mix them, and saleable area runs 30-40% over carpet (owner 2026-11-03), so a
    size is never said without it and two sizes of different kinds are never compared."""
    if re.search(r"carpet|rera area", quote, re.I):
        return "carpet area"
    if re.search(r"saleable|sellable|built[- ]?up|super", quote, re.I):
        return "saleable area"
    return "area kind not stated"


def home_sizes(outside: List[Tuple[str, str]], web: Optional[dict]) -> List[dict]:
    """Each kind of home's size from the pages read for this project: [{bhk, low, high, kind, official, one_site, sites, url, quote}].
    The builder's site or two sites within webfacts.TOLERANCE of each other; else one site, said to be one (owner 2026-11-05), which
    two sites disagreeing never is. Only pages the reading took as about this project count."""
    read = {r.get("site"): r for r in (web or {}).get("read") or [] if r.get("official") or re.match(r"\d+ facts", str(r.get("why") or ""))}
    by_kind: Dict[str, List[dict]] = {}
    for site, text in outside:
        if site in read:
            for bhk, s in prices.sizes_on(text).items():
                by_kind.setdefault(bhk, []).append({**s, "site": site, "official": bool(read[site].get("official")), "url": read[site].get("url")})
    out = []
    for bhk, seen in sorted(by_kind.items()):
        mine = [s for s in seen if s["official"]]
        agreed = [s for s in seen if any(o is not s and abs(o["low"] - s["low"]) <= webfacts.TOLERANCE * s["low"] for o in seen)]
        use = mine or agreed or (seen if len(seen) == 1 else [])
        if use:
            s = use[0]
            out.append({"bhk": bhk, "low": s["low"], "high": s["high"], "kind": s["kind"], "official": bool(mine),
                        "one_site": not mine and not agreed,
                        "sites": [x["site"] for x in use], "url": s["url"], "quote": s["quote"]})
    return out


def homes_per_acre(doc: dict, land: Optional[dict], scoped: dict) -> Optional[int]:
    """Homes per acre, only when the homes and the land surely cover the same ground: land is mostly given for the whole marketed
    project and homes for one registration, so a phase, a tower, a group of registrations or a scoped count says nothing."""
    total, acres = _int(doc.get("units_total")), webfacts.number((land or {}).get("value"))
    if not total or not acres or scoped or doc.get("cluster_id") or re.search(r"\b(?:phase|part|tower|wing|building|bldg)\b", str(doc.get("name") or ""), re.I):
        return None
    return round(total / acres)


def whole_project_homes(doc: dict, docs: List[dict]) -> Optional[str]:
    """The homes and bookings of every registration of the project the page stands for (towers, phases), when there are several:
    homes summed over the registrations that report a count (a 0 is one that has not yet), bookings over those that report both,
    so the booked share compares the same registrations. None for a project registered once."""
    rows = pages.towers(doc, docs)
    if len(rows) < 2:
        return None
    counted = [t for t in rows if (t.get("units_total") or 0) > 0]
    both = [t for t in counted if t.get("units_booked") is not None and t["units_booked"] <= t["units_total"]]
    if not both:
        return None
    total, sold = sum(t["units_total"] for t in both), sum(t["units_booked"] for t in both)
    scope = (f"all {len(rows)} MahaRERA registrations" if len(both) == len(rows)
             else f"{len(both)} of the {len(rows)} MahaRERA registrations")
    return f"Homes across {scope} of the project: {total}, {sold} of {total} booked ({round(100 * sold / total)}%)"


def fact_sheet(doc: dict, gathered: Optional[dict], web: Optional[dict], prof: Optional[dict], pinned: bool,
               others: Optional[List[dict]] = None, docs: Optional[List[dict]] = None, now: Optional[datetime] = None) -> List[dict]:
    """Every fact the page may say, one per line: {key, text, source, url, quote}. Worked out by code from the record, the checked
    web facts, highlights and prices. Stored on the record as `fact_sheet`; the writer sees only this, and each point it writes
    names the keys it used, so a point can be traced to its source and checked by code. MahaRERA's readings stay as they are:
    this is a view of them for the page, never where a history is kept."""
    out: List[dict] = []
    area = BY_KEY.get(doc.get("locality") or "")
    place = area.name if area else doc.get("pune_place_name") or None
    read = "MahaRERA"

    def add(key: str, text: str, source: str = read, url: Optional[str] = None, quote: Optional[str] = None) -> None:
        out.append({"key": key, "text": text, "source": source, "url": url or (doc.get("source_url") if source == read else None), "quote": quote})

    b = brands.of(doc)
    if b and doc.get("promoter"):
        add("brand", f"Sold under the brand {b.name}; the company filed with MahaRERA is {doc['promoter']}")
    filed, first = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))
    if filed:
        add("filed", f"Completion date filed with MahaRERA: {pages._long(filed)}")
    if first and first != filed:
        add("first", f"Completion date filed at registration: {pages._long(first)}")
        if pages.extension_months(doc) and pages.months_later(doc) == 0:
            add("extension", f"{pages.EXTENSION_NOTE}: that is the whole difference between the two dates; the builder did not move it")
    total, sold = _int(doc.get("units_total")), pages.booked(doc)
    housing = pages.homes(doc)
    unit = "Homes" if housing else "Shop and office units"
    if total:
        whole = PART_OF_PROJECT.search(str(doc.get("name") or "")) or doc.get("cluster_id")
        add("homes", f"{unit} in this registration: {total}" + (" (one part of a bigger project, not the whole project)" if whole else ""))
    if total and sold is not None and sold <= total:
        # scoped like the line above: the model read a part's bare "booked: 0 of 168" as the whole project's (Venkatesh Vanaya,
        # 7 registrations and 745 homes, opened "Zero of 168 homes booked", 2026-11-12)
        add("booked", f"{unit} booked{' in this registration' if whole else ''}: {sold} of {total} ({round(100 * sold / total)}%)")
    project = whole_project_homes(doc, docs) if docs else None
    if project:
        add("project_homes", project.replace("Homes", unit, 1))
    t = doc.get("building_totals") or {}
    if t.get("towers"):
        add("buildings", f"Buildings in this registration: {t['towers']}" + (f", up to {t['max_floors']} floors" if t.get("max_floors") else ""))
    for i, line in enumerate(worked_out(doc)):
        add(f"worked{i}", line.replace("Worked out: ", "").replace(" homes ", " homes " if housing else " units "), "worked out from MahaRERA")
    rest = [o for o in others or [] if o.get("_id") != doc.get("_id") and not o.get("cluster_primary")]
    # an area's booked share and sizes are about homes, so offices and shops are not set beside them
    compare = pages.area_compare(doc, rest, place, (now or datetime.now(timezone.utc)).date()) if place and housing else None
    if compare and compare.get("booked"):
        c = compare["booked"]
        add("area_booked", f"{c['pct']}% booked here; the middle of {c['projects']} {place} projects registered within a year of it is {c['area_pct']}%", "worked out from MahaRERA")
    for i, line in enumerate(area_context(doc, others) if housing else []):
        add(f"area{i}", line, "worked out from MahaRERA")
    record = pages.track_record(doc, docs) if docs else None
    if record and record.get("record_ok"):
        add("builder_record", f"Of {record['with_dates']} {record['name']} projects in Pune with both dates on MahaRERA, {record['moved_later'] or 'none'} moved the completion date 3 months or more later", "worked out from MahaRERA")
    scoped = {f["key"]: mine for f, mine in whole_project_counts(doc, web)}
    for f, line in zip((web or {}).get("facts") or [], webfacts.lines(web)):
        src = (f.get("sources") or [{}])[0]
        add(f"web_{f.get('key')}", f"{f['label']}: {f['text']} for the whole project; this registration has {scoped[f['key']]}" if f.get("key") in scoped else line,
            ", ".join(s["site"] for s in f.get("sources") or []), src.get("url"), src.get("quote"))
    land = next((f for f in (web or {}).get("facts") or [] if f.get("key") == "land_acres"), None)
    per_acre = homes_per_acre(doc, land, scoped) if housing else None
    if per_acre:
        add("homes_per_acre", f"About {per_acre} homes per acre", "worked out from MahaRERA and the land size")
    for i, (h, line) in enumerate(zip(profile.shown_highlights(prof, doc), profile.lines(prof, doc))):
        src = (h.get("sources") or [{}])[0]
        add(f"highlight{i}", line, ", ".join(s["site"] for s in h.get("sources") or []), src.get("url"), src.get("quote"))
    sized = {x["bhk"] for x in doc.get("home_sizes") or []}
    for x in (doc.get("home_sizes") or []) if housing else []:   # flat sizes and prices read under a shared name are not this project's
        span = f"{x['low']} to {x['high']} sq ft" if x["high"] != x["low"] else f"{x['low']} sq ft"
        add(f"size_{x['bhk'].replace(' ', '')}", f"{x['bhk']} size: {span}, {x['kind']}" + (", on one property site" if x.get("one_site") else ""),
            ", ".join(x["sites"]), x.get("url"), x.get("quote"))
    for r in ((doc.get("prices") or {}).get("rows") or []) if housing else []:
        if isinstance(r, dict) and isinstance(r.get("from_inr"), int) and r.get("bhk"):
            src = (r.get("sources") or [{}])[0]
            where = ", ".join(s["site"] for s in r.get("sources") or [])
            add(f"price_{str(r['bhk']).replace(' ', '')}", f"{r['bhk']} from {_money(r['from_inr'])}", where, src.get("url"), src.get("quote"))
            quote = str(src.get("quote") or "")
            sqft = prices.sqft_of(r, quote)
            if sqft and r["bhk"] not in sized:
                add(f"size_{str(r['bhk']).replace(' ', '')}", f"{r['bhk']} size from {sqft} sq ft, {size_kind(quote)}", where, src.get("url"), quote)
    if pinned:
        for i, x in enumerate(((gathered or {}).get("nearby") or [])[:10]):
            if x.get("name") and isinstance(x.get("km"), (int, float)):
                add(f"near{i}", f"{str(x.get('label') or 'place').capitalize()}: {x['name']}, {x['km']} km in a straight line", "Google Maps")
    for i, line in enumerate(worth_asking(doc, web)):
        add(f"ask{i}", line.replace("Worth asking: ", ""), "worked out from MahaRERA")
    return out


POINTS_SYSTEM = ("You help home buyers in Pune. From the FACTS about one housing project, pick the 3 to 5 that matter most to someone "
                 "choosing a home here, and say each as one short point. Fewer is right when few facts matter; never pad. Think like a "
                 "local researcher telling a friend what stands out: what is unusual about this project against its area, what is good "
                 "and what should worry a buyer, said straight. Lead with what makes this project different; leave out what would be "
                 "true of any project. Each point has a label of 2 to 6 plain words that says this project's finding with its number "
                 "when it has one (\"Only 4% of homes booked\", \"Taller than 80 of 83 projects\"; not \"Bookings\", not \"Taller than "
                 "most neighbors\"), and text of one or two short sentences. Never call a project small when the facts say this is one "
                 "part of a bigger project. No superlatives such as largest or tallest; say the count. Never say average; say \"similar "
                 "projects are at about 83%\". Use only the facts given, each number exactly as "
                 "given, and name in `facts` the keys of the lines you used. Plain English, your own words; do not copy a fact's line. "
                 "Write whole sentences, not notes. Say what a middle figure means simply: \"similar projects are at about 53%\". Keep each date with its label. When a line "
                 "says MahaRERA's order is the only change to the date, say MahaRERA's order added the months, and never that the date "
                 "moved or was extended or pushed back. A line "
                 "that starts with a question to ask may be used as a point, in your own words; put no other question. No praise, no "
                 "sales words, no advice to buy or not to buy. Never use: furthermore, moreover, additionally, notably, overall, nestled, "
                 "boasts, vibrant, seamless, ideal, convenient, proximity, ensures, caters to, designed to, making it, serves as, stands "
                 "as, residents can, potential buyers, consists of, boutique, footprint, solitary, venture, parcel, residences, or a dash "
                 "in place of a comma. "
                 f"search_summary: one line under {MAX_SUMMARY} characters for search results, naming the project and its area. "
                 'Answer as JSON: {"points": [{"label": "...", "text": "...", "facts": ["key"]}], "search_summary": "..."}')


def code_points(doc: dict, sheet: List[dict]) -> Optional[dict]:
    """Points written by code from the sheet, for a page with facts whose model answer did not pass and which has no text: a page
    must not leave search because a draft failed (2026-11-05: 14 pages did). Plain, and a newer round replaces them."""
    by_key = {f["key"]: f["text"] for f in sheet}
    points: List[dict] = []

    def point(label: str, text: str, key: str) -> None:
        points.append({"heading": label, "text": text + ".", "facts": [key]})

    word = "homes" if pages.homes(doc) else "units"
    whole = re.match(r"(?:Homes|Shop and office units) across (.+?) of the project: (\d+), (\d+) of (\d+) booked \((\d+)%\)",
                     by_key.get("project_homes", ""))
    m = re.match(r"(?:Homes|Shop and office units) booked(?: in this registration)?: (\d+) of (\d+) \((\d+)%\)", by_key.get("booked", ""))
    if whole:   # a project in several registrations: its own count, never one part's
        point(f"{whole.group(5)}% of {word} booked", f"MahaRERA shows {whole.group(3)} of {whole.group(4)} {word} booked across {whole.group(1)}",
              "project_homes")
    elif m:
        point(f"{m.group(3)}% of {word} booked", f"MahaRERA shows {m.group(1)} of {m.group(2)} {word} booked", "booked")
    if "buildings" in by_key:
        point(by_key["buildings"].split(":", 1)[1].strip().capitalize() + " floors" if "floors" not in by_key["buildings"] else by_key["buildings"].split(":", 1)[1].strip().capitalize(), by_key["buildings"], "buildings")
    for key in by_key:
        if len(points) < MAX_POINTS - 1 and key.startswith(("price_", "size_", "web_", "highlight", "area")):
            line = by_key[key].split(" (from ")[0]
            point(line.split(":")[0][:60], line, key)
    if "filed" in by_key:
        point(by_key["filed"].split(": ", 1)[1] + " filed completion", by_key["filed"], "filed")
    if len(points) < MIN_POINTS:
        return None
    points = points[:MAX_POINTS]
    return {"text": "\n\n".join(f"{x['heading']}: {x['text']}" for x in points), "sections": points, "summary": None}


def points_of(out: Any, sheet: List[dict], doc: dict, web: Optional[dict], outside: Optional[List[Tuple[str, str]]] = None) -> Tuple[List[dict], List[str]]:
    """(points kept as {heading, text, facts}, why the others went). A point goes when it names no fact we hold, says a number its
    facts do not, or carries stock words, a question its facts do not raise or another site's words. The sheet's lines are ours
    to say, so lifting from them is not checked; the writer is told to use its own words and the outside pages are what count."""
    by_key = {f["key"]: f["text"] for f in sheet}
    names = pages.names(doc)[0]
    kept, why = [], []
    raw = out.get("points") if isinstance(out, dict) else None
    for p in raw if isinstance(raw, list) else []:
        if not isinstance(p, dict):
            continue
        label, text = (" ".join(str(p.get(k) or "").replace("‑", "-").split()) for k in ("label", "text"))
        used = [k for k in p.get("facts") or [] if k in by_key] if isinstance(p.get("facts"), list) else []
        said = label + ". " + text
        known = _numbers(" ".join(by_key[k] for k in used) + " " + names)
        # a number on another line of the sheet is still ours: the model named the wrong line, and that cost whole pages their text
        # ("Taller than 25 of 83 projects: a number its facts do not say (6)", the 6 floors being on the buildings line)
        for k, line in by_key.items():
            if used and k not in used and (_numbers(_without_names(doc, said)) - known) & _numbers(line):
                used.append(k)
                known |= _numbers(line)
        problem = ("no fact named" if not used else "empty" if not label or not text
                   else "calls offices or shops homes" if not pages.homes(doc) and pages.says_homes(said)
                   else "says the date moved" if pages.extension_months(doc) and pages.months_later(doc) == 0 and says_moved(said)
                   else f"a number its facts do not say ({', '.join(sorted(_numbers(_without_names(doc, said)) - known)[:3])})" if _numbers(_without_names(doc, said)) - known
                   else "sales words" if BANNED.search(said) else "overclaims" if OVERCLAIM.search(said)
                   else "stock words" if STOCK.search(said) or AI_WORDS.search(said)
                   else "a question its facts do not raise" if ASKS.search(said) and not any(k.startswith("ask") for k in used)
                   else "too long" if len(text) > MAX_POINT else None)
        for site, page in outside or []:
            if not problem and lifted(doc, said, page):
                problem = f"copies {site}"
        if problem:
            why.append(f"{label or 'a point'}: {problem}")
        elif len(kept) < MAX_POINTS and label.lower() not in {x["heading"].lower() for x in kept}:
            kept.append({"heading": label, "text": text, "facts": used})
    return kept, why


async def write_points(llm, doc: dict, sheet: List[dict], web: Optional[dict] = None, others: Optional[List[dict]] = None,
                       outside: Optional[List[Tuple[str, str]]] = None) -> tuple:
    """({text, sections, summary} or None, why it was refused): the last step of a round. The points are kept in `page_sections` as
    {heading, text, facts}, so the page check, chat's knowledge and search read them as they read the sections before."""
    if llm is None:
        return None, ["no LLM key"]
    user = "FACTS:\n" + "\n".join(f"[{f['key']}] {f['text']}" for f in sheet)
    if not pages.homes(doc):
        user += "\n\nThis project is shops or offices. Say units, shops or offices; never homes, flats, apartments, BHK or residents."
    problems: List[str] = []
    used_labels = Counter(x.get("heading", "").lower() for o in others or [] if o.get("_id") != doc.get("_id") and int(o.get("page_text_version") or 1) >= 6
                          for x in o.get("page_sections") or [])
    for ask in (user, None):
        ask = ask or f"{user}\n\nYour last answer was refused: {'; '.join(problems)}. Write it again without that."
        try:
            out = await llm.json(POINTS_SYSTEM, ask)
        except Exception as e:
            log.exception("enrich: model call failed for %s", doc.get("_id"))
            return None, problems or [f"model call failed ({type(e).__name__})"]
        if out is None:
            return None, problems or ["no model answer"]
        points, dropped = points_of(out, sheet, doc, web, outside)
        body = "\n\n".join(f"{x['heading']}: {x['text']}" for x in points)
        problems = [] if len(points) >= MIN_POINTS else [f"only {len(points)} points kept"] + dropped
        twin = alike(doc, body, others or [])
        if twin:
            problems.append(f"reads like the page of {twin}")
        problems += [f'the label "{x["heading"]}" is on other pages: say this project\'s number' for x in points if used_labels.get(x["heading"].lower(), 0) >= LABEL_REPEATS]
        if ask is None or ask != user:   # the second answer: a repeated label costs the point, not the page
            points = [x for x in points if used_labels.get(x["heading"].lower(), 0) < LABEL_REPEATS]
            body = "\n\n".join(f"{x['heading']}: {x['text']}" for x in points)
            problems = [p for p in problems if "is on other pages" not in p] + ([] if len(points) >= MIN_POINTS else [f"only {len(points)} points kept"])
        if not problems:
            summary = " ".join(str(out.get("search_summary") or "").split())
            good = 40 <= len(summary) <= MAX_SUMMARY and websearch_mentions(pages.names(doc)[0], summary) and not AI_WORDS.search(summary)
            return {"text": body, "sections": points, "summary": summary if good else None}, []
        log.info("enrich: points for %s refused: %s", doc.get("_id"), "; ".join(problems))
        if hasattr(llm, "forget"):
            try:
                await llm.forget(POINTS_SYSTEM, ask)
            except Exception:
                log.exception("enrich: forgetting a refused answer failed for %s", doc.get("_id"))
    return None, problems


# ---- Avasetu's read: the facts taken together (owner 2026-11-05: a line that reads as someone looked, with no site visits) ---------

READ_SIGNALS = ("read_pace", "read_moves", "area_booked", "builder_record")
READ_KEYS = READ_SIGNALS + ("booked", "filed")
READ_MIN_SIGNALS = 2                  # one signal is a fact the page already shows, not a reading of it
MAX_READ = 480                        # characters
READ_SYSTEM = ("You help home buyers in Pune. From the FACTS about one housing project, write 2 or 3 short plain sentences saying what "
               "they mean taken together, under 350 characters: is it selling well or slowly against similar projects, is the builder's date record good "
               "or poor, is anything worrying. Say it straight, as a friend who read the record would, and say the bad as plainly as "
               "the good. Use only these facts, each number exactly as given. Never say or suggest that anyone visited the site. "
               "Never predict: say what the record shows, not what will happen, and never that a date will be met. No praise words "
               "such as strong or solid: give the count and let it speak. No advice to buy or not to buy; you may say what to ask "
               "the builder when a fact is worrying. Never use: "
               "furthermore, moreover, additionally, notably, overall, best, largest, tallest, average, ideal, convenient, or a dash "
               "in place of a comma. Keep each date with its label. "
               'Answer as JSON: {"read": "...", "facts": ["key"]}')


def this_project(text: str) -> str:
    """The sentences not about the builder's other projects: "8 of its 59 projects moved their dates" is no word on this one's."""
    return " ".join(x for x in re.split(r"(?<=[.!?])\s+", text) if not re.search(r"\bprojects\b", x, re.I))


def plain_middle(text: str) -> str:
    """The sheet's "the middle of 13 Kharadi projects registered within a year of it is 86%" as a reader says it: a model copies the
    words it is given, and `OVERCLAIM` then refuses them (11 of the first 12 reads, 2026-11-05)."""
    return re.sub(r"the middle of (\d+) (.+?) projects registered within a year of it is (\d+%)", r"\1 similar \2 projects are at about \3", text)


def read_lines(doc: dict, sheet: List[dict]) -> List[dict]:
    """The facts Avasetu's read may use: the sheet's own on bookings, dates and the builder, and what only our dated readings show,
    which is how fast homes are going and how often the date moved. MahaRERA shows neither."""
    lines = [dict(f, text=plain_middle(f["text"])) for f in sheet if f.get("key") in READ_KEYS]
    seen = pagefacts.booked_readings(doc)
    if len(seen) >= 2 and seen[-1]["booked"] >= seen[0]["booked"]:
        gained = seen[-1]["booked"] - seen[0]["booked"]
        lines.append({"key": "read_pace", "text": f"{gained} more homes booked between {pages._long(seen[0]['on'])} and {pages._long(seen[-1]['on'])}"})
    moved = [m for m in pages.completion_moves(doc) if not m.get("blanket")]
    if moved:
        lines.append({"key": "read_moves", "text": f"The builder has moved the filed completion date {len(moved)} time{'s' if len(moved) > 1 else ''} since we began reading it"})
    return lines


async def buyer_read(store: Store, doc: dict, llm, now: datetime) -> Optional[dict]:
    """Writes `page_read` {text, facts, on, key} from the stored sheet when there is enough to read and it has changed; None when not.
    No fallback: with no good answer the page shows no read. Its own text, so the page's points and date stay as they are."""
    lines = read_lines(doc, (doc.get("fact_sheet") or {}).get("facts") or [])
    if llm is None or sum(1 for f in lines if f["key"] in READ_SIGNALS) < READ_MIN_SIGNALS:
        return None
    key = own_facts_key(lines)
    if (doc.get("page_read") or {}).get("key") == key:
        return None
    user = "FACTS:\n" + "\n".join(f"[{f['key']}] {f['text']}" for f in lines)
    try:
        out = await llm.json(READ_SYSTEM, user)
    except Exception:
        log.exception("enrich: read failed for %s", doc.get("_id"))
        return None
    text = " ".join(str((out or {}).get("read") or "").split())
    by_key = {f["key"]: f["text"] for f in lines}
    used = [k for k in (out or {}).get("facts") or [] if k in by_key] if isinstance((out or {}).get("facts"), list) else []
    known = _numbers(" ".join(by_key[k] for k in used) + " " + pages.names(doc)[0])
    bad = (not used or not 60 <= len(text) <= MAX_READ or _numbers(_without_names(doc, text)) - known or BANNED.search(text) or OVERCLAIM.search(text)
           or AI_WORDS.search(text) or STOCK.search(text) or VISITED.search(text) or FORECAST.search(text)
           or pages.extension_months(doc) and pages.months_later(doc) == 0 and says_moved(this_project(text)))
    if bad:
        log.info("enrich: read for %s refused", doc.get("_id"))
        if hasattr(llm, "forget"):
            await llm.forget(READ_SYSTEM, user)
        return None
    read = {"text": text, "facts": used, "on": _day(doc.get("details_checked_at")) or now.date().isoformat(), "key": key}
    await store.set_project(doc["_id"], page_read=read)
    return read


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


def area_pincode(doc: dict) -> Optional[str]:
    """A pincode of the project's area, for a record MahaRERA filed without one (Godrej Ivara): the place check needs a centre to
    measure from, and the area's is good enough for a check NEAR_KM wide."""
    locality = doc.get("locality")
    if locality == "upper_kharadi":
        return UPPER_KHARADI_PINCODES[0]
    return next((pin for pin, area in AREA_PINCODES.items() if area == locality), None) or next(
        (pin for pin, areas in SHARED_PINCODES.items() if locality in areas), None)


async def check_places(store: Store, doc: dict, sheet: Optional[dict], located_from: str, now: datetime) -> tuple:
    """(step, register fields): where the gathered sheet put the project, checked against the pincode's centre."""
    lat, lon = sheet_value(sheet, "lat"), sheet_value(sheet, "lon")
    if sheet_value(sheet, "located_at") == "project":
        located_from = "google"                                    # the project's own pin (propertyfacts.pin)
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return _step(False, now, located_from=located_from or None, checked="no position found"), {}
    fields = {"geo": {"lat": float(lat), "lon": float(lon), "located_from": located_from}}
    pin, centre = doc.get("pincode") or area_pincode(doc), None
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
                general = {**general, **readings.booked(doc, general, now), **readings.details_changed(doc, general, now)}
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
    fetch = webfacts.memo(webfacts.read_page)   # the web facts and the profile read the same pages: each once
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
    draft, text, turned_down, own_key, by = None, None, False, None, None
    # sizes come from the pages just read, by code, before the writer decides whether it has anything to say
    web_now = (web or {}).get("web_facts") or doc.get("web_facts")
    outside = await outside_pages(web_now, fetch) if spends else []
    sizes = home_sizes(outside, web_now)
    if sizes:
        await store.set_project(doc["_id"], home_sizes=sizes)
    # the writer is the last step: only with every read done, and something of the project's own to write from
    writable = urgent or pages.own_facts(await store.project(doc["_id"]) or doc)
    if not spends or reading and not put_off and not writable or reading and not urgent and not rewrite and keeps_text(doc, now):
        steps["text"] = kept_steps.get("text") or {}
        if spends and not writable:
            notes.append("no text written: no fact of its own yet")
    elif reading and not put_off:
        ask = _ask(llm, tier, "text")
        before = _deferred(ask)
        area_docs = (await store.projects_in([doc["locality"]]) if doc.get("locality")
                     else await store.projects_at(doc["pune_place"]) if doc.get("pune_place") else [])
        latest = await store.project(doc["_id"]) or doc
        sheet = fact_sheet(latest, gathered, web_now, (prof or {}).get("profile") or latest.get("profile"), pinned, area_docs,
                           await store.shared_projects(), now)
        own_key = own_facts_key(sheet)
        keep = settled(latest, own_key, now)
        if keep:   # the stored sheet stays the one the text was written from
            notes.append("text kept: in search and its own facts have not changed")
            if not latest.get("page_facts_key"):
                await store.set_project(doc["_id"], page_facts_key=own_key)
        else:
            await store.set_project(doc["_id"], fact_sheet={"at": now, "facts": sheet})
            draft, refused = await write_points(ask, latest, sheet, web_now, area_docs, outside)
        if keep:
            steps["text"] = kept_steps.get("text") or {}
        elif _deferred(ask) > before:
            put_off.append("text")
            steps["text"] = kept_steps.get("text") or {}
        else:
            by = "model"
            if draft is None and not latest.get("page_text"):
                draft, by = code_points(latest, sheet), "code"
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
        fields.update(page_text=text, page_text_version=TEXT_VERSION, page_sections=draft["sections"], page_facts_key=own_key,
                      page_text_by=by, page_summary=draft["summary"] or kept_line(doc))
        if text != doc.get("page_text") or draft["summary"] != doc.get("page_summary"):
            fields["page_text_at"] = now   # the page's date moves only when what a reader sees changed
    elif ("text" in ran and doc.get("page_text") and int(doc.get("page_text_version") or 1) < 6
          and not websearch_mentions(pages.names(doc)[0], doc["page_text"])):   # points need not repeat the name the page opens with
        # a kept text that does not name the project (a model's misspelling) gives way to the code-written paragraph
        fields.update(page_text=None, page_sections=None, page_summary=None)
        notes.append("old text dropped: it does not name the project")
    await store.set_project(doc["_id"], **fields)
    after = await store.project(doc["_id"])
    state = pages.search_state(after, now) if after else None
    if state:
        await store.set_project(doc["_id"], search_state=state)
    if rewrite and text:
        await count_rewrite(store, now)
    if reading and spends and not put_off and after:
        await buyer_read(store, after, _ask(llm, tier, "text"), now)
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


async def step(store: Store, llm, now: datetime, last_regular: Optional[datetime], every: timedelta,
               last_backfill: Optional[datetime] = None) -> Optional[dict]:
    """The facts turn: urgent requests always; otherwise one project when `every` has passed since the last regular one. Its
    reading runs in the same round when a model may be asked, else it is put off (read_step takes it later). A backfill rewrite
    keeps its own clock (`last_backfill`): while it waits, the next project that is not one goes."""
    urgent = await store.db.get_collection(REQUESTS).count_documents({})
    if not urgent and last_regular is not None and now - _aware(last_regular) < every:
        return None
    doc = await next_project(store, now)
    if doc is None:
        return None
    reread, is_backfill = True, False
    is_urgent = bool(urgent) and (doc.get("regno") or doc["_id"]) in await _urgent(store)
    rewrite = not is_urgent and rewrite_due(doc, now) and await rewrites_left(store, now) > 0
    if rewrite:                                                 # the writer alone when what the sites say is recent
        reread = not sources_fresh(doc, now) or bool(outdated(doc))
    elif backfill(doc, now, is_urgent):                         # the group of the key before the area and launch order
        reread = not sources_fresh(doc, now) or bool(outdated(doc))
        is_backfill = True
        if reread and last_backfill is not None and now - _aware(last_backfill) < BACKFILL_EVERY:
            wait = "its turn is every %d minutes" % (BACKFILL_EVERY.total_seconds() // 60)
        elif not can_read(llm, tier_of(doc)) or busy(llm):      # a rewrite is reading only: it waits for a model with room
            wait = "no model has room"
        else:
            wait = ""
        if wait:
            log.info("enrich: rewrite for %s waits (%s); the next project goes", doc.get("_id"), wait)
            doc = await next_project(store, now, backfills=False)
            if doc is None:
                return None
            reread, is_backfill = True, False
            is_urgent = bool(urgent) and (doc.get("regno") or doc["_id"]) in await _urgent(store)
            rewrite = not is_urgent and rewrite_due(doc, now) and await rewrites_left(store, now) > 0
            if rewrite:
                reread = not sources_fresh(doc, now) or bool(outdated(doc))
    if not is_urgent and wider(doc, now) and not launch_due(doc, now):
        await count_wider(store, now)
    try:
        out = await asyncio.wait_for(enrich_one(store, doc, llm, now, reread=reread, urgent=is_urgent, rewrite=rewrite), ROUND_SECONDS)
    except asyncio.CancelledError:
        raise
    except Exception as e:   # noted on the record and the next project goes on; the request does not keep the loop busy
        out = await failed_round(store, doc, now, e)
    out["urgent"] = bool(urgent)
    out["backfill"] = is_backfill
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
    ranked = sorted(((k, d) for d in await store.all_projects()
                     if (_ours(d) or launches.fresh(d, now)) and (k := reading_key(d, now)) is not None),
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
    last_backfill: Optional[datetime] = None
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
                    out = await step(Store(get_database()), llm, now, last_regular, cfg.every, last_backfill)
                    if out:   # enrich_one logged it (pipeline=enrich)
                        if not out["urgent"]:
                            last_regular = now
                        if out.get("backfill"):
                            last_backfill = now
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
