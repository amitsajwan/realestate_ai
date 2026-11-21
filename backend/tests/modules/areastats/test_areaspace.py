"""areastats.areaspace: each area from space, month by month, the project pages' timeline made for a whole area: a frame of
a few kilometres around its middle, a median picture a dry month, Gemini's checked line a season given the area's MahaRERA
counts (the code's own sentence behind its summary), a video with no ring, and a few areas a day within the request budget."""
from datetime import date, datetime, timezone

import numpy as np

from app.core import areas
from app.modules.areastats import areaspace as asp, fromabove as fa, pictures
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 11, 21, 6, 0, tzinfo=timezone.utc)
fa.GEMINI_RETRY_S = 0   # no real wait for a busy Gemini in tests
asp.PX = 40             # small pictures: the tests are about what is asked and kept, not the pixels


def month_arrays(px, green, clear=True, shade=120):
    rgb = np.full((px, px, 3), shade, np.uint8)
    ir = np.zeros((px, px, 3), np.uint8)
    ir[: px * green // 100, :, 0], ir[: px * green // 100, :, 1] = 200, 40     # the top `green`% of rows under plants
    ir[px * green // 100:, :, 0], ir[px * green // 100:, :, 1] = 90, 80
    return {"rgb": rgb, "ir": ir, "n": np.full((px, px), 3 if clear else 0, np.uint8)}


class Sat:
    """Copernicus as the area pass sees it: every dry month clear, plant cover falling a few points a year from 60%."""

    def __init__(self, left=10_000, cloudy=()):
        self.left, self.used, self.cloudy, self.asked, self.sizes = left, 0, set(cloudy), [], set()

    def month(self, box, start, end, px=fa.PX):
        if self.left <= 0:
            raise fa.Budget("spent")
        self.left -= 1
        self.used += 1
        self.asked.append(start[:7])
        self.sizes.add(px)
        return month_arrays(px, 60 - 5 * (int(start[:4]) - 2019), start[:7] not in self.cloudy, shade=100 + int(start[2:4]) * 5)


class Gemini:
    def __init__(self, line="New blocks of buildings in the north-east.", summary="Fields in the east gave way to buildings.",
                 answer=True):
        self.line, self.summary, self.answer, self.calls, self.systems = line, summary, answer, [], []

    async def json(self, system, content):
        self.calls.append(content)
        self.systems.append(system)
        if not self.answer:
            return None
        labels = [c["text"].split(",")[0] for c in content if c["type"] == "text" and ", true colour" in c.get("text", "")]
        return {"seasons": {lab: self.line for lab in labels}, "summary": self.summary}


def render(name, place, shots, story, credit, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"mp4")
    poster = out.with_suffix(".webp")
    shots[-1][1].save(poster, "WEBP")
    render.called = (name, place, shots, story)
    return out, poster


async def seeded():
    store = Store(FakeDb())
    for i, year in enumerate((2019, 2022, 2022, 2024)):
        await store.projects.insert_one({"_id": f"P{i}", "name": f"P{i}", "locality": "kharadi",
                                         "registered_on": f"{year}-05-01", "completion_now": "2028-12-31"})
    return store


def test_each_areas_frame_is_a_square_around_its_middle_a_few_kilometres_wide():
    for a in areas.AREAS:
        (lat, lon), side, box = asp.frame(a.key)
        s, w, n, e = pictures.box_for(a.key)
        assert asp.SIDE_MIN_M <= side <= asp.SIDE_MAX_M
        assert abs(lat - (s + n) / 2) < 1e-4 and abs(lon - (w + e) / 2) < 1e-4
        assert abs((box[2] - box[0]) * pictures.KM_PER_DEG * 1000 - side) < 1
    assert asp.frame("wagholi")[1] == asp.SIDE_MAX_M        # 7.6 km of boundary: held to 6 km, 10 m a pixel
    assert asp.frame("keshav_nagar")[1] == asp.SIDE_MIN_M


def test_plant_cover_is_measured_over_the_whole_picture():
    assert asp.cover(month_arrays(40, 60)["ir"]) == 60 and asp.cover(month_arrays(40, 0)["ir"]) == 0


def test_an_area_is_looked_at_again_each_season_and_under_new_rules():
    assert asp.due(None, NOW)
    done = {"version": asp.VERSION, "at": datetime(2026, 11, 1, tzinfo=timezone.utc)}
    assert not asp.due(done, NOW)
    assert asp.due({**done, "at": datetime(2026, 8, 1, tzinfo=timezone.utc)}, NOW)
    assert asp.due({**done, "version": asp.VERSION - 1}, NOW)
    assert not asp.due({**done, "none": True, "at": datetime(2026, 8, 1, tzinfo=timezone.utc)}, NOW)


async def test_the_pass_keeps_an_areas_years_season_lines_and_video_with_gemini_given_its_maharera_counts(tmp_path):
    asp.configure(render=render)
    store = await seeded()
    gem, sat = Gemini(), Sat()
    got = await asp.refresh(store, NOW, sat=sat, ask=gem, out_dir=tmp_path)
    assert got["done"] == asp.LOOKS_PER_DAY and got["stopped"] is None and sat.sizes == {asp.PX}
    rec = await asp.AreaSpace(store.db).get("kharadi")
    assert rec["story"] == "Fields in the east gave way to buildings." and rec["side_m"] == asp.frame("kharadi")[1]
    assert [f["year"] for f in rec["frames"]] == list(range(2019, 2027))
    assert rec["seasons"][0] == {"label": "Jan-Mar 2019", "day": "2019-01-01", "line": "New blocks of buildings in the north-east."}
    told = gem.calls[0][0]["text"]
    assert "Area: Kharadi, Pune" in told and "2022: 2" in told and "2024: 1" in told
    assert "a square 5.5 km\nacross" in gem.systems[0]                    # Kharadi's 5.5 km frame, said to Gemini
    assert render.called[:2] == ("Upper Kharadi", "Pune")                 # the last area drawn, named, with no pin
    assert (tmp_path / "kharadi" / "2024.webp").is_file() and (tmp_path / "kharadi" / "months.mp4").is_file()
    view = await asp.one(store.db, "kharadi")
    assert view["area"]["slug"] == "kharadi" and view["video"]["src"] == "/uploads/" + rec["video"]["path"]
    assert view["frames"][0]["src"].startswith("/uploads/") and "plants" not in view["frames"][0]
    assert [x["slug"] for x in await asp.every(store.db)] == ["kharadi", "upper-kharadi"]   # menu order, two a day


async def test_a_few_areas_a_day_in_menu_order_until_every_one_has_its_look(tmp_path):
    asp.configure(render=render)
    store = await seeded()
    seen = []
    for day in range(5):
        now = datetime(2026, 11, 21 + day, 6, 0, tzinfo=timezone.utc)
        await asp.refresh(store, now, sat=Sat(), ask=Gemini(), out_dir=tmp_path)
        seen.append([x["slug"] for x in await asp.every(store.db)])
    assert seen[0] == ["kharadi", "upper-kharadi"] and len(seen[1]) == 4
    assert seen[-1] == [a.slug for a in areas.AREAS]


async def test_a_line_with_a_claim_the_satellite_cannot_make_is_dropped_and_the_summary_is_the_codes_own(tmp_path):
    asp.configure(render=render)
    store = await seeded()
    await asp.refresh(store, NOW, sat=Sat(), ask=Gemini(line="Rapid progress: towers rising.", summary="Luxury towers rising."),
                      out_dir=tmp_path)
    rec = await asp.AreaSpace(store.db).get("kharadi")
    assert all(x["line"] == "" for x in rec["seasons"]) and rec["words"] == {"gemini": 0, "dropped": len(rec["seasons"]),
                                                                              "summary": False}
    assert rec["story"].startswith("Kharadi as the Sentinel-2 satellite has seen it each dry season from Jan 2019")
    assert "Plant cover across the picture went from 60% in early 2019 to 25% in early 2026" in rec["story"]
    assert (await asp.one(store.db, "kharadi"))["seasons"] == []     # an empty line is not shown


async def test_without_gemini_the_pass_stops_and_publishes_nothing(tmp_path):
    asp.configure(render=render)
    store = await seeded()
    got = await asp.refresh(store, NOW, sat=Sat(), ask=Gemini(answer=False), out_dir=tmp_path)
    assert got["stopped"]["reason"] == "gemini" and got["done"] == 0
    assert await asp.AreaSpace(store.db).get("kharadi") is None and await asp.one(store.db, "kharadi") is None
    await asp.refresh(store, datetime(2026, 11, 23, 6, 0, tzinfo=timezone.utc), sat=Sat(), ask=None, out_dir=tmp_path)
    mark = await store.status.find_one({"_id": asp.MARK})
    assert mark["stopped"]["reason"] == "gemini" and mark["stopped"]["since"] == NOW   # since the first stop


async def test_a_later_look_asks_only_for_the_months_since(tmp_path):
    asp.configure(render=render)
    store = await seeded()
    first = Sat()
    await asp.refresh(store, NOW, sat=first, ask=Gemini(), out_dir=tmp_path)
    assert first.asked[0] == "2019-01" and "2019-07" not in first.asked
    for a in areas.AREAS:   # every area looked at this season, so only kharadi and upper kharadi come due again
        if a.key not in ("kharadi", "upper_kharadi"):
            await asp.AreaSpace(store.db).save(a.key, {"version": asp.VERSION, "none": True, "at": NOW})
    later = Sat()
    await asp.refresh(store, datetime(2027, 2, 20, 6, 0, tzinfo=timezone.utc), sat=later, ask=Gemini(), out_dir=tmp_path)
    assert later.asked == ["2026-11", "2026-12", "2027-01", "2027-02"] * 2
    assert (await asp.AreaSpace(store.db).get("kharadi"))["seasons"][-1]["label"] == "Jan-Mar 2027"


async def test_too_few_clear_seasons_show_nothing_and_cost_no_gemini(tmp_path):
    asp.configure(render=render)
    store = await seeded()
    cloudy = {m for m in fa.dry_months(2019, NOW.date()) if m >= "2020-01"}
    gem = Gemini()
    got = await asp.refresh(store, NOW, sat=Sat(cloudy=cloudy), ask=gem, out_dir=tmp_path)
    assert got["none"] == asp.LOOKS_PER_DAY and gem.calls == []
    assert (await asp.AreaSpace(store.db).get("kharadi"))["none"] is True and await asp.one(store.db, "kharadi") is None


async def test_the_pass_stops_when_the_days_requests_are_spent(tmp_path):
    asp.configure(render=render)
    store = await seeded()
    got = await asp.refresh(store, NOW, budget=0, sat=Sat(), ask=Gemini(), out_dir=tmp_path)
    assert got["done"] == 0 and got["requests"] == 0


async def test_a_frame_that_changed_size_starts_its_months_afresh(tmp_path):
    folder = tmp_path / "kharadi"
    asp.save_kept(folder, (18.55, 73.95), 5500, {"months": {"2024-01": {"clear": 1.0}}})
    assert asp.load_kept(folder, (18.55, 73.95), 5500)["months"]
    assert asp.load_kept(folder, (18.55, 73.95), 6000) == {"months": {}}


def test_an_unknown_area_or_an_older_look_is_not_shown():
    assert asp.public_view(None) is None
    assert asp.public_view({"_id": "kharadi", "area": "kharadi", "version": 0, "story": "x", "where": "y", "credit": "z",
                            "frames": [{"year": 2020, "day": "2020-02-15", "path": "a", "width": 1, "height": 1}] * 3}) is None


class Quiet(Gemini):
    """Gemini as on Kharadi's first look (2026-11-21): "Little change." for most seasons, one change, and one left empty."""

    async def json(self, system, content):
        out = await super().json(system, content)
        labels = list(out["seasons"])
        out["seasons"] = {lab: "Little change." for lab in labels}
        out["seasons"][labels[3]] = "Fields cleared in the south-east."
        out["seasons"][labels[4]] = ""
        return out


async def test_a_season_with_nothing_new_has_no_line_and_gemini_compares_with_a_year_before(tmp_path):
    asp.configure(render=render)
    store = await seeded()
    gem = Quiet()
    await asp.refresh(store, NOW, sat=Sat(), ask=gem, out_dir=tmp_path)
    assert "same season a year before" in gem.systems[0] and '"Little change"' in gem.systems[0]   # named only as forbidden
    rec = await asp.AreaSpace(store.db).get("kharadi")
    assert [s["line"] for s in rec["seasons"] if s["line"]] == ["Fields cleared in the south-east."]
    assert [s[2] for s in render.called[2] if s[2]] == ["Fields cleared in the south-east."]      # nor on the video
    assert [s["line"] for s in (await asp.one(store.db, "kharadi"))["seasons"]] == ["Fields cleared in the south-east."]
