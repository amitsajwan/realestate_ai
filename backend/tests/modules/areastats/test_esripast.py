"""areastats.esripast: Esri's sharp past pictures, about one a year, found from Esri's metadata (capture dates per release)
with a galloping search, stored as release numbers and dates only, for the pages and areas showing their ground from space."""
from datetime import datetime, timezone

import httpx

from app.modules.areastats import esripast as ep, esripast_view

NOW = datetime(2026, 11, 21, 6, 0, tzinfo=timezone.utc)


def ms(day):
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp() * 1000)


# 40 monthly releases, newest first, and the capture each shows at the pin: the date only moves forward release by release
RELEASES = [(1000 + i, f"{2026 - i // 12:04d}-{12 - i % 12:02d}-01", f"https://meta.test/r{i}") for i in range(40)]
CAPTURE = {i: ("2026-04-04" if i < 5 else "2025-10-12" if i < 9 else "2025-02-02" if i < 20 else "2024-01-11" if i < 30
               else "2022-11-12") for i in range(40)}


def esri(asked):
    def answer(request):
        i = int(request.url.path.split("/")[1][1:])
        asked.append(i)
        return httpx.Response(200, json={"features": [{"attributes": {"SRC_DATE2": ms(CAPTURE[i]), "SRC_RES": 0.31,
                                                                      "NICE_DESC": "Maxar"}}]})
    return httpx.AsyncClient(transport=httpx.MockTransport(answer))


async def test_each_capture_is_found_without_asking_every_release():
    asked = []
    meta = ep.Metadata(esri(asked), 1000)
    caps = await ep.history(meta, RELEASES, 18.54, 73.96, "2021-01-01")
    assert [c["captured"] for c in caps] == ["2026-04-04", "2025-10-12", "2025-02-02", "2024-01-11", "2022-11-12"]
    assert [c["release"] for c in caps] == [1000, 1005, 1009, 1020, 1030]     # the newest release showing each
    assert meta.used < len(RELEASES)


def test_about_one_picture_a_year_over_the_last_three_years():
    caps = [{"captured": d} for d in ("2026-04-04", "2025-10-12", "2025-02-02", "2024-01-11", "2022-11-12", "2022-01-24",
                                      "2020-04-13")]
    assert [c["captured"] for c in ep.pick(caps)] == ["2026-04-04", "2025-02-02", "2024-01-11", "2022-11-12"]


def test_the_release_list_is_read_newest_first_from_2019():
    config = {"5": {"itemTitle": "World Imagery (Wayback 2018-05-16)", "metadataLayerUrl": "u1"},
              "7": {"itemTitle": "World Imagery (Wayback 2026-11-18)", "metadataLayerUrl": "u2"},
              "9": {"itemTitle": "World Imagery (Wayback 2024-01-18)", "metadataLayerUrl": "u3"}}
    assert ep.releases(config) == [(7, "2026-11-18", "u2"), (9, "2024-01-18", "u3")]


async def test_the_day_stops_when_its_questions_are_spent():
    meta = ep.Metadata(esri([]), 3)
    try:
        await ep.history(meta, RELEASES, 18.54, 73.96, "2021-01-01")
        assert False, "should stop"
    except ep.Spent:
        assert meta.used == 3


def test_a_page_shows_the_pictures_only_at_the_pin_they_were_looked_up_for():
    doc = {"esri_past": {"version": esripast_view.VERSION, "lat": 18.5447, "lon": 73.9685, "zoom": 17,
                         "shown": [{"release": 3692, "captured": "2026-04-04", "source": "Vantor", "res": 0.34},
                                   {"release": 39767, "captured": "2022-11-12", "source": "Maxar", "res": 0.31}]}}
    view = esripast_view.public_view(doc, (18.5447, 73.9685))
    assert [s["captured"] for s in view["shots"]] == ["2022-11-12", "2026-04-04"] and view["zoom"] == 17
    assert esripast_view.public_view(doc, (18.5457, 73.9685)) is None     # about 100 m away: other ground
    assert esripast_view.public_view({}, (18.5447, 73.9685)) is None


