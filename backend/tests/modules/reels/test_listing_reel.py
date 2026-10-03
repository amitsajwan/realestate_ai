"""Listing reels: jobs, limits, idempotency, facts-only scripts, the worker with a stubbed renderer, render() with stubbed
compose / voice / ffmpeg (no network, no ffmpeg), the agent routes, and posting on behalf through the concierge."""
import re
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.core.auth_backend import current_active_user
from app.modules.reels import compose, listing_reel as lr
from app.modules.reels import router as rr
from app.modules.reels.director import _valid

from ..listings_fakes import ListingsDb

pytestmark = pytest.mark.asyncio
AGENT = "agent1"
PROFILE = {"agent_id": AGENT, "slug": "rahul", "agent_name": "Rahul Sharma", "phone": "+919876543210",
           "branding_data": {"business_name": "Rahul Homes", "rera_agent_no": "A51800012345"}}


class Clock:
    def __init__(self):
        self.t = datetime(2026, 10, 1, 9, 0, 0)

    def __call__(self):
        self.t += timedelta(seconds=1)
        return self.t


class Renderer:
    """Stands in for listing_reel.render: records the call and writes a tiny file."""

    def __init__(self, fail: Exception = None):
        self.calls, self.fail = [], fail

    def __call__(self, script, photos, lang, out, **kw):
        if self.fail:
            raise self.fail
        self.calls.append({"script": script, "photos": list(photos), "lang": lang, "out": Path(out), **kw})
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(b"mp4")
        return {"audio": "voice+music" if kw.get("voiced") else "music", "note": "" if kw.get("voiced") else lr.NO_VOICE_NOTE}


def photo(dir_: Path, name: str) -> str:
    (dir_ / "images").mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 48), (120, 90, 60)).save(dir_ / "images" / name)
    return f"/uploads/images/{name}"


async def setup(tmp_path, photos=2, title="2 BHK in Kharadi", status="live", llm=None, voiced=False, renderer=None, **extra):
    db, clock = ListingsDb(), Clock()
    media = [{"url": photo(tmp_path, f"p{i}.jpg"), "kind": "image", "order": i} for i in range(photos)]
    listing = dict(_id="L1", agent_id=AGENT, status=status, title=title, transaction="sale", property_type="apartment",
                   price_inr=8500000, city="Pune", locality="Kharadi", bhk=2, carpet_sqft=780, floor=7, total_floors=22,
                   furnishing="semi", possession="ready", amenities=["Gym", "Parking", "Lift"], media=media,
                   about={"highlights": ["East-facing balcony"]}, created_at=clock(), updated_at=clock(), **extra)
    await db.get_collection("listings").insert_one(listing)
    await db.get_collection("agent_public_profiles").insert_one(dict(PROFILE))
    jobs = lr.ReelJobs(db, tmp_path, llm_factory=(lambda: llm) if llm else None, renderer=renderer or Renderer(), now=clock,
                       voice_available=lambda: voiced)
    return jobs, db


# ---- jobs: creation, limits, idempotency ----------------------------------------------------------------------------
async def test_create_queues_a_job_and_a_re_request_returns_it(tmp_path):
    jobs, db = await setup(tmp_path)
    doc, created = await jobs.create(AGENT, "L1", "hi")
    assert created and doc["status"] == "queued" and doc["lang"] == "hi" and doc["listing_id"] == "L1" and doc["agent_id"] == AGENT
    again, created2 = await jobs.create(AGENT, "L1", "hi")
    assert again["_id"] == doc["_id"] and not created2
    other, created3 = await jobs.create(AGENT, "L1", "en")
    assert created3 and other["_id"] != doc["_id"]
    assert len(db.get_collection("reel_jobs").docs) == 2
    latest = await jobs.latest(AGENT, "L1")
    assert set(latest) == {"hi", "en"}


