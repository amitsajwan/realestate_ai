"""The only place where the calendar touches the creative and reels modules (they never import the calendar).

  entry_to_brief / make_pack     library entry -> creative Brief -> CreativePack (images + caption), for Instagram or Facebook
  agent_item_to_brief            the agent-attraction briefs (product benefits only, same claims as the library's agent posts)
  reel_item / render_reel / publish_reel   a short vertical video (tip, pitch) and its publication
  consented_projects / project_reel_caption   live projects of agents who consented to be featured, for the daily evening reel
  render_reel_for               also renders the daily reels: an area insight (area_reels) or an agent's project (agentprojects.reel)

Facts: a Brief carries only what the library entry itself says (its points, its body sentences, the claim in its `review` note).
creative's guards reject any number that is not in the Brief, any price, prediction, phone, URL, hype or filler, and replace the
offending field with its deterministic draft, so the LLM cannot add a fact.
"""
from app.core import brand
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

from app.modules.creative import make as _creative_make
from app.modules.creative import samples as _creative_samples
from app.modules.creative.models import Brief, CreativePack
from app.modules.reels import compose as _reel_compose
from app.modules.social import reel_publish as _reel_publish
from app.modules.reels import templates as _reel_templates
from app.platform.meta_graph.config import SocialConfig
from app.platform.meta_graph.publisher import PublishError, Result

from . import render as _cards
from .library import SITE, Entry

CHANNEL_OF = {"facebook_page": "facebook", "instagram": "instagram", "facebook": "facebook"}
REEL_DIR = "calendar/reels"
SLIDES_REEL_DIR = "calendar/slidereels"

# 2 to 4 words naming the subject; creative's hooks read "Do you really know your <short>?" and "What nobody tells you about <short>".
SHORT = {
    "myth-rera-means-safe": "RERA number", "myth-token-booking": "booking amount", "myth-stamp-on-price": "stamp duty",
    "myth-cc-means-move-in": "commencement certificate", "myth-uc-always-cheaper": "under-construction homes", "myth-near-metro": "metro distance",
    "myth-rent-is-waste": "rent", "carpet-under-rera": "carpet area", "cost-sheet-decoded": "cost sheet", "read-your-agreement": "agreement for sale",
    "read-a-rera-page": "MahaRERA page", "loan-eligibility-basics": "home loan eligibility", "registration-steps": "registration day",
    "possession-and-oc": "possession and OC", "defect-liability-5yrs": "defect window", "rera-70-percent-account": "RERA project account",
    "payment-plan-milestones": "payment plan", "water-and-power-questions": "water and power", "commute-test-3-runs": "commute",
    "society-and-maintenance": "maintenance charges", "questions-for-agent": "agent questions", "red-flags-in-ads": "property ads",
    "resale-vs-new": "resale or new", "documents-before-booking": "booking documents", "rainy-day-visit": "monsoon visit",
    "possession-day-snag-list": "possession day", "monthly-outgoings": "monthly costs", "poll-near-office-vs-space": "commute vs space",
    "poll-ready-vs-uc": "ready or under construction", "poll-top-priority": "top priority", "poll-wfh-room": "work-from-home room",
    "poll-metro-pay-more": "metro premium", "local-10-minute-test": "neighbourhood", "local-sunday-vs-monday": "area visit",
    "local-evening-walk": "evening walk", "agent-consistent-posting": "posting", "agent-buyer-summary": "buyer enquiries",
    "agent-hindi": "agent posting", "agent-marathi": "agent posting",
}

