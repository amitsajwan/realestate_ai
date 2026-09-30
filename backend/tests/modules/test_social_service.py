import socket
from datetime import datetime, timedelta

import httpx
import pytest

from app.modules.social import config
from app.modules.social.config import SocialConfig
from app.modules.social.schemas import PublishIn
from app.modules.social.service import CONSENT_TEXT, SocialError, SocialService, build_payload, rebase

from .test_social_helpers import DRY, REAL, TOKEN, FakeGraph, graph_service, make_db, pack

pytestmark = pytest.mark.asyncio

BODY = dict(channels=["facebook_page", "instagram"], approve=True, consent=True)


def body(**over) -> PublishIn:
    return PublishIn(**{**BODY, **over})


def dry_service(db, cfg=DRY, now=datetime.utcnow) -> SocialService:
    return SocialService(db, config_loader=lambda: cfg, now=now)


# ---- config / status ------------------------------------------------------------------------------------------
async def test_config_defaults_to_dry_run_and_no_channels(monkeypatch):
    for k in ("SOCIAL_DRY_RUN", "META_GRAPH_VERSION", "META_PAGE_ID", "META_PAGE_ACCESS_TOKEN", "META_IG_BUSINESS_ID", "PUBLIC_MEDIA_BASE_URL"):
        monkeypatch.delenv(k, raising=False)
    cfg = config.load()
    assert cfg.dry_run is True and cfg.graph_version == "v23.0" and not cfg.configured("facebook_page") and not cfg.media_url_ok
    monkeypatch.setenv("SOCIAL_DRY_RUN", "garbage")
    assert config.load().dry_run is True  # only an explicit false turns it off
    monkeypatch.setenv("SOCIAL_DRY_RUN", "false")
    monkeypatch.setenv("META_GRAPH_VERSION", "v24.0")
    monkeypatch.setenv("META_PAGE_ID", "P")
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", TOKEN)
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://m.test/")
    cfg = config.load()
    assert cfg.dry_run is False and cfg.graph_version == "v24.0" and cfg.configured("facebook_page")
    assert not cfg.configured("instagram") and cfg.media_url_ok and cfg.media_base_url == "https://m.test"
    assert TOKEN not in repr(cfg)
    monkeypatch.setenv("META_GRAPH_VERSION", "../evil")
    assert config.load().graph_version == "v23.0"


async def test_status_has_no_secrets(monkeypatch):
    monkeypatch.setenv("META_PAGE_ID", "P")
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", TOKEN)
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "http://insecure.test")
    monkeypatch.delenv("SOCIAL_DRY_RUN", raising=False)
    st = SocialService(make_db()).status()
    assert st == {"dry_run": True, "channels": {"facebook_page": True, "instagram": False}, "brand": "PUNE Property", "media_url_ok": False}
    assert TOKEN not in str(st)


# ---- payload ---------------------------------------------------------------------------------------------------
async def test_rebase_and_payloads():
    assert rebase("http://localhost:8000/uploads/marketing/L1/cover.jpg?x=1", "https://m.test") == "https://m.test/uploads/marketing/L1/cover.jpg"
    assert rebase("/uploads/a.jpg", "") == "/uploads/a.jpg"
    assert rebase("https://cdn.other/x.jpg", "https://m.test") == "https://cdn.other/x.jpg"
    fb = build_payload(pack(), "facebook_page", "https://m.test")
    assert fb["text"] == "Ready 2 BHK in Baner\n\n\U0001F517 Details and photos: https://site.test/agent/rahul/listings/L1?src=whatsapp"
    assert fb["image_urls"] == ["https://m.test/uploads/marketing/L1/cover.jpg"]
    ig = build_payload(pack(), "instagram", "https://m.test")
    assert ig["text"] == "2 BHK in Baner\n\n#Pune #Baner" and len(ig["image_urls"]) == 4 and ig["image_urls"][0].endswith("cover.jpg")
    assert build_payload(pack(images=()), "facebook_page", "https://m.test")["image_urls"] == []


# ---- dry run ---------------------------------------------------------------------------------------------------
async def test_dry_run_records_and_never_touches_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network touched in dry run")
    monkeypatch.setattr(httpx.AsyncClient, "send", boom)
    monkeypatch.setattr(socket.socket, "connect", boom)
    db = make_db()
    pubs = await dry_service(db).publish("A1", "L1", body())
    assert [p.channel for p in pubs] == ["facebook_page", "instagram"]
    for p in pubs:
        assert p.status == "dry_run" and p.error is None and p.attempts == 1 and p.pack_version == 1
        assert p.external_id.startswith("dryrun_") and p.consent.text == CONSENT_TEXT and p.approved_at == p.consent.given_at
        assert p.agent_id == "A1" and p.listing_id == "L1" and p.payload.text
    assert pubs[0].payload.image_urls == ["/uploads/marketing/L1/cover.jpg"]  # no base configured: path kept
    stored = db.get_collection("publications").docs
    assert len(stored) == 2 and all(d["status"] == "dry_run" for d in stored)


