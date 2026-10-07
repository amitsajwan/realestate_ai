import pytest

from app.modules.calendar.groups import GROUPS, campaign_id, group_of

LID = "0123456789abcdef0123456789abcdef"


def row(source=None, slug="x", kind="post", **creative):
    c = dict(creative)
    if source is not None:
        c["source"] = source
    return {"slug": slug, "kind": kind, "creative": c}


@pytest.mark.parametrize("doc,group", [
    (row("campaign", f"campaign-{LID}-price", role="listing"), "listings"),
    (row("campaign", f"campaign-{LID}-walkthrough", kind="reel", template="campaign"), "listings"),
    (row("agentprojects", "hd-goyal-my-home", role="project"), "listings"),
    (row("agentprojects", "hd-goyal-my-home-reel", kind="reel", role="project", template="project"), "listings"),
    (row("library", "carpet-under-rera", role="checklist"), "guides"),
    (row("trend_reels", "flat-60-lakh-real-cost", kind="reel"), "guides"),
    (row("reel", "water-questions", kind="reel", role="guide", template="tip"), "guides"),
    (row("reel", "reel-w1-tip", kind="reel", role="reel", template="tip"), "guides"),
    (row("agent_reels", "agent-a1", kind="reel", role="agent"), "agents"),
    (row("promo_agents", "promo-1"), "agents"),
    (row("promo_agents_v2", "promo-v2-3"), "agents"),
    (row(None, "promo-old"), "agents"),
    (row("agent", "agent-lead-cards", role="agent"), "agents"),
    (row("library", "agent-three-details", role="agent"), "agents"),
    (row("reel", "reel-w2-pitch", kind="reel", role="reel", template="pitch"), "agents"),
    (row("area_insight", "area-wagholi-20261012", kind="reel", role="area", template="area"), "news"),
    (row("newsroom", "news-x"), "news"),
    (row("home", "kharadi-2bhk-ready", kind="showcase", role="showcase"), "other"),
    (row("reel", "reel-w3-tour", kind="reel", role="reel", template="tour"), "other"),
    (row(None, "mystery"), "other"),
    ({"slug": "bare"}, "other"),
])
def test_every_source_has_a_group(doc, group):
    assert group_of(doc) == group and group in GROUPS


def test_campaign_id_from_the_row_or_its_slug():
    assert campaign_id({**row("campaign", f"campaign-{LID}-price"), "listing_id": "L1"}) == "L1"
    assert campaign_id(row("campaign", f"campaign-{LID}-price-reel")) == LID
    assert campaign_id(row("campaign", "campaign-abc-price")) == "abc"
    assert campaign_id(row("agentprojects", "hd-goyal")) is None
    assert campaign_id(row("library", "carpet")) is None
