"""The photo scout (docs/plan/area-pictures.md step 4): Commons' hard rules, the vision judge's checks and variety ranking,
checked captions, and the round that turns all of it into suggestions nobody sees until the owner taps Publish. No network:
`commons.search`/`fetch_bytes` and `gemini.read_counted` are stubbed throughout."""
from datetime import datetime, timedelta, timezone

from app.core.areas import get as get_area
from app.modules.areaphotos import caption, commons, config, judge, scout
from app.modules.areaphotos.service import AreaPhotos
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 17, 6, 0, tzinfo=timezone.utc)
KHARADI = get_area("kharadi")


def page(pageid=1, licence="CC BY-SA 4.0", mime="image/jpeg", width=2000, height=1500, lat=18.552, lon=73.948,
        date_taken="2024-03-02 10:00", artist="Jane Doe", title="File:Kharadi road.jpg"):
    return {"pageid": pageid, "title": title,
            "imageinfo": [{"url": f"https://upload.wikimedia.org/x/{pageid}.jpg", "thumburl": f"https://thumb/{pageid}.jpg",
                           "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{pageid}.jpg",
                           "width": width, "height": height, "mime": mime, "timestamp": "2024-03-02T10:00:00Z",
                           "extmetadata": {"LicenseShortName": {"value": licence}, "LicenseUrl": {"value": "https://cc/by-sa/4.0"},
                                          "Artist": {"value": artist}, "DateTimeOriginal": {"value": date_taken},
                                          "ObjectName": {"value": "Kharadi road"}}}],
            "coordinates": [{"lat": lat, "lon": lon}]}


# ---- commons' hard rules ----------------------------------------------------------------------------------------------
def test_licence_must_be_free():
    cand, why = commons.hard_rules(KHARADI, page(licence="CC BY-NC 4.0"))
    assert cand is None and "licence" in why
    cand, why = commons.hard_rules(KHARADI, page(licence="CC0"))
    assert cand is not None


def test_mime_and_size_are_checked():
    cand, why = commons.hard_rules(KHARADI, page(mime="image/gif"))
    assert cand is None and "photo file" in why
    cand, why = commons.hard_rules(KHARADI, page(width=800, height=600))
    assert cand is None and "small" in why


def test_the_photo_must_be_inside_the_area():
    cand, why = commons.hard_rules(KHARADI, page(lat=19.2, lon=72.9))   # Mumbai, not Kharadi
    assert cand is None and "outside" in why


def test_date_taken_not_before_2015():
    cand, why = commons.hard_rules(KHARADI, page(date_taken="2010-01-01"))
    assert cand is None and "old" in why
    cand, why = commons.hard_rules(KHARADI, page(date_taken=""))   # falls back to the upload timestamp (2024)
    assert cand is not None and cand.taken_on == "2024-03-02"


def test_a_clean_candidate_carries_credit_and_licence_from_commons_alone():
    cand, why = commons.hard_rules(KHARADI, page())
    assert why == ""
    assert cand.credit == "Jane Doe" and cand.licence == "CC BY-SA 4.0"
    assert cand.page_url == "https://commons.wikimedia.org/wiki/File:1.jpg"


# ---- the vision judge --------------------------------------------------------------------------------------------------
def test_faces_watermark_interior_and_low_quality_are_rejected():
    ok = {"is_outdoor_photo_of_place": True, "shows": ["main_road"], "faces_prominent": False,
         "watermark_or_text_overlay": False, "interior": False, "quality": 4, "caption_hint": "a busy road"}
    assert judge._parse(ok).ok
    assert not judge._parse({**ok, "faces_prominent": True}).ok
    assert not judge._parse({**ok, "watermark_or_text_overlay": True}).ok
    assert not judge._parse({**ok, "interior": True}).ok
    assert not judge._parse({**ok, "quality": 2}).ok
    assert not judge._parse({**ok, "is_outdoor_photo_of_place": False}).ok
    assert not judge._parse("not json").ok


async def test_model_failure_or_spent_budget_judges_nothing(monkeypatch):
    import app.platform.gemini as gemini_module
    monkeypatch.setattr(gemini_module, "available", lambda: False)
    verdict, why = await judge.judge(FakeDb(), NOW, "Kharadi", b"x")
    assert verdict is None and "key" in why