async def test_dry_run_ignores_configuration_and_rebases_media():
    cfg = SocialConfig(dry_run=True, media_base_url="https://media.test")
    p = (await dry_service(make_db(), cfg).publish("A1", "L1", body(channels=["instagram"])))[0]
    assert p.status == "dry_run" and p.payload.image_urls[0] == "https://media.test/uploads/marketing/L1/cover.jpg"


# ---- rules -----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("over", [dict(approve=False), dict(consent=False), dict(approve=False, consent=False)])
async def test_approve_and_consent_required(over):
    db = make_db()
    with pytest.raises(SocialError) as e:
        await dry_service(db).publish("A1", "L1", body(**over))
    assert e.value.status_code == 422 and not db.get_collection("publications").docs


async def test_owner_isolation_and_state_checks():
    db = make_db()
    svc = dry_service(db)
    with pytest.raises(SocialError) as e:
        await svc.publish("A2", "L1", body())
    assert e.value.status_code == 404
    with pytest.raises(SocialError) as e:
        await svc.list("A2", "L1")
    assert e.value.status_code == 404
    with pytest.raises(SocialError) as e:
        await svc.publish("A1", "NOPE", body())
    assert e.value.status_code == 404
    for status in ("draft", "sold", "archived"):
        db.get_collection("listings").docs[0]["status"] = status
        with pytest.raises(SocialError) as e:
            await svc.publish("A1", "L1", body())
        assert e.value.status_code == 409
    db.get_collection("listings").docs[0]["status"] = "under_offer"
    assert (await svc.publish("A1", "L1", body(channels=["facebook_page"])))[0].status == "dry_run"
    db2 = make_db()
    db2.get_collection("marketing_packs").docs.clear()
    with pytest.raises(SocialError) as e:
        await dry_service(db2).publish("A1", "L1", body())
    assert e.value.status_code == 409 and "marketing pack" in str(e.value)


async def test_instagram_without_images_is_400_and_records_nothing():
    db = make_db(images=())
    with pytest.raises(SocialError) as e:
        await dry_service(db).publish("A1", "L1", body())
    assert e.value.status_code == 400 and "image" in str(e.value)
    assert not db.get_collection("publications").docs
    # facebook alone is fine without images
    assert (await dry_service(db).publish("A1", "L1", body(channels=["facebook_page"])))[0].payload.image_urls == []


async def test_publications_are_owner_scoped_across_listings():
    db = make_db()
    db.get_collection("listings").docs.append({"_id": "L2", "agent_id": "A1", "status": "live"})
    await dry_service(db).publish("A1", "L1", body(channels=["facebook_page"]))
    assert await dry_service(db).list("A1", "L2") == []


# ---- idempotency -----------------------------------------------------------------------------------------------
async def test_idempotency_and_force():
    db = make_db()
    svc = dry_service(db)
    await svc.publish("A1", "L1", body(channels=["facebook_page"]))
    with pytest.raises(SocialError) as e:
        await svc.publish("A1", "L1", body(channels=["facebook_page", "instagram"]))
    assert e.value.status_code == 409
    assert len(db.get_collection("publications").docs) == 1  # nothing partially posted
    assert (await svc.publish("A1", "L1", body(channels=["instagram"])))[0].channel == "instagram"  # other channel is fine
    forced = await svc.publish("A1", "L1", body(channels=["facebook_page"], force=True))
    assert len(db.get_collection("publications").docs) == 3 and forced[0].status == "dry_run"
    # a new pack version is a new post
    db.get_collection("marketing_packs").docs[0]["version"] = 2
    again = await svc.publish("A1", "L1", body(channels=["facebook_page"]))
    assert again[0].pack_version == 2
    items = await svc.list("A1", "L1")
    assert len(items) == 4 and items[0].id == again[0].id  # newest first


async def test_queued_in_flight_blocks_but_stale_queued_does_not():
    db = make_db()
    t0 = datetime(2026, 1, 1, 12, 0, 0)
    svc = dry_service(db, now=lambda: t0)
    ts = t0.isoformat() + "Z"
    db.get_collection("publications").docs.append({
        "_id": "q1", "listing_id": "L1", "agent_id": "A1", "channel": "facebook_page", "pack_version": 1, "status": "queued",
        "updated_at": ts, "created_at": ts, "attempts": 0})
    with pytest.raises(SocialError) as e:
        await svc.publish("A1", "L1", body(channels=["facebook_page"]))
    assert e.value.status_code == 409
    svc.now = lambda: t0 + timedelta(minutes=10)
    assert (await svc.publish("A1", "L1", body(channels=["facebook_page"])))[0].status == "dry_run"


