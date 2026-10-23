"""Pins for the area maps by the name a project is sold under: sure ones go on the map, doubtful ones wait for the owner, a sales
gallery never counts, a rejected place is never offered again."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import areamap, mappins
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 23, 9, 0, tzinfo=timezone.utc)
PAGE = {"promoter": "Some Builder", "registered_on": "2024-01-10", "completion_now": "2029-10-30", "project_type": "Residential",
        "locality": "upper_kharadi", "news": []}
UK = areamap.MAPS["upper_kharadi"]


def place(name, lat=18.565, lon=73.968, pid=None, types=("apartment_building",)):
    return {"name": name, "address": "Upper Kharadi Main Rd, Wagholi, Pune 412207", "lat": lat, "lon": lon,
            "place_id": pid or name.replace(" ", "-"), "types": list(types)}


class Google:
    def __init__(self, answers):
        self.answers, self.queries = answers, []

    async def __call__(self, db, query, centre):
        self.queries.append(query)
        return next((v for k, v in self.answers.items() if query.startswith(k)), [])


async def seeded(*docs):
    db = FakeDb()
    store = Store(db)
    for regno, name, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": name, "page_slug": name.lower().replace(" ", "-"),
                                         **PAGE, **extra})
    return db, store


def test_a_project_is_looked_up_by_the_names_it_is_sold_under_never_by_a_working_name():
    giardino = {"name": "Kharadi Pune Phase I - Tower 1 to 4", "marketed_name_override": "Lodha Giardino", "promoter": "Lodha"}
    assert mappins.names_for(giardino)[0] == "Lodha Giardino"
    assert mappins.names_for({"name": "Kharadi New Project -Tower 5"}) == []          # nothing Google could know it by
    assert mappins.names_for({"name": "Pristine O2 World Part 3"})[0] == "Pristine O2 World Part 3".rsplit(" Part", 1)[0] \
        or "Pristine O2 World" in mappins.names_for({"name": "Pristine O2 World Part 3"})


def test_the_site_counts_a_sales_gallery_never_and_a_shared_word_only_with_the_owners_yes():
    j = lambda c, sold="Lodha Camelot": mappins.judge(c, [sold], "Lodha Developers Limited", UK)[0]   # noqa: E731
    assert j(place("Lodha Camelot, Wagholi")) == "ok"
    assert j(place("Lodha Camelot Wagholi Gallery")) == "no"            # 500 m from the site (2026-10-23)
    assert j(place("Camelot Residency")) == "doubtful"                  # shares the project's own word
    assert j(place("Lodha Giardino")) == "no"                           # only the builder's word
    assert j(place("Lodha Camelot", lat=18.70)) == "no"                 # outside the map
    assert j(place("Camelot", types=("restaurant", "food"))) == "no"


async def test_the_daily_round_pins_sure_ones_and_a_doubtful_one_waits_for_the_owner():
    db, store = await seeded(("P1", "Kharadi Pune Phase I", {"marketed_name_override": "Lodha Giardino", "hot_score": 30}),
                             ("P2", "Majestique Towers East Phase 8", {"hot_score": 40}),
                             ("P3", "Kharadi Pune P2", {"hot_score": 5}))   # nothing to search for: left alone
    google = Google({"Lodha Giardino": [place("Lodha Giardino Gallery", pid="gal"), place("Lodha Giardino, Wagholi", 18.5626, 73.9668)],
                     "Majestique Towers East": [place("Majestique Towers", 18.5588, 73.9599)]})
    mappins.configure(search=google)
    got = await mappins.refresh(store, NOW)
    assert got == {"upper_kharadi": {"auto": 1, "doubtful": 1}}
    p1 = (await store.project("P1"))["map_pin"]
    assert p1["status"] == "auto" and p1["name"] == "Lodha Giardino" and p1["google_name"] == "Lodha Giardino, Wagholi"
    assert all(q.endswith(", Upper Kharadi, Pune") for q in google.queries)
    shown = await areamap.public(db, "upper_kharadi", NOW)
    assert [i["name"] for i in shown["items"]] == ["Lodha Giardino"]           # the doubtful one is not on the map
    assert await mappins.refresh(store, NOW + timedelta(hours=1)) is None      # once a day
    waiting = await mappins.doubtful(db)
    assert [(w["regno"], w["google_name"]) for w in waiting] == [("P2", "Majestique Towers")] and "maps" in waiting[0]["maps_url"]
    await mappins.decide(db, "P2", True, "owner", NOW)
    Store_cache_clear()
    assert [i["name"] for i in (await areamap.public(db, "upper_kharadi", NOW))["items"]] == ["Majestique Towers East", "Lodha Giardino"]


async def test_a_rejected_place_is_never_offered_again_and_the_next_round_looks_for_another():
    db, store = await seeded(("P2", "Majestique Towers East Phase 8", {"hot_score": 40}))
    google = Google({"Majestique Towers East": [place("Majestique Towers", pid="wrong"), place("Majestique Towers East", pid="right")]})
    mappins.configure(search=google)
    await store.set_project("P2", map_pin={"status": "doubtful", "place_id": "wrong", "lat": 18.56, "lon": 73.96, "at": NOW})
    await mappins.decide(db, "P2", False, "owner", NOW)
    await mappins.refresh(store, NOW, force=True)
    pin = (await store.project("P2"))["map_pin"]
    assert pin["status"] == "auto" and pin["place_id"] == "right" and pin["refused"] == ["wrong"]


def Store_cache_clear():
    from app.modules.newsroom import store as s
    s._SHARED.clear()
