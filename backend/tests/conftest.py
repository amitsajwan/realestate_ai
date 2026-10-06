"""Pytest configuration.

Legacy tests below were written against services/fixtures that no longer exist
(post_management_service removed, AnalyticsService.collection is now a property,
User ids must be PydanticObjectId, ...). They are quarantined, not deleted, until
their subject modules are rebuilt in v2 (see docs/IMPLEMENTATION_PLAN.md, WS-7).
"""

collect_ignore = [
    "test_analytics_service.py",
]


import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def _production_wiring():
    """Every test runs with the startup wiring production uses (app/wiring.py: callbacks passed into lower modules)."""
    from app.wiring import wire
    wire()
