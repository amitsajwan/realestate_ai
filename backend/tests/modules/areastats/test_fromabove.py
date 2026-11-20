"""areastats.fromabove: every page the satellite can say something true about gets its site from above by itself, within the
free Copernicus quota; pages.view shows it only at the pin it was taken at."""
import io
from datetime import date, datetime, timezone

import httpx
from PIL import Image

from app.modules.areastats import fromabove as fa, fromabove_view, pages, sitepics as s
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc)
PIN = {"geo": {"lat": 18.5447, "lon": 73.9685, "located_from": "google"}, "enrichment": {"steps": {"places": {"ok": True}}}}
PAGE = {"registered_on": "2023-01-10", "completion_now": "2028-12-31", "project_type": "Residential", "locality": "kharadi",
        "news": [], "in_register": True, "promoter": "Some Builder", "units_total": 648}


def class_png(cls: int, haze: int = 40, px: int = s.FRAME_PX) -> bytes:
    img = Image.merge("LA", (Image.new("L", (px, px), cls), Image.new("L", (px, px), haze)))
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


def colour_png() -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (300, 300), (150, 120, 100)).save(out, "PNG")
    return out.getvalue()


class Sat:
    """Copernicus as the pass sees it: a pass on the 10th of every month, the ground green until 2023, then built over."""

    def __init__(self, left=10_000, built_from="2023-06"):
        self.left, self.used, self.built_from, self.colour_days = left, 0, built_from, []

    def _spend(self):
        if self.left <= 0:
            raise fa.Budget("spent")
        self.left -= 1
        self.used += 1

    def passes(self, box, start, end):
        self._spend()
        out, d = [], date.fromisoformat(start)
        while d <= date.fromisoformat(end):
            out.append({"properties": {"datetime": f"{d.isoformat()[:8]}10T05:30:00Z", "eo:cloud_cover": 3.0}})
            d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        return out

    def classes(self, box, day):
        self._spend()
        return class_png(s.BUILT if day[:7] >= self.built_from else s.GREEN)

    def colour(self, box, day):
        self._spend()
        self.colour_days.append(day)
        return colour_png()


async def seeded(*docs):
    store = Store(FakeDb())
    for regno, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": regno, "page_slug": regno.lower(), **PAGE, **extra})
    return store


def render(name, place, shots, story, credit, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"mp4")
    poster = out.with_suffix(".webp")
    shots[-1][1].save(poster, "WEBP")
    return out, poster


def test_only_large_unfinished_projects_with_their_own_pin_are_looked_at():
    big = {"_id": "P1", **PAGE, **PIN}
    assert fa.due(big, [big], NOW) == (18.5447, 73.9685)
    small = {**big, "units_total": 120}
    assert fa.due(small, [small], NOW) is None
    # a project split into registrations counts all its homes
    parts = [small, {"_id": "P2", "units_total": 200, "cluster_primary": "P1"}]
    assert fa.due(small, parts, NOW) == (18.5447, 73.9685)
    assert fa.due({**big, "geo": {**big["geo"], "located_from": "locality"}}, [big], NOW) is None   # an area's centre
    assert fa.due({**big, "cluster_primary": "P9"}, [big], NOW) is None                            # its page is P9's
    assert fa.due({**big, "completion_now": "2024-03-31"}, [big], NOW) is None                      # finished
    done = {**big, "from_above": {"lat": 18.5447, "lon": 73.9685, "at": datetime(2026, 3, 1, tzinfo=timezone.utc)}}
    assert fa.due(done, [done], NOW) is None
    moved = {**done, "geo": {**big["geo"], "lat": 18.5457}}
    assert fa.due(moved, [moved], NOW) == (18.5457, 73.9685)                                        # a new pin: new pictures


def test_months_are_grouped_least_cloudy_first_and_the_monsoon_left_out():
    feats = [{"properties": {"datetime": d + "T05:30:00Z", "eo:cloud_cover": c}}
             for d, c in (("2024-01-05", 8.0), ("2024-01-15", 1.0), ("2024-07-10", 0.0), ("2024-10-02", 5.0))]
    assert fa.by_month(feats) == {"2024-01": ["2024-01-15", "2024-01-05"], "2024-10": ["2024-10-02"]}
    assert fa.seasons(2021, date(2026, 11, 20))[:2] == [("2021-01-01", "2021-05-31"), ("2021-10-01", "2022-05-31")]
    assert fa.seasons(2021, date(2026, 11, 20))[-1] == ("2026-10-01", "2026-11-20")


def test_one_class_map_a_pass_gives_the_months_picture_and_the_years_measure():
    seen = fa.look(Sat(), s.box_around(18.5447, 73.9685, s.FRAME_SIDE_M), date(2026, 11, 20))
    assert seen.months[0]["day"] == "2021-01-10" and seen.months[-1]["day"] == "2026-11-10"
    assert all(int(m["day"][5:7]) in s.DRY_MONTHS for m in seen.months)
    assert [(y["day"], y["built"]) for y in seen.years][:3] == [("2021-01-10", 0), ("2022-01-10", 0), ("2023-01-10", 0)]
    assert seen.years[-1]["built"] == 100


