"""Photo tags (kind and room): fake vision clients only (no network). The schema check, the cache, the fallbacks (no client,
a rate limit, a wrong reply, tagging off) and the room-flow order."""
from pathlib import Path

import httpx
import pytest

from app.modules.photoquality import tagging as tg
from app.modules.photoquality import vision_review as vr

from ..photo_helpers import save, scene

pytestmark = pytest.mark.asyncio


class FakeTagger:
    def __init__(self, *replies, model="fake-vision"):
        self.replies, self.model, self.calls = list(replies), model, []

    async def ask(self, images, prompt, system, max_tokens=600, retry=True):
        self.calls.append({"n": len(images), "prompt": prompt, "system": system, "retry": retry})
        r = self.replies.pop(0) if self.replies else None
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    vr._MEM.clear()
    monkeypatch.delenv("AI_PHOTO_TAGS", raising=False)
    monkeypatch.delenv("AI_VISION_REVIEW", raising=False)
    yield
    vr._MEM.clear()


@pytest.fixture
def photos(tmp_path):
    return [save(tmp_path / "images", f"p{i}.jpg", scene(i + 1, (320, 240))) for i in range(5)]


def reply(*pairs):
    return {"photos": [{"kind": k, "room": r} for k, r in pairs]}


async def test_tags_are_verified_and_cached_on_disk(photos, tmp_path):
    fake = FakeTagger(reply(("interior", "Kitchen"), ("Exterior", "living"), ("pool deck", None)),
                      reply(("interior", "bathroom"), ("interior", "attic")))
    tags = await tg.tag_photos(photos, clients=[fake], cache=tmp_path / "c")
    assert [c["n"] for c in fake.calls] == [3, 2] and all(c["retry"] is False for c in fake.calls)
    assert tags[photos[0]] == {"kind": "interior", "room": "kitchen"}
    assert tags[photos[1]] == {"kind": "exterior", "room": None}           # a building from outside has no room
    assert tags[photos[2]] == {"kind": "other", "room": None}              # an unknown kind is 'other'
    assert tags[photos[3]] == {"kind": "interior", "room": "bath"}
    assert tags[photos[4]] == {"kind": "interior", "room": "other"}        # an unknown room is 'other'
    vr._MEM.clear()                                                         # the disk cache survives a restart
    again = FakeTagger()
    assert await tg.tag_photos(photos, clients=[again], cache=tmp_path / "c") == tags and again.calls == []
    assert tg.cached_tags(photos, cache=tmp_path / "c") == tags


async def test_a_wrong_reply_is_not_used_and_the_next_provider_is_asked(photos, tmp_path):
    short = FakeTagger(reply(("interior", "kitchen")), model="a")          # 1 item for 3 photos: could tag the wrong photo
    ok = FakeTagger(reply(("interior", "living"), ("view", "balcony"), ("amenity", None)), model="b")
    tags = await tg.tag_photos(photos[:3], clients=[short, ok], cache=tmp_path / "c")
    assert tags[photos[1]] == {"kind": "view", "room": "balcony"} and len(tags) == 3
    for bad in ({"photos": "x"}, None, "not json", {"photos": [1, 2, 3]}):
        assert tg.clean_reply(bad, 3) is None


async def test_no_client_a_rate_limit_or_tagging_off_means_no_tags(photos, tmp_path, monkeypatch):
    assert await tg.tag_photos(photos, clients=[], cache=tmp_path / "c") == {}
    limited = FakeTagger(None, reply(("interior", "living")))               # the first batch fails: the run stops there
    assert await tg.tag_photos(photos, clients=[limited], cache=tmp_path / "c") == {} and len(limited.calls) == 1
    boom = FakeTagger(RuntimeError("down"))
    assert await tg.tag_photos(photos, clients=[boom], cache=tmp_path / "c") == {}
    monkeypatch.setattr(tg, "default_tag_clients", lambda: [])               # no key configured
    assert await tg.tag_photos(photos, cache=tmp_path / "c") == {}
    ok = FakeTagger(reply(("interior", "living"), ("interior", "kitchen"), ("exterior", None)))
    await tg.tag_photos(photos[:3], clients=[ok], cache=tmp_path / "c")
    monkeypatch.setenv("AI_PHOTO_TAGS", "off")
    never = FakeTagger(reply(("interior", "living")))
    assert await tg.tag_photos(photos[:3], clients=[never], cache=tmp_path / "c") == {} and never.calls == []
    assert tg.cached_tags(photos[:3], cache=tmp_path / "c") == {} and tg.default_tag_clients() == []
    monkeypatch.setenv("AI_PHOTO_TAGS", "on")
    monkeypatch.setenv("AI_VISION_REVIEW", "off")
    assert tg.default_tag_clients() == [] and tg.cached_tags(photos[:3], cache=tmp_path / "c") == {}


async def test_a_429_gives_up_at_once_without_waiting(photos, tmp_path, monkeypatch):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(429, headers={"retry-after": "30"})

    async def no_sleep(_):
        raise AssertionError("tagging must not wait on a rate limit")

    monkeypatch.setattr(vr.asyncio, "sleep", no_sleep)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = vr.OpenAIVision("k", "m", "https://x", timeout=tg.TAG_TIMEOUT, client=http)
        assert await tg.tag_photos(photos, clients=[client], cache=tmp_path / "c") == {}
    assert len(seen) == 1                                                    # one request, no retry, no further batches


async def test_only_the_first_photos_are_tagged(tmp_path):
    many = [save(tmp_path / "images", f"q{i}.jpg", scene(i + 20, (200, 150))) for i in range(12)]
    fake = FakeTagger(*[reply(*[("interior", "living")] * 3)] * 4)
    tags = await tg.tag_photos(many, clients=[fake], cache=tmp_path / "c")
    assert len(tags) == tg.MAX_TAGGED and len(fake.calls) == tg.MAX_TAGGED // 3


def test_room_order_keeps_the_hero_and_walks_through_the_home():
    p = {n: Path(f"{n}.jpg") for n in ("hero", "bath", "kitchen", "pool", "living", "outside", "bed", "plan", "x", "balcony")}
    tags = {p["hero"]: {"kind": "interior", "room": "bedroom"}, p["bath"]: {"kind": "interior", "room": "bath"},
            p["kitchen"]: {"kind": "interior", "room": "kitchen"}, p["pool"]: {"kind": "amenity", "room": None},
            p["living"]: {"kind": "interior", "room": "living"}, p["outside"]: {"kind": "exterior", "room": None},
            p["bed"]: {"kind": "interior", "room": "bedroom"}, p["plan"]: {"kind": "floor_plan", "room": None},
            p["balcony"]: {"kind": "view", "room": "balcony"}}
    order = [p[n] for n in ("hero", "bath", "kitchen", "pool", "plan", "x", "living", "outside", "bed", "balcony")]
    assert [x.stem for x in tg.room_order(order, tags)] == [
        "hero", "outside", "living", "kitchen", "bed", "bath", "balcony", "pool", "x", "plan"]
    assert tg.room_order(order, {}) == order                                 # no tags: the ranked order stands
    two_beds = [p["hero"], p["bed"], Path("b2.jpg")]
    tags2 = {**tags, Path("b2.jpg"): {"kind": "interior", "room": "bedroom"}}
    assert tg.room_order(two_beds, tags2) == two_beds                        # the agent's order breaks ties
