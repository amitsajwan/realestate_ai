from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest

from app.core.config import settings
from app.services import meta_instagram_oauth as oauth


class MemoryCollection:
    def __init__(self):
        self.documents = []

    async def insert_one(self, document):
        self.documents.append(dict(document))

    async def delete_many(self, query):
        expires_before = query.get("expires_at", {}).get("$lte")
        if expires_before:
            self.documents = [doc for doc in self.documents if doc.get("expires_at") > expires_before]

    async def find_one_and_delete(self, query):
        for index, document in enumerate(self.documents):
            if all(document.get(key) == value for key, value in query.items()):
                return self.documents.pop(index)
        return None

    async def update_one(self, query, update, upsert=False):
        values = update["$set"]
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                document.update(values)
                return
        if upsert:
            self.documents.append(dict(values))

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return dict(document)
        return None

    async def delete_one(self, query):
        await self.find_one_and_delete(query)


class MemoryDatabase:
    def __init__(self):
        self.facebook_oauth_states = MemoryCollection()
        self.social_connections = MemoryCollection()


@pytest.fixture
def meta_settings(monkeypatch):
    monkeypatch.setattr(settings, "facebook_app_id", "test-app-id")
    monkeypatch.setattr(settings, "facebook_app_secret", "test-app-secret")
    monkeypatch.setattr(
        settings,
        "facebook_oauth_redirect_uri",
        "https://propertyai.example/api/v1/auth/facebook/callback",
    )
    monkeypatch.setattr(settings, "facebook_graph_api_version", "v25.0")


@pytest.mark.asyncio
async def test_create_login_url_uses_page_linked_instagram_flow(meta_settings):
    db = MemoryDatabase()

    login_url = await oauth.create_login_url("user-123", db)
    query = parse_qs(urlparse(login_url).query)

    assert urlparse(login_url).path == "/v25.0/dialog/oauth"
    assert query["client_id"] == ["test-app-id"]
    assert query["redirect_uri"] == ["https://propertyai.example/api/v1/auth/facebook/callback"]
    assert query["response_type"] == ["token"]
    assert "instagram_content_publish" in query["scope"][0]
    assert query["state"]
    assert db.facebook_oauth_states.documents[0]["user_id"] == "user-123"
    assert db.facebook_oauth_states.documents[0]["state_hash"] != query["state"][0]


@pytest.mark.asyncio
async def test_complete_login_encrypts_page_token_and_consumes_state(meta_settings, monkeypatch):
    db = MemoryDatabase()
    login_url = await oauth.create_login_url("user-123", db)
    state = parse_qs(urlparse(login_url).query)["state"][0]
    page_token = "page-access-token-secret"

    class MockResponse:
        status_code = 200

        @staticmethod
        def json():
            return {
                "data": [
                    {
                        "id": "page-456",
                        "name": "My Page",
                        "access_token": page_token,
                        "instagram_business_account": {"id": "instagram-789"},
                    }
                ]
            }

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

        async def get(self, url, params):
            assert url.endswith("/v25.0/me/accounts")
            assert params["access_token"] == "long-lived-user-token"
            assert params["appsecret_proof"]
            return MockResponse()

    monkeypatch.setattr(oauth.httpx, "AsyncClient", lambda timeout: MockClient())

    result = await oauth.complete_login(state, "long-lived-user-token", db)
    stored = db.social_connections.documents[0]

    assert result == {
        "page_id": "page-456",
        "page_name": "My Page",
        "instagram_account_id": "instagram-789",
    }
    assert stored["page_access_token_encrypted"] != page_token
    assert oauth.decrypt_page_access_token(stored["page_access_token_encrypted"]) == page_token
    status = await oauth.get_connection_status("user-123", db)
    assert status["connected"] is True
    assert page_token not in repr(status)

    with pytest.raises(oauth.MetaInstagramOAuthError, match="expired or was already used"):
        await oauth.complete_login(state, "long-lived-user-token", db)


@pytest.mark.asyncio
async def test_complete_login_rejects_expired_state(meta_settings):
    db = MemoryDatabase()
    state = "an-expired-one-time-state-value"
    db.facebook_oauth_states.documents.append(
        {
            "state_hash": oauth._state_hash(state),
            "user_id": "user-123",
            "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
    )

    with pytest.raises(oauth.MetaInstagramOAuthError, match="expired"):
        await oauth.complete_login(state, "long-lived-user-token", db)
