"""The master boost pair of a listing: one reel and one carousel made to be boosted (paid) on Meta, with their ad copy, tracked
links and a spend guide. Made in the marketing run right after the posts and reels (jobs.py); a failure never fails the run.

Reel (9:16, under 20 s, compose.make_reel): a hook card first (price and place, no fade-in, no brand tag), the property's own
pictures (its photos, or stills of its video), two fact beats (size; distance to work or the EMI), the MahaRERA proof card only
when registered, and a WhatsApp end card. At most 7 words a beat, every number from the verified facts.
Carousel (1080x1350, up to 6 cards, the campaign's card pipeline): hook + photo, price breakdown, size, nearby, MahaRERA check
(registered only), and the WhatsApp card. Cards are English (no Devanagari font); the ad copy is in the run's language.
Every line goes through the creative guards (creative.guards.problems_in) against the facts' corpus."""
import asyncio
import hashlib
import logging
import re
import zipfile
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote

from app.modules.creative import i18n, pipeline
from app.modules.creative.guards import problems_in
from app.modules.creative.hooks import PATTERNS
from app.modules.creative.listing_brief import price_label
from app.modules.creative.models import Brief

from . import campaign, surroundings
from .facts import Fact

log = logging.getLogger(__name__)

META_OPEN_URL = "https://business.facebook.com/latest/home"
CTA = "WHATSAPP_MESSAGE"
CHANNEL = "boost"
PRIMARY_MAX, HEADLINE_MAX, BEAT_WORDS = 125, 40, 7
READY_AFTER_H = 48
MIN_REEL_S = 18.5   # scene seconds before the cross-fades: the reel lands at about 15 to 20 s
# where the buyers are: (localities, radius km, reel ₹/day); anything else gets DEFAULT_GUIDE
AREA_GUIDES: Tuple[Tuple[Tuple[str, ...], int, int], ...] = (
    (("kharadi", "upper kharadi", "wagholi", "lohegaon", "keshav nagar"), 15, 400),
    (("ranjangaon", "shikrapur", "shirur"), 25, 250),
)
DEFAULT_GUIDE = (15, 300)
DAYS, CAROUSEL_DAILY, CAROUSEL_DELAY, AGE = 5, 150, 2, (28, 55)
CTA_CARD = "Send 'Hi' on WhatsApp: get the fact sheet and a site visit slot."
END_LINE = "WhatsApp us — tap below"   # the ad's button sits under the reel: code-written, not a caption (no guard on 'tap')


def ref(listing_id: str, kind: str) -> str:
    """The interest-link ref of a boost piece: kind is boost_reel or boost_post."""
    return f"campaign-{listing_id}-{kind}"


def guide(locality: str, taluka: str = "") -> Dict[str, Any]:
    places = {(locality or "").strip().lower(), (taluka or "").strip().lower()}
    radius, daily = next(((r, d) for names, r, d in AREA_GUIDES if places & set(names)), DEFAULT_GUIDE)
    return {"objective_label": "Messages (WhatsApp)", "area": locality or taluka or "Pune", "radius_km": radius,
            "age_min": AGE[0], "age_max": AGE[1], "daily_budget_inr": daily, "days": DAYS,
            "carousel_daily_inr": CAROUSEL_DAILY, "carousel_delay_days": CAROUSEL_DELAY}


def short_price(n: int) -> str:
    """4200000 -> '₹42L', 12500000 -> '₹1.25Cr' (the same digits as price_label says)."""
    lab = price_label(n)
    return lab.replace(" lakh", "L").replace(" crore", "Cr")


def _words(s: str) -> int:
    return len([w for w in re.split(r"\s+", s.strip()) if w and w not in ("—", "-", ":")])


def _fit(options: Sequence[str], n: int = BEAT_WORDS) -> str:
    """The first option of at most n words ('' when none fits)."""
    return next((o for o in options if o and _words(o) <= n), "")


