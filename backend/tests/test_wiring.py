"""Callbacks the composition root passes in (docs/ARCHITECTURE.md §2); tests/conftest.py applies the wiring for every test."""
from app.modules.concierge.attribution import attribution_text, register_hub_item
from app.modules.social import router as social_routes


def test_the_social_route_gets_the_concierge_callbacks(monkeypatch):
    monkeypatch.setattr(social_routes, "get_database", lambda: _Db())
    svc = social_routes.get_service()
    assert svc.attribution_hook is attribution_text
    assert svc.on_instagram_published is register_hub_item


class _Db:
    def get_collection(self, name):
        return None


def test_the_quality_route_lets_the_operator_review_any_listing(monkeypatch):
    from types import SimpleNamespace
    from app.modules.photoquality import router as quality_routes

    monkeypatch.setenv("CONCIERGE_OWNER_IDS", "op1")
    assert quality_routes._operator(SimpleNamespace(id="op1", is_superuser=False))
    assert not quality_routes._operator(SimpleNamespace(id="agent7", is_superuser=False))
    assert quality_routes._operator(SimpleNamespace(id="agent7", is_superuser=True))


def test_the_interest_hub_gets_the_sample_catalogue():
    from app.modules.interest import router as interest_routes
    from app.modules.showcase import samples

    slugs = interest_routes._sample_slugs()
    assert slugs == samples.catalogue_slugs() and slugs
    home = interest_routes._sample_home(slugs[0])
    assert home["title"].startswith(samples.SAMPLE_LABEL + ": ")
    assert home["image_url"] == interest_routes.SAMPLE_IMAGE_PATH + slugs[0]


def test_social_posts_use_marketings_link_line_in_the_packs_language():
    from app.modules.social.service import build_payload

    pack = {"language": "hi", "share_url": "https://site.test/l/1", "facebook": {"post": "पोस्ट"}, "images": {}}
    text = build_payload(pack, "facebook_page", "")["text"]
    assert text.endswith("🔗 विवरण और फोटो: https://site.test/l/1")