def test_variety_ranking_prefers_a_main_road_over_a_second_skyline():
    v_road = judge.Verdict(True, "road", ("main_road",), 4, "")
    v_sky1 = judge.Verdict(True, "sky", ("skyline",), 5, "")
    v_sky2 = judge.Verdict(True, "sky2", ("skyline",), 5, "")
    picks = judge.pick_variety([("a", v_sky1), ("b", v_road), ("c", v_sky2)], limit=2)
    assert [c for c, _ in picks] == ["b", "a"]   # the road first (ranked above skyline), then the first skyline kept


# ---- captions -------------------------------------------------------------------------------------------------------------
def test_caption_falls_back_when_the_model_invents_a_name_not_in_the_facts():
    good = caption.build(KHARADI, "File:Kharadi bypass road (2).jpg", "a busy main road near the EON IT Park signal")
    assert "Kharadi" in good and len(good) <= 160
    # the hint invents a builder name the title and area never said
    invented = caption.build(KHARADI, "File:Kharadi bypass road.jpg", "near Lodha Developers' new tower")
    assert "Lodha Developers" not in invented
    assert invented == caption.fallback(KHARADI, "File:Kharadi bypass road.jpg")


def test_caption_fallback_is_built_from_the_commons_title_alone():
    assert caption.fallback(KHARADI, "File:Metro_station_(3).JPG") == "Kharadi: Metro station"
    assert caption.fallback(KHARADI, "File:Kharadi_Road.jpg") == "Kharadi Road"


# ---- one area's round -----------------------------------------------------------------------------------------------------
class FakeJudgeAlwaysGood:
    def __init__(self, shows=("main_road",), quality=4):
        self.shows, self.quality, self.calls = shows, quality, 0

    async def __call__(self, db, now, area_name, image):
        self.calls += 1
        return judge.Verdict(True, "shows it", self.shows, self.quality, "a view of the road"), ""


def _stub_network(monkeypatch, pages):
    async def fake_search(*a, **k):
        return pages

    async def fake_fetch(*a, **k):
        return b"fakejpegbytes"

    def fake_keep(body, folder, name, min_side=0, root=None):
        return {"url": f"/uploads/{folder}/{name}.webp", "small_url": f"/uploads/{folder}/{name}-small.webp",
               "width": 1600, "height": 1067}

    monkeypatch.setattr(scout.commons, "search", fake_search)
    monkeypatch.setattr(scout.commons, "fetch_bytes", fake_fetch)
    monkeypatch.setattr(scout.media, "keep_photo", fake_keep)


async def _round(monkeypatch, pages, judge_fn, cfg=None, known_pageids=()):
    db = FakeDb()
    for pid in known_pageids:
        await db.area_photos.insert_one({"_id": f"seed{pid}", "area": "kharadi", "commons_pageid": pid, "status": "live",
                                         "caption": "x" * 10, "credit": "c", "taken_on": "2024-01-01", "kind": "licensed",
                                         "licence": "CC0", "source_url": "https://x.in/a", "order": 0, "created_at": NOW})
    _stub_network(monkeypatch, pages)
    monkeypatch.setattr(scout.judge, "judge", judge_fn)
    cfg = cfg or config.Config(enabled=True)
    result = await scout.round_for_area(db, KHARADI, NOW, cfg, judge_limit=cfg.max_judged_per_area)
    return db, result


async def test_a_round_keeps_up_to_eight_suggestions_never_public(monkeypatch):
    pages = [page(pageid=i, title=f"File:Kharadi view {i}.jpg") for i in range(1, 11)]
    db, result = await _round(monkeypatch, pages, FakeJudgeAlwaysGood())
    assert result["kept"] == 8   # config default max_suggested_per_area
    docs = await AreaPhotos(db).list_area("kharadi")
    assert all(d["status"] == "suggested" and d["origin"] == "scout" for d in docs)
    assert len(docs) == 8
    public = await AreaPhotos(db).public("kharadi")
    assert public["photos"] == []   # suggested is never public


