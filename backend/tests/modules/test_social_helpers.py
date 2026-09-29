"""Shared fixtures for the social tests (helper module, contains no tests)."""
from urllib.parse import parse_qsl

import httpx

from app.modules.social.config import SocialConfig
from app.modules.social.graph import GraphPublisher
from app.modules.social.service import SocialService

from .fakes import FakeDb

TOKEN = "EAAGsecrettoken1234567890ABCDEFGHIJ"
REAL = SocialConfig(dry_run=False, page_id="PAGE1", ig_id="IG1", media_base_url="https://media.test", page_token=TOKEN)
DRY = SocialConfig(dry_run=True)

LISTING = {"_id": "L1", "agent_id": "A1", "status": "live"}


def pack(version: int = 1, images=("cover", "facts", "amenities", "cta")) -> dict:
    return {"_id": "L1", "agent_id": "A1", "version": version, "share_url": "https://site.test/agent/rahul/listings/L1?src=whatsapp",
            "facebook": {"post": "Ready 2 BHK in Baner"}, "instagram": {"caption": "2 BHK in Baner", "hashtags": ["#Pune", "#Baner"]},
            "images": {k: {"path": f"/uploads/marketing/L1/{k}.jpg", "width": 1080, "height": 1080} for k in images}}


def make_db(version: int = 1, status: str = "live", images=("cover", "facts", "amenities", "cta")) -> FakeDb:
    db = FakeDb()
    db.get_collection("listings").docs.append({**LISTING, "status": status})
    db.get_collection("marketing_packs").docs.append(pack(version, images))
    return db


class FakeGraph:
    """Records every Graph call; `routes` maps (METHOD, path) to a response, a list of responses (consumed in order) or a callable."""

    def __init__(self, routes=None):
        self.routes, self.calls = routes or {}, []

    def transport(self):
        return httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        form = dict(parse_qsl(request.content.decode())) if request.method == "POST" else {}
        query = dict(request.url.params)
        self.calls.append({"method": request.method, "path": request.url.path, "form": form, "query": query})
        route = self.routes.get((request.method, request.url.path))
        if callable(route):
            route = route(self.calls[-1])
        if isinstance(route, list):
            route = route.pop(0) if len(route) > 1 else route[0]
        if route is None:
            return httpx.Response(404, json={"error": {"message": "no route", "code": 100}})
        if isinstance(route, Exception):
            raise route
        if isinstance(route, httpx.Response):
            return route
        status, body = route
        return httpx.Response(status, json=body)

    def order(self):
        return [f"{c['method']} {c['path']}" for c in self.calls]


class Clock:
    def __init__(self):
        self.t, self.sleeps = 0.0, 0

    def __call__(self):
        return self.t

    async def sleep(self, s):
        self.sleeps += 1
        self.t += s


def graph_service(db, graph: FakeGraph, cfg: SocialConfig = REAL, clock: Clock = None) -> SocialService:
    clock = clock or Clock()
    return SocialService(db, publisher_factory=lambda c: GraphPublisher(c, transport=graph.transport(), sleep=clock.sleep, clock=clock),
                         config_loader=lambda: cfg)


def never_called_transport():
    def boom(request):
        raise AssertionError(f"network must not be touched: {request.method} {request.url}")
    return httpx.MockTransport(boom)
