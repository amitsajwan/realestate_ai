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
    doc = {"esri_past": {"version": esripast_view.VERSION, "lat": 18.5447, "lon": 73.9685, "zoom": 18,
                         "shown": [{"release": 3692, "captured": "2026-04-04", "source": "Vantor", "res": 0.34},
                                   {"release": 39767, "captured": "2022-11-12", "source": "Maxar", "res": 0.31}]}}
    view = esripast_view.public_view(doc, (18.5447, 73.9685))
    assert [s["captured"] for s in view["shots"]] == ["2022-11-12", "2026-04-04"] and view["zoom"] == 18
    assert esripast_view.public_view(doc, (18.5457, 73.9685)) is None     # about 100 m away: other ground
    assert esripast_view.public_view({}, (18.5447, 73.9685)) is None


def test_a_lookup_is_redone_monthly_or_when_the_pin_moves():
    old = {"version": esripast_view.VERSION, "at": datetime(2026, 11, 1, tzinfo=timezone.utc), "lat": 18.5447, "lon": 73.9685}
    assert not ep.due(old, (18.5447, 73.9685), NOW)
    assert ep.due(old, (18.5547, 73.9685), NOW)
    assert ep.due({**old, "at": datetime(2026, 10, 1, tzinfo=timezone.utc)}, (18.5447, 73.9685), NOW)
