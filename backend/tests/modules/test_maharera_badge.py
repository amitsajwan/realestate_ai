"""The MahaRERA badge (AR-3): a QR code that decodes back to the project's MahaRERA page, "MahaRERA: P5..." and the website,
at the top right of the pack's cover, cta and status cards, and only for a project number (never the agent's own)."""
import asyncio

import numpy as np
import pytest
from PIL import Image

from app.modules.marketing import maharera as mr
from app.modules.marketing.images import render
from app.modules.marketing.service import MarketingService

from .fakes import FakeDb
from .marketing_helpers import PROFILE, facts, listing
from .qr_helpers import decode

VIEW = "https://maharerait.maharashtra.gov.in/public/project/view/40123"
PHOTO = Image.new("RGB", (1600, 1200), (150, 190, 225))


# ---- numbers and urls --------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("raw,want", [("P52100012345", "P52100012345"), (" p 52100 012345 ", "P52100012345"),
                                      ("P5-2100-012345", "P52100012345"), ("A51700012345", ""), ("P5210001234", ""),
                                      ("9876543210", ""), (None, ""), ("P" + "5" * 40, "")])
def test_only_a_project_number_is_a_registration(raw, want):
    assert mr.project_regno(raw) == want
    assert (mr.registration(raw) is not None) == bool(want)


def test_the_qr_leads_to_the_project_page_or_the_maharera_site_and_nowhere_else():
    assert mr.registration("P52100012345", VIEW).url == VIEW
    for other in ("", "https://evil.example/public/project/view/1", "http://maharerait.maharashtra.gov.in/public/project/view/1",
                  VIEW + "?x=1", "javascript:alert(1)"):
        assert mr.registration("P52100012345", other).url == mr.HOME_URL
    with pytest.raises(ValueError):
        mr.qr_image("https://example.com/", 160)


@pytest.mark.parametrize("url", [VIEW, mr.HOME_URL])
@pytest.mark.parametrize("qr_px,text_px", [(140, 24), (160, 30), (216, 32)])
def test_badge_decodes_keeps_its_quiet_zone_and_says_number_and_website(url, qr_px, text_px):
    b = mr.badge(mr.registration("P52100012345", url), qr_px, text_px)
    assert b.texts == ["MahaRERA: P52100012345", "maharera.maharashtra.gov.in"]
    assert decode(b.img) == url
    x0, y0, x1, y1 = b.qr_box
    code = b.img.crop(b.qr_box).convert("L")
    assert x1 - x0 == y1 - y0 and abs((x1 - x0) - qr_px) <= 40            # square, about the size asked
    edge = np.array(code)[: (x1 - x0) // 12]                              # the quiet zone: white all round
    assert edge.min() > 200


# ---- on the pack cards --------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("photo", [None, PHOTO])
@pytest.mark.parametrize("kind", ["cover", "cta", "status"])
def test_pack_cards_carry_the_badge_top_right_and_it_scans(kind, photo):
    f = facts()
    f.registration = mr.registration(f.rera, VIEW)
    card = render(kind, f, photo)
    assert "MahaRERA: P52100012345" in card.texts and "maharera.maharashtra.gov.in" in card.texts
    assert decode(card.img) == VIEW
    w, _ = card.size
    badge = next(b for b in card.boxes if b[1] == card.top and b[2] == w - 84)   # flush with the top right of the safe area
    assert badge[0] > w // 4
    if kind == "cover":   # never over the price
        price = card.texts.index(f.price_text)
        assert card.boxes[price][1] > badge[3]


def test_the_listing_number_alone_draws_the_badge_to_the_maharera_site():
    card = render("cover", facts(), None)
    assert "MahaRERA: P52100012345" in card.texts
    assert decode(card.img) == mr.HOME_URL


@pytest.mark.parametrize("kind", ["cover", "cta", "status"])
@pytest.mark.parametrize("over", [{"rera_no": None}, {"rera_no": "A51700012345"}, {"title": "Sample 2 BHK"}])
def test_no_badge_without_a_project_number(kind, over):
    f = facts(**over)
    f.agent_business, f.agent_rera_no = "Sharma Realty", "A51700012345"   # the agent's own registration is not the project's
    card = render(kind, f, None)
    assert not any(t.startswith("MahaRERA") for t in card.texts)
    assert decode(card.img) == ""


def test_the_cta_card_does_not_repeat_the_number_under_the_badge():
    card = render("cta", facts(), None)
    assert "RERA: P52100012345" not in card.texts
    f = facts(rera_no="P" + "5" * 40)   # not a project number: no badge, the old line stays
    assert "RERA: " + "P" + "5" * 40 in render("cta", f, None).texts


# ---- who decides (the wired resolver) -----------------------------------------------------------------------------------------
def test_for_listing_asks_the_wired_resolver_and_falls_back_to_the_listing():
    async def run():
        seen = []

        async def exempt(db, doc):
            seen.append(doc["_id"])
            return None

        async def broken(db, doc):
            raise RuntimeError("db down")

        doc = listing()
        try:
            mr.configure(resolve=exempt)
            assert await mr.for_listing(doc, db=object()) is None and seen == ["L1"]      # e.g. the agent said "exempt"
            assert (await mr.for_listing(doc)).regno == "P52100012345"                    # no db: the listing's own number
            mr.configure(resolve=broken)
            assert (await mr.for_listing(doc, db=object())).regno == "P52100012345"
            assert await mr.for_listing({**doc, "title": "Sample flat"}, db=object()) is None
        finally:
            mr.configure(resolve=None)
    asyncio.run(run())


def test_the_pack_uses_the_resolver_answer(tmp_path):
    async def run():
        db = FakeDb()
        await db.get_collection("listings").insert_one(listing())
        await db.get_collection("agent_public_profiles").insert_one(dict(PROFILE))
        svc = MarketingService(db, tmp_path, "https://site.test")

        async def exempt(_db, _doc):
            return None
        try:
            await svc.generate("A1", "L1", "en", "http://t/")
            with Image.open(tmp_path / "marketing/L1/cover.jpg") as im:
                assert decode(im) == mr.HOME_URL
            mr.configure(resolve=exempt)
            await svc.generate("A1", "L1", "en", "http://t/")
            with Image.open(tmp_path / "marketing/L1/cover.jpg") as im:
                assert decode(im) == ""
        finally:
            mr.configure(resolve=None)
    asyncio.run(run())



async def test_a_pack_for_a_project_we_do_not_trust_prints_no_number_at_all(tmp_path, monkeypatch):
    """The resolver said no (an exempt answer, or a number MahaRERA contradicts): no badge, and no "RERA: P5..." in the
    captions or the WhatsApp text either."""
    from app.modules.marketing import service
    from .listings_fakes import ListingsDb
    from .marketing_helpers import PROFILE, listing

    async def none(listing, db):
        return None
    monkeypatch.setattr(service, "project_registration", none)
    db = ListingsDb()
    (tmp_path / "images").mkdir()
    db.get_collection("agent_public_profiles").docs.append(dict(PROFILE))
    db.get_collection("listings").docs.append({**listing(), "rera_no": "P52100012345"})
    pack = await service.MarketingService(db, tmp_path, "https://site.test").generate("A1", "L1", "en", "")
    text = " ".join([pack.instagram.caption, pack.facebook.caption if hasattr(pack.facebook, "caption") else str(pack.facebook),
                     pack.whatsapp.message])
    assert "P52100012345" not in text
