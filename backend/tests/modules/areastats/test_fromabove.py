"""areastats.fromabove: every page the satellite can say something true about gets its site from above by itself: a median
picture a dry month, seasons made from them, Gemini's line a season (checked, with the code's own line behind it), and a
stop, said in admin health, when Gemini does not answer or every Copernicus account is spent."""
import io
import tarfile
from datetime import date, datetime, timezone

import httpx
import numpy as np
from PIL import Image

from app.modules.admin import health
from app.modules.areastats import fromabove as fa, fromabove_view, pages, sitepics as s
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc)
fa.GEMINI_RETRY_S = 0   # no real wait for a busy Gemini in tests
PIN = {"geo": {"lat": 18.5447, "lon": 73.9685, "located_from": "google"}, "enrichment": {"steps": {"places": {"ok": True}}}}
PAGE = {"registered_on": "2022-08-10", "completion_now": "2028-12-31", "project_type": "Residential", "locality": "kharadi",
        "news": [], "in_register": True, "promoter": "Some Builder", "units_total": 648,
        "buildings": [{"name": "Tower A", "floors": 28}, {"name": "Tower B", "floors": 28}]}


def month_arrays(green: bool, clear: bool = True, shade: int = 120):
    rgb = np.full((fa.PX, fa.PX, 3), shade, np.uint8)
    ir = np.zeros((fa.PX, fa.PX, 3), np.uint8)
    ir[..., 0], ir[..., 1] = (200, 40) if green else (90, 80)      # near-infrared, red: plants or not
    n = np.full((fa.PX, fa.PX), 3 if clear else 0, np.uint8)
    return {"rgb": rgb, "ir": ir, "n": n}


class Sat:
    """Copernicus as the pass sees it: every dry month clear, plants until `cleared` (a month), then gone."""

    def __init__(self, left=10_000, cleared="2023-06", cloudy=()):
        self.left, self.used, self.cleared, self.cloudy, self.asked, self.switched = left, 0, cleared, set(cloudy), [], []

    def month(self, box, start, end):
        if self.left <= 0:
            raise fa.Budget("spent")
        self.left -= 1
        self.used += 1
        self.asked.append(start[:7])
        return month_arrays(start[:7] < self.cleared, start[:7] not in self.cloudy, shade=100 + int(start[2:4]) * 5)


class Gemini:
    """Gemini as the pass asks it: a line for every season label it is shown, a summary and a pin check."""

    def __init__(self, line="Ground cleared inside the ring.", summary="Plants cleared after the Aug 2022 registration.",
                 pin="ok", answer=True):
        self.line, self.summary, self.pin, self.answer, self.calls = line, summary, pin, answer, []

    async def json(self, system, content):
        self.calls.append(content)
        if not self.answer:
            return None
        labels = [c["text"].split(",")[0] for c in content if c["type"] == "text" and ", true colour" in c.get("text", "")]
        return {"seasons": {lab: self.line for lab in labels}, "summary": self.summary, "pin": self.pin,
                "pin_reason": "buildings stood there before the registration" if self.pin == "doubtful" else ""}


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
    render.shots = shots
    return out, poster


def test_only_large_unfinished_projects_with_their_own_pin_and_page_are_looked_at():
    big = {"_id": "P1", **PAGE, **PIN}
    assert fa.due(big, [big], NOW) == (18.5447, 73.9685)
    small = {**big, "units_total": 120}
    assert fa.due(small, [small], NOW) is None
    assert fa.due(small, [small, {"_id": "P2", "units_total": 200, "cluster_primary": "P1"}], NOW) == (18.5447, 73.9685)
    assert fa.due({**big, "geo": {**big["geo"], "located_from": "locality"}}, [big], NOW) is None   # an area's centre
    assert fa.due({**big, "completion_now": "2024-03-31"}, [big], NOW) is None                      # finished
    assert fa.due({**big, "cluster_primary": "P9"}, [big], NOW) is None                            # its page is P9's
    done = {**big, "from_above": {"lat": 18.5447, "lon": 73.9685, "at": datetime(2026, 11, 1, tzinfo=timezone.utc),
                                  "version": fa.LOOK_VERSION}}
    assert fa.due(done, [done], NOW) is None
    older_rules = {**big, "from_above": {**done["from_above"], "version": 3}}
    assert fa.due(older_rules, [older_rules], NOW) == (18.5447, 73.9685)
    a_season_ago = {**big, "from_above": {**done["from_above"], "at": datetime(2026, 8, 1, tzinfo=timezone.utc)}}
    assert fa.due(a_season_ago, [a_season_ago], NOW) == (18.5447, 73.9685)


