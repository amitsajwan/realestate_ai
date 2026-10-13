"""The builder's brochure (docs/MARKETING_ARCHITECTURE_REVIEW.md §5.1, G6, G11): an agent uploads the PDF, we read its text
layer, and the listing gets a kit of fact candidates the agent confirms, fixes or drops on one screen.

    upload  -> the original kept under <uploads>/brochures/<listing>/<sha>.pdf (the same file is read once per listing),
               a small JPEG of every page for the confirm screen, the text of each page read with pdfium
    facts   -> brochure_parse finds candidates by rules; the free model may add more, each checked against the page text
    level   -> every candidate is a `builder_claim`, pending until the agent confirms it. Only confirmed claims reach the fact
               sheet (`readings`), where they never override MahaRERA or the listing, and posts say "as per the builder's
               brochure" whenever they use them (campaign.py)
    images  -> a page whose text says it is a floor plan, master plan, location map or an artist's impression
               (brochure_parse.image_kind) is also kept as a large JPEG (i<page>.jpg, IMAGE_LONG_SIDE px), pending until the
               agent says "use" or "don't use". A confirmed floor plan can carry a post (campaign.floor_plan); a confirmed
               render is only ever shown labelled "Artist's impression" and never in the walkthrough reel (S4).
               Most big-builder brochures are image-only pages; there the vision triage (brochure_triage: triage.json next
               to the pages) names each page, and its plans, maps and renders join the kit the same way, pending. Pages it
               calls the builder's other projects, company, stock lifestyle or text are never kit images, and an image-only
               brochure without triage gives no page to the posts' photos (pictures.brochure_photos; the kit's photo_note says so)
    MahaRERA-> a registration number in the brochure is looked up. MahaRERA not returning it means `unverified`: held for the
               agent, never posted as registered. No number and no record means `unknown`, and the agent is asked whether the
               project is registered or exempt (RERA Act section 3). A brochure printing several numbers (tower by tower)
               gets a `rera_nos` list too; the first number that is a member of a marketed project group
               (agentprojects.groups) is the one checked, and the registration names the group

Collection `brochures`: one document per (listing, brochure file); the listing's kit is the latest one uploaded. This module is
its only writer. The PDF is untrusted input: pdfium reads it without forms or scripts, under page, size and time limits."""
import asyncio
import hashlib
import json
import logging
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from app.core.rera import HINT as RERA_HINT

from . import brochure_parse as bp
from . import pictures, registration
from .facts import Reading

log = logging.getLogger(__name__)

COLLECTION = "brochures"
MAX_PAGES = 40
MAX_BYTES = 30 * 1024 * 1024
READ_BUDGET_S = 30.0     # reading every page (text and thumbnail); a brochure that takes longer is not read
LLM_BUDGET_S = 12.0      # the optional model pass; past it the rules' findings stand alone
LOOKUP_BUDGET_S = 25.0   # the MahaRERA check; past it the number stays unverified
THUMB_WIDTH = 360
THUMB_MAX_HEIGHT = 1000
IMAGE_LONG_SIDE = 1600   # a plan, map or render kept as an image: its long side in pixels
IMAGE_QUALITY = 85
SOURCE = "brochure"
ATTRIBUTION = "as per the builder's brochure"
STATES = ("pending", "confirmed", "dropped")
REG_STATUSES = ("verified", "unverified", "unknown", "registered_by_agent", "exempt")
ASK = ("Is this project registered on MahaRERA, or exempt? Under section 3 of the RERA Act, a project on more than 500 sq m of "
       "land or with more than 8 units must be registered before it is advertised; smaller projects and resale homes are exempt.")

_pdfium_lock = threading.Lock()  # pdfium is not thread-safe: one document at a time in this process


class BrochureError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail, self.status_code = detail, status_code


@dataclass
class PdfRead:
    pages: int = 0
    texts: Dict[int, str] = field(default_factory=dict)  # page number (from 1) -> cleaned text
    image_only: List[int] = field(default_factory=list)
    error: str = ""
    too_many: bool = False  # over the page limit: the upload is refused, not kept as a failed kit
    images: List[Tuple[int, str, List[str]]] = field(default_factory=list)  # (page, kind, configurations named on it)


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(s))[:64] or "x"


