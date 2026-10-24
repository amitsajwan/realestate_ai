"""The owner's System tab (app/modules/areastats/owner.py): how many Serper searches a day the rounds spend."""
from datetime import datetime, timezone

import pytest

from app.modules.areastats import owner, pricing, websearch
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 25, 9, 0, tzinfo=timezone.utc)
RESULTS = websearch.AREA_PER_DAY + websearch.PROJECT_PER_DAY + websearch.TARGET_PER_DAY + websearch.PANEL_PER_DAY


@pytest.mark.asyncio
async def test_serper_daily_use_counts_the_prices_round(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    monkeypatch.delenv("PRICES_SEARCHES_PER_DAY", raising=False)
    out = await owner.system(Store(FakeDb(), clock=lambda: NOW), NOW, {})
    assert out["serper_split"] == [{"name": "rank checks", "per_day": RESULTS},
                                   {"name": "prices", "per_day": pricing.SEARCHES_PER_DAY}]
    assert out["serper_per_day"] == RESULTS + pricing.SEARCHES_PER_DAY == 35


def test_the_prices_share_follows_its_setting(monkeypatch):
    monkeypatch.setenv("PRICES_SEARCHES_PER_DAY", "4")
    assert owner.serper_split()[1] == {"name": "prices", "per_day": 4}
