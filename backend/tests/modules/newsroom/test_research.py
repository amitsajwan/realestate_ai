"""Research before writing, and full articles written from it.

The story is modelled on a real one found while researching this change (Punekar News, September 2026: Pune homebuyers still
awaiting Rs 106.72 crore in refunds and compensation across 176 recovery cases despite MahaRERA orders). The page text is ours,
written for the test; the shape is what the newsroom meets in practice: one publisher's full page, another publisher's shorter
report of the same story, and a Google News item whose link cannot be read.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from app.modules.newsroom import codec, policy, public
from app.modules.newsroom import presentation as pr
from app.modules.newsroom.config import NewsroomConfig
from app.modules.newsroom.pipeline import run_once
from app.modules.newsroom.stages import research as rs
from app.modules.newsroom.stages.check import check
from app.modules.newsroom.stages.draft import ARTICLE_MIN_CHARS, can_be_article, draft
from app.modules.newsroom.stages.extract import extract
from app.modules.newsroom.stages.filter import assess, same_story
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import Fact, Facts, RawItem, Relevance, Research, SourceDoc

from ..fakes import FakeDb

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
CFG = NewsroomConfig(enabled=True)

MAIN_URL = "https://www.punekarnews.in/pune-homebuyers-await-refunds"
OTHER_URL = "https://www.hindustantimes.com/cities/pune-news/maharera-recovery-cases"
GOOGLE_URL = "https://news.google.com/rss/articles/CBMiabc"

MAIN_PARAS = [
    "Homebuyers in Pune district are still waiting for Rs 106.72 crore in refunds and compensation that MahaRERA has ordered developers to pay.",
    "The amount is spread across 176 recovery cases in which developers have not paid what the authority ordered, according to data from the district collectorate.",
    "When a developer does not pay, MahaRERA issues a recovery warrant, and the collector can attach and auction the developer's property to recover the dues.",
    "Officials said notices have been sent in all 176 cases and that hearings are being held every week at the collectorate in Pune.",
    "Buyers said they had waited for years for possession before turning to MahaRERA, and now wait again for the money the orders promised.",
    "The collectorate has recovered part of the dues in some cases by auctioning flats and land held by developers, officials said.",
    "MahaRERA can order a refund with interest when a project is delayed beyond the possession date in the registered agreement.",
]
OTHER_PARAS = [
    "Recovery of MahaRERA dues remains slow in Pune, with 176 warrants pending at the collectorate.",
    "The Pune collectorate said 41 of the cases involve projects in Haveli taluka.",
    "Under the RERA Act a recovery warrant is executed like arrears of land revenue, which allows the attachment of a defaulter's property.",
    "Several buyers told the newspaper that they had first approached MahaRERA after their projects missed the promised possession dates.",
]


def page(paras):
    body = "".join(f"<p>{p}</p>" for p in paras)
    return f"<html><head><title>x</title></head><body><nav><p>Home | Pune | Subscribe</p></nav><article>{body}</article></body></html>"


PAGES = {MAIN_URL: page(MAIN_PARAS), OTHER_URL: page(OTHER_PARAS)}


async def get(url):
    if url.endswith("/robots.txt"):
        return "User-agent: *\nAllow: /\n"
    if url in PAGES:
        return PAGES[url]
    raise RuntimeError("404")


def raw(n, source, url, title, text, hours=6):
    return RawItem(id=f"r{n}", source=source, url=url, title=title, text=text,
                   published_at=NOW - timedelta(hours=hours), fetched_at=NOW)


MAIN = raw(1, "Punekar News", MAIN_URL, "Pune Homebuyers Await Rs 106.72 Crore in Refunds, Compensation Despite MahaRERA Orders",
           "Homebuyers in Pune district are still awaiting nearly Rs 106.72 crore in refunds.")
OTHER = raw(2, "Hindustan Times", OTHER_URL, "176 MahaRERA recovery warrants pending in Pune as homebuyers await refunds",
            "Recovery of MahaRERA dues remains slow in Pune.", hours=3)
GOOGLE = raw(3, "The Times of India", GOOGLE_URL, "Rs 106.72 crore MahaRERA refunds stuck in Pune", "Rs 106.72 crore MahaRERA refunds stuck in Pune")
UNRELATED = raw(4, "Hindustan Times", "https://www.hindustantimes.com/cities/pune-news/pmc-budget", "PMC presents budget for water projects",
                "The PMC presented its budget.")


# ---- finding the other reports -------------------------------------------------------------------------------------------------

def test_other_publishers_reports_of_the_same_story_are_found_and_unrelated_news_is_not():
    got = rs.pick_related(MAIN, [OTHER, GOOGLE, UNRELATED, MAIN], same_story)
    assert [g.id for g in got] == ["r2", "r3"]  # the readable publisher first, the Google item after it, the budget story not at all


def test_one_report_per_publisher_and_never_the_items_own_publisher():
    own = replace(OTHER, id="r9", source="Punekar News", url="https://www.punekarnews.in/other")
    twin = replace(OTHER, id="r8", url="https://www.hindustantimes.com/x")
    got = rs.pick_related(MAIN, [own, OTHER, twin], same_story)
    assert [g.source for g in got] == ["Hindustan Times"]


def test_background_comes_from_the_area_guide_shares_a_topic_and_is_never_advice():
    bg = rs.background_for(["wagholi"], "Corridor 2B metro work near Wagholi")
    assert bg and any("Corridor 2B" in b for b in bg)
    assert not any(b.lower().startswith("check") for b in bg)
    assert rs.background_for(["wagholi"], "Stamp duty unchanged") == []  # nothing in the guide is about stamp duty: no padding


# ---- the research stage --------------------------------------------------------------------------------------------------------

async def test_research_reads_the_full_report_and_the_other_reports_and_says_what_it_could_not_read():
    r = await rs.research(MAIN, Relevance(keep=True, pillar="rules_money"), [OTHER, GOOGLE, UNRELATED], get, same_story=same_story)
    main, other = r.sources
    assert main.role == "main" and main.full and "176 recovery cases" in main.text and "Subscribe" not in main.text
    assert other.name == "Hindustan Times" and other.full and "41 of the cases" in other.text
    assert r.also_reported == ["The Times Of India"] or r.also_reported == ["The Times of India"]
    assert any("Read the full report from Punekar News" in n for n in r.notes)
    assert any("Google News link" in n for n in r.notes)
    assert rs.readable_chars(r) >= ARTICLE_MIN_CHARS


async def test_a_page_robots_txt_forbids_is_not_read_and_the_feed_text_is_used():
    async def no_robots(url):
        return "User-agent: *\nDisallow: /\n" if url.endswith("/robots.txt") else PAGES[url]
    r = await rs.research(MAIN, None, [], no_robots)
    assert not r.sources[0].full and r.sources[0].text == MAIN.text
    assert any("robots.txt" in n for n in r.notes) and any("No other report" in n for n in r.notes)


# ---- extraction across reports -------------------------------------------------------------------------------------------------

class Llm:
    """Answers like a model would: facts for the extract prompt, an article for the article prompt."""

    def __init__(self, facts=None, article=None):
        self.facts, self.article, self.calls = facts, article, []

    async def json(self, system, user):
        self.calls.append((system, user))
        if "extract facts" in system:
            return {"facts": self.facts or []}
        if "news article" in system:
            return self.article
        return None

    async def text(self, system, user, timeout=None):
        return None


FACTS_REPLY = [
    {"text": "Pune homebuyers are waiting for Rs 106.72 crore in refunds and compensation ordered by MahaRERA",
     "quote": "Homebuyers in Pune district are still waiting for Rs 106.72 crore in refunds and compensation that MahaRERA has ordered developers to pay.", "source": 1},
    {"text": "The money is spread across 176 recovery cases",
     "quote": "The amount is spread across 176 recovery cases in which developers have not paid what the authority ordered", "source": 1},
    {"text": "The collector can attach and auction a developer's property to recover the dues",
     "quote": "the collector can attach and auction the developer's property to recover the dues", "source": 1},
    {"text": "41 of the cases involve projects in Haveli taluka",
     "quote": "The Pune collectorate said 41 of the cases involve projects in Haveli taluka.", "source": 1},  # wrong number: it is report 2
    {"text": "500 cases were closed last month", "quote": "500 cases were closed last month", "source": 2},  # invented: not in any report
]


async def _research():
    return await rs.research(MAIN, Relevance(keep=True, pillar="rules_money"), [OTHER, GOOGLE], get, same_story=same_story)


async def test_facts_come_from_every_report_each_credited_to_the_report_that_says_it():
    facts = await extract(MAIN, Llm(FACTS_REPLY), research=await _research())
    by = {f.text: f.source for f in facts.facts}
    assert by["The money is spread across 176 recovery cases"] == "Punekar News"
    assert by["41 of the cases involve projects in Haveli taluka"] == "Hindustan Times"  # credited to the report that has the quote
    assert "500 cases were closed last month" not in by  # a quote no report contains is dropped
    assert facts.as_of == OTHER.published_at  # the newest report the facts come from


# ---- the article ---------------------------------------------------------------------------------------------------------------

ARTICLE = {
    "title": "Pune buyers still owed Rs 106.72 crore under MahaRERA orders",
    "standfirst": "Homebuyers in Pune district are owed Rs 106.72 crore in refunds and compensation that MahaRERA ordered, but developers have not paid.",
    "body": [
        "According to Punekar News, the dues are spread across 176 recovery cases at the district collectorate.",
        "When a developer ignores an order, the collector can attach and auction the developer's property to recover the money.",
        "Hindustan Times reported that 41 of the cases involve projects in Haveli taluka.",
    ],
    "background": "",
    "why": "A MahaRERA order in your favour may still take a long time to turn into money. Buyers in a delayed project could weigh that before choosing refund or possession.",
    "check": ["Ask the developer for the project's MahaRERA complaint history", "Look up the project's registration status on the MahaRERA website"],
    "question": "Have you waited for a MahaRERA refund?",
}


async def test_a_researched_story_becomes_a_full_article_that_passes_the_checks():
    r = await _research()
    facts = await extract(MAIN, Llm(FACTS_REPLY), research=r)
    rel = Relevance(keep=True, pillar="rules_money")
    d = await draft(MAIN, facts, rel, "article", Llm(article=ARTICLE), research=r)
    assert d.format == "article" and d.title == ARTICLE["title"]
    assert d.source_names[:2] == ["Punekar News", "Hindustan Times"] and d.source_urls[:2] == [MAIN_URL, OTHER_URL]
    assert "Sources: Punekar News (" in d.text and "as of 30 Sep 2026" in d.text
    parts = pr.split_text(d.text)
    assert parts.lead == ARTICLE["standfirst"] and len(parts.body) == 4 and parts.our_view and parts.what_to_check
    evidence = replace(MAIN, text=MAIN.text + "\n\n" + rs.evidence_text(r))
    res = check(d, facts, evidence, now=NOW)
    assert res.ok, res.problems


async def test_the_check_still_catches_a_figure_no_report_gives():
    r = await _research()
    facts = await extract(MAIN, Llm(FACTS_REPLY), research=r)
    bad = {**ARTICLE, "body": ARTICLE["body"] + ["Developers have paid Rs 12 crore so far."]}
    d = await draft(MAIN, facts, Relevance(keep=True, pillar="rules_money"), "article", Llm(article=bad), research=r)
    res = check(d, facts, replace(MAIN, text=MAIN.text + "\n\n" + rs.evidence_text(r)), now=NOW)
    assert not res.ok and any("12" in p for p in res.problems)


async def test_without_the_model_the_article_is_built_from_the_facts_grouped_by_report():
    r = await _research()
    facts = await extract(MAIN, Llm(FACTS_REPLY), research=r)
    d = await draft(MAIN, facts, Relevance(keep=True, pillar="rules_money"), "article", None, research=r)
    assert d.format == "article" and "(Reported by Hindustan Times.)" in d.text
    res = check(d, facts, replace(MAIN, text=MAIN.text + "\n\n" + rs.evidence_text(r)), now=NOW)
    assert res.ok, res.problems


def test_a_headline_and_a_line_never_make_an_article():
    facts = Facts([Fact("a", "a"), Fact("b", "b"), Fact("c", "c")], NOW)
    thin = Research(sources=[SourceDoc("Punekar News", MAIN_URL, MAIN.title, MAIN.text, role="main", full=False)])
    assert not can_be_article(MAIN, facts, thin) and not can_be_article(MAIN, facts, None)
    one = SourceDoc("Punekar News", MAIN_URL, MAIN.title, " ".join(MAIN_PARAS), role="main", full=True)
    assert len(one.text) >= ARTICLE_MIN_CHARS
    assert not can_be_article(MAIN, facts, Research(sources=[one]))  # one publisher alone is not a researched report
    full = Research(sources=[one, SourceDoc("Hindustan Times", "https://www.hindustantimes.com/x", "t", "u", full=True)])
    assert can_be_article(MAIN, facts, full)
    assert not can_be_article(MAIN, Facts(facts.facts[:2], NOW), full)  # too few facts for an article


# ---- through the pipeline, onto the site ---------------------------------------------------------------------------------------

class Source:
    name = "test"

    async def fetch(self, _get):
        return [MAIN, OTHER, GOOGLE]


async def test_pipeline_researches_writes_an_article_and_the_site_shows_every_source():
    s = Store(FakeDb(), clock=lambda: NOW)

    async def research_stage(item, rel, candidates, fetch):
        return await rs.research(item, rel, candidates, fetch, same_story=same_story)

    stages = {"filter": assess, "same_story": same_story, "research": research_stage, "extract": extract, "draft": draft,
              "check": check, "get": get}
    stages["check"] = lambda d, f, it: check(d, f, it, now=NOW)
    await run_once(s, [Source()], stages, None, Llm(FACTS_REPLY, ARTICLE), NOW, CFG)
    doc = await s.get("r1")
    assert "relevance" in doc, doc["history"]
    assert doc["relevance"]["pillar"] == "rules_money" and doc["relevance"]["areas"] == []  # city-wide buyer news, no area needed
    assert doc["status"] == "pending_review", doc["history"][-1]
    assert [x["name"] for x in doc["research"]["sources"]] == ["Punekar News", "Hindustan Times"]
    assert doc["draft"]["format"] == "article" and "176 recovery cases" in doc["raw"]["text"]  # the full report replaced the feed line
    assert (await s.get("r2"))["status"] == "dropped" and (await s.get("r3"))["status"] == "dropped"  # same story: one article, not three

    view = public.view({**doc, "status": "published"})
    assert view["summary"] == ARTICLE["standfirst"] and view["body"] == ARTICLE["body"]
    assert [x["name"] for x in view["sources"]][:2] == ["Punekar News", "Hindustan Times"]
    assert view["sources"][0]["url"] == MAIN_URL and view["our_view"] and view["what_to_check"]
    assert codec.evidence(doc).text.count("41 of the cases") >= 1


def test_market_is_a_pillar_with_a_label_a_buyer_line_and_a_place_in_the_priority():
    assert pr.PILLAR_LABELS["market"] == "Market" and ("market", "") in policy.BUYER_LINES
    assert policy.PILLAR_PRIORITY.index("rules_money") < policy.PILLAR_PRIORITY.index("infrastructure")


async def test_background_from_the_area_guide_is_labelled_and_passes_the_checks():
    text = ("Maha-Metro has started soil testing for Corridor 2B between Ramwadi and Wagholi, officials said on Monday. "
            "The work covers 11 planned stations along Nagar Road. Officials said the tender for civil work will be issued after the tests. "
            "Residents of Wagholi have long complained about traffic on Nagar Road at peak hours. ") * 3
    it = RawItem("w1", "Punekar News", "https://www.punekarnews.in/wagholi-metro", "Soil testing begins for Wagholi metro corridor",
                 text, NOW - timedelta(hours=3), NOW)
    bg = rs.background_for(["wagholi"], f"{it.title} {text}")
    assert any("approved is not the same as running" in b for b in bg)
    r = Research([SourceDoc("Punekar News", it.url, it.title, text, role="main", full=True),
                  SourceDoc("Pune Mirror", "https://punemirror.com/w", it.title, text, full=True)], bg, "Avasetu area guide")
    facts = Facts([
        Fact("Maha-Metro has started soil testing for Corridor 2B", "Maha-Metro has started soil testing for Corridor 2B between Ramwadi and Wagholi", "Punekar News"),
        Fact("The work covers 11 planned stations", "The work covers 11 planned stations along Nagar Road", "Punekar News"),
        Fact("A civil work tender will follow the tests", "the tender for civil work will be issued after the tests", "Punekar News")], NOW)
    reply = {"title": "Soil tests start on the Ramwadi to Wagholi metro route",
             "standfirst": "Maha-Metro has begun soil testing on Corridor 2B, the planned metro route from Ramwadi to Wagholi.",
             "body": ["According to Punekar News, the testing covers the 11 planned stations along Nagar Road.",
                      "Officials said a tender for the civil work would follow once the tests are done."],
             "background": "Corridor 2B has been approved by the Union Cabinet, but approved is not the same as running.",
             "why": "Soil tests are an early step, so a working line may still be years away. Buyers in Wagholi could treat the metro as planned, not as a reason to pay more today.",
             "check": ["Ask how far your shortlisted project is from the nearest planned station"], "question": "Would a metro change where you buy?"}
    d = await draft(it, facts, Relevance(True, "infrastructure", ["wagholi"]), "article", Llm(article=reply), research=r)
    assert d.format == "article" and pr.split_text(d.text).background.startswith("Corridor 2B has been approved")
    res = check(d, facts, replace(it, text=it.text + "\n\n" + rs.evidence_text(r)), now=NOW)
    assert res.ok, res.problems


# ---- what gets picked: real headlines from the research for this change (Punekar News, Tribune, September and July 2026) ------

def _assess(title, text):
    return assess(RawItem("t", "x", "https://x.test", title, text, NOW, NOW), NOW)


def test_city_wide_rulings_rules_and_market_reports_are_kept_without_naming_an_area():
    kept = [
        ("Pune Homebuyers Await Rs 106.72 Crore in Refunds, Compensation Despite MahaRERA Orders",
         "Homebuyers in Pune district are still awaiting refunds across 176 pending recovery cases.", "rules_money"),
        ("MahaRERA orders Aqura Builder to pay delay interest to 4 homebuyers in Pune project",
         "The authority ordered interest from January 7, 2026.", "rules_money"),
        ("Pune Home Sales Rebound 7% After Three-Year Slowdown, But Unsold Inventory Hits Record Rs 92,110 Crore: Gera Report",
         "Sales increased from 86,666 units in June 2025 to 92,341 units in June 2026.", "market"),
        ("Maharashtra hikes ready reckoner rates by 5% across Pune",
         "The state revenue department raised ready reckoner rates for Pune district, raising stamp duty paid by home buyers.", "rules_money"),
        ("RBI cuts repo rate by 25 bps; home loan EMIs to fall", "Banks are expected to lower home loan rates.", "rules_money"),
    ]
    for title, text, pillar in kept:
        r = _assess(title, text)
        assert r.keep and r.pillar == pillar and r.areas == [], (title, r)


def test_airport_operations_are_not_property_news_but_airport_land_and_building_rules_are():
    for title, text in [("Pune airport sees record passenger traffic in September", "Pune airport handled 9 lakh passengers."),
                        ("IndiGo launches new flight from Pune airport to Bangkok", "The airline will start daily flights."),
                        ("Pune airport new terminal parking charges revised", "Parking charges at the new terminal have been revised."),
                        ("Lohegaon airport to get more flights to Dubai", "New flights from Lohegaon begin next month.")]:
        assert not _assess(title, text).keep, title
    assert _assess("Purandar airport: farmers protest land acquisition",
                   "Farmers in seven villages near Pune protested the land acquisition for the Purandar airport.").keep
    assert _assess("Lohegaon airport: height restriction rules eased for buildings",
                   "The Airports Authority of India eased height clearance rules for buildings near Lohegaon.").keep


def test_other_localities_launches_and_other_cities_stay_out():
    assert not _assess("Launch of new housing project in Hinjewadi Phase 3", "A developer launched a new project in Hinjewadi.").keep
    assert not _assess("Mumbai property registrations hit record in September", "Mumbai recorded 12,000 property registrations.").keep
