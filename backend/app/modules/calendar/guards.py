"""Safety guards over captions. Used by `calendar_admin.py --dry-check` and by the tests; pure, no I/O except reading the frontend files."""
import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from app.modules.marketing.polish import HYPE, PHONE

from .library import SITE, Entry

FB_MAX = 900
IG_MAX = 2000
IG_TAGS_MIN, IG_TAGS_MAX = 3, 8
IG_TAGS_HARD_MAX = 10
URL = re.compile(r"https?://|www\.", re.I)
HASHTAG = re.compile(r"#\w+")
PRICE = re.compile(r"₹|\brs\.?\s*\d|\binr\b|\blakhs?\b|\bcrores?\b|\bper\s*sq\.?\s*(?:ft|feet)\b|\bsqft\b", re.I)
PREDICT = re.compile(r"\b(will (?:rise|go up|increase|double|appreciate)|expected to (?:rise|grow|open)|appreciation|guaranteed returns?)\b", re.I)
PROMPT = re.compile(r"\?|\bsave\b|\bshare\b|\bcomment\b|शेयर|शेअर|सेव", re.I)
FRONTEND = Path(__file__).resolve().parents[4] / "frontend"


def site_paths(frontend: Optional[Path] = None) -> Set[str]:
    """Public site paths that exist: parsed from the frontend sources (insight slugs, locality slugs, fixed pages)."""
    root = frontend or FRONTEND
    paths = {"/", "/localities", "/insights", "/request-invite"}
    ins = root / "lib" / "marketing" / "insights.ts"
    loc = root / "lib" / "marketing" / "localities.ts"
    if ins.is_file():
        paths |= {f"/insights/{s}" for s in re.findall(r"^\s{4}slug: '([a-z0-9-]+)'", ins.read_text(encoding="utf-8"), re.M)}
    if loc.is_file():
        paths |= {f"/localities/{s}" for s in re.findall(r"^\s{4}slug: '([a-z0-9-]+)'", loc.read_text(encoding="utf-8"), re.M)}
    return paths


def check_entry(e: Entry, paths: Optional[Set[str]] = None) -> List[str]:
    """Problems with one library entry; an empty list means every guard passes."""
    fb, ig = e.fb_caption, e.ig_caption
    out: List[str] = []
    for name, text in (("facebook", fb), ("instagram", ig)):
        if HYPE.search(text):
            out.append(f"{name}: hype word '{HYPE.search(text).group(0)}'")
        if PHONE.search(text):
            out.append(f"{name}: phone number")
        if PRICE.search(text):
            out.append(f"{name}: price wording '{PRICE.search(text).group(0)}'")
        if PREDICT.search(text):
            out.append(f"{name}: prediction wording '{PREDICT.search(text).group(0)}'")
    if URL.search(e.body):
        out.append("body contains a URL")
    if URL.search(ig):
        out.append("instagram caption contains a URL")
    if len(fb) >= FB_MAX:
        out.append(f"facebook caption is {len(fb)} characters (limit {FB_MAX})")
    if len(ig) >= IG_MAX:
        out.append(f"instagram caption is {len(ig)} characters (limit {IG_MAX})")
    tags = len(HASHTAG.findall(ig))
    if tags > IG_TAGS_HARD_MAX or not IG_TAGS_MIN <= tags <= IG_TAGS_MAX:
        out.append(f"instagram has {tags} hashtags (want {IG_TAGS_MIN} to {IG_TAGS_MAX}, never over {IG_TAGS_HARD_MAX})")
    if e.link and "link in our bio" not in ig.lower():
        out.append("instagram caption does not say 'link in our bio'")
    if e.link and paths is not None and e.link not in paths:
        out.append(f"facebook link {e.link} is not a site page")
    last = [ln for ln in e.body.splitlines() if ln.strip()][-1]
    if not PROMPT.search(last):
        out.append("body does not end with a question or a save/share prompt")
    if not e.review.strip():
        out.append("review note is empty")
    if not (e.kicker and e.title and e.points):
        out.append("card text is incomplete")
    return out


def check_all(entries: Iterable[Entry], paths: Optional[Set[str]] = None) -> dict:
    """{slug: [problems]} for the entries that have any."""
    paths = site_paths() if paths is None else paths
    return {e.slug: p for e in entries if (p := check_entry(e, paths))}


def link_url(e: Entry) -> Optional[str]:
    return f"{SITE}{e.link}" if e.link else None
