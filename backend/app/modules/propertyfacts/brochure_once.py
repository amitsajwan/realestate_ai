"""One brochure file is understood once, ever (owner, 2026-11-07; docs/plan/brochure-reading.md).

The file's sha256 is the key. Whoever attaches it, on whichever listing, the stored reading is used and no model is called. A
file that could not be read stays "could not read": nothing tries it again by itself, and a better reader does not re-read
anything unless the owner says so. Marketing runs, chat and the page writer never open the PDF.

    sweep     a brochure attached to a listing gets a job in `brochure_jobs` (the dispatch loop asks every 20 s)
    run_once  the Cloud Run renderer takes one job: pages, Gemini labels, the useful pages read, stored in `brochure_reads`
    adopt     Brochures.adopt turns the reading into the listing's kit, so the confirm actions, the posts' images and the
              project page's plans work as they always did

The pilot on two real PDFs set the rules here. Gemini reads at low thinking: the default took 74 s a page and cost five times
as much with no better reading. A MahaRERA number read off a whole page was wrong by one character, so it is cropped, read
twice and the reads must agree; a text layer is read by code, never by a model. Only Gemini reads plans: free vision models made
up room sizes. An area table is checked by code (sq m to sq ft). A plan with no printed carpet area or a joined label
("4 BHK, F-08+09") is a picture only, never a home type the project sells. This module is the only writer of both collections.
"""
import asyncio
import hashlib
import io
import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence

from app.modules.areastats import budget
from app.platform import gemini

from . import brochure as br
from . import brochure_parse as bp
from . import brochure_triage as triage
from . import files

log = logging.getLogger(__name__)

VERSION = 1
READS, JOBS = "brochure_reads", "brochure_jobs"
CAP_INR = 10.0              # owner, 2026-11-07: one brochure stops here
MAX_TRIES = 3
WAIT = timedelta(hours=6)   # no credit or a full day's budget: not a try, it waits
READ_S = 300.0              # pages and thumbnails; the upload's own 30 s is for a request, this is a background job
PAGE_S = 150.0              # one model call: a slower page is skipped, not a crash
THINKING = "low"
NUMBER_SIDE = 3000          # a page's long side when its MahaRERA number is read
TABLE_SIDE = 2600
FACT_SIDE = 1600
FACT_PAGES = 6
NUMBER_PAGES = 3
SQM_SQFT, SQM_TOLERANCE = 10.7639, 0.015
FACT_KINDS = ("legal", "cover", "amenities", "specs", "text", "master_plan", "location_map")
NO_TRY = re.compile(r"HTTP (401|402|403|429)\b")
NOT_A_NAME = re.compile(r"area statement|floor plan|brochure|disclaimer", re.I)

Ask = Callable[[List[bytes], str], Awaitable[Any]]

BOX = ("Find the MahaRERA registration number printed on this page. Answer JSON {\"box\": [ymin, xmin, ymax, xmax]} from 0 to 1000 "
       "around the number with its label, or {\"box\": null} when no number is printed.")
NUMBER = ("Read the MahaRERA registration number on this picture character by character, exactly as printed. They look like "
          "P52100012345, or two letters then 13 digits like PR1260001234567. JSON {\"number\": null or the number}. Never guess.")
HEADINGS = ("Read the headings of this floor plan page. JSON {\"plans\": [{\"title\": as printed, \"carpet_area\": as printed or null, "
            "\"unit_label\": the flat label such as F-08 or null}]}. Never guess; null when it is not printed.")
AREAS = ("Read the area statement table on this page exactly. JSON {\"rows\": [{\"units\": as printed, \"type\": as printed, \"sqm\": "
         "the number or null, \"sqft\": the number or null}]}, or {\"rows\": []} when there is no such table. Never guess.")
