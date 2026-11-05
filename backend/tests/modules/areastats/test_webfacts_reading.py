"""How the web-facts readers take a page's lines, and when two sites count as two sources (docs/plan/search-recovery.md R8).
The pages are cut-down copies of a marketer's page of Godrej Ivara, read on 2026-11-05."""
import httpx
import pytest

from app.modules.areastats import profile, webfacts

REGNO = "PR1260002502426"
NAME = "Godrej Ivara"
INTRO = ("Godrej Ivara marks the newest residential address by Godrej Properties in Kharadi, one of Pune's thriving IT and "
         "business landmarks. These boutique residences span 14 acres and rise in 11 towers. " + "Homebuyers will find more. " * 25)


def test_a_long_block_is_cut_into_sentences_not_dropped():
    assert len(INTRO) > webfacts.LONG_LINE
    part = webfacts.relevant(INTRO, NAME, regno=REGNO)
    assert "These boutique residences span 14 acres and rise in 11 towers." in part.split("\n")
    assert webfacts.on_page("These boutique residences span 14 acres and rise in 11 towers.", INTRO)


def test_an_abbreviation_does_not_end_a_sentence():
    line = "1.29 Cr* Onwards* (Inc. of Taxes & Charges) Rera Approved Godrej Elaris " * 12
    assert not any(x.startswith("of Taxes") for x in webfacts.fact_lines(line, NAME, REGNO))


def test_a_label_is_read_with_the_value_under_it():
    text = "Godrej Ivara\nTotal Units\n2792 Units\nLand Area\n14 Acres"
    lines = list(webfacts.fact_lines(text, NAME, REGNO))
    assert "Total Units 2792 Units" in lines and "Land Area 14 Acres" in lines
    assert webfacts.on_page("Total Units 2792 Units", text)


def test_another_projects_card_in_a_comparison_table_is_left_out():
    text = "\n".join(["Current Project", "Godrej Ivara", "Kharadi, Pune", "RERA No. PR1260002502426", "Land Area 14 Acres",
                      "Total Units 2792", "Godrej Elaris", "Mundhwa, Pune", "RERA No. PM1260002501385", "Land Area 12 Acres",
                      "Total Units 1,030", "How many towers are there in Godrej Ivara Pune?",
                      "The residential township will rise across 11 towers."])
    part = webfacts.relevant(text, NAME, regno=REGNO)
    assert "Land Area 14 Acres" in part and "Total Units 2792" in part and "11 towers" in part
    assert "12 Acres" not in part and "1,030" not in part


def test_another_projects_card_in_a_carousel_is_left_out():
    text = "\n".join(["Godrej Ivara Kharadi, Pune", "2 BHK Apartment 4 BHK Apartment 14 Acres Land Area", "2792 Units Number of Units",
                      "Godrej Elaris Mundhwa, Pune", "2 BHK Apartment 4 BHK Apartment 12 Acres Land Area", "1,030 Units Number of Units",
                      "Godrej Aqua Vista Keshav Nagar, Pune", "7 Acres Land Area", "1,532 Units Number of Units"])
    part = webfacts.relevant(text, NAME, regno=REGNO)
    assert "14 Acres" in part and "2792" in part
    assert "12 Acres" not in part and "1,030" not in part and "1,532" not in part
    assert "1,030" not in profile.relevant(text, NAME, regno=REGNO)


def test_a_place_alone_is_not_another_projects_card():
    assert not webfacts.other_card("Mundhwa, Pune", NAME)
    assert not webfacts.other_card("Upper Kharadi Road, Pune", NAME)
    assert not webfacts.other_card("Godrej Ivara Kharadi, Pune", NAME)
    assert webfacts.other_card("Kumar Prajwal Wadegaon, Pune", NAME)


def _reading(site, value, quote, key="land_acres"):
    return {"key": key, "value": value, "quote": quote, "site": site, "url": f"https://{site}/ivara", "official": False}


COPY = "The residential venture is spread across 14 acres, with 6 acres set aside for landscaping."


def test_two_sites_with_the_same_sentence_are_one_source():
    facts, _ = webfacts.agree([_reading("broker-one.in", 14, COPY), _reading("broker-two.com", 14, "Overview. " + COPY)])
    assert facts == []


def test_two_sites_in_their_own_words_publish_the_fact():
    facts, _ = webfacts.agree([_reading("broker-one.in", 14, COPY),
                               _reading("broker-two.com", 14, "Godrej Ivara sits on a land parcel of 14 acres in Kharadi.")])
    assert [(f["key"], f["value"]) for f in facts] == [("land_acres", 14)]


def test_short_quotes_count_apart():
    facts, _ = webfacts.agree([_reading("broker-one.in", 14, "Land Area 14 Acres"), _reading("broker-two.com", 14, "Land Area 14 Acres")])
    assert [f["value"] for f in facts] == [14]


def test_a_highlight_copied_by_a_second_site_is_not_published():
    bullet = {"topic": "clubhouse", "text": "Two clubhouses of 1,00,000 sq ft", "official": False}
    quote = "A grand 1,00,000 sq. ft. luxury clubhouse, split across two, anchors the amenities on offer."
    copied = [{**bullet, "quote": quote, "site": "a.in", "url": "https://a.in/x"}, {**bullet, "quote": quote, "site": "b.in", "url": "https://b.in/x"}]
    assert profile.agree(copied) == []
    own = copied[:1] + [{**bullet, "quote": "Two clubhouses with 1,00,000 sq ft of amenities between them.", "site": "b.in", "url": "https://b.in/x"}]
    assert [h["topic"] for h in profile.agree(own)] == ["clubhouse"]


@pytest.fixture
def fresh(monkeypatch):
    monkeypatch.setattr(webfacts, "_robots", {})
    monkeypatch.setattr(webfacts, "_last_read", {})
    monkeypatch.setattr(webfacts, "SITE_GAP_S", 0)


def _site(robots_status, robots_text=""):
    seen = []

    def answer(request):
        seen.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(robots_status, text=robots_text)
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<p>Godrej Ivara</p>")
    return httpx.MockTransport(answer), seen


async def test_a_page_robots_txt_forbids_is_not_read(fresh):
    transport, seen = _site(200, "User-agent: *\nDisallow: /projects/")
    assert await webfacts.read_page("https://builder.example/projects/ivara", transport) is None
    assert seen == ["/robots.txt"]
    assert await webfacts.read_page("https://builder.example/about", transport) == "<p>Godrej Ivara</p>"


async def test_robots_txt_naming_our_bot_is_followed(fresh):
    transport, _ = _site(200, "User-agent: AvasetuBot\nDisallow: /\n\nUser-agent: *\nAllow: /")
    assert await webfacts.read_page("https://builder.example/ivara", transport) is None


async def test_no_robots_txt_allows_every_page(fresh):
    transport, _ = _site(404)
    assert await webfacts.read_page("https://builder.example/ivara", transport) == "<p>Godrej Ivara</p>"


async def test_a_robots_txt_that_fails_allows_no_page(fresh):
    transport, seen = _site(503)
    assert await webfacts.read_page("https://builder.example/ivara", transport) is None
    assert seen == ["/robots.txt"]


async def test_robots_txt_is_read_once_per_site(fresh):
    transport, seen = _site(200, "User-agent: *\nAllow: /")
    await webfacts.read_page("https://builder.example/a", transport)
    await webfacts.read_page("https://builder.example/b", transport)
    assert seen.count("/robots.txt") == 1
