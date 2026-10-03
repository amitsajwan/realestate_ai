"""MahaRERA projects listed or updated recently (Pune district).

Reads the public search page https://www.maharera.maharashtra.gov.in/projects-search-result (no login, no captcha).
Results are paged 10 per page in ascending registration order, so the newest projects sit on the LAST pages.
We fetch page 0 only to learn the total count, then read the last `pages` pages. Anything unexpected gives [].
The site often answers "No Records Found" for a page that has results (about a third of requests, verified 2026-10-02), so an
empty page is asked for again, up to `TRIES` times, before it is given up.
See docs/handoff/N1a-sources.md for the verified limits.
The only date a card gives is "Last Modified", so an item never claims the project is newly registered: it was listed or updated.
"""
import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from app.modules.newsroom.policy import MAHARERA_PAGES, MAHARERA_PHRASE
from app.modules.newsroom.sources._util import canonical_url, item_id, now_utc, strip_html
from app.modules.newsroom.types import Fetcher, MahaReraProject, RawItem

log = logging.getLogger(__name__)

SEARCH = ("https://www.maharera.maharashtra.gov.in/projects-search-result?project_name=&project_location="
          "&project_completion_date=&project_state=27&project_district={district}&carpetAreas=&completionPercentages="
          "&project_division=&page={page}&op=")
PUNE_DISTRICT = 521  # value of the site's district filter for Pune (verified 2026-09-30)
PAGE_SIZE = 10
TRIES = 3
RETRY_DELAY = 2.0  # seconds, grows per try; tests set it to 0
# the site's failures come in bursts of several seconds (verified live 2026-10-03: pages 1291 and 1290, where the newest
# in-area projects were, failed all 3 quick tries), so pages still missing after the pass are asked again after a pause
LATE_ROUNDS = 2
LATE_PAUSE = 20.0  # seconds before each late round; tests set it to 0
DETAIL = "https://maharerait.maharashtra.gov.in/public/project/view/"

_TOTAL = re.compile(r'Showing Final\s*<span[^>]*>\s*(\d+)\s*</span>', re.I)
_CARD = re.compile(r'<div class="row shadow[^"]*">(.*?)(?=<div class="row shadow|\Z)', re.S)
_REGNO = re.compile(r'<p class="p-0">\s*#\s*([A-Z0-9]+)\s*</p>')
_NAME = re.compile(r'<h4 class="title4"><strong>(.*?)</strong></h4>', re.S)
_PROMOTER = re.compile(r'<p class="darkBlue bold\s*">(.*?)</p>', re.S)
_LOCATION = re.compile(r'fa-location-dot"></em>(.*?)</a>', re.S)
_DETAIL = re.compile(r'href="(?:https?://[^"/]*)?/public/project/view/(\d+)"')
# organisation markers: individuals may be promoters and are personal data, so only companies and societies are named
_ORG = re.compile(r"\b(ltd|limited|llp|pvt|private|builders?|developers?|constructions?|realty|realtors?|infra\w*|"
                  r"properties|housing|society|associates|enterprises|group|corporation|trust|co-?op\w*)\b", re.I)


def _field(label: str, card: str) -> str:
    m = re.search(r'<div class="greyColor">\s*' + label + r'\s*</div>\s*<p>(.*?)</p>', card, re.S)
    return strip_html(m.group(1)) if m else ""


def parse_total(page: str) -> Optional[int]:
    m = _TOTAL.search(page or "")
    return int(m.group(1)) if m else None


def parse_projects(page: str) -> List[MahaReraProject]:
    """The cards of one results page as fields. A promoter is kept only when it is an organisation."""
    out: List[MahaReraProject] = []
    for card in _CARD.findall(page or ""):
        try:
            reg = _REGNO.search(card)
            name = _NAME.search(card)
            if not reg or not name or not strip_html(name.group(1)):
                continue
            loc = _LOCATION.search(card)
            prom = _PROMOTER.search(card)
            promoter = strip_html(prom.group(1)) if prom else ""
            det = _DETAIL.search(card)
            modified = _field("Last Modified", card)
            out.append(MahaReraProject(
                regno=reg.group(1), name=strip_html(name.group(1)),
                promoter=promoter if promoter and _ORG.search(promoter) else "",
                location=strip_html(loc.group(1)) if loc else "", district=_field("District", card),
                pincode=_field("Pincode", card), last_modified=modified if re.fullmatch(r"\d{4}-\d{2}-\d{2}", modified) else "",
                url=canonical_url(DETAIL + det.group(1) if det else
                                  f"https://www.maharera.maharashtra.gov.in/projects-search-result?regno={reg.group(1)}")))
        except Exception:
            continue
    return out


