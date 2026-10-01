import pytest


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    from app.modules.newsroom.stages import draft
    monkeypatch.setattr(draft, "RETRY_DELAY", 0)