# One hand-written hook per entry (2 to 9 words, nothing the entry does not say), used when the strategist has no LLM idea of its own.
HOOK = {
    "myth-rera-means-safe": "A RERA number is where checking starts", "myth-token-booking": "Before you pay that booking amount, read this",
    "myth-stamp-on-price": "Is stamp duty really on the price?", "myth-cc-means-move-in": "Commencement or occupancy certificate? Know the difference",
    "myth-uc-always-cheaper": "Is under construction really the smarter buy?", "myth-near-metro": "An approved metro line is not a running metro",
    "myth-rent-is-waste": "Is rent really money thrown away?", "carpet-under-rera": "What really counts as carpet area",
    "cost-sheet-decoded": "Read your cost sheet before the price", "read-your-agreement": "Find these five things before you sign",
    "read-a-rera-page": "How to read a project's MahaRERA page", "loan-eligibility-basics": "What a lender checks before approving your loan",
    "registration-steps": "Registration day, step by step", "possession-and-oc": "The OC first, then the keys",
    "defect-liability-5yrs": "Found a defect after moving in? Know your rights", "rera-70-percent-account": "Where does your money go after you pay?",
    "payment-plan-milestones": "Pay against progress, not against pressure", "water-and-power-questions": "Ask these water and power questions before booking",
    "commute-test-3-runs": "Test the commute three times before you buy", "society-and-maintenance": "Ask about maintenance before you book",
    "questions-for-agent": "Questions to ask your property agent", "red-flags-in-ads": "Red flags to spot in a property ad",
    "resale-vs-new": "Resale or new? Check these first", "documents-before-booking": "Documents to see before you pay anything",
    "rainy-day-visit": "Visit the flat once when it rains", "possession-day-snag-list": "Your possession-day snag list",
    "monthly-outgoings": "What a home costs beyond the EMI", "poll-near-office-vs-space": "Near the office, or more space?",
    "poll-ready-vs-uc": "Ready to move or under construction?", "poll-top-priority": "One thing you would never compromise on?",
    "poll-wfh-room": "Work-from-home room or bigger living room?", "poll-metro-pay-more": "Would you pay extra for a planned metro?",
    "local-10-minute-test": "What should be within ten minutes of home?", "local-sunday-vs-monday": "Visit on a Sunday, then on a Monday",
    "local-evening-walk": "Take an evening walk before you book", "agent-consistent-posting": "Too busy showing flats to keep posting?",
    "agent-buyer-summary": "Which enquiry is serious? Know at a glance",
}

# (myth, truth) in the entry's own words, short enough for the myth_fact layout.
MYTH_FACT = {
    "myth-rera-means-safe": ("It has a RERA number, so I can relax", "It gives you information and rights. Read the page yourself."),
    "myth-token-booking": ("The booking amount is just a small token", "RERA caps advances at 10% of the cost without a registered agreement."),
    "myth-stamp-on-price": ("Stamp duty is on the price I pay", "Maharashtra charges on the higher of agreement value and ready reckoner value."),
    "myth-cc-means-move-in": ("A commencement certificate means I can move in", "CC is permission to start building. The OC says it is ready to occupy."),
    "myth-uc-always-cheaper": ("Under construction is always the smarter buy", "It can cost less to enter, but you wait."),
    "myth-near-metro": ("A planned metro line means a metro nearby", "Approved is not the same as running. Approved lines take years to build."),
    "myth-rent-is-waste": ("Rent is money thrown away", "Rent buys flexibility. Buying adds EMI, maintenance, tax and repairs."),
}

# Entries with one number that is stated in their own text: (value, label, tip).
STAT = {
    "registration-steps": ("4 months", "to present your document for registration", "Present the document within four months of signing."),
    "rera-70-percent-account": ("70%", "of buyer payments go into a separate project account", "Withdrawals follow the project's progress."),
    "defect-liability-5yrs": ("5 years", "to report defects after possession", "Report defects in writing and keep dated photos and emails."),
    "token-booking-cap": ("10%", "RERA cap on advances before a registered agreement", "Ask to see the agreement before paying more."),
    "possession-and-oc": ("2 months", "to take possession after the OC under RERA", "Inspect the flat against the agreement."),
}
STAT["myth-token-booking"] = STAT.pop("token-booking-cap")
STAT_SLUGS = tuple(STAT)

DARK_PHOTOS = ("tower-low", "glass-dusk")
_EMOJI = re.compile(r"^[^\w\"“(]+", re.U)
_NUM = re.compile(r"^\s*\d+[.)]\s*")


def _clean(line: str) -> str:
    return _EMOJI.sub("", line.strip()).strip()


def _points(entry: Entry) -> List[str]:
    out = []
    for p in entry.points:
        p = _NUM.sub("", p).strip()
        if p.lower().startswith(("myth:", "fact:")):
            p = p.split(":", 1)[1].strip()
            p = p[:1].upper() + p[1:]
        elif p.lower().startswith("comment "):
            p = ""
        if p:
            out.append(p)
    return out


def _facts(entry: Entry) -> List[str]:
    """Statements taken from the entry itself: its points, the sentences of its body, and the claim written in its review note."""
    facts = _points(entry)
    paras = [_clean(p) for p in entry.body.split("\n\n")]
    for para in paras[1:-1]:
        for sent in re.split(r"(?<=[.!?])\s+", para):
            s = sent.strip()
            if 3 <= len(s.split()) <= 40 and not s.endswith("?") and "\n" not in s and not s.startswith(("1", "2", "3", "4")):
                facts.append(s)
    m = re.match(r"(?:Claim|Verified[^:]*):\s*([^.]+)", entry.review)
    if m:
        facts.append(m.group(1).strip())
    seen, uniq = set(), []
    for f in facts:
        if f.lower() not in seen:
            seen.add(f.lower())
            uniq.append(f)
    return uniq


