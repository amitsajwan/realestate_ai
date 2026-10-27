"""No new title or description fixes while the site settles after the drop of 2026-10-26 (seo/actions.HOLD_UNTIL)."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import searchconsole
from app.modules.newsroom.store import Store
from app.modules.seo import actions, targets

from ..fakes import FakeDb

NOW = datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc)


def test_fixes_wait_until_the_hold_ends():
    assert actions.on_hold(NOW)
    assert actions.on_hold(actions.HOLD_UNTIL - timedelta(seconds=1))
    assert not actions.on_hold(actions.HOLD_UNTIL)


async def test_titles_stay_as_they_are_during_the_hold(monkeypatch):
    monkeypatch.setattr(searchconsole, "key", lambda: {"client_email": "x"})
    store = Store(FakeDb())
    assert await targets.run_once(store, NOW) == {"held": True}
    assert await targets.run_once(store, NOW + timedelta(minutes=5)) is None   # once a round, like before
