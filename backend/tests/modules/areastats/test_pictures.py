"""areastats.pictures: boxes for every area, the AI judge (platform.llm + budget), and the append-only `area_pictures` store
(docs/plan/area-pictures.md step 3)."""
import io
from datetime import date, datetime, timezone

import pytest
from PIL import Image

from app.core.areas import AREAS, get as area_get
from app.modules.areastats import pictures as p
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 17, 6, 0, tzinfo=timezone.utc)


def png(color=(90, 110, 80, 255), size=(40, 40), patch=None) -> bytes:
    img = Image.new("RGBA", size, color)
    if patch:
        share, fill = patch
        for x in range(size[0]):
            for y in range(int(size[1] * share)):
                img.putpixel((x, y), fill)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def svc(db=None, now=NOW, tmp_path=None) -> p.AreaPictures:
    return p.AreaPictures(db or FakeDb(), now=lambda: now, root=tmp_path)


# ---- a box for every area (item 2) --------------------------------------------------------------------------------------
def test_every_area_gets_a_box_drawn_map_then_boundary_then_a_square_around_the_middle():
    for a in AREAS:
        s, w, n, e = p.box_for(a.key)
        assert s < n and w < e

    # kharadi has a drawn map (areamap.MAPS): its box is the map's own
    from app.modules.areastats.areamap import MAPS
    assert p.box_for("kharadi") == MAPS["kharadi"].box

    # lohegaon has no drawn map but a boundary (app/core/area_bounds.py): its box is the boundary's bounding box
    from app.core import area_bounds
    poly = area_bounds.BOUNDS["lohegaon"]
    lats, lons = [v[0] for v in poly], [v[1] for v in poly]
    assert p.box_for("lohegaon") == (min(lats), min(lons), max(lats), max(lons))

    # baner has neither: a fixed square around its hand-set middle (landmarks.middle)
    from app.modules.areastats.landmarks import middle
    lat, lon, _ = middle(area_get("baner"))
    s, w, n, e = p.box_for("baner")
    assert round((s + n) / 2, 3) == round(lat, 3) and round((w + e) / 2, 3) == round(lon, 3)
    assert n - s > 0 and e - w > 0

    # an explicit box always wins
    given = (18.0, 73.0, 18.1, 73.1)
    assert p.box_for("baner", given) == given


# ---- which years an area needs (item 3) -----------------------------------------------------------------------------
def test_needed_years_wants_the_earliest_and_latest_together_on_a_fresh_area():
    today = date(2026, 11, 17)
    assert p.needed_years([], today) == [p.EARLIEST_YEAR, 2026]            # 2026's dry season (Feb-Apr) has passed
    assert p.needed_years([], date(2026, 3, 1)) == [p.EARLIEST_YEAR, 2025]  # 2026's own season is not over yet


def test_needed_years_only_wants_the_latest_once_the_earliest_is_kept():
    assert p.needed_years([2017], date(2026, 11, 17)) == [2026]
    assert p.needed_years([2017, 2025], date(2026, 11, 17)) == [2026]
    assert p.needed_years([2017, 2026], date(2026, 11, 17)) == []          # both already kept: nothing to do


# ---- the code-only checks (unchanged from the script) ----------------------------------------------------------------
def test_judge_code_refuses_no_data_and_cloud_but_reports_the_measured_share():
    img, cloud_pct = p.judge_code(png())
    assert img.size == (40, 40) and cloud_pct == 0.0
    with pytest.raises(p.Failed, match="without data"):
        p.judge_code(png(patch=(0.3, (0, 0, 0, 0))))
    with pytest.raises(p.Failed, match="cloud"):
        p.judge_code(png(patch=(0.5, (250, 250, 250, 255))))


# ---- the AI judge: strict JSON, a deterministic fallback on failure ---------------------------------------------------
class FakeAsk:
    def __init__(self, answer=None, raises=False):
        self.answer, self.raises, self.calls = answer, raises, []

    async def json(self, system, user):
        self.calls.append((system, user))
        if self.raises:
            raise RuntimeError("boom")
        return self.answer