async def test_needs_two_local_photos_a_live_listing_and_the_owner(tmp_path):
    jobs, _ = await setup(tmp_path, photos=1)
    with pytest.raises(lr.ReelJobError) as e:
        await jobs.create(AGENT, "L1", "en")
    assert e.value.status_code == 422 and e.value.detail == "Add at least 2 photos"
    # remote URLs never count (they are never fetched)
    jobs, db = await setup(tmp_path / "b", photos=1)
    await db.get_collection("listings").update_one({"_id": "L1"}, {"$push": {"media": {"url": "https://x.test/a.jpg", "kind": "image"}}})
    with pytest.raises(lr.ReelJobError):
        await jobs.create(AGENT, "L1", "en")
    jobs, _ = await setup(tmp_path / "c", status="draft")
    with pytest.raises(lr.ReelJobError) as e:
        await jobs.create(AGENT, "L1", "en")
    assert e.value.status_code == 409
    with pytest.raises(lr.ReelJobError) as e:
        await jobs.create("someone-else", "L1", "en")
    assert e.value.status_code == 404
    with pytest.raises(lr.ReelJobError) as e:
        await jobs.create(AGENT, "L1", "ta")
    assert e.value.status_code == 422


async def test_five_reels_a_day_failed_ones_do_not_count(tmp_path):
    jobs, db = await setup(tmp_path)
    col = db.get_collection("reel_jobs")
    for i in range(5):
        await col.insert_one({"_id": f"j{i}", "agent_id": AGENT, "listing_id": f"other{i}", "lang": "en", "status": "done",
                              "created_at": jobs.now()})
    await col.insert_one({"_id": "jf", "agent_id": AGENT, "listing_id": "x", "lang": "en", "status": "failed", "created_at": jobs.now()})
    with pytest.raises(lr.ReelJobError) as e:
        await jobs.create(AGENT, "L1", "en")
    assert e.value.status_code == 429 and "5 reels a day" in e.value.detail
    for d in col.docs:  # a day later the quota is back
        d["created_at"] -= timedelta(hours=25)
    assert (await jobs.create(AGENT, "L1", "en"))[1]


async def test_finished_reel_is_reused_until_the_listing_changes_or_again(tmp_path):
    jobs, db = await setup(tmp_path)
    first, _ = await jobs.create(AGENT, "L1", "en")
    assert await jobs.run_once()
    same, created = await jobs.create(AGENT, "L1", "en")
    assert same["_id"] == first["_id"] and same["status"] == "done" and not created
    forced, created = await jobs.create(AGENT, "L1", "en", again=True)
    assert created and forced["_id"] != first["_id"]
    await jobs.run_once()
    await db.get_collection("listings").update_one({"_id": "L1"}, {"$set": {"updated_at": jobs.now() + timedelta(minutes=1)}})
    jobs.now.t += timedelta(minutes=2)
    assert (await jobs.create(AGENT, "L1", "en"))[1]


# ---- the worker ------------------------------------------------------------------------------------------------------
async def test_worker_renders_with_the_listing_photos_the_listed_by_line_and_no_voice_note(tmp_path):
    r = Renderer()
    jobs, db = await setup(tmp_path, renderer=r)
    doc, _ = await jobs.create(AGENT, "L1", "mr")
    assert await jobs.run_once() and not await jobs.run_once()
    out = lr.job_out(await db.get_collection("reel_jobs").find_one({"_id": doc["_id"]}), "http://api.test/")
    assert out["status"] == "done" and re.fullmatch(r"/uploads/reels/listing-L1-mr-[0-9a-f]{8}\.mp4", out["video_path"])
    assert out["video_url"] == "http://api.test" + out["video_path"]
    assert out["audio"] == "music" and "GOOGLE_TTS_API_KEY" in out["note"]
    call = r.calls[0]
    assert call["lang"] == "mr" and [p.name for p in call["photos"]] == ["p0.jpg", "p1.jpg"]
    assert call["closing"] == "Listed by Rahul Homes · RERA A51800012345" and "98765" not in str(call)
    assert call["badge"] is None and call["kicker"] == "KHARADI, PUNE" and call["voiced"] is False
    assert out["script"]["made_by"] == "rules"
    assert not re.search(r"[ऀ-ॿ]", " ".join(b["screen"] for b in out["script"]["beats"]))  # Roman on screen
    assert re.search(r"[ऀ-ॿ]", out["script"]["beats"][0]["voice"])                        # Marathi voice


async def test_sample_listing_carries_the_sample_badge_and_says_so(tmp_path):
    r = Renderer()
    jobs, db = await setup(tmp_path, title="Sample: 2 BHK in Kharadi", renderer=r)
    await jobs.create(AGENT, "L1", "en")
    await jobs.run_once()
    assert r.calls[0]["badge"] == "Sample listing"
    assert "sample" in r.calls[0]["script"]["cta_voice"].lower()
    assert db.get_collection("reel_jobs").docs[0]["sample"] is True


