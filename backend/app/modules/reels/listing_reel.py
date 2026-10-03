"""Reels for an agent's own listing: a render job queue (`reel_jobs`) and one background worker per process.

POST /listings/{id}/reel {lang} queues a job; the worker renders ONE job at a time (CPU bound, so make_reel runs in a thread):
  * the listing's own photos (our uploads only, at least 2),
  * a script from the listing's facts and its `about` only (an LLM writes it, director._valid checks it: no invented numbers,
    no phone numbers, Roman on-screen text; otherwise a rules script built from the same facts),
  * 'Listed by <business> · RERA <no>' on the closing scene (never a phone number), with the small Avasetu mark (no end card),
  * a voiceover in English, Hindi or Marathi (Google TTS) with Hinglish/Roman on-screen text (the renderer cannot shape
    Devanagari), over our own generated music bed. Without the TTS key the reel is made with music only, and the job says so.
Sample listings carry the 'Sample listing' badge on every scene.

Limits: 5 reels per agent per rolling 24 hours (failed ones do not count), one active job per listing + language (a re-request
returns it), and a finished reel is returned again unless the listing changed since or `again` is asked for.
Output: <uploads>/reels/listing-<id>-<lang>-<short>.mp4, served under /uploads/reels/.
"""
import asyncio
import logging
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from app.core import brand
from app.modules.marketing.facts import T, Facts
from app.modules.marketing.images import latin, local_upload_path

from . import ffmpeg, voice
from .compose import Scene, TextLine, make_reel, plan, stretch
from .director import XFADE, _valid

log = logging.getLogger(__name__)

COLLECTION = "reel_jobs"
LANGS = ("en", "hi", "mr")
LANG_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
ACTIVE = ("queued", "rendering")
COUNTED = ("queued", "rendering", "done")
DAILY_LIMIT = 5
MIN_PHOTOS = 2
MAX_SCENE_PHOTOS = 5
MARKETABLE = ("live", "under_offer")
STALE_AFTER = timedelta(minutes=15)       # a 'rendering' job older than this was lost (process restart): marked failed
SILENT_SECONDS = 3.0                      # scene length when there is no voice to time it
SAMPLE_BADGE = "Sample listing"
NO_VOICE_NOTE = "Made without a voiceover: the voice service is not set up on the server (GOOGLE_TTS_API_KEY). Music only."
VOICE_FAILED_NOTE = "Made without a voiceover: the voice service did not answer. Music only."

SYSTEM = (
    "You direct a 12 to 16 second vertical reel for ONE property listing, for home buyers in Pune. Write JSON only: "
    '{"beats": [{"screen": "...", "voice": "..."}], "cta_screen": "...", "cta_voice": "..."}. '
    "Rules: 4 beats. beat 1 is the hook: what the home is and where, said so a buyer stops scrolling. "
    "screen: at most 6 words, Roman letters only (English, or Hinglish for Hindi and Marathi), wrap ONE key word in *stars*. "
    "voice: one natural spoken sentence of at most 16 words in the requested voice language (Hindi = Devanagari script, "
    "Marathi = Devanagari, English = English). Write numbers as digits exactly as they appear in the facts. "
    "Use ONLY the facts given: never invent numbers, distances, prices, schools, builders, views or promises. "
    "Never mention phone numbers, names of people or the agent. If the facts say it is a sample listing, say it is a sample. "
    "Plain, calm words: no sales words such as only, just, best, hurry, grab or limited. "
    "cta: invite them to message to book a visit (for a sample listing our own closing line replaces it)."
)


class ReelJobError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
        self.detail = message


# ---- inputs: photos, facts, attribution ------------------------------------------------------------------------
def listing_photos(listing: dict, uploads_dir: Path) -> List[Path]:
    """The listing's own photos (files under <uploads>/images, in the agent's order). Remote URLs are never fetched."""
    media = [(m.get("order") or 0, i, m) for i, m in enumerate(listing.get("media") or []) if (m.get("kind") or "image") == "image"]
    out: List[Path] = []
    for _, _, m in sorted(media, key=lambda t: (t[0], t[1])):
        p = local_upload_path(m.get("url"), uploads_dir)
        if p is not None and p not in out:
            out.append(p)
    return out


