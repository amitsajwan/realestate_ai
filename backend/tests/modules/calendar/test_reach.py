from app.modules.calendar import reach

PROJECT = "Goyal My Home, Upper Kharadi: ₹97 L.\n\nMahaRERA P52100078796.\n\n#Pune #UpperKharadi #NewProjects #MahaRERA"


def row(caption, channel="instagram", **kw):
    return {"caption": caption, "channel": channel, "slug": kw.pop("slug", "hd-goyal"), **kw}


def test_buyer_posts_get_area_and_project_tags_in_one_line():
    out = reach.apply(row(PROJECT))
    body, tags = out["caption"].rsplit("\n\n", 1)
    assert "#" not in body and body.endswith("MahaRERA P52100078796.")
    assert tags.split() == ["#UpperKharadi", "#GoyalMyHome", "#PuneProperty", "#MahaRERA", "#KharadiPune"]


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
    assert reach.hashtags(row("2 BHK in Lohgaon near the airport road"))[:2] == ["#LohegaonPune", "#FlatsInPune"]
    assert "#Lohegaon" in reach.hashtags(row("Homes in Lohgaon near the airport road"))
    assert reach.hashtags(row("Ready flats in Hinjewadi Phase 2"))[:2] == ["#HinjewadiPune", "#FlatsInPune"]
    assert reach.hashtags(row("Keshav Nagar, Mundhwa: 3 projects"))[:3] == ["#KeshavNagarPune", "#PuneProperty", "#Keshavnagar"]
    assert reach.hashtags(row("Wakad homes", channel="facebook_page")) == ["#WakadPune", "#PuneProperty", "#Wakad"]
    assert reach.area(row("Baner")).key == "baner"


def test_a_caption_naming_two_areas_picks_the_most_specific():
    assert reach.area(row("Upper Kharadi homes, 10 minutes from Kharadi IT parks")).key == "upper_kharadi"
    assert reach.area(row("Wagholi or Keshav Nagar: where 50 L goes further")).key == "keshav_nagar"


def test_an_explicit_area_key_wins_over_the_caption(monkeypatch):
    insight = row("12 projects finish in 2027. Kharadi buyers, look east.", area="wagholi")
    assert reach.area(insight).key == "wagholi"
    assert reach.hashtags(insight)[:3] == ["#WagholiPune", "#PuneProperty", "#WagholiHomes"]
    assert reach.area(row("Wakad", area="upper-kharadi")).key == "upper_kharadi"  # a slug works too
    assert reach.area(row("Wakad", area="nowhere")).key == "wakad"  # an unknown key falls back to the caption
    monkeypatch.setenv("IG_LOCATION_WAGHOLI", "333")
    assert reach.location_id(insight) == "333"


def test_unknown_area_falls_back_to_pune(monkeypatch):
    monkeypatch.setenv("IG_LOCATION_PUNE", "111")
    monkeypatch.delenv("IG_LOCATION_HINJAWADI", raising=False)
    other = row("3 checks before you buy a resale flat in Kothrud")
    assert reach.area(other) is None
    assert reach.hashtags(other) == ["#FlatsInPune", "#PuneProperty", "#PuneHomes", "#PuneRealEstate"]  # no MahaRERA number
    assert reach.location_id(other) == "111"
    assert reach.location_id(row("Hinjewadi Phase 3 flats")) == "111"  # area known, its id not configured yet
    monkeypatch.setenv("IG_LOCATION_HINJAWADI", "444")
    assert reach.location_id(row("Hinjewadi Phase 3 flats")) == "444"


def test_agent_posts_keep_agent_tags_even_when_they_name_an_area():
    promo = row("Wagholi agents: buyers are asking about your area.", slug="promo-wagholi", area="wagholi")
    assert reach.hashtags(promo) == reach.AGENT_TAGS


# --- the most specific tags first, the caption's own kept as candidates (live 2026-10-07: Gulmohar City, Ranjangaon went
# out with "#PuneProperty #MahaRERA #PuneHomes": its locality and "plots" were thrown away) ---

GULMOHAR = ("Myth: Every plot is ready to build on.\n\nGulmohar City, Ranjangaon.\nMyth: Every plot is ready to build on.\n"
            "Fact: Check the NA order and the approved layout first.\n- House Deal team\n\nDid you believe this one? Tell us below."
            "\n\n📞 कॉल / WhatsApp: +91 99219 93099\n\n"
            "Full details of Gulmohar City, Ranjangaon, with its MahaRERA record: link in bio.\n\n"
            "#Ranjangaon #PuneProperty #PlotsInPune #MahaRERA")
CAMPAIGN = {"role": "listing", "source": "campaign", "path": "campaign", "angle": "myth", "ok": True}  # as schedule.items writes it


def campaign(caption=GULMOHAR, channel="instagram"):
    return row(caption, channel, slug="campaign-6650f1-myth", creative=CAMPAIGN, listing_id="6650f1")