class Facts:
    """The numbers a boost piece may say, from the usable facts (campaign.Ctx)."""

    def __init__(self, facts: Dict[str, Fact]):
        self.c = c = campaign.Ctx(facts)
        v = c.v
        self.price = v.get("price_inr")
        self.work = (v.get("nearby.industry") or [None])[0]
        if self.work:   # the name a buyer uses ("Ranjangaon MIDC"), as the campaign's cards say it
            self.work = {**self.work, "name": c.place("industry", self.work)}
        self.near = campaign._near(c)
        self.emi = v.get("emi") if not c.layout else None
        self.rera = str(v.get("rera_no") or "") if c.registered else ""
        self.place = c.project or c.locality
        self.kinds = (c.kind + "s") if c.layout else c.kind

    def hook(self) -> str:
        c, lead = self.c, ""
        if self.price:
            p = short_price(self.price)
            lead = f"{c.kind.capitalize()}s from {p}" if c.layout else f"{p} {c.kind}"
        else:
            lead = f"{c.kind.capitalize()}s" if c.layout else f"A {c.kind}"
        opts = [f"{lead}, {campaign._km(self.work['km'])} from {self.work['name']}"] if self.work else []
        if c.locality:
            opts.append(f"{lead} in {c.locality}")
        if self.place:
            opts.append(f"{lead} at {self.place}")
        if self.work:
            opts.append(f"{lead}, {campaign._km(self.work['km'])} to work")
        return _fit(opts) or lead

    def size(self) -> str:
        c, v = self.c, self.c.v
        lo, hi = v.get("size_min_sqft"), v.get("size_max_sqft")
        if c.layout and lo and hi and hi > lo:
            return f"{lo:,} to {hi:,} sq ft {c.kind}s"
        if c.sqft:
            g = v.get("plot_guntha")
            return _fit([f"{c.sqft:,} sq ft {c.kind} ({g:g} guntha)" if g else "", f"{c.sqft:,} sq ft {c.kind}"])
        if v.get("units_total"):
            return f"{v['units_total']} {c.kind}s in all"
        return ""

    def second(self, hook: str) -> Tuple[str, str]:
        """(beat, small print): the distance to work unless the hook already says it, else the EMI."""
        if self.work and campaign._km(self.work["km"]) not in hook:
            line = _fit([f"{campaign._km(self.work['km'])} to {self.work['name']}", f"{campaign._km(self.work['km'])} to work"])
            if line:
                return line, "straight-line distance"
        if self.emi:
            return f"EMI about ₹{self.emi['emi']:,} a month", self.emi_note()
        if self.near:
            k, p = self.near[0]
            return _fit([f"{self.c.place(k, p)}: {campaign._km(p['km'])}", f"{surroundings.label(k)}: {campaign._km(p['km'])}"]), \
                "straight-line distance"
        return "", ""

    def emi_note(self) -> str:
        e = self.emi
        return f"80% loan at {e['rate']:g}% for {e['years']} years" if e else ""


# ---- the carousel: the campaign's card pipeline, one card per brief ---------------------------------------------------------
def carousel_briefs(f: Facts, hook: str, photo: str) -> List[Tuple[str, Brief]]:
    c, v = f.c, f.c.v
    en = lambda b: replace(b, language="en", contact=[])   # cards are English
    out: List[Tuple[str, Brief]] = []
    base = campaign.price_reveal(c) or campaign.overview(c)
    if base is not None:
        work = [f"{c.place('industry', p)} is about {campaign._km(p['km'])} away (straight line)." for p in v.get("nearby.industry") or []]
        out.append(("hook", en(replace(base, hooks={p: hook for p in PATTERNS}, photo=photo, facts=list(base.facts) + work))))
    # single cards only (stat and tip layouts): a list layout draws a carousel of its own, whose cover alone says nothing
    if f.price:
        price = price_label(f.price)
        rate = v.get("price_per_sqft")
        label = ("starting price" if c.layout else "listed price") + (f", ₹{rate:,} per sq ft" if rate else "")
        facts = [f"Listed price: {price}."] + ([f"Rate: ₹{rate:,} per sq ft."] if rate else [])
        tip = "Ask what the price includes: stamp duty, registration and charges."
        if f.emi:
            tip = f"EMI about ₹{f.emi['emi']:,} a month: {f.emi_note()}. Ask your bank for its rate."
            facts.append(tip)
        out.append(("price", en(c.brief(hook=f"What {price} buys at {f.place}" if f.place else f"What {price} buys",
                                         topic="Price breakdown", short="price breakdown", stat_value=price, stat_label=label,
                                         facts=facts, tip=tip, prefer="stat"))))
    size = campaign.size_in_guntha(c) or campaign.land_area(c) or campaign.layout_size(c)
    if size is None and f.size():
        size = c.brief(hook=f.size(), topic="Size", short="size", stat_value=f"{c.sqft:,} sq ft" if c.sqft else f.size(),
                       stat_label=f"this {c.kind}", facts=[f.size()], prefer="stat")
    if size is not None:
        out.append(("size", en(replace(size, prefer="stat"))))
    near = f.near[:3]
    if near:
        k0, p0 = near[0]
        lines = [f"{p['name']}: about {campaign._km(p['km'])}" for _, p in near]
        out.append(("nearby", en(c.brief(hook=f"What is near {f.place}?" if f.place else "What is nearby?", topic="Nearby",
                                          short="what is nearby", stat_value=campaign._km(p0["km"]), stat_label=f"to {p0['name']}",
                                          facts=lines, tip="; ".join(lines[1:]) + ". Straight-line distances." if len(lines) > 1
                                          else "Straight-line distance: drive it once.", prefer="stat"))))
    if f.rera:
        out.append(("maharera", en(c.brief(hook=f"MahaRERA {f.rera}: check it yourself", topic="Check it on MahaRERA",
                                            short="MahaRERA check", stat_value=f.rera, stat_label="MahaRERA registration number",
                                            facts=[f"{c.project or 'This project'} is registered on MahaRERA as {f.rera}."],
                                            tip="Search it on the MahaRERA website: completion date, approvals, promoter.",
                                            prefer="stat"))))
    out.append(("cta", en(c.brief(hook="Want the full fact sheet?", topic="Get the fact sheet", short="fact sheet", tip=CTA_CARD,
                                   facts=[CTA_CARD], prefer="single"))))
    return out