FACTS = ("This is a page of an Indian real-estate project brochure. Read only what is printed. JSON {\"project_name\": null, "
         "\"builder\": null, \"configurations\": [], \"possession\": null, \"amenities\": [], \"specifications\": [], \"address\": "
         "null, \"towers\": null, \"floors\": null, \"units\": null, \"land_area\": null, \"location_claims\": []}. Never guess or "
         "work anything out; null or [] when it is not printed.")


class OverCap(Exception):
    """The brochure reached CAP_INR."""


class NoCredit(Exception):
    """The model refused for money or quota: not the file's fault, so it is not a try."""


class ReadFailed(Exception):
    """This try could not read the file."""


@dataclass
class Cost:
    tokens_in: int = 0
    tokens_out: int = 0
    calls: int = 0
    inr: float = 0.0
    usd_inr: float = field(default_factory=lambda: budget.load().usd_inr)

    def add(self, usage: Dict[str, Any]) -> None:
        self.calls += 1
        self.tokens_in += int(usage.get("tokens_in") or 0)
        self.tokens_out += int(usage.get("tokens_out") or 0)
        self.inr += budget.cost_inr(str(usage.get("model") or ""), int(usage.get("tokens_in") or 0),
                                    int(usage.get("tokens_out") or 0), self.usd_inr)


def asker(cost: Cost) -> Ask:
    """One model call for this read, counted. A page that fails gives None; running out of credit stops the read."""
    async def ask(images: List[bytes], prompt: str) -> Any:
        if cost.inr >= CAP_INR:
            raise OverCap()
        try:
            out, usage = await gemini.read_counted(images, prompt, timeout=PAGE_S, thinking=THINKING)
        except gemini.GeminiError as e:
            if NO_TRY.search(str(e)):
                raise NoCredit(str(e))
            log.info("brochure read: a page failed (%s)", str(e)[:120])
            return None
        cost.add(usage)
        return out
    return ask


def page_jpeg(pdf: bytes, n: int, long_side: int, box: Optional[Sequence[float]] = None) -> bytes:
    """Page `n` (from 1) as a JPEG, or the part of it inside `box` ([ymin, xmin, ymax, xmax], 0 to 1000) with a margin."""
    import pypdfium2 as pdfium  # heavy optional library, loaded on first use

    with br._pdfium_lock:
        doc = pdfium.PdfDocument(pdf)
        try:
            page = doc[n - 1]
            w, h = page.get_size()
            im = page.render(scale=long_side / max(w, h, 1.0), may_draw_forms=False).to_pil().convert("RGB")
            page.close()
        finally:
            doc.close()
    if box:
        y0, x0, y1, x1 = box
        W, H = im.size
        pad = 25
        im = im.crop((max(0, int((x0 - pad) * W / 1000)), max(0, int((y0 - pad) * H / 1000)),
                      min(W, int((x1 + pad) * W / 1000)), min(H, int((y1 + pad) * H / 1000))))
    out = io.BytesIO()
    im.save(out, "JPEG", quality=90)
    return out.getvalue()


def _box(answer: Any) -> Optional[List[float]]:
    box = (answer.get("box") or answer.get("box_2d")) if isinstance(answer, dict) else None   # Gemini uses both names
    if not isinstance(box, list) or len(box) != 4 or not all(isinstance(v, (int, float)) for v in box):
        return None
    return box if box[0] < box[2] and box[1] < box[3] else None


async def read_number(pdf: bytes, page: int, ask: Ask) -> str:
    """The MahaRERA number printed on a picture page, or "". Two reads of a close crop must agree: one wrong character can put
    another project's plans on a page, so a near match is no match."""
    whole = await asyncio.to_thread(page_jpeg, pdf, page, 1600)
    box = _box(await ask([whole], BOX))
    if not box:
        return ""
    crop = await asyncio.to_thread(page_jpeg, pdf, page, NUMBER_SIDE, box)
    reads = []
    for _ in range(2):
        answer = await ask([crop], NUMBER)
        reads.append(bp.rera_no(str(answer.get("number") or "")) if isinstance(answer, dict) else "")
    return reads[0] if reads[0] and reads[0] == reads[1] else ""


