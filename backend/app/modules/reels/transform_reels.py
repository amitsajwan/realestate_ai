"""Transformation reels: the input -> output demo that agent_reels does not have. Where the agent reels show one static
product screen, these show the journey: the agent's raw property-details message (a drawn chat mock, demo data only, never a
real buyer) -> a real Avasetu screen -> the deliverable (a drawn "post ready" card, or the own-website screen for many
properties). The five-scene Script in agent_reels cannot hold that, so this module is a sibling with its own scenes().

Same rules as agent_reels: no time claims, no publish/auto-post promises, no invented numbers in any checked text, no
Devanagari on screen, and the same Comment AGENT CTA and trial link so a sign-up traces back through `source` like reels
A1..D2 (agent_reels.funnel already accepts `reel_e1_*`). Preview only for now: nothing here is wired into the calendar
plan or the report.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from app.modules.marketing.images import GOLD, brand_background, load_font, wrap, _logo

from .compose import INK, PHONE_RE, H, W, Scene, TextLine, make_reel
from .agent_reels import (
    BANNED,
    BEZEL,
    CTA_WORD,
    DARK,
    KICKER,
    MAX_HOOK_WORDS,
    NUMBER,
    PHONE_TOP,
    PHONE_W,
    PRODUCT_LINE,
    REEL_PROJECT,
    _rounded_mask,
    phone_still,
    pilot_link,
)

HOOK_SECONDS, INPUT_SECONDS, SCREEN_SECONDS = 2.0, 2.8, 3.0
OUTPUT_SECONDS, RESULT_SECONDS, CTA_SECONDS = 3.2, 2.2, 2.6
XFADE = 0.4
CHAT_BG = (11, 18, 33)
CHAT_HEADER = (17, 26, 46)
CHAT_DIVIDER = (23, 33, 56)
CHAT_TEXT = (240, 244, 252)
CHAT_MUTED = (150, 160, 178)
BUBBLE = (31, 62, 112)
BUBBLE_EDGE = (58, 96, 158)
ONLINE = (72, 187, 110)
CARD = (247, 248, 250)
CARD_LINE = (222, 226, 233)
CARD_GRAY = (108, 116, 130)
CARD_INK_SOFT = (70, 78, 92)


@dataclass(frozen=True)
class Script:
    code: str                  # E1..: the reel's id in captions, links and (later) reports
    theme: str                 # the one journey this reel shows
    hook: str                  # at most 7 words: on screen from the first frame
    input_line: str            # said above the chat mock
    bubbles: Tuple[str, ...]   # the demo details message(s) in the chat mock (made-up property, never a real buyer)
    screen: str                # a screenshot in agent_reels' assets/screens: the product step
    screen_line: str           # what Avasetu does, above the phone
    output: str                # "post" (drawn ready-post card) | "site" (the own-website screen for many properties)
    output_line: str           # the deliverable, above the phone
    result: str
    caption: str               # first line of the caption (English: captions are read, not heard)


SCRIPTS: Tuple[Script, ...] = (
    Script("E1", "From a details message to a ready post", "Property *details* bhejo.",
           "Type karo. *Bas* itna.",
           ("2 BHK, Wagholi\n950 sq ft, ready possession\nEast facing, 1 covered parking",),
           "07-review-top.jpg", "Details listing mein *bhari* gayi",
           "post", "Post *ready*. English, Hindi, *Marathi*.",
           "Copy karo. *Share* karo. Bas.",
           "I sent Avasetu my property details. The post came back ready."),
    Script("E2", "Many properties, all their marketing in one place", "Itni *properties*? Sab ki *posts*?",
           "Properties ki *list* bhejo",
           ("2 BHK Wagholi, ready possession", "3 BHK Kharadi, under construction", "2 BHK Baner, resale"),
           "22-marketing-ready.jpg", "Har property ka post *ready*",
           "site", "Sab kuch ek *link* pe",
           "Ek jagah. *Saari* marketing.",
           "Many properties. One place for all their posts."),
)
BY_CODE: Dict[str, Script] = {s.code: s for s in SCRIPTS}
ORDER = tuple(s.code for s in SCRIPTS)


def _plain(text: str) -> str:
    return text.replace("*", "")


def check_script(s: Script) -> List[str]:
    """Problems with a script (empty = fine to preview). Same guards as agent_reels, plus no phone numbers in the chat mock."""
    out = []
    if len(_plain(s.hook).split()) > MAX_HOOK_WORDS:
        out.append(f"{s.code}: hook has more than {MAX_HOOK_WORDS} words")
    texts = [s.hook, s.input_line, s.screen_line, s.output_line, s.result, s.caption]
    for t in texts:
        hit = BANNED.search(_plain(t))
        if hit:
            out.append(f"{s.code}: '{hit.group(0)}' is a claim we do not make: {t}")
        extra = set(NUMBER.findall(t))
        if extra:
            out.append(f"{s.code}: number {sorted(extra)} has no source: {t}")
        if re.search(r"[ऀ-ॿ]", t):
            out.append(f"{s.code}: Devanagari cannot be drawn on a reel: {t}")
    for b in s.bubbles:
        if PHONE_RE.search(b):
            out.append(f"{s.code}: the chat mock must not show a phone number: {b}")
        if re.search(r"[ऀ-ॿ]", b):
            out.append(f"{s.code}: Devanagari cannot be drawn on a reel: {b}")
    if s.output not in ("post", "site"):
        out.append(f"{s.code}: output must be 'post' or 'site'")
    return out


# ---- the drawn mocks (demo data only) --------------------------------------------------------------------------------------
def _phone_frame(inner: Image.Image, seed: str) -> Image.Image:
    """A 1080x1920 frame: brand background with a phone showing `inner`, a UI drawn at the phone's exact size."""
    bg = brand_background((W, H), seed, skyline=False)
    inner_w = PHONE_W - 2 * BEZEL
    inner_h = H - PHONE_TOP + 200 - BEZEL
    src = inner.resize((inner_w, round(inner.height * inner_w / inner.width)), Image.LANCZOS) if inner.size != (inner_w, inner_h) else inner
    x0 = (W - PHONE_W) // 2
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle([x0, PHONE_TOP + 24, x0 + PHONE_W, H + 300], 58, fill=150)
    bg.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(34)))
    body = Image.new("RGB", (PHONE_W, H - PHONE_TOP + 200), DARK)
    ImageDraw.Draw(body).rounded_rectangle([0, 0, PHONE_W - 1, body.height - 1], 58, outline=(70, 86, 118), width=3)
    body.paste(src, (BEZEL, BEZEL), _rounded_mask(src.size, 42))
    bg.paste(body, (x0, PHONE_TOP), _rounded_mask(body.size, 58))
    return bg


