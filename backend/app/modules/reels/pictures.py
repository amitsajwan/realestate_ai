"""Pictures for reels that have no photos of their own (guide reels: a MHADA deadline, a scheme): Gemini draws each shot from a
prompt, then Gemini looks at it and names what would embarrass us on a public reel (readable text, a logo, a wrong hand). A
picture with problems is drawn again; after the last try the shot has no picture (the caller decides).

A picture someone made by hand wins: `own/<n>.jpg|png` in the reel's folder is used as it is, no check (owner 2026-10-17:
"we can create images ourself and pass to team").

Every drawn picture is an illustration: the reel says so on screen (guide_reels.SYMBOLIC), and nothing drawn is ever called a
real project or MHADA's homes. Costs about Rs 3-4 a picture (gemini-3.1-flash-image, our paid key)."""
import base64
import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import httpx

log = logging.getLogger(__name__)

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
IMAGE_MODELS = ("gemini-3.1-flash-image", "gemini-2.5-flash-image")
CHECK_MODELS = ("gemini-3-flash-preview", "gemini-flash-latest")
TRIES = 3
# Said before every shot. 'No text' is the rule that matters: the first test (2026-10-17) drew a real calendar brand with '2024'
# and jumbled dates; our own overlays carry every date and word.
STYLE = ("Photorealistic vertical photo, 9:16 portrait. Pune, Maharashtra, present day. Ordinary middle-class Marathi people, "
         "natural candid documentary style, warm natural light, true-to-life colours. Absolutely no text, letters, numbers, "
         "logos, brand names, posters, calendars with dates or watermarks anywhere in the image; any screen is blurred and unreadable.")
# Judged at phone size. The first strict check (2026-10-17) refused all 18 pictures for 'deformed fingers' that were not there at
# reel size; the pictures were good. Only what a viewer would clearly see in three seconds on a phone blocks a picture.
CHECK = ("You check a photo before it goes into a public Instagram reel, watched on a phone for about three seconds. It was asked "
         "for as:\n{want}\n\nList only BLOCKING problems an ordinary viewer would clearly notice at phone size: large readable "
         "text, words or digits; a recognisable logo or brand name; an obviously wrong body (a clearly extra or missing limb, a "
         "large hand with clearly wrong fingers in the foreground, a melted face); or a scene that is plainly not what was asked. "
         "Do NOT list small or background details, slightly odd fingers, blurred or tiny gibberish, lighting or style differences. "
         'Answer JSON only: {{"blocking": ["..."]}} with an empty list when the photo can be used.')
OWN_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


class PictureError(Exception):
    pass


def available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def _post(model: str, body: dict, timeout: float = 120.0) -> dict:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise PictureError("GEMINI_API_KEY is not set")
    try:
        r = httpx.post(URL.format(model=model), headers={"x-goog-api-key": key}, json=body, timeout=timeout)
    except Exception as e:
        raise PictureError(f"{model} unreachable ({type(e).__name__})")
    if r.status_code >= 400:
        raise PictureError(f"{model} HTTP {r.status_code}: {r.text[:200]}".replace(key, "[redacted]"))
    return r.json()


def _parts(resp: dict) -> list:
    return ((resp.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []


def draw(prompt: str, aspect: str = "9:16") -> bytes:
    """One picture (PNG or JPEG bytes) for `prompt`, with STYLE before it. Raises PictureError when no model draws."""
    body = {"contents": [{"parts": [{"text": f"{STYLE}\n\n{prompt}"}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}}
    why = "no model answered"
    for model in IMAGE_MODELS:
        try:
            resp = _post(model, body)
        except PictureError as e:
            why = str(e)
            continue
        for p in _parts(resp):
            data = (p.get("inlineData") or {}).get("data")
            if data:
                return base64.b64decode(data)
        why = f"{model} answered without a picture"
    raise PictureError(why)


def problems(img: bytes, prompt: str) -> List[str]:
    """What Gemini sees wrong in the picture ([] = fine). A check that cannot run counts as a problem: an unchecked picture
    never goes out on its own."""
    mime = "image/png" if img[:4] == b"\x89PNG" else "image/jpeg"
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": mime, "data": base64.b64encode(img).decode()}},
                                    {"text": CHECK.format(want=prompt)}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    for model in CHECK_MODELS:
        try:
            resp = _post(model, body, timeout=90.0)
            text = "".join(p.get("text", "") for p in _parts(resp))
            found = json.loads(text).get("blocking")
        except (PictureError, ValueError, AttributeError) as e:
            log.warning("pictures: check by %s failed: %s", model, e)
            continue
        if isinstance(found, list):
            return [str(x) for x in found if str(x).strip()]
    return ["the picture could not be checked"]


def own(folder: Path, n: int) -> Optional[Path]:
    """The hand-made picture for shot `n` (1-based), if one was put in `folder`/own."""
    for suffix in OWN_SUFFIXES:
        p = Path(folder) / "own" / f"{n}{suffix}"
        if p.is_file():
            return p
    return None


def shot(folder: Path, n: int, prompt: str, tries: int = TRIES) -> Tuple[Optional[Path], dict]:
    """The picture for shot `n`: a hand-made one, else one already drawn and passed earlier (`<n>.png`, kept so a re-render
    costs nothing), else drawn now until one passes the check. (path or None, a note of what happened)."""
    folder = Path(folder)
    mine = own(folder, n)
    if mine:
        return mine, {"shot": n, "from": "own"}
    done = folder / f"{n}.png"
    if done.is_file():
        return done, {"shot": n, "from": "drawn earlier"}
    folder.mkdir(parents=True, exist_ok=True)
    seen: List[str] = []
    for k in range(1, tries + 1):
        try:
            img = draw(prompt)
        except PictureError as e:
            seen.append(str(e))
            continue
        found = problems(img, prompt)
        if not found:
            done.write_bytes(img)
            return done, {"shot": n, "from": "drawn", "tries": k, "rejected": seen}
        (folder / f"{n}-rejected-{k}.png").write_bytes(img)   # kept for a look: what the check refused and why (the note)
        seen.append("; ".join(found))
        log.info("pictures: shot %s try %s refused: %s", n, k, found)
    return None, {"shot": n, "from": "none", "rejected": seen}


def shots(folder: Path, prompts: Sequence[str]) -> Tuple[List[Optional[Path]], List[dict]]:
    out, notes = [], []
    for i, prompt in enumerate(prompts, start=1):
        p, note = shot(folder, i, prompt)
        out.append(p)
        notes.append(note)
    return out, notes