def to_item(p: MahaReraProject, fetched_at: Optional[datetime] = None) -> RawItem:
    published = datetime.strptime(p.last_modified, "%Y-%m-%d").replace(tzinfo=timezone.utc) if p.last_modified else None
    where = ", ".join(x for x in (p.location, f"{p.district} district" if p.district else "") if x)
    parts = [f"Project {p.name} (MahaRERA registration number {p.regno}) was {MAHARERA_PHRASE}."]
    if where:
        parts.append(f"Location: {where}" + (f", pincode {p.pincode}." if p.pincode else "."))
    if p.promoter:
        parts.append(f"Promoter: {p.promoter}.")
    if p.last_modified:
        parts.append(f"MahaRERA record last modified {p.last_modified}.")
    return RawItem(
        id=item_id(p.url), source="MahaRERA", url=p.url,
        title=f"{MAHARERA_PHRASE[0].upper()}{MAHARERA_PHRASE[1:]}: {p.name}" + (f", {p.location}" if p.location else ""),
        text=" ".join(parts), published_at=published, fetched_at=fetched_at or now_utc())


def parse_page(page: str, fetched_at: Optional[datetime] = None) -> List[RawItem]:
    fetched_at = fetched_at or now_utc()
    return [to_item(p, fetched_at) for p in parse_projects(page)]


async def _ask(get: Fetcher, url: str, ok) -> Optional[str]:
    """The page body once `ok(body)` holds; None after `TRIES` empty or failed answers."""
    for attempt in range(TRIES):
        try:
            body = await get(url)
            if ok(body):
                return body
        except Exception:
            pass
        if attempt < TRIES - 1:
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    return None


class MahaReraSource:
    """`fetch` returns news items; `projects` then holds the same records as fields, for the project register."""
    name = "maharera"

    def __init__(self, district: int = PUNE_DISTRICT, pages: int = MAHARERA_PAGES):
        self.district, self.pages = district, max(1, pages)
        self.projects: List[MahaReraProject] = []

    async def fetch(self, get: Fetcher) -> List[RawItem]:
        self.projects = []
        try:
            first = None
            for rnd in range(1 + LATE_ROUNDS):  # without the count nothing else can be read: it gets the late rounds too
                if rnd:
                    await asyncio.sleep(LATE_PAUSE)
                first = await _ask(get, SEARCH.format(district=self.district, page=0), lambda b: parse_total(b))
                if first is not None:
                    break
            total = parse_total(first or "")
            if not total or total < 1:
                log.warning("newsroom: MahaRERA gave no result count after %d rounds", 1 + LATE_ROUNDS)
                return []
            last = (total - 1) // PAGE_SIZE
            seen, missed = set(), list(range(last, max(last - self.pages, -1), -1))
            for rnd in range(1 + LATE_ROUNDS):
                if rnd and missed:
                    await asyncio.sleep(LATE_PAUSE)
                still = []
                for page in missed:
                    body = await _ask(get, SEARCH.format(district=self.district, page=page), lambda b: parse_projects(b))
                    if body is None:
                        still.append(page)
                        continue
                    for p in parse_projects(body):
                        if p.regno not in seen:
                            seen.add(p.regno)
                            self.projects.append(p)
                missed = still
            if missed:  # the count's last page is often empty for good; any other page here means projects were lost this run
                log.warning("newsroom: MahaRERA pages %s stayed empty after %d rounds", missed, 1 + LATE_ROUNDS)
            fetched_at = now_utc()
            return [to_item(p, fetched_at) for p in self.projects]
        except Exception:
            self.projects = []
            return []