def checked_rows(answer: Any) -> List[dict]:
    """The rows of an area table whose sq m and sq ft agree: code checks the model here."""
    rows = answer.get("rows") if isinstance(answer, dict) else None
    out = []
    for r in rows if isinstance(rows, list) else []:
        try:
            sqm, sqft = float(str(r.get("sqm")).replace(",", "")), float(str(r.get("sqft")).replace(",", ""))
        except (AttributeError, TypeError, ValueError):
            continue
        if sqft > 0 and abs(sqm * SQM_SQFT - sqft) / sqft <= SQM_TOLERANCE:
            out.append({"units": str(r.get("units") or "")[:200], "type": str(r.get("type") or "")[:40], "sqm": sqm, "sqft": sqft})
    return out


def carpet_facts(rows: List[dict], headings: List[dict], page_of_rows: Dict[str, int]) -> List[bp.Candidate]:
    """One carpet area per home type: from the checked table when there is one, else from the plan's own printed heading. A
    plan with no printed area or a joined label says nothing here."""
    spans: Dict[str, List[float]] = {}
    for r in rows:
        config = next(iter(bp.plan_configs(r["type"])), "")
        spans.setdefault(config, []).append(r["sqft"])
    out = []
    for config, sizes in spans.items():
        lo, hi = int(round(min(sizes))), int(round(max(sizes)))
        value = f"{lo} sq ft" if lo == hi else f"{lo}-{hi} sq ft"
        out.append(bp.Candidate("carpet_area", value, page_of_rows.get(config, 1), f"Area statement: {value}", config=config, by="vision"))
    for h in headings:
        config = next(iter(bp.plan_configs(str(h.get("title") or ""))), "")
        area = " ".join(str(h.get("carpet_area") or "").split())
        if config and area and not joined(h) and config not in spans:
            out.append(bp.Candidate("carpet_area", area, int(h.get("page") or 1), f"{h.get('title')}: {area}", config=config, by="vision"))
    return out


def joined(heading: dict) -> bool:
    """Two flats drawn as one ("F-08+09"), or a plan with no printed area: shown as a picture, never counted as a home type."""
    return "+" in str(heading.get("unit_label") or "") or not str(heading.get("carpet_area") or "").strip()


def _item(x: Any) -> str:
    """A list item as text: the model sometimes groups them ({"category": "WINDOWS", "details": ["3 Track Sliding Window."]})."""
    if isinstance(x, dict):
        return ": ".join(p for p in (_item(v) for v in x.values()) if p)
    if isinstance(x, list):
        return ", ".join(p for p in (_item(v) for v in x) if p)
    return " ".join(str(x if x is not None else "").split())


def best_of_each(facts: List[bp.Candidate]) -> List[bp.Candidate]:
    """One value for a key that has one answer: the fullest of what the pages say ("KP" on the cover, "Kanifnath Realtors" in the
    small print). An address must read like one ("@NIBM ANNEXE" is a slogan). Carpet areas, one per home type, stay."""
    single: Dict[str, bp.Candidate] = {}
    out: List[bp.Candidate] = []
    for c in facts:
        if c.key == "address" and len(str(c.value).split()) < 3:
            continue
        if c.key == "project_name" and NOT_A_NAME.search(str(c.value)):
            continue
        if c.key in ("project_name", "promoter", "address", "possession", "land_area"):
            held = single.get(c.key)
            if held is None or len(str(c.value)) > len(str(held.value)):
                single[c.key] = c
        else:
            out.append(c)
    return list(single.values()) + out