def entry_to_brief(entry: Entry, prefer: str = "", channel: str = "instagram") -> Brief:
    """A creative Brief from one library entry. Nothing is added: structure is cut out of the entry's own points."""
    pts = _points(entry)
    title = entry.title.strip().strip('"“”')
    b = Brief(topic=title, short=SHORT.get(entry.slug, ""), facts=_facts(entry), steps=pts if len(pts) >= 3 else [], tip=pts[-1] if pts else "",
              link=f"{SITE}{entry.link}" if entry.link else "", hashtags=list(entry.tags))
    if entry.pillar != "agent":  # the dark bundled photos keep the headline legible (the light ones greyed it out in review)
        b.photo = DARK_PHOTOS[sum(map(ord, entry.slug)) % len(DARK_PHOTOS)]
    if entry.slug in HOOK:
        b.hooks = {p: HOOK[entry.slug] for p in ("mistake", "nobody", "question")}
    if entry.pillar == "myth" and entry.slug in MYTH_FACT:
        b.myth, b.truth = MYTH_FACT[entry.slug]
        b.prefer = "myth-vs-fact"
        b.tip = pts[-1] if pts else ""
    elif entry.pillar == "poll":
        raw = [_NUM.sub("", p) for p in entry.points if _NUM.match(p)]
        b.question = title if title.endswith("?") else title + "?"
        if len(raw) == 2:
            b.options = [r.split(":")[0].strip() for r in raw]
            b.prefer = "poll"
        else:
            b.options, b.steps, b.prefer = [], [], "single"
            b.facts = raw + b.facts
        b.tip = "Comment your pick below."
    elif entry.pillar in ("checklist", "local"):
        b.prefer = "carousel"
        b.steps = [p for p in pts if len(p.split()) <= 14]
    elif entry.pillar == "agent":
        b.prefer = "single"
        b.steps = []
    else:  # explainer
        b.prefer = "carousel"
    if entry.slug in STAT:
        b.stat_value, b.stat_label, b.tip = STAT[entry.slug]
    if prefer:
        b.prefer = prefer
    if channel in ("facebook", "facebook_page") and b.prefer in ("carousel", "checklist"):
        b.prefer = "single"  # a Facebook post carries one image: the cover alone would only be a hook
    return b


def agent_brief(spec: Brief, audience_slug: str = "") -> Brief:
    spec.link = spec.link or f"{SITE}/request-invite"
    return spec


def agent_items() -> List[Dict]:
    """The pool of agent-attraction posts that are not library entries: (slug, Brief). Product claims only (the same as the library's agent posts and the
    creative samples: comments become lead cards with BHK, budget and timing)."""
    briefs = _creative_samples.agent_briefs()
    slugs = ["agent-lead-cards", "agent-post-to-lead", "agent-comment-not-lead", "agent-notebook-vs-cards", "agent-three-details", "agent-poll-tracking"]
    hooks = ["Still copying buyer comments into a notebook?", "From one listing post to a ready lead", "Is every comment really a lead?",
             "Notebook chaos or ready lead cards?", "3 details on every lead before you reply", "How do you track buyer comments today?"]
    out = []
    for s, b, h in zip(slugs, briefs, hooks):
        b.hooks = {p: h for p in ("mistake", "nobody", "question")}
        out.append({"slug": s, "brief": agent_brief(b)})
    return out


AGENT_POOL = {a["slug"]: a for a in agent_items()}


def _is_local_card(entry: Entry) -> bool:
    return bool(entry.card_from)


async def make_pack(entry: Entry, channel: str, llm=None, recent_layouts: Sequence[str] = (), out_dir: Optional[Path] = None, seed: int = 0,
                    prefer: str = "", llm_critic: bool = False) -> CreativePack:
    """Creative pack for a library entry. Instagram 1080x1350, Facebook 1080x1080. Hindi/Marathi entries keep their pre-rendered card and caption."""
    ch = CHANNEL_OF[channel]
    if _is_local_card(entry):
        out = Path(out_dir) if out_dir else Path("uploads/calendar")
        path = _cards.render_entry(entry, out, "instagram" if ch == "instagram" else "facebook_page")
        cap = entry.ig_caption if ch == "instagram" else entry.fb_caption
        return CreativePack(channel=ch, audience="agent", images=[str(path)], caption=cap, hashtags=list(entry.tags),
                            design={"layout": "static_card", "format": "single", "palette": "brand"}, report={"ok": True, "problems": []}, used_llm=False)
    brief = entry_to_brief(entry, prefer, channel)
    audience = "agent" if entry.pillar == "agent" else "buyer"
    return await _creative_make(brief, audience, ch, llm, seed=seed, recent_layouts=list(recent_layouts), out_dir=out_dir, llm_critic=llm_critic)


