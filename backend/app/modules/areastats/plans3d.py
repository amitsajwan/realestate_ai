"""3D floor plans drawn from a project's own floor plans (owner 2026-10-31: "if we can fetch floor plans that are correct, we use AI
to build a 3d floor plan"; "its fine if we know floor plan from other site is correct ... if we generate our own").

For each stored unit plan (areastats.profile `plans`: the builder's site, the brochure, or another site's copy):
1. read: Gemini reads the plan into JSON (title, each room's name, the sq ft printed in it, the legend's dimensions). The free
   vision models were tried first and made sizes up (Lodha Camelot: Study 71 sq ft for a printed 51), so only Gemini reads.
2. check, by code: two readings by two Gemini models give the same rooms and the same printed sizes (a misread is rarely made
   twice); a unit plan (not a master or typical-floor plan) with MIN_ROOMS rooms; a room that prints both a size and legend
   dimensions has the printed size inside LEGEND times the legend's area (10'6" X 12'0" + 3'9" X 2'0" = 133.5 sq ft): builders
   print more than the legend's rectangles (Camelot: kitchen 142 printed, 107 by the legend; staff room 64 and 40; niches and
   wardrobes), so this only catches a gross misread (829 for 289); the second reading catches the near ones; the bedrooms named match the plan title's count when it states one. A plan that fails is not drawn.
3. draw: Gemini draws a 3D isometric cutaway from the plan picture itself (PROMPT: the same walls and rooms, our colours, only the
   room names written). About Rs 4 a picture.
4. verify: Gemini compares the drawing with the plan: every room of the plan is there with its name, none added, the layout the
   same, no area or dimension written anywhere and no garbled name (a first Camelot 4 BHK drawing wrote "MASTER BEDROOM 207 SQ.FT." for a
   printed 297: sizes are only ever shown from the checked reading, beside the picture). A drawing that fails is drawn again
   (DRAW_TRIES), then dropped.
Kept as WebP under uploads/project_media/<regno>-3d/ and on the record as `plans_3d` = {at, items: [{path, width, height, title,
label, rooms: [{name, sqft, dims}], source: {site, kind, path}}], tried: [{path, ok, why}]}. Only what passed all four is
shown (`public`), always called a drawing made from the builder's or the site's plan, with the room sizes the plan prints.
Run by hand for now (scripts/plans_3d.py <regno>): one project to judge the look before it runs by itself.
"""
import asyncio
import hashlib
import io
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, List, Optional, Tuple

from PIL import Image

from app.platform import gemini

log = logging.getLogger(__name__)

MIN_ROOMS = 4
LEGEND = (0.8, 2.0)                    # printed sq ft over the legend's area (Camelot 2026-10-31: 1.0 to 1.6, its staff room)
MAX_PLANS = 6
DRAW_TRIES = 3
KEEP_SIDE = 1600

READ = ("Read this picture exactly. Answer JSON: {\"unit_plan\": true only when it is the plan of ONE apartment (false for a master "
        "plan, site plan, typical floor plan with several flats, elevation or photo), \"title\": the plan's printed title or null, "
        "\"rooms\": [{\"name\": as printed, \"printed_sqft\": the area number printed inside that room or null when none is "
        "printed there, \"legend_dims\": the dimension text the legend gives for that room, exactly, or null}]}. Never guess or "
        "work anything out: null when it is not printed.")
PROMPT = ("Turn this exact apartment floor plan into a clean 3D isometric cutaway view (dollhouse view from above at about 45 degrees, "
          "walls cut at waist-to-door height). Keep the layout EXACTLY as drawn: same walls, same rooms in the same places and "
          "proportions, same doors, windows, balcony/deck, kitchen and toilets; do not add, remove, merge or move any room. "
          "Furnish each room simply as the plan shows it. Style: bright soft daylight, warm white walls, light oak floors, muted sage "
          "and sand accents, clean modern architectural visualisation on a plain off-white background. Write each room's name from "
          "the plan in small clean dark grey capital letters on its floor, exactly as the plan writes it (e.g. MASTER BEDROOM, "
          "BEDROOM-02, LIVING/DINING, KITCHEN). Never write an area, sq ft or a dimension anywhere. No other text, no legend, no "
          "logo, no watermark, no key plan, no compass.")
VERIFY = ("The first picture is an apartment floor plan, the second a 3D drawing made from it. The plan's rooms are: {rooms}. "
          "Answer JSON: {{\"missing\": [rooms of the plan not in the drawing, or drawn without their name], \"extra\": [rooms in the "
          "drawing that the plan does not have], \"same_layout\": true only when every room sits where the plan has it, with "
          "the same neighbours, doors and outer shape, \"sizes\": [every area, sq ft figure or dimension written in the drawing; a room's "
          "own number such as BEDROOM-02 is not one], \"misspelled\": [room names written garbled or as another word in the drawing; "
          "spacing, hyphens and leading zeros do not count]}}.")

