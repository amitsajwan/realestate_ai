import logging

import httpx
import pytest

from app.platform.meta_graph.publisher import DryRunPublisher, Post, sanitize
from app.modules.social.schemas import PublishIn

from .test_social_helpers import REAL, TOKEN, Clock, FakeGraph, graph_service, make_db

pytestmark = pytest.mark.asyncio

V = "/v23.0"


def body(*channels, **over) -> PublishIn:
    return PublishIn(channels=list(channels), approve=True, consent=True, **over)


async def run(graph, *channels, images=("cover", "facts", "amenities", "cta"), clock=None, db=None):
    db = db or make_db(images=images)
    return await graph_service(db, graph, REAL, clock).publish("A1", "L1", body(*channels))


# ---- Facebook --------------------------------------------------------------------------------------------------
async def test_facebook_photo_flow():
    g = FakeGraph({("POST", f"{V}/PAGE1/photos"): (200, {"id": "555", "post_id": "PAGE1_555"})})
    (p,) = await run(g, "facebook_page")
    assert g.order() == [f"POST {V}/PAGE1/photos"]
    form = g.calls[0]["form"]
    assert form == {"url": "https://media.test/uploads/marketing/L1/cover.jpg", "published": "true", "access_token": TOKEN,
                    "caption": "Ready 2 BHK in Baner\n\n\U0001F517 Details and photos: https://site.test/agent/rahul/listings/L1?src=whatsapp"}
    assert (p.status, p.external_id, p.permalink, p.error) == ("published", "PAGE1_555", "https://www.facebook.com/PAGE1_555", None)
    assert TOKEN not in p.model_dump_json()


async def test_facebook_photo_without_post_id_fetches_link_best_effort():
    g = FakeGraph({("POST", f"{V}/PAGE1/photos"): (200, {"id": "555"}), ("GET", f"{V}/555"): (200, {"link": "https://fb.test/p/555"})})
    (p,) = await run(g, "facebook_page")
    assert p.external_id == "555" and p.permalink == "https://fb.test/p/555"
    assert g.calls[1]["query"] == {"fields": "link", "access_token": TOKEN}
    g2 = FakeGraph({("POST", f"{V}/PAGE1/photos"): (200, {"id": "555"}), ("GET", f"{V}/555"): (400, {"error": {"message": "x"}})})
    (p2,) = await run(g2, "facebook_page")
    assert p2.status == "published" and p2.permalink is None


async def test_facebook_feed_flow_when_no_image():
    g = FakeGraph({("POST", f"{V}/PAGE1/feed"): (200, {"id": "PAGE1_9"})})
    (p,) = await run(g, "facebook_page", images=())
    assert g.order() == [f"POST {V}/PAGE1/feed"]
    assert g.calls[0]["form"] == {"message": "Ready 2 BHK in Baner\n\n\U0001F517 Details and photos: https://site.test/agent/rahul/listings/L1?src=whatsapp",
                                  "link": "https://site.test/agent/rahul/listings/L1?src=whatsapp", "access_token": TOKEN}
    assert p.status == "published" and p.external_id == "PAGE1_9"


async def test_graph_version_is_configurable():
    g = FakeGraph({("POST", "/v25.0/PAGE1/photos"): (200, {"id": "1", "post_id": "P_1"})})
    cfg = REAL.__class__(**{**REAL.__dict__, "graph_version": "v25.0"})
    (p,) = await graph_service(make_db(), g, cfg).publish("A1", "L1", body("facebook_page"))
    assert p.status == "published"


# ---- Instagram -------------------------------------------------------------------------------------------------
def ig_routes(status_codes=("FINISHED",), **over):
    n = iter(range(100, 200))
    routes = {("POST", f"{V}/IG1/media"): lambda c: (200, {"id": f"C{next(n)}"}),
              ("GET", f"{V}/C104"): [(200, {"status_code": s}) for s in status_codes],
              ("POST", f"{V}/IG1/media_publish"): (200, {"id": "M1"}),
              ("GET", f"{V}/M1"): (200, {"permalink": "https://instagram.com/p/abc"})}
    routes.update(over)
    return routes


