"""YouTube Data API v3, read-only with an API key (YOUTUBE_API_KEY). Free quota: 10,000 units a day; `search` costs 100,
`commentThreads` 1. Tests inject a fake `get`. The key is never logged."""
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable, List, Optional, Tuple

import httpx

log = logging.getLogger(__name__)

BASE = "https://www.googleapis.com/youtube/v3"
SEARCH_COST, COMMENTS_COST = 100, 1


@dataclass
class Video:
    id: str
    title: str
    channel: str
    published_at: str


@dataclass
class Comment:
    id: str
    video_id: str
    author: str
    author_channel: str
    text: str
    published_at: str
    reply_count: int
    replies: List[str]


def api_key() -> str:
    return (os.environ.get("YOUTUBE_API_KEY") or "").strip()


class YouTubeError(Exception):
    def __init__(self, status: int, reason: str):
        super().__init__(f"youtube {status}: {reason}")
        self.status, self.reason = status, reason


Getter = Callable[[str, dict], Awaitable[dict]]


class YouTube:
    def __init__(self, key: str, get: Optional[Getter] = None, timeout: float = 20.0):
        self._key, self._get, self._timeout = key, get, timeout
        self.units = 0  # quota spent by this client

    async def _call(self, path: str, params: dict, cost: int) -> dict:
        self.units += cost
        params = {**params, "key": self._key}
        if self._get is not None:
            return await self._get(path, params)
        async with httpx.AsyncClient(timeout=self._timeout) as c:
            r = await c.get(f"{BASE}/{path}", params=params)
        if r.status_code != 200:
            try:
                reason = r.json()["error"]["errors"][0]["reason"]
            except Exception:
                reason = r.text[:120]
            raise YouTubeError(r.status_code, reason)
        return r.json()

    async def search_videos(self, query: str, published_after: Optional[datetime] = None, limit: int = 15,
                            region: str = "IN", order: str = "relevance") -> List[Video]:
        params = {"part": "snippet", "q": query, "type": "video", "maxResults": min(limit, 50), "regionCode": region,
                  "order": order}
        if published_after:
            params["publishedAfter"] = published_after.strftime("%Y-%m-%dT%H:%M:%SZ")
        data = await self._call("search", params, SEARCH_COST)
        out = []
        for it in data.get("items", []):
            vid = (it.get("id") or {}).get("videoId")
            sn = it.get("snippet") or {}
            if vid:
                out.append(Video(vid, sn.get("title", ""), sn.get("channelTitle", ""), sn.get("publishedAt", "")))
        return out

    async def comments(self, video_id: str, page_token: str = "", limit: int = 100) -> Tuple[List[Comment], str]:
        """Newest top-level comments first, with the first few replies. Returns (comments, next page token).
        Disabled comments come back as an empty list, not an error."""
        params = {"part": "snippet,replies", "videoId": video_id, "maxResults": min(limit, 100), "order": "time",
                  "textFormat": "plainText"}
        if page_token:
            params["pageToken"] = page_token
        try:
            data = await self._call("commentThreads", params, COMMENTS_COST)
        except YouTubeError as e:
            if e.reason in ("commentsDisabled", "videoNotFound"):
                return [], ""
            raise
        out = []
        for it in data.get("items", []):
            sn = (it.get("snippet") or {})
            top = ((sn.get("topLevelComment") or {}).get("snippet")) or {}
            replies = [((r.get("snippet") or {}).get("textDisplay") or "") for r in ((it.get("replies") or {}).get("comments") or [])]
            out.append(Comment(id=it.get("id", ""), video_id=video_id, author=top.get("authorDisplayName", ""),
                               author_channel=((top.get("authorChannelId") or {}).get("value") or ""),
                               text=top.get("textDisplay") or top.get("textOriginal") or "", published_at=top.get("publishedAt", ""),
                               reply_count=int(sn.get("totalReplyCount") or 0), replies=replies))
        return out, data.get("nextPageToken", "")


def default_client() -> Optional[YouTube]:
    key = api_key()
    return YouTube(key) if key else None


def comment_url(video_id: str, comment_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}"


def to_dt(iso: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat((iso or "").replace("Z", "+00:00"))
    except ValueError:
        return None

