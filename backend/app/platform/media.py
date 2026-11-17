"""Media records: which upload URLs are ours, enhanced-copy names, the URL shown for a photo, and keeping a public photo.

Moved unchanged from photoquality/store.py (MODERNIZATION step 2; `_local_path` is now the public `upload_path`); output
pinned by tests/platform_layer/test_media.py. The photo analysis and enhancement stay in photoquality. `keep_photo` (2026-11-17)
is the one way a module stores a picture people send for a public page: checked, turned upright, sized and saved as WebP.
"""
import io
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from PIL import Image, ImageOps

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
    """Media for public pages: photos only, the chosen url only (no quality details, no second url). An agent's project files
    (the builder's raw video and brochure) are working material for Studio, never shown as they are."""
    out = []
    for m in media or []:
        if hasattr(m, "model_dump"):
            m = m.model_dump()
        if isinstance(m, dict) and (m.get("kind") or "image") == "image":
            out.append({"url": display_url(m), "kind": m.get("kind") or "image", "order": m.get("order") or 0})
    return out


# ---- keeping a photo for a public page ---------------------------------------------------------------------------------
UPLOADS = Path("uploads")
# the same limits as the listing photo upload (api/v1/endpoints/uploads.py), less GIF: an animation is not a photo
PHOTO_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_PHOTO_BYTES = 10 * 1024 * 1024
MAX_PHOTO_PIXELS = 60_000_000          # a phone's 50 MP shot; more is a decompression bomb, not a photo
# the longest side kept for the page and for the small copy lists show; the project pages keep 1600 too (areastats.profile)
PHOTO_SIZES: Tuple[Tuple[str, int], ...] = (("", 1600), ("-small", 640))
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,80}$")


class PhotoError(ValueError):
    """The bytes are not a photo we can keep (unreadable, too small, too many pixels)."""


def keep_photo(body: bytes, folder: str, name: str, min_side: int = 0, root: Path = UPLOADS) -> Dict[str, Any]:
    """Save a photo under uploads/<folder>/<name>.webp at most 1600 px on its long side, plus <name>-small.webp at 640 px.

    Turned upright from its EXIF orientation, then saved without EXIF: a phone writes where it stood (GPS) into every photo,
    and a public page must not carry that. Returns {url, small_url, width, height}; urls are site-relative (/uploads/...),
    which Caddy sends to the api on the public address. Raises PhotoError when it cannot be read or is under `min_side`
    on its long side."""
    if not _NAME_RE.match(name) or not all(_NAME_RE.match(p) for p in folder.split("/")):
        raise PhotoError("bad file name")
    try:
        im = Image.open(io.BytesIO(body))
        if im.width * im.height > MAX_PHOTO_PIXELS:
            raise PhotoError("too many pixels")
        im.load()
        im = ImageOps.exif_transpose(im).convert("RGB")
    except PhotoError:
        raise
    except Exception as e:   # PIL raises many kinds for a broken or foreign file
        raise PhotoError("not a readable picture") from e
    if max(im.size) < min_side:
        raise PhotoError("too small")
    out_dir = root / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    rel = (root / folder).relative_to(root).as_posix()
    out: Dict[str, Any] = {}
    for suffix, side in PHOTO_SIZES:
        copy = im.copy()
        copy.thumbnail((side, side), Image.LANCZOS)
        copy.save(out_dir / f"{name}{suffix}.webp", "WEBP", quality=82, method=4)
        if not suffix:
            out.update(url=f"/uploads/{rel}/{name}.webp", width=copy.width, height=copy.height)
        else:
            out["small_url"] = f"/uploads/{rel}/{name}{suffix}.webp"
    return out


def drop_photo(folder: str, name: str, root: Path = UPLOADS) -> None:
    """Remove what keep_photo saved (a record that could not be stored afterwards). Never raises."""
    for suffix, _ in PHOTO_SIZES:
        try:
            (root / folder / f"{name}{suffix}.webp").unlink(missing_ok=True)
        except OSError:
            pass
