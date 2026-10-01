import pytest


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    from app.modules.newsroom.stages import draft
    monkeypatch.setattr(draft, "RETRY_DELAY", 0)


@pytest.fixture(autouse=True)
def private_uploads(monkeypatch, tmp_path):
    """Cards are drawn into a temporary uploads folder, never into the repo; no real media or site address leaks in from the environment."""
    monkeypatch.setenv("UPLOAD_DIRECTORY", str(tmp_path / "uploads"))
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://media.test")
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://site.test")
    for k in ("META_IG_BUSINESS_ID", "META_PAGE_ID", "META_PAGE_ACCESS_TOKEN", "SOCIAL_DRY_RUN", "INTEREST_OWNER_AGENT_ID", "ENGAGE_OWNER_AGENT_ID"):
        monkeypatch.delenv(k, raising=False)