async def test_ai_judge_reads_usable_and_notes_falls_back_to_none_on_failure():
    ask = FakeAsk({"usable": True, "clouds": "none", "haze": False, "covers_area": True, "notes": "clear"})
    out = await p.ai_judge(ask, "Kharadi", 2017, png())
    assert out == {"ok": True, "reason": "clear", "model": "gemini"}
    # the image is sent as a vision message, not folded into the cached text key as a bare string
    assert isinstance(ask.calls[0][1], list) and ask.calls[0][1][1]["type"] == "image_url"

    unusable = FakeAsk({"usable": False, "notes": "mostly haze"})
    out = await p.ai_judge(unusable, "Kharadi", 2017, png())
    assert out == {"ok": False, "reason": "mostly haze", "model": "gemini"}

    assert await p.ai_judge(None, "Kharadi", 2017, png()) is None            # no budget/provider at all
    assert await p.ai_judge(FakeAsk(None), "Kharadi", 2017, png()) is None    # the model answered nothing usable
    assert await p.ai_judge(FakeAsk(raises=True), "Kharadi", 2017, png()) is None  # the call itself failed


# ---- capture_year: retries within a season, judge-unusable moves to the next pass ------------------------------------
class FakeHttp:
    """A sequence of (catalog features, process responses) keyed by day, enough for capture_year's own tests."""
    def __init__(self, features, pngs):
        self.features, self.pngs = features, pngs

    def post(self, url, json=None, headers=None, timeout=None):
        import httpx
        if url == p.CATALOG_URL:
            return httpx.Response(200, json={"features": self.features})
        day = json["input"]["data"][0]["dataFilter"]["timeRange"]["from"][:10]
        body = self.pngs[day]
        return body if isinstance(body, httpx.Response) else httpx.Response(200, content=body, headers={"content-type": "image/png"})


def feature(day, cc):
    return {"type": "Feature", "properties": {"datetime": f"{day}T05:00:00Z", "eo:cloud_cover": cc}}


async def test_capture_year_tries_the_next_least_cloudy_pass_when_the_code_checks_fail():
    client = FakeHttp([feature("2017-02-10", 0.4), feature("2017-03-12", 1.0)],
                      {"2017-02-10": png(patch=(0.5, (250, 250, 250, 255))), "2017-03-12": png()})
    kharadi = area_get("kharadi")
    box = p.box_for("kharadi")
    got = await p.capture_year(client, "tok", box, kharadi, 2017)
    assert got is not None
    img, meta, judged = got
    assert meta["captured_on"] == "2017-03-12" and judged is None     # no ask given: no judge call, kept on code checks alone


async def test_capture_year_skips_a_pass_the_judge_calls_unusable():
    client = FakeHttp([feature("2017-02-10", 0.4), feature("2017-03-12", 1.0)],
                      {"2017-02-10": png(), "2017-03-12": png()})
    ask = FakeAsk({"usable": False, "notes": "haze"})
    kharadi = area_get("kharadi")
    box = p.box_for("kharadi")

    class TwoAnswers(FakeAsk):
        def __init__(self):
            super().__init__()
            self.n = 0

        async def json(self, system, user):
            self.n += 1
            return {"usable": self.n == 2, "notes": "ok" if self.n == 2 else "haze"}

    got = await p.capture_year(client, "tok", box, kharadi, 2017, TwoAnswers())
    assert got is not None
    _img, meta, judged = got
    assert meta["captured_on"] == "2017-03-12" and judged == {"ok": True, "reason": "ok", "model": "gemini"}


async def test_capture_year_gives_up_after_the_dry_seasons_passes_are_exhausted():
    client = FakeHttp([feature("2017-02-10", 0.4)], {"2017-02-10": png()})
    kharadi = area_get("kharadi")
    box = p.box_for("kharadi")
    always_unusable = FakeAsk({"usable": False, "notes": "haze"})
    assert await p.capture_year(client, "tok", box, kharadi, 2017, always_unusable) is None
    assert await p.capture_year(FakeHttp([], {}), "tok", box, kharadi, 2018) is None  # no pass at all


# ---- the stored record: trust, append-only, public() --------------------------------------------------------------------
KHARADI = area_get("kharadi")


