"""Facebook Graph calls for comments: list recent posts with their comments, reply to a comment. Errors are sanitised."""
import json
from typing import List, Optional

import httpx

from app.platform.meta_graph.publisher import sanitize

from .config import EngageConfig


class EngageGraphError(Exception):
    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code  # Meta's error code: 190 = the access token is no longer valid


class EngageGraph:
    def __init__(self, cfg: EngageConfig, transport: Optional[httpx.AsyncBaseTransport] = None):
        self.cfg, self._transport = cfg, transport

    def _url(self, path: str) -> str:
        return f"https://graph.facebook.com/{self.cfg.graph_version}/{path}"

    async def _call(self, method: str, path: str, params: dict) -> dict:
        params = {**params, "access_token": self.cfg.page_token}
        try:
            async with httpx.AsyncClient(timeout=30, transport=self._transport) as c:
                r = await (c.get(self._url(path), params=params) if method == "GET" else c.post(self._url(path), data=params))
            body = r.json()
        except Exception as e:
            raise EngageGraphError(sanitize(f"network error ({type(e).__name__})", self.cfg.secrets))
        if r.status_code >= 400 or "error" in body:
            err = body.get("error") or {}
            raise EngageGraphError(sanitize(err.get("message", f"HTTP {r.status_code}"), self.cfg.secrets), int(err.get("code") or 0))
        return body

    async def recent_posts_with_comments(self) -> List[dict]:
        fields = "id,message,created_time,comments.limit(50){id,message,from,created_time,parent,permalink_url}"
        body = await self._call("GET", f"{self.cfg.page_id}/posts", {"fields": fields, "limit": self.cfg.lookback_posts})
        return body.get("data", [])

    async def reply(self, comment_id: str, text: str) -> str:
        body = await self._call("POST", f"{comment_id}/comments", {"message": text})
        return str(body.get("id", ""))

    # ---- private replies (needs pages_messaging; instagram_manage_messages for Instagram) ---------------------------------------
    platform = "messenger"

    async def private_reply(self, comment_id: str, text: str) -> str:
        """One private message to the person who wrote the comment (Meta allows one per comment, within 7 days). Returns their
        Page-scoped id, which is how their answer is found in the inbox later."""
        body = await self._call("POST", f"{self.cfg.page_id}/messages",
                                {"recipient": json.dumps({"comment_id": comment_id}), "message": json.dumps({"text": text})})
        return str(body.get("recipient_id", ""))

    async def inbox(self, limit: int = 25) -> List[dict]:
        """Recent conversations: [{participant ids, messages: [{message, from: {id}, created_time}]}], newest first."""
        fields = "participants,updated_time,messages.limit(10){message,from,created_time}"
        body = await self._call("GET", f"{self.cfg.page_id}/conversations", {"platform": self.platform, "fields": fields, "limit": limit})
        return body.get("data", [])