async def test_a_candidate_already_refused_is_never_suggested_again(monkeypatch):
    async def reject(db, now, area_name, image):
        return judge.Verdict(False, "quality 1 of 5"), ""

    pages = [page(pageid=5, title="File:Kharadi five.jpg")]
    db, result = await _round(monkeypatch, pages, reject)
    assert result["kept"] == 0
    # the same candidate, offered again next round: it was remembered, so the model is never asked about it again
    calls = FakeJudgeAlwaysGood()
    _stub_network(monkeypatch, pages)
    monkeypatch.setattr(scout.judge, "judge", calls)
    result2 = await scout.round_for_area(db, KHARADI, NOW + timedelta(days=7), config.Config(enabled=True),
                                         judge_limit=30)
    assert result2["judged"] == 0 and calls.calls == 0


async def test_already_stored_pageid_is_skipped_without_judging(monkeypatch):
    pages = [page(pageid=9, title="File:Kharadi nine.jpg")]
    calls = FakeJudgeAlwaysGood()
    db, result = await _round(monkeypatch, pages, calls, known_pageids=(9,))
    assert result["judged"] == 0 and calls.calls == 0


async def test_model_failure_stops_the_round_without_suggesting_anything_unjudged(monkeypatch):
    async def unavailable(db, now, area_name, image):
        return None, "the day's Gemini budget is spent"

    pages = [page(pageid=i) for i in (21, 22)]
    db, result = await _round(monkeypatch, pages, unavailable)
    assert result["kept"] == 0 and "budget" in result["stopped_for"]


# ---- the gap nudge, once per 30 days ---------------------------------------------------------------------------------------
async def test_a_short_area_is_nudged_once_then_not_again_within_30_days(monkeypatch):
    db = FakeDb()
    sent = []

    async def notify_gap(db, area, missing, now):
        sent.append((area.key, missing, now))

    monkeypatch.setitem(scout._hooks, "notify_gap", notify_gap)
    cfg = config.Config(enabled=True)
    await scout._check_gap(db, KHARADI, NOW, cfg)
    assert len(sent) == 1
    await scout._check_gap(db, KHARADI, NOW + timedelta(days=5), cfg)
    assert len(sent) == 1   # too soon
    await scout._check_gap(db, KHARADI, NOW + timedelta(days=31), cfg)
    assert len(sent) == 2


async def test_no_nudge_once_the_area_has_enough_live_and_suggested_photos(monkeypatch):
    db = FakeDb()
    for i in range(4):
        await db.area_photos.insert_one({"_id": f"p{i}", "area": "kharadi", "status": "live", "created_at": NOW})
    sent = []

    async def notify_gap(db, area, missing, now):
        sent.append(area.key)

    monkeypatch.setitem(scout._hooks, "notify_gap", notify_gap)
    await scout._check_gap(db, KHARADI, NOW, config.Config(enabled=True))
    assert sent == []


# ---- the daily cycle respects the on/off switch -----------------------------------------------------------------------
async def test_run_once_is_a_no_op_until_switched_on():
    out = await scout.run_once(FakeDb(), NOW, config.Config(enabled=False))
    assert out == {"enabled": False}


# ---- flagging agents' own uploads: a reason added, never a rejection ---------------------------------------------------
async def test_an_agents_upload_is_flagged_with_the_models_reason_but_never_rejected(tmp_path, monkeypatch):
    db = FakeDb()
    svc = AreaPhotos(db, now=lambda: NOW, root=tmp_path)
    doc = await svc.add("kharadi", {"caption": "Kharadi bypass road at the signal", "taken_on": "2026-11-10",
                                   "credit": "Rohan", "kind": "own"}, _jpeg(), "image/jpeg", "agent1")

    async def says_watermark(db, now, area_name, image):
        return judge.Verdict(False, "a watermark or text is drawn on it"), ""

    monkeypatch.setattr(scout.media, "UPLOADS", tmp_path)
    monkeypatch.setattr(scout.judge, "judge", says_watermark)
    flagged = await scout.flag_uploads(db, KHARADI, NOW, config.Config(enabled=True))
    assert flagged == 1
    again = await svc._get(doc["_id"])
    assert again["status"] == "pending"   # never auto-rejected
    assert "watermark" in again["ai"]["reason"]


def _jpeg():
    import io

    from PIL import Image
    out = io.BytesIO()
    Image.new("RGB", (1600, 1067), (90, 120, 160)).save(out, "JPEG")
    return out.getvalue()
