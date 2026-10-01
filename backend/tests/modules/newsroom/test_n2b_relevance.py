"""N2b: relevance tightening after the live Google News dry run (filter denylist, headline-only drafts, check false positives)."""
from datetime import datetime, timezone

import pytest

from app.modules.newsroom import policy
from app.modules.newsroom.stages.check import check
from app.modules.newsroom.stages.draft import draft, headline_only, template_draft
from app.modules.newsroom.stages.filter import assess
from app.modules.newsroom.types import Draft, Fact, Facts, RawItem, Relevance

NOW = datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc)
PUB = datetime(2026, 9, 28, 6, 0, tzinfo=timezone.utc)
URL = "https://news.test/kharadi-road"


def it(title, text="", **kw):
    base = dict(id="x", source="google_news", url=URL, title=title, text=text, published_at=PUB, fetched_at=NOW)
    base.update(kw)
    return RawItem(**base)


# ---- A. filter ----

def test_pillar_fallback_no_longer_passes_an_item():
    r = assess(it("Kharadi residents host an art exhibition"), NOW)
    assert not r.keep and "pillar keyword evidence" in r.reason


def test_area_in_first_sentence_counts_as_subject():
    r = assess(it("Civic body announces repairs", "Metro pillar work in Kharadi will need a road closure for months. More later."), NOW)
    assert r.keep and r.areas == ["kharadi"]


def test_area_only_deep_in_body_is_not_the_subject():
    r = assess(it("Hinjewadi flyover work begins", "Work on the Hinjewadi road flyover has begun. Officials also toured Kharadi."), NOW)
    assert not r.keep and "in passing" in r.reason


def test_landmark_in_another_locality_story_is_dropped_but_landmark_alone_is_kept():
    assert not assess(it("Baner residents want a new road near EON IT Park"), NOW).keep
    r = assess(it("New metro road planned near EON IT Park"), NOW)
    assert r.keep and "kharadi" in r.areas


@pytest.mark.parametrize("title,label", [
    ("Wagholi hospital cricket tournament final", "sports"),
    ("Kharadi mall hosts film trailer launch", "entertainment"),
    ("Kharadi weather: IMD issues yellow alert", "weather"),
    ("Kharadi restaurant opens new menu", "hotels"),
])
def test_denylist_topics(title, label):
    r = assess(it(title), NOW)
    assert not r.keep and label in r.reason


def test_one_day_diversion_dropped_but_long_works_kept():
    assert "stale by nature" in assess(it("Kharadi traffic diversion on Saturday between 10 am and 4 pm"), NOW).reason
    assert assess(it("Traffic diversion on Kharadi bypass for flyover girder work", "Diversion will last for months."), NOW).keep


def test_weak_item_below_score_is_dropped():
    r = assess(it("Some news", "Officials met and discussed the road. Nothing more was said about Kharadi."), NOW)
    assert not r.keep


def test_kept_item_reports_score():
    r = assess(it("Pune: PMC Initiates Land Acquisition For Kharadi Road, ₹27.14 Crore Deposited"), NOW)
    assert r.keep and "score" in r.reason


# ---- B. headline-only drafts ----

pytestmark_async = pytest.mark.asyncio
HEAD = "Pune: PMC Initiates Land Acquisition For Kharadi Road, ₹27.14 Crore Deposited"
HITEM = it(HEAD, HEAD)
HFACTS = Facts([Fact("PMC has started land acquisition for Kharadi Road.", HEAD)], PUB)
REL = Relevance(True, "infrastructure", ["kharadi"])


class FakeLlm:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    async def json(self, system, user):
        self.calls.append((system, user))
        return self.reply

    async def text(self, system, user, timeout=None):
        raise AssertionError


def test_headline_only_detection():
    assert headline_only(it("A title", ""))
    assert headline_only(it("A title here", "A title here"))
    assert headline_only(it("A title here", "A title here  Times of India"))
    assert headline_only(it("A title", "A short summary of four words."))
    assert not headline_only(it("A title", " ".join(["word"] * 40)))


@pytest.mark.asyncio
async def test_headline_only_draft_is_short_and_has_no_our_view():
    reply = {"title": "t", "what": "PMC has started acquiring land for Kharadi Road.", "why": "This may reshape the area's future.",
             "check": "Look for the PMC notice.", "question": "Do you use Kharadi Road daily?"}
    llm = FakeLlm(reply)
    d = await draft(HITEM, HFACTS, REL, "article", llm)
    assert d.format == "post"  # never an article from a headline
    assert "Our view" not in d.text and "reshape" not in d.text
    assert "What to check: Look for the PMC notice." in d.text and "Source: Google News" in d.text and d.text.count("\n\n") <= 5
    assert "no room" not in llm.calls[0][0] and "only a headline" in llm.calls[0][0]
    r = check(d, HFACTS, HITEM, now=NOW)
    assert r.ok, r.problems


@pytest.mark.asyncio
async def test_headline_only_accepts_reply_without_why_and_fills_check():
    d = await draft(HITEM, HFACTS, REL, "post", FakeLlm({"what": "PMC has started acquiring land for Kharadi Road."}))
    assert d is not None and "What to check:" in d.text and "Kharadi? Tell us" in d.text