def page_facts(answer: Any, page: int) -> List[bp.Candidate]:
    if not isinstance(answer, dict):
        return []
    out = []
    for key, field_name in (("project_name", "project_name"), ("promoter", "builder"), ("possession", "possession"),
                            ("address", "address"), ("land_area", "land_area")):
        v = " ".join(str(answer.get(field_name) or "").split())
        if v:
            out.append(bp.Candidate(key, v[:300], page, v[:200], by="vision"))
    for key in ("towers", "floors", "units"):
        v = answer.get(key)
        if v not in (None, ""):
            out.append(bp.Candidate(key, str(v)[:40], page, str(v)[:200], by="vision"))
    for key in ("configurations", "amenities", "specifications"):
        items = [t[:bp.ITEM_MAX] for t in (_item(x) for x in answer.get(key) or []) if t]
        if items:
            out.append(bp.Candidate(key, items[:bp.LIST_MAX], page, ", ".join(items)[:200], by="vision"))
    return out


async def read_file(data: bytes, folder: Path, ask: Ask) -> Dict[str, Any]:
    """Everything one brochure says, with its page pictures in `folder`. Raises ReadFailed when the file gives nothing."""
    read = await asyncio.to_thread(lambda: br.read_pdf(data, folder, budget_s=READ_S))
    if read.error:
        raise ReadFailed(read.error)
    jpgs = [str(folder / f"p{n}.jpg") for n in range(1, read.pages + 1)]
    labels: Dict[int, dict] = {}
    for nums in triage.batches(read.pages):
        sheet = await asyncio.to_thread(triage.contact_sheet, [jpgs[n - 1] for n in nums], nums)
        if sheet:
            labels.update(triage.clean(await ask([sheet], f"{triage.SYSTEM} {triage.PROMPT.format(first=nums[0], last=nums[-1])}"), nums))
    if not labels:
        raise ReadFailed("The pages could not be labelled.")
    images = [br._image_doc(n, kind, configs) for n, kind, configs in read.images]
    images, draw = br.merge_triage(images, labels)
    images = br._drawn_only(images, draw, await asyncio.to_thread(br.render_images, data, folder, draw))

    rules = bp.extract(sorted(read.texts.items()))
    numbers = [c.value for c in rules if c.key == "rera_no"]
    source = "text" if numbers else ""
    if not numbers:
        pages = triage.read_order(labels, read.pages)
        order = [n for kinds in (("legal",), ("cover", "text"), ("floor_plan", "master_plan")) for n in pages if labels.get(n, {}).get("kind") in kinds]
        for n in order[:NUMBER_PAGES]:   # a one-sheet brochure prints it on the plan
            number = await read_number(data, n, ask)
            if number:
                numbers, source = [number], "vision"
                break

    rows: List[dict] = []
    headings: List[dict] = []
    table_pages: Dict[str, int] = {}
    plans = [n for n in sorted(labels) if labels[n]["kind"] == "floor_plan" and not labels[n]["other_project"]]
    for n in plans:
        page = await asyncio.to_thread(page_jpeg, data, n, TABLE_SIDE)
        said = await ask([page], HEADINGS)
        for h in (said.get("plans") if isinstance(said, dict) else None) or []:
            if isinstance(h, dict):
                headings.append({**h, "page": n})
        table = checked_rows(await ask([page], AREAS))
        rows += table
        for r in table:
            table_pages.setdefault(next(iter(bp.plan_configs(r["type"])), ""), n)
    for im in images:   # a joined plan keeps its picture, without a home type
        if im.get("kind") == "floor_plan":
            here = [h for h in headings if h.get("page") == im.get("page")]
            im["configs"] = [c for h in here if not joined(h) for c in bp.plan_configs(str(h.get("title") or ""))]

    found: List[bp.Candidate] = list(rules) + carpet_facts(rows, headings, table_pages)
    claims: List[str] = []
    wanted = [n for n in triage.read_order(labels, read.pages) if labels.get(n, {}).get("kind") in FACT_KINDS][:FACT_PAGES]
    for n in wanted:
        answer = await ask([await asyncio.to_thread(page_jpeg, data, n, FACT_SIDE)], FACTS)   # the thumbnails are too small to read
        found += page_facts(answer, n)
        if isinstance(answer, dict):
            claims += [str(x)[:120] for x in answer.get("location_claims") or []]
    if source == "vision":
        found.append(bp.Candidate("rera_no", numbers[0], next(iter(labels)), f"Read twice: {numbers[0]}", by="vision"))
    facts = best_of_each(bp.merge(found, []))
    return {"version": VERSION, "pages": read.pages, "image_only_pages": list(read.image_only), "labels": {str(k): v for k, v in labels.items()},
            "images": images, "numbers": numbers, "number_source": source, "area_rows": rows, "headings": headings,
            "location_claims": list(dict.fromkeys(claims))[:40],
            "facts": [{"key": c.key, "value": c.value, "page": c.page, "quote": c.quote, "label": c.label, "config": c.config, "by": c.by}
                      for c in facts]}


