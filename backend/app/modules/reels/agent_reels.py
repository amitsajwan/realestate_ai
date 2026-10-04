"""Agent reels: 10 to 15 second Reels that recruit Pune property agents (not buyers). One reel = one message, in five scenes:

  HOOK (about 2 s, no logo: the viewer's problem, "for Pune property agents" on frame one) -> PAIN -> PRODUCT (a real Avasetu
  screen in a phone, sample data) -> RESULT -> CTA ("Comment AGENT": the comment assistant answers with the pilot link).

The ten scripts below are the first experiment (docs/plan/agent-reels.md): 3 pain, 3 product demo, 2 before/after, 2 result.
They are written and reviewed by people, not by the LLM, and `check_script` keeps them to what the product really does:
no time claims ("in seconds": a listing reel takes minutes to render), no "publish/auto-post" (we prepare the posts, the agent
shares them; posting from an agent's own Page needs Meta review), no invented numbers, no 24/7. On-screen text is Hinglish in
Roman letters (the renderer cannot shape Devanagari); `*word*` is drawn in gold.

Every reel has a code (A1..D2). It goes into the caption link (?src=reel_<code>_fb) and the calendar row, so a sign-up can be
traced back to the reel that brought it (scripts/agent_reels.py report).
"""
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from app.core import brand
from app.modules.marketing.images import brand_background

from .compose import H, W, Scene, TextLine, make_reel

SCREENS = Path(__file__).resolve().parent / "assets" / "screens"
CTA_WORD = "AGENT"
GROUPS = ("pain", "demo", "before_after", "result")
HOOK_SECONDS, PAIN_SECONDS, SCREEN_SECONDS, RESULT_SECONDS, CTA_SECONDS = 2.0, 2.4, 3.4, 2.4, 2.8
XFADE = 0.4
KICKER = "Pune property agents"
PILOT_PATH = "/pilot"

# Sample data on the screenshots that must not appear in a reel: boxes (x0, y0, x1, y1) in screenshot pixels, painted over with
# the screen's own background. 19-lead-detail shows a sample buyer's phone number; reels never show a phone number.
REDACT = {"19-lead-detail.jpg": [(56, 180, 420, 242)]}


@dataclass(frozen=True)
class Script:
    code: str           # A1..D2: the reel's id in captions, links and reports
    group: str          # pain | demo | before_after | result
    theme: str          # the one agent problem this reel is about
    hook: str           # at most 7 words: the viewer's problem, on screen from the first frame
    pain: str
    screen: str         # a file in assets/screens, or "reel" (a listing reel's first frame, drawn from a sample home)
    screen_line: str    # what the product does, above the phone
    result: str
    caption: str        # first line of the caption (English: captions are read, not heard)
    screen_top: float = 0.0   # where the phone's view of the screen starts (0 = top of the screenshot, 1 = as low as it goes)


