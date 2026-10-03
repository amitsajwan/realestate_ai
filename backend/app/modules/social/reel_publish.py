"""Publish a finished reel MP4 to Instagram (Reels) and the Facebook Page (Reels) through the Graph API.

Instagram:  POST {ig}/media (media_type=REELS, video_url, caption, share_to_feed[, cover_url]) -> poll status_code until FINISHED -> POST {ig}/media_publish.
Facebook:   POST {page}/video_reels upload_phase=start -> upload to rupload.facebook.com (file_url header = public https url of the mp4,
            or the binary body) -> poll the video status -> POST {page}/video_reels upload_phase=finish, video_state=PUBLISHED, description.
Both need the file at a public https URL: PUBLIC_MEDIA_BASE_URL + /uploads/reels/<name>.mp4 (see `stage`).
SOCIAL_DRY_RUN (the default) returns fake ids and never touches the network. Errors are sanitised and never contain tokens.
"""
import asyncio
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Awaitable, Callable, Optional
from urllib.parse import urlparse

import httpx

from app.platform.meta_graph.config import SocialConfig
from app.platform.meta_graph.config import load as load_config
from app.platform.meta_graph.graph import REQUEST_TIMEOUT_S, GraphPublisher
from app.platform.meta_graph.publisher import PublishError, Result

REEL_POLL_INTERVAL_S = 5.0
REEL_POLL_TIMEOUT_S = 300.0     # reels take longer than photos to process
UPLOAD_TIMEOUT_S = 180.0
RUPLOAD_HOST = "rupload.facebook.com"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,80}\.mp4$")
COVER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,80}-cover\.jpg$")
COVER_SUFFIX = "-cover.jpg"     # the renderer writes <name>-cover.jpg next to <name>.mp4 (reels.compose.cover_path)
CHANNELS = ("instagram", "facebook_page")


def public_url(cfg: SocialConfig, name: str) -> str:
    """https URL Meta can fetch the staged file from. Requires PUBLIC_MEDIA_BASE_URL to be https."""
    if not NAME_RE.match(name or ""):
        raise PublishError("Invalid reel file name")
    if not cfg.media_url_ok:
        raise PublishError("Set PUBLIC_MEDIA_BASE_URL to a public https address so Meta can fetch the video")
    return f"{cfg.media_base_url}/uploads/reels/{name}"


def cover_name(name: str) -> str:
    """'reel-x.mp4' -> 'reel-x-cover.jpg'."""
    return name[:-4] + COVER_SUFFIX


def cover_file(mp4: Path) -> Optional[Path]:
    """The cover JPG rendered next to `mp4`, or None when there is none (older reels)."""
    p = Path(mp4).with_name(Path(mp4).stem + COVER_SUFFIX)
    return p if p.is_file() and p.stat().st_size > 0 else None


def public_cover_url(cfg: SocialConfig, name: str) -> str:
    """https URL of a staged cover under /uploads/reels/ (built like `public_url`)."""
    if not COVER_RE.match(name or ""):
        raise PublishError("Invalid reel cover file name")
    if not cfg.media_url_ok:
        raise PublishError("Set PUBLIC_MEDIA_BASE_URL to a public https address so Meta can fetch the cover")
    return f"{cfg.media_base_url}/uploads/reels/{name}"


