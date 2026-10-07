import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.unified_property_service import UnifiedPropertyService


@pytest.fixture
def property_service():
    service = UnifiedPropertyService.__new__(UnifiedPropertyService)
    service.collection = MagicMock()
    service.logger = logging.getLogger(__name__)

    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[])
    service.collection.find.return_value = cursor
    return service, cursor


@pytest.mark.asyncio
async def test_get_properties_by_user_applies_listing_and_publishing_filters(property_service):
    service, cursor = property_service

    result = await service.get_properties_by_user(
        "agent-123",
        skip=5,
        limit=10,
        status="active",
        publishing_status="published",
    )

    assert result == []
    service.collection.find.assert_called_once_with(
        {
            "agent_id": "agent-123",
            "status": "active",
            "publishing_status": "published",
        }
    )
    cursor.skip.assert_called_once_with(5)
    cursor.limit.assert_called_once_with(10)
    cursor.to_list.assert_awaited_once_with(length=None)


@pytest.mark.asyncio
async def test_get_public_properties_excludes_unpublished_and_inactive(property_service):
    service, cursor = property_service

    result = await service.get_public_properties(skip=2, limit=7)

    assert result == []
    service.collection.find.assert_called_once_with(
        {"status": "active", "publishing_status": "published"}
    )
    cursor.skip.assert_called_once_with(2)
    cursor.limit.assert_called_once_with(7)
    cursor.to_list.assert_awaited_once_with(length=None)
