"""The `area_pictures` background loop: off by default, off without Copernicus credentials, picks each area's earliest and
latest missing year, and leaves everything already covered alone."""
import io
from datetime import datetime, timezone

import httpx
from PIL import Image

from app.core.config import settings
from app.modules.areastats import pictures as p
from app.modules.areastats import picturesloop as loop
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 17, 6, 0, tzinfo=timezone.utc)


def png(color=(90, 110, 80, 255), size=(10, 10)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGBA", size, color).save(buf, "PNG")
    return buf.getvalue()


def feature(day, cc):
    return {"type": "Feature", "properties": {"datetime": f"{day}T05:00:00Z", "eo:cloud_cover": cc}}


def fake_client(token_ok=True, passes=None, pics=None):
    """A sync httpx.Client (as the script and the loop both use), stubbed for the token, catalogue and process calls."""
    passes, pics = passes or {}, pics or {}

    def handler(req: httpx.Request):
        if req.url == p.TOKEN_URL:
            return (httpx.Response(200, json={"access_token": "tok"}) if token_ok
                    else httpx.Response(401, json={"error": {"message": "bad secret"}}))
        assert req.headers["Authorization"] == "Bearer tok"
        import json as jsonlib
        body = jsonlib.loads(req.content)
        if str(req.url) == p.CATALOG_URL:
            year = int(body["datetime"][:4])
            return httpx.Response(200, json={"features": passes.get(year, [])})
        day = body["input"]["data"][0]["dataFilter"]["timeRange"]["from"][:10]
        return httpx.Response(200, content=pics[day], headers={"content-type": "image/png"})
    return httpx.Client(transport=httpx.MockTransport(handler))


# ---- enabled(): the flag, and off when Copernicus credentials are missing --------------------------------------------
def test_enabled_needs_the_flag_and_both_copernicus_credentials(monkeypatch):
    monkeypatch.setenv("AREA_FROM_ABOVE", "true")
    monkeypatch.setattr(settings, "copernicus_client_id", "id")
    monkeypatch.setattr(settings, "copernicus_client_secret", "secret")
    assert loop.enabled() is True

    monkeypatch.setenv("AREA_FROM_ABOVE", "false")
    assert loop.enabled() is False

    monkeypatch.setenv("AREA_FROM_ABOVE", "true")
    monkeypatch.setattr(settings, "copernicus_client_secret", None)
    assert loop.enabled() is False


# ---- cycle(): which years it fetches, and that a satisfied area is left alone -----------------------------------------
async def test_cycle_fetches_the_earliest_and_latest_year_for_a_fresh_area(tmp_path):
    db = FakeDb()
    client = fake_client(passes={2017: [feature("2017-03-12", 0.4)], 2026: [feature("2026-02-18", 1.0)]},
                        pics={"2017-03-12": png(), "2026-02-18": png()})
    svc = p.AreaPictures(db, now=lambda: NOW, root=tmp_path)
    out = await loop.cycle(db, NOW, client=client, reader=None, per_run=1)
    assert out["checked"] == 8 and out["kept"] == 2
    years = await svc.kept_years("kharadi")
    assert years == [2017, 2026]


async def test_cycle_does_nothing_once_every_area_has_its_pair(tmp_path):
    db = FakeDb()
    svc = p.AreaPictures(db, now=lambda: NOW, root=tmp_path)
    from app.core.areas import AREAS, get as area_get
    for a in AREAS:
        await svc.add(area_get(a.key), 2017, Image.new("RGB", (5, 5)), "2017-03-01", 0.0, None, p.box_for(a.key))
        await svc.add(area_get(a.key), 2026, Image.new("RGB", (5, 5)), "2026-03-01", 0.0, None, p.box_for(a.key))

    def no_network(req):
        raise AssertionError("nothing is due: the loop must not touch the network")
    out = await loop.cycle(db, NOW, client=httpx.Client(transport=httpx.MockTransport(no_network)))
    assert out == {"checked": 8, "kept": 0}


async def test_cycle_reports_a_refused_key_without_keeping_anything(tmp_path):
    db = FakeDb()
    client = fake_client(token_ok=False)
    out = await loop.cycle(db, NOW, client=client, per_run=1)
    assert out["kept"] == 0 and "error" in out
    assert await p.AreaPictures(db, now=lambda: NOW, root=tmp_path).kept_years("kharadi") == []