async def test_worker_failure_is_stored_with_a_safe_message(tmp_path):
    jobs, db = await setup(tmp_path, renderer=Renderer(fail=RuntimeError("C:\\secret\\path broke")))
    await jobs.create(AGENT, "L1", "en")
    await jobs.run_once()
    d = db.get_collection("reel_jobs").docs[0]
    assert d["status"] == "failed" and d["error"] == "Could not make the reel. Please try again." and "secret" not in d["error"]
    jobs, db = await setup(tmp_path / "b", renderer=Renderer(fail=compose.ReelError("the reel came out larger than 20 MB")))
    await jobs.create(AGENT, "L1", "en")
    await jobs.run_once()
    assert db.get_collection("reel_jobs").docs[0]["error"] == "the reel came out larger than 20 MB"


async def test_stale_rendering_jobs_are_failed(tmp_path):
    jobs, db = await setup(tmp_path)
    await db.get_collection("reel_jobs").insert_one({"_id": "old", "agent_id": AGENT, "listing_id": "L1", "lang": "en",
                                                     "status": "rendering", "created_at": jobs.now(), "started_at": jobs.now() - timedelta(hours=1)})
    await jobs.fail_stale()
    assert db.get_collection("reel_jobs").docs[0]["status"] == "failed"


# ---- facts-only scripts (director._valid reused) -------------------------------------------------------------------------
class LLM:
    def __init__(self, out):
        self.out, self.calls = out, 0

    async def json(self, system, user):
        self.calls += 1
        return self.out


GOOD = {"beats": [{"screen": "*2 BHK* in Kharadi", "voice": "A 2 BHK in Kharadi, Pune."},
                  {"screen": "*780* sq ft carpet", "voice": "780 square feet of carpet area."},
                  {"screen": "Floor *7* of 22", "voice": "On floor 7 of 22, ready to move."},
                  {"screen": "Gym · Parking · *Lift*", "voice": "With a gym, parking and a lift."}],
        "cta_screen": "Message to book a *visit*", "cta_voice": "Like it? Message us to book a visit."}


async def test_llm_script_used_only_when_it_keeps_to_the_facts(tmp_path):
    llm = LLM(GOOD)
    r = Renderer()
    jobs, _ = await setup(tmp_path, llm=llm, renderer=r)
    await jobs.create(AGENT, "L1", "en")
    await jobs.run_once()
    assert r.calls[0]["script"]["made_by"] == "llm" and r.calls[0]["script"]["beats"][1]["screen"] == "*780* sq ft carpet"
    invented = {**GOOD, "beats": GOOD["beats"][:3] + [{"screen": "*5 min* to metro", "voice": "Just 5 minutes to the metro."}]}
    phone = {**GOOD, "cta_voice": "Call 9876543210 now."}
    devanagari_screen = {**GOOD, "cta_screen": "विज़िट बुक करें"}
    for bad in (invented, phone, devanagari_screen, {"beats": []}, None):
        llm2, r2 = LLM(bad), Renderer()
        jobs, _ = await setup(tmp_path / str(id(bad)), llm=llm2, renderer=r2)
        await jobs.create(AGENT, "L1", "en")
        await jobs.run_once()
        assert r2.calls[0]["script"]["made_by"] == "rules" and llm2.calls == 2


@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
async def test_rules_script_passes_the_director_rules_in_every_language(lang):
    for listing in (
        dict(_id="a", title="Sample flat", transaction="sale", price_inr=12500000, city="Pune", locality="Baner", bhk=3,
             carpet_sqft=1050, floor=4, total_floors=12, furnishing="furnished", possession="under_construction", amenities=["Pool"]),
        dict(_id="b", title="Flat", transaction="rent", price_inr=45000, city="Pune", locality="Wakad", bhk=1),
        dict(_id="c", title="Plot", transaction="sale", property_type="plot", city="Pune"),
    ):
        subject, facts, f = lr.reel_facts(listing, PROFILE)
        script = lr.rules_script(f, lang)
        assert _valid(script, subject + "\n" + "\n".join(f"- {x}" for x in facts)), (lang, script)
    assert "98765" not in str(lr.reel_facts(listing, PROFILE))