def staged_cover_url(cfg: SocialConfig, mp4: Path, uploads_dir: Path, name: str) -> Optional[str]:
    """Copy the cover of `mp4` (if it has one) to <uploads>/reels/<name minus .mp4>-cover.jpg and return its public url; None
    when there is no cover, so the reel is published exactly as before."""
    src = cover_file(mp4)
    if src is None or not NAME_RE.match(name or ""):
        return None
    dest = Path(uploads_dir) / "reels" / cover_name(name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dest.resolve():
        shutil.copyfile(src, dest)
    return public_cover_url(cfg, dest.name)


def stage(mp4: Path, uploads_dir: Path, name: Optional[str] = None) -> str:
    """Copy the video to <uploads>/reels/<name>.mp4 (served at /uploads/reels/...) and return the file name."""
    name = name or f"reel-{uuid.uuid4().hex[:12]}.mp4"
    if not NAME_RE.match(name):
        raise PublishError("Invalid reel file name")
    dest = Path(uploads_dir) / "reels"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(mp4, dest / name)
    return name


class ReelPublisher(GraphPublisher):
    """Reuses GraphPublisher's request/error handling; `transport`, `sleep` and `clock` are injectable (tests never use the network)."""

    def __init__(self, cfg: SocialConfig, transport: Optional[httpx.AsyncBaseTransport] = None,
                 sleep: Callable[[float], Awaitable[None]] = asyncio.sleep, clock: Callable[[], float] = time.monotonic,
                 poll_interval: float = REEL_POLL_INTERVAL_S, poll_timeout: float = REEL_POLL_TIMEOUT_S):
        super().__init__(cfg, transport, sleep, clock, poll_interval, poll_timeout)

    async def publish_reel(self, channel: str, video_url: str, caption: str, file_path: Optional[Path] = None,
                           cover_url: Optional[str] = None) -> Result:
        if channel not in CHANNELS:
            raise PublishError(f"Unknown channel {channel}")
        if not self.cfg.configured(channel):
            raise PublishError(f"{channel} is not configured")
        if not str(video_url).lower().startswith("https://"):
            raise PublishError("Only https media urls can be sent to Meta (set PUBLIC_MEDIA_BASE_URL to a public https address)")
        async with httpx.AsyncClient(transport=self.transport, timeout=REQUEST_TIMEOUT_S) as client:
            self._client = client
            try:
                if channel == "instagram":
                    return await self._instagram_reel(video_url, caption, cover_url)
                return await self._facebook_reel(video_url, caption, file_path)
            finally:
                self._client = None

    # ---- Instagram -------------------------------------------------------------------------------------------
    async def _instagram_reel(self, video_url: str, caption: str, cover_url: Optional[str] = None) -> Result:
        ig = self.cfg.ig_id
        params = {"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true"}
        if cover_url and str(cover_url).lower().startswith("https://"):
            params["cover_url"] = cover_url   # the hook still as the grid/feed cover (else Instagram picks a frame)
        body = await self._call("POST", f"{ig}/media", params)
        container = self._need_id(body, "the reel container")
        await self._wait_finished(container)
        media_id = self._need_id(await self._call("POST", f"{ig}/media_publish", {"creation_id": container}), "the published reel")
        permalink = None
        try:
            permalink = (await self._call("GET", media_id, {"fields": "permalink"})).get("permalink")
        except PublishError:
            pass  # best effort
        return Result(media_id, permalink)

    # ---- Facebook Page ---------------------------------------------------------------------------------------
    async def _facebook_reel(self, video_url: str, caption: str, file_path: Optional[Path]) -> Result:
        page = self.cfg.page_id
        start = await self._call("POST", f"{page}/video_reels", {"upload_phase": "start"})
        video_id = self._need_id({"id": start.get("video_id")}, "the reel upload session")
        await self._upload(video_id, start.get("upload_url"), video_url, file_path)
        await self._wait_uploaded(video_id)
        done = await self._call("POST", f"{page}/video_reels", {"upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED",
                                                               "description": caption})
        if done.get("success") is False:
            raise PublishError("Facebook did not accept the reel")
        return Result(video_id, f"https://www.facebook.com/reel/{video_id}")

    def _rupload_url(self, video_id: str, given: Optional[str]) -> str:
        """The upload URL from step 1 if it is on rupload.facebook.com (the token is only ever sent there), else the documented one."""
        if given:
            u = urlparse(str(given))
            if u.scheme == "https" and u.hostname == RUPLOAD_HOST:
                return str(given)
        return f"https://{RUPLOAD_HOST}/video-upload/{self.cfg.graph_version}/{video_id}"

    async def _upload(self, video_id: str, upload_url, video_url: str, file_path: Optional[Path]) -> None:
        url = self._rupload_url(video_id, upload_url)
        headers = {"Authorization": f"OAuth {self.cfg.page_token}"}
        kwargs = {}
        if file_path is not None:
            data = Path(file_path).read_bytes()
            headers.update({"offset": "0", "file_size": str(len(data)), "Content-Type": "application/octet-stream"})
            kwargs["content"] = data
        else:
            headers["file_url"] = video_url
        assert self._client is not None
        try:
            resp = await self._client.post(url, headers=headers, timeout=UPLOAD_TIMEOUT_S, **kwargs)
        except httpx.TimeoutException:
            raise PublishError("Facebook video upload timed out")
        except httpx.HTTPError as e:
            raise PublishError(self._clean(f"Facebook video upload failed ({type(e).__name__})"))
        try:
            body = resp.json()
        except ValueError:
            body = {}
        err = body.get("error") if isinstance(body, dict) else None
        if err or resp.status_code >= 400 or not (isinstance(body, dict) and body.get("success")):
            detail = self._describe(err, resp.status_code) if err else f"Facebook video upload was not accepted (HTTP {resp.status_code})"
            raise PublishError(self._clean(detail))

    async def _wait_uploaded(self, video_id: str) -> None:
        """Wait until Facebook has the bytes (upload_complete / processing / ready) before finishing."""
        deadline = self.clock() + self.poll_timeout
        while True:
            status = (await self._call("GET", video_id, {"fields": "status"})).get("status") or {}
            state = status.get("video_status") if isinstance(status, dict) else None
            if state in ("upload_complete", "processing", "ready"):
                return
            if state in ("upload_failed", "error", "expired"):
                raise PublishError(self._clean(f"Facebook could not process the video ({state})"))
            if self.clock() >= deadline:
                raise PublishError(f"Facebook video was not received after {int(self.poll_timeout)} s (last status {state or 'unknown'})")
            await self.sleep(self.poll_interval)


async def publish_reel(channel: str, video_url: str, caption: str, cfg: Optional[SocialConfig] = None, file_path: Optional[Path] = None,
                       dry_run: Optional[bool] = None, cover_url: Optional[str] = None, **kwargs) -> Result:
    """Entry point. Dry run (SOCIAL_DRY_RUN, the default) returns a fake id without any network call.
    `cover_url` (Instagram only): public https url of the cover JPG; the Facebook path ignores it."""
    cfg = cfg or load_config()
    if channel not in CHANNELS:
        raise PublishError(f"Unknown channel {channel}")
    if (cfg.dry_run if dry_run is None else dry_run):
        return Result(external_id=f"dryrun_{uuid.uuid4().hex[:12]}")
    return await ReelPublisher(cfg, **kwargs).publish_reel(channel, video_url, caption, file_path, cover_url=cover_url)
