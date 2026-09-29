"""Pytest configuration.

Legacy tests below were written against services/fixtures that no longer exist
(post_management_service removed, AnalyticsService.collection is now a property,
User ids must be PydanticObjectId, ...). They are quarantined, not deleted, until
their subject modules are rebuilt in v2 (see docs/IMPLEMENTATION_PLAN.md, WS-7).
"""

collect_ignore = [
    "test_integration.py",
    "test_post_management_service.py",
    "test_post_management_api.py",
    "test_analytics_service.py",
]
