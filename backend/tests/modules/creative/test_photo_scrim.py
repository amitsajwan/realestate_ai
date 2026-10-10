"""Text on a real photo: the photo stays bright, a scrim is added only behind text, just enough for the contrast target."""
from PIL import Image

from app.modules.creative.layouts.base import photo_scrim
from app.modules.creative.layouts.palette import contrast


def test_scrim_only_where_needed():
    img = Image.new("RGB", (400, 400), (235, 225, 200))
    a = photo_scrim(img, (100, 100, 300, 160), (255, 255, 255))
    assert a > 0
    assert contrast((255, 255, 255), img.getpixel((200, 130))) >= 4.5
    assert img.getpixel((5, 395)) == (235, 225, 200)          # away from the text the photo is untouched
    dark = Image.new("RGB", (400, 400), (20, 30, 40))
    assert photo_scrim(dark, (100, 100, 300, 160), (255, 255, 255)) == 0
