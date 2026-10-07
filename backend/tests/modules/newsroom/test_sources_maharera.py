"""MahaRERA source. Fixtures maharera_pune_first.html / maharera_pune_last.html are the results region of the REAL
public pages (district=Pune, page 0 and last page), captured 2026-09-30."""
from pathlib import Path

import pytest

from app.modules.newsroom.sources.maharera import MahaReraSource, last_page, parse_page, parse_total, read_pincode_page

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
    assert it.source == "MahaRERA" and it.title.startswith("Listed or updated on MahaRERA: Shantivan Homes Phase 8")
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
    # 12920 results, 10 per page, numbered from 1: the newest are on page 1292 (the site answers page 0 as page 1)
    assert "page=1292&" in urls[1] and "page=1291&" in urls[2] and len(urls) == 3
    assert len(items) == 10  # the second page is the same fixture: de-duplicated by id
    assert "project_district=521" in urls[1]


def test_last_page_counts_from_one():
    assert [last_page(n) for n in (1, 10, 11, 12920, 12949, 0)] == [1, 1, 2, 1292, 1295, 1]


async def test_pincode_page_reads_one_pincode():
    urls = []

    async def get(url):
        urls.append(url)
        return LAST

    total, projects = await read_pincode_page(get, "411047", 3)
    assert total == 12920 and len(projects) == 10
    assert "project_location=411047&" in urls[0] and "page=3&" in urls[0] and "project_district=521" in urls[0]

    async def empty(url):
        return "<html>No Records Found</html>"

    assert await read_pincode_page(empty, "411047", 1) == (None, [])


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
