"""Location pictures: a street map around the project's checked pin for pages with no picture of their own, drawn once, drawn
again only when the pin moves, and never at an unchecked position."""
import io
from datetime import datetime, timedelta, timezone

from PIL import Image

from app.modules.areastats import locmap, pages
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 31, 9, 0, tzinfo=timezone.utc)
PAGE = {"registered_on": "2024-01-10", "completion_now": "2029-10-30", "project_type": "Residential", "locality": "kharadi",
        "news": [], "in_register": True, "promoter": "Some Builder"}
CHECKED = {"enrichment": {"steps": {"places": {"ok": True}}}}


def tile() -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (256, 256), (230, 228, 220)).save(out, "PNG")
    return out.getvalue()


class Tiles:
    def __init__(self, answer=True):
        self.urls, self.answer = [], answer

    async def __call__(self, url):
        self.urls.append(url)
        return tile() if self.answer else None


async def seeded(*docs):
    db = FakeDb()
    store = Store(db)
    for regno, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": regno, "page_slug": regno.lower(), **PAGE, **extra})
    return store


def test_the_map_is_drawn_at_the_checked_pin_and_only_there():
    assert pages.checked_pin({"geo": {"lat": 18.55, "lon": 73.94}, **CHECKED}) == (18.55, 73.94)
    assert pages.checked_pin({"geo": {"lat": 18.55, "lon": 73.94}}) is None               # the places check did not pass
    assert pages.checked_pin({"map_pin": {"status": "doubtful", "lat": 18.5, "lon": 73.9}}) is None
    assert pages.checked_pin({"map_pin": {"status": "approved", "lat": 18.5, "lon": 73.9}, "geo": {"lat": 1, "lon": 2}, **CHECKED}) == (18.5, 73.9)


def test_the_pin_is_at_the_centre_of_the_picture():
    wanted, (left, top) = locmap.tiles_for(18.5527, 73.9427)
    cx, cy = locmap.world_px(18.5527, 73.9427)
    assert (cx - left, cy - top) == (locmap.W / 2, locmap.H / 2)
    assert len(wanted) <= locmap.TILES_PER_MAP and all(x * 256 <= cx + locmap.W for x, _ in wanted)


async def test_pages_without_pictures_get_a_map_once_and_a_new_one_when_the_pin_moves(tmp_path):
    store = await seeded(("P1", {"geo": {"lat": 18.5527, "lon": 73.9427}, **CHECKED, "hot_score": 5}),
                         ("P2", {"geo": {"lat": 18.56, "lon": 73.95}, **CHECKED,
                                 "profile": {"photos": [{"path": "project_media/p2/a.webp", "source": "builder"}]}}),
                         ("P3", {"geo": {"lat": 18.56, "lon": 73.95}}))           # unchecked position: no map
    tiles = Tiles()
    assert await locmap.refresh(store, NOW, fetch=tiles, map_dir=tmp_path) == {"drawn": 1, "failed": 0}
    assert len(tiles.urls) <= locmap.TILES_PER_MAP and all(u.startswith("https://tile.openstreetmap.org/15/") for u in tiles.urls)
    p1 = await store.project("P1")
    shown = pages.location_picture(p1)
    assert shown["url"].endswith("p1.webp") and (shown["width"], shown["height"]) == locmap.MAP_SIZE
    assert Image.open(tmp_path / "p1.webp").size == locmap.MAP_SIZE
    assert pages.view(p1, [])["location_picture"] == shown
    assert "location_map" not in await store.project("P2") and "location_map" not in await store.project("P3")
    assert await locmap.refresh(store, NOW + timedelta(hours=3), fetch=tiles, map_dir=tmp_path) is None   # once a day
    tiles.urls.clear()
    assert await locmap.refresh(store, NOW + timedelta(days=1), fetch=tiles, map_dir=tmp_path) == {"drawn": 0, "failed": 0}
    await store.set_project("P1", geo={"lat": 18.5600, "lon": 73.9427})
    moved = await store.project("P1")
    assert pages.location_picture(moved) is None   # the old map is not shown at the new place
    assert await locmap.refresh(store, NOW + timedelta(days=2), fetch=tiles, map_dir=tmp_path) == {"drawn": 1, "failed": 0}


async def test_a_tile_server_that_does_not_answer_stops_the_round_and_leaves_no_map(tmp_path):
    store = await seeded(*[(f"P{i}", {"geo": {"lat": 18.55 + i / 100, "lon": 73.94}, **CHECKED}) for i in range(5)])
    tiles = Tiles(answer=False)
    assert await locmap.refresh(store, NOW, fetch=tiles, map_dir=tmp_path) == {"drawn": 0, "failed": 3}
    assert len(tiles.urls) == 3 and not list(tmp_path.glob("*.webp"))