async def make_agent_pack(slug: str, channel: str, llm=None, recent_layouts: Sequence[str] = (), out_dir: Optional[Path] = None, seed: int = 0,
                          prefer: str = "") -> CreativePack:
    b = AGENT_POOL[slug]["brief"]
    if prefer:
        b = Brief(**{**b.__dict__, "prefer": prefer})
    return await _creative_make(b, "agent", CHANNEL_OF[channel], llm, seed=seed, recent_layouts=list(recent_layouts), out_dir=out_dir)


# ---- reels --------------------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ReelSpec:
    template: str                 # tip | pitch
    key: str                      # file stem, shared by the Instagram and the Facebook row
    ref: str                      # entry slug (tip) or "" (pitch)


PITCH_CAPTION_BODY = ("\U0001F91D Property agent in Pune?\n\nBuyers message all day, and the same questions come back every time.\n\n"
                      "✅ Post a property from your phone\n✅ Ready-made posts for Facebook, Instagram and WhatsApp\n✅ Your own website is ready\n\n"
                      "Claim your free trial: 1 month free, every property. \U0001F4E4 Know an agent who would like this? Share this reel.")


def reel_caption(spec: ReelSpec, channel: str, entry: Optional[Entry] = None) -> str:
    if spec.template == "tip" and entry is not None:
        return entry.ig_caption if channel == "instagram" else entry.fb_caption
    tags = "#PuneAgents #RealEstateAgent #PuneRealEstate"
    if channel == "instagram":
        return PITCH_CAPTION_BODY + "\n\nRequest your invite: link in our bio.\n\n" + tags + " " + brand.HASHTAG
    return PITCH_CAPTION_BODY + f"\n\n\U0001F517 {SITE}/request-invite\n\n{brand.HASHTAG} {tags}"


def reel_scenes(spec: ReelSpec, entry: Optional[Entry] = None):
    t = _reel_templates
    if spec.template == "tip":
        if entry is None:
            raise ValueError("a tip reel needs a library entry")
        pts = _points(entry)[:3]
        from app.modules.creative.layouts.base import PHOTO_DIR
        photos = [PHOTO_DIR / f"{k}.jpg" for k in DARK_PHOTOS + ("living-room",) if (PHOTO_DIR / f"{k}.jpg").is_file()]
        return t.tip_reel([entry.title.strip('"')] + pts + ["Save this for when you need it."], images=photos or None, seed=spec.key)
    return t.agent_pitch(problem="Buyers message you all day. *Same* questions. Every time.",
                         solution="Post a property from your phone. Your own website is *ready*.",
                         proof=("Ready-made posts for social", "Free trial: 1 month free"), cta="Claim your free trial.")


def render_reel(spec: ReelSpec, uploads: Path, entry: Optional[Entry] = None, composer: Optional[Callable] = None) -> str:
    """Render the mp4 for `spec` to <uploads>/calendar/reels/<key>.mp4 (about a minute) and return its path relative to uploads."""
    rel = f"{REEL_DIR}/{spec.key}.mp4"
    dest = Path(uploads) / rel
    if dest.is_file() and dest.stat().st_size > 0:
        return rel
    scenes, options = reel_scenes(spec, entry)
    (composer or _reel_compose.make_reel)(scenes, dest, **options)
    return rel


def spec_of(doc: dict) -> ReelSpec:
    c = doc.get("creative") or {}
    return ReelSpec(c.get("template", "tip"), c.get("reel_key") or doc["slug"], c.get("ref", ""))


def video_info(rel: str, uploads: Path) -> Dict:
    """{duration_s, render} of a rendered video (relative to uploads), for the row's tags; {} when it cannot be read."""
    try:
        from app.modules.reels import ffmpeg as _ffmpeg
        return {"duration_s": round(_ffmpeg.probe(Path(uploads) / rel).duration, 1), "render": _reel_compose.RENDER_VERSION}
    except Exception:
        return {}


def render_reel_for(doc: dict, uploads: Path) -> str:
    """Runner hook: render the reel behind a calendar row."""
    from .library import BY_SLUG
    c = doc.get("creative") or {}
    if c.get("template") in ("area", "project", "puzzle", "delay"):
        return _render_daily(doc, Path(uploads))
    if c.get("template") == "agent":
        return render_agent_reel(doc, Path(uploads))
    if c.get("template") == "guide":
        from .guide_reels import render_row
        return render_row(doc, Path(uploads))
    spec = spec_of(doc)
    return render_reel(spec, uploads, BY_SLUG.get(spec.ref))


