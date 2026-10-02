"""MahaRERA projects listed or updated recently (Pune district).

Reads the public search page https://www.maharera.maharashtra.gov.in/projects-search-result (no login, no captcha).
Results are paged 10 per page in ascending registration order, so the newest projects sit on the LAST pages.
We fetch page 0 only to learn the total count, then read the last `pages` pages. Anything unexpected gives [].
See docs/handoff/N1a-sources.md for the verified limits.
The only date a card gives is "Last Modified", so an item never claims the project is newly registered: it was listed or updated.
"""
import re
from datetime import datetime, timezone
from typing import List, Optional

from app.modules.newsroom.policy import MAHARERA_PAGES, MAHARERA_PHRASE
from app.modules.newsroom.sources._util import canonical_url, item_id, now_utc, strip_html
from app.modules.newsroom.types import Fetcher, RawItem

SEARCH = ("https://www.maharera.maharashtra.gov.in/projects-search-result?project_name=&project_location="
          "&project_completion_date=&project_state=27&project_district={district}&carpetAreas=&completionPercentages="
          "&project_division=&page={page}&op=")
PUNE_DISTRICT = 521  # value of the site's district filter for Pune (verified 2026-09-30)
PAGE_SIZE = 10
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


def parse_page(page: str, fetched_at: Optional[datetime] = None) -> List[RawItem]:
    fetched_at = fetched_at or now_utc()
    out: List[RawItem] = []
    for card in _CARD.findall(page or ""):
        try:
            reg = _REGNO.search(card)
            name = _NAME.search(card)
            if not reg or not name:
                continue
            regno, title_name = reg.group(1), strip_html(name.group(1))
            if not title_name:
                continue
            loc = _LOCATION.search(card)
            location = strip_html(loc.group(1)) if loc else ""
            district, pincode, modified = _field("District", card), _field("Pincode", card), _field("Last Modified", card)
            prom = _PROMOTER.search(card)
            promoter = strip_html(prom.group(1)) if prom else ""
            det = _DETAIL.search(card)
            url = DETAIL + det.group(1) if det else f"https://www.maharera.maharashtra.gov.in/projects-search-result?regno={regno}"
            published = None
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", modified):
                published = datetime.strptime(modified, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            where = ", ".join(p for p in (location, f"{district} district" if district else "") if p)
            parts = [f"Project {title_name} (MahaRERA registration number {regno}) was {MAHARERA_PHRASE}."]
            if where:
                parts.append(f"Location: {where}" + (f", pincode {pincode}." if pincode else "."))
            if promoter and _ORG.search(promoter):
                parts.append(f"Promoter: {promoter}.")
            if modified:
                parts.append(f"MahaRERA record last modified {modified}.")
            out.append(RawItem(
                id=item_id(url), source="MahaRERA", url=canonical_url(url),
                title=f"{MAHARERA_PHRASE[0].upper()}{MAHARERA_PHRASE[1:]}: {title_name}" + (f", {location}" if location else ""),
                text=" ".join(parts), published_at=published, fetched_at=fetched_at))
        except Exception:
            continue
    return out


class MahaReraSource:
    name = "maharera"

    def __init__(self, district: int = PUNE_DISTRICT, pages: int = MAHARERA_PAGES):
        self.district, self.pages = district, max(1, pages)

    async def fetch(self, get: Fetcher) -> List[RawItem]:
        try:
            total = parse_total(await get(SEARCH.format(district=self.district, page=0)))
            if not total or total < 1:
                return []
            last = (total - 1) // PAGE_SIZE
            out, seen = [], set()
            for page in range(last, max(last - self.pages, -1), -1):
                try:
                    body = await get(SEARCH.format(district=self.district, page=page))
                except Exception:
                    continue
                for it in parse_page(body or ""):
                    if it.id not in seen:
                        seen.add(it.id)
                        out.append(it)
            return out
        except Exception:
            return []
