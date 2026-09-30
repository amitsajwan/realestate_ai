"""MahaRERA source. Fixtures maharera_pune_first.html / maharera_pune_last.html are the results region of the REAL
public pages (district=Pune, page 0 and last page), captured 2026-09-30."""
from pathlib import Path

import pytest

from app.modules.newsroom.sources.maharera import MahaReraSource, parse_page, parse_total

pytestmark = pytest.mark.asyncio
FIX = Path(__file__).parent / "fixtures" / "sources"
FIRST = (FIX / "maharera_pune_first.html").read_text(encoding="utf-8")
LAST = (FIX / "maharera_pune_last.html").read_text(encoding="utf-8")


def test_total_and_cards():
    assert parse_total(FIRST) == 12920
    assert parse_total("<html>nothing</html>") is None
    items = parse_page(LAST)
    assert len(items) == 10
    it = items[0]
    assert it.source == "MahaRERA" and it.title.startswith("MahaRERA project registration: Shantivan Homes Phase 8")
    assert "PP1260002601949" in it.text and "Pune district" in it.text
    assert it.url.startswith("https://maharerait.maharashtra.gov.in/public/project/view/")
    assert it.published_at.isoformat() == "2026-09-17T00:00:00+00:00"
    assert len({i.id for i in items}) == 10


def test_individual_promoters_are_not_named():
    items = parse_page(LAST)
    assert "Shekhar Valmik Kurundale" not in items[0].text
    assert any("Promoter:" in i.text for i in items)  # companies are still named


def test_unexpected_formats_give_empty():
    assert parse_page("") == [] and parse_page("<html><body>captcha required</body></html>") == []
    assert parse_page('<div class="row shadow p-3"><p>broken card</p></div>') == []


async def test_fetch_reads_last_pages_only():
    urls = []

    async def get(url):
        urls.append(url)
        return FIRST if "page=0&" in url else LAST

    items = await MahaReraSource(pages=2).fetch(get)
    assert "page=0&" in urls[0]
    assert "page=1291&" in urls[1] and "page=1290&" in urls[2] and len(urls) == 3  # 12920 results, 10 per page
    assert len(items) == 10  # the second page is the same fixture: de-duplicated by id
    assert "project_district=521" in urls[1]


async def test_fetch_never_raises():
    async def boom(url):
        raise RuntimeError("blocked")

    async def junk(url):
        return "<html>Access denied</html>"

    assert await MahaReraSource().fetch(boom) == []
    assert await MahaReraSource().fetch(junk) == []

    async def flaky(url):
        if "page=0&" in url:
            return FIRST
        raise TimeoutError

    assert await MahaReraSource().fetch(flaky) == []