def read_pdf(data: bytes, thumbs: Optional[Path] = None, max_pages: int = MAX_PAGES, budget_s: float = READ_BUDGET_S,
             clock: Callable[[], float] = time.monotonic) -> PdfRead:
    """The text of every page and, with `thumbs`, a JPEG per page (p1.jpg, p2.jpg...) plus a large JPEG of each page that
    holds a plan, map or render (i3.jpg: `images`). Never raises: a file pdfium cannot open, a password, too many pages or
    too long a read come back as `error`."""
    import pypdfium2 as pdfium  # heavy optional library, loaded on first use

    out = PdfRead()
    start = clock()
    with _pdfium_lock:
        try:
            doc = pdfium.PdfDocument(data)
        except pdfium.PdfiumError as e:
            out.error = ("The PDF is password-protected. Upload a copy without a password."
                         if "password" in str(e).lower() else "This file could not be read as a PDF.")
            return out
        try:
            out.pages = len(doc)
            if out.pages == 0:
                out.error = "The PDF has no pages."
                return out
            if out.pages > max_pages:
                out.error = f"The brochure has {out.pages} pages; up to {max_pages} can be read. Upload the main pages only."
                out.too_many = True
                return out
            if thumbs is not None:
                thumbs.mkdir(parents=True, exist_ok=True)
            for i in range(out.pages):
                if clock() - start > budget_s:
                    out.error = "The brochure took too long to read. Try a smaller file."
                    return out
                page = doc[i]
                try:
                    tp = page.get_textpage()
                    text = bp.clean(tp.get_text_range())
                    tp.close()
                    if bp.image_only(text):
                        out.image_only.append(i + 1)
                    else:
                        out.texts[i + 1] = text
                    kind = bp.image_kind(text)
                    if thumbs is not None:
                        w, h = page.get_size()
                        scale = min(THUMB_WIDTH / max(w, 1.0), THUMB_MAX_HEIGHT / max(h, 1.0))
                        img = page.render(scale=scale, may_draw_forms=False).to_pil()
                        img.convert("RGB").save(thumbs / f"p{i + 1}.jpg", "JPEG", quality=70)
                        if kind:
                            big = page.render(scale=IMAGE_LONG_SIDE / max(w, h, 1.0), may_draw_forms=False).to_pil()
                            big.convert("RGB").save(thumbs / f"i{i + 1}.jpg", "JPEG", quality=IMAGE_QUALITY, optimize=True)
                    if kind:
                        out.images.append((i + 1, kind, bp.plan_configs(text) if kind == "floor_plan" else []))
                finally:
                    page.close()
        except pdfium.PdfiumError:
            out.error = "This file could not be read as a PDF."
        finally:
            doc.close()
    return out


def render_images(pdf: Any, thumbs: Path, pages: Sequence[int]) -> List[int]:
    """A large JPEG (i<page>.jpg) of each of `pages` (from 1) of `pdf` (bytes or a path), as read_pdf keeps for a plan, map
    or render; returns the pages drawn. Never raises (a page that fails is left out)."""
    import pypdfium2 as pdfium

    done: List[int] = []
    if not pages:
        return done
    thumbs.mkdir(parents=True, exist_ok=True)
    with _pdfium_lock:
        try:
            doc = pdfium.PdfDocument(pdf if isinstance(pdf, (bytes, bytearray)) else str(pdf))
        except Exception:
            return done
        try:
            for n in sorted(set(pages)):
                if not 1 <= n <= len(doc):
                    continue
                page = doc[n - 1]
                try:
                    w, h = page.get_size()
                    big = page.render(scale=IMAGE_LONG_SIDE / max(w, h, 1.0), may_draw_forms=False).to_pil()
                    big.convert("RGB").save(thumbs / f"i{n}.jpg", "JPEG", quality=IMAGE_QUALITY, optimize=True)
                    done.append(n)
                except Exception:
                    log.info("brochure: page %s could not be drawn", n, exc_info=True)
                finally:
                    page.close()
        finally:
            doc.close()
    return done


# ---- the vision triage (brochure_triage) ----------------------------------------------------------------------------------
def triage_sig(triage: Dict[int, dict]) -> str:
    if not triage:
        return ""
    blob = json.dumps(sorted((int(k), v) for k, v in triage.items()), sort_keys=True, default=str)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def merge_triage(images: Sequence[dict], triage: Dict[int, dict]) -> Tuple[List[dict], List[int]]:
    """The kit's images with the triage applied, and the pages whose large image must be drawn. The agent stays in control:
    a page triage calls a plan, map or render is added pending (or a pending one re-kinded); a pending image of a page it
    calls anything else is removed. An image the agent already decided keeps their decision, except one of the builder's
    other projects, which is never used (dropped)."""
    out: List[dict] = []
    seen = set()
    for im in images:
        im = dict(im)
        page = int(im.get("page") or 0)
        seen.add(page)
        e = triage.get(page)
        if e is None:
            out.append(im)
            continue
        use = pictures.page_use(e)
        pending = (im.get("state") or "pending") == "pending"
        if use in ("plan", "render"):
            kind = str(e.get("kind")) if use == "plan" else "render"
            if pending and kind != im.get("kind"):
                im.update(kind=kind, label=bp.ARTISTS_IMPRESSION if kind == "render" else "",
                          configs=list(im.get("configs") or []) if kind == "floor_plan" else [])
            out.append(im)
        elif pending:
            continue
        elif e.get("other_project"):
            out.append({**im, "state": "dropped", "by": "triage"})
        else:
            out.append(im)
    draw = []
    for n in sorted(triage):
        use = pictures.page_use(triage[n])
        if n in seen or use not in ("plan", "render"):
            continue
        out.append({**_image_doc(n, str(triage[n].get("kind")) if use == "plan" else "render", []), "by": "triage"})
        draw.append(n)
    out.sort(key=lambda im: int(im.get("page") or 0))
    return out, draw