async def _cards(briefs: List[Tuple[str, Brief]], out: Path) -> List[str]:
    """One card per brief (the first image of its pack); a card that fails a guard is left out."""
    paths: List[str] = []
    for i, (name, b) in enumerate(briefs):
        try:
            pack = await pipeline.make(b, "buyer", "instagram", None, seed=i, out_dir=out / name, reviewer=None)
        except Exception:
            log.warning("boost card %s failed", name, exc_info=True)
            continue
        if pack.report.get("ok") and pack.images:
            dest = out / f"card{len(paths) + 1}{Path(pack.images[0]).suffix}"
            Path(pack.images[0]).replace(dest)
            paths.append(str(dest))
        else:
            log.info("boost card %s dropped: %s", name, pack.report.get("problems"))
    return paths


def _zip(paths: Sequence[str], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, Path(p).name)
    return dest


# ---- the reel: compose scenes ----------------------------------------------------------------------------------------------
def reel_beats(f: Facts, brand_name: str = "") -> Tuple[str, List[dict]]:
    """(hook, beats): each beat {"lines": [main, small?], "photo": bool, "kind"}. Main lines at most 7 words."""
    hook = f.hook()
    beats: List[dict] = []
    size = f.size()
    if size:
        beats.append({"kind": "size", "lines": [size], "photo": True})
    second, small = f.second(hook)
    if second:
        beats.append({"kind": "fact", "lines": [second] + ([small] if small else []), "photo": True})
    if f.rera:
        beats.append({"kind": "maharera", "lines": [f"MahaRERA {f.rera}", "Check it yourself on maharera.maharashtra.gov.in"],
                      "photo": False})
    beats.append({"kind": "cta", "lines": [END_LINE] + ([brand_name[:40]] if brand_name else []), "photo": False})
    return hook, beats


def reel_scenes(hook: str, beats: List[dict], photos: Sequence[str], kicker: str) -> List[Any]:
    from app.modules.reels.compose import Scene, TextLine
    pics = list(photos)
    scenes = [Scene(lines=[TextLine(hook, size=124, max_lines=4)], kicker=kicker or None, seconds=2.2, seed="boost-hook")]
    for i, p in enumerate(pics[:2]):   # the property itself, right after the hook
        scenes.append(Scene(image=p, seconds=2.4, seed=f"boost-photo{i}"))
    for i, b in enumerate(beats):
        img = pics[(2 + i) % len(pics)] if pics and b["photo"] else None
        lines = [TextLine(b["lines"][0], size=96, max_lines=3)] + [TextLine(x, size=40) for x in b["lines"][1:]]
        scenes.append(Scene(image=img, lines=lines, layout="center", seconds=2.8 if b["kind"] == "cta" else 2.5,
                            seed=f"boost-{b['kind']}"))
    total = sum(x.seconds for x in scenes)
    if total < MIN_REEL_S:   # few pictures: the beats stay on screen longer, so the reel still runs 15 s or more
        k = min(MIN_REEL_S / total, 1.7)
        scenes = [replace(x, seconds=round(x.seconds * k, 2)) if i else x for i, x in enumerate(scenes)]
    return scenes


