"""Small helpers shared by the source plugins. Standard library only."""
import hashlib
import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TAG = re.compile(r"<[^>]*>")
_WS = re.compile(r"\s+")
_DROP_PARAMS = ("utm_", "fbclid", "gclid", "mc_", "ref_", "igshid")


def strip_html(text: Optional[str]) -> str:
    """Tags out, entities decoded, whitespace collapsed. Handles double-escaped markup (RSS descriptions)."""
    if not text:
        return ""
    s = html.unescape(text)
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = _TAG.sub(" ", s)
    return _WS.sub(" ", html.unescape(s)).strip()


def canonical_url(url: str) -> str:
    """Drop fragment and tracking params, lowercase scheme/host, keep the rest in order."""
    parts = urlsplit((url or "").strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith(_DROP_PARAMS)]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(query), ""))


def item_id(url: str) -> str:
    return hashlib.sha1(canonical_url(url).encode("utf-8")).hexdigest()


def parse_rfc822(value: Optional[str]) -> Optional[datetime]:
    """RSS pubDate to an aware UTC datetime, or None when unparseable."""
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value.strip())
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
