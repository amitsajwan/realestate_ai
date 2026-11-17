"""The weekly SEO audit fails on what keeps a sitemap page out of Google and only warns on the rest."""
import asyncio

import httpx

from app.modules.seo import audit

SITE = "https://avasetu.in"
DESC = "Wagholi flats: MahaRERA registration, completion dates and homes booked, from the public register."


def page(path, title="Wagholi projects", canonical=None, robots="", ld='{"@type": "Place"}', h1=1, desc=DESC, img='<img src="a" alt="">'):
    canon = f'<link rel="canonical" href="{canonical or SITE + path}">' if canonical != "" else ""
    return (f"<html><head><title>{title}</title><meta name=\"description\" content=\"{desc}\">{canon}"
            + (f'<meta name="robots" content="{robots}">' if robots else "")
            + f'<script type="application/ld+json">{ld}</script></head><body>' + "<h1>x</h1>" * h1
            + f"<svg><title>icon</title></svg>{img}</body></html>")


def site(pages, robots="User-agent: *\nAllow: /\nDisallow: /studio\nSitemap: https://avasetu.in/sitemap.xml\n"):
    urls = "".join(f"<url><loc>{SITE}{p}</loc></url>" for p in pages)
    xml = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'

    def handler(req):
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text=robots)
        if req.url.path == "/sitemap.xml":
            return httpx.Response(200, text=xml)
        body = pages.get(req.url.path)
        if body is None:
            return httpx.Response(404, text="nope")
        if isinstance(body, int):
            return httpx.Response(body, headers={"location": SITE + "/"})
        return httpx.Response(200, text=body, headers={"content-type": "text/html"})
    return httpx.MockTransport(handler)


async def test_a_clean_site_has_no_errors_or_warnings():
    rep = await audit.audit(SITE, transport=site({"/": page("/", title="Avasetu"), "/localities/wagholi": page("/localities/wagholi")}))
    assert (rep.errors, rep.warnings, rep.checked, rep.listed) == ([], [], 2, 2)


async def test_what_keeps_a_page_out_of_google_is_an_error():
    rep = await audit.audit(SITE, transport=site({
        "/a": page("/a", title="A", robots="noindex, follow"),
        "/b": page("/b", title="B", canonical=SITE + "/elsewhere"),
        "/c": page("/c", title="", ld="{not json"),
        "/d": 301,
        "/studio/x": page("/studio/x", title="S"),
    }))
    joined = "\n".join(rep.errors)
    for bit in ("`/a` is in the sitemap but says noindex", "`/b` is in the sitemap but names", "`/c` has no <title>",
                "`/c` structured data block 1 is not valid JSON", "`/d` answers 301", "`/studio/x` is in the sitemap but robots.txt blocks it"):
        assert bit in joined


async def test_softer_problems_are_warnings():
    rep = await audit.audit(SITE, transport=site({
        "/a": page("/a", title="T" * 80, h1=0, desc="short", img='<img src="a">'),
        "/b": page("/b", title="Same", canonical=""),
        "/c": page("/c", title="Same", h1=2),
    }))
    assert rep.errors == []
    joined = "\n".join(rep.warnings)
    for bit in ("`/a` title is 80 characters", "`/a` description is 5 characters", "`/a` has 0 <h1>", "`/a` has 1 image(s) without alt",
                "`/b` has no canonical link", "`/c` has 2 <h1>", '2 pages share the title "Same"'):
        assert bit in joined


async def test_robots_txt_must_name_the_sitemap():
    rep = await audit.audit(SITE, transport=site({"/": page("/")}, robots="User-agent: *\nAllow: /\n"))
    assert rep.errors == ["robots.txt does not name the sitemap"]


def test_a_large_sitemap_is_sampled_evenly():
    urls = [f"u{i}" for i in range(1000)]
    picked = audit.spread(urls, 10)
    assert len(picked) == 10 and picked[0] == "u0" and picked[-1] == "u900"
    assert audit.spread(urls[:5], 10) == urls[:5]


def test_the_report_counts_errors_and_warnings():
    text = audit.markdown(SITE, audit.Report(errors=["e1"], warnings=["w1", "w2"], checked=3, listed=9))
    assert "Checked 3 of 9 sitemap pages: **1 errors**, 2 warnings." in text and "- e1" in text and "- w2" in text