def test_parallel_runs_split_the_pages_without_overlap():
    regnos = [f"P5210{i:07d}" for i in range(200)]
    a = {r for r in regnos if fa.in_shard(r, (0, 2))}
    b = {r for r in regnos if fa.in_shard(r, (1, 2))}
    assert a and b and not a & b and a | b == set(regnos)


def test_a_month_is_asked_once_and_the_month_still_running_again(tmp_path):
    sat = Sat()
    kept = fa.read_new(sat, (0, 0, 1, 1), {"months": {}}, tmp_path, date(2026, 11, 20))
    assert sat.asked[0] == "2021-01" and "2021-07" not in sat.asked and sat.asked[-1] == "2026-11"
    assert kept["partial"] == "2026-11" and kept["months"]["2021-01"]["plants"] == 100
    later = Sat()
    fa.read_new(later, (0, 0, 1, 1), kept, tmp_path, date(2026, 12, 5))
    assert later.asked == ["2026-11", "2026-12"]


def test_a_cloudy_month_is_kept_as_such_and_left_out_of_the_seasons(tmp_path):
    kept = fa.read_new(Sat(cloudy={"2024-01"}), (0, 0, 1, 1), {"months": {}}, tmp_path, date(2024, 3, 31))
    months = fa.usable(kept, tmp_path)
    assert "2024-01" not in months and "2024-02" in months
    seasons = fa.seasons(months, tmp_path)
    assert [x.label for x in seasons][-1] == "Jan-Mar 2024" and seasons[-1].months == ["2024-02", "2024-03"]


async def test_the_pass_stores_the_yearly_row_season_lines_and_video_with_gemini_given_every_fact(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", {**PIN, "hot_score": 1}), ("P2", {**PIN, "units_total": 100, "cluster_primary": "P1",
                                                                     "name": "Phase 2", "registered_on": "2024-03-01"}))
    gem = Gemini()
    got = await fa.refresh(store, NOW, sat=Sat(), ask=gem, out_dir=tmp_path)
    assert got["done"] == 1 and got["stopped"] is None
    rec = (await store.projects.find_one({"_id": "P1"}))["from_above"]
    assert rec["story"] == "Plants cleared after the Aug 2022 registration." and rec["pin"] == "ok"
    assert [f["year"] for f in rec["frames"]] == [2021, 2022, 2023, 2024, 2025, 2026]
    assert rec["seasons"][0] == {"label": "Jan-Mar 2021", "day": "2021-01-01", "line": "Ground cleared inside the ring."}
    # one picture a season, named by its season (owner 2026-11-21: month after month "looks same")
    assert rec["video"]["seasons"] == len(render.shots) == len(rec["seasons"]) < rec["video"]["months"]
    assert render.shots[0][2:] == ("Ground cleared inside the ring.", "Jan-Mar 2021")
    told = gem.calls[0][0]["text"]
    assert "registered Aug 2022" in told and "Tower A (28 floors)" in told and "Phase 2" in told   # every registration
    assert sum(1 for c in gem.calls[0] if c["type"] == "image_url") == len(rec["seasons"]) + 6   # + each year's infrared
    assert (tmp_path / "p1" / "2024.webp").is_file() and (tmp_path / "p1" / "reads.json").is_file()
    shown = pages.view(await store.projects.find_one({"_id": "P1"}), [])["from_above"]
    assert shown["seasons"][0]["line"] == "Ground cleared inside the ring." and "plants" not in shown["frames"][0]