def render_agent_reel(doc: dict, uploads: Path, composer: Optional[Callable] = None) -> str:
    """An agent-recruitment reel by its code (A1..D2: reels.agent_reels; E1..: reels.transform_reels; F1..: reels.flow_reels); the Instagram and Facebook rows share one file."""
    from app.modules.reels import agent_reels, flow_reels, transform_reels
    c = doc.get("creative") or {}
    rel = f"{REEL_DIR}/{c.get('reel_key') or doc['slug']}.mp4"
    dest = uploads / rel
    if not (dest.is_file() and dest.stat().st_size > 0):
        code = c["reel_code"]
        mod = flow_reels if code in flow_reels.BY_CODE else transform_reels if code in transform_reels.BY_CODE else agent_reels
        mod.render(code, dest, composer)
    return rel


def _render_daily(doc: dict, uploads: Path, composer: Optional[Callable] = None) -> str:
    """An area insight plays its checked slides (stored with the row); a project reel is drawn from the project record and agent
    name stored with the row when it was planned (the same facts the owner approved)."""
    c = doc.get("creative") or {}
    rel = f"{REEL_DIR}/{c.get('reel_key') or doc['slug']}.mp4"
    dest = uploads / rel
    if dest.is_file() and dest.stat().st_size > 0:
        return rel
    if c["template"] in ("area", "puzzle", "delay"):  # all play their checked slides
        from . import area_reels
        (composer or area_reels.render_video)([uploads / p for p in c.get("slides") or doc.get("images") or []], dest)
    else:
        from app.modules.agentprojects import reel as _project_reel
        (composer or _project_reel.render)(c["project"], c["agent"], dest)
    return rel


# ---- the daily evening reel: an agent's real project, only with the agent's consent ------------------------------------------------------
async def consented_projects(db) -> List[Dict]:
    """Live, MahaRERA-checked projects of agents whose concierge record says consent.given is True and whose public site is
    indexable (public, not the demo, not an unpublished preview). Consent is read every time a plan is made, so a revoked
    consent (House Deal: given=False) stops new rows at once. Returns [{slug, agent_id, area, project, agent, agent_slug}]."""
    from app.core import areas as core_areas
    from app.modules.agentprojects.service import COLLECTION, _agent_name, indexable, public_view
    agents = await db.get_collection("concierge_agents").find({}).to_list(None)
    ok = {str(a["_id"]) for a in agents if (a.get("consent") or {}).get("given") is True}
    if not ok:
        return []
    profiles = {str(p["agent_id"]): p for p in await db.get_collection("agent_public_profiles").find({}).to_list(None)
                if str(p.get("agent_id")) in ok and indexable(p)}
    out = []
    docs = await db.get_collection(COLLECTION).find({}).to_list(None)
    for d in sorted(docs, key=lambda d: (str(d.get("agent_id")), d.get("order") or 0, d.get("slug", ""))):
        prof = profiles.get(str(d.get("agent_id")))
        if not prof or d.get("status") != "live" or not d.get("rera") or not d.get("configurations"):
            continue
        p = public_view(d)
        named = core_areas.named_in(p.get("locality") or "")
        out.append({"slug": d["slug"], "agent_id": str(d["agent_id"]), "area": named[0].key if named else "", "project": p,
                    "agent": {"name": _agent_name(prof)}, "agent_slug": prof.get("slug", "")})
    return out


def project_reel_caption(p: dict, agent: dict, channel: str, agent_slug: str = "") -> str:
    """The project's facts as the agent quoted them and MahaRERA filed them, with the read date; no phone number (interest links
    and comments reach the agent)."""
    from app.modules.agentprojects.cards import bhk_range, day, price_range
    r = p.get("rera") or {}
    page = f"{SITE}/projects/{p.get('catalog_slug') or p['slug']}"
    lines = [f"{p['name']}, {p['locality']}: {price_range(p)}, {bhk_range(p.get('bhk_options') or [])}.",
             f"MahaRERA {p['rera_no']}: completion date filed {day(r.get('completion_now'))}"
             + (f", {p['booked_pct']}% of {r.get('units_total')} homes booked" if p.get("booked_pct") is not None else "")
             + (f" (read on {day(r.get('checked_at'))})." if r.get("checked_at") else "."),
             f"Builder's target: {day(p.get('possession_target'))}. Plan around the MahaRERA date." if p.get("possession_target") else "",
             f"Prices as quoted by {agent['name']}; confirm before booking. Listed by {agent['name']}.",
             "Comment PRICE for the prices on your floor.",
             "Every fact with its source: link in our bio." if channel == "instagram" else f"Every fact with its source: {page}",
             "#Pune #" + p["locality"].replace(" ", "") + " #MahaRERA"]
    return "\n\n".join(x for x in lines if x)


def project_reel_script(p: dict, agent: dict) -> List[str]:
    from app.modules.agentprojects import reel as _project_reel
    return [l if isinstance(l, str) else l.text for s in _project_reel.scenes(p, agent) for l in s.lines]


