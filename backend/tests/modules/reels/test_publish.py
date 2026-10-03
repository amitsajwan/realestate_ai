import re
from urllib.parse import parse_qsl

import httpx
import pytest

from app.modules.reels import publish
from app.modules.reels.publish import ReelPublisher
from app.platform.meta_graph.config import SocialConfig
from app.platform.meta_graph.publisher import PublishError

pytestmark = pytest.mark.asyncio

TOKEN = "EAAB" + "x" * 40
CFG = SocialConfig(dry_run=False, graph_version="v23.0", page_id="PAGE1", ig_id="IG1", media_base_url="https://media.test", page_token=TOKEN)
URL = "https://media.test/uploads/reels/reel-abc.mp4"
V = "/v23.0"


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    async def sleep(self, s):
        self.t += s


class Fake:
    """Routes (method, path) -> (status, json) or a list of them (consumed in order, the last repeats); records every request."""

    def __init__(self, routes):
        self.routes = {k: list(v) if isinstance(v, list) else [v] for k, v in routes.items()}
        self.calls = []

    def __call__(self, req: httpx.Request) -> httpx.Response:
        raw = req.content or b""
        form = {}
        if req.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            form = dict(parse_qsl(raw.decode()))
        self.calls.append({"method": req.method, "host": req.url.host, "path": req.url.path, "form": form,
                           "headers": dict(req.headers), "raw": raw})
        q = self.routes.get((req.method, req.url.path))
        if not q:
            return httpx.Response(404, json={"error": {"message": f"no route {req.method} {req.url.path}", "code": 1}})
        status, body = q.pop(0) if len(q) > 1 else q[0]
        return httpx.Response(status, json=body)

    def order(self):
        return [f"{c['method']} {c['path']}" for c in self.calls]


def pub(fake, clock=None, **kw):
    clock = clock or Clock()
    return ReelPublisher(CFG, transport=httpx.MockTransport(fake), sleep=clock.sleep, clock=clock, **kw)


# ---- Instagram -------------------------------------------------------------------------------------------------
async def test_instagram_reel_flow_polls_then_publishes():
    f = Fake({("POST", f"{V}/IG1/media"): (200, {"id": "C1"}),
              ("GET", f"{V}/C1"): [(200, {"status_code": "IN_PROGRESS"}), (200, {"status_code": "IN_PROGRESS"}), (200, {"status_code": "FINISHED"})],
              ("POST", f"{V}/IG1/media_publish"): (200, {"id": "M1"}),
              ("GET", f"{V}/M1"): (200, {"permalink": "https://www.instagram.com/reel/abc/"})})
    r = await pub(f).publish_reel("instagram", URL, "Caption here")
    assert f.order() == [f"POST {V}/IG1/media", f"GET {V}/C1", f"GET {V}/C1", f"GET {V}/C1", f"POST {V}/IG1/media_publish", f"GET {V}/M1"]
    assert f.calls[0]["form"] == {"media_type": "REELS", "video_url": URL, "caption": "Caption here", "share_to_feed": "true",
                                  "access_token": TOKEN}
    assert f.calls[4]["form"]["creation_id"] == "C1"
    assert (r.external_id, r.permalink) == ("M1", "https://www.instagram.com/reel/abc/")


async def test_instagram_processing_failure_is_reported_without_token():
    f = Fake({("POST", f"{V}/IG1/media"): (200, {"id": "C1"}),
              ("GET", f"{V}/C1"): (200, {"status_code": "ERROR", "status": f"2207026: bad video access_token={TOKEN}"})})
    with pytest.raises(PublishError) as e:
        await pub(f).publish_reel("instagram", URL, "c")
    assert "ERROR" in str(e.value) and TOKEN not in str(e.value)
    assert not any(c["path"].endswith("media_publish") for c in f.calls)


async def test_instagram_poll_times_out_after_five_minutes_by_default():
    clock = Clock()
    f = Fake({("POST", f"{V}/IG1/media"): (200, {"id": "C1"}), ("GET", f"{V}/C1"): (200, {"status_code": "IN_PROGRESS"})})
    with pytest.raises(PublishError) as e:
        await pub(f, clock).publish_reel("instagram", URL, "c")
    assert "300 s" in str(e.value) and "IN_PROGRESS" in str(e.value)
    assert 300 <= clock.t <= 310
    assert len([c for c in f.calls if c["method"] == "GET"]) > 10


