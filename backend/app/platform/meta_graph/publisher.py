"""Publisher interface, sanitising of error text and the dry-run implementation (never touches the network)."""
import re
import uuid
from dataclasses import dataclass
from typing import List, Optional, Protocol

MAX_ERROR = 300

_PATTERNS = [
    (re.compile(r"(access_token|token)=[^&\s\"'<>]+", re.I), r"\1=[redacted]"),
    (re.compile(r"(\"(?:access_token|token)\"\s*:\s*)\"[^\"]*\"", re.I), r'\1"[redacted]"'),
    (re.compile(r"(Bearer|OAuth)\s+[A-Za-z0-9_\-\.]{20,}", re.I), r"\1 [redacted]"),
    (re.compile(r"\bEA[A-Za-z0-9]{20,}"), "[redacted]"),  # Meta access tokens start with EA...
]


def sanitize(text, secrets=()) -> str:
    """Strip tokens and `access_token=` values from text and truncate it, so it is safe to store and return."""
    out = str(text or "")
    for s in secrets or ():
        if s:
            out = out.replace(s, "[redacted]")
    for rx, repl in _PATTERNS:
        out = rx.sub(repl, out)
    out = " ".join(out.split())
    return out if len(out) <= MAX_ERROR else out[: MAX_ERROR - 3] + "..."


class PublishError(Exception):
    """A publish attempt failed; the message is already safe to store (sanitised by the raiser)."""


@dataclass
class Post:
    channel: str
    text: str
    image_urls: List[str]
    link: Optional[str] = None  # Facebook feed post only (used when there is no image)


@dataclass
class Result:
    external_id: str
    permalink: Optional[str] = None


class Publisher(Protocol):
    async def publish(self, post: Post) -> Result: ...


class DryRunPublisher:
    async def publish(self, post: Post) -> Result:
        return Result(external_id=f"dryrun_{uuid.uuid4().hex[:12]}")