async def test_instagram_carousel_flow_exact_order_and_params():
    g = FakeGraph(ig_routes(("IN_PROGRESS", "FINISHED")))
    clock = Clock()
    (p,) = await run(g, "instagram", clock=clock)
    assert g.order() == [f"POST {V}/IG1/media"] * 5 + [f"GET {V}/C104", f"GET {V}/C104", f"POST {V}/IG1/media_publish", f"GET {V}/M1"]
    urls = [f"https://media.test/uploads/marketing/L1/{k}.jpg" for k in ("cover", "facts", "amenities", "cta")]
    for i, call in enumerate(g.calls[:4]):
        assert call["form"] == {"image_url": urls[i], "is_carousel_item": "true", "access_token": TOKEN}
    assert g.calls[4]["form"] == {"media_type": "CAROUSEL", "children": "C100,C101,C102,C103", "caption": "2 BHK in Baner\n\n#Pune #Baner",
                                  "access_token": TOKEN}
    assert g.calls[5]["query"] == {"fields": "status_code", "access_token": TOKEN}
    assert g.calls[7]["form"] == {"creation_id": "C104", "access_token": TOKEN}
    assert g.calls[8]["query"] == {"fields": "permalink", "access_token": TOKEN}
    assert clock.sleeps == 1
    assert (p.status, p.external_id, p.permalink) == ("published", "M1", "https://instagram.com/p/abc")


async def test_instagram_single_image_flow():
    g = FakeGraph({("POST", f"{V}/IG1/media"): (200, {"id": "C1"}), ("GET", f"{V}/C1"): (200, {"status_code": "FINISHED"}),
                   ("POST", f"{V}/IG1/media_publish"): (200, {"id": "M1"}), ("GET", f"{V}/M1"): (200, {"permalink": "https://ig/p"})})
    (p,) = await run(g, "instagram", images=("cover",))
    assert g.order() == [f"POST {V}/IG1/media", f"GET {V}/C1", f"POST {V}/IG1/media_publish", f"GET {V}/M1"]
    assert g.calls[0]["form"] == {"image_url": "https://media.test/uploads/marketing/L1/cover.jpg", "caption": "2 BHK in Baner\n\n#Pune #Baner",
                                  "access_token": TOKEN}
    assert p.status == "published"


@pytest.mark.parametrize("bad", ["ERROR", "EXPIRED"])
async def test_instagram_container_error_fails_and_never_publishes(bad):
    g = FakeGraph(ig_routes((bad,)))
    (p,) = await run(g, "instagram")
    assert p.status == "failed" and bad in p.error
    assert not any(c["path"].endswith("media_publish") for c in g.calls)


async def test_instagram_container_timeout_is_bounded_and_fast():
    g = FakeGraph(ig_routes(("IN_PROGRESS",)))
    clock = Clock()
    (p,) = await run(g, "instagram", clock=clock)
    assert p.status == "failed" and "not ready after 60 s" in p.error and "IN_PROGRESS" in p.error
    assert clock.t >= 60 and clock.sleeps == 30  # 2 s interval, bounded, no real waiting
    assert not any(c["path"].endswith("media_publish") for c in g.calls)


async def test_instagram_permalink_failure_is_best_effort():
    g = FakeGraph(ig_routes())
    g.routes[("GET", f"{V}/M1")] = (500, {"error": {"message": "nope"}})
    (p,) = await run(g, "instagram")
    assert p.status == "published" and p.external_id == "M1" and p.permalink is None


async def test_instagram_caps_carousel_at_ten():
    from app.platform.meta_graph.graph import GraphPublisher
    from app.platform.meta_graph.publisher import Post
    g = FakeGraph({("POST", f"{V}/IG1/media"): lambda c: (200, {"id": f"C{len(g.calls)}"}),
                   ("GET", f"{V}/C11"): (200, {"status_code": "FINISHED"}), ("POST", f"{V}/IG1/media_publish"): (200, {"id": "M"})})
    pub = GraphPublisher(REAL, transport=g.transport())
    await pub.publish(Post("instagram", "cap", [f"https://m.test/uploads/{i}.jpg" for i in range(14)]))
    assert sum(1 for c in g.calls if c["path"].endswith("/IG1/media")) == 11  # 10 items + 1 carousel


# ---- error handling --------------------------------------------------------------------------------------------
async def test_graph_error_shape_is_parsed():
    err = {"error": {"message": "Invalid OAuth access token.", "type": "OAuthException", "code": 190, "error_subcode": 460, "fbtrace_id": "AbC123"}}
    (p,) = await run(FakeGraph({("POST", f"{V}/PAGE1/photos"): (400, err)}), "facebook_page")
    assert p.status == "failed" and p.error == "Graph API error 190/460: Invalid OAuth access token. (fbtrace_id AbC123)"