def test_a_plot_campaign_outside_our_areas_keeps_locality_project_and_plots():
    out = reach.apply(campaign())["caption"]
    body, tags = out.rsplit("\n\n", 1)
    assert tags.split() == ["#Ranjangaon", "#GulmoharCity", "#PlotsInPune", "#PuneProperty", "#MahaRERA"]
    assert "#" not in body and body.endswith("with its MahaRERA record: link in bio.")
    assert reach.locality(campaign()) == ("Ranjangaon", None)
    assert reach.project_and_locality(campaign()) == ("Gulmohar City", "Ranjangaon")


def test_facebook_campaign_gets_the_three_most_specific_even_without_the_link_line():
    fb = GULMOHAR.replace("Full details of Gulmohar City, Ranjangaon, with its MahaRERA record: link in bio.",
                          "Full details and the MahaRERA record: https://avasetu.in/p/gulmohar?src=fb_myth")
    assert reach.hashtags(campaign(fb, "facebook_page")) == ["#Ranjangaon", "#GulmoharCity", "#PlotsInPune"]


def test_a_locality_with_two_words_becomes_one_camel_case_tag():
    cap = "A 1,500 sq ft plot.\n\nShree Nisarg, Shirur Pune.\n\n#PuneProperty"
    assert reach.hashtags(campaign(cap))[:3] == ["#ShirurPune", "#ShreeNisarg", "#PlotsInPune"]
    assert reach.camel_tag("chakan midc") == "#ChakanMidc"
    assert reach.camel_tag("Hill View, Phase II") == "#HillViewPhaseII"


def test_fields_on_the_row_win_over_the_caption():
    r = row("A new launch near the highway.", creative={"source": "campaign", "project_name": "Green Acres",
                                                        "locality": "Chakan", "property_type": "plot"})
    assert reach.hashtags(r)[:3] == ["#Chakan", "#GreenAcres", "#PlotsInPune"]


def test_a_wagholi_flat_gets_area_type_and_rera_before_a_second_area_tag():
    cap = "2 BHK flats in Wagholi from ₹58 L.\n\nMahaRERA P52100012345.\n\n#Wagholi #PuneHomes"
    assert reach.hashtags(row(cap)) == ["#WagholiPune", "#FlatsInPune", "#PuneProperty", "#MahaRERA", "#WagholiHomes"]
    assert reach.hashtags(row(cap, "facebook_page")) == ["#WagholiPune", "#FlatsInPune", "#PuneProperty"]


def test_a_daily_project_reel_takes_its_project_from_the_creative():
    p = {"name": "Kolte Patil Ivy", "locality": "Wagholi", "bhk_options": [{"bhk": 2}], "rera_no": "P52100099999"}
    r = row("Kolte Patil Ivy, Wagholi: ₹65 L to 80 L, 2 BHK.\n\n#Pune #Wagholi #MahaRERA", slug="project-x",
            creative={"source": "agentprojects", "template": "project", "project": p}, area="wagholi")
    assert reach.hashtags(r) == ["#WagholiPune", "#KoltePatilIvy", "#FlatsInPune", "#PuneProperty", "#MahaRERA"]


def test_an_agent_reel_keeps_agent_tags():
    reel = row("Agents in Ranjangaon: buyers ask us about plots daily. Join Avasetu.\n\n#PuneAgents #RealEstateAgent",
               slug="agentreel-3", creative={"source": "agent_reels"})
    assert reach.hashtags(reel) == reach.AGENT_TAGS
    assert reach.hashtags({**reel, "channel": "facebook_page"}) == reach.AGENT_TAGS[:3]


def test_a_news_post_keeps_its_topic_tag_and_drops_areas_it_does_not_mention():
    news = row("Metro line 3 reaches Hinjewadi by March.\n\nWhat it means for buyers.\n\n"
               "#Pune #Avasetu #Kharadi #Wagholi #PuneInfrastructure", slug="news-metro")
    tags = reach.hashtags(news)
    assert tags == ["#HinjewadiPune", "#PuneProperty", "#Hinjawadi", "#PuneInfrastructure", "#PuneHomes"]
    assert not {"#Kharadi", "#Wagholi"} & set(tags)


def test_a_guide_keeps_its_own_topic_tags():
    guide = row("Stamp duty in Pune: what you pay on a 60 L home.\n\n#StampDuty #HomeBuyingTips #PuneHomes", slug="guide-stamp")
    assert reach.hashtags(guide)[:3] == ["#StampDuty", "#PuneProperty", "#HomeBuyingTips"]


def test_tags_are_deduplicated_whatever_their_case():
    cap = "Gulmohar City, Ranjangaon.\n\n#ranjangaon #GULMOHARCITY #plotsinpune #maharera"
    tags = reach.hashtags(campaign(cap))
    assert [t.lower() for t in tags] == ["#ranjangaon", "#gulmoharcity", "#plotsinpune", "#puneproperty", "#maharera"]


def test_a_locality_outside_our_areas_has_its_own_location_variable(monkeypatch):
    monkeypatch.setenv("IG_LOCATION_PUNE", "111")
    monkeypatch.delenv("IG_LOCATION_RANJANGAON", raising=False)
    assert reach.location_id(campaign()) == "111"
    monkeypatch.setenv("IG_LOCATION_RANJANGAON", "555")
    assert reach.location_id(campaign()) == "555"
    assert reach.location_env("Shirur Pune") == "IG_LOCATION_SHIRUR_PUNE"
