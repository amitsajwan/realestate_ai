"""The reel's photos: the agent's own uploads (the enhanced copy when kept on), ranked by photoquality: no duplicates, no blurry
or dark photo unless the reel needs it to reach two, the hero on the first scene."""
import pytest

from app.modules.reels import listing_reel as lr

from ..photo_helpers import blurred, brighter, darker, save, scene
from .test_listing_reel import AGENT, Renderer, setup


def media(*names):
    return [{"url": f"/uploads/images/{n}.jpg", "kind": "image", "order": i} for i, n in enumerate(names)]


@pytest.fixture
def up(tmp_path):
    d = tmp_path / "images"
    for name, img in {"tall": scene(6, (900, 1200)), "blur": blurred(scene(4)), "a": scene(1), "a_copy": brighter(scene(1)),
                      "b": scene(2), "c": scene(3), "d": scene(7), "e": scene(11), "dark": darker(scene(5))}.items():
        save(d, f"{name}.jpg", img)
    return tmp_path


def names(paths):
    return [p.stem for p in paths]


def test_scene_photos_drop_copies_and_blurry_ones_and_lead_with_the_hero(up):
    listing = {"media": media("tall", "blur", "a", "a_copy", "b", "dark")}
    assert names(lr.listing_photos(listing, up)) == ["tall", "blur", "a", "a_copy", "b", "dark"]
    assert names(lr.scene_photos(listing, up)) == ["a", "tall", "b"]


def test_scene_photos_keep_two_when_only_weak_ones_exist_and_stop_at_five(up):
    assert names(lr.scene_photos({"media": media("blur", "dark")}, up)) == ["blur", "dark"]
    assert names(lr.scene_photos({"media": media("a", "a_copy")}, up)) == ["a", "a_copy"]
    many = lr.scene_photos({"media": media("a", "b", "c", "d", "e", "tall")}, up)
    assert len(many) == lr.MAX_SCENE_PHOTOS and names(many) == ["a", "b", "c", "d", "e"]


def test_the_enhanced_copy_is_used_when_the_agent_kept_it_on(up):
    save(up / "images", "b-enh.jpg", scene(2))
    m = [{"url": "/uploads/images/b.jpg", "kind": "image", "order": 0, "enhanced_url": "/uploads/images/b-enh.jpg",
          "use_enhanced": True}, {"url": "/uploads/images/c.jpg", "kind": "image", "order": 1}]
    assert names(lr.listing_photos({"media": m}, up)) == ["b-enh", "c"]
    m[0]["use_enhanced"] = False
    assert names(lr.listing_photos({"media": m}, up)) == ["b", "c"]
    m[0]["use_enhanced"], m[0]["enhanced_url"] = True, "/uploads/images/gone-enh.jpg"
    assert names(lr.listing_photos({"media": m}, up)) == ["b", "c"]   # a missing enhanced copy falls back to the original


@pytest.mark.asyncio
async def test_the_worker_renders_the_ranked_photos(up):
    r = Renderer()
    jobs, db = await setup(up, renderer=r)
    await db.get_collection("listings").update_one({"_id": "L1"}, {"$set": {"media": media("blur", "tall", "a", "a_copy", "b")}})
    await jobs.create(AGENT, "L1", "en")
    assert await jobs.run_once()
    assert names(r.calls[0]["photos"]) == ["a", "tall", "b"]
