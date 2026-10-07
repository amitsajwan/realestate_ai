"""Three reel templates. Each returns (scenes, options) to pass to compose.make_reel(scenes, out, **options).

Rules (docs/NEWSROOM_PLAN.md, brand): no phone numbers, no invented facts, no price unless given; a builder's render is labelled (badge).
"""
from typing import Dict, List, Optional, Sequence, Tuple

from .compose import Scene, TextLine, distinct_photos, read_seconds, split_screens, stretch
from .director import CTA_SCREEN, CTA_WORD  # noqa: F401  (CTA_WORD re-exported: the comment keyword)
HOOK_SECONDS = 2.2  # the opening scene: most viewers decide in the first 1-2 s, so the hook is short and on screen from frame one
# Tip and pitch reels open like the slide reels (reels/slides.py): the first slide reel lost 62% of plays in one second when frame
# one was a busy picture. So frame one is a hook card: the hook alone, big, on the plain brand background (no photo, no label, no
# brand tag), then quick cuts instead of slow cross-fades.
HOOK_CARD_SECONDS = 1.6
QUICK_XFADE = 0.35  # short enough to keep the pace, long enough to read as a smooth blend (0.15 s looked like a hard jump)
HOOK_OPTIONS = {"transition": "fade", "xfade": QUICK_XFADE, "hook_tag": False}


def tip_reel(lines: Sequence[str], images: Optional[Sequence] = None, seed: str = "tip") -> Tuple[List[Scene], Dict]:
    """'Tip in 15 seconds': lines[0] = hook, lines[1:4] = three beats, lines[4] (optional) = call to action.
    Fewer beats are fine (minimum: a hook and one beat). Use *asterisks* to colour a word gold."""
    lines = [l.strip() for l in lines if l and l.strip()]
    if len(lines) < 2:
        raise ValueError("a tip reel needs a hook and at least one beat")
    hook, beats = lines[0], lines[1:4]
    cta = lines[4] if len(lines) > 4 else "Save this for when you need it."
    imgs = list(images or [])

    def img(i):
        return imgs[i % len(imgs)] if imgs else None

    scenes = [Scene(lines=[TextLine(hook, size=140, max_lines=4)], seconds=HOOK_CARD_SECONDS, seed=f"{seed}-0")]
    for i, b in enumerate(beats):  # a long tip becomes two or three quick screens (same photo, same label): short enough to read muted
        for k, part in enumerate(split_screens(b)):
            scenes.append(Scene(image=img(i + 1), lines=[TextLine(part, size=110, max_lines=4)], kicker=f"Tip {i + 1} of {len(beats)}",
                                seconds=read_seconds(part), seed=f"{seed}-{i + 1}"))   # same seed: one continuous background
    scenes.append(Scene(image=img(len(beats) + 1), lines=[TextLine(cta, size=96, max_lines=4)], seconds=2.8, seed=f"{seed}-cta"))
    return _at_least_min(scenes, QUICK_XFADE), dict(HOOK_OPTIONS)


