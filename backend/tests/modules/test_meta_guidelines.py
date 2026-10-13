"""Meta's content rules the posts follow: at most 5 hashtags on Instagram, no engagement bait, alt text on Instagram images, and
nothing important cut off by the profile grid's 3:4 crop."""
import pytest

from app.modules.calendar.footer import with_footer
from app.modules.creative.guards import problems_in
from app.modules.creative.models import SIZES
from app.modules.marketing.images import MARGIN
from app.modules.reels import compose
from app.platform.meta_graph.graph import GraphPublisher
from app.platform.meta_graph.publisher import Post
from app.platform.text import IG_MAX_HASHTAGS, cap_hashtags

from .test_social_helpers import REAL, FakeGraph

V = "/v23.0"
SEVEN = "#Pune #Kharadi #Wagholi #PuneProperty #MahaRERA #FlatsInPune #PuneHomes"


# ---- hashtags ----------------------------------------------------------------------------------------------------
def test_instagram_allows_five_hashtags():
    assert IG_MAX_HASHTAGS == 5


def test_cap_hashtags_keeps_the_first_five_and_drops_the_rest():
    out = cap_hashtags(f"Ready 2 BHK in Kharadi.\n\n{SEVEN}")
    assert out == "Ready 2 BHK in Kharadi.\n\n#Pune #Kharadi #Wagholi #PuneProperty #MahaRERA"


def test_cap_hashtags_leaves_text_within_the_limit_unchanged():
    text = "Ready 2 BHK.\n\n#Pune  #Kharadi\n"
    assert cap_hashtags(text) is text


def test_calendar_footer_keeps_five_tags_on_instagram_and_ten_on_facebook():
    caption = f"Ready 2 BHK in Kharadi.\n\n{SEVEN}"
    assert with_footer(caption, "instagram").count("#") == 5
    assert with_footer(caption, "facebook_page").count("#") == 7


@pytest.mark.asyncio
async def test_instagram_publisher_sends_at_most_five_hashtags_and_the_alt_text():
    g = FakeGraph({("POST", f"{V}/IG1/media"): (200, {"id": "C1"}), ("GET", f"{V}/C1"): (200, {"status_code": "FINISHED"}),
                   ("POST", f"{V}/IG1/media_publish"): (200, {"id": "M1"}), ("GET", f"{V}/M1"): (200, {"permalink": "https://ig/p"})})
    pub = GraphPublisher(REAL, transport=g.transport(), sleep=_no_sleep)
    await pub.publish(Post("instagram", f"2 BHK in Kharadi\n\n{SEVEN}", ["https://media.test/a.jpg"],
                           alt_text="Text card. Headline: 2 BHK in Kharadi."))
    form = g.calls[0]["form"]
    assert form["caption"].count("#") == 5
    assert form["alt_text"] == "Text card. Headline: 2 BHK in Kharadi."


@pytest.mark.asyncio
async def test_instagram_carousel_puts_the_alt_text_on_the_cover_only():
    n = iter(range(100, 200))
    g = FakeGraph({("POST", f"{V}/IG1/media"): lambda c: (200, {"id": f"C{next(n)}"}),
                   ("GET", f"{V}/C102"): (200, {"status_code": "FINISHED"}),
                   ("POST", f"{V}/IG1/media_publish"): (200, {"id": "M1"}), ("GET", f"{V}/M1"): (200, {"permalink": "https://ig/p"})})
    pub = GraphPublisher(REAL, transport=g.transport(), sleep=_no_sleep)
    await pub.publish(Post("instagram", "Two slides", ["https://media.test/a.jpg", "https://media.test/b.jpg"], alt_text="Cover"))
    assert g.calls[0]["form"]["alt_text"] == "Cover"
    assert "alt_text" not in g.calls[1]["form"] and "alt_text" not in g.calls[2]["form"]


async def _no_sleep(_s):
    return None


# ---- engagement bait ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text", ["Share this with a friend who is buying", "Tag a friend who needs this", "Vote in the comments",
                                  "React with one", "Double-tap if you agree", "Send this to someone buying"])
def test_engagement_bait_is_rejected(text):
    assert "engagement bait" in problems_in(text, "")


@pytest.mark.parametrize("text", ["Which would you pick, and why? Tell us below.", "Save this list", "We share what to check",
                                  "A or B? Tell us why below"])
def test_real_questions_and_saves_pass(text):
    assert "engagement bait" not in problems_in(text, "")


# ---- the profile grid shows a centred 3:4 crop --------------------------------------------------------------------
def test_feed_card_margins_survive_the_3_4_grid_crop():
    w, h = SIZES["instagram"]
    cut_each_side = (w - h * 3 / 4) / 2
    assert MARGIN >= cut_each_side


def test_reel_text_survives_the_3_4_grid_crop_of_the_cover():
    cut_each_end = (compose.H - compose.W * 4 / 3) / 2
    assert compose.TEXT_TOP >= cut_each_end and compose.TEXT_BOTTOM <= compose.H - cut_each_end


# ---- originality: a news post keeps our own view when the caption runs out of room ---------------------------------
def _long_news_doc():
    from app.modules.newsroom.samples import make_doc
    fact = "Metro corridor 2B to Wagholi is approved."
    d = make_doc("x1", fact, [fact], "infrastructure", ["wagholi"], "The Indian Express")
    summary = " ".join([fact] * 15)  # long enough that only a shortened summary fits beside our view
    d["draft"]["text"] = (f"{summary}\n\nOur view: Buyers in Wagholi can ask builders which station is nearest.\n\n"
                          "What to check: Read the official notice for the latest status before you decide.\n\n"
                          "Source: The Indian Express, as of 29 Sep 2026.\n\n#Pune")
    return d


def test_news_caption_drops_the_house_line_before_our_view():
    from app.modules.newsroom import captions
    from app.modules.newsroom import presentation as pr
    d = _long_news_doc()
    assert pr.buyer_line(d)
    for ch, text in captions.build(d).items():
        assert "Our view: Buyers in Wagholi" in text, ch
        assert len(text) < captions.FB_MAX