def ai_site(pages, robots="User-agent: *\nAllow: /\nSitemap: https://avasetu.in/sitemap.xml\n", for_bots=None):
    """Like site(), but a request whose user agent names an AI fetcher gets for_bots(path, ua) when that gives a response."""
    plain = site(pages, robots)

    def handler(req):
        ua = req.headers.get("user-agent", "")
        if for_bots and "compatible;" in ua:
            got = for_bots(req.url.path, ua)
            if got is not None:
                return got
        return plain.handler(req)
    return httpx.MockTransport(handler)


async def test_ai_fetchers_get_the_same_pages():
    rep = await audit.audit(SITE, transport=ai_site({"/": page("/", title="Avasetu"), "/a": page("/a", title="A")}))
    assert rep.errors == [] and rep.ai_checked == 2 * len(audit.AI_AGENTS)
    assert "and 8 reads as AI search fetchers" in audit.markdown(SITE, rep)


async def test_a_page_ai_fetchers_cannot_read_is_an_error():
    def shield(path, ua):
        if "PerplexityBot" in ua:
            return httpx.Response(403, text="blocked")
        if "bingbot" in ua and path == "/a":
            return httpx.Response(200, text="<html><head><title>Just a moment...</title></head><body></body></html>")
        if "OAI-SearchBot" in ua and path == "/a":
            return httpx.Response(200, text='<html><head><title>A</title></head><body><h1></h1><div id="app"></div></body></html>')
        return None
    rep = await audit.audit(SITE, transport=ai_site({"/": page("/", title="Avasetu"), "/a": page("/a", title="A")}, for_bots=shield))
    joined = "\n".join(rep.errors)
    assert "`/a` answers 403 to perplexitybot (200 to us)" in joined
    assert '`/a` shows bingbot another page (title "Just a moment...")' in joined
    assert "`/a` has no <h1> text in the HTML oai-searchbot gets" in joined


async def test_robots_txt_blocking_an_ai_fetcher_is_an_error():
    robots = "User-agent: *\nAllow: /\n\nUser-agent: OAI-SearchBot\nDisallow: /\nSitemap: https://avasetu.in/sitemap.xml\n"
    rep = await audit.audit(SITE, transport=ai_site({"/": page("/", title="Avasetu")}, robots=robots))
    assert rep.errors == ["`/`: robots.txt blocks oai-searchbot"]


def stalling(pages, slow=(), fail_first=()):
    """`site` with some pages answering late (`slow`) or 500 at the first read (`fail_first`), as a stalled server does."""
    inner, failed = site(pages), set()

    async def handler(req):
        if req.url.path in slow:
            await asyncio.sleep(0.05)
        if req.url.path in fail_first and req.url.path not in failed:
            failed.add(req.url.path)
            return httpx.Response(500, text="busy")
        return inner.handle_request(req)
    return httpx.MockTransport(handler)


async def test_a_server_that_stalls_under_a_crawl_fails_the_audit(monkeypatch):
    monkeypatch.setattr(audit, "SLOW_S", 0.02)
    monkeypatch.setattr(audit, "RETRY_S", 0.0)
    pages = {f"/p{i}": page(f"/p{i}", title=f"P{i}") for i in range(10)}
    rep = await audit.audit(SITE, transport=stalling(pages, slow={"/p1"}, fail_first={"/p2"}))
    assert rep.strained == 2
    assert any(e.startswith("2 of 10 pages were slow") for e in rep.errors)
    assert any(w.startswith("`/p1` took") for w in rep.warnings)
    assert "`/p2` answered 500, then 200 0 s later" in rep.warnings


async def test_one_slow_page_among_many_is_only_a_warning(monkeypatch):
    monkeypatch.setattr(audit, "SLOW_S", 0.02)
    pages = {f"/p{i}": page(f"/p{i}", title=f"P{i}") for i in range(60)}
    rep = await audit.audit(SITE, transport=stalling(pages, slow={"/p7"}))
    assert (rep.errors, rep.strained) == ([], 1)
    assert [w for w in rep.warnings if "took" in w] and rep.warnings[0].startswith("`/p7` took")
