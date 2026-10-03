"""Startup policy: production never serves without its database; development may."""
import pytest
from fastapi import FastAPI

from app.core import application


async def _no_database():
    raise ConnectionError("mongo unreachable")


async def _noop():
    return None


@pytest.fixture
def no_database(monkeypatch):
    monkeypatch.setattr(application, "setup_logging", lambda **_: None)  # the real one reconfigures logging for every later test
    monkeypatch.setattr(application, "init_database", _no_database)
    monkeypatch.setattr(application, "stop_token_cleanup", _noop)
    monkeypatch.setattr(application, "close_database", _noop)


async def test_production_refuses_to_start_without_the_database(no_database, monkeypatch):
    monkeypatch.setattr(application.settings, "environment", "production")
    with pytest.raises(ConnectionError):
        async with application.lifespan(FastAPI()):
            pass


async def test_development_starts_without_the_database(no_database, monkeypatch):
    monkeypatch.setattr(application.settings, "environment", "development")
    app = FastAPI()
    async with application.lifespan(app):
        assert getattr(app.state, "newsroom_task", None) is None  # no database, no background loops
