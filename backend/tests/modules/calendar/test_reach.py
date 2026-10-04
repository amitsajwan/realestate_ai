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


def test_new_areas_get_their_tags_whatever_the_spelling():
    assert reach.hashtags(row("2 BHK in Lohgaon near the airport road"))[:2] == ["#LohegaonPune", "#Lohegaon"]
    assert reach.hashtags(row("Ready flats in Hinjewadi Phase 2"))[:2] == ["#HinjewadiPune", "#Hinjawadi"]
    assert reach.hashtags(row("Keshav Nagar, Mundhwa: 3 projects"))[:2] == ["#KeshavNagarPune", "#Mundhwa"]
    assert reach.hashtags(row("Wakad homes", channel="facebook_page")) == ["#WakadPune", "#Wakad", "#PuneProperty"]
    assert reach.area(row("Baner")).key == "baner"


def test_a_caption_naming_two_areas_picks_the_most_specific():
    assert reach.area(row("Upper Kharadi homes, 10 minutes from Kharadi IT parks")).key == "upper_kharadi"
    assert reach.area(row("Wagholi or Keshav Nagar: where 50 L goes further")).key == "keshav_nagar"


def test_an_explicit_area_key_wins_over_the_caption(monkeypatch):
    insight = row("12 projects finish in 2027. Kharadi buyers, look east.", area="wagholi")
    assert reach.area(insight).key == "wagholi"
    assert reach.hashtags(insight)[:2] == ["#WagholiPune", "#WagholiHomes"]
    assert reach.area(row("Wakad", area="upper-kharadi")).key == "upper_kharadi"  # a slug works too
    assert reach.area(row("Wakad", area="nowhere")).key == "wakad"  # an unknown key falls back to the caption
    monkeypatch.setenv("IG_LOCATION_WAGHOLI", "333")
    assert reach.location_id(insight) == "333"


def test_unknown_area_falls_back_to_pune(monkeypatch):
    monkeypatch.setenv("IG_LOCATION_PUNE", "111")
    monkeypatch.delenv("IG_LOCATION_HINJAWADI", raising=False)
    other = row("3 checks before you buy a resale flat in Kothrud")
    assert reach.area(other) is None
    assert reach.hashtags(other) == ["#PuneProperty", "#MahaRERA", "#PuneHomes"]
    assert reach.location_id(other) == "111"
    assert reach.location_id(row("Hinjewadi Phase 3 flats")) == "111"  # area known, its id not configured yet
    monkeypatch.setenv("IG_LOCATION_HINJAWADI", "444")
    assert reach.location_id(row("Hinjewadi Phase 3 flats")) == "444"


def test_agent_posts_keep_agent_tags_even_when_they_name_an_area():
    promo = row("Wagholi agents: buyers are asking about your area.", slug="promo-wagholi", area="wagholi")
    assert reach.hashtags(promo) == reach.AGENT_TAGS
