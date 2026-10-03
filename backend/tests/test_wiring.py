"""Callbacks the composition root passes in (docs/ARCHITECTURE.md §2): lower modules never import the operator console."""
from app.api.v1 import router as api  # noqa: F401  (importing the route list does the wiring)
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