async def test_poll_timeout_is_configurable():
    clock = Clock()
    f = Fake({("POST", f"{V}/IG1/media"): (200, {"id": "C1"}), ("GET", f"{V}/C1"): (200, {"status_code": "IN_PROGRESS"})})
    with pytest.raises(PublishError) as e:
        await pub(f, clock, poll_interval=1.0, poll_timeout=10.0).publish_reel("instagram", URL, "c")
    assert "10 s" in str(e.value)


async def test_instagram_api_error_is_sanitised():
    f = Fake({("POST", f"{V}/IG1/media"): (400, {"error": {"message": f"Invalid OAuth access token {TOKEN}", "code": 190, "fbtrace_id": "T1"}})})
    with pytest.raises(PublishError) as e:
        await pub(f).publish_reel("instagram", URL, "c")
    assert "190" in str(e.value) and TOKEN not in str(e.value)


async def test_instagram_permalink_failure_still_succeeds():
    f = Fake({("POST", f"{V}/IG1/media"): (200, {"id": "C1"}), ("GET", f"{V}/C1"): (200, {"status_code": "FINISHED"}),
              ("POST", f"{V}/IG1/media_publish"): (200, {"id": "M1"}), ("GET", f"{V}/M1"): (500, {"error": {"message": "x"}})})
    r = await pub(f).publish_reel("instagram", URL, "c")
    assert r.external_id == "M1" and r.permalink is None


async def test_non_https_video_url_is_refused_before_any_request():
    f = Fake({})
    with pytest.raises(PublishError):
        await pub(f).publish_reel("instagram", "http://media.test/uploads/reels/a.mp4", "c")
    assert f.calls == []


# ---- Facebook ---------------------------------------------------------------------------------------------------
def fb_routes(status_seq=None, upload=(200, {"success": True}), finish=(200, {"success": True})):
    start = (200, {"video_id": "VID1", "upload_url": "https://rupload.facebook.com/video-upload/VID1"})
    return {("POST", f"{V}/PAGE1/video_reels"): [start, finish],
            ("POST", f"/video-upload/{CFG.graph_version}/VID1"): upload,
            ("POST", "/video-upload/VID1"): upload,
            ("GET", f"{V}/VID1"): status_seq or (200, {"status": {"video_status": "upload_complete"}})}


async def test_facebook_reel_flow_with_hosted_file_url():
    f = Fake(fb_routes())
    r = await pub(f).publish_reel("facebook_page", URL, "Desc")
    assert f.order() == [f"POST {V}/PAGE1/video_reels", "POST /video-upload/VID1", f"GET {V}/VID1", f"POST {V}/PAGE1/video_reels"]
    start, up, _, finish = f.calls
    assert start["form"] == {"upload_phase": "start", "access_token": TOKEN}
    assert up["host"] == "rupload.facebook.com"
    assert up["headers"]["authorization"] == f"OAuth {TOKEN}" and up["headers"]["file_url"] == URL
    assert finish["form"] == {"upload_phase": "finish", "video_id": "VID1", "video_state": "PUBLISHED", "description": "Desc", "access_token": TOKEN}
    assert r.external_id == "VID1" and r.permalink == "https://www.facebook.com/reel/VID1"


async def test_facebook_reel_flow_with_binary_upload(tmp_path):
    mp4 = tmp_path / "r.mp4"
    mp4.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"x" * 100)
    f = Fake(fb_routes())
    await pub(f).publish_reel("facebook_page", URL, "Desc", file_path=mp4)
    up = f.calls[1]
    assert up["raw"] == mp4.read_bytes()
    assert up["headers"]["offset"] == "0" and up["headers"]["file_size"] == str(mp4.stat().st_size)
    assert "file_url" not in up["headers"]