def _drawn_only(images: List[dict], draw: Sequence[int], drawn: Sequence[int]) -> List[dict]:
    """Triage-added images whose page could not be drawn are left out (an image without a file is never offered)."""
    missing = set(draw) - set(drawn)
    return [im for im in images if not (im.get("by") == "triage" and im.get("state") == "pending" and im["page"] in missing)]


def photo_note(image_only: Sequence[int], pages: int, triage: Dict[int, dict]) -> str:
    """What the agent is told about the brochure's pages as photos on posts (pictures.brochure_photos), or ""."""
    return pictures.brochure_photos([], triage, len(image_only) / max(pages, 1))[1]


# ---- the kit ---------------------------------------------------------------------------------------------------------------
def _iso(dt: Any) -> Optional[str]:
    if not isinstance(dt, datetime):
        return dt
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.replace(microsecond=0).isoformat() + "Z"


def image_url(listing_id: str, image_id: str) -> str:
    return f"/api/v1/listings/{listing_id}/brochure/images/{image_id}.jpg"


def kit_out(doc: Optional[dict]) -> Optional[dict]:
    """The kit as the API returns it (the contract the confirm screen is built on)."""
    if not doc:
        return None
    reg = doc.get("registration") or {}
    images = [{"id": im["id"], "page": im["page"], "kind": im["kind"], "label": im.get("label") or None,
               "url": image_url(doc["listing_id"], im["id"]), "state": im.get("state") or "pending"}
              for im in doc.get("images") or []]
    out = {"id": doc["_id"], "listing_id": doc["listing_id"], "filename": doc.get("filename") or "",
           "pages": int(doc.get("pages") or 0), "image_only_pages": list(doc.get("image_only_pages") or []),
           "status": doc.get("status") or "failed", "read_at": _iso(doc.get("read_at")),
           "facts": [{"id": f["id"], "key": f["key"], "label": f["label"], "value": f["value"], "page": f["page"],
                      "quote": f["quote"], "level": "builder_claim", "state": f["state"], "edited": bool(f.get("edited"))}
                     for f in doc.get("facts") or []],
           "registration": {"status": reg.get("status") or "unknown", "rera_no": reg.get("rera_no") or None,
                            "note": reg.get("note") or ""},
           "images": images, "photo_note": doc.get("photo_note") or None}
    if doc.get("error"):
        out["error"] = doc["error"]
    return out


def _image_doc(page: int, kind: str, configs: List[str]) -> dict:
    return {"id": f"i{page}", "page": page, "kind": kind, "state": "pending", "configs": list(configs),
            "label": bp.ARTISTS_IMPRESSION if kind == "render" else ""}


def usable_images(kit: Optional[dict], uploads_dir: Any) -> List[dict]:
    """The kit's images the agent said to use, whose file is on disk: [{id, page, kind, label, configs, path}]. A render's
    label is always "Artist's impression"."""
    if not kit or kit.get("status") != "done":
        return []
    folder = Path(uploads_dir) / "brochures" / _safe(kit["listing_id"]) / kit["sha256"]
    out = []
    for im in kit.get("images") or []:
        p = folder / f"{_safe(im['id'])}.jpg"
        if im.get("state") == "confirmed" and im.get("kind") in bp.IMAGE_KINDS and p.is_file():
            label = bp.ARTISTS_IMPRESSION if im["kind"] == "render" else (im.get("label") or "")
            out.append({"id": im["id"], "page": im["page"], "kind": im["kind"], "label": label,
                        "configs": list(im.get("configs") or []), "path": str(p)})
    return out


def _fact_doc(i: int, c: bp.Candidate) -> dict:
    return {"id": f"f{i}", "key": c.key, "label": c.label, "value": c.value, "page": c.page, "quote": c.quote,
            "level": "builder_claim", "state": "pending", "edited": False, "config": c.config, "by": c.by}


