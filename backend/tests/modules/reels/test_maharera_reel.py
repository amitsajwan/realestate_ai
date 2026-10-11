"""AR-3: the walkthrough reel's closing scene carries the MahaRERA badge (a QR a phone reads, at least 160 px on the 1080-wide
frame), only for the project's own registration."""
from pathlib import Path

import pytest

from app.modules.marketing.maharera import badge, registration
from app.modules.reels import listing_reel as lr
from app.modules.reels.compose import CONTENT_TOP, TEXT_RIGHT, Renderer, Scene, TextLine, layout_scene

from .test_listing_reel import Renderer as FakeRenderer
from .test_listing_reel import setup as listing_setup
from ..qr_helpers import decode

PHOTOS = Path(__file__).resolve().parents[3] / "app/modules/creative/assets/photos"
VIEW = "https://maharerait.maharashtra.gov.in/public/project/view/40123"
REG = registration("P52100076768", VIEW)
CLOSING = "Listed by Rahul Homes · RERA A51800012345"


def test_badge_is_big_enough_to_scan_on_a_phone():
    b = badge(REG, lr.MAHARERA_QR, lr.MAHARERA_TEXT)
    assert b.qr_box[2] - b.qr_box[0] >= 160
    assert lr._maharera_overlay(REG).size == b.size and b.size[0] <= TEXT_RIGHT - 72


def test_tour_closing_scene_shows_the_badge_and_keeps_the_text_below_it():
    lines = [TextLine("Comment *INTERESTED* for the details", size=96)] + lr._closing_lines(CLOSING)
    overlay = lr._maharera_overlay(REG)
    scenes = [Scene(image=PHOTOS / "tower-low.jpg", lines=["2 BHK in *Kharadi*"], layout="lower", seconds=2.0, seed="a"),
              Scene(image=PHOTOS / "living-room.jpg", lines=lines, layout="lower", seconds=3.0, seed="b", overlay=overlay)]
    r = Renderer(scenes, transition="slide", xfade=0.45)
    assert decode(r.frame_at(r.tl.total - 0.05)) == VIEW
    assert decode(r.frame_at(0.5)) == ""                                   # the hook scene has none
    for it in layout_scene(scenes[1]):
        assert it.box[1] >= CONTENT_TOP + overlay.size[1]                  # nothing runs into it


def test_stack_reel_shows_the_badge_with_the_closing_lines():
    beats = [{"screen": "2 BHK in *Kharadi*"}, {"screen": "780 sq ft carpet"}, {"screen": "Comment INTERESTED"}]
    picks = [PHOTOS / "tower-low.jpg", PHOTOS / "living-room.jpg", PHOTOS / "living-sofa.jpg"]
    sc = lr._stack_scene(beats, picks, [2.5, 2.5, 3.0], None, "KHARADI", CLOSING, REG)
    assert sc.overlay_at == 5.0
    r = Renderer([sc], xfade=0.0, hook_tag=False)
    assert decode(r.frame_at(0.1)) == ""
    assert decode(r.frame_at(r.tl.total - 0.05)) == VIEW
    plain = lr._stack_scene(beats, picks, [2.5, 2.5, 3.0], None, "KHARADI", CLOSING)
    assert plain.overlay is None


@pytest.mark.parametrize("rera,want", [("P52100076768", "P52100076768"), ("A51800012345", None), (None, None)])
async def test_the_job_passes_only_a_project_registration(tmp_path, rera, want):
    r = FakeRenderer()
    jobs, _ = await listing_setup(tmp_path, renderer=r, **({"rera_no": rera} if rera else {}))
    await jobs.create("agent1", "L1", "en")
    assert await jobs.run_once()
    got = r.calls[0].get("maharera")
    assert (got.regno if got else None) == want