@pytest.mark.asyncio
async def test_long_source_without_a_why_falls_back_to_the_plain_template():
    long_item = it("Ring road", " ".join(["PMRDA said work has begun near Wagholi."] * 8))
    d = await draft(long_item, HFACTS, REL, "post", FakeLlm({"what": "Work began."}))
    assert d is not None and "Our view" not in d.text


def test_template_draft_has_no_generic_why_and_passes_check():
    d = template_draft(HITEM, HFACTS, REL, "post")
    assert "Our view" not in d.text and check(d, HFACTS, HITEM, now=NOW).ok


# ---- filler check ----

def _draft(text):
    return Draft("post", text, None, URL, ["Google News"])


BASE_FACTS = Facts([Fact("x", HEAD)], PUB)


def _post(extra=""):
    return (f"PMC has begun acquiring land for Kharadi Road, and ₹27.14 crore is deposited. {extra}\n\n"
            f"Source: Google News, as of 28 Sep 2026. {URL}\n\nDo you use this road? Tell us in the comments.\n\n#Pune")


@pytest.mark.parametrize("filler", [
    "Our view: This may affect the surrounding area's amenities.",
    "Our view: It is worth keeping an eye on.",
    "Our view: This could have implications for the local real estate market.",
    "Our view: Stay informed as things develop.",
])
def test_generic_filler_is_rejected(filler):
    r = check(_draft(_post(filler)), BASE_FACTS, HITEM, now=NOW)
    assert not r.ok and any("filler" in p.lower() for p in r.problems), r.problems


def test_specific_why_is_not_filler():
    r = check(_draft(_post("Our view: If you commute from Kharadi, this road may get wider over time.")), BASE_FACTS, HITEM, now=NOW)
    assert r.ok, r.problems


# ---- C. check false positives ----

@pytest.mark.parametrize("starter", ["Having", "Knowing", "Local", "Checking", "Nearby", "Recent"])
def test_sentence_initial_ordinary_words_are_not_names(starter):
    r = check(_draft(_post(f"{starter} the notice helps.")), BASE_FACTS, HITEM, now=NOW)
    assert not any("Names not in the source" in p for p in r.problems), r.problems


def test_real_unknown_names_still_caught_at_sentence_start():
    r = check(_draft(_post("Sunrise Developers are involved.")), BASE_FACTS, HITEM, now=NOW)
    assert any("Names not in the source" in p and "Sunrise" in p for p in r.problems)
    r = check(_draft(_post("Hinjewadi is nearby.")), BASE_FACTS, HITEM, now=NOW)
    assert any("Hinjewadi" in p for p in r.problems)


def _price_post(fig):
    return (f"The Thar OG is listed at {fig} in Wagholi.\n\nSource: Google News, as of 28 Sep 2026. {URL}\n\n"
            "Do you track vehicle prices? Tell us in the comments.\n\n#Pune")


@pytest.mark.parametrize("src,draft_fig", [("₹12.37L", "₹12.37 lakh"), ("₹12.37 Lakh", "₹12.37L"), ("₹27.14 Cr", "₹27.14 crore"),
                                          ("₹27.14 crore", "₹27.14 Cr")])
def test_lakh_and_crore_unit_spellings_are_equivalent(src, draft_fig):
    item = it(f"Thar OG price {src}", f"Thar OG price {src}")
    r = check(_draft(_price_post(draft_fig)), Facts([Fact("x", item.title)], PUB), item, now=NOW)
    assert not any("unit" in p.lower() or "Figures not found" in p for p in r.problems), r.problems


def test_wrong_unit_still_caught():
    item = it("Thar OG price ₹12.37L", "Thar OG price ₹12.37L")
    r = check(_draft(_price_post("₹12.37 crore")), Facts([Fact("x", item.title)], PUB), item, now=NOW)
    assert any("unit" in p.lower() for p in r.problems)


def test_hotel_brunch_news_is_not_buyer_news():
    r = assess(it("Novotel Pune Nagar Road Brings Back Its Sunday Brunch", "Novotel Pune Nagar Road has restarted its Sunday brunch service."), NOW)
    assert not r.keep


def test_a_hyphenated_name_made_of_source_words_is_not_flagged():
    item = it("Pune Ring Road: Rs 10,502 Crore Nod for Soratwadi-Varve Budruk Stretch", "The Pune Ring Road project has approval of Rs 10,502 crore for Soratwadi-Varve Budruk.")
    facts = Facts([Fact("Approval of Rs 10,502 crore", "approval of Rs 10,502 crore")], PUB)
    text = ("The Pune Ring Road has approval of Rs 10,502 crore to develop the Soratwadi-Varve Budruk section.\n\nSource: Pune Mirror, as of 28 Sep 2026. "
            + URL + "\n\nWould you like more details?\n\n#Pune")
    d = Draft("post", text, None, URL, ["Pune Mirror"])
    res = check(d, facts, item, now=NOW)
    assert not any("Names not in the source" in p for p in res.problems), res.problems