def listing_tour(photos: Sequence, facts: Dict, badge: Optional[str] = None) -> Tuple[List[Scene], Dict]:
    """'Listing tour': photos plus key facts. facts keys: bhk (number), property_type (default 'apartment'), locality, city (default 'Pune'),
    area_sqft, possession ('ready' | 'under_construction' or free text), price_text (shown only when provided), furnishing.
    `badge` (e.g. "Artist's impression" for a builder's render, "Sample listing" for a labelled sample) is shown on every scene.
    With a price it is 'guess the price': the price is revealed on the last scene, which also carries the call to action.
    One photo per scene: with fewer distinct photos than facts, the least important fact scenes are left out (furnishing, then
    possession, then area) rather than a photo shown twice; the opening and the closing scene always stay."""
    photos = distinct_photos(photos)
    if not photos:
        raise ValueError("a listing tour needs at least one photo")
    poss = {"ready": "Ready to move", "under_construction": "Under construction"}.get(facts.get("possession") or "", facts.get("possession"))
    optional = [k for k, v in (("area_sqft", facts.get("area_sqft")), ("possession", poss),
                               ("furnishing", facts.get("furnishing"))) if v]          # most important first (the price is always kept)
    keep = set(optional[:max(0, len(photos) - 2)])
    facts = {k: v for k, v in facts.items() if k not in optional or k in keep}
    bhk = facts.get("bhk")
    ptype = facts.get("property_type") or "apartment"
    locality, city = facts.get("locality") or "", facts.get("city") or "Pune"
    head = (f"{int(bhk) if float(bhk).is_integer() else bhk} BHK " if bhk else "") + ptype
    where = f"{locality}, {city}" if locality else city

    def ph(i):
        return photos[i % len(photos)]

    head = head.capitalize() if not bhk else head
    if facts.get("price_text"):  # 'guess the price': the price is revealed on the last scene before the call to action
        opening = [TextLine("Guess the *price*", size=124), TextLine(f"{head} in {where}", size=60, weight="semibold")]
    else:
        opening = [TextLine(head, size=108), TextLine(f"*{where}*", size=64, weight="semibold")]
    scenes = [Scene(image=ph(0), lines=opening, layout="lower", badge=badge, seconds=HOOK_SECONDS + 0.2, seed="tour-0")]
    n = 1
    if facts.get("area_sqft"):
        scenes.append(Scene(image=ph(n), lines=[TextLine(f"{int(facts['area_sqft']):,}", size=176), TextLine("sq ft of *usable* space" if False else "square feet", size=60)],
                            layout="lower", badge=badge, seconds=2.8, seed=f"tour-{n}"))
        n += 1
    poss = poss if "possession" in keep else None
    if poss:
        scenes.append(Scene(image=ph(n), lines=[TextLine(poss, size=104), TextLine("Possession", size=56)], layout="lower", badge=badge,
                            seconds=2.8, seed=f"tour-{n}"))
        n += 1
    if facts.get("furnishing"):
        scenes.append(Scene(image=ph(n), lines=[TextLine(str(facts["furnishing"]), size=104), TextLine("Furnishing", size=56)], layout="lower",
                            badge=badge, seconds=2.6, seed=f"tour-{n}"))
        n += 1
    if facts.get("price_text"):  # the reveal is the last scene and carries the call to action: nothing to wait for after the payoff
        scenes.append(Scene(image=ph(n), lines=[TextLine(str(facts["price_text"]), size=150), TextLine("Did you guess right?", size=60),
                                                TextLine(CTA_SCREEN["en"], size=56, weight="semibold", max_lines=2)],
                            layout="lower", badge=badge, seconds=3.4, seed=f"tour-{n}"))
    else:
        scenes.append(Scene(image=ph(n), lines=[TextLine(CTA_SCREEN["en"], size=100, max_lines=3)],
                            layout="lower", badge=badge, seconds=2.8, seed=f"tour-{n}"))
    return _at_least_min(scenes, 0.5), {"transition": "slide", "xfade": 0.5}


def agent_pitch(problem: str = "Buyers message you all day. *Same* questions. Every time.",
                solution: str = "Your own link that answers them, *qualifies* the buyer and hands you only the serious ones.",
                proof: Sequence[str] = ("Listings in 2 minutes", "Posts made for you"),
                cta: str = "Free for agents in Pune.",
                images: Optional[Sequence] = None) -> Tuple[List[Scene], Dict]:
    """'Agent pitch': problem, solution, two proof points, call to action. The defaults state only what the product does."""
    imgs = list(images or [])

    def img(i):
        return imgs[i % len(imgs)] if imgs else None

    scenes = [
        Scene(lines=[TextLine(problem, size=116, max_lines=5)], seconds=2.6, seed="pitch-problem"),   # a longer hook: a little longer
    ]
    for k, part in enumerate(split_screens(solution)):
        scenes.append(Scene(image=img(1), lines=[TextLine(part, size=100, max_lines=4)], kicker="There is a better way",
                            seconds=read_seconds(part), seed="pitch-solution"))
    for i, p in enumerate(list(proof)[:2]):
        scenes.append(Scene(image=img(i + 2), lines=[TextLine(p, size=108)], kicker="What you get", seconds=2.4, seed=f"pitch-proof-{i}"))
    scenes.append(Scene(image=img(4), lines=[TextLine(cta, size=104)], seconds=2.6, seed="pitch-cta"))
    return scenes, dict(HOOK_OPTIONS)


def _at_least_min(scenes: List[Scene], xfade: float) -> List[Scene]:
    """Stretch short reels (few scenes) to compose.MIN_SECONDS, so a two-scene tour is not over in five seconds."""
    durs = stretch([s.seconds or 3.0 for s in scenes], xfade)
    for s, d in zip(scenes, durs):
        s.seconds = d
    return scenes


# Made-up listing facts for tests and local previews only: never posted.
DEMO_FACTS = {
    "kharadi": {"bhk": 2, "locality": "Kharadi", "area_sqft": 1050, "possession": "ready", "property_type": "apartment"},
    "wagholi": {"bhk": 3, "locality": "Wagholi", "area_sqft": 1420, "possession": "under_construction", "property_type": "apartment"},
}

TIP_LINES = [
    "Buying in Pune? *Check this first.*",
    "Ask for the *RERA number*. Then look it up on the MahaRERA site.",
    "Compare *carpet area*, not super built-up area.",
    "Visit on a *weekday evening* to see traffic and parking.",
    "Follow for more Pune property tips.",
]