async def test_a_picture_is_pending_while_untrusted_even_when_the_judge_says_ok(tmp_path):
    s = svc(tmp_path=tmp_path)
    judged_ok = {"ok": True, "reason": "clear", "model": "gemini"}
    doc = await s.add(KHARADI, 2017, Image.new("RGB", (10, 10)), "2017-03-12", 0.0, judged_ok, p.box_for("kharadi"))
    assert doc["status"] == "pending"
    assert await s.public("kharadi") == {"area": {"key": "kharadi", "name": "Kharadi", "slug": "kharadi"}, "pictures": []}


async def test_after_the_owner_approves_the_first_picture_a_later_judged_ok_picture_goes_live(tmp_path):
    s = svc(tmp_path=tmp_path)
    judged_ok = {"ok": True, "reason": "clear", "model": "gemini"}
    first = await s.add(KHARADI, 2017, Image.new("RGB", (10, 10)), "2017-03-12", 0.0, judged_ok, p.box_for("kharadi"))
    assert first["status"] == "pending"
    await s.decide(first["_id"], True, "owner1")
    assert await s.trusted() is True

    live = await s.add(KHARADI, 2026, Image.new("RGB", (10, 10)), "2026-03-01", 0.0, judged_ok, p.box_for("kharadi"))
    assert live["status"] == "live"
    pub = await s.public("kharadi")
    assert [x["year"] for x in pub["pictures"]] == [2017, 2026]
    assert pub["pictures"][1]["credit"] == "Contains modified Copernicus Sentinel data 2026"


async def test_a_picture_the_judge_doubts_stays_pending_even_when_trusted(tmp_path):
    s = svc(tmp_path=tmp_path)
    judged_ok = {"ok": True, "reason": "clear", "model": "gemini"}
    first = await s.add(KHARADI, 2017, Image.new("RGB", (10, 10)), "2017-03-12", 0.0, judged_ok, p.box_for("kharadi"))
    await s.decide(first["_id"], True, "owner1")
    judged_bad = {"ok": False, "reason": "hazy", "model": "gemini"}
    doubtful = await s.add(KHARADI, 2026, Image.new("RGB", (10, 10)), "2026-03-01", 0.0, judged_bad, p.box_for("kharadi"))
    assert doubtful["status"] == "pending"


async def test_a_model_failure_keeps_the_picture_pending_with_judged_null(tmp_path):
    s = svc(tmp_path=tmp_path)
    first = await s.add(KHARADI, 2017, Image.new("RGB", (10, 10)), "2017-03-12", 0.0, {"ok": True, "reason": "x", "model": "gemini"},
                        p.box_for("kharadi"))
    await s.decide(first["_id"], True, "owner1")
    doc = await s.add(KHARADI, 2026, Image.new("RGB", (10, 10)), "2026-03-01", 0.0, None, p.box_for("kharadi"))
    assert doc["status"] == "pending" and doc["judged"] is None


async def test_a_retake_never_overwrites_the_kept_year_supersede_marks_the_old_one(tmp_path):
    s = svc(tmp_path=tmp_path)
    first = await s.add(KHARADI, 2017, Image.new("RGB", (10, 10)), "2017-03-12", 0.0, None, p.box_for("kharadi"))
    second = await s.add(KHARADI, 2017, Image.new("RGB", (12, 12)), "2017-03-20", 0.0, None, p.box_for("kharadi"))
    assert first["_id"] != second["_id"] and first["url"] != second["url"]  # two documents, two files: nothing overwritten
    await s.supersede("kharadi", 2017)
    docs = await s.list_area("kharadi")
    assert {d["status"] for d in docs} == {"superseded"}
    assert await s.kept_years("kharadi") == []


async def test_decide_refuse_leaves_trust_alone():
    s = svc()
    doc = await s.col.insert_one({"_id": "p1", "area": "kharadi", "year": 2017, "status": "pending", "judged": None})
    out = await s.decide("p1", False, "owner1")
    assert out["status"] == "refused"
    assert await s.trusted() is False


async def test_public_is_404_for_an_area_we_do_not_cover():
    s = svc()
    assert await s.public("nowhere") is None