def test_listed_by_line_never_carries_a_phone_number():
    assert lr.listed_by_line(PROFILE) == "Listed by Rahul Homes · RERA A51800012345"
    assert lr.listed_by_line({"agent_name": "Rahul", "branding_data": {"rera_agent_no": "9876543210"}}) == "Listed by Rahul"
    assert lr.listed_by_line({"branding_data": {"business_name": "Homes 98765 43210"}}) == "Listed by Homes"
    assert lr.listed_by_line(None) == ""


def test_compose_allows_a_rera_number_but_not_a_phone_number():
    assert not compose.PHONE_RE.search("Listed by Rahul Homes · RERA A51800012345")
    assert compose.PHONE_RE.search("Call 98765 43210") and compose.PHONE_RE.search("+91 9876543210")


# ---- render() with compose, voice and ffmpeg stubbed ----------------------------------------------------------------------
@pytest.fixture
def stubs(monkeypatch):
    seen = {"ffmpeg": [], "synth": []}

    def make_reel(scenes, out, music=None, **kw):
        seen["scenes"], seen["music"] = scenes, Path(music)
        assert Path(music).is_file()
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(b"mp4")
        return Path(out)

    def run(args, **kw):
        seen["ffmpeg"].append(args)
        Path(args[-2]).write_bytes(b"m4a")  # the narration output
        return ""

    def synth(text, lang):
        seen["synth"].append((text, lang))
        return b"mp3"

    monkeypatch.setattr(lr, "make_reel", make_reel)
    monkeypatch.setattr(lr.ffmpeg, "run", run)
    monkeypatch.setattr(lr.ffmpeg, "probe", lambda p: SimpleNamespace(duration=2.5))
    monkeypatch.setattr(lr.voice, "synth", synth)
    return seen


def _script():
    return {**GOOD, "made_by": "llm"}


def test_render_voiced_mixes_voice_and_music_and_closes_with_listed_by(tmp_path, stubs):
    out = lr.render(_script(), ["a.jpg", "b.jpg"], "hi", tmp_path / "r.mp4", badge="Sample listing", kicker="KHARADI",
                    closing="Listed by Rahul Homes · RERA A51800012345", voiced=True)
    assert out == {"audio": "voice+music", "note": ""}
    scenes = stubs["scenes"]
    assert len(scenes) == 5 and all(s.badge == "Sample listing" for s in scenes)
    assert [s.image for s in scenes] == ["a.jpg", "b.jpg", "a.jpg", "b.jpg", "a.jpg"]
    assert scenes[0].kicker == "KHARADI" and scenes[1].kicker is None
    assert [l.text for l in scenes[-1].lines[1:]] == ["Listed by Rahul Homes", "RERA A51800012345"]
    assert all(s.seconds == pytest.approx(3.05) for s in scenes)
    assert [l for _, l in stubs["synth"]] == ["hi"] * 5 and stubs["ffmpeg"] and stubs["music"].suffix == ".m4a"
    compose._no_phone_numbers(scenes)  # the renderer's own phone check accepts the RERA number


def test_render_without_the_voice_key_is_music_only_and_says_so(tmp_path, stubs):
    out = lr.render(_script(), ["a.jpg", "b.jpg"], "en", tmp_path / "r.mp4", voiced=False)
    assert out["audio"] == "music" and out["note"] == lr.NO_VOICE_NOTE
    assert not stubs["synth"] and not stubs["ffmpeg"] and stubs["music"].suffix == ".wav"


def test_render_falls_back_to_music_when_the_voice_service_fails(tmp_path, stubs, monkeypatch):
    def boom(text, lang):
        raise lr.voice.VoiceError("HTTP 403")
    monkeypatch.setattr(lr.voice, "synth", boom)
    out = lr.render(_script(), ["a.jpg", "b.jpg"], "en", tmp_path / "r.mp4", voiced=True)
    assert out == {"audio": "music", "note": lr.VOICE_FAILED_NOTE}


# ---- agent routes ------------------------------------------------------------------------------------------------------
def client(jobs, user_id=AGENT):
    app = FastAPI()
    app.include_router(rr.router, prefix="/listings")
    app.dependency_overrides[rr.get_jobs] = lambda: jobs
    app.dependency_overrides[rr.start_worker] = lambda: None
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id=user_id)
    return TestClient(app)