SCRIPTS: Tuple[Script, ...] = (
    Script("A1", "pain", "Typing the same WhatsApp message", "Same property message, *roz* type?",
           "Har group mein. Har buyer ko. *Phir se.*", "22-marketing-ready.jpg", "WhatsApp message aur posts *ready* milte hain",
           "Copy karo. Share karo. *Bas.*", "Still typing the same property message for every group?"),
    Script("A2", "pain", "Listings lost in WhatsApp groups", "Property sirf WhatsApp *groups* mein?",
           "Message neeche chala gaya. Buyer ne *dekha* hi nahi.", "12-site-home.jpg", "Aapki apni *website*, saari properties ke saath",
           "Ek link. Kabhi *neeche* nahi jaata.", "Your properties deserve more than a WhatsApp group."),
    Script("A3", "pain", "No designer", "Designer nahi hai? *Koi baat nahi.*",
           "Post banane mein *ghanta* nikal jaata hai?", "22-marketing-ready.jpg", "Property daalo. *Designed* posts ready.",
           "Instagram, Facebook aur *WhatsApp* ke liye", "No designer? No problem.", screen_top=0.55),
    Script("B1", "demo", "Creating a listing", "Bol ke *listing* banao.",
           "Har listing ka form. Har baar *type*.", "07-review-top.jpg", "Bolo ya likho. *AI* details bhar deta hai.",
           "Aap check karo, *post* karo.", "Say it or type it. Your listing is filled in for you to check."),
    Script("B2", "demo", "All the marketing for one property", "Ek property. *Saari* marketing.",
           "Caption, post, WhatsApp message... *alag alag?*", "22-marketing-ready.jpg", "Sab ek jagah, *ready*",
           "English, Hindi aur *Marathi* mein", "One property. All its marketing, in one place."),
    Script("B3", "demo", "Reels from property photos", "Property photos se *Reel*?",
           "Editing app seekhne ka *time* nahi?", "reel", "Photos daalo. *Reel* ban jaati hai.",
           "Koi editing *nahi*.", "Turn your property photos into a Reel. No editing."),
    Script("C1", "before_after", "Leads in a diary", "Leads abhi bhi *diary* mein?",
           "Kaun serious tha? *Yaad* nahi.", "19-lead-detail.jpg", "Har buyer ka card: *budget*, area, timing",
           "Hot ya warm, *pehle* se pata.", "Before: leads in a diary. After: a card for every buyer."),
    Script("C2", "before_after", "Who to send a new property to", "Nayi property. *Kisko* bhejein?",
           "Contacts scroll... scroll... *scroll...*", "27-buyers-match.jpg", "Matching buyers, *ek* list mein",
           "WhatsApp pe *ek tap* mein bhejo.", "New property? See which of your buyers match it."),
    Script("D1", "result", "New agents", "Naye agent ho? *Shuruaat* yahan se.",
           "Website banwana *mehenga* lagta hai?", "12-site-home.jpg", "Aapki property *website*, aapke naam se",
           "Pilot mein *free*.", "Just started as an agent? Get your own property website."),
    Script("D2", "result", "Agents with many properties", "50+ properties? *Kisko* pehle call?",
           "Itne buyers. Itne messages. *Confusion.*", "30-home-actions.jpg", "Har subah: *aaj* kisko call karna hai",
           "Leads *sorted*, aapke liye.", "Managing 50+ properties? See who to call first, every morning."),
)
BY_CODE: Dict[str, Script] = {s.code: s for s in SCRIPTS}

# What the product does not do (yet), or numbers nobody measured: never on screen or in a caption.
BANNED = re.compile(r"\b(seconds?|secs?|minutes?|instant\w*|publish\w*|auto[- ]?post\w*|24\s*/\s*7|guarantee\w*|best|no\.?\s*1|"
                    r"automatic\w*|sell faster|more leads|double)\b", re.I)
NUMBER = re.compile(r"\d+")
ALLOWED_NUMBERS = {"D2": {"50"}}   # "50+ properties" describes the viewer, not a result we promise
MAX_HOOK_WORDS = 7


def _plain(text: str) -> str:
    return text.replace("*", "")


def check_script(s: Script) -> List[str]:
    """Problems with a script (empty = fine to publish)."""
    out = []
    if s.group not in GROUPS:
        out.append(f"{s.code}: unknown group {s.group}")
    if len(_plain(s.hook).split()) > MAX_HOOK_WORDS:
        out.append(f"{s.code}: hook has more than {MAX_HOOK_WORDS} words")
    texts = [s.hook, s.pain, s.screen_line, s.result, s.caption]
    for t in texts:
        if BANNED.search(_plain(t)):
            out.append(f"{s.code}: '{BANNED.search(_plain(t)).group(0)}' is a claim we do not make: {t}")
        extra = set(NUMBER.findall(t)) - ALLOWED_NUMBERS.get(s.code, set())
        if extra:
            out.append(f"{s.code}: number {sorted(extra)} has no source: {t}")
        if re.search(r"[ऀ-ॿ]", t):
            out.append(f"{s.code}: Devanagari cannot be drawn on a reel: {t}")
    if s.screen != "reel" and not (SCREENS / s.screen).is_file():
        out.append(f"{s.code}: screen {s.screen} is missing")
    return out


