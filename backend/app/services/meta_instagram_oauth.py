"""OAuth helpers for connecting one Instagram professional account via Meta."""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


PROVIDER = "instagram_facebook_login"
STATE_TTL = timedelta(minutes=10)
SCOPES = (
    "instagram_basic",
    "instagram_content_publish",
    "pages_show_list",
    "pages_read_engagement",
)


class MetaInstagramOAuthError(ValueError):
    """Safe, user-displayable error from the Meta connection flow."""


def _token_cipher() -> Fernet:
    """Derive an at-rest encryption key from the server-only Meta app secret."""
    if not settings.facebook_app_secret:
        raise MetaInstagramOAuthError("Meta app credentials are not configured on the server.")

    key_material = hashlib.sha256(
        b"propertyai-meta-page-token-v1:" + settings.facebook_app_secret.encode("utf-8")
    ).digest()
    return Fernet(base64.urlsafe_b64encode(key_material))


def _state_hash(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


async def create_login_url(user_id: str, db: Any) -> str:
    """Create a short-lived, one-use Business Login URL for Instagram."""
    if not settings.facebook_app_id or not settings.facebook_app_secret:
        raise MetaInstagramOAuthError("Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in the backend environment first.")
    if not settings.facebook_oauth_redirect_uri:
        raise MetaInstagramOAuthError("Set FACEBOOK_OAUTH_REDIRECT_URI to the callback URL registered in Meta.")

    state = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    await db.facebook_oauth_states.delete_many({"expires_at": {"$lte": now}})
    await db.facebook_oauth_states.insert_one(
        {
            "state_hash": _state_hash(state),
            "user_id": str(user_id),
            "created_at": now,
            "expires_at": now + STATE_TTL,
        }
    )

    extras = json.dumps({"setup": {"channel": "IG_API_ONBOARDING"}}, separators=(",", ":"))
    params = {
        "client_id": settings.facebook_app_id,
        "display": "page",
        "extras": extras,
        "redirect_uri": settings.facebook_oauth_redirect_uri,
        "response_type": "token",
        "scope": ",".join(SCOPES),
        "state": state,
    }
    return f"https://www.facebook.com/{settings.facebook_graph_api_version}/dialog/oauth?{urlencode(params)}"


async def complete_login(state: str, access_token: str, db: Any) -> Dict[str, str]:
    """Validate OAuth state, resolve the linked Page/Instagram account, and store its encrypted Page token."""
    if not state or len(state) > 512 or not access_token or len(access_token) > 8192:
        raise MetaInstagramOAuthError("The Meta login response was incomplete. Please try connecting again.")

    state_record = await db.facebook_oauth_states.find_one_and_delete({"state_hash": _state_hash(state)})
    now = datetime.now(timezone.utc)
    if not state_record or state_record.get("expires_at") is None:
        raise MetaInstagramOAuthError("The Meta login session expired or was already used. Please try again.")

    expires_at = state_record["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise MetaInstagramOAuthError("The Meta login session expired. Please try again.")

    app_secret = settings.facebook_app_secret
    if not app_secret:
        raise MetaInstagramOAuthError("Meta app credentials are not configured on the server.")

    app_secret_proof = hmac.new(
        app_secret.encode("utf-8"), access_token.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    params = {
        "fields": "id,name,access_token,instagram_business_account",
        "access_token": access_token,
        "appsecret_proof": app_secret_proof,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"https://graph.facebook.com/{settings.facebook_graph_api_version}/me/accounts",
                params=params,
            )
        if response.status_code != 200:
            raise MetaInstagramOAuthError("Meta could not verify the account or Page permissions.")
        pages = response.json().get("data", [])
    except MetaInstagramOAuthError:
        raise
    except Exception:
        # Do not log or return the request URL; it contains the user's access token.
        raise MetaInstagramOAuthError("Could not contact Meta to verify the connected Page.") from None

    instagram_pages = [
        page for page in pages
        if page.get("id") and page.get("name") and page.get("access_token")
        and (page.get("instagram_business_account") or {}).get("id")
    ]
    if not instagram_pages:
        raise MetaInstagramOAuthError(
            "No Instagram professional account linked to a Page was found. Link Instagram to your Facebook Page and try again."
        )
    if len(instagram_pages) > 1:
        raise MetaInstagramOAuthError(
            "More than one Page has a linked Instagram account. Disconnect unused Pages or choose a single Page before connecting."
        )

    page = instagram_pages[0]
    encrypted_page_token = _token_cipher().encrypt(page["access_token"].encode("utf-8")).decode("ascii")
    user_id = str(state_record["user_id"])
    connection = {
        "user_id": user_id,
        "provider": PROVIDER,
        "page_id": str(page["id"]),
        "page_name": str(page["name"]),
        "instagram_account_id": str(page["instagram_business_account"]["id"]),
        "page_access_token_encrypted": encrypted_page_token,
        "connected_at": now,
        "updated_at": now,
    }
    await db.social_connections.update_one(
        {"user_id": user_id, "provider": PROVIDER},
        {"$set": connection},
        upsert=True,
    )

    return {
        "page_id": connection["page_id"],
        "page_name": connection["page_name"],
        "instagram_account_id": connection["instagram_account_id"],
    }


async def get_connection_status(user_id: str, db: Any) -> Dict[str, Any]:
    """Return connection metadata only; never expose the stored token."""
    connection = await db.social_connections.find_one(
        {"user_id": str(user_id), "provider": PROVIDER},
        {"_id": 0, "page_id": 1, "page_name": 1, "instagram_account_id": 1, "connected_at": 1},
    )
    if not connection:
        return {"connected": False, "pages": []}
    return {
        "connected": True,
        "pages": [{"id": connection["page_id"], "name": connection["page_name"]}],
        "instagram_account_id": connection["instagram_account_id"],
        "connected_at": connection.get("connected_at"),
    }


async def disconnect(user_id: str, db: Any) -> None:
    """Delete the user's stored Meta connection and any outstanding OAuth states."""
    await db.social_connections.delete_one({"user_id": str(user_id), "provider": PROVIDER})
    await db.facebook_oauth_states.delete_many({"user_id": str(user_id)})


def decrypt_page_access_token(encrypted_token: str) -> str:
    """Decrypt a connected Page token for server-side Graph API calls only."""
    try:
        return _token_cipher().decrypt(encrypted_token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeDecodeError):
        raise MetaInstagramOAuthError("The stored Meta connection cannot be decrypted. Reconnect the account.") from None
