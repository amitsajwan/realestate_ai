"""Uploading a video to our YouTube channel (YouTube Data API v3, videos.insert, resumable). The read-only client with an API key
is app.platform.youtube; an upload needs the channel owner's OAuth consent instead, kept as a refresh token.

Settings, read at call time and never logged:
  YOUTUBE_UPLOAD             "on" to upload; anything else and nothing is sent (the default: off until the owner sets it up)
  YOUTUBE_CLIENT_ID          the OAuth client (Google Cloud console, "Desktop app" or "Web" client of the API project)
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN      from a one-time consent by the channel owner, scope youtube.upload
  YOUTUBE_PRIVACY            public (default), unlisted or private
  YOUTUBE_UPLOADS_PER_DAY    default 5: an upload costs 1,600 of the project's 10,000 daily quota units

Note: Google keeps uploads from an API project that has not passed its audit as private until the audit passes
(https://support.google.com/youtube/contact/yt_api_form). Set YOUTUBE_PRIVACY=private until then, so nothing claims to be live.
"""
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import httpx

log = logging.getLogger(__name__)

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
UPLOAD_COST = 1600
TITLE_MAX = 100
DESCRIPTION_MAX = 5000
TAGS_MAX_CHARS = 450                    # the API allows 500 characters of tags in all
CATEGORY_PEOPLE_BLOGS = "22"            # YouTube has no real estate category
PRIVACY = ("public", "unlisted", "private")


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


@dataclass(frozen=True)
class UploadConfig:
    on: bool = False
    client_id: str = ""
    client_secret: str = field(default="", repr=False)
    refresh_token: str = field(default="", repr=False)
    privacy: str = "public"
    per_day: int = 5

    @property
    def ready(self) -> bool:
        """On, and every key there: only then does an upload leave the building."""
        return self.on and bool(self.client_id and self.client_secret and self.refresh_token)

    @property
    def secrets(self) -> list:
        return [s for s in (self.client_secret, self.refresh_token) if s]


def load() -> UploadConfig:
    privacy = _env("YOUTUBE_PRIVACY").lower() or "public"
    try:
        per_day = max(0, int(_env("YOUTUBE_UPLOADS_PER_DAY") or 5))
    except ValueError:
        per_day = 5
    return UploadConfig(on=_env("YOUTUBE_UPLOAD").lower() in ("on", "1", "true", "yes"), client_id=_env("YOUTUBE_CLIENT_ID"),
                        client_secret=_env("YOUTUBE_CLIENT_SECRET"), refresh_token=_env("YOUTUBE_REFRESH_TOKEN"),
                        privacy=privacy if privacy in PRIVACY else "public", per_day=per_day)


class UploadError(Exception):
    pass


@dataclass(frozen=True)
class VideoMeta:
    title: str
    description: str
    tags: List[str] = field(default_factory=list)
    language: str = "en"


def fit(meta: VideoMeta) -> VideoMeta:
    """Within YouTube's limits: title 100 characters, description 5,000, no angle brackets (the API refuses them), tags 450
    characters in all; cut at a word, never mid-word."""
    def cut(s: str, n: int) -> str:
        s = s.replace("<", "").replace(">", "").strip()
        if len(s) <= n:
            return s
        at = s.rfind(" ", 0, n - 1)
        return (s[:at] if at > n * 0.6 else s[:n - 1]).rstrip(" ,·-:") + "…"
    tags, used = [], 0
    for t in meta.tags:
        t = t.replace("<", "").replace(">", "").strip()
        if t and t not in tags and used + len(t) + 1 <= TAGS_MAX_CHARS:
            tags.append(t)
            used += len(t) + 1
    return VideoMeta(cut(meta.title, TITLE_MAX), cut(meta.description, DESCRIPTION_MAX), tags, meta.language)


async def access_token(cfg: UploadConfig, client: httpx.AsyncClient) -> str:
    r = await client.post(TOKEN_URL, data={"client_id": cfg.client_id, "client_secret": cfg.client_secret,
                                           "refresh_token": cfg.refresh_token, "grant_type": "refresh_token"})
    if r.status_code != 200:
        raise UploadError(f"youtube token {r.status_code}: {(r.json() if r.headers.get('content-type', '').startswith('application/json') else {}).get('error', r.text[:80])}")
    return r.json()["access_token"]


async def upload(cfg: UploadConfig, video: Path, meta: VideoMeta,
                 transport: Optional[httpx.AsyncBaseTransport] = None) -> str:
    """Uploads the file and returns the new video's id. Raises UploadError on any refusal; the caller decides about retries."""
    if not cfg.ready:
        raise UploadError("YouTube upload is not set up (YOUTUBE_UPLOAD and its three keys)")
    if not video.is_file():
        raise UploadError(f"video file missing: {video.name}")
    meta = fit(meta)
    body = {"snippet": {"title": meta.title, "description": meta.description, "tags": meta.tags,
                        "categoryId": CATEGORY_PEOPLE_BLOGS, "defaultLanguage": meta.language, "defaultAudioLanguage": meta.language},
            "status": {"privacyStatus": cfg.privacy, "selfDeclaredMadeForKids": False}}
    size = video.stat().st_size
    async with httpx.AsyncClient(timeout=120, transport=transport) as c:
        bearer = await access_token(cfg, c)
        start = await c.post(UPLOAD_URL, json=body, headers={
            "Authorization": f"Bearer {bearer}", "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
        if start.status_code != 200 or not start.headers.get("location"):
            raise UploadError(f"youtube upload start {start.status_code}: {start.text[:160]}")
        done = await c.put(start.headers["location"], content=video.read_bytes(),
                           headers={"Authorization": f"Bearer {bearer}", "Content-Type": "video/mp4"})
        if done.status_code not in (200, 201):
            raise UploadError(f"youtube upload {done.status_code}: {done.text[:160]}")
        vid = (done.json() or {}).get("id")
        if not vid:
            raise UploadError("youtube upload returned no video id")
        return vid


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/shorts/{video_id}"