DIM = re.compile(r"(\d{1,2})\s*'\s*(?:(\d{1,2}(?:\.\d+)?)\s*(?:\"|''|”|″)?)?\s*[x×X]\s*(\d{1,2})\s*'\s*(?:(\d{1,2}(?:\.\d+)?)\s*(?:\"|''|”|″)?)?")
BED = re.compile(r"\bbed\s*-?\s*room|\bbedroom|\bbed\b", re.I)
TITLE_BEDS = re.compile(r"\b([1-5])\s*(?:-|\s)?\s*(?:bhk|bed)", re.I)

Read = Callable[..., Awaitable[dict]]            # read(images, prompt, models=(...)) -> dict
Draw = Callable[[bytes, str], Awaitable[bytes]]


def dims_sqft(text: Optional[str]) -> Optional[float]:
    """The area of a legend's dimensions: "10'6\" X 12'0\" + 3'9\" X 2'0\"" -> 133.5; None when there is no dimension pair."""
    parts = DIM.findall(text or "")
    if not parts:
        return None
    total = 0.0
    for a_ft, a_in, b_ft, b_in in parts:
        total += (int(a_ft) + float(a_in or 0) / 12) * (int(b_ft) + float(b_in or 0) / 12)
    return round(total, 1)


def _num(v: Any) -> Optional[float]:
    """45, "45", "45 SQ.FT." -> 45.0 (models write it either way); None for anything else."""
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(v)) if isinstance(v, (int, float, str)) and not isinstance(v, bool) else None
    n = float(m.group(1)) if m else None
    return n if n else None


def check(reading: Any) -> Tuple[bool, str, List[dict]]:
    """(ok, why, rooms): rooms = [{name, sqft, dims}] with the printed sq ft, else the legend's area rounded."""
    if not isinstance(reading, dict) or reading.get("unit_plan") is not True:
        return False, "not one apartment's plan", []
    rooms = []
    for r in reading.get("rooms") or []:
        if not isinstance(r, dict) or not str(r.get("name") or "").strip():
            continue
        name = " ".join(str(r["name"]).split())
        printed, dims = _num(r.get("printed_sqft")), " ".join(str(r.get("legend_dims") or "").split()) or None
        legend = dims_sqft(dims)
        if printed and legend and not LEGEND[0] <= printed / legend <= LEGEND[1]:
            return False, f"{name}: {printed:g} sq ft printed, {legend:g} from {dims}", []
        sqft = printed or legend
        rooms.append({"name": name, "sqft": int(round(sqft)) if sqft else None, "dims": dims})
    if len(rooms) < MIN_ROOMS:
        return False, f"{len(rooms)} rooms read", []
    beds = sum(1 for r in rooms if BED.search(r["name"]))
    m = TITLE_BEDS.search(str(reading.get("title") or ""))
    if m and beds and int(m.group(1)) != beds:
        return False, f"title says {m.group(1)} bedrooms, {beds} named", []
    return True, f"{len(rooms)} rooms", rooms


def same_reading(a: Any, b: Any) -> Tuple[bool, str]:
    """Two readings of one plan name the same rooms with the same printed sizes ("BEDROOM -02" is "BEDROOM-02")."""
    def rooms(r: Any) -> dict:
        return {re.sub(r"[^A-Z0-9]", "", str(x.get("name") or "").upper()): _num(x.get("printed_sqft"))
                for x in (r or {}).get("rooms") or [] if isinstance(x, dict)} if isinstance(r, dict) else {}
    ra, rb = rooms(a), rooms(b)
    if ra != rb:
        diff = sorted(k for k in set(ra) | set(rb) if ra.get(k, -1) != rb.get(k, -1))
        return False, f"two readings differ on {', '.join(diff[:4])}"
    return True, ""


def verified(answer: Any) -> Tuple[bool, str]:
    if not isinstance(answer, dict):
        return False, "no check answer"
    missing, extra = answer.get("missing") or [], answer.get("extra") or []
    digits, wrong = answer.get("sizes") or [], answer.get("misspelled") or []
    if missing or extra or digits or wrong or answer.get("same_layout") is not True:
        return False, "; ".join(x for x in (f"missing {missing}" if missing else "", f"extra {extra}" if extra else "",
                                            f"sizes written {digits[:4]}" if digits else "", f"misspelled {wrong[:4]}" if wrong else "",
                                            "" if answer.get("same_layout") is True else "layout differs") if x)
    return True, "matches the plan"