async def test_graph_error_echoing_the_token_never_leaks(caplog):
    caplog.set_level(logging.DEBUG)
    echo = {"error": {"message": f"Invalid token {TOKEN} for request ?access_token={TOKEN}&x=1 "
                                 f'{{"access_token":"{TOKEN}"}} Bearer {TOKEN} ' + "long " * 200, "code": 190, "fbtrace_id": "T"}}
    db = make_db()
    g = FakeGraph({("POST", f"{V}/PAGE1/photos"): (400, echo)})
    (p,) = await graph_service(db, g).publish("A1", "L1", body("facebook_page"))
    assert p.status == "failed" and len(p.error) <= 300
    stored = db.get_collection("publications").docs[0]
    for blob in (p.model_dump_json(), repr(stored), caplog.text):
        assert TOKEN not in blob and TOKEN[:12] not in blob
    assert "access_token=" not in p.error or "access_token=[redacted]" in p.error
    assert "failed" in caplog.text  # the failure is logged, sanitised


async def test_bare_token_in_a_non_json_body_does_not_leak():
    resp = httpx.Response(502, text=f"<html>bad gateway ?access_token={TOKEN}</html>")
    (p,) = await run(FakeGraph({("POST", f"{V}/PAGE1/photos"): resp}), "facebook_page")
    assert p.status == "failed" and "non-JSON" in p.error and "502" in p.error and TOKEN not in p.error


async def test_timeout_and_transport_errors_are_recorded_not_raised():
    (p,) = await run(FakeGraph({("POST", f"{V}/PAGE1/photos"): httpx.ReadTimeout("slow")}), "facebook_page")
    assert p.status == "failed" and p.error == "Graph API request timed out"
    exc = httpx.ConnectError(f"cannot connect https://graph.facebook.com/x?access_token={TOKEN}")
    (p,) = await run(FakeGraph({("POST", f"{V}/PAGE1/photos"): exc}), "facebook_page")
    assert p.status == "failed" and "ConnectError" in p.error and TOKEN not in p.error


async def test_unexpected_exception_is_recorded_not_raised():
    (p,) = await run(FakeGraph({("POST", f"{V}/PAGE1/photos"): RuntimeError(f"kaboom {TOKEN}")}), "facebook_page")
    assert p.status == "failed" and "RuntimeError" in p.error and TOKEN not in p.error


async def test_missing_id_and_non_object_json():
    (p,) = await run(FakeGraph({("POST", f"{V}/PAGE1/photos"): (200, {})}), "facebook_page")
    assert p.status == "failed" and "did not return an id" in p.error
    (p,) = await run(FakeGraph({("POST", f"{V}/PAGE1/photos"): (200, ["x"])}), "facebook_page")
    assert p.status == "failed" and "unexpected response" in p.error


async def test_one_channel_failing_does_not_stop_the_other():
    g = FakeGraph({("POST", f"{V}/PAGE1/photos"): (400, {"error": {"message": "nope", "code": 10}}), **ig_routes()})
    fb, ig = await run(g, "facebook_page", "instagram")
    assert fb.status == "failed" and ig.status == "published"


async def test_graph_publisher_itself_refuses_http_urls():
    from app.platform.meta_graph.graph import GraphPublisher
    from app.platform.meta_graph.publisher import PublishError
    g = FakeGraph()
    with pytest.raises(PublishError):
        await GraphPublisher(REAL, transport=g.transport()).publish(Post("facebook_page", "t", ["http://x.test/a.jpg"]))
    assert g.calls == []


# ---- helpers ---------------------------------------------------------------------------------------------------
async def test_sanitize_and_dry_run_publisher():
    assert sanitize(f"a access_token=abc123&b=1 c", ["zzz"]) == "a access_token=[redacted]&b=1 c"
    assert sanitize("secret zzz here", ["zzz"]) == "secret [redacted] here"
    assert sanitize("x" * 1000).endswith("...") and len(sanitize("x" * 1000)) == 300
    assert sanitize(None) == ""
    r = await DryRunPublisher().publish(Post("instagram", "t", []))
    assert r.external_id.startswith("dryrun_") and r.permalink is None
