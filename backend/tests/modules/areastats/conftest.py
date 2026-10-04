import pytest


@pytest.fixture(autouse=True)
def no_pauses(monkeypatch):
    from app.modules.areastats import refresh, service
    from app.modules.newsroom.sources import maharera
    monkeypatch.setattr(refresh, "PAUSE", 0)
    monkeypatch.setattr(maharera, "RETRY_DELAY", 0)
    service.clear_cache()
    yield
    service.clear_cache()