async def test_a_line_with_a_claim_the_satellite_cannot_make_falls_back_to_the_codes_own(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN))
    await fa.refresh(store, NOW, sat=Sat(), ask=Gemini(line="Rapid progress: the 12th floor is done.",
                                                       summary="Construction well underway."), out_dir=tmp_path)
    rec = (await store.projects.find_one({"_id": "P1"}))["from_above"]
    assert not any("floor" in x["line"] or "Rapid" in x["line"] for x in rec["seasons"])
    assert {x["line"] for x in rec["seasons"]} <= {"Plants on the ground", "Plants being cleared", "Ground cleared", ""}
    assert rec["story"].startswith("The ground around the project's map pin") and rec["words"]["gemini"] == 0


async def test_without_gemini_the_pass_stops_publishes_nothing_and_health_says_so(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN), ("P2", PIN))
    got = await fa.refresh(store, NOW, sat=Sat(), ask=Gemini(answer=False), out_dir=tmp_path)
    assert got["stopped"]["reason"] == "gemini" and got["done"] == 0
    assert (await store.projects.find_one({"_id": "P1"})).get("from_above") is None
    mark = await store.status.find_one({"_id": fa.MARK})
    row = health.from_above_row(True, mark, NOW)
    assert row["status"] == health.WARN and "Gemini is not answering" in row["text"]
    later = datetime(2026, 11, 23, 6, 0, tzinfo=timezone.utc)
    await fa.refresh(store, later, sat=Sat(), ask=None, out_dir=tmp_path, force=True)
    row = health.from_above_row(True, await store.status.find_one({"_id": fa.MARK}), later)
    assert row["status"] == health.BAD and "Stopped 3.0 days" in row["text"]   # since the first stop, not the latest


async def test_a_pin_gemini_finds_doubtful_hides_the_section(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN))
    await fa.refresh(store, NOW, sat=Sat(), ask=Gemini(pin="doubtful"), out_dir=tmp_path)
    doc = await store.projects.find_one({"_id": "P1"})
    assert doc["from_above"]["pin"] == "doubtful" and doc["from_above"]["pin_reason"]
    assert pages.view(doc, [])["from_above"] is None


async def test_a_later_look_asks_only_for_the_months_since(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN))
    first = Sat()
    await fa.refresh(store, NOW, sat=first, ask=Gemini(), out_dir=tmp_path)
    later = Sat()
    await fa.refresh(store, datetime(2027, 2, 20, 6, 0, tzinfo=timezone.utc), sat=later, ask=Gemini(), out_dir=tmp_path,
                     force=True)
    assert later.asked == ["2026-11", "2026-12", "2027-01", "2027-02"] and first.used > 40
    rec = (await store.projects.find_one({"_id": "P1"}))["from_above"]
    assert rec["seasons"][-1]["label"] == "Jan-Mar 2027"


async def test_an_older_video_is_drawn_again_from_the_kept_pictures_and_lines_with_no_request_and_no_gemini(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN))
    await fa.refresh(store, NOW, sat=Sat(), ask=Gemini(), out_dir=tmp_path)
    first = (await store.projects.find_one({"_id": "P1"}))["from_above"]
    await store.set_project("P1", from_above={**first, "video": {**first["video"], "version": 3}})
    sat, gem = Sat(), Gemini(line="A different line.")
    later = datetime(2026, 11, 22, 6, 0, tzinfo=timezone.utc)
    got = await fa.refresh(store, later, sat=sat, ask=gem, out_dir=tmp_path, force=True)
    assert got["redrawn"] == 1 and sat.used == 0 and gem.calls == []
    rec = (await store.projects.find_one({"_id": "P1"}))["from_above"]
    assert rec["video"]["version"] == fa.VIDEO_VERSION and rec["at"] == first["at"] and rec["seasons"] == first["seasons"]
    assert render.shots[0][2] == "Ground cleared inside the ring."   # the stored line, not a new one
    again = await fa.refresh(store, later, sat=Sat(), ask=Gemini(), out_dir=tmp_path, force=True)
    assert again["redrawn"] == 0


