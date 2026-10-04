from app.modules.calendar import reach

PROJECT = "Goyal My Home, Upper Kharadi: ₹97 L.\n\nMahaRERA P52100078796.\n\n#Pune #UpperKharadi #NewProjects #MahaRERA"


def row(caption, channel="instagram", **kw):
    return {"caption": caption, "channel": channel, "slug": kw.pop("slug", "hd-goyal"), **kw}


def test_buyer_posts_get_area_tags_and_lose_their_own():
    out = reach.apply(row(PROJECT))
    body, tags = out["caption"].rsplit("\n\n", 1)
    assert "#" not in body and body.endswith("MahaRERA P52100078796.")
    assert tags.split() == ["#UpperKharadi", "#KharadiPune", "#PuneProperty", "#MahaRERA", "#PuneHomes"]


def test_agent_promo_gets_agent_tags_and_facebook_gets_three():
    promo = row("Pune property agents: stop chasing comments.\n\n#PuneRealEstate #Avasetu", slug="promo-v2-group",
                creative={"source": "promo_agents_v2"})
    assert reach.audience(promo) == "agents"
    assert reach.apply(promo)["caption"].endswith("#PuneRealEstate #RealEstateAgentPune #PuneBrokers #ChannelPartner #PuneProperty")
    fb = reach.apply({**promo, "channel": "facebook_page"})["caption"]
    assert fb.endswith("#PuneRealEstate #RealEstateAgentPune #PuneBrokers")


def test_an_inline_tag_keeps_its_word():
    assert reach.with_hashtags("Homes in #Wagholi under 70 L", ["#WagholiPune"]) == "Homes in Wagholi under 70 L\n\n#WagholiPune"


def test_location_uses_the_area_then_pune_and_is_off_when_unset(monkeypatch):
    for k in ("PUNE", "KHARADI", "UPPER_KHARADI", "WAGHOLI"):
        monkeypatch.delenv(f"IG_LOCATION_{k}", raising=False)
    assert reach.location_id(row(PROJECT)) is None
    monkeypatch.setenv("IG_LOCATION_PUNE", "111")
    assert reach.location_id(row(PROJECT)) == "111"
    monkeypatch.setenv("IG_LOCATION_UPPER_KHARADI", "222")
    assert reach.location_id(row(PROJECT)) == "222"
    assert reach.location_id(row(PROJECT, channel="facebook_page")) is None  # Instagram only
    monkeypatch.setenv("IG_LOCATION_PUNE", "not-a-number")
    assert reach.location_id(row("A news item about Pune metro")) is None
