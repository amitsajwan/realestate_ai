"""A project page's address comes from the name it is sold under, moved a few a day with the old one kept
(docs/plan/one-project-one-page.md 1c)."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import pages, spotlight

from .test_pages import FULL as _FULL, seeded

FULL = {**_FULL, "promoter": "Sky Developers LLP"}   # no brand: the address is the selling name as it is

NOW = datetime(2026, 11, 28, 6, 0, tzinfo=timezone.utc)


def test_the_address_name_is_the_selling_name_never_the_search_name_or_a_place_only_name():
    base = {"name": "KHARADI NEW PROJECT -TOWER 5", "locality": "upper_kharadi"}
    assert pages.address_name(base) is None   # only the registered name: the address stays as given
    assert pages.address_name({**base, "search_name": "Lodha Camelot Kharadi"}) is None   # the rank loop's, it changes
    assert pages.address_name({**base, "group_name": "Kharadi New Project"}) is None      # place and filler words only
    assert pages.address_name({**base, "market_name": "Lodha Camelot"}) == "Lodha Camelot"
    assert pages.address_name({**base, "market_name": "Lodha Camelot", "marketed_name_override": "Camelot by Lodha"}) == "Camelot by Lodha"
    assert pages.address_slug({**base, "market_name": "Lodha Camelot"}) == "lodha-camelot-upper-kharadi"
    assert pages.address_slug({**base, "page_slug": "x"}) == pages.base_slug(base)
    # what sites add to the selling name comes off: a tower, a trailing place, the word "Project"
    assert pages.address_name({**base, "market_name": "Majestique 27 Grand Residences Tower 1 in Balewadi"}) == "Majestique 27 Grand Residences"
    assert pages.address_name({**base, "group_name": "Geras Planet of Joy Project"}) == "Geras Planet of Joy"
    assert pages.address_name({**base, "market_name": "Life in Green"}) == "Life in Green"   # short names keep their words
    assert pages.address_name({**base, "market_name": "Ganga Amber PH"}) == "Ganga Amber"
    assert pages.address_name({**base, "market_name": "Samrajya Heights Wing GH"}) == "Samrajya Heights"
    # one word names nothing a buyer types, unless the owner chose it
    assert pages.address_name({**base, "market_name": "Bramha"}) is None
    assert pages.address_name({**base, "market_name": "Top Towers"}) == "Top Towers"   # stripping "Towers" would leave one word
    assert pages.address_name({**base, "marketed_name_override": "Sukoon"}) == "Sukoon"
    # the builder's brand in front when buyers search it that way and the name lacks it
    assert pages.address_name({**base, "market_name": "Abhilasha", "promoter": "Rohan Builders"}) == "Rohan Abhilasha"


async def test_pages_move_to_their_selling_name_a_few_a_day_least_seen_first_keeping_the_old_address():
    db, store = await seeded(
        ("P1", "Aditya Vivaaz Project Three", "upper_kharadi", {**FULL, "page_slug": "aditya-vivaaz-project-three-upper-kharadi",
                                                                 "market_name": "Aditya Vivaaz", "gsc_impressions": 900}),
        ("P2", "Sky One Building A", "upper_kharadi", {**FULL, "page_slug": "sky-one-building-a-upper-kharadi",
                                                        "market_name": "Sky One", "gsc_impressions": 3}),
        ("P3", "Rohan Abhilasha", "upper_kharadi", {**FULL, "page_slug": "rohan-abhilasha-upper-kharadi"}),   # nothing to change
        # no selling name: stays where it is even when its registered name would give another address (Godrej Ivara)
        ("P4", "Godrej Ivara", "upper_kharadi", {**FULL, "page_slug": "godrej-ivara-pune"}))
    out = await pages.rename_addresses(store, NOW, limit=1)
    assert out == {"renamed": 1, "left": 1, "day": "2026-11-28"}
    p2 = await store.project("P2")
    assert (p2["page_slug"], p2["old_slugs"], p2["address_from"]) == ("sky-one-upper-kharadi", ["sky-one-building-a-upper-kharadi"],
                                                                      "sky-one-building-a-upper-kharadi")
    assert (await pages.rename_addresses(store, NOW + timedelta(hours=2), limit=1))["renamed"] == 0   # the day's one is spent
    assert (await store.project("P4"))["page_slug"] == "godrej-ivara-pune"
    assert (await pages.rename_addresses(store, NOW + timedelta(days=1), limit=1))["renamed"] == 1
    assert (await store.project("P1"))["page_slug"] == "aditya-vivaaz-upper-kharadi"
    # the old address still serves the page, under its new address (the site answers 308)
    assert (await pages.project_page(db, "sky-one-building-a-upper-kharadi"))["slug"] == "sky-one-upper-kharadi"
    # renamed once by code: a later name never moves it again
    await store.set_project("P2", market_name="Sky One Residences")
    assert (await pages.rename_addresses(store, NOW + timedelta(days=2), limit=5))["renamed"] == 0


async def test_an_address_another_page_has_or_had_is_never_taken():
    db, store = await seeded(
        ("P1", "Sky One Building A", "upper_kharadi", {**FULL, "page_slug": "sky-one-building-a-upper-kharadi", "market_name": "Sky One"}),
        ("P2", "Sky One", "upper_kharadi", {**FULL, "page_slug": "old-sky", "old_slugs": ["sky-one-upper-kharadi"]}),
        ("P3", "Tower Two", "upper_kharadi", {**FULL, "page_slug": "tower-two-upper-kharadi", "market_name": "Tower Two",
                                               "cluster_primary": "P1"}))   # a tower serves its primary's page: never moved
    assert (await pages.rename_addresses(store, NOW, limit=5))["renamed"] == 0
    assert (await store.project("P1"))["page_slug"] == "sky-one-building-a-upper-kharadi"


async def test_nothing_moves_when_the_daily_pace_is_zero():
    db, store = await seeded(("P1", "Sky One Building A", "upper_kharadi", {**FULL, "page_slug": "sky-one-building-a-upper-kharadi",
                                                                             "market_name": "Sky One"}))
    assert (await pages.rename_addresses(store, NOW, limit=0))["renamed"] == 0
    assert (await store.project("P1"))["page_slug"] == "sky-one-building-a-upper-kharadi"


async def test_a_banner_pick_saved_under_an_old_address_still_shows_its_project():
    db, store = await seeded(("P1", "Sky One", "upper_kharadi", {**FULL, "page_slug": "sky-one-upper-kharadi",
                                                                  "old_slugs": ["sky-one-building-a-upper-kharadi"]}))
    await db.get_collection(spotlight.COLLECTION).insert_one({"_id": spotlight.DOC_ID, "auto": False,
                                                               "items": [{"slug": "sky-one-building-a-upper-kharadi"}]})
    got = await spotlight.public(db, now=NOW)
    assert [x["slug"] for x in got] == ["sky-one-upper-kharadi"]
    saved = await spotlight.set_config(db, {"items": [{"slug": "sky-one-building-a-upper-kharadi"}]}, "OWNER", NOW)
    assert [x["slug"] for x in saved["items"]] == ["sky-one-upper-kharadi"]