async def test_a_new_launch_says_when_it_registered(tmp_path):
    fa.configure(render=render)
    store = await seeded(("NEW", {**PIN, "registered_on": "2026-03-15"}))
    await fa.refresh(store, NOW, sat=Sat(), ask=Gemini(), out_dir=tmp_path)
    rec = (await store.projects.find_one({"_id": "NEW"}))["from_above"]
    assert rec["story"].startswith("Registered with MahaRERA in Mar 2026.")


async def test_the_timeline_starts_the_year_before_the_project_first_registered(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", {**PIN, "registered_on": "2024-03-01"}),
                         ("P2", {**PIN, "units_total": 100, "cluster_primary": "P1", "registered_on": "2023-05-10"}))
    sat = Sat(cleared="2024-06")
    await fa.refresh(store, NOW, sat=sat, ask=Gemini(), out_dir=tmp_path)
    rec = (await store.projects.find_one({"_id": "P1"}))["from_above"]
    assert [f["year"] for f in rec["frames"]] == [2022, 2023, 2024, 2025, 2026]   # 2023 registration behind the page, less a year
    assert rec["seasons"][0]["label"] == "Jan-Mar 2022" and render.shots[0][0] == "2022-01-01"
    assert rec["registered"] == "2023-05-10" and min(sat.asked) == "2021-01"     # two spare years read, no more
    assert pages.view(await store.projects.find_one({"_id": "P1"}), [])["from_above"]["registered"] == "2023-05-10"


async def test_a_new_launch_still_shows_three_yearly_pictures(tmp_path):
    fa.configure(render=render)
    store = await seeded(("NEW", {**PIN, "registered_on": "2026-03-15"}))
    sat = Sat()
    await fa.refresh(store, NOW, sat=sat, ask=Gemini(), out_dir=tmp_path)
    rec = (await store.projects.find_one({"_id": "NEW"}))["from_above"]
    assert [f["year"] for f in rec["frames"]] == [2024, 2025, 2026] and min(sat.asked) == "2023-01"


async def test_an_older_look_from_2021_is_cut_to_the_window_when_redrawn_with_its_own_lines(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN))
    await fa.refresh(store, NOW, sat=Sat(), ask=Gemini(), out_dir=tmp_path)
    first = (await store.projects.find_one({"_id": "P1"}))["from_above"]
    await store.set_project("P1", registered_on="2025-01-10",
                            from_above={**first, "video": {**first["video"], "version": 4}})
    sat, gem = Sat(), Gemini()
    got = await fa.refresh(store, datetime(2026, 11, 22, 6, 0, tzinfo=timezone.utc), sat=sat, ask=gem, out_dir=tmp_path,
                           force=True)
    assert got["redrawn"] == 1 and sat.used == 0 and gem.calls == []
    rec = (await store.projects.find_one({"_id": "P1"}))["from_above"]
    assert [f["year"] for f in rec["frames"]] == [2024, 2025, 2026] and rec["seasons"][0]["label"] == "Jan-Mar 2024"
    assert rec["credit"].endswith("2024-2026") and rec["story"] == first["story"] and rec["at"] == first["at"]


async def test_too_few_clear_seasons_show_nothing_and_cost_no_gemini(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN))
    cloudy = {m for m in fa.dry_months(2021, NOW.date()) if m >= "2022-01"}
    gem = Gemini()
    await fa.refresh(store, NOW, sat=Sat(cloudy=cloudy), ask=gem, out_dir=tmp_path)
    assert (await store.projects.find_one({"_id": "P1"}))["from_above"]["none"] is True and gem.calls == []


