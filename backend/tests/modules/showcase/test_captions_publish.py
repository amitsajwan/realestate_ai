"""Caption guards, publish flows (MockTransport, dry-run) and the posting plan. No network."""
import json
from datetime import date
from urllib.parse import parse_qs

import httpx
import pytest

from app.platform.meta_graph.config import SocialConfig
from app.platform.meta_graph.graph import GraphPublisher
from app.modules.showcase import captions, plan, publish, samples
from app.modules.showcase.samples import HOMES

H = samples.get("kharadi-2bhk-ready")


# ---- captions ------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("h", HOMES, ids=lambda h: h.slug)
def test_deterministic_captions_pass_their_own_guards(h):
    ig, fb = captions.instagram_caption(h), captions.facebook_caption(h)
    assert captions.validate(ig, "instagram") == []
    assert captions.validate(fb, "facebook") == []
    for text in (ig, fb):
        assert "Sample listing" in text and "Illustrative home, not available for sale; real agent listings coming" in text
        assert h.price_text in text and "RERA number: shown on real listings" in text
    assert ig.splitlines()[0] == captions.hook(h)              # hook first
    assert "link in our bio" in ig and "http" not in ig.lower()
    assert 3 <= len(captions.HASHTAG.findall(ig)) <= 8
    assert "/localities" in fb and not captions.HASHTAG.findall(fb)


def test_hooks_vary_across_homes():
    assert len({captions.hook(h).split(":")[0].split(" in ")[0] for h in HOMES}) >= 2


def test_validate_catches_problems():
    good = captions.instagram_caption(H)
    assert captions.validate(good.replace("Sample listing", "Listing"), "instagram")
    assert captions.validate(good + " Call 9876543210", "instagram")
    assert captions.validate(good + " www.example.com", "instagram")
    assert captions.validate(good.replace("link in our bio", "link"), "instagram")
    assert captions.validate(good + " This is the best home", "instagram")
    assert captions.validate(good + " #a #b #c #d #e #f #g #h #i", "instagram")


class Llm:
    def __init__(self, out):
        self.out, self.calls = out, 0

    async def text(self, system, user):
        self.calls += 1
        if isinstance(self.out, Exception):
            raise self.out
        return self.out


async def test_polish_accepts_a_faithful_rewording():
    draft = captions.instagram_body(H)
    better = draft.replace("here is how a home looks", "here is how a home looks")
    out = await captions.polish(Llm(better.replace("Amenities:", "Amenities include:")), draft, H, "instagram")
    assert "Amenities include:" in out


@pytest.mark.parametrize("bad", [
    "", "Sample listing only", None,
    "Call 9876543210. " , "a" * 5000,
])
async def test_polish_rejects_bad_output(bad):
    draft = captions.instagram_body(H)
    assert await captions.polish(Llm(bad), draft, H, "instagram") == draft


async def test_polish_rejects_invented_facts_phone_hype_url_hashtag():
    draft = captions.instagram_body(H)
    for evil in (draft + " Only 2 flats left at 55 Lakh", draft + " Call 98765 43210 now".replace(" ", ""),
                 draft + " A perfect dream home", draft + " Visit https://x.example", draft + " #Hot"):
        assert await captions.polish(Llm(evil), draft, H, "instagram") == draft
    assert await captions.polish(Llm(draft.replace("Sample listing", "Listing")), draft, H, "instagram") == draft
    assert await captions.polish(Llm(draft.replace("Comment INTERESTED", "Comment")), draft, H, "instagram") == draft
    assert await captions.polish(Llm(RuntimeError("down")), draft, H, "instagram") == draft
    assert await captions.polish(None, draft, H, "instagram") == draft


async def test_build_caption_without_llm_is_the_template():
    assert await captions.build_caption(H, "instagram") == captions.instagram_caption(H)
    assert await captions.build_caption(H, "facebook") == captions.facebook_caption(H)


# ---- publish -------------------------------------------------------------------------------------------------
def cfg(dry=False, **kw):
    base = dict(dry_run=dry, page_id="PAGE1", ig_id="IG1", media_base_url="https://media.example.org", page_token="TOK123")
    base.update(kw)
    return SocialConfig(**base)


class Graph:
    """A fake Graph API that records every call."""

    def __init__(self):
        self.calls = []
        self.n = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = {k: v[0] for k, v in parse_qs(request.content.decode()).items()} if request.method == "POST" else {}
        self.calls.append((request.method, request.url.path, body, dict(request.url.params)))
        path = request.url.path
        if path.endswith("/media"):
            self.n += 1
            return httpx.Response(200, json={"id": f"c{self.n}"})
        if path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "M1"})
        if path.endswith("/photos"):
            return httpx.Response(200, json={"id": "ph1", "post_id": "PAGE1_77"})
        if request.method == "GET" and request.url.params.get("fields") == "status_code":
            return httpx.Response(200, json={"status_code": "FINISHED"})
        if request.method == "GET":
            return httpx.Response(200, json={"permalink": "https://www.instagram.com/p/ABC/"})
        return httpx.Response(404, json={"error": {"message": "nope"}})


