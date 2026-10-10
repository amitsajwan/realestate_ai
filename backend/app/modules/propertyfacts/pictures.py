"""Which of a listing's pictures go on its post cards, and in what order: one ranked pool of the agent's photos, the stills
of its video and the pages of its brochure. Clear, sharp, colourful place shots (site, road, building, plot) first; a
presenter filling the frame, burned-in captions or phone numbers, and text-heavy pages last; near-duplicates (perceptual
hash) of a picture already chosen left out, so neighbouring cards never show the same scene. Pillow only, on thumbnails:
fast, and every failure falls back to a neutral score."""
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from PIL import Image, ImageFilter, ImageStat

NEAR = 10          # dHash bits (of 64) under which two pictures count as the same scene
PLACE = re.compile(r"plot|site|road|gate|entrance|building|tower|facade|layout|boundary|stones?|green|garden|tree|land|"
                   r"aerial|drone|view|amenit|club|pool|street|signboard|park|open space|construction|interior|room|kitchen",
                   re.I)
PERSON = re.compile(r"presenter|person|man |woman|talking|speaking|selfie|face|host|agent", re.I)
SHOTS_FILE = "shots.json"


def shot_notes(frames_dir: Path) -> Dict[str, dict]:
    """{still file name: what the vision model saw in it} written by video_director.best_frames, or {}."""
    try:
        return json.loads((Path(frames_dir) / SHOTS_FILE).read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _dhash(im: Image.Image) -> int:
    g = im.convert("L").resize((9, 8), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for r in range(8):
        for c in range(8):
            bits = (bits << 1) | (px[r * 9 + c] > px[r * 9 + c + 1])
    return bits


def _measure(path: str) -> Optional[dict]:
    """Sharpness, colourfulness, page-likeness (share of near-white paper) and the perceptual hash of one picture."""
    try:
        with Image.open(path) as im:
            im.draft("RGB", (256, 256))
            im = im.convert("RGB")
            im.thumbnail((192, 192))
    except Exception:
        return None
    g = im.convert("L")
    sharp = ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0] ** 0.5          # ~0 (blurred) .. 60+ (crisp)
    r, gg, b = [list(c.getdata()) for c in im.split()]
    rg = [abs(x - y) for x, y in zip(r, gg)]
    yb = [abs((x + y) / 2 - z) for x, y, z in zip(r, gg, b)]
    n = len(rg) or 1

    def ms(v):
        m = sum(v) / n
        return m, (sum((x - m) ** 2 for x in v) / n) ** 0.5
    (mrg, srg), (myb, syb) = ms(rg), ms(yb)
    colour = (srg ** 2 + syb ** 2) ** 0.5 + 0.3 * (mrg ** 2 + myb ** 2) ** 0.5           # Hasler-Suesstrunk, ~0..100
    hist = g.histogram()
    paper = sum(hist[235:]) / n                                                          # brochure text pages are mostly paper
    return {"sharp": sharp, "colour": colour, "paper": paper, "hash": _dhash(im)}


def score(path: str, m: dict, own: bool, note: Optional[dict]) -> float:
    """Higher is a better card picture."""
    s = min(m["sharp"], 40) / 40 * 3 + min(m["colour"], 60) / 60 * 3
    s -= 10 * max(0.0, m["paper"] - 0.25)                    # a page that is mostly white paper is text, not a place
    p = Path(path)
    if own:
        s += 2                                               # the agent's own photo of the property
    if p.parent.name == "brochure":
        s -= 1                                               # a brochure page usually carries the builder's words
    if note:
        what = str(note.get("what") or "")
        if PLACE.search(what):
            s += 2
        if note.get("person_on_screen") or (PERSON.search(what) and not PLACE.search(what)):
            s -= 4
        if note.get("text_on_screen"):
            s -= 2
        if note.get("phone_on_screen"):
            s -= 6
        try:
            s += (float(note.get("score") or 5) - 5) * 0.3
        except (TypeError, ValueError):
            pass
    return s


def _far(h: int, chosen: Iterable[int]) -> bool:
    return all(bin(h ^ c).count("1") > NEAR for c in chosen)


def rank(pool: Sequence[str], own: Iterable[str] = (), notes: Optional[Dict[str, dict]] = None) -> List[str]:
    """`pool` best first, near-duplicates of an earlier pick left out (a picture that cannot be read keeps its place at the
    end). Order of equal scores: the given order."""
    own, notes = set(map(str, own)), notes or {}
    scored, unread = [], []
    for i, p in enumerate(pool):
        m = _measure(p)
        if m is None:
            unread.append(p)
            continue
        note = notes.get(Path(p).name) if Path(p).parent.name == "frames" else None
        scored.append((-score(p, m, p in own, note), i, p, m["hash"]))
    scored.sort()
    out, hashes = [], []
    for _, _, p, h in scored:
        if _far(h, hashes):
            out.append(p)
            hashes.append(h)
    return out + unread


def walkthrough_pictures(pool: Sequence[str], keep: int = 5) -> List[str]:
    """Pictures from a run's ranked pool fit for a walkthrough reel when the listing has fewer than 2 photos: readable files,
    text pages left out (a reel scene shows a picture for seconds, full screen)."""
    out = []
    for p in pool:
        if not Path(p).is_file():
            continue
        m = _measure(p)
        if m is None or m["paper"] > 0.55:
            continue
        out.append(p)
        if len(out) >= keep:
            break
    return out