async def test_routes_create_and_list_jobs(tmp_path):
    jobs, _ = await setup(tmp_path)
    c = client(jobs)
    r = c.post("/listings/L1/reel", json={"lang": "hi"})
    assert r.status_code == 202 and r.json()["created"] and r.json()["job"]["status"] == "queued"
    jid = r.json()["job"]["id"]
    assert c.post("/listings/L1/reel", json={"lang": "hi"}).json()["job"]["id"] == jid
    assert c.post("/listings/L1/reel", json={"lang": "xx"}).status_code == 422
    got = c.get("/listings/L1/reel").json()["jobs"]
    assert list(got) == ["hi"] and got["hi"]["id"] == jid
    assert client(jobs, "intruder").get("/listings/L1/reel").status_code == 404
    assert client(jobs, "intruder").post("/listings/L1/reel", json={}).status_code == 404


# ---- posting the reel on behalf (concierge) ------------------------------------------------------------------------------
async def test_concierge_reel_post_needs_consent_and_a_finished_reel_and_uses_attribution(tmp_path):
    from app.modules.concierge.service import ConciergeError
    from app.modules.listings.schemas import ListingCreate
    from app.platform.meta_graph.config import SocialConfig
    from ..concierge.helpers import FULL, PHONE, make

    svc, db, _ = make()
    aid = (await svc.create_agent("OWNER", "Rahul Sharma", PHONE, "Rahul"))["agent"]["id"]
    media = [{"url": photo(tmp_path, f"c{i}.jpg"), "kind": "image", "order": i} for i in range(2)]
    lid = (await svc.create_listing("OWNER", aid, ListingCreate(**FULL, media=media)))["id"]
    await svc.publish_listing("OWNER", aid, lid)
    r = Renderer()
    svc.reels = lr.ReelJobs(db, tmp_path, renderer=r, voice_available=lambda: False)
    doc, created = await svc.make_reel("OWNER", aid, lid, "en")
    assert created and db.get_collection("concierge_audit").docs[-1]["action"] == "reel.make"
    assert set(await svc.reels_for(aid, lid)) == {"en"}

    sent = []

    async def publish_fn(ch, url, text, cfg=None, file_path=None):
        sent.append((ch, url, text, file_path))
        return SimpleNamespace(external_id="dryrun_1", permalink=None)

    dry = lambda: SocialConfig(dry_run=True, media_base_url="https://media.test")
    with pytest.raises(ConciergeError) as e:
        await svc.post_reel("OWNER", aid, lid, "en", ["instagram"], publish_fn=publish_fn, config_loader=dry)
    assert e.value.status_code == 409 and "consent" in str(e.value) and not sent
    await svc.record_consent("OWNER", aid)
    with pytest.raises(ConciergeError) as e:  # still rendering
        await svc.post_reel("OWNER", aid, lid, "en", ["instagram"], publish_fn=publish_fn, config_loader=dry)
    assert "Make the reel first" in str(e.value)
    await svc.reels.run_once()
    out = await svc.post_reel("OWNER", aid, lid, "en", ["instagram", "facebook_page"], publish_fn=publish_fn, config_loader=dry)
    assert [o["status"] for o in out] == ["dry_run", "dry_run"]
    (ch1, url1, ig, fp1), (ch2, _, fb, fp2) = sent
    assert url1.startswith("https://media.test/uploads/reels/listing-") and fp1 is None and fp2.name == url1.rsplit("/", 1)[-1]
    assert "Listed by Rahul Sharma on Avasetu" in ig and "Link in our bio" in ig and "#Avasetu" in ig
    assert "Listed by Rahul Sharma" in fb and "9876543210" not in ig + fb
    assert db.get_collection("concierge_audit").docs[-1]["action"] == "reel.post"


async def test_concierge_reel_routes_are_owner_only(monkeypatch):
    from app.modules.concierge import router as cr
    monkeypatch.delenv("CONCIERGE_OWNER_IDS", raising=False)
    paths = {r.path for r in cr.router.routes}
    assert {"/agents/{agent_id}/listings/{listing_id}/reel", "/agents/{agent_id}/listings/{listing_id}/reel/post"} <= paths
    from ..concierge.helpers import make
    svc, _, _ = make()
    app = FastAPI()
    app.include_router(cr.router, prefix="/concierge")
    app.dependency_overrides[cr.get_service] = lambda: svc
    app.dependency_overrides[cr.reel_worker] = lambda: None
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="agent1", is_superuser=False)
    c = TestClient(app)
    assert c.post("/concierge/agents/a/listings/l/reel", json={"lang": "en"}).status_code == 403
    assert c.post("/concierge/agents/a/listings/l/reel/post", json={}).status_code == 403


