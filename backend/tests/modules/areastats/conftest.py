import pytest


@pytest.fixture(autouse=True)
def no_pauses(monkeypatch):
    from app.modules.areastats import discover, hot, refresh, service, watch
    monkeypatch.setattr(discover, "PAUSE", 0)
    monkeypatch.setattr(watch, "_SOURCES", {})  # each test registers the sources it wants
    monkeypatch.setattr(hot, "_SIGNALS", {})
    from app.modules.newsroom.sources import maharera
    monkeypatch.setattr(refresh, "PAUSE", 0)
    monkeypatch.setattr(maharera, "RETRY_DELAY", 0)
    service.clear_cache()
    yield
    service.clear_cache()