def webp(data: bytes) -> Tuple[bytes, int, int]:
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((KEEP_SIDE, KEEP_SIDE))
    out = io.BytesIO()
    im.save(out, "WEBP", quality=86)
    return out.getvalue(), im.width, im.height


def unit_plans(profile: Optional[dict]) -> List[dict]:
    """The stored plans worth reading: not a master or site plan by their caption, with a file on disk."""
    return [p for p in (profile or {}).get("plans") or []
            if p.get("path") and not re.search(r"master|site|layout|location|typical", str(p.get("alt") or ""), re.I)][:MAX_PLANS]


def label_of(plan: dict, title: Optional[str]) -> str:
    """'3 BHK with study' from the stored caption ("Lodha Camelot 3 BHK with study floor plan"), else the plan's own title."""
    m = re.search(r"(\d(?:\.5)?\s*bhk.*?)(?:\s+floor\s*plan)?$", str(plan.get("alt") or ""), re.I)
    return m.group(1).strip() if m else (title or "Floor plan")


async def make(doc: dict, now: datetime, read: Optional[Read] = None, draw: Optional[Draw] = None,
               uploads: Path = Path("uploads"), redo: bool = False) -> dict:
    """{"plans_3d": {...}} for one project record (a group's primary: its profile holds the plans). A plan already drawn is kept
    unless `redo`."""
    read = read or gemini.read
    draw = draw or gemini.draw_from
    regno = str(doc.get("regno") or doc["_id"])
    items, tried = [], []
    done = {} if redo else {(i.get("source") or {}).get("path"): i for i in (doc.get("plans_3d") or {}).get("items") or []}
    for plan in unit_plans(doc.get("profile")):
        if plan["path"] in done:   # drawn and checked before: kept, not paid for again
            items.append(done[plan["path"]])
            tried.append({"path": plan["path"], "ok": True, "why": "kept"})
            continue
        src = uploads / plan["path"]
        if not src.is_file():
            tried.append({"path": plan["path"], "ok": False, "why": "plan file missing"})
            continue
        image = await asyncio.to_thread(src.read_bytes)
        try:
            reading = await read([image], READ, models=gemini.READ_MODELS[:1])
            second = await read([image], READ, models=gemini.READ_MODELS[1:])
        except gemini.GeminiError as e:
            tried.append({"path": plan["path"], "ok": False, "why": f"read failed: {e}"})
            continue
        ok, why = same_reading(reading, second)
        if ok:
            ok, why, rooms = check(reading)
        reading_title = (" ".join(str(reading.get("title") or "").split()) or None) if isinstance(reading, dict) else None
        if not ok:
            tried.append({"path": plan["path"], "ok": False, "why": why})
            continue
        drawn, why = None, ""
        for _ in range(DRAW_TRIES):
            try:
                pic = await draw(image, PROMPT)
                good, why = verified(await read([image, pic], VERIFY.format(rooms=", ".join(r["name"] for r in rooms))))
            except gemini.GeminiError as e:
                good, why = False, f"draw failed: {e}"
            if good:
                drawn = pic
                break
        if drawn is None:
            tried.append({"path": plan["path"], "ok": False, "why": why})
            continue
        body, w, h = await asyncio.to_thread(webp, drawn)
        rel = f"project_media/{regno.lower()}-3d/{hashlib.sha1(body).hexdigest()[:16]}.webp"
        out = uploads / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(out.write_bytes, body)
        items.append({"path": rel, "width": w, "height": h, "title": reading_title, "label": label_of(plan, reading_title),
                      "rooms": rooms, "source": {"site": plan.get("site"), "kind": plan.get("source") or "builder", "path": plan["path"]}})
        tried.append({"path": plan["path"], "ok": True, "why": why})
        log.info("plans3d: %s drew %s", regno, rel)
    return {"plans_3d": {"at": now, "items": items, "tried": tried}}


def public(plans: Optional[dict]) -> Optional[dict]:
    """What a project page shows: each drawing with its label, the plan's room sizes and where the plan came from."""
    items = (plans or {}).get("items") or []
    if not items:
        return None
    return {"items": [{"url": "/uploads/" + i["path"], "width": i.get("width"), "height": i.get("height"), "label": i.get("label"),
                       "title": i.get("title"), "rooms": i.get("rooms") or [],
                       "site": (i.get("source") or {}).get("site"), "kind": (i.get("source") or {}).get("kind")} for i in items]}