def render_slides_reel_for(doc: dict, uploads: Path) -> str:
    """Runner hook: the Reel made from a carousel post's slides (its Facebook copy), rendered once to
    <uploads>/calendar/slidereels/<row id>.mp4; returns the path relative to uploads."""
    from app.modules.reels.slides import make_slides_reel
    rel = f"{SLIDES_REEL_DIR}/{doc['_id']}.mp4"
    dest = Path(uploads) / rel
    if not (dest.is_file() and dest.stat().st_size > 0):
        imgs = list(doc.get("images") or [])
        # the reel opens on the post's hook line (the creative's hook, else the caption's first line) in big type
        hook = (doc.get("creative") or {}).get("hook") or doc.get("caption")
        make_slides_reel([Path(uploads) / p for p in imgs], dest, hook=hook)
    return rel


async def publish_reel(doc: dict, social: SocialConfig, uploads: Path, name: Optional[str] = None) -> Result:
    """Stage the video under uploads/reels and publish it as an Instagram Reel or a Facebook Page Reel (dry run: no network).
    `name` is the staged file name (default: the reel's key)."""
    mp4 = Path(uploads) / doc["video"]
    if not social.dry_run and not mp4.is_file():
        raise PublishError("the reel video is missing")
    if social.dry_run:
        return await _reel_publish.publish_reel(doc["channel"], "https://dry.run/reel.mp4", doc["caption"], cfg=social)
    name = _reel_publish.stage(mp4, Path(uploads), name or f"{spec_of(doc).key}.mp4")
    url = _reel_publish.public_url(social, name)
    extra = {}
    if doc["channel"] == "instagram":  # the hook still rendered next to the mp4, when there is one, as the reel's cover
        cover = _reel_publish.staged_cover_url(social, mp4, Path(uploads), name)
        if cover:
            extra["cover_url"] = cover
        from .reach import location_id
        if location_id(doc):
            extra["location_id"] = location_id(doc)
    return await _reel_publish.publish_reel(doc["channel"], url, doc["caption"], cfg=social, file_path=mp4, **extra)


# ---- interest links, footer and the link-in-bio hub ----------------------------------------------------------------------------------------
def _owner_agent() -> str:
    import os
    return os.environ.get("INTEREST_OWNER_AGENT_ID") or os.environ.get("ENGAGE_OWNER_AGENT_ID") or ""


def whatsapp_lines(caption: str, code: str, channel: str) -> str:
    """The caption's contact lines made trackable: an agent's own phone line ('📞 ...') is dropped, and the WhatsApp line ('💬 ...')
    becomes our number with this post's code, so the chat reaches our bot, which routes it to the agent and counts the lead for this
    post (whatsapp.adapters.codes_in reads 'interested in <code>'). Facebook gets a tap-to-chat link; Instagram captions cannot
    link, so it says what to send. Without our number configured the WhatsApp line is dropped and the interest link remains."""
    from urllib.parse import quote

    from app.modules.propertyfacts.identity import WA_MARK, phone_label, posts_whatsapp_number
    num = posts_whatsapp_number()
    line = ""
    if num:
        line = (f"{WA_MARK} WhatsApp: https://wa.me/{num}?text={quote(f'Hi, I am interested in {code}')}" if channel == "facebook"
                else f"{WA_MARK} WhatsApp {phone_label('+' + num)} and send: interested in {code}")
    out = []
    for ln in caption.splitlines():
        s = ln.strip()
        if s.startswith("\U0001F4DE"):
            continue
        if s.startswith(WA_MARK):
            if not line:
                continue
            ln = line
        out.append(ln)
    return "\n".join(out)


async def _listing_shown(db, doc: dict) -> dict:
    """For a post about one listing: what its interest page shows (the listing's first photo, its price, its own page),
    so a buyer who taps through sees the home from the post. {} for any other post."""
    if not doc.get("listing_id"):
        return {}
    from app.modules.interest.service import site_url
    from app.modules.creative.listing_brief import price_label
    listing = await db.get_collection("listings").find_one({"_id": doc["listing_id"]})
    if not listing:
        return {}
    prof = await db.get_collection("agent_public_profiles").find_one({"agent_id": listing.get("agent_id")}) or {}
    page = f"{site_url()}/agent/{prof['slug']}/listings/{listing['_id']}" if prof.get("slug") else f"{site_url()}/listings/{listing['_id']}"
    imgs = sorted([m for m in listing.get("media") or [] if isinstance(m, dict) and m.get("kind", "image") == "image" and m.get("url")],
                  key=lambda m: m.get("order") or 0)
    price = listing.get("price_inr")
    sub = ""
    if isinstance(price, int) and price > 0:   # a starting price ("... onwards" in the title) is never shown as a flat price
        sub = f"from {price_label(price)} onwards" if "onwards" in (listing.get("title") or "").lower() else price_label(price)
    return {"page_url": page, "image_url": imgs[0]["url"] if imgs else "", "subtitle": sub, "locality": listing.get("locality") or ""}


