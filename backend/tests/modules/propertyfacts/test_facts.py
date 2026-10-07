from app.modules.propertyfacts.facts import Reading, conflicts, decide, same, sheet, usable


def R(value, source, key="k"):
    return Reading(key, value, source)


def test_same_text_and_numbers():
    assert same("Gulmohar  City", "gulmohar city")
    assert same(3230000, 3300000)          # within 5%
    assert not same(3230000, 3470000)
    assert same(["Gym", "Garden"], ["garden", "gym"])
    assert not same(True, 1)


def test_official_wins_and_keeps_the_disagreeing_portal():
    f = decide("k", [R("2028-12", "99acres"), R("2029-04-30", "maharera"), R("2029-04-30", "magicbricks")])
    assert f.level == "official" and f.value == "2029-04-30" and f.usable
    assert f.sources == ["magicbricks", "maharera"] and [r.source for r in f.disagree] == ["99acres"]


def test_listing_is_the_agents_own_offer():
    assert decide("k", [R(8500000, "listing")]).level == "official"


def test_measured_corroborated_single_conflict():
    assert decide("k", [R(4.2, "osm")]).level == "measured"
    assert decide("k", [R(3230000, "99acres"), R(3250000, "magicbricks")]).level == "corroborated"
    assert decide("k", [R(3230000, "99acres"), R(3230000, "99acres")]).level == "single"   # one source twice is still one
    c = decide("k", [R("ready", "99acres"), R("under construction", "magicbricks")])
    assert c.level == "conflict" and not c.usable


def test_two_official_readings_that_disagree_are_a_conflict():
    assert decide("k", [R("P52100076768", "listing"), R("P52100077275", "maharera")]).level == "conflict"


def test_empty_values_are_ignored():
    assert decide("k", [R("", "maharera"), R(None, "osm")]) is None


def test_sheet_usable_and_conflicts():
    rs = [R("Shirur", "maharera", "taluka"), R("Shirur", "osm", "taluka"), R(1800, "99acres", "rate"),
          R("ready", "99acres", "status"), R("2028", "housing", "status")]
    s = sheet(rs)
    assert list(s) == ["taluka", "rate", "status"]
    assert list(usable(s)) == ["taluka"]
    assert [f.key for f in conflicts(s)] == ["status"]