def listed_by_line(profile: Optional[dict]) -> str:
    """'Listed by <business name> · RERA <agent no>'; the agent's name when there is no business name. Never a phone number."""
    profile = profile or {}
    branding = profile.get("branding_data") or {}
    clean = lambda s: re.sub(r"\s+", " ", re.sub(r"(?:\+?\d[\s-]?){8,}", "", latin(str(s or "")))).strip(" ,-|·")
    name = clean(branding.get("business_name"))[:60] or clean(profile.get("agent_name"))[:60]
    if not name:
        return ""
    rera = re.sub(r"[^A-Za-z0-9/ -]", "", str(branding.get("rera_agent_no") or "")).strip()[:24]
    if re.fullmatch(r"(?:\+?91)?[6-9]\d{9}", rera.replace(" ", "").replace("-", "")):
        rera = ""  # a mobile number is not a registration number
    return f"Listed by {name}" + (f" · RERA {rera}" if rera else "")


def reel_facts(listing: dict, profile: Optional[dict]) -> Tuple[str, List[str], Facts]:
    """(subject, fact lines, Facts): everything the script may say, from the listing and its `about` only."""
    f = Facts.from_docs(listing, {k: v for k, v in (profile or {}).items() if k != "phone"}, "")  # the reel never needs his number
    about = listing.get("about") or {}
    subject = f.title_line("en") + (" (sample listing, shown for illustration, not available)" if f.sample else "")
    lines: List[str] = [f.title_line("en")]
    if f.price_text:
        lines.append(f"Price {f.price_text}")
    if f.area_text:
        lines.append(f"{f.area_kind.capitalize()} area {f.area_text}")
    if f.floor_text("en"):
        lines.append(f.floor_text("en"))
    if f.possession_text("en"):
        lines.append(f.possession_text("en"))
    if f.furnishing:
        lines.append(T["en"]["furn"].get(f.furnishing, f.furnishing))
    if f.project:
        lines.append(f"Project: {f.project}")
    if f.amenities:
        lines.append("Amenities: " + ", ".join(f.amenities[:10]))
    if f.rera:
        lines.append(f"Project RERA {f.rera}")
    for h in (about.get("highlights") or [])[:6]:
        lines.append(f"Highlight: {h}")
    for c in (about.get("connectivity") or [])[:4]:
        lines.append(f"Connectivity: {c}")
    for n in (about.get("nearby") or [])[:6]:
        if isinstance(n, dict) and n.get("name"):
            lines.append(f"Nearby {n.get('type') or 'place'}: {n['name']}" + (f", {n['minutes']} minutes" if n.get("minutes") is not None else ""))
    for key in ("builder_known_as", "water", "power_backup", "parking", "society", "possession_note"):
        if about.get(key):
            lines.append(f"{key.replace('_', ' ').capitalize()}: {about[key]}")
    if f.sample:
        lines.append("This is a sample listing shown for illustration, not available")
    return subject, lines, f


# ---- the rules script (always valid, used when the LLM is missing or breaks the rules) -------------------------------
_UNIT = {"hi": {"Lakh": "लाख", "Cr": "करोड़", "/month": " महीना"}, "mr": {"Lakh": "लाख", "Cr": "कोटी", "/month": " दरमहा"}}
_WORDS = {
    "en": {"price": "Price {p}.", "area": "{a} square feet {k} area", "sqft": "sq ft", "look": "Take a *look* inside",
           "look_v": "Take a look inside.", "cta_s": "Message to book a *visit*", "cta_v": "Like it? Message us to book a visit.",
           "sample": "This is a sample listing, shown for illustration. ", "with": "with", "in": "{w} in {l}",
           "cta_sample_s": "Tell us *what* you want", "cta_sample_v": "Tell us what you are looking for, and we will find a real one."},
    "hi": {"price": "कीमत {p}।", "area": "{a} स्क्वेयर फीट {k} एरिया", "look": "Andar ek *nazar*", "look_v": "अंदर एक नज़र डालिए।",
           "cta_s": "Visit ke liye *message* karein", "cta_v": "पसंद आया? विज़िट बुक करने के लिए मैसेज कीजिए।",
           "sample": "यह एक सैंपल लिस्टिंग है, सिर्फ़ दिखाने के लिए। ", "with": "साथ में", "in": "{l} mein {w}",
           "cta_sample_s": "Batayein aapko *kya* chahiye", "cta_sample_v": "बताइए आपको कैसा घर चाहिए, हम असली घर ढूँढेंगे।"},
    "mr": {"price": "किंमत {p}.", "area": "{a} स्क्वेअर फूट {k} एरिया", "look": "Aat ek *nazar*", "look_v": "आत एक नजर टाका.",
           "cta_s": "Visit sathi *message* kara", "cta_v": "आवडलं? व्हिजिट बुक करण्यासाठी मेसेज करा.",
           "sample": "ही एक सॅम्पल लिस्टिंग आहे, फक्त दाखवण्यासाठी. ", "with": "सोबत", "in": "{l} madhye {w}",
           "cta_sample_s": "Sanga tumhala *kay* hava", "cta_sample_v": "तुम्हाला कसं घर हवं ते सांगा, आम्ही खरं घर शोधू."},
}
_KIND = {"hi": {"carpet": "कार्पेट", "super built-up": "सुपर बिल्ट-अप"}, "mr": {"carpet": "कार्पेट", "super built-up": "सुपर बिल्ट-अप"}}