async def test_the_pass_stores_pictures_sentence_and_loop_hottest_first_in_our_areas(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", {**PIN, "hot_score": 1}), ("P2", {**PIN, "hot_score": 9, "locality": "", "pune_place": "charholi", "pune_place_name": "Charholi"}),
                         ("P3", {**PIN, "hot_score": 5}))
    sat = Sat()
    got = await fa.refresh(store, NOW, budget=1, sat=sat, out_dir=tmp_path)
    assert got["done"] == 1 and got["due"] == 3  # the day's budget is reached inside the first project: it finishes, no other starts
    p3 = (await store.projects.find_one({"_id": "P3"}))["from_above"]                 # our area, hotter than P1
    assert (await store.projects.find_one({"_id": "P2"})).get("from_above") is None   # hottest, but outside our areas: after them
    got = await fa.refresh(store, NOW, budget=10_000, sat=sat, out_dir=tmp_path, force=True)
    assert got["done"] == 2 and got["due"] == 2
    assert p3["story"].startswith("Within 100 m of the map pin") and p3["credit"].startswith(s.CREDIT)
    assert [f["year"] for f in p3["frames"]] == [2021, 2022, 2023, 2024, 2025, 2026]
    assert (tmp_path / "p3" / "2024.webp").is_file() and p3["video"]["path"].endswith("p3/months.mp4")
    assert await fa.refresh(store, NOW, sat=Sat()) is None          # once a day


async def test_a_site_with_no_change_is_recorded_as_such_and_fetches_no_pictures(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN))
    sat = Sat(built_from="2099-01")
    got = await fa.refresh(store, NOW, sat=sat, out_dir=tmp_path)
    rec = (await store.projects.find_one({"_id": "P1"}))["from_above"]
    assert got["none"] == 1 and rec["none"] is True and sat.colour_days == []
    assert fromabove_view.public_view({"from_above": rec}, (18.5447, 73.9685)) is None


async def test_the_pass_stops_when_the_days_requests_are_spent(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN), ("P2", PIN))
    got = await fa.refresh(store, NOW, budget=0, sat=Sat(), out_dir=tmp_path)
    assert got["done"] == 0 and got["requests"] == 0          # the day's budget is spent: nothing starts
    got = await fa.refresh(store, NOW, budget=10_000, sat=Sat(left=40), out_dir=tmp_path, force=True)
    assert got["done"] == 0 and got["failed"] == 0             # Copernicus's ceiling reached mid-project: stop, try tomorrow
    assert (await store.projects.find_one({"_id": "P1"})).get("from_above") is None


async def test_the_page_shows_it_only_at_the_pin_it_was_taken_at(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN))
    await fa.refresh(store, NOW, sat=Sat(), out_dir=tmp_path)
    doc = await store.projects.find_one({"_id": "P1"})
    shown = pages.view(doc, [])["from_above"]
    assert shown["frames"][0]["src"].startswith("/uploads/") and shown["video"]["src"].endswith("/months.mp4")
    assert "bare" not in shown["frames"][0] and "path" not in shown["frames"][0]
    moved = {**doc, "geo": {**doc["geo"], "lat": 18.5457}}
    assert pages.view(moved, [])["from_above"] is None


def test_an_expired_token_is_renewed_and_the_call_made_again():
    seen = []

    def answer(request):
        seen.append(request.headers["Authorization"])
        ok = request.headers["Authorization"] == "Bearer fresh"
        return httpx.Response(200 if ok else 401, json={"features": []})

    sat = fa.Copernicus(httpx.Client(transport=httpx.MockTransport(answer)), "stale", 10, renew=lambda: "fresh")
    assert sat.passes(s.box_around(18.5, 73.9, 600), "2025-01-01", "2025-05-31") == []
    assert seen == ["Bearer stale", "Bearer fresh"] and sat.auth == "fresh" and sat.used == 1


async def test_a_project_is_not_stored_with_a_years_picture_missing(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN))

    class NoColourIn2024(Sat):
        def colour(self, box, day):
            return None if day.startswith("2024-01") else super().colour(box, day)

    got = await fa.refresh(store, NOW, sat=NoColourIn2024(), out_dir=tmp_path)
    assert got["failed"] == 1 and got["done"] == 0
    assert (await store.projects.find_one({"_id": "P1"})).get("from_above") is None   # tried again next round


def test_the_sitemap_date_moves_when_the_site_from_above_goes_on_the_page_and_not_for_a_look_with_nothing_to_show():
    base = {"page_text_at": datetime(2026, 11, 17, 19, 35, tzinfo=timezone.utc), "details_ok": False}
    assert pages.page_updated(base).startswith("2026-11-17")
    shown = {**base, "from_above": {"story": "Within 100 m of the map pin, ...", "at": NOW}}
    assert pages.page_updated(shown).startswith("2026-11-20")
    nothing = {**base, "from_above": {"none": True, "at": NOW}}
    assert pages.page_updated(nothing).startswith("2026-11-17")
