"""Instagram Graph calls for comments (same Page token). Output is normalised to the Facebook shape so the service treats both alike:
post {id, message, permalink, comments: {data: [{id, message, from: {id, name}, created_time, own, replied}]}}."""
from typing import List, Optional

from .graph import EngageGraph, EngageGraphError  # noqa: F401  (EngageGraphError re-exported for callers)

IG_FIELDS = "id,caption,timestamp,permalink,comments.limit(50){id,text,username,timestamp,replies{id,username}}"


class IgGraph(EngageGraph):
    def __init__(self, cfg, transport=None):
        super().__init__(cfg, transport)
        self._username: Optional[str] = None

    async def own_username(self) -> str:
        """Our own Instagram username, fetched once. Comments by it are never answered."""
        if self._username is None:
            body = await self._call("GET", self.cfg.ig_business_id, {"fields": "username"})
            self._username = str(body.get("username") or "").lower()
        return self._username

    async def recent_posts_with_comments(self) -> List[dict]:
        me = await self.own_username()
        body = await self._call("GET", f"{self.cfg.ig_business_id}/media", {"fields": IG_FIELDS, "limit": self.cfg.lookback_posts})
        posts = []
        for m in body.get("data", []):
            items = []
            for c in (m.get("comments") or {}).get("data", []):
                user = str(c.get("username") or "")
                replies = (c.get("replies") or {}).get("data", [])
                items.append({"id": c["id"], "message": c.get("text") or "", "from": {"id": f"ig:{user.lower()}" if user else None, "name": user or None},
                              "created_time": c.get("timestamp"), "own": bool(me) and user.lower() == me,
                              "replied": bool(me) and any(str(r.get("username") or "").lower() == me for r in replies)})
            posts.append({"id": m["id"], "message": m.get("caption") or "", "permalink": m.get("permalink"), "comments": {"data": items}})
        return posts

    async def reply(self, comment_id: str, text: str) -> str:
        body = await self._call("POST", f"{comment_id}/replies", {"message": text})
        return str(body.get("id", ""))

    platform = "instagram"  # private replies and the inbox go through the Page's messaging API with platform=instagram