# The search line (docs/plan/reach-captions.md): what the home is, where and for how much, right under the headline, so it is in the
# ~125 characters shown before "more" and in the words Instagram search reads. From the listing record only.
_KIND_WORDS = {"en": {"apartment": "flat", "flat": "flat", "plot": "plot", "villa": "villa", "house": "house", "commercial": "commercial space",
                      "office": "office", "shop": "shop"},
               "mr": {"apartment": "फ्लॅट", "flat": "फ्लॅट", "plot": "प्लॉट", "villa": "व्हिला", "house": "घर", "commercial": "व्यावसायिक जागा",
                      "office": "ऑफिस", "shop": "दुकान"},
               "hi": {"apartment": "फ्लैट", "flat": "फ्लैट", "plot": "प्लॉट", "villa": "विला", "house": "मकान", "commercial": "कमर्शियल जगह",
                      "office": "ऑफिस", "shop": "दुकान"}}
_SEARCH_LINE = {"en": {"sale": "📍 {what} for sale in {where} · {price}", "rent": "📍 {what} for rent in {where} · {price}"},
                "mr": {"sale": "📍 {where} येथे {what} विक्रीसाठी · {price}", "rent": "📍 {where} येथे {what} भाड्याने · {price}"},
                "hi": {"sale": "📍 {where} में {what} बिक्री के लिए · {price}", "rent": "📍 {where} में {what} किराये पर · {price}"}}
_FROM = {"en": "from {p} onwards", "mr": "{p} पासून पुढे", "hi": "{p} से शुरू"}
_PUNE = {"en": "Pune", "mr": "पुणे", "hi": "पुणे"}


def search_line(listing: dict, language: str = "en") -> str:
    """'📍 2 BHK flat for sale in Wagholi, Pune · ₹85 lakh' in the post's language; '' when the listing lacks the place or the price."""
    from app.modules.creative import i18n
    from app.modules.creative.listing_brief import price_label
    lang = language if language in _SEARCH_LINE else "en"
    price, loc = listing.get("price_inr"), str(listing.get("locality") or "").strip()
    if not isinstance(price, (int, float)) or price <= 0 or not loc:
        return ""
    tx = "rent" if listing.get("transaction") == "rent" else "sale"
    p = price_label(int(price), tx)
    if tx == "sale" and "onwards" in str(listing.get("title") or "").lower():   # a starting price is never shown as a flat price
        p = _FROM[lang].format(p=p)
    if lang != "en":
        p = i18n.money(p, lang).replace("a month", "/ महिना" if lang == "mr" else "/ महीना")
    kind = str(listing.get("property_type") or "").lower()
    what = _KIND_WORDS[lang].get(kind, _KIND_WORDS[lang]["apartment"] if listing.get("bhk") else "")
    bhk = listing.get("bhk")
    if bhk and kind in ("", "apartment", "flat", "villa", "house"):
        what = f"{bhk:g} BHK {what}".strip()
    if not what:
        return ""
    place = i18n.PLACES.get(loc, {}).get(lang, loc) if lang != "en" else loc
    return _SEARCH_LINE[lang][tx].format(what=what, where=f"{place}, {_PUNE[lang]}", price=p)


def with_search_line(caption: str, line: str, place: str = "") -> str:
    """The line right after the caption's first line; unchanged when there is no line, it is already there, or the first line already
    names both the place and a price (a price-reveal headline says it already)."""
    if not line or line in caption:
        return caption
    first, _, rest = caption.partition("\n")
    if "₹" in first and place and place.lower() in first.lower():
        return caption
    return f"{first}\n{line}\n{rest}" if rest else f"{first}\n{line}"


async def _search_line_for(db, doc: dict, language: str) -> str:
    if not doc.get("listing_id"):
        return ""
    listing = await db.get_collection("listings").find_one({"_id": doc["listing_id"]}, {"price_inr": 1, "locality": 1, "transaction": 1,
                                                                                       "title": 1, "property_type": 1, "bhk": 1,
                                                                                       "is_sample": 1, "sample": 1})
    if not listing or listing.get("is_sample") or listing.get("sample"):
        return ""
    return search_line(listing, language)