class BrochureReads:
    def __init__(self, db, uploads_dir: Any, kits: Any, now: Callable[[], datetime] = datetime.utcnow,
                 read: Callable[..., Awaitable[Dict[str, Any]]] = read_file):
        self.db, self.uploads_dir, self.kits, self.now, self.read = db, Path(uploads_dir), kits, now, read
        self.reads, self.jobs = db.get_collection(READS), db.get_collection(JOBS)
        self.listings = db.get_collection("listings")

    async def sweep(self) -> int:
        """Queue every attached brochure file not seen yet. -> how many."""
        added = 0
        async for doc in self.listings.find({"media.kind": "document"}, {"media": 1, "agent_id": 1}):
            pdf = files.brochure_pdf(doc, self.uploads_dir)
            if not pdf:
                continue
            jid = f"{doc['_id']}:{pdf.name}"
            if await self.jobs.find_one({"_id": jid}):
                continue
            now = self.now()
            await self.jobs.insert_one({"_id": jid, "listing_id": doc["_id"], "agent_id": doc.get("agent_id"), "file": pdf.name,
                                        "status": "queued", "tries": 0, "not_before": now, "created_at": now})
            added += 1
        return added

    async def fail_stale(self) -> None:
        """A job left "reading" by a cut renderer goes back in the queue; its try is already counted."""
        for job in await self.jobs.find({"status": "reading"}).to_list(100):
            await self._after_failure(job, "The read was cut off.")

    async def status(self, listing_id: str) -> Optional[dict]:
        docs = await self.jobs.find({"listing_id": listing_id}).sort("created_at", -1).limit(1).to_list(1)
        if not docs:
            return None
        return {"status": docs[0]["status"], "note": docs[0].get("note") or None}

    async def _claim(self) -> Optional[dict]:
        now = self.now()
        docs = await self.jobs.find({"status": "queued", "not_before": {"$lt": now + timedelta(seconds=1)}}).sort("created_at", 1).limit(1).to_list(1)
        if not docs:
            return None
        res = await self.jobs.update_one({"_id": docs[0]["_id"], "status": "queued"},
                                         {"$set": {"status": "reading", "started_at": now}, "$inc": {"tries": 1}})
        return {**docs[0], "tries": docs[0].get("tries", 0) + 1} if res.modified_count else None

    async def _after_failure(self, job: dict, why: str) -> None:
        if int(job.get("tries") or 0) >= MAX_TRIES:
            await self._close(job, "failed", "We could not read this brochure. Your listing is fine; its plans just stay off the page.")
            if job.get("sha256"):
                await self.reads.update_one({"_id": job["sha256"]},
                                            {"$set": {"status": "failed", "error": why[:200], "read_at": self.now(), "version": VERSION}},
                                            upsert=True)
        else:
            await self.jobs.update_one({"_id": job["_id"]}, {"$set": {"status": "queued", "note": why[:200], "not_before": self.now()}})

    async def _close(self, job: dict, status: str, note: str = "") -> None:
        await self.jobs.update_one({"_id": job["_id"]}, {"$set": {"status": status, "note": note, "finished_at": self.now()}})

    async def _wait(self, job: dict, why: str) -> None:
        """Money or quota: not this file's fault, so the try is given back and it waits."""
        await self.jobs.update_one({"_id": job["_id"]}, {"$set": {"status": "queued", "note": why[:200], "tries": int(job.get("tries") or 1) - 1,
                                                                  "not_before": self.now() + WAIT}})

    async def _reading(self, job: dict, sha: str, data: bytes, folder: Path) -> Optional[dict]:
        """The stored reading of this very file, made now if it has none. None when it could not be read before: never retried."""
        stored = await self.reads.find_one({"_id": sha})
        if stored and stored.get("status") == "done":
            first = self.uploads_dir / str(stored.get("folder") or "")
            if stored.get("folder") and first != folder and first.is_dir() and not folder.is_dir():
                await asyncio.to_thread(shutil.copytree, first, folder)
            return stored
        if stored and stored.get("status") in ("failed", "over_cap"):
            return None
        day = await budget.today(self.db, self.now())
        if day["gemini_inr"] >= day["gemini_inr_cap"]:
            raise NoCredit("The day's Gemini budget is spent.")
        cost = Cost()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            reading = await self.read(data, folder, asker(cost))
        finally:
            if cost.calls:
                await budget.spend(self.db, self.now(), cost.inr, cost.calls, cost.tokens_in, cost.tokens_out, "brochure")
        doc = {"_id": sha, "status": "done", "version": VERSION, "reading": reading, "read_at": self.now(), "cost_inr": round(cost.inr, 2),
               "calls": cost.calls, "tokens_in": cost.tokens_in, "tokens_out": cost.tokens_out,
               "folder": folder.relative_to(self.uploads_dir).as_posix(), "first_listing": job["listing_id"]}
        await self.reads.update_one({"_id": sha}, {"$set": doc}, upsert=True)
        return doc

    async def run_once(self) -> bool:
        job = await self._claim()
        if not job:
            return False
        try:
            listing = await self.listings.find_one({"_id": job["listing_id"]})
            pdf = files.brochure_pdf(listing, self.uploads_dir) if listing else None
            if not pdf or pdf.name != job["file"]:
                await self._close(job, "dropped", "The brochure is no longer on this listing.")
                return True
            data = await asyncio.to_thread(pdf.read_bytes)
            sha = hashlib.sha256(data).hexdigest()
            await self.jobs.update_one({"_id": job["_id"]}, {"$set": {"sha256": sha}})
            job["sha256"] = sha
            stored = await self._reading(job, sha, data, self.kits._dir(job["listing_id"]) / sha)
            if not stored:
                await self._close(job, "failed", "We could not read this brochure. Your listing is fine; its plans just stay off the page.")
                return True
            await self.kits.adopt(listing, sha, job["file"], stored["reading"], data)
            await self._close(job, "done")
        except NoCredit as e:
            await self._wait(job, str(e))
        except OverCap:
            await self.reads.update_one({"_id": job["sha256"]}, {"$set": {"status": "over_cap", "read_at": self.now(), "version": VERSION}}, upsert=True)
            await self._close(job, "failed", f"This brochure reached the ₹{CAP_INR:g} limit before it was finished.")
        except ReadFailed as e:
            await self._after_failure(job, str(e))
        except Exception as e:
            log.exception("brochure read %s failed", job["_id"])
            await self._after_failure(job, type(e).__name__)
        return True


def default_reads() -> BrochureReads:
    from app.core.config import settings
    from app.core.database import get_database
    return BrochureReads(get_database(), Path(settings.upload_directory), br.default_brochures())


async def sweep(db: Any) -> int:
    """The dispatch loop's call (app.wiring): it runs where no renderer does, so it only reads the listings and queues."""
    return await default_reads().sweep()