async def test_the_pass_stops_when_the_days_requests_are_spent(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN), ("P2", PIN))
    got = await fa.refresh(store, NOW, budget=0, sat=Sat(), ask=Gemini(), out_dir=tmp_path)
    assert got["done"] == 0 and got["requests"] == 0


def tar_of(**arrays):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        for name, arr in arrays.items():
            png = io.BytesIO()
            Image.fromarray(arr).save(png, "PNG")
            info = tarfile.TarInfo(f"{name}.png")
            info.size = len(png.getvalue())
            t.addfile(info, io.BytesIO(png.getvalue()))
    return buf.getvalue()


def test_when_one_accounts_month_is_spent_the_next_account_carries_on_and_both_spent_stops():
    body = tar_of(**month_arrays(True))

    def answer(request):
        if "token" in str(request.url):
            return httpx.Response(200, json={"access_token": "t2"})
        return httpx.Response(403 if request.headers["Authorization"] == "Bearer t1" else 200, content=body)

    sat = fa.Copernicus(httpx.Client(transport=httpx.MockTransport(answer)), [("id1", "s1"), ("id2", "s2")], 10, auth="t1")
    got = sat.month(s.box_around(18.5, 73.9, 600), "2025-01-01", "2025-01-31")
    assert got is not None and got["rgb"].shape == (fa.PX, fa.PX, 3) and sat.at == 1 and sat.switched

    def refuse(request):
        if "token" in str(request.url):
            return httpx.Response(200, json={"access_token": "t"})
        return httpx.Response(402)

    sat = fa.Copernicus(httpx.Client(transport=httpx.MockTransport(refuse)), [("id1", "s1"), ("id2", "s2")], 10, auth="t")
    try:
        sat.month(s.box_around(18.5, 73.9, 600), "2025-01-01", "2025-01-31")
        assert False, "should stop"
    except fa.Budget as e:
        assert "every account" in str(e)


def test_a_line_is_checked_for_claims_and_length():
    assert fa.checked("Ground cleared; new road along the west edge.", fa.LINE_WORDS)
    for bad in ("Slabs going up fast", "Work is on track", "The 8th tower", "Rising structures appear", "x " * 30):
        assert fa.checked(bad, fa.LINE_WORDS) is None


def test_an_older_look_is_not_shown():
    doc = {"geo": {"lat": 18.5447, "lon": 73.9685}, "from_above": {"version": 3, "story": "x", "where": "y", "credit": "z",
                                                                    "lat": 18.5447, "lon": 73.9685, "frames": []}}
    assert fromabove_view.public_view(doc, (18.5447, 73.9685)) is None


def test_the_sitemap_date_moves_when_the_site_from_above_goes_on_the_page_and_not_for_a_look_with_nothing_to_show():
    base = {"page_text_at": datetime(2026, 11, 17, 19, 35, tzinfo=timezone.utc), "details_ok": False}
    assert pages.page_updated(base).startswith("2026-11-17")
    assert pages.page_updated({**base, "from_above": {"story": "The ground ...", "at": NOW}}).startswith("2026-11-20")
    assert pages.page_updated({**base, "from_above": {"none": True, "at": NOW}}).startswith("2026-11-17")


async def test_the_from_space_list_has_every_page_showing_it_for_the_video_sitemap_and_hub(tmp_path):
    fa.configure(render=render)
    store = await seeded(("P1", PIN), ("P2", PIN))
    await fa.refresh(store, NOW, sat=Sat(), ask=Gemini(), out_dir=tmp_path)
    await store.projects.update_one({"_id": "P2"}, {"$set": {"from_above.pin": "doubtful"}})
    listed = await pages.from_space(store.db)
    assert [x["slug"] for x in listed] == ["p1"]
    assert listed[0]["video"]["src"].endswith("/months.mp4") and listed[0]["years"] == [2021, 2026]
