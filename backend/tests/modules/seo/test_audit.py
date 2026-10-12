"""The weekly SEO audit fails on what keeps a sitemap page out of Google and only warns on the rest."""
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