def _value_ok(key: str, value: Any) -> Any:
    """The agent's edit in the shape its key needs, or BrochureError."""
    if key in bp.LIST_KEYS:
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise BrochureError("Give a list of short texts.", 422)
        vals = [v.strip() for v in value if v.strip()]
        if not vals or len(vals) > bp.LIST_MAX or any(len(v) > bp.ITEM_MAX for v in vals):
            raise BrochureError(f"Give 1 to {bp.LIST_MAX} items, each under {bp.ITEM_MAX} characters.", 422)
        if key == "rera_nos":
            if not all(bp.rera_no(v) for v in vals):
                raise BrochureError(RERA_HINT, 422)
            vals = list(dict.fromkeys(bp.rera_no(v) for v in vals))
        return vals
    if key in bp.COUNT_KEYS:
        n = value if isinstance(value, int) and not isinstance(value, bool) else (
            int(value) if isinstance(value, str) and value.strip().isdigit() else None)
        if n is None or not 0 < n < 100000:
            raise BrochureError("Give a whole number.", 422)
        return n
    if not isinstance(value, str) or not value.strip() or len(value) > 300:
        raise BrochureError("Give a short text.", 422)
    v = value.strip()
    if key == "rera_no":
        v = bp.rera_no(v)
        if not v:
            raise BrochureError(RERA_HINT, 422)
    if key == "carpet_area" and bp.area_sqft(v) is None:
        raise BrochureError("Give the area with its unit, such as 650 sq ft.", 422)
    return v


# ---- the registration check ------------------------------------------------------------------------------------------------
async def _group_of(groups: Any, numbers: Sequence[str]) -> Tuple[Optional[dict], str]:
    """The marketed project (agentprojects.groups) any of the brochure's numbers belongs to, and the first member number
    found: (group, regno), or (None, "")."""
    if groups is None:
        return None, ""
    for no in numbers:
        try:
            g = await groups.resolve(no, "")
        except Exception as e:
            log.info("brochure: project group lookup failed (%s)", type(e).__name__)
            return None, ""
        if g:
            return g, no
    return None, ""


async def check_registration(clients: Any, rera: str, name: str = "", now: Optional[datetime] = None,
                             others: Sequence[str] = ()) -> dict:
    """{status, rera_no, note, group?}. `clients` needs get_text, fetch_general and optionally register and groups
    (gather.Clients; tests fake it). Only MahaRERA (or our register of it) returning this very number makes it `verified`.
    `others`: the brochure's other MahaRERA numbers (a project registered tower by tower). When any of them is a member of a
    marketed project group (agentprojects.groups), that member is the number checked and the kit names the group."""
    numbers = list(dict.fromkeys(n for n in [bp.rera_no(rera or "")] + [bp.rera_no(str(o)) for o in others or ()] if n))
    if not numbers:
        return {"status": "unknown", "rera_no": None, "note": "No MahaRERA number was found in the brochure. " + ASK}
    rera = numbers[0]
    group, member = await _group_of(getattr(clients, "groups", None), numbers) if clients is not None else (None, "")
    if group:
        rera = member
    held = f"The brochure shows {rera}, but MahaRERA did not return it"
    if clients is None:
        return {"status": "unverified", "rera_no": rera, "note": f"{held} (not checked). It will not be posted as registered "
                                                                  "until it is confirmed."}
    out = await _check_one(clients, rera, name, now, held)
    if group:
        regs = [r.get("regno") for r in group.get("registrations") or [] if r.get("regno")]
        out["group"] = {"name": group.get("name") or "", "primary": group.get("primary") or "", "registrations": regs,
                        "slug": group.get("slug")}
        out["note"] += (f" {rera} is one of the {len(regs)} MahaRERA registrations {group.get('name') or 'this project'} "
                        "is sold under.")
    return out


async def _check_one(clients: Any, rera: str, name: str, now: Optional[datetime], held: str) -> dict:
    try:
        match, _ = await asyncio.wait_for(registration.lookup(clients.get_text, clients.fetch_general, name, rera, None, now,
                                                              getattr(clients, "register", None),
                                                              getattr(clients, "groups", None)), LOOKUP_BUDGET_S)
    except Exception:  # timeout or a site failure: not an answer either way
        log.info("brochure: MahaRERA check of %s failed", rera, exc_info=True)
        match = None
    if match is not None and match.project is not None and match.project.regno.upper() == rera:
        return {"status": "verified", "rera_no": rera, "note": f"MahaRERA lists {rera} as {match.project.name}."}
    why = f" ({match.how})" if match is not None and match.how else ""
    return {"status": "unverified", "rera_no": rera,
            "note": f"{held}{why}. It will not be posted as registered: check the number with the builder, then confirm."}


