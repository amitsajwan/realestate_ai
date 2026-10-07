"""Real Meta Graph API publisher (Facebook Page photo/feed post, Instagram single image or carousel)."""
import asyncio
import json
import time
from typing import Awaitable, Callable, Optional
from urllib.parse import quote

import httpx

from .config import SocialConfig
from .publisher import Post, PublishError, Result, sanitize

GRAPH_HOST = "https://graph.facebook.com"
POLL_INTERVAL_S = 2.0
POLL_TIMEOUT_S = 60.0
REQUEST_TIMEOUT_S = 20.0
MAX_CAROUSEL = 10
DEDUP_WINDOW = 12  # recent Instagram posts checked for an identical caption before publishing


class GraphPublisher:
    """`transport`, `sleep` and `clock` are injectable so tests never touch the network or wait."""

    def __init__(self, cfg: SocialConfig, transport: Optional[httpx.AsyncBaseTransport] = None,
                 sleep: Callable[[float], Awaitable[None]] = asyncio.sleep, clock: Callable[[], float] = time.monotonic,
                 poll_interval: float = POLL_INTERVAL_S, poll_timeout: float = POLL_TIMEOUT_S):
        self.cfg, self.transport, self.sleep, self.clock = cfg, transport, sleep, clock
        self.poll_interval, self.poll_timeout = poll_interval, poll_timeout
        self._client: Optional[httpx.AsyncClient] = None

    # ---- low level -------------------------------------------------------------------------------------------
    def _clean(self, text) -> str:
        return sanitize(text, self.cfg.secrets)

    def _url(self, path: str) -> str:
        return f"{GRAPH_HOST}/{self.cfg.graph_version}/" + "/".join(quote(seg, safe="") for seg in str(path).split("/"))

    async def _call(self, method: str, path: str, params: dict) -> dict:
        assert self._client is not None
        token = {"access_token": self.cfg.page_token}
        try:
            if method == "GET":
                resp = await self._client.get(self._url(path), params={**params, **token})
            else:
                resp = await self._client.post(self._url(path), data={**params, **token})
        except httpx.TimeoutException:
            raise PublishError("Graph API request timed out")
        except httpx.HTTPError as e:
            raise PublishError(self._clean(f"Graph API request failed ({type(e).__name__})"))
        try:
            body = resp.json()
        except ValueError:
            raise PublishError(f"Graph API returned HTTP {resp.status_code} with a non-JSON body")
        if not isinstance(body, dict):
            raise PublishError(f"Graph API returned an unexpected response (HTTP {resp.status_code})")
        err = body.get("error")
        if err or resp.status_code >= 400:
            raise PublishError(self._clean(self._describe(err, resp.status_code)))
        return body

    @staticmethod
    def _describe(err, status: int) -> str:
        if not isinstance(err, dict):
            return f"Graph API error (HTTP {status})"
        parts = [f"Graph API error {err.get('code', status)}"]
        if err.get("error_subcode"):
            parts[0] += f"/{err['error_subcode']}"
        msg = f"{parts[0]}: {err.get('message') or 'unknown error'}"
        return f"{msg} (fbtrace_id {err['fbtrace_id']})" if err.get("fbtrace_id") else msg

    @staticmethod
    def _need_id(body: dict, what: str) -> str:
        val = body.get("id")
        if not val:
            raise PublishError(f"Graph API did not return an id for {what}")
        return str(val)

    def _require_https(self, urls) -> None:
        if not all(str(u).lower().startswith("https://") for u in urls):
            raise PublishError("Only https media urls can be sent to Meta (set PUBLIC_MEDIA_BASE_URL to a public https address)")

    # ---- entry point -----------------------------------------------------------------------------------------
    async def publish(self, post: Post) -> Result:
        self._require_https(post.image_urls)
        async with httpx.AsyncClient(transport=self.transport, timeout=REQUEST_TIMEOUT_S) as client:
            self._client = client
            try:
                if post.channel == "facebook_page":
                    return await self._facebook(post)
                if post.channel == "instagram":
                    return await self._instagram(post)
                raise PublishError(f"Unknown channel {post.channel}")
            finally:
                self._client = None

    # ---- Facebook Page ---------------------------------------------------------------------------------------
    async def _facebook(self, post: Post) -> Result:
        page = self.cfg.page_id
        if len(post.image_urls) > 1:
            return await self._facebook_album(post)
        if post.image_urls:
            body = await self._call("POST", f"{page}/photos", {"url": post.image_urls[0], "caption": post.text, "published": "true"})
            post_id = body.get("post_id")
            ext = str(post_id) if post_id else self._need_id(body, "the photo")
            link = await self._fb_permalink(ext) if post_id else None
            if not link:
                try:
                    link = (await self._call("GET", ext, {"fields": "link"})).get("link")
                except PublishError:
                    link = None
            return Result(ext, link)
        params = {"message": post.text}
        if post.link:
            params["link"] = post.link
        body = await self._call("POST", f"{page}/feed", params)
        ext = self._need_id(body, "the post")
        return Result(ext, await self._fb_permalink(ext))

    async def _facebook_album(self, post: Post) -> Result:
        """Several photos in one Page post, like an Instagram carousel: each photo is uploaded unpublished, then one feed post
        attaches them all in order with the caption."""
        page, ids = self.cfg.page_id, []
        for url in post.image_urls[:MAX_CAROUSEL]:
            body = await self._call("POST", f"{page}/photos", {"url": url, "published": "false"})
            ids.append(self._need_id(body, "a photo of the post"))
        params = {"message": post.text}
        for i, fbid in enumerate(ids):
            params[f"attached_media[{i}]"] = json.dumps({"media_fbid": fbid})
        ext = self._need_id(await self._call("POST", f"{page}/feed", params), "the post")
        return Result(ext, await self._fb_permalink(ext))

    async def _fb_permalink(self, post_id: str) -> str:
        """Facebook's own public link for a Page post (permalink_url). The bare 'facebook.com/<page>_<post>' form sends
        logged-out visitors to the login screen, so it is only the fallback when Graph does not answer."""
        try:
            url = (await self._call("GET", post_id, {"fields": "permalink_url"})).get("permalink_url") or ""
        except PublishError:
            url = ""
        if url.startswith("/"):
            url = "https://www.facebook.com" + url
        return url if url.startswith("https://") else f"https://www.facebook.com/{post_id}"

    # ---- Instagram -------------------------------------------------------------------------------------------
    async def _already_on_instagram(self, caption: str, video: bool = False) -> Optional[Result]:
        """The account's recent post with this exact caption, if any. Instagram sometimes publishes a post and still answers
        media_publish with an error (seen live 2026-10-03: error 4/2207051, the carousel appeared twice after one retry), so a
        retry first looks for its own post instead of publishing a copy. Best effort: no answer means "not found"."""
        key = (caption or "").strip()
        if not key:
            return None
        try:
            body = await self._call("GET", f"{self.cfg.ig_id}/media", {"fields": "id,caption,permalink,media_type", "limit": DEDUP_WINDOW})
        except PublishError:
            return None
        for m in body.get("data") or []:
            # a reel and a carousel of the same project share their caption: only the same kind counts as already posted
            if m.get("media_type") and (m["media_type"] == "VIDEO") != video:
                continue
            if (m.get("caption") or "").strip() == key and m.get("id"):
                return Result(str(m["id"]), m.get("permalink"))
        return None

    async def _instagram(self, post: Post) -> Result:
        ig = self.cfg.ig_id
        urls = post.image_urls[:MAX_CAROUSEL]
        if not urls:
            raise PublishError("Instagram needs at least one image")
        found = await self._already_on_instagram(post.text)
        if found:
            return found
        place = {"location_id": post.location_id} if post.location_id else {}
        if len(urls) == 1:
            container = self._need_id(await self._call("POST", f"{ig}/media", {"image_url": urls[0], "caption": post.text, **place}),
                                      "the container")
        else:
            children = []
            for u in urls:
                body = await self._call("POST", f"{ig}/media", {"image_url": u, "is_carousel_item": "true"})
                children.append(self._need_id(body, "a carousel item"))
            container = self._need_id(await self._call("POST", f"{ig}/media", {
                "media_type": "CAROUSEL", "children": ",".join(children), "caption": post.text, **place}), "the carousel")
        await self._wait_finished(container)
        media_id = self._need_id(await self._call("POST", f"{ig}/media_publish", {"creation_id": container}), "the published media")
        permalink = None
        try:
            permalink = (await self._call("GET", media_id, {"fields": "permalink"})).get("permalink")
        except PublishError:
            pass  # best effort
        return Result(media_id, permalink)

    async def _wait_finished(self, container: str) -> None:
        deadline = self.clock() + self.poll_timeout
        while True:
            body = await self._call("GET", container, {"fields": "status_code"})
            code = body.get("status_code")
            if code == "FINISHED":
                return
            if code in ("ERROR", "EXPIRED"):
                detail = f": {body['status']}" if body.get("status") else ""
                raise PublishError(self._clean(f"Instagram could not process the media ({code}){detail}"))
            if self.clock() >= deadline:
                raise PublishError(f"Instagram media was not ready after {int(self.poll_timeout)} s (last status {code or 'unknown'})")
            await self.sleep(self.poll_interval)