# ---- the phone frame ---------------------------------------------------------------------------------------------------
PHONE_W = 600
PHONE_TOP = 760          # the text block (kicker + up to 2 lines) sits above, from CONTENT_TOP
BEZEL = 16
DARK = (8, 14, 28)


def _rounded_mask(size, r) -> Image.Image:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    return m


def _screen_image(name: str) -> Image.Image:
    if name == "reel":
        return _reel_frame()
    with Image.open(SCREENS / name) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
    d = ImageDraw.Draw(im)
    for box in REDACT.get(name, []):
        bg = im.getpixel((box[0] - 8, box[1] + 4)) if box[0] >= 8 else im.getpixel((2, box[1]))
        d.rectangle(box, fill=bg)
    return im


@lru_cache(maxsize=1)
def _reel_frame() -> Image.Image:
    """What a listing reel looks like: the first frame of a 'tour' reel of a labelled sample home (the feature 'Make reel' makes)."""
    from app.modules.showcase.samples import get
    from .compose import Renderer
    from .templates import listing_tour
    h = get("kharadi-2bhk-ready")
    facts = {"bhk": h.bhk, "locality": h.locality, "area_sqft": h.carpet_sqft, "possession": "ready" if h.ready else "under_construction"}
    scenes, _ = listing_tour([p.path for p in h.photos], facts, sample=True)
    return Renderer(scenes[:2], hook_tag=False).cover()   # the opening frame as viewers see it (two scenes: no brand mark on it)


def phone_still(screen: str, seed: str, top: float = 0.0) -> Image.Image:
    """A 1080x1920 frame: the brand background with a phone holding `screen` (scaled to the phone's width; the view starts `top`
    of the way down when the screenshot is taller than the phone). The phone runs past the bottom edge, like a hand holding it."""
    bg = brand_background((W, H), seed, skyline=False)
    inner_w = PHONE_W - 2 * BEZEL
    inner_h = H - PHONE_TOP + 200 - BEZEL       # past the bottom edge
    src = _screen_image(screen)
    src = src.resize((inner_w, round(src.height * inner_w / src.width)), Image.LANCZOS)
    if src.height > inner_h:
        y = round((src.height - inner_h) * max(0.0, min(1.0, top)))
        src = src.crop((0, y, inner_w, y + inner_h))
    else:
        src = ImageOps.pad(src, (inner_w, inner_h), color=src.getpixel((2, src.height - 2)), centering=(0.5, 0.0))
    x0 = (W - PHONE_W) // 2
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle([x0, PHONE_TOP + 24, x0 + PHONE_W, H + 300], 58, fill=150)
    bg.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(34)))
    body = Image.new("RGB", (PHONE_W, H - PHONE_TOP + 200), DARK)
    ImageDraw.Draw(body).rounded_rectangle([0, 0, PHONE_W - 1, body.height - 1], 58, outline=(70, 86, 118), width=3)
    body.paste(src, (BEZEL, BEZEL), _rounded_mask(src.size, 42))
    bg.paste(body, (x0, PHONE_TOP), _rounded_mask(body.size, 58))
    return bg