def default_reel_renderer(scenes, out: Path) -> Dict[str, Any]:
    from app.modules.reels.compose import Renderer, cover_path, make_reel
    path = make_reel(scenes, out, progress=False, hook_tag=False)
    return {"video": Path(path), "poster": cover_path(path), "seconds": round(Renderer(scenes, progress=False).tl.total, 1)}


# ---- copy ------------------------------------------------------------------------------------------------------------------
COPY = {
    "en": {"reel": "{hook}. {fact} MahaRERA {rera}: check it yourself. WhatsApp us for the fact sheet.",
           "reel_plain": "{hook}. {fact} WhatsApp us for the fact sheet and a site visit slot.",
           "post": "Saw the {project} video? Here are the numbers: {price}{size}. WhatsApp us for the fact sheet.",
           "head_reel": "{kind} in {place}", "head_post": "{place}: price, size, distances",
           "rera": "MahaRERA {rera}.", "fact_end": "."},
    "mr": {"reel": "{hook}. {fact} MahaRERA {rera}: स्वतः तपासा. फॅक्ट शीटसाठी WhatsApp करा.",
           "reel_plain": "{hook}. {fact} फॅक्ट शीट आणि साइट व्हिजिटसाठी WhatsApp करा.",
           "post": "{project} चा व्हिडिओ पाहिला? आकडे इथे: {price}{size}. फॅक्ट शीटसाठी WhatsApp करा.",
           "head_reel": "{place} येथे {kind}", "head_post": "{place}: किंमत, आकार, अंतर",
           "rera": "MahaRERA {rera}.", "fact_end": "."},
    "hi": {"reel": "{hook}. {fact} MahaRERA {rera}: खुद जाँचिए. फैक्ट शीट के लिए WhatsApp कीजिए.",
           "reel_plain": "{hook}. {fact} फैक्ट शीट और साइट विज़िट के लिए WhatsApp कीजिए.",
           "post": "{project} का वीडियो देखा? आंकड़े यहाँ: {price}{size}. फैक्ट शीट के लिए WhatsApp कीजिए.",
           "head_reel": "{place} में {kind}", "head_post": "{place}: कीमत, साइज़, दूरी",
           "rera": "MahaRERA {rera}.", "fact_end": "."},
}
KIND_WORD = {"mr": {"plot": "प्लॉट", "home": "घर", "plots": "प्लॉट", "homes": "घरे"},
             "hi": {"plot": "प्लॉट", "home": "घर", "plots": "प्लॉट", "homes": "घर"}}


def _local(place: str, language: str) -> str:
    if language not in ("mr", "hi"):
        return place
    return ", ".join(i18n.PLACES.get(p.strip(), {}).get(language, p.strip()) for p in place.split(","))


def _cut(text: str, n: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n - 1].rsplit(" ", 1)[0].rstrip(",:;") + "…"


