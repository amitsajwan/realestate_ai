"""PF-4 surroundings, PF-7 calculators and CA-1 campaign angles."""
from app.modules.creative.guards import problems_in
from app.modules.propertyfacts import calc, campaign, surroundings
from app.modules.propertyfacts.facts import Reading, sheet

LAT, LON = 18.7536, 74.2446


def test_calculators():
    assert calc.per_sqft(3230000, 1927) == 1676
    assert calc.guntha(1927) == 1.77
    assert calc.emi(2584000, 8.5, 20) == 22425
    rs = {r.key: r.value for r in calc.readings({"price_inr": 3230000, "plot_sqft": 1927})}
    assert rs["emi"] == {"emi": 22425, "loan": 2584000, "rate": 8.5, "years": 20} and rs["plot_sqm"] == 179
    assert "emi" not in {r.key for r in calc.readings({"price_inr": 25000, "transaction": "rent"})}


def test_overpass_keeps_the_three_nearest_named_per_category():
    els = [{"type": "node", "id": i, "lat": LAT + i * 0.01, "lon": LON, "tags": {"amenity": "school", "name": f"School {i}"}}
           for i in range(1, 5)] + [{"type": "node", "id": 9, "lat": LAT, "lon": LON, "tags": {"amenity": "school"}}]
    best = surroundings.from_overpass(els, LAT, LON)
    assert [i["name"] for i in best["school"]] == ["School 1", "School 2", "School 3"]


async def test_nominatim_is_the_fallback_when_overpass_fails():
    async def get_json(url, params):
        if url == surroundings.OVERPASS:
            return None  # busy or refused
        if params["q"] == "industrial":
            return [{"name": "IndoSpace Industrial Park Ranjangaon", "category": "landuse", "type": "industrial",
                     "lat": "18.77", "lon": "74.26", "osm_type": "way", "osm_id": 5}]
        if params["q"] == "temple":
            return [{"name": "Mahaganapati Temple", "category": "amenity", "type": "place_of_worship", "lat": "18.76", "lon": "74.25"}]
        return []
    rs, notes = await surroundings.around(get_json, LAT, LON)
    got = {r.key: r.value for r in rs}
    assert got["nearby.industry"][0]["name"] == "IndoSpace Industrial Park Ranjangaon" and "nearby.temple" in got
    assert notes and "hospital" in notes[0]


def gulmohar():
    rs = [Reading(k, v, "listing") for k, v in dict(project_name="Gulmohar City", locality="Ranjangaon", property_type="plot",
                                                     transaction="sale", price_inr=3230000, plot_sqft=1927).items()]
    rs += [Reading(k, v, "maharera") for k, v in dict(rera_no="P52100076768", possession_now="2029-04-30",
                                                       possession_at_registration="2028-12-31", units_total=123,
                                                       registered_on="2024-06-28").items()]
    rs += [Reading("possession_moved_months", 4, "calc"),
           Reading("nearby.hospital", [{"name": "Narwade Hospital", "km": 0.4}], "osm"),
           Reading("nearby.industry", [{"name": "IndoSpace Industrial Park Ranjangaon", "km": 3.0},
                                       {"name": "Maharashtra Industrial Development Corporation", "km": 5.2}], "osm")]
    rs += calc.readings({"price_inr": 3230000, "plot_sqft": 1927, "transaction": "sale"})
    return sheet(rs)


def test_plan_uses_every_angle_the_facts_support():
    ids = [aid for aid, _ in campaign.plan(gulmohar())]
    assert ids == [a.id for a in campaign.ANGLES]
    b = dict(campaign.plan(gulmohar()))
    assert b["price_reveal"].kicker == "GULMOHAR CITY" and "#Ranjangaon" in b["price_reveal"].hashtags
    assert b["possession"].truth == "MahaRERA now shows 30 Apr 2029 for Gulmohar City."
    for aid, brief in campaign.plan(gulmohar()):   # every hand-written hook is itself guard-clean
        hook = next(iter(brief.hooks.values()), "")
        assert problems_in(hook, brief.corpus()) == [], (aid, hook)


def test_thin_facts_give_fewer_angles_and_never_invent():
    thin = sheet([Reading("project_name", "Sample Heights", "listing"), Reading("locality", "Kharadi", "listing")])
    assert campaign.plan(thin) == []


async def test_make_renders_a_guard_clean_campaign(tmp_path):
    dropped = {}
    packs = await campaign.make(gulmohar(), tmp_path, dropped=dropped)
    assert len(packs) >= 10, dropped
    for aid, p in packs:
        assert p.report["ok"] and p.images and "#Ranjangaon" in p.caption
        assert "How many did you do" not in p.caption


def test_every_angle_asks_its_own_question_in_every_language():
    b = dict(campaign.plan(gulmohar()))
    for aid, brief in b.items():
        assert set(brief.asks) == {"en", "mr", "hi"}, aid
        for text in brief.asks.values():
            assert "?" in text and problems_in(text, brief.corpus()) == [], (aid, text)
    assert b["emi"].asks["en"] == "What EMI did you plan for? Tell us below."
    assert len({brief.asks["en"] for brief in b.values()}) == len(b)        # no two posts ask the same thing


def test_an_agents_cards_carry_the_listing_price_and_maharera_number():
    from app.modules.creative.models import CardBrand
    agent = CardBrand("House Deal", "Call / WhatsApp +91 99219 93099", phone="+91 99219 93099")
    for _, brief in campaign.plan(gulmohar(), card_brand=agent, language="mr"):
        assert brief.card_brand.price == "₹32.3 lakh" and brief.card_brand.rera == "P52100076768"
        assert brief.link_line.endswith("बायोमधील लिंक.") and "Gulmohar City, रांजणगाव" in brief.link_line
    assert all(b.card_brand is None for _, b in campaign.plan(gulmohar()))