# ---- into the fact sheet -----------------------------------------------------------------------------------------------------
def confirmed(kit: Optional[dict]) -> List[dict]:
    return [f for f in (kit or {}).get("facts") or [] if f.get("state") == "confirmed"] if (kit or {}).get("status") == "done" else []


def lookup_inputs(kit: Optional[dict]) -> Tuple[str, str]:
    """(project name, MahaRERA number) the kit adds for the MahaRERA lookup, from confirmed facts and the agent's answer."""
    reg = (kit or {}).get("registration") or {}
    facts = {f["key"]: f["value"] for f in confirmed(kit) if f["key"] in ("project_name", "rera_no")}
    rera = ""
    if reg.get("status") in ("verified", "registered_by_agent") and reg.get("rera_no"):
        rera = reg["rera_no"]
    rera = rera or bp.rera_no(str(facts.get("rera_no") or ""))
    if not rera:   # only the list of a project's registrations was confirmed: its first
        rera = next((bp.rera_no(str(v)) for f in confirmed(kit) if f["key"] == "rera_nos" for v in f["value"] or []
                     if bp.rera_no(str(v))), "")
    return str(facts.get("project_name") or ""), rera


def readings(kit: Optional[dict], now: datetime, official: Optional[Dict[str, Any]] = None,
             listing: Optional[Dict[str, Any]] = None) -> List[Reading]:
    """Confirmed brochure facts as readings with source "brochure". Their own keys ("brochure.amenities") become builder claims;
    a value MahaRERA or the listing also states (RERA number, possession, units, carpet area, project, builder) is read on the
    same key, so a disagreement shows up as one (facts.decide). `official`: MahaRERA's values by key; `listing`: the listing."""
    official, listing = official or {}, listing or {}
    url = f"brochure:{(kit or {}).get('sha256', '')[:12]}"
    out: List[Reading] = []
    lists: Dict[str, List[str]] = {}
    carpets: List[str] = []
    try:   # a listing's bhk is a number; a stray "2BHK" or "Studio" only loses the carpet comparison, never the run
        listing_bhk = f"{float(listing['bhk']):g} BHK" if listing.get("bhk") else ""
    except (TypeError, ValueError):
        listing_bhk = ""

    def r(key: str, value: Any, page: int):
        out.append(Reading(key, value, SOURCE, f"{url}#page={page}", now))

    for f in confirmed(kit):
        k, v, p = f["key"], f["value"], f["page"]
        if k in ("project_name", "promoter"):
            r(k, v, p)
        elif k == "rera_no":
            if bp.rera_no(str(v)):
                r("rera_no", bp.rera_no(str(v)), p)
        elif k in ("address", "land_area"):
            r(f"brochure.{k}", v, p)
        elif k in bp.LIST_KEYS:
            lists.setdefault(k, [])
            lists[k] += [x for x in v if x not in lists[k]]
        elif k == "possession":
            r("brochure.possession", v, p)
            now_iso = official.get("possession_now")
            if now_iso:  # the same month reads as MahaRERA's own date; another month is a disagreement
                r("possession_now", now_iso if bp.same_possession(str(v), now_iso) else str(v), p)
        elif k in ("towers", "floors"):
            r(f"brochure.{k}", bp.count_of(v), p)
        elif k == "units":
            if official.get("units_total") is not None:
                r("units_total", bp.count_of(v), p)
            r("brochure.units", bp.count_of(v), p)
        elif k == "carpet_area":
            config = f.get("config") or ""
            carpets.append(f"{config}: {v} carpet" if config else f"{v} carpet")
            if listing.get("carpet_sqft") and config and config == listing_bhk:
                area = bp.area_sqft(v)
                theirs = int(listing["carpet_sqft"])
                if area is not None:
                    r("carpet_sqft", theirs if area == theirs else area, p)
    for k, vals in lists.items():
        page = next(f["page"] for f in confirmed(kit) if f["key"] == k)
        r(f"brochure.{k}", vals, page)
    if carpets:
        page = next(f["page"] for f in confirmed(kit) if f["key"] == "carpet_area")
        r("brochure.carpet_area", carpets, page)
    return out


# ---- page labels (brochure_triage), after the upload ----------------------------------------------------------------------
_label_tasks: set = set()   # running label tasks (a task nobody holds may be collected before it ends)