async def test_facebook_waits_for_upload_before_finishing():
    seq = [(200, {"status": {"video_status": "uploading"}}), (200, {"status": {"video_status": "uploading"}}),
           (200, {"status": {"video_status": "processing"}})]
    f = Fake(fb_routes(status_seq=seq))
    await pub(f).publish_reel("facebook_page", URL, "d")
    assert f.order().count(f"GET {V}/VID1") == 3 and f.order()[-1] == f"POST {V}/PAGE1/video_reels"


async def test_facebook_upload_failure_status_failure_and_timeout():
    f = Fake(fb_routes(upload=(400, {"error": {"message": f"bad file access_token={TOKEN}", "code": 100}})))
    with pytest.raises(PublishError) as e:
        await pub(f).publish_reel("facebook_page", URL, "d")
    assert TOKEN not in str(e.value) and "100" in str(e.value)
    f2 = Fake(fb_routes(status_seq=(200, {"status": {"video_status": "upload_failed"}})))
    with pytest.raises(PublishError) as e2:
        await pub(f2).publish_reel("facebook_page", URL, "d")
    assert "upload_failed" in str(e2.value)
    clock = Clock()
    f3 = Fake(fb_routes(status_seq=(200, {"status": {"video_status": "uploading"}})))
    with pytest.raises(PublishError) as e3:
        await pub(f3, clock, poll_timeout=20.0).publish_reel("facebook_page", URL, "d")
    assert "20 s" in str(e3.value)
    assert not any(c["form"].get("upload_phase") == "finish" for c in f3.calls)


async def test_token_is_only_sent_to_rupload_host():
    routes = fb_routes()
    routes[("POST", f"{V}/PAGE1/video_reels")][0] = (200, {"video_id": "VID1", "upload_url": "https://evil.example/steal"})
    f = Fake(routes)
    await pub(f).publish_reel("facebook_page", URL, "d")
    up = f.calls[1]
    assert up["host"] == "rupload.facebook.com" and up["path"] == f"/video-upload/{CFG.graph_version}/VID1"
    assert all(c["host"] != "evil.example" for c in f.calls)


async def test_facebook_start_without_video_id_fails():
    f = Fake({("POST", f"{V}/PAGE1/video_reels"): (200, {})})
    with pytest.raises(PublishError):
        await pub(f).publish_reel("facebook_page", URL, "d")


async def test_facebook_finish_error_is_sanitised():
    f = Fake(fb_routes(finish=(400, {"error": {"message": f"oops {TOKEN}", "code": 368}})))
    with pytest.raises(PublishError) as e:
        await pub(f).publish_reel("facebook_page", URL, "d")
    assert TOKEN not in str(e.value) and "368" in str(e.value)


# ---- dry run, config, helpers ------------------------------------------------------------------------------------
async def test_dry_run_returns_fake_id_and_never_calls_network():
    def boom(req):
        raise AssertionError("network used in dry run")

    dry = SocialConfig(dry_run=True, page_id="P", ig_id="I", media_base_url="https://media.test", page_token=TOKEN)
    for ch in ("instagram", "facebook_page"):
        r = await publish.publish_reel(ch, URL, "c", cfg=dry, transport=httpx.MockTransport(boom))
        assert r.external_id.startswith("dryrun_")


async def test_unconfigured_channel_and_unknown_channel():
    with pytest.raises(PublishError):
        await ReelPublisher(SocialConfig(dry_run=False)).publish_reel("instagram", URL, "c")
    with pytest.raises(PublishError):
        await publish.publish_reel("tiktok", URL, "c", cfg=CFG)


def test_public_url_and_stage(tmp_path):
    assert publish.public_url(CFG, "reel-abc.mp4") == URL
    for bad in ("../x.mp4", "a b.mp4", "x.mov", ""):
        with pytest.raises(PublishError):
            publish.public_url(CFG, bad)
    with pytest.raises(PublishError):
        publish.public_url(SocialConfig(media_base_url="http://x.test"), "a.mp4")
    src = tmp_path / "in.mp4"
    src.write_bytes(b"abc")
    name = publish.stage(src, tmp_path / "uploads")
    assert re.fullmatch(r"reel-[0-9a-f]{12}\.mp4", name) and (tmp_path / "uploads" / "reels" / name).read_bytes() == b"abc"