def _chat_inner(bubbles: Tuple[str, ...]) -> Image.Image:
    """The phone view of a chat with Avasetu: header, day divider, then the agent's details bubbles (bottom-anchored)."""
    inner_w, inner_h = PHONE_W - 2 * BEZEL, H - PHONE_TOP + 200 - BEZEL
    img = Image.new("RGB", (inner_w, inner_h), CHAT_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, inner_w, 88], fill=CHAT_HEADER)
    logo = _logo(56)
    if logo is not None:
        img.paste(logo, (16, 16), logo)
    d.text((88, 16), "Avasetu", font=load_font(30, "semibold"), fill=(255, 255, 255))
    d.text((88, 52), "property assistant", font=load_font(22, "regular"), fill=CHAT_MUTED)
    d.ellipse([inner_w - 46, 34, inner_w - 26, 54], fill=ONLINE)
    label = "Today"
    f_div = load_font(22, "medium")
    tw = d.textlength(label, font=f_div)
    d.rounded_rectangle([(inner_w - tw) // 2 - 18, 110, (inner_w + tw) // 2 + 18, 146], radius=18, fill=CHAT_DIVIDER)
    d.text(((inner_w - tw) // 2, 116), label, font=f_div, fill=(160, 170, 188))
    f = load_font(27, "medium")
    asc, desc = f.getmetrics()
    lh = asc + desc + 6
    y = 180   # right under the day divider: the phone runs past the frame's bottom edge, so never bottom-anchor
    for b in bubbles:
        lines = wrap(d, b, f, inner_w - 96)
        bh = lh * len(lines) + 28 + 28
        bw = int(max(d.textlength(ln, font=f) for ln in lines)) + 40
        x1 = inner_w - 28
        x0 = x1 - bw
        d.polygon([(x1 - 26, y + bh - 2), (x1 - 4, y + bh + 18), (x1 - 12, y + bh - 10)], fill=BUBBLE)
        d.rounded_rectangle([x0, y, x1, y + bh], radius=22, fill=BUBBLE, outline=BUBBLE_EDGE, width=1)
        ty = y + 16
        for ln in lines:
            d.text((x0 + 20, ty), ln, font=f, fill=CHAT_TEXT)
            ty += lh
        tk = y + bh - 24
        d.line([x1 - 46, tk + 8, x1 - 38, tk + 16], fill=GOLD, width=3)
        d.line([x1 - 38, tk + 16, x1 - 24, tk - 4], fill=GOLD, width=3)
        y += bh + 24
    return img


def _post_inner() -> Image.Image:
    """The phone view of the deliverable: the ready property post card for the consented demo project (same image and
    'Artist's impression' label as agent_reels' B3), with the three share destinations as chips."""
    inner_w, inner_h = PHONE_W - 2 * BEZEL, H - PHONE_TOP + 200 - BEZEL
    img = Image.new("RGB", (inner_w, inner_h), CHAT_BG)
    d = ImageDraw.Draw(img)
    card_h = 872
    d.rounded_rectangle([14, 14, inner_w - 14, 14 + card_h], radius=26, fill=CARD)
    logo = _logo(46)
    if logo is not None:
        img.paste(logo, (36, 34), logo)
    d.text((96, 36), "Avasetu", font=load_font(26, "semibold"), fill=INK)
    d.text((96, 70), "Property post - ready", font=load_font(20, "regular"), fill=CARD_GRAY)
    with Image.open(REEL_PROJECT["image"]) as im:
        photo = ImageOps.fit(im.convert("RGB"), (inner_w - 72, 520), Image.LANCZOS)
    img.paste(photo, (36, 116))
    badge_f = load_font(19, "semibold")
    label = REEL_PROJECT["label"]
    tw = d.textlength(label, font=badge_f)
    d.rounded_rectangle([48, 130, 48 + tw + 26, 162], radius=16, fill=(8, 10, 16))
    d.text((61, 135), label, font=badge_f, fill=(255, 255, 255))
    d.text((36, 654), f"{REEL_PROJECT['bhk']} in {REEL_PROJECT['locality']}", font=load_font(30, "bold"), fill=INK)
    d.text((36, 700), f"Listed by {REEL_PROJECT['listed_by']}", font=load_font(22, "medium"), fill=CARD_GRAY)
    d.line([36, 752, inner_w - 36, 752], fill=CARD_LINE, width=2)
    x = 36
    chip_f = load_font(17, "semibold")
    for chip in ("INSTAGRAM", "FACEBOOK", "WHATSAPP"):
        tw = d.textlength(chip, font=chip_f)
        d.rounded_rectangle([x, 776, x + tw + 28, 818], radius=21, outline=(200, 206, 216), width=2)
        d.text((x + 14, 787), chip, font=chip_f, fill=CARD_INK_SOFT)
        x += int(tw) + 42
    return img


# ---- scenes -----------------------------------------------------------------------------------------------------------------
def scenes(s: Script) -> Tuple[List[Scene], Dict]:
    problems = check_script(s)
    if problems:
        raise ValueError("; ".join(problems))
    chat = _phone_frame(_chat_inner(s.bubbles), f"transform-{s.code}-chat")
    out = phone_still("12-site-home.jpg", f"transform-{s.code}-out") if s.output == "site" \
        else _phone_frame(_post_inner(), f"transform-{s.code}-out")
    blurred = out.filter(ImageFilter.GaussianBlur(18))
    return [
        Scene(lines=[TextLine(s.hook, size=124, max_lines=4)], kicker=KICKER, seconds=HOOK_SECONDS, seed=f"transform-{s.code}-hook"),
        Scene(image=chat, screen=True, layout="top", kicker="STEP 1 · YOUR DETAILS",
              lines=[TextLine(s.input_line, size=74, max_lines=2)], seconds=INPUT_SECONDS, seed=f"transform-{s.code}-input"),
        Scene(image=phone_still(s.screen, f"transform-{s.code}-app"), screen=True, layout="top", kicker="STEP 2 · WITH AVASETU",
              lines=[TextLine(s.screen_line, size=74, max_lines=2)], seconds=SCREEN_SECONDS, seed=f"transform-{s.code}-screen"),
        Scene(image=out, screen=True, layout="top", kicker="STEP 3 · READY",
              lines=[TextLine(s.output_line, size=74, max_lines=2)], seconds=OUTPUT_SECONDS, seed=f"transform-{s.code}-out"),
        Scene(image=blurred, lines=[TextLine(s.result, size=112, max_lines=3)], seconds=RESULT_SECONDS, seed=f"transform-{s.code}-result"),
        Scene(lines=[TextLine(f"*{CTA_WORD}* comment karein", size=112), TextLine("Pune agents ke liye free trial", size=58)],
              seconds=CTA_SECONDS, seed=f"transform-{s.code}-cta"),
    ], {"transition": "fade", "xfade": XFADE, "hook_tag": False}


def render(code: str, dest, composer=None) -> Path:
    sc, opts = scenes(BY_CODE[code])
    return (composer or make_reel)(sc, Path(dest), **opts)


# ---- captions --------------------------------------------------------------------------------------------------------------
def caption(code: str, channel: str) -> str:
    """Same shape as agent_reels.caption, so the calendar and the funnel treat these reels like the others."""
    s = BY_CODE[code]
    lines = [s.caption,
             PRODUCT_LINE,
             f"Comment {CTA_WORD} and we will send you the free trial link."]
    if channel != "instagram":
        lines.append(f"Or join here: {pilot_link(code, channel)}")
    return "\n\n".join(lines)
