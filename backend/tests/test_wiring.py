"""Callbacks the composition root passes in (docs/ARCHITECTURE.md §2): lower modules never import the operator console."""
from app.modules.concierge.attribution import attribution_text, register_hub_item
from app.modules.social import router as social_routes
from app.wiring import wire

wire()


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