def test_sales_words_are_refused_and_sample_homes_do_not_offer_a_visit():
    from app.modules.reels.listing_reel import for_sample, pushy
    hype = {"beats": [{"screen": "Only *78 Lakh*", "voice": "Priced at just 78 lakh."}], "cta_screen": "x", "cta_voice": "y"}
    assert pushy(hype)
    assert pushy({"beats": [{"screen": "Price", "voice": "कीमत केवल 95 लाख रुपये।"}]})
    calm = {"beats": [{"screen": "Price *78 Lakh*", "voice": "The price is 78 lakh."}],
            "cta_screen": "Message to book a *visit*", "cta_voice": "Message us to book a visit."}
    assert not pushy(calm)
    for lang in ("en", "hi", "mr"):
        s = for_sample(calm, lang)
        assert "visit" not in s["cta_screen"].lower() and "visit" not in s["cta_voice"].lower() and s["beats"] == calm["beats"]
        assert s["cta_voice"].startswith(("This is a sample", "यह एक सैंपल", "ही एक सॅम्पल"))


def test_a_sample_home_is_never_called_for_sale():
    from app.modules.reels.listing_reel import for_sample
    hi = {"beats": [{"screen": "Wagholi *3 BHK*", "voice": "वाघोली में यह 3 बीएचके अपार्टमेंट बिक्री के लिए उपलब्ध है।"},
                    {"screen": "Price *82 Lakh*", "voice": "कीमत 82 लाख रुपये है।"}],
          "cta_screen": "Message to book a *visit*", "cta_voice": "विज़िट बुक करें।"}
    s = for_sample(hi, "hi")
    assert s["beats"][0]["voice"] == "वाघोली में यह 3 बीएचके अपार्टमेंट है।" and "सैंपल" in s["cta_voice"]
    en = {"beats": [{"screen": "Sample *2 BHK*", "voice": "This is a sample 2 BHK apartment for sale in Upper Kharadi."}],
          "cta_screen": "x", "cta_voice": "y"}
    s = for_sample(en, "en")
    assert s["beats"][0]["voice"] == "This is a sample 2 BHK apartment in Upper Kharadi." and "visit" not in s["cta_voice"]


async def test_concierge_reel_post_sends_the_cover_to_instagram_when_the_reel_has_one(tmp_path):
    from app.modules.listings.schemas import ListingCreate
    from app.platform.meta_graph.config import SocialConfig
    from ..concierge.helpers import FULL, PHONE, make

    svc, db, _ = make()
    aid = (await svc.create_agent("OWNER", "Rahul Sharma", PHONE, "Rahul"))["agent"]["id"]
    media = [{"url": photo(tmp_path, f"c{i}.jpg"), "kind": "image", "order": i} for i in range(2)]
    lid = (await svc.create_listing("OWNER", aid, ListingCreate(**FULL, media=media)))["id"]
    await svc.publish_listing("OWNER", aid, lid)

    class WithCover(Renderer):
        def __call__(self, script, photos, lang, out, **kw):
            res = super().__call__(script, photos, lang, out, **kw)
            Path(out).with_name(Path(out).stem + "-cover.jpg").write_bytes(b"jpg")
            return res

    svc.reels = lr.ReelJobs(db, tmp_path, renderer=WithCover(), voice_available=lambda: False)
    await svc.make_reel("OWNER", aid, lid, "en")
    await svc.record_consent("OWNER", aid)
    await svc.reels.run_once()
    sent = []

    async def publish_fn(ch, url, text, cfg=None, file_path=None, **kw):
        sent.append((ch, url, kw.get("cover_url")))
        return SimpleNamespace(external_id="dryrun_1", permalink=None)

    dry = lambda: SocialConfig(dry_run=True, media_base_url="https://media.test")
    await svc.post_reel("OWNER", aid, lid, "en", ["instagram", "facebook_page"], publish_fn=publish_fn, config_loader=dry)
    (_, ig_url, ig_cover), (_, _, fb_cover) = sent
    assert ig_cover == ig_url[:-4] + "-cover.jpg" and ig_cover.startswith("https://media.test/uploads/reels/listing-")
    assert fb_cover is None
