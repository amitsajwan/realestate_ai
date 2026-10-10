"""Flow reels: one real property, from the listing to its marketing, shown on the real Avasetu screens.

Audience: Pune property agents and brokers, about 28-50, on Facebook first (Instagram second), Hinglish. They are short of time and
doubt that "apps" help, so the reel shows the product working on a real listing instead of promising anything.

The screens are captured from avasetu.in on the owner's own listing (Avasetu's Gulmohar City plot, Ranjangaon), not a sample and
not another agent's property (House Deal has not agreed to be in our ads). The offer at the end is the founding offer
(onboarding/trial.py: TRIAL_DAYS free for the first TRIAL_SPOTS agents). Same guards as agent_reels: no time claims, no
"auto-post", no number without a source (the only numbers allowed are the offer's), no Devanagari on screen; the same Comment AGENT
CTA and ?src=reel_<code>_<fb|ig> trial link, so a sign-up traces back to the reel.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from .agent_reels import BANNED, CTA_WORD, KICKER, MAX_HOOK_WORDS, NUMBER, PRODUCT_LINE, phone_still, pilot_link
from .compose import Scene, TextLine, make_reel

HOOK_SECONDS, STEP_SECONDS, CTA_SECONDS = 2.2, 3.0, 3.2
XFADE = 0.4
OFFER_NUMBERS = {"20"}   # "pehle 20 agents": the founding offer (onboarding/trial.py TRIAL_SPOTS), not a result


@dataclass(frozen=True)
class Step:
    kicker: str
    line: str
    screen: str     # a screenshot in agent_reels' assets/screens
    top: float = 0.0


@dataclass(frozen=True)
class FlowScript:
    code: str
    hook: str
    steps: Tuple[Step, ...]
    offer: str
    caption: str


SCRIPTS: Tuple[FlowScript, ...] = (
    FlowScript("F1", "Ek property. *Zero* se posts tak.",
               (Step("STEP 1 · PROPERTY", "Price aur jagah *daalo*", "40-flow-listing.jpg"),
                Step("STEP 2 · FACTS", "MahaRERA *match*, facts check", "41-flow-facts.jpg"),
                Step("STEP 3 · POSTS", "Posts *ready*, design ke saath", "42-flow-posts.jpg"),
                Step("STEP 4 · SHARE KARO", "Approve karo, *share* karo", "43-flow-post.jpg")),
               "Pehle *20* Pune agents: ek mahina *free*",
               "One real plot, from the listing to its posts, on the real Avasetu screens."),
)
BY_CODE: Dict[str, FlowScript] = {s.code: s for s in SCRIPTS}


def _plain(t: str) -> str:
    return t.replace("*", "")


def check_script(s: FlowScript) -> List[str]:
    out = []
    if len(_plain(s.hook).split()) > MAX_HOOK_WORDS:
        out.append(f"{s.code}: hook has more than {MAX_HOOK_WORDS} words")
    for t in [s.hook, s.offer, s.caption] + [st.line for st in s.steps]:
        hit = BANNED.search(_plain(t))
        if hit:
            out.append(f"{s.code}: '{hit.group(0)}' is a claim we do not make: {t}")
        extra = set(NUMBER.findall(t)) - OFFER_NUMBERS
        if extra:
            out.append(f"{s.code}: number {sorted(extra)} has no source: {t}")
    return out


def scenes(s: FlowScript) -> Tuple[List[Scene], Dict]:
    problems = check_script(s)
    if problems:
        raise ValueError("; ".join(problems))
    out = [Scene(lines=[TextLine(s.hook, size=124, max_lines=4)], kicker=KICKER, seconds=HOOK_SECONDS, seed=f"flow-{s.code}-hook")]
    for i, st in enumerate(s.steps):
        out.append(Scene(image=phone_still(st.screen, f"flow-{s.code}-{i}", st.top), screen=True, layout="top", kicker=st.kicker,
                         lines=[TextLine(st.line, size=74, max_lines=2)], seconds=STEP_SECONDS, seed=f"flow-{s.code}-{i}"))
    out.append(Scene(lines=[TextLine(s.offer, size=96, max_lines=3), TextLine(f"*{CTA_WORD}* comment karein", size=70)],
                     seconds=CTA_SECONDS, seed=f"flow-{s.code}-cta"))
    return out, {"transition": "fade", "xfade": XFADE, "hook_tag": False}


def render(code: str, dest, composer=None) -> Path:
    sc, opts = scenes(BY_CODE[code])
    return (composer or make_reel)(sc, Path(dest), **opts)


def caption(code: str, channel: str) -> str:
    s = BY_CODE[code]
    lines = [s.caption,
             "Founding offer: the first 20 Pune agents get one month free, every property, no card.",
             PRODUCT_LINE,
             f"Comment {CTA_WORD} and we will send you the free trial link."]
    if channel != "instagram":
        lines.append(f"Or join here: {pilot_link(code, channel)}")
    return "\n\n".join(lines)