async def label_pages(folder: Path, pages: int) -> None:
    """brochure_triage on the kit's page thumbnails (p1.jpg...), saved as triage.json beside them. Never raises."""
    from . import brochure_triage
    try:
        thumbs = [str(folder / f"p{n}.jpg") for n in range(1, pages + 1)]
        if pages and all(Path(p).is_file() for p in thumbs) and not brochure_triage.load(folder):
            labels = await brochure_triage.triage(thumbs)
            if labels:
                brochure_triage.save(folder, labels)
    except Exception:
        log.info("brochure: page labels failed", exc_info=True)


def label_pages_later(folder: Path, pages: int) -> None:
    """Label the pages in the background: the upload answers at once, the kit's next read finds triage.json."""
    try:
        task = asyncio.get_running_loop().create_task(label_pages(folder, pages))
    except RuntimeError:
        return
    _label_tasks.add(task)
    task.add_done_callback(_label_tasks.discard)


# ---- the service ---------------------------------------------------------------------------------------------------------
class Brochures:
    def __init__(self, db, uploads_dir, clients_factory: Optional[Callable[[], Any]] = None,
                 llm_factory: Optional[Callable[[], Any]] = None, now: Callable[[], datetime] = datetime.utcnow,
                 label_pages: bool = False):
        """`clients_factory()` gives what the MahaRERA check needs (gather.Clients); `llm_factory()` the optional free model
        (None: rules only); `label_pages`: after an upload, label every page with the vision model in the background
        (brochure_triage; triage.json in the kit's folder)."""
        self.label_pages = label_pages
        self.col = db.get_collection(COLLECTION)
        self.listings = db.get_collection("listings")
        self.uploads_dir = Path(uploads_dir)
        self.clients_factory, self.llm_factory, self.now = clients_factory, llm_factory, now

    def _dir(self, listing_id: str) -> Path:
        return self.uploads_dir / "brochures" / _safe(listing_id)

    async def _listing(self, agent_id: str, listing_id: str) -> dict:
        doc = await self.listings.find_one({"_id": listing_id, "agent_id": agent_id})
        if not doc:
            raise BrochureError("Listing not found", 404)
        return doc

    async def current(self, listing_id: str) -> Optional[dict]:
        """The listing's kit: the brochure read last (for the fact sheet; no owner check). A brochure that could not be read is
        kept for the record but never replaces the kit before it (its confirmed facts and registration answer stay in use)."""
        docs = await self.col.find({"listing_id": str(listing_id), "status": "done"}).sort("uploaded_at", -1).limit(1).to_list(1)
        return await self._triaged(docs[0]) if docs else None

    async def _triaged(self, kit: dict) -> dict:
        """The kit with a vision triage that arrived (or changed) after it was read applied once (merge_triage): new plans,
        maps and renders pending for the agent, photo_note brought up to date. Never raises: the kit as it was on any failure."""
        try:
            folder = self._dir(kit["listing_id"]) / kit["sha256"]
            triage = await asyncio.to_thread(pictures.load_triage, folder)
            if not triage or triage_sig(triage) == kit.get("triage_sig"):
                return kit
            images, draw = merge_triage(kit.get("images") or [], triage)
            pdf = self._dir(kit["listing_id"]) / f"{kit['sha256']}.pdf"
            drawn = await asyncio.to_thread(render_images, pdf, folder, draw) if draw and pdf.is_file() else []
            update = {"images": _drawn_only(images, draw, drawn), "triage_sig": triage_sig(triage),
                      "photo_note": photo_note(kit.get("image_only_pages") or [], int(kit.get("pages") or 0), triage)}
            await self.col.update_one({"_id": kit["_id"]}, {"$set": update})
            return {**kit, **update}
        except Exception:
            log.warning("brochure: the page triage of %s could not be applied", kit.get("_id"), exc_info=True)
            return kit

    async def get(self, agent_id: str, listing_id: str) -> dict:
        await self._listing(agent_id, listing_id)
        kit = await self.current(listing_id)
        if not kit:
            raise BrochureError("No brochure for this listing yet.", 404)
        return kit

    async def _model_facts(self, texts: Dict[int, str]) -> Tuple[List[bp.Candidate], bool]:
        llm = self.llm_factory() if self.llm_factory else None
        if llm is None or not texts:
            return [], False
        system, user = bp.llm_prompt(sorted(texts.items()))
        try:
            data = await asyncio.wait_for(llm.json(system, user), LLM_BUDGET_S)
        except Exception:
            log.info("brochure: the model pass failed; rules only", exc_info=True)
            return [], False
        return bp.verify(data, texts), data is not None

    async def upload(self, agent_id: str, listing_id: str, filename: str, data: bytes) -> dict:
        """Read the brochure into a kit (or return the kit already made from this very file for this listing)."""
        listing = await self._listing(agent_id, listing_id)
        if len(data) > MAX_BYTES:
            raise BrochureError(f"The brochure is over {MAX_BYTES // (1024 * 1024)} MB. Upload a smaller PDF.", 413)
        if not data.lstrip()[:5].startswith(b"%PDF-"):
            raise BrochureError("Upload the brochure as a PDF file.", 415)
        sha = hashlib.sha256(data).hexdigest()
        now = self.now()
        same = await self.col.find_one({"listing_id": listing_id, "sha256": sha, "status": "done"})
        if same:
            await self.col.update_one({"_id": same["_id"]}, {"$set": {"uploaded_at": now, "filename": filename or same.get("filename")}})
            return {**same, "uploaded_at": now, "filename": filename or same.get("filename")}
        folder = self._dir(listing_id)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{sha}.pdf").write_bytes(data)
        read = await asyncio.to_thread(read_pdf, data, folder / sha)
        if read.too_many:
            (folder / f"{sha}.pdf").unlink(missing_ok=True)
            raise BrochureError(read.error, 413)
        doc: Dict[str, Any] = {"_id": uuid.uuid4().hex, "listing_id": listing_id, "agent_id": agent_id, "sha256": sha,
                               "filename": (filename or "brochure.pdf")[:200], "pages": read.pages,
                               "image_only_pages": read.image_only, "uploaded_at": now, "read_at": now, "facts": [],
                               "page_types": {}, "used_llm": False, "images": []}
        if read.error:
            doc.update(status="failed", error=read.error,
                       registration={"status": "unknown", "rera_no": None, "note": ASK})
            await self.col.insert_one(doc)
            return doc
        texts = read.texts
        doc["page_types"] = {str(n): bp.page_type(t, n) for n, t in texts.items()}
        doc["images"] = [_image_doc(n, kind, configs) for n, kind, configs in read.images]
        triage = await asyncio.to_thread(pictures.load_triage, folder / sha)
        if triage:
            doc["images"], draw = merge_triage(doc["images"], triage)
            drawn = await asyncio.to_thread(render_images, data, folder / sha, draw)
            doc["images"] = _drawn_only(doc["images"], draw, drawn)
            doc["triage_sig"] = triage_sig(triage)
        rules = bp.extract(sorted(texts.items()))
        model, used = await self._model_facts(texts)
        cands = bp.merge(rules, model)
        doc["facts"] = [_fact_doc(i + 1, c) for i, c in enumerate(cands)]
        doc["used_llm"] = used
        rera = next((c.value for c in cands if c.key == "rera_no"), "") or bp.rera_no(str(listing.get("rera_no") or ""))
        name = next((c.value for c in cands if c.key == "project_name"), "") or (listing.get("project_name") or "")
        clients = self.clients_factory() if self.clients_factory else None
        others = [v for c in cands if c.key == "rera_nos" for v in c.value or []]
        doc["registration"] = await check_registration(clients, rera, name, now, others)
        if read.image_only:
            doc["notes"] = [f"Pages {', '.join(map(str, read.image_only))} have no text layer (images only); they are not "
                            "read yet."]
        doc["photo_note"] = photo_note(read.image_only, read.pages, triage)
        doc.update(status="done", error=None)
        await self.col.insert_one(doc)
        if self.label_pages:
            label_pages_later(folder / sha, read.pages)
        return doc

    async def set_fact(self, agent_id: str, listing_id: str, fact_id: str, state: str, value: Any = None,
                       has_value: bool = False) -> dict:
        """Confirm, drop or reopen one fact; a new value keeps the page and quote it came from and marks it edited."""
        if state not in STATES:
            raise BrochureError("state is confirmed, dropped or pending.", 422)
        kit = await self.get(agent_id, listing_id)
        facts = list(kit.get("facts") or [])
        idx = next((i for i, f in enumerate(facts) if f["id"] == fact_id), None)
        if idx is None:
            raise BrochureError("No such fact in this brochure.", 404)
        f = dict(facts[idx])
        f["state"] = state
        changed_rera = False
        if has_value:
            v = _value_ok(f["key"], value)
            if v != f["value"]:
                f.setdefault("original", f["value"])
                f.update(value=v, edited=True)
                changed_rera = f["key"] == "rera_no"
        f["decided_at"] = self.now()
        facts[idx] = f
        # one array slot, not the whole array: two taps in flight (Confirm f1, Confirm f2) must not undo each other
        update: Dict[str, Any] = {f"facts.{idx}": f}
        reg = kit.get("registration") or {}
        agents_word = reg.get("status") in ("exempt", "registered_by_agent")
        if changed_rera and not agents_word:
            clients = self.clients_factory() if self.clients_factory else None
            update["registration"] = await check_registration(clients, f["value"], self._name(facts), self.now())
        elif (f["key"] == "rera_no" and state == "dropped" and not agents_word and reg.get("rera_no")
              and bp.rera_no(str(reg.get("rera_no"))) == bp.rera_no(str(f["value"]))):
            # the agent says the brochure's number is wrong: it no longer stands as the project's registration
            update["registration"] = {"status": "unknown", "rera_no": None, "note": ASK}
        await self.col.update_one({"_id": kit["_id"]}, {"$set": update})
        return await self.col.find_one({"_id": kit["_id"]}) or kit

    @staticmethod
    def _name(facts: Sequence[dict]) -> str:
        return next((str(f["value"]) for f in facts if f["key"] == "project_name" and f["state"] != "dropped"), "")

    async def answer_registration(self, agent_id: str, listing_id: str, status: str, rera_no: Optional[str] = None) -> dict:
        """The agent's answer to "registered, or exempt?", kept on the kit. A number they give is looked up; MahaRERA returning
        it makes it `verified`, otherwise it is kept as the agent's word (`registered_by_agent`) and still not posted as
        MahaRERA-checked."""
        kit = await self.get(agent_id, listing_id)
        now = self.now()
        answer = {"status": status, "rera_no": None, "by": agent_id, "at": now}
        if status == "exempt":
            reg = {"status": "exempt", "rera_no": None,
                   "note": "The agent says this project is exempt from MahaRERA registration (RERA Act section 3: up to "
                           "500 sq m of land and up to 8 units, or a resale home). Posts carry no registration line."}
        elif status == "registered":
            rera = ""
            if rera_no:
                rera = bp.rera_no(rera_no)
                if not rera:
                    raise BrochureError(RERA_HINT, 422)
            answer["rera_no"] = rera or None
            clients = self.clients_factory() if self.clients_factory else None
            reg = await check_registration(clients, rera, self._name(kit.get("facts") or []), now) if rera else {}
            if reg.get("status") != "verified":
                reg = {"status": "registered_by_agent", "rera_no": rera or None,
                       "note": ("The agent says the project is registered as " + rera + ", but MahaRERA did not return it. "
                                "It is not shown as MahaRERA-checked." if rera else
                                "The agent says the project is registered. Add its MahaRERA number: ads must show it.")}
        else:
            raise BrochureError("status is registered or exempt.", 422)
        reg["answer"] = answer
        await self.col.update_one({"_id": kit["_id"]}, {"$set": {"registration": reg}})
        return {**kit, "registration": reg}

    async def set_image(self, agent_id: str, listing_id: str, image_id: str, state: str) -> dict:
        """Use (confirmed), don't use (dropped) or undecided (pending) for one image from the brochure."""
        if state not in STATES:
            raise BrochureError("state is confirmed, dropped or pending.", 422)
        kit = await self.get(agent_id, listing_id)
        images = [dict(im) for im in kit.get("images") or []]
        im = next((x for x in images if x["id"] == image_id), None)
        if im is None:
            raise BrochureError("No such image in this brochure.", 404)
        im.update(state=state, decided_at=self.now())
        idx = images.index(im)
        await self.col.update_one({"_id": kit["_id"]}, {"$set": {f"images.{idx}": im}})   # one slot: taps in flight don't collide
        return await self.col.find_one({"_id": kit["_id"]}) or {**kit, "images": images}

    async def image_file(self, agent_id: str, listing_id: str, image_id: str) -> Path:
        kit = await self.get(agent_id, listing_id)
        if not any(im["id"] == image_id for im in kit.get("images") or []):
            raise BrochureError("No such image.", 404)
        p = self._dir(listing_id) / kit["sha256"] / f"{_safe(image_id)}.jpg"
        if not p.is_file():
            raise BrochureError("No such image.", 404)
        return p

    async def page_image(self, agent_id: str, listing_id: str, n: int) -> Path:
        kit = await self.get(agent_id, listing_id)
        if not 1 <= n <= int(kit.get("pages") or 0):
            raise BrochureError("No such page.", 404)
        p = self._dir(listing_id) / kit["sha256"] / f"p{n}.jpg"
        if not p.is_file():
            raise BrochureError("No such page.", 404)
        return p


def default_brochures() -> Brochures:
    from app.core.config import settings
    from app.core.database import get_database
    from app.modules.agentprojects.groups import Groups
    from app.modules.newsroom.store import Store
    from app.platform.llm import default_llm

    from .gather import Clients
    db = get_database()
    return Brochures(db, Path(settings.upload_directory),
                     clients_factory=lambda: Clients(timeout=15.0, register=Store(db), groups=Groups(db)),
                     llm_factory=default_llm, label_pages=True)
