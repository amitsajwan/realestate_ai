"""The home plan's offices (frontend/lib/site/homeplan.ts WORK) are the project pages' work hubs (app/core/work_hubs.py): the
plan's "N km from EON IT Park" must be the same distance the project page shows."""
import re
from pathlib import Path

import pytest

from app.core.work_hubs import HUBS

PLAN = Path(__file__).resolve().parents[4] / "frontend" / "lib" / "site" / "homeplan.ts"
pytestmark = pytest.mark.skipif(not PLAN.is_file(), reason="frontend sources are not on this machine")
ROW = re.compile(r"hub: '([^']+)', lat: ([\d.]+), lon: ([\d.]+)")


def test_every_home_plan_office_is_a_work_hub_at_the_same_position():
    rows = ROW.findall(PLAN.read_text(encoding="utf-8"))
    assert len(rows) == 3
    hubs = {h.name: (h.lat, h.lon) for h in HUBS}
    for name, lat, lon in rows:
        assert name in hubs, name
        assert (float(lat), float(lon)) == hubs[name], name