def pub(c, g):
    return GraphPublisher(c, transport=httpx.MockTransport(g.handler), poll_interval=0, poll_timeout=5)


async def test_instagram_carousel_flow(tmp_path):
    g, c = Graph(), cfg()
    r = await publish.publish_instagram(H.slug, cfg=c, publisher=pub(c, g), root=tmp_path)
    items = [x for x in g.calls if x[0] == "POST" and x[2].get("is_carousel_item")]
    assert [x[2]["image_url"] for x in items] == [f"https://media.example.org/uploads/showcase/{H.slug}/{i}.jpg" for i in range(1, 6)]
    container = next(x for x in g.calls if x[2].get("media_type") == "CAROUSEL")
    assert container[2]["children"] == "c1,c2,c3,c4,c5"
    assert "Sample listing" in container[2]["caption"] and "link in our bio" in container[2]["caption"]
    assert any(x[1].endswith("/media_publish") for x in g.calls)
    assert r.permalink == "https://www.instagram.com/p/ABC/" and not r.dry_run and r.channel == "instagram"
    assert (tmp_path / H.slug / "1.jpg").exists()     # rendered on demand


async def test_facebook_photo_flow(tmp_path):
    g, c = Graph(), cfg()
    r = await publish.publish_facebook(H.slug, cfg=c, publisher=pub(c, g), root=tmp_path)
    post = next(x for x in g.calls if x[1].endswith("/photos"))
    assert post[2]["url"] == f"https://media.example.org/uploads/showcase/{H.slug}/facebook.jpg"
    assert "Sample listing" in post[2]["caption"] and "/localities" in post[2]["caption"]
    assert r.permalink == "https://www.facebook.com/PAGE1_77"


async def test_dry_run_never_touches_the_network(tmp_path):
    def boom(request):
        raise AssertionError("network used in dry run")
    c = cfg(dry=True, page_token="", media_base_url="")
    res = await publish.publish_showcase(H.slug, "both", cfg=c, root=tmp_path)
    assert [r.channel for r in res] == ["instagram", "facebook_page"]
    assert all(r.dry_run and r.external_id.startswith("dryrun_") for r in res)
    assert res[0].image_urls[0] == f"/uploads/showcase/{H.slug}/1.jpg"


async def test_env_dry_run_default(monkeypatch, tmp_path):
    monkeypatch.delenv("SOCIAL_DRY_RUN", raising=False)
    monkeypatch.delenv("PUBLIC_MEDIA_BASE_URL", raising=False)
    (r,) = await publish.publish_showcase(H.slug, "facebook", root=tmp_path)
    assert r.dry_run


async def test_real_post_needs_config_and_https(tmp_path):
    with pytest.raises(publish.ShowcaseError, match="not configured"):
        await publish.publish_instagram(H.slug, cfg=cfg(page_token=""), root=tmp_path)
    with pytest.raises(publish.ShowcaseError, match="https"):
        await publish.publish_instagram(H.slug, cfg=cfg(media_base_url="http://x.test"), root=tmp_path)


async def test_caption_without_label_is_refused_and_nothing_sent(tmp_path):
    g, c = Graph(), cfg()
    with pytest.raises(publish.ShowcaseError, match="refused"):
        await publish.publish_instagram(H.slug, cfg=c, publisher=pub(c, g), caption="Lovely home #a #b #c link in our bio", root=tmp_path)
    assert g.calls == []


async def test_graph_error_becomes_showcase_error(tmp_path):
    c = cfg()
    bad = GraphPublisher(c, transport=httpx.MockTransport(lambda r: httpx.Response(400, json={"error": {"code": 190, "message": "bad token TOK123"}})))
    with pytest.raises(publish.ShowcaseError) as e:
        await publish.publish_facebook(H.slug, cfg=c, publisher=bad, root=tmp_path)
    assert "TOK123" not in str(e.value)


async def test_unknown_slug_and_channel(tmp_path):
    with pytest.raises(KeyError):
        await publish.publish_instagram("nope", cfg=cfg(dry=True), root=tmp_path)
    with pytest.raises(publish.ShowcaseError):
        await publish.publish_showcase(H.slug, "tiktok")


# ---- plan ----------------------------------------------------------------------------------------------------
def test_two_week_plan_alternates_channels_and_areas():
    slots = plan.schedule_plan(date(2026, 10, 6), 14)
    assert len(slots) == 7
    assert [(b.day - a.day).days for a, b in zip(slots, slots[1:])] == [2] * 6
    assert all(a.channel != b.channel for a, b in zip(slots, slots[1:]))
    assert all(a.locality != b.locality for a, b in zip(slots, slots[1:]))
    assert len({s.slug for s in slots}) == 7           # no home repeats within two weeks
    assert {s.locality for s in slots} == {"Kharadi", "Upper Kharadi", "Wagholi"}


def test_admin_script_plan_and_list(capsys):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("showcase_admin", Path(__file__).resolve().parents[3] / "scripts" / "showcase_admin.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main(["schedule-plan", "--start", "2026-10-06"]) == 0
    assert "kharadi-2bhk-ready" in capsys.readouterr().out
    assert mod.main(["list"]) == 0