def _spoken_price(f: Facts, lang: str) -> str:
    """'₹85 Lakh' -> '85 lakh rupees' / '85 लाख रुपये'; '₹45,000/month' -> '45,000 rupees a month' / '45,000 रुपये महीना'."""
    p = f.price_text.replace("₹", "").replace("/month", "")
    if lang == "en":
        return p.replace("Cr", "crore").replace("Lakh", "lakh") + (" rupees a month" if f.rent else " rupees")
    for a, b in _UNIT[lang].items():
        p = p.replace(a, b)
    return p + " रुपये" + (_UNIT[lang]["/month"] if f.rent else "")


def _join_and(items: List[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _end(lang: str) -> str:
    return "।" if lang == "hi" else "."


def _short(text: str, words: int = 6) -> str:
    return " ".join(latin(text).split()[:words])


def rules_script(f: Facts, lang: str) -> Dict:
    """A plain script from the facts alone: hook, price, size and floor, features (3 to 4 beats) and the visit call."""
    w = _WORDS[lang]
    what = latin(f.bhk_text or f.type_text("en").title())
    place = _short(f.locality or f.city or "", 3)
    hook_s = w["in"].format(w=f"*{what}*", l=place) if place else f"*{what}*"
    beats = [{"screen": hook_s, "voice": f.title_line(lang) + _end(lang)}]
    if f.price_text:
        beats.append({"screen": f"*{f.price_text}*", "voice": w["price"].format(p=_spoken_price(f, lang))})
    if f.area or f.floor is not None:
        # commas, not ' · ': the renderer wraps on spaces, so a lone dot could start the next line
        screen = ", ".join(x for x in [f"*{f.area:,}* sq ft" if f.area else "", f.floor_text("en") or ""] if x)
        kind = f.area_kind or "carpet"
        spoken = [w["area"].format(a=f"{f.area:,}", k=_KIND.get(lang, {}).get(kind, kind))] if f.area else []
        if f.floor_text(lang):
            spoken.append(("on " + f.floor_text(lang).lower()) if lang == "en" and spoken else f.floor_text(lang))
        beats.append({"screen": screen, "voice": ", ".join(spoken) + _end(lang)})
    feats_en = [x for x in (f.possession_text("en"), T["en"]["furn"].get(f.furnishing or "")) if x]
    amen = [latin(a) for a in f.amenities if latin(a)][:3]
    if feats_en or amen:
        screen_bits = [_short(x, 3) for x in (feats_en[:1] + amen)[:3]]
        screen_bits[-1] = f"*{screen_bits[-1]}*"
        spoken = [x for x in (f.possession_text(lang), T[lang]["furn"].get(f.furnishing or "")) if x]
        if amen:
            spoken.append(f"with {_join_and(amen)}" if lang == "en" else f"{w['with']} " + ", ".join(amen))
        text = ", ".join(x[:1].lower() + x[1:] if lang == "en" else x for x in spoken)
        beats.append({"screen": ", ".join(screen_bits), "voice": text[:1].upper() + text[1:] + _end(lang)})
    if f.highlights and len(beats) < 4 and latin(f.highlights[0]):
        h = latin(f.highlights[0])
        beats.append({"screen": _short(h, 6), "voice": h if lang == "en" else f.highlights[0]})
    while len(beats) < 3:
        beats.append({"screen": w["look"], "voice": w["look_v"]})
    if f.sample:  # a sample home cannot be visited: ask what they want instead
        return {"beats": beats[:5], "cta_screen": w["cta_sample_s"], "cta_voice": w["sample"] + w["cta_sample_v"]}
    return {"beats": beats[:5], "cta_screen": w["cta_s"], "cta_voice": w["cta_v"]}


_PUSHY = re.compile(r"\b(only|just|best|hurry|grab|limited|don'?t miss|guarantee\w*|steal|unbeatable)\b|केवल|जल्दी|मौका|घाई", re.I)


def pushy(script: Dict) -> bool:
    """Sales words ('only 78 lakh', 'hurry'): listing reels stay calm and factual."""
    beats = list(script.get("beats") or []) + [{"screen": script.get("cta_screen", ""), "voice": script.get("cta_voice", "")}]
    return any(_PUSHY.search(f"{b.get('screen', '')} {b.get('voice', '')}") for b in beats if isinstance(b, dict))


_ON_SALE = re.compile(r"\s*(for sale|for rent|on sale|बिक्री के लिए( उपलब्ध)?|किराये के लिए|विक्रीसाठी|भाड्याने)", re.I)


def for_sample(script: Dict, lang: str) -> Dict:
    """A sample home is not for sale and cannot be visited: no 'for sale' wording, and the closing says it is a sample and
    asks what the viewer wants instead of offering a visit (the badge is on every scene too)."""
    w = _WORDS[lang]
    beats = [{**b, "screen": _ON_SALE.sub("", str(b.get("screen", ""))).strip(),
              "voice": _ON_SALE.sub("", str(b.get("voice", ""))).strip()} for b in script.get("beats") or []]
    return {**script, "beats": beats, "cta_screen": w["cta_sample_s"], "cta_voice": w["sample"] + w["cta_sample_v"]}


async def write_script(subject: str, facts: Sequence[str], lang: str, llm, fallback: Dict) -> Dict:
    """The LLM's script when it keeps to the facts (director._valid), else the rules script."""
    facts_text = "\n".join(f"- {x}" for x in facts)
    if llm is not None:
        for _ in range(2):
            try:
                out = await llm.json(SYSTEM, f"Voice language: {LANG_NAMES[lang]}\nSubject: {subject}\nFacts:\n{facts_text}")
            except Exception:
                out = None
            if _valid(out, subject + "\n" + facts_text) and not pushy(out):
                return {"beats": out["beats"], "cta_screen": out["cta_screen"], "cta_voice": out["cta_voice"], "made_by": "llm"}
    return {**fallback, "made_by": "rules"}


# ---- rendering (blocking; runs in a worker thread) -----------------------------------------------------------------
def render(script: Dict, photos: Sequence, lang: str, out_path: Path, badge: Optional[str] = None, kicker: Optional[str] = None,
           closing: str = "", voiced: bool = True) -> Dict:
    """Render the reel. Returns {"audio": "voice+music"|"music", "note": str}. Falls back to music only if the voice fails."""
    beats = list(script["beats"]) + [{"screen": script["cta_screen"], "voice": script["cta_voice"]}]
    work = Path(tempfile.mkdtemp(prefix="listing-reel-"))
    note = ""
    try:
        clips: List[Path] = []
        durs: List[float] = []
        if voiced:
            try:
                for i, b in enumerate(beats):
                    mp3 = work / f"b{i}.mp3"
                    mp3.write_bytes(voice.synth(b["voice"], lang))
                    clips.append(mp3)
                    durs.append(max(2.2, ffmpeg.probe(mp3).duration + 0.55))
            except voice.VoiceError:
                voiced, clips, note = False, [], VOICE_FAILED_NOTE
        if not voiced:
            note = note or NO_VOICE_NOTE
            durs = [SILENT_SECONDS + (0.4 if i == 0 else 0.0) for i in range(len(beats))]
        durs = stretch(durs, XFADE)
        scenes = []
        for i, b in enumerate(beats):
            first, last = i == 0, i == len(beats) - 1
            lines = [TextLine(b["screen"], size=104 if first else 96)]
            if last and closing:  # 'Listed by X · RERA Y' as two lines, so the separator never starts a wrapped line
                for part in [p.strip() for p in closing.split(" · ") if p.strip()]:
                    lines.append(TextLine(part, size=44, weight="medium", max_lines=2))
            scenes.append(Scene(image=photos[i % len(photos)], lines=lines, layout="lower", badge=badge,
                                kicker=kicker if first else None, seconds=durs[i], seed=f"listing-{i}"))
        tl = plan(durs, XFADE)   # no end card: the closing scene carries the brand mark and the reel loops
        from .music import write as write_music
        bed = write_music(work / "bed.wav", seconds=tl.total + 1.0)
        if voiced:
            inputs, filters = [], []
            for i, c in enumerate(clips):
                inputs += ["-i", str(c)]
                ms = int((tl.starts[i] + (0.35 if i == 0 else 0.25)) * 1000)
                filters.append(f"[{i}:a]adelay={ms}|{ms},aresample=48000[a{i}]")
            mix = "".join(f"[a{i}]" for i in range(len(clips)))
            filters.append(f"{mix}amix=inputs={len(clips)}:normalize=0,apad=whole_dur={tl.total:.2f},volume=1.35[voice]")
            inputs += ["-i", str(bed)]
            filters.append(f"[{len(clips)}:a]aresample=48000,volume=0.22[bed]")
            filters.append("[voice][bed]amix=inputs=2:normalize=0:duration=first[out]")
            audio = work / "narration.m4a"
            ffmpeg.run([*inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-t", f"{tl.total:.2f}",
                        "-c:a", "aac", "-b:a", "160k", str(audio), "-y"])
        else:
            audio = bed
        make_reel(scenes, out_path, music=audio, transition="slide", xfade=XFADE)
        return {"audio": "voice+music" if voiced else "music", "note": note}
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---- jobs ------------------------------------------------------------------------------------------------------------
def _iso(dt) -> Optional[str]:
    return dt.replace(microsecond=0).isoformat() + "Z" if isinstance(dt, datetime) else dt


def job_out(doc: Optional[dict], base_url: str = "") -> Optional[dict]:
    """The job as the API returns it. `video_url` is absolute when `base_url` is given."""
    if not doc:
        return None
    path = doc.get("video_path")
    return {"id": doc["_id"], "listing_id": doc["listing_id"], "lang": doc["lang"], "status": doc["status"],
            "video_path": path, "video_url": (base_url.rstrip("/") + path if base_url and path else path),
            "script": doc.get("script"), "audio": doc.get("audio"), "note": doc.get("note") or "", "error": doc.get("error") or "",
            "sample": bool(doc.get("sample")), "created_at": _iso(doc.get("created_at")), "finished_at": _iso(doc.get("finished_at")),
            "posts": doc.get("posts") or []}


def _safe_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(s))[:40] or "x"


class ReelJobs:
    def __init__(self, db, uploads_dir, llm_factory: Optional[Callable] = None, renderer: Callable = render,
                 now: Callable[[], datetime] = datetime.utcnow, voice_available: Callable[[], bool] = voice.available):
        self.jobs = db.get_collection(COLLECTION)
        self.listings = db.get_collection("listings")
        self.profiles = db.get_collection("agent_public_profiles")
        self.uploads_dir = Path(uploads_dir)
        self.llm_factory = llm_factory
        self.renderer, self.now, self.voice_available = renderer, now, voice_available

    async def _listing(self, agent_id: str, listing_id: str) -> dict:
        doc = await self.listings.find_one({"_id": listing_id, "agent_id": agent_id})
        if not doc:
            raise ReelJobError("Listing not found", 404)
        return doc

    async def _latest(self, flt: dict) -> Optional[dict]:
        docs = await self.jobs.find(flt).sort("created_at", -1).limit(1).to_list(1)
        return docs[0] if docs else None

    async def create(self, agent_id: str, listing_id: str, lang: str, again: bool = False) -> Tuple[dict, bool]:
        """(job doc, created). Re-requests return the active job, or the finished one if the listing has not changed."""
        if lang not in LANGS:
            raise ReelJobError("Language must be en, hi or mr", 422)
        listing = await self._listing(agent_id, listing_id)
        if listing.get("status") not in MARKETABLE:
            raise ReelJobError("Only live or under-offer listings can have a reel. Publish this listing first.", 409)
        active = await self._latest({"listing_id": listing_id, "agent_id": agent_id, "lang": lang, "status": {"$in": list(ACTIVE)}})
        if active:
            return active, False
        if not again:
            done = await self._latest({"listing_id": listing_id, "agent_id": agent_id, "lang": lang, "status": "done"})
            changed = listing.get("updated_at")
            if done and not (isinstance(changed, datetime) and changed > done["created_at"]):
                return done, False
        if len(listing_photos(listing, self.uploads_dir)) < MIN_PHOTOS:
            raise ReelJobError("Add at least 2 photos", 422)
        now = self.now()
        used = await self.jobs.count_documents({"agent_id": agent_id, "status": {"$in": list(COUNTED)},
                                                "created_at": {"$gte": now - timedelta(hours=24)}})
        if used >= DAILY_LIMIT:
            raise ReelJobError(f"You can make {DAILY_LIMIT} reels a day. Try again tomorrow.", 429)
        jid = uuid.uuid4().hex
        doc = {"_id": jid, "listing_id": listing_id, "agent_id": agent_id, "lang": lang, "status": "queued", "video_path": None,
               "script": None, "error": None, "note": None, "audio": None, "created_at": now, "started_at": None, "finished_at": None,
               "sample": (listing.get("title") or "").strip().lower().startswith("sample")}
        await self.jobs.insert_one(doc)
        return doc, True

    async def latest(self, agent_id: str, listing_id: str) -> Dict[str, dict]:
        await self._listing(agent_id, listing_id)
        out = {}
        for lang in LANGS:
            doc = await self._latest({"listing_id": listing_id, "agent_id": agent_id, "lang": lang})
            if doc:
                out[lang] = doc
        return out

    async def latest_done(self, agent_id: str, listing_id: str, lang: str) -> Optional[dict]:
        return await self._latest({"listing_id": listing_id, "agent_id": agent_id, "lang": lang, "status": "done"})

    # ---- worker side -------------------------------------------------------------------------------------------
    async def fail_stale(self) -> None:
        cutoff = self.now() - STALE_AFTER
        for d in await self.jobs.find({"status": "rendering"}).to_list(100):
            if isinstance(d.get("started_at"), datetime) and d["started_at"] < cutoff:
                await self.jobs.update_one({"_id": d["_id"], "status": "rendering"},
                                           {"$set": {"status": "failed", "error": "The reel was interrupted. Please try again.",
                                                     "finished_at": self.now()}})

    async def claim(self) -> Optional[dict]:
        nxt = await self._oldest_queued()
        if not nxt:
            return None
        res = await self.jobs.update_one({"_id": nxt["_id"], "status": "queued"}, {"$set": {"status": "rendering", "started_at": self.now()}})
        if res is not None and getattr(res, "modified_count", 1) == 0:
            return None  # another process took it
        return {**nxt, "status": "rendering"}

    async def _oldest_queued(self) -> Optional[dict]:
        docs = await self.jobs.find({"status": "queued"}).sort("created_at", 1).limit(1).to_list(1)
        return docs[0] if docs else None

    async def _finish(self, jid: str, **fields) -> None:
        await self.jobs.update_one({"_id": jid}, {"$set": {**fields, "finished_at": self.now()}})

    async def run(self, job: dict) -> None:
        """Render one claimed job. Never raises: failures are stored on the job with a message safe to show."""
        jid = job["_id"]
        try:
            listing = await self.listings.find_one({"_id": job["listing_id"], "agent_id": job["agent_id"]})
            if not listing:
                return await self._finish(jid, status="failed", error="The listing was removed.")
            photos = listing_photos(listing, self.uploads_dir)
            if len(photos) < MIN_PHOTOS:
                return await self._finish(jid, status="failed", error="Add at least 2 photos")
            profile = await self.profiles.find_one({"agent_id": job["agent_id"]})
            subject, facts, f = reel_facts(listing, profile)
            llm = self.llm_factory() if self.llm_factory else None
            script = await write_script(subject, facts, job["lang"], llm, rules_script(f, job["lang"]))
            if f.sample:
                script = for_sample(script, job["lang"])
            await self.jobs.update_one({"_id": jid}, {"$set": {"script": script}})
            name = f"listing-{_safe_id(job['listing_id'])}-{job['lang']}-{jid[:8]}.mp4"
            out = self.uploads_dir / "reels" / name
            kicker = _short(f.loc.upper(), 5) or None
            result = await asyncio.to_thread(
                self.renderer, script, photos[:MAX_SCENE_PHOTOS], job["lang"], out, badge=SAMPLE_BADGE if f.sample else None,
                kicker=kicker, closing=listed_by_line(profile), voiced=self.voice_available())
            await self._finish(jid, status="done", video_path=f"/uploads/reels/{name}", audio=result.get("audio"),
                               note=result.get("note") or "", error=None)
        except Exception as e:  # ffmpeg missing, disk full, a bad photo...
            log.exception("listing reel %s failed", jid)
            msg = str(e) if e.__class__.__name__ in ("ReelError", "FfmpegError") else "Could not make the reel. Please try again."
            await self._finish(jid, status="failed", error=msg[:300])

    async def run_once(self) -> bool:
        job = await self.claim()
        if not job:
            return False
        await self.run(job)
        return True


# ---- the background worker -----------------------------------------------------------------------------------------
_task: Optional[asyncio.Task] = None


def default_jobs() -> ReelJobs:
    from app.core.config import settings
    from app.core.database import get_database
    from app.platform.llm import default_llm
    return ReelJobs(get_database(), Path(settings.upload_directory), llm_factory=default_llm)


HEARTBEAT_EVERY_S = 60.0  # the loop polls every few seconds; its heartbeat is written at most once a minute
HEARTBEAT_INTERVAL_S = STALE_AFTER.total_seconds()  # a render may take this long without a heartbeat (app/worker.py --check)


def _get_database():
    from app.core.database import get_database
    return get_database()


async def loop(make_jobs: Callable[[], ReelJobs] = default_jobs, poll: float = 3.0, get_db: Callable = _get_database) -> None:
    """Render queued jobs one at a time, forever. Started only under the 'listing_reels' runner lease (ensure_worker in the
    API, or app/worker.py), so one process renders at a time."""
    from app.platform.heartbeats import heartbeat
    try:
        await make_jobs().fail_stale()
    except Exception:
        log.exception("reel worker: could not clean up stale jobs")
    while True:
        try:
            async with heartbeat("listing_reels", get_db, every_s=HEARTBEAT_EVERY_S):
                busy = await make_jobs().run_once()
            if busy:
                continue
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("reel worker loop error")
        await asyncio.sleep(poll)


def ensure_worker() -> Optional[asyncio.Task]:
    """Start the worker if it is not running in this process (idempotent; called by the app lifespan and the reel routes).
    The worker renders only while this process holds the 'listing_reels' runner lease, so with several processes one renders
    and the others wait; its startup clean-up (fail_stale) therefore never fails a render another process is still running.
    With RUN_BACKGROUND_LOOPS=false the API starts nothing (returns None): the worker process (app/worker.py) renders the
    jobs the API queues in `reel_jobs`."""
    global _task
    from app.core.config import settings
    if not settings.run_background_loops:
        return None
    if _task is None or _task.done():
        from app.core.database import get_database
        from app.platform.leases import run_as_leader
        _task = asyncio.get_running_loop().create_task(run_as_leader("listing_reels", loop, get_database))
    return _task


def caption(listing: dict, attribution: str) -> str:
    """Caption for posting the reel on the Avasetu pages: what and where, price, the 'Listed by' attribution, the brand."""
    f = Facts.from_docs(listing, None, "")
    bits = " · ".join(x for x in (f.price_text, f.area_text and f"{f.area_text} {f.area_kind}") if x)
    title = _ON_SALE.sub("", f.title_line("en")).strip() if f.sample else f.title_line("en")  # a sample is not for sale
    lines = [title + (f"\n{bits}" if bits else "")]
    if f.sample:
        lines.append("Sample listing, shown for illustration. Not available.")
    if attribution:
        lines.append(attribution)
    lines.append(f"{brand.NAME} · {brand.TAGLINE} {brand.HASHTAG}")
    return "\n\n".join(lines)