# ---- scenes ----------------------------------------------------------------------------------------------------------------
def scenes(s: Script) -> Tuple[List[Scene], Dict]:
    """The five scenes of a script and the make_reel options (no brand tag on the hook)."""
    problems = check_script(s)
    if problems:
        raise ValueError("; ".join(problems))
    before_after = s.group == "before_after"
    still = phone_still(s.screen, f"agent-{s.code}", s.screen_top)
    blurred = still.filter(ImageFilter.GaussianBlur(18))
    out = [
        Scene(lines=[TextLine(s.hook, size=124, max_lines=4)], kicker=KICKER, seconds=HOOK_SECONDS, seed=f"agent-{s.code}-hook"),
        Scene(lines=[TextLine(s.pain, size=104, max_lines=4)], kicker="Before" if before_after else None, seconds=PAIN_SECONDS,
              seed=f"agent-{s.code}-pain"),
        Scene(image=still, screen=True, layout="top", lines=[TextLine(s.screen_line, size=74, max_lines=2)],
              kicker="After: with Avasetu" if before_after else "With Avasetu", seconds=SCREEN_SECONDS, seed=f"agent-{s.code}-screen"),
        Scene(image=blurred, lines=[TextLine(s.result, size=112, max_lines=3)], seconds=RESULT_SECONDS, seed=f"agent-{s.code}-result"),
        Scene(lines=[TextLine(f"*{CTA_WORD}* comment karein", size=112), TextLine("Pune agents ke liye free pilot", size=58)],
              seconds=CTA_SECONDS, seed=f"agent-{s.code}-cta"),
    ]
    return out, {"transition": "fade", "xfade": XFADE, "hook_tag": False}


def render(code: str, dest: Path, composer=None) -> Path:
    sc, opts = scenes(BY_CODE[code])
    return (composer or make_reel)(sc, Path(dest), **opts)


# ---- captions --------------------------------------------------------------------------------------------------------------
def source_tag(code: str, channel: str) -> str:
    return f"reel_{code.lower()}_{'ig' if channel == 'instagram' else 'fb'}"


def pilot_link(code: str, channel: str) -> str:
    return f"{brand.SITE}{PILOT_PATH}?src={source_tag(code, channel)}"


def caption(code: str, channel: str) -> str:
    """The caption: the one message, what the pilot is, the comment keyword; Facebook also gets the tagged pilot link.
    Hashtags are added at publish time by calendar.reach (agent tags)."""
    s = BY_CODE[code]
    lines = [s.caption,
             "Avasetu is for Pune property agents: your listings, posts and leads in one place. Screens show sample data.",
             f"Comment {CTA_WORD} and we will send you the free pilot link."]
    if channel != "instagram":
        lines.append(f"Or join here: {pilot_link(code, channel)}")
    return "\n\n".join(lines)


# ---- the experiment: posting order and the funnel ------------------------------------------------------------------------------
# One group after another, so no two reels in a row test the same kind of message.
ORDER = ("A1", "B2", "C1", "D2", "A2", "B1", "C2", "D1", "A3", "B3")
SOURCE = re.compile(r"reel_([a-z]\d)_(?:ig|fb)")


def _tail(phone) -> str:
    digits = re.sub(r"\D", "", str(phone or ""))
    return digits[-10:] if len(digits) >= 10 else ""


def funnel(comments: List[dict], requests: List[dict], users: List[dict], listings: List[dict]) -> Dict[str, Dict[str, int]]:
    """Per reel code: agent comments answered -> invite requests carrying the reel's src tag -> those phones signed up -> of them,
    agents who added at least one property. Pure: the caller reads the four collections (comments carry `reel_code`)."""
    out = {c: {"comments": 0, "requests": 0, "signed_up": 0, "added_property": 0} for c in ORDER}
    for c in comments:
        code = c.get("reel_code")
        if code in out and c.get("intent") == "interested":
            out[code]["comments"] += 1
    by_phone = {_tail(u.get("phone")): str(u.get("_id") or u.get("id")) for u in users if _tail(u.get("phone"))}
    with_listing = {str(l.get("agent_id")) for l in listings}
    seen = set()
    for r in requests:
        m = SOURCE.fullmatch(str(r.get("source") or ""))
        code = m.group(1).upper() if m else None
        phone = _tail(r.get("phone"))
        if code not in out or (code, phone) in seen:
            continue
        seen.add((code, phone))
        out[code]["requests"] += 1
        uid = by_phone.get(phone)
        if uid:
            out[code]["signed_up"] += 1
            out[code]["added_property"] += int(uid in with_listing)
    return out
