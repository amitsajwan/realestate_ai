from datetime import datetime

import pytest

from app.modules.onboarding import branding as bd
from app.modules.onboarding.schemas import SiteCreate, SiteUpdate

from .test_onboarding import make

pytestmark = pytest.mark.asyncio


def test_all_presets_have_aa_contrast_for_white_text():
    assert set(bd.PRESET_NAMES) == {"navy-gold", "emerald", "terracotta", "royal-purple", "slate-teal", "cream-ink"}
    for name, p in bd.PRESETS.items():
        assert bd.contrast_ratio(p["primary"], "#ffffff") >= 4.5, name
        assert bd.contrast_ratio(p["secondary"], "#ffffff") >= 4.5, name


@pytest.mark.parametrize("bad", ["#ffff00", "#f0f0f0", "red", "#12", "#12345g", "#fff"])
def test_low_contrast_or_malformed_custom_colour_rejected(bad):
    with pytest.raises(ValueError):
        SiteUpdate(custom_primary=bad)


def test_dark_custom_colour_accepted_and_lowercased():
    assert SiteUpdate(custom_primary="#1A2B5C").custom_primary == "#1a2b5c"


@pytest.mark.parametrize("raw,clean", [("A52100012345", "A52100012345"), (" a5210 0012345 ", "A52100012345"), ("A-52100012345", "A52100012345")])
def test_rera_agent_number_normalised(raw, clean):
    assert SiteUpdate(rera_agent_no=raw).rera_agent_no == clean


@pytest.mark.parametrize("bad", ["P52100012345", "A12", "A" + "1" * 25, "12345678", "A5210001234x"])
def test_rera_agent_number_rejected(bad):
    with pytest.raises(ValueError):
        SiteUpdate(rera_agent_no=bad)


@pytest.mark.parametrize("field,bad", [
    ("tagline", "Call me 98765 43210"), ("tagline", "visit www.mysite.com"), ("about", "mail me at a@b.com"),
    ("business_name", "Rahul <b>Homes</b>"), ("about", "see https://x.test"), ("business_name", "+91 9876543210 Realty"),
    ("tagline", "x" * 200), ("about", "y" * 700), ("business_name", "R"),
])
def test_text_fields_reject_phones_urls_markup_and_overlong(field, bad):
    with pytest.raises(ValueError):
        SiteUpdate(**{field: bad})


def test_plain_text_is_kept_and_whitespace_collapsed():
    u = SiteUpdate(business_name="  Deshmukh   Realty ", tagline="Homes for families, 9 years in Baner")
    assert u.business_name == "Deshmukh Realty" and u.tagline.startswith("Homes for")


def test_areas_pune_only_deduped_and_capped():
    assert SiteUpdate(areas=["Baner", "baner", "Kharadi", "Anything, Pune"]).areas == ["Baner", "Kharadi", "Anything, Pune"]
    with pytest.raises(ValueError):
        SiteUpdate(areas=["Andheri"])
    with pytest.raises(ValueError):
        SiteUpdate(areas=["Baner", "Aundh", "Wakad", "Kharadi", "Wagholi", "Hadapsar", "Kothrud"])
    with pytest.raises(ValueError):
        SiteUpdate(areas=["Baner 98765 43210"])


def test_preset_languages_years_validated():
    assert SiteUpdate(preset="emerald", languages=["Hindi", "hindi", "Marathi"], years_experience=9).languages == ["Hindi", "Marathi"]
    for kw in ({"preset": "neon"}, {"years_experience": 80}, {"languages": ["Hi<script>"]}):
        with pytest.raises(ValueError):
            SiteUpdate(**kw)


def test_banner_must_be_an_uploaded_image():
    assert SiteUpdate(banner="/uploads/images/b1.jpg").banner == "/uploads/images/b1.jpg"
    with pytest.raises(ValueError):
        SiteUpdate(banner="https://evil.test/x.jpg")


async def test_brand_roundtrip_create_update_clear():
    svc, db, _, users, _ = make()
    user = await users.create("+919876543210")
    await svc.create_site(user, SiteCreate(name="Priya Deshmukh", city="Pune", business_name="Deshmukh Realty", preset="terracotta"))
    doc = await db.get_collection("agent_public_profiles").find_one({"slug": "priya-deshmukh"})
    b = doc["branding_data"]
    assert b["business_name"] == "Deshmukh Realty" and b["preset"] == "terracotta" and b["colors"]["primary"] == bd.PRESETS["terracotta"]["primary"]

    out = await svc.update_site(user, SiteUpdate(banner="/uploads/images/b.jpg", tagline="Baner homes, honestly", rera_agent_no="a52100012345",
                                                  areas=["Baner", "Aundh"], languages=["English", "Marathi"], years_experience=9, custom_primary="#1a2b5c"))
    b = out["branding_data"]
    assert b["rera_agent_no"] == "A52100012345" and b["areas"] == ["Baner", "Aundh"] and b["years_experience"] == 9
    assert b["banner"] == "/uploads/images/b.jpg" and b["colors"]["primary"] == "#1a2b5c" and b["preset"] == "terracotta"
    assert (await svc.get_site(user))["branding_data"] == b

    out = await svc.update_site(user, SiteUpdate(banner="", rera_agent_no="", areas=[], custom_primary=""))
    b = out["branding_data"]
    assert "banner" not in b and "rera_agent_no" not in b and "areas" not in b and "custom_primary" not in b
    assert b["colors"]["primary"] == bd.PRESETS["terracotta"]["primary"] and b["business_name"] == "Deshmukh Realty"  # omitted fields stay


def test_public_profile_passes_brand_fields_through():
    from app.schemas.agent_public import AgentPublicProfile
    b = {"business_name": "X Realty", "preset": "emerald", "areas": ["Baner"], "rera_agent_no": "A52100012345"}
    base = dict(id="1", agent_id="1", agent_name="Asha", slug="asha", is_active=True, is_public=True,
                created_at=datetime.now(), updated_at=datetime.now(), view_count=0, contact_count=0)
    assert AgentPublicProfile(**{**base, "branding_data": b}).model_dump()["branding_data"] == b
