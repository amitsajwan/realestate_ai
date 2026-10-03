"""Media records: which upload URLs are ours, enhanced-copy names, and the URL shown for a photo.

Moved unchanged from photoquality/store.py (MODERNIZATION step 2; `_local_path` is now the public `upload_path`); output
pinned by tests/platform_layer/test_media.py. The photo analysis and enhancement stay in photoquality.
"""
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

ENH_SUFFIX = "-enh"
UPLOAD_IMAGE_RE = re.compile(r"^/uploads/images/([A-Za-z0-9][A-Za-z0-9._-]{0,200})$")


def enhanced_name(name: str) -> str:
    return f"{Path(name).stem}{ENH_SUFFIX}.jpg"


def is_enhanced_name(name: str) -> bool:
    return Path(name).stem.endswith(ENH_SUFFIX)


# ---- choosing what to show --------------------------------------------------------------------------
def upload_path(url: Optional[str]) -> Optional[str]:
    """'/uploads/images/x.jpg' for any url (relative or absolute) pointing at our uploads; None otherwise."""
    if not url or not isinstance(url, str):
        return None
    try:
        p = urlparse(url.strip()).path or ""
    except ValueError:
        return None
    m = UPLOAD_IMAGE_RE.match(p)
    return p if m and ".." not in m.group(1) else None


def display_url(m: Dict[str, Any]) -> str:
    """The URL to show for a media record: the enhanced copy when the agent kept 'Use enhanced' on and it is one of our
    own uploads, otherwise the original."""
    url = m.get("url") or ""
    enh = m.get("enhanced_url")
    if m.get("use_enhanced") and upload_path(enh):
        # keep the original's host so absolute and relative urls stay alike
        orig = upload_path(url)
        if orig and url != orig:
            return url[: len(url) - len(orig)] + upload_path(enh)
        return enh
    return url


def public_media(media: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Media for public pages: the chosen url only (no quality details, no second url)."""
    out = []
    for m in media or []:
        if hasattr(m, "model_dump"):
            m = m.model_dump()
        if isinstance(m, dict):
            out.append({"url": display_url(m), "kind": m.get("kind") or "image", "order": m.get("order") or 0})
    return out