def ad_copy(f: Facts, hook: str, beats: List[dict], language: str, corpus: str) -> Dict[str, Any]:
    """{reel: {primary_text, headline}, post: {...}, cta}. A line that fails the guards falls back to a plain one."""
    t = COPY.get(language, COPY["en"])
    c = f.c
    place = _local(c.locality or f.place or "Pune", language)
    project = f.place or place
    kind = KIND_WORD.get(language, {}).get(f.kinds, f.kinds)
    fact = next((b["lines"][0] for b in beats if b["kind"] == "fact"), "")
    fact = (fact + t["fact_end"]) if fact else ""
    reel = (t["reel"] if f.rera else t["reel_plain"]).format(hook=hook, fact=fact, rera=f.rera)
    if len(reel) > PRIMARY_MAX:
        reel = (t["reel"] if f.rera else t["reel_plain"]).format(hook=hook, fact="", rera=f.rera)
    size = next((b["lines"][0] for b in beats if b["kind"] == "size"), "")
    price = (("from " if c.layout and language == "en" else "") + price_label(f.price)) if f.price else ""
    post = t["post"].format(project=project, price=price, size=(", " + size) if size else "")
    if len(post) > PRIMARY_MAX:
        post = t["post"].format(project=project, price=price, size="")
    if not f.price:
        post = post.replace(": , ", ": ").replace(": .", ".")
    out = {"reel": {"primary_text": _cut(reel, PRIMARY_MAX), "headline": _cut(t["head_reel"].format(kind=kind.capitalize() if language == "en" else kind, place=place), HEADLINE_MAX)},
           "post": {"primary_text": _cut(post, PRIMARY_MAX), "headline": _cut(t["head_post"].format(place=project), HEADLINE_MAX)},
           "cta": CTA}
    plain = {"en": "WhatsApp us for the fact sheet of {p}.", "mr": "{p} ची फॅक्ट शीट: WhatsApp करा.",
             "hi": "{p} की फैक्ट शीट: WhatsApp कीजिए."}.get(language, "WhatsApp us for the fact sheet of {p}.")
    full = corpus + "\n" + " ".join(_local(x, language) for x in (c.locality, c.project, c.v.get("city") or ""))
    for piece in ("reel", "post"):
        for k in ("primary_text", "headline"):
            if problems_in(out[piece][k], full, allow_url=True):
                log.info("boost copy %s.%s held: %s", piece, k, problems_in(out[piece][k], full, allow_url=True))
                out[piece][k] = _cut(plain.format(p=project), PRIMARY_MAX if k == "primary_text" else HEADLINE_MAX)
    return out


def check_beats(hook: str, beats: List[dict], corpus: str) -> List[dict]:
    """Beats whose main line passes the guards (the end card is code-written and kept); raises when the hook does not pass."""
    from app.modules.reels.listing_reel import _PUSHY
    if problems_in(hook, corpus) or _PUSHY.search(hook):
        raise ValueError(f"boost hook failed the checks: {problems_in(hook, corpus)}")
    keep = []
    for b in beats:
        main = b["lines"][0]
        if b["kind"] == "cta" or not (problems_in(" ".join(b["lines"]), corpus, allow_url=True) or _PUSHY.search(main)
                                      or _words(main) > BEAT_WORDS):
            keep.append(b)
    return keep


# ---- tracking --------------------------------------------------------------------------------------------------------------
async def link(db, listing_id: str, kind: str, agent_id: str, title: str, locality: str, now: datetime) -> dict:
    """The interest link (kind post, channel boost) of this boost piece, made once: {code, url}."""
    from app.modules.interest.service import site_url
    from app.modules.interest.store import Store
    store, r = Store(db), ref(listing_id, kind)
    doc = await store.find_link("post", r, CHANNEL)
    if not doc:
        doc = await store.insert_link({"kind": "post", "ref": r, "agent_id": agent_id, "channel": CHANNEL, "created_at": now,
                                       "sample": False, "title": title[:140], "locality": locality[:80], "subtitle": "",
                                       "image_url": ""})
    return {"code": doc["code"], "url": f"{site_url()}/i/{doc['code']}"}


def whatsapp_number(profile: Optional[dict]) -> Optional[str]:
    """Our public posts number (it routes the chat to the agent by its code), else the agent's own phone, as wa.me digits."""
    from .identity import posts_whatsapp_number
    num = posts_whatsapp_number()
    if num:
        return num
    p = profile or {}
    d = re.sub(r"\D", "", str(p.get("phone") or (p.get("branding_data") or {}).get("phone") or ""))
    if re.fullmatch(r"[6-9]\d{9}", d):
        d = "91" + d
    return d if 11 <= len(d) <= 15 else None


def prefill(project: str, locality: str, code: str) -> str:
    """The WhatsApp opening message; 'ref <code>' is what whatsapp.adapters.codes_in routes on."""
    what = " ".join(x for x in (project, locality) if x) or "this property"
    return f"Hi, I'm interested in {what} [ref {code}]"


# ---- the pair --------------------------------------------------------------------------------------------------------------
def key(facts: Dict[str, Fact], photos: Sequence[str], language: str) -> str:
    """What the boost pair is made from: changes when a fact it says or a picture it shows changes."""
    f = Facts(facts)
    hook, beats = reel_beats(f)
    text = "\n".join([hook, *(l for b in beats for l in b["lines"]), *(b.corpus() for _, b in carousel_briefs(f, hook, "none")),
                      language, *(Path(p).name for p in photos)])
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