# ---- real mode gating ------------------------------------------------------------------------------------------
async def test_unconfigured_channel_is_recorded_as_failed():
    cfg = SocialConfig(dry_run=False, media_base_url="https://media.test", page_id="", page_token="")
    graph = FakeGraph()
    pubs = await graph_service(make_db(), graph, cfg).publish("A1", "L1", body())
    assert [(p.status, p.error) for p in pubs] == [("failed", "channel not configured")] * 2
    assert graph.calls == [] and all(p.attempts == 1 for p in pubs)


@pytest.mark.parametrize("base", ["", "http://media.test"])
async def test_non_https_media_is_refused_for_real_posts(base):
    cfg = SocialConfig(dry_run=False, media_base_url=base, page_id="PAGE1", ig_id="IG1", page_token=TOKEN)
    graph = FakeGraph()
    pubs = await graph_service(make_db(), graph, cfg).publish("A1", "L1", body())
    assert all(p.status == "failed" and "https" in p.error for p in pubs)
    assert graph.calls == []


async def test_facebook_feed_post_needs_no_media_url():
    cfg = SocialConfig(dry_run=False, media_base_url="", page_id="PAGE1", page_token=TOKEN)
    graph = FakeGraph({("POST", "/v23.0/PAGE1/feed"): (200, {"id": "PAGE1_9"})})
    p = (await graph_service(make_db(images=()), graph, cfg).publish("A1", "L1", body(channels=["facebook_page"])))[0]
    assert p.status == "published" and p.external_id == "PAGE1_9"


# ---- retry -----------------------------------------------------------------------------------------------------
async def test_retry_only_failed_and_owner_scoped():
    db = make_db()
    bad = FakeGraph({("POST", "/v23.0/PAGE1/photos"): (500, {"error": {"message": "boom", "code": 2}})})
    svc = graph_service(db, bad)
    failed = (await svc.publish("A1", "L1", body(channels=["facebook_page"])))[0]
    assert failed.status == "failed" and failed.attempts == 1
    with pytest.raises(SocialError) as e:
        await svc.retry("A2", failed.id)
    assert e.value.status_code == 404
    good = FakeGraph({("POST", "/v23.0/PAGE1/photos"): (200, {"id": "1", "post_id": "PAGE1_1"})})
    svc2 = graph_service(db, good)
    done = await svc2.retry("A1", failed.id)
    assert done.status == "published" and done.attempts == 2 and done.error is None and done.external_id == "PAGE1_1"
    assert done.id == failed.id and len(db.get_collection("publications").docs) == 1
    with pytest.raises(SocialError) as e:
        await svc2.retry("A1", failed.id)  # published now
    assert e.value.status_code == 409
    with pytest.raises(SocialError) as e:
        await svc2.retry("A1", "missing")
    assert e.value.status_code == 404


async def test_publish_again_reuses_the_failed_record():
    db = make_db()
    svc = graph_service(db, FakeGraph({("POST", "/v23.0/PAGE1/photos"): (500, {"error": {"message": "x", "code": 1}})}))
    first = (await svc.publish("A1", "L1", body(channels=["facebook_page"])))[0]
    svc2 = graph_service(db, FakeGraph({("POST", "/v23.0/PAGE1/photos"): (200, {"id": "7", "post_id": "PAGE1_7"})}))
    second = (await svc2.publish("A1", "L1", body(channels=["facebook_page"])))[0]
    assert second.id == first.id and second.status == "published" and second.attempts == 2
    assert len(db.get_collection("publications").docs) == 1


async def test_retry_refused_when_listing_no_longer_live_or_already_posted():
    db = make_db()
    svc = graph_service(db, FakeGraph({("POST", "/v23.0/PAGE1/photos"): (500, {"error": {"message": "x", "code": 1}})}))
    failed = (await svc.publish("A1", "L1", body(channels=["facebook_page"])))[0]
    db.get_collection("listings").docs[0]["status"] = "sold"
    with pytest.raises(SocialError) as e:
        await svc.retry("A1", failed.id)
    assert e.value.status_code == 409
    db.get_collection("listings").docs[0]["status"] = "live"
    await dry_service(db).publish("A1", "L1", body(channels=["facebook_page"], force=True))  # a forced post succeeded meanwhile
    with pytest.raises(SocialError) as e:
        await svc.retry("A1", failed.id)
    assert e.value.status_code == 409