async def with_interest(db, doc: dict) -> dict:
    """The row with its caption ready to publish: a tap-to-show-interest line (a real link on Facebook, 'link in our bio' on Instagram,
    whose bio link is the /go hub) and the standard footer. Any failure returns the row unchanged: a post never waits on this."""
    try:
        from app.modules.interest.service import interest_url
        from .footer import with_footer
        channel = "instagram" if doc["channel"] == "instagram" else "facebook"
        from .reach import audience
        if audience(doc) == "agents":  # recruitment posts carry their own free-trial link and comment keyword, not a buyer interest link
            return {**doc, "caption": with_footer(doc["caption"], channel)}
        agent = doc.get("agent_id") or _owner_agent()  # an agent's own post (agentprojects) sends interest to that agent
        caption = doc["caption"]
        if agent:
            kind = "post"
            shown = await _listing_shown(db, doc)
            url = await interest_url(db, kind=kind, ref=doc["slug"], agent_id=agent, channel=channel,
                                     title=(caption.splitlines() or [""])[0][:140], **shown)
            if shown.get("page_url"):  # the agent's site line points at this listing, not the agent's home page
                caption = re.sub(r"(\U0001F3E0[^\n]*?)\b(?:https?://)?[\w.-]+/agent/[\w-]+/?(?=\s|$)",
                                 lambda m: m.group(1) + shown["page_url"].split("://", 1)[-1], caption)
            if "link in our bio" not in caption and channel == "instagram":
                line = "👉 Interested? Tap the link in our bio and press 'I am interested'."
            elif channel == "facebook":
                line = f"👉 Interested? One tap tells us: {url}"
            else:
                line = ""
            if line and line not in caption:
                caption = caption.rstrip() + "\n\n" + line
            caption = whatsapp_lines(caption, url.rsplit("/", 1)[-1], channel)
        from .reach import locality
        language = str((doc.get("tags") or {}).get("language") or (doc.get("creative") or {}).get("language") or "en")
        place = locality(doc)[0]
        try:   # the search line is a help, never a reason to hold a post
            caption = with_search_line(caption, await _search_line_for(db, doc, language), place)
        except Exception:
            pass
        if language in ("mr", "hi"):
            from app.modules.creative import i18n
            place = i18n.PLACES.get(place, {}).get(language, place)
        return {**doc, "caption": with_footer(caption, channel, key=str(doc.get("slug") or doc.get("_id") or ""), place=place,
                                              language=language)}
    except Exception:
        return doc


async def register_hub(db, doc: dict, permalink: str = "") -> None:
    """Best effort: show a published post or home on the /go link-in-bio hub."""
    try:
        if doc.get("kind") == "reel" or not (doc.get("images") or doc.get("image_path")):
            return
        from app.modules.interest.service import interest_url, upsert_hub_item
        import os
        agent = _owner_agent()
        if not agent:
            return
        kind = "post"
        channel = "instagram" if doc["channel"] == "instagram" else "facebook"
        url = await interest_url(db, kind=kind, ref=doc["slug"], agent_id=agent, channel=channel)
        code = url.rsplit("/", 1)[-1]
        first = (doc.get("images") or [doc.get("image_path")])[0]
        base = os.environ.get("PUBLIC_MEDIA_BASE_URL", "").rstrip("/")
        await upsert_hub_item(db, kind, doc["slug"], (doc["caption"].splitlines() or [""])[0][:140], f"{base}/uploads/{first}" if base else "",
                              "", code, permalink or "")
    except Exception:
        return


INTEREST_LINK = re.compile(r"https?://\S+/i/[a-z0-9]{4,12}\b")


def link_comment_text(caption: str) -> Optional[str]:
    """The Page's own first comment under a Facebook reel: the post's interest link, which is tappable in a comment (a reel's
    description link often is not). None when the caption carries no interest link (e.g. recruitment posts)."""
    found = INTEREST_LINK.search(caption or "")
    return f"Interested? Details in one tap: {found.group(0)}" if found else None


async def link_comment(db, doc: dict, object_id: str, social: SocialConfig) -> None:
    """Best effort, once per calendar row: a failure is logged and never fails or repeats the post. CALENDAR_REEL_LINK_COMMENT=off
    turns it off."""
    import logging
    import os
    from app.modules.social.distribution import page_comment, send
    log = logging.getLogger(__name__)
    text = link_comment_text(doc.get("caption", ""))
    if not text or not object_id or os.environ.get("CALENDAR_REEL_LINK_COMMENT", "").lower() in ("off", "false", "0"):
        return
    try:
        async def post() -> Result:
            return Result(await page_comment(social, object_id, text))
        await send(db, f"calendar-comment:{doc['_id']}", post)
    except Exception as e:
        log.warning("calendar: link comment on %s failed: %s", doc.get("slug"), type(e).__name__ if not isinstance(e, PublishError) else e)