async def make(db, *, facts: Dict[str, Fact], listing: dict, agent_id: str, out: Path, uploads_dir: Path, language: str,
               photos: Sequence[str], profile: Optional[dict] = None, brand_name: str = "", card_brand: Any = None,
               reel_renderer: Optional[Callable] = None, now: Callable[[], datetime] = datetime.utcnow) -> dict:
    """The boost pair as kept on the run (`boost`, state "ready"); raises on failure (the caller stores the error)."""
    uploads_dir, out = Path(uploads_dir), Path(out)
    rel = lambda p: "/uploads/" + Path(p).resolve().relative_to(uploads_dir.resolve()).as_posix()
    f = Facts(facts)
    hook, beats = reel_beats(f, brand_name)
    briefs = carousel_briefs(f, hook, photos[0] if photos else "none")
    if card_brand is not None:
        briefs = [(n, replace(b, card_brand=card_brand)) for n, b in briefs]
    corpus = "\n".join(b.corpus() for _, b in briefs)   # the facts only: the hook and beats are checked against it
    beats = check_beats(hook, beats, corpus)
    # carousel
    cards = await _cards(briefs, out / "carousel")
    if len(cards) < 3:
        raise ValueError("the boost carousel needs at least 3 cards")
    zipped = await asyncio.to_thread(_zip, cards, out / "carousel" / "boost-carousel.zip")
    # reel
    render = reel_renderer or default_reel_renderer
    scenes = reel_scenes(hook, beats, photos, (f.c.project or "").upper()[:28])
    res = await asyncio.to_thread(render, scenes, out / "reel" / "boost-reel.mp4")
    if res["seconds"] >= 29:
        raise ValueError("the boost reel is too long")
    # copy and links
    project, locality = f.c.project or listing.get("project_name") or "", f.c.locality or listing.get("locality") or ""
    copy = ad_copy(f, hook, beats, language, corpus)
    title = ", ".join(x for x in (project, locality) if x) or hook
    reel_link = await link(db, listing["_id"], "boost_reel", agent_id, title, locality, now())
    post_link = await link(db, listing["_id"], "boost_post", agent_id, title, locality, now())
    msg = prefill(project, locality, reel_link["code"])
    num = whatsapp_number(profile)
    return {"state": "ready", "error": None, "ready_at": None, "made_at": now(),
            "reel": {"video_url": rel(res["video"]), "poster_url": rel(res["poster"]) if Path(res["poster"]).is_file() else None,
                     "duration_s": res["seconds"]},
            "carousel": {"images": [rel(p) for p in cards], "zip_url": rel(zipped)},
            "copy": copy, "wa_prefill": msg, "wa_link": f"https://wa.me/{num}?text={quote(msg, safe='')}" if num else None,
            "tracked_link": reel_link["url"], "post_tracked_link": post_link["url"],
            "codes": {"reel": reel_link["code"], "post": post_link["code"]},
            "guide": guide(locality, str(f.c.v.get("taluka") or "")), "meta_open_url": META_OPEN_URL, "reel_permalink": None,
            "boosted_at": None, "daily_spend_inr": None, "days": None, "key": key(facts, photos, language)}


# ---- results ---------------------------------------------------------------------------------------------------------------
async def results(db, run: dict, items: List[dict], now: datetime) -> Dict[str, Any]:
    """{boost_results: {clicks, interests, spend_inr, cost_per_enquiry}, organic: {clicks, interests}}. Spend is the agent's
    stated daily spend times the days run so far (we do not read Meta's bill)."""
    from app.modules.interest.store import Store
    store, b = Store(db), run.get("boost") or {}
    clicks = interests = 0
    for code in (b.get("codes") or {}).values():
        if code:
            clicks += await store.count(code, "click")
            interests += await store.count(code, "interest")
    spend = 0
    if b.get("boosted_at") and b.get("daily_spend_inr"):
        at = b["boosted_at"].replace(tzinfo=None) if isinstance(b["boosted_at"], datetime) else now
        ran = min(int(b.get("days") or 0), max(1, (now - at).days + 1))
        spend = int(b["daily_spend_inr"]) * ran
    return {"boost_results": {"clicks": clicks, "interests": interests, "spend_inr": spend,
                              "cost_per_enquiry": round(spend / interests) if interests and spend else None},
            "organic": {"clicks": sum(i.get("clicks", 0) for i in items), "interests": sum(i.get("interests", 0) for i in items)}}