def test_a_lookup_is_redone_monthly_or_when_the_pin_moves():
    old = {"version": esripast_view.VERSION, "at": datetime(2026, 11, 1, tzinfo=timezone.utc), "lat": 18.5447, "lon": 73.9685}
    assert not ep.due(old, (18.5447, 73.9685), NOW)
    assert ep.due(old, (18.5547, 73.9685), NOW)
    assert ep.due({**old, "at": datetime(2026, 10, 1, tzinfo=timezone.utc)}, (18.5447, 73.9685), NOW)


def test_the_page_date_moves_only_when_a_new_sharp_picture_shows():
    two = {"shown": [{"captured": "2026-04-04"}, {"captured": "2025-02-02"}]}
    first = ep.changed_at(None, two, NOW)
    assert first == NOW
    later = datetime(2026, 12, 21, tzinfo=timezone.utc)
    assert ep.changed_at({**two, "changed_at": NOW}, two, later) == NOW                       # the same pictures
    newer = {"shown": [{"captured": "2026-10-12"}, {"captured": "2025-02-02"}]}
    assert ep.changed_at({**two, "changed_at": NOW}, newer, later) == later                   # a new capture
    from app.modules.areastats import pages
    base = {"page_text_at": datetime(2026, 11, 1, tzinfo=timezone.utc)}
    assert pages.page_updated({**base, "esri_past": {**two, "changed_at": NOW}}).startswith("2026-11-21")
    assert pages.page_updated({**base, "esri_past": {"shown": [{"captured": "2026-04-04"}], "changed_at": NOW}}).startswith("2026-11-01")


async def test_every_page_with_its_own_pin_gets_its_past_pictures_and_the_page_sends_them():
    from app.modules.areastats import pages
    from app.modules.newsroom.store import Store
    from ..fakes import FakeDb
    store = Store(FakeDb())
    pin = {"geo": {"lat": 18.5447, "lon": 73.9685, "located_from": "google"}, "enrichment": {"steps": {"places": {"ok": True}}}}
    page = {"registered_on": "2022-08-10", "completion_now": "2028-12-31", "project_type": "Residential", "locality": "kharadi",
            "in_register": True, "units_total": 80}
    await store.projects.insert_one({"_id": "P1", "regno": "P1", "name": "P1", "page_slug": "p1", **page, **pin})
    await store.projects.insert_one({"_id": "P2", "regno": "P2", "name": "P2", "page_slug": "p2", **page})   # no pin of its own
    config = {str(n): {"itemTitle": f"World Imagery (Wayback {d})", "metadataLayerUrl": u} for n, d, u in RELEASES}

    def answer(request):
        if request.url.host == "s3-us-west-2.amazonaws.com":
            return httpx.Response(200, json=config)
        i = int(request.url.path.split("/")[1][1:])
        return httpx.Response(200, json={"features": [{"attributes": {"SRC_DATE2": ms(CAPTURE[i]), "SRC_RES": 0.31, "NICE_DESC": "Maxar"}}]})

    got = await ep.refresh(store, NOW, client=httpx.AsyncClient(transport=httpx.MockTransport(answer)))
    assert got["done"] == 1 and got["due"] == 1        # a small page counts too; a page without its own pin does not
    rec = (await store.projects.find_one({"_id": "P1"}))["esri_past"]
    assert [s["captured"] for s in rec["shown"]] == ["2026-04-04", "2025-02-02", "2024-01-11", "2022-11-12"] and rec["changed_at"] == NOW
    sent = pages.view(await store.projects.find_one({"_id": "P1"}), [])["esri_past"]
    assert sent["zoom"] == ep.PROJECT_ZOOM and [s["release"] for s in sent["shots"]] == [1030, 1020, 1009, 1000]
    assert await ep.refresh(store, NOW, client=httpx.AsyncClient(transport=httpx.MockTransport(answer))) is None   # once a day
