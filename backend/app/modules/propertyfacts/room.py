"""The creative room: a campaign is pitched and chosen before anything is drawn (owner, 2026-10-14: "not randomly a reel or a
post; a team that brainstorms concepts, thinks from different angles and pitches, like a good agency").

    room = await convene(ctx, listing, llm, photos=4, images=kit_images)
    planned = briefs(room, ctx, photos, images)      # [(angle id, Brief)] for campaign.make
    reels = scripts(room)                            # {angle id: ad_reel.Script} for the ad reels

Who is in the room (each one an LLM call with its own brief; JSON in, JSON out):

  strategist          the facts in, the brief out: what this property is (premium brand, family, first home, plot), who buys it
                      and why, the one idea to own, the tone, what to avoid
  copywriter          \
  art director         | one campaign pitch each, from its own lens (words, pictures, film, the feed), one after another
  film director        | (the free model tiers rate-limit parallel calls)
  reel creator        /
  the discussion      each seat builds on someone else's pitch and names a concern; the strongest ideas across the pitches
  creative director   scores the pitches, then merges the campaign from the strongest pieces of at least two pitches,
                      following the discussion: 4-6 pieces, each with a different job in the story, in posting order

Code then does what a fact checker and a producer do: every line must be worded from the numbered fact book (a number or a
claim not in it is cut; a piece whose headline fails is dropped), and each piece becomes a Brief for the existing design desk
(campaign.make) and, where the director wrote one, a reel script for ad_reel.render. Under MIN_PIECES pieces survive: no room
campaign, and the run falls back to the fixed angles (campaign.plan). English only for now; other languages use the angles."""
import asyncio
import logging
import re
from dataclasses import replace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.modules.creative.guards import problems_in
from app.modules.creative.models import Brief

from . import ad_reel
from .campaign import Ctx, _km, _near, buyer_place, day, possession_card_ok, price_label

log = logging.getLogger(__name__)

MIN_PIECES = 3
MAX_PIECES = 6
MAX_REELS = 4          # a reel takes minutes to render: the director's best few, not one per post
ROLES = ("teaser", "brand", "design", "homes", "lifestyle", "location", "price", "trust", "why_us", "visit")
# why a buyer books through us (owner, 2026-10-15: all four true); our own campaigns only, a partner agent's terms differ
AGENCY = ("Through Avasetu: no brokerage for buyers; the builder pays us.",
          "Through Avasetu: the same price as the builder, with the builder's offers.",
          "Through Avasetu: free site visit help.",
          "Through Avasetu: we compare nearby projects honestly and help with home-loan and paperwork checks (MahaRERA, agreement).")
WHY_US = ("Why book through Avasetu?", ["No brokerage for buyers", "Same price as the builder", "Free site visit help",
                                        "Honest comparison, loan and paperwork help"])
FORMATS = ("carousel", "stat", "single", "checklist")
# a brochure or agent line that goes stale or promises stock: never a fact a post may state
STALE = re.compile(r"\bavailab|\boffer\b|\bdiscount|\blimited\b|\blast few\b|\bhurry|\bany (?:tower|floor)", re.I)   # "bookings open" is a status, kept
# a stat card's big number: the price when the headline has one, else a number with its unit
PRICE = re.compile(r"₹\s?[\d.,]+\s*(?:crore|lakh|cr|l)?\b", re.I)
STAT = re.compile(r"\b\d[\d.,]*\s*(?:km|sq ft|BHK|homes|acres|minutes|min)\b", re.I)


def stat_of(headline: str) -> str:
    m = PRICE.search(headline) or STAT.search(headline)
    return m.group(0).strip()[:14] if m else ""
LENSES = {
    "copywriter":("Copywriter", "You think in words and story: a line people remember, a story arc across the posts, the buyer's "
                   "own words for what they want."),
    "art_director": ("Art director", "You think in pictures: which photo, render or plan carries each idea, what the eye sees first, "
                     "a calm consistent look across the feed."),
    "film_director": ("Film director", "You think in reels: the opening two seconds, the arc of a 20-second story, pace, what the "
                      "voice says over which picture."),
    "reel_creator": ("Reel creator", "You are a Pune Instagram creator with a big following, not an ad agency: you know what stops "
                     "the scroll in the first second, the native formats (POV, a day in the life, 'things nobody tells you', a walk "
                     "through, this-or-that) and what people send to a friend. You talk like a creator talks."),
}
# where each one starts, so the pitches differ (the first live room: three pitches named after the brief's own line)
LEAD = {
    "copywriter": "Start from one of the brief's buyers: the life this home gives them, told as a story across the posts.",
    "art_director": "Start from the place itself: its design, architecture, landscape and spaces, shown before price or distance.",
    "film_director": "Start from a moment: a morning, a commute, an arrival home; the campaign plays like short scenes.",
    "reel_creator": "Start from the feed: what a Pune buyer scrolling at night would stop for, save, and send to a friend.",
}
SEATS = ("Strategist", *(v[0] for v in LENSES.values()))
# what the checker cuts whatever the prompt said: registration sold as approval, puffery, a walk to somewhere a car is needed
OVERCLAIM = re.compile(r"\b(?:approved|trusted|certified|endorsed)\b[^.]{0,30}\b(?:rera|maharera|regulator)|\b(?:rera|maharera|regulator)s?\b"
                       r"[^.]{0,20}\b(?:approved|trusted|certified)\b|\b(?:renowned|world[\s-]*class|iconic|unmatched|unparalleled)\b", re.I)
WALK = re.compile(r"\bwalk(?:ing|able)?\b|\bsteps? (?:from|away)\b|\bdoorstep\b", re.I)   # "Steps from IT parks, schools"
KM = re.compile(r"(\d+(?:\.\d+)?)\s*km\b", re.I)


# claims the facts never carry (the third live meeting: "ready soon", "registration ensures compliance", "premium finishes")
UNBACKED = re.compile(r"\bensur\w*|\bguarant\w*|\bcomplian\w*|\btransparen\w*|\bsecure (?:home |your )?(?:purchase|investment)\b"
                      r"|\blimited (?:units|stock|period)\b|\bfew (?:units|homes) left\b|\bfinish(?:es|ing)\b|\bappreciat\w*"
                      r"|\b(?:homes?|units?|project|flats?) (?:are |is )?approved\b|\bapproved (?:homes?|units?|project|flats?)\b"
                      r"|\bawaiting your move\b|\bmove[\s-]*in\b|\bprogress (?:is )?visible\b|\baward[\s-]*winning\b", re.I)
READY = re.compile(r"\bready\b", re.I)
# the future is for infrastructure; the project itself is launched (Camelot reels said "Lodha Camelot is coming")
NOT_YET = re.compile(r"\bcoming\b|\bsoon\b|\bupcoming\b|\blaunch(?:ing|es)?\b|\bfuture of\b|\bon the way\b", re.I)
INFRA = re.compile(r"\bmetro\b|\bline \d|\broad\b|\bring road\b|\bexpressway\b|\bairport\b|\bflyover\b|\bbridge\b|\bstation\b", re.I)
# a coming metro sold as running ("take the metro to work"): the future is sold as coming, never as here
RUNNING = re.compile(r"\b(?:take|ride|catch|by|via) (?:the )?metro\b|\bmetro (?:is |now )?(?:running|operational|open|live)\b"
                     r"|\bmetro (?:station )?(?:next door|at your doorstep)\b|\bmetro\b[^.]{0,25}\bruns\b", re.I)


def overclaims(text: str, corpus: str = "") -> bool:
    """A registration sold as an approval, puffery, a claim no fact carries, 'ready' for a project the facts do not call
    ready, or a walk to a place 1 km or more away (or with no distance at all)."""
    if OVERCLAIM.search(text) or UNBACKED.search(text) or (RUNNING.search(text) and "not running" in corpus.lower()):
        return True
    if READY.search(text) and not READY.search(corpus):
        return True
    if NOT_YET.search(text) and not INFRA.search(text):   # the project is registered and booking: never "coming"
        return True
    if WALK.search(text):
        kms = [float(x) for x in KM.findall(text)]
        return not kms or max(kms) >= 1
    return False


# ---- the fact book: every claim a piece may make, numbered --------------------------------------------------------------------
def book(c: Ctx, listing: dict, ours: bool = False) -> List[Dict[str, str]]:
    """[{id, text}] — the property's facts in plain sentences. MahaRERA, the listing and Google Maps first, then the agent's notes
    about the project (listing.about: what the brochure and the agent say), each said as theirs. Nothing stale or promissory."""
    out: List[str] = []
    name, where = c.project or c.locality or "this property", c.where or c.locality or "Pune"
    price = c.v.get("price_inr")
    if price:
        out.append(f"{c.units if c.layout else 'This ' + c.unit} at {where}: " + (f"from {price_label(int(price))} onwards" if c.layout
                                                                              else price_label(int(price))) + ".")
    if c.sqft and not c.layout:
        out.append(f"Carpet area {c.sqft:,} sq ft.")
    lo, hi = c.v.get("size_min_sqft"), c.v.get("size_max_sqft")
    if c.layout and lo and hi and hi > lo:
        out.append(f"Homes from {lo:,} to {hi:,} sq ft.")
    if c.v.get("units_total") and c.maharera:
        out.append(f"{int(c.v['units_total'])} {'plots' if c.plot else 'homes'} in {name}, by MahaRERA's count.")
    if c.v.get("rera_no"):
        out.append(f"Registered on MahaRERA: {c.v['rera_no']}.")
    if c.v.get("possession_now") and possession_card_ok(c):
        out.append(f"Completion {day(c.v['possession_now'])} on MahaRERA.")
    elif c.v.get("possession_now"):
        out.append("Under construction.")
    for k, p in _near(c)[:10]:
        n = buyer_place(c, k, p)
        if n:
            out.append(f"{n} ({k.split('.', 1)[-1]}): {_km(p['km'])} away, straight line.")
    about = listing.get("about") or {}
    seen = set()
    for key, said in (("highlights", "The project's notes say"), ("amenities", "Amenities listed"),
                      ("connectivity", "Connectivity")):
        items = about.get(key) or []
        if key == "amenities" and items:
            items = [", ".join(str(x) for x in items if str(x).strip())]
        for x in items:
            x = " ".join(str(x).split())
            if not x or STALE.search(x) or x.lower() in seen:
                continue
            seen.add(x.lower())
            out.append(f"{said}: {x}.")
    for k, v in c.brochure.items():   # what the agent confirmed from the brochure kit
        if k.startswith("brochure.") and isinstance(v, list):
            items = [str(x) for x in v if str(x).strip() and not STALE.search(str(x))][:8]
            if items:
                out.append(f"The builder's brochure ({k.split('.', 1)[1].replace('_', ' ')}): {', '.join(items)}.")
    out += list(AGENCY) * ours
    return [{"id": f"F{i + 1}", "text": t} for i, t in enumerate(dict.fromkeys(out))]


def _book_text(facts: Sequence[Dict[str, str]]) -> str:
    return "\n".join(f"{f['id']}: {f['text']}" for f in facts)


# ---- the people --------------------------------------------------------------------------------------------------------------
RULES = ("Rules for everyone in the room: use ONLY the numbered facts; never a number, name, date or claim that is not in them "
         "(no prices beyond the one given, no 'ready to move', no investment returns, no 'best', 'dream', 'guaranteed', 'luxurious'). "
         "Premium words are fine when the facts carry them (a known builder, a named architect, a clubhouse). A price that is a "
         "starting price is always 'from ... onwards'. Keep every fact where it belongs: a feature of one home type (a servant "
         "quarter in the 4 BHK) is never given to another. A MahaRERA registration is a registration: never 'approved', "
         "'trusted' or 'certified'. 'Walk' or 'walking distance' only for a place under 1 km; others are 'X km away'. No "
         "'renowned', 'world-class', 'iconic', 'unmatched'. The only ask is a comment: 'Comment INFO'. Plain English a Pune "
         "buyer speaks. You are a sales team: sell the future the facts give you. Approved or planned infrastructure (a metro "
         "line, a road, an IT park) is a selling point to use, worded as coming ('Metro Line 4 is coming to Kharadi', 'on the "
         "approved metro route'), never as running today and never with a date the facts do not give. Aspirational lines are "
         "welcome when a fact stands behind them; returns, appreciation and 'ready' are not. The project itself is launched "
         "and booking: never 'coming' or 'soon'. Spread the facts across the campaign: each named fact (an architect, a place, "
         "the metro, the price) leads at most one piece and appears in at most two, unless it is the brief's focus (then up "
         "to three, on purpose). When the facts say what booking 'Through Avasetu' gives a buyer, one piece (role why_us) "
         "answers why book through us instead of the builder or another agent, with exactly those points; never 'best deal', "
         "'lowest price' or 'cheapest'.")

STRATEGIST = (
    "You are the marketing strategist of a Pune property agency. From the numbered facts, write the campaign brief. Decide what "
    "this property is (premium brand / mid-range family / first home / plot / rental), who really buys it (2-3 buyer types, "
    "each with why), the single-minded idea to own, the tone, and what would cheapen it. Upcoming infrastructure in the facts "
    "(a metro line, a road) is part of the story to tell, honestly as coming; never list it under what to avoid. " + RULES +
    " Reply JSON only: {\"positioning\": \"...\", \"tier\": \"premium|family|first_home|plot|rental\", \"buyers\": [{\"who\": \"...\", "
    "\"why\": \"...\"}], \"idea\": \"...\", \"focus\": \"the one fact worth repeating on purpose, or empty\", \"tone\": \"...\", \"avoid\": [\"...\"]}")


def _creative(lens: str) -> str:
    title, how = LENSES[lens]
    return (f"You are the {title} in the creative room. {how} {LEAD[lens]} Pitch ONE campaign for this brief: your OWN campaign "
            "name (2-5 words) and your OWN big idea in one sentence (not the brief's words: two other people pitch too, and a "
            "pitch that repeats the brief loses), and 4-6 pieces in posting order, each with a DIFFERENT job in the story (" + ", ".join(ROLES) + "): never two "
            "pieces selling the same thing (at most one about distances). For each piece: role, format (" + ", ".join(FORMATS) +
            "), a headline of at most 9 words, 2-5 short lines (at most 12 words each), the visual (photo, render, floor_plan or "
            "text), the fact ids it uses, and for 2-3 pieces a reel: hook (at most 9 words), 3 beats (at most 8 words each), "
            "a payoff line. " + RULES + " Reply JSON only: {\"name\": \"...\", \"idea\": \"...\", \"pieces\": [{\"role\": \"...\", "
            "\"format\": \"...\", \"headline\": \"...\", \"lines\": [\"...\"], \"visual\": \"...\", \"facts\": [\"F1\"], "
            "\"reel\": {\"hook\": \"...\", \"beats\": [\"...\"], \"payoff\": \"...\"} or null}]}")


# The director assembles by reference (pitch, piece) instead of rewriting every piece: the first live meeting's rewrite was
# too long an answer and came back empty. A borrowed piece has passed the checker already; only a sharpened headline is new.
# Before the director decides, the room talks: each seat builds on another's pitch and names one worry, and the room lists
# the strongest ideas across all pitches (owner: "don't they brainstorm and conclude, take the best, merge").
DISCUSSION = (
    "You are running the creative room's discussion after the pitches. Speak for each seat in turn (" + ", ".join(SEATS) +
    "): what they would take from SOMEONE ELSE's pitch and how they would build on it (one sentence), and one honest concern "
    "(one sentence). Then list the 3 strongest ideas across all the pitches, each with the pitch it came from. Be specific "
    "and constructive, like a good agency team. " + RULES + " Reply JSON only (short): {\"talk\": [{\"seat\": \"...\", "
    "\"builds_on\": 2, \"build\": \"...\", \"concern\": \"...\"}], \"best\": [{\"pitch\": 1, \"idea\": \"...\"}]}")

DIRECTOR = (
    "You are the creative director. You have the brief, the facts, the pitches (each piece numbered) and the room's discussion. "
    "Score each pitch 1-10 for fit with the brief, freshness, and how well it is backed by the facts. Then MERGE: build the "
    "final campaign from the strongest pieces of the pitches, following the discussion's builds, taking pieces from at least "
    "two different pitches when there are two or more: 4-6 pieces in posting order, each with a "
    "different job, never two about the same thing, at most one about distances, and 2-3 of them pieces that have a reel. You "
    "may sharpen a piece's headline (at most 9 words, only from the facts) or leave it empty to keep it. Write each piece's "
    "closing caption question (one line). Give the campaign a name and its idea in one sentence. " + RULES +
    " Reply JSON only (short): {\"scores\": [{\"pitch\": 1, \"score\": 8, \"note\": \"...\"}], \"chosen\": 1, \"why\": \"...\", "
    "\"name\": \"...\", \"idea\": \"...\", \"pieces\": [{\"from\": [1, 2], \"headline\": \"\", \"ask\": \"...\"}]}")


def assemble(refs: Any, pitches: List[Dict[str, Any]], corpus: str) -> List[Dict[str, Any]]:
    """The director's [{from: [pitch, piece], headline, ask}] as pieces: each a copy of a checked piece, with the director's
    headline when it passes the same checks and the closing question when it does."""
    out = []
    for r in (refs if isinstance(refs, list) else [])[:MAX_PIECES]:
        try:
            i, j = (int(x) for x in r.get("from")[:2])
            piece = dict(pitches[i - 1]["pieces"][j - 1], source={"pitch": i, "by": pitches[i - 1]["by"]})
        except (TypeError, ValueError, IndexError, AttributeError, KeyError):
            continue
        head = _clean(r.get("headline"), 10)
        if head and not problems_in(head, corpus) and not overclaims(head, corpus):
            piece["headline"] = head
        ask = _clean(r.get("ask"), 16)
        if ask and not problems_in(ask, corpus) and not overclaims(ask, corpus):
            piece["ask"] = ask
        out.append(piece)
    return out


def _user(facts, room: Dict[str, Any], extra: str = "") -> str:
    brief = room.get("brief") or {}
    parts = ["Facts:\n" + _book_text(facts)]
    if brief:
        parts.append("Brief: " + "; ".join(f"{k}: {v}" for k, v in brief.items() if v))
    if room.get("pictures"):
        parts.append("Pictures we have: " + room["pictures"])
    if extra:
        parts.append(extra)
    return "\n\n".join(parts)


RETRY_WAITS = (20.0, 45.0)   # seconds before asking again: the free model tiers answer 429 for a minute when busy


CREATIVE_HEAT = 0.9   # the pitches: at 0 four seats came back with the same campaign name
STEADY = 0.2          # the strategist and the director


async def _ask(llm: Any, system: str, user: str, waits: Sequence[float] = RETRY_WAITS, heat: float = STEADY) -> Dict[str, Any]:
    """One person's answer as a dict; an empty answer (every provider busy or broken JSON) is asked again after a pause."""
    for wait in (0.0, *waits):
        if wait:
            await asyncio.sleep(wait)
        try:
            try:
                r = await llm.json(system, user, temperature=heat)
            except TypeError:   # a client without the temperature argument
                r = await llm.json(system, user)
        except Exception:
            log.info("creative room: a call failed", exc_info=True)
            r = None
        if isinstance(r, dict) and r:
            return r
    return {}


# ---- the fact checker --------------------------------------------------------------------------------------------------------
def _clean(s: Any, words: int) -> str:
    s = " ".join(str(s or "").replace("*", "").split()).strip()
    return s if s and len(s.split()) <= words else ""


def check(piece: Dict[str, Any], corpus: str) -> Optional[Dict[str, Any]]:
    """The piece with only lines the facts back (guards.problems_in against the whole fact book), or None when its headline
    fails or a post is left with nothing to say."""
    head = _clean(piece.get("headline"), 10)
    if not head or problems_in(head, corpus) or overclaims(head, corpus):
        return None
    lines = [x for x in (_clean(l, 14) for l in (piece.get("lines") or [])[:5]) if x and not problems_in(x, corpus) and not overclaims(x, corpus)]
    if not lines:
        return None
    role = str(piece.get("role") or "").lower().strip()
    fmt = str(piece.get("format") or "").lower().strip()
    out = {"role": role if role in ROLES else "story", "format": fmt if fmt in FORMATS else "single", "headline": head,
           "lines": lines, "visual": str(piece.get("visual") or "photo").lower(), "facts": [str(x) for x in piece.get("facts") or []][:8],
           "ask": _clean(piece.get("ask"), 16) if not problems_in(str(piece.get("ask") or ""), corpus) else ""}
    if out["format"] in ("carousel", "checklist") and len(lines) < 3:
        out["format"] = "single"
    reel = piece.get("reel") if isinstance(piece.get("reel"), dict) else None
    if reel:
        s = ad_reel.Script("story", _clean(reel.get("hook"), 10), [x for x in (_clean(b, 9) for b in reel.get("beats") or []) if x][:5],
                           _clean(reel.get("payoff"), 10), ad_reel.CTA_TEXT, by="room")
        if s.hook and s.payoff and not ad_reel.check(s, corpus) and not any(overclaims(x, corpus) for x in s.lines()):
            out["reel"] = s.out()
    return out


def _pitch(raw: Dict[str, Any], corpus: str, by: str) -> Optional[Dict[str, Any]]:
    pieces = [p for p in (check(x, corpus) for x in (raw.get("pieces") or [])[:MAX_PIECES] if isinstance(x, dict)) if p]
    name, idea = _clean(raw.get("name"), 8), _clean(raw.get("idea"), 30)
    if not pieces or not name:
        return None
    return {"by": by, "name": name, "idea": idea, "pieces": pieces}


def _distinct(pieces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One piece per job and at most one about distances (the Camelot run: three reels of "X km from here")."""
    out, roles, distance = [], set(), False
    for p in pieces:
        far = p["role"] == "location" or bool(re.search(r"\bkm\b", p["headline"]))
        if p["role"] in roles or (far and distance):
            continue
        roles.add(p["role"])
        distance = distance or far
        out.append(p)
    return out


# ---- the meeting -------------------------------------------------------------------------------------------------------------
async def convene(c: Ctx, listing: dict, llm: Any, photos: int = 0, images: Sequence[Dict[str, Any]] = (), ours: bool = False,
                  pick: Optional[int] = None, earlier: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """The room's work: {book, brief, pitches, chosen, why, scores, campaign}, or None when there is no model or too little
    survives the fact check. `pick` (1-based) with `earlier` (a previous room): the agent chose that pitch; the director
    writes the campaign from it, the brief and pitches stay as they were."""
    if llm is None:
        return None
    facts = book(c, listing, ours)
    if len(facts) < 4:
        log.info("creative room: only %d facts", len(facts))
        return None
    corpus = "\n".join(f["text"] for f in facts)   # what the checker reads: the facts without their ids (F12 is not a 12)
    kinds = [str(i.get("kind") or "") for i in images]
    room: Dict[str, Any] = {"book": facts, "pictures": ", ".join(x for x in (
        f"{photos} photos of the property" if photos else "", f"{kinds.count('render')} builder render(s)" if "render" in kinds else "",
        f"{kinds.count('floor_plan')} floor plan(s)" if "floor_plan" in kinds else "") if x) or "text cards only"}
    if earlier and pick:
        room.update({k: earlier.get(k) for k in ("brief", "pitches", "discussion")})
    else:
        brief = await _ask(llm, STRATEGIST, _user(facts, room))
        if not brief.get("idea"):   # a short answer: the positioning is the idea to own
            brief["idea"] = brief.get("positioning")
        if not brief.get("idea"):
            log.info("creative room: the strategist gave no brief (%s)", list(brief)[:6])
            return None
        room["brief"] = {k: brief.get(k) for k in ("positioning", "tier", "buyers", "idea", "focus", "tone", "avoid")}
        raws = [await _ask(llm, _creative(lens), _user(facts, room), heat=CREATIVE_HEAT) for lens in LENSES]   # one at a time: the free tiers rate-limit
        room["pitches"] = [p for p in (_pitch(r, corpus, LENSES[lens][0]) for lens, r in zip(LENSES, raws)) if p]
        log.info("creative room: pitches %s", [(lens, len((r or {}).get("pieces") or []), bool(p)) for lens, r, p in
                                               zip(LENSES, raws, [_pitch(r, corpus, "x") for r in raws])])
    if not room.get("pitches"):
        return None
    listed = "\n\n".join(f"Pitch {i + 1} ({p['by']}): {p['name']}. {p['idea']}\n" + "\n".join(
        f"- piece {j + 1}, {x['role']} / {x['format']}: {x['headline']} | {' / '.join(x['lines'])}" + (" | reel" if x.get("reel") else "")
        for j, x in enumerate(p["pieces"])) for i, p in enumerate(room["pitches"]))
    if len(room["pitches"]) > 1 and not room.get("discussion"):
        room["discussion"] = discuss(await _ask(llm, DISCUSSION, _user(facts, room, "Pitches:\n" + listed), heat=0.6),
                                     len(room["pitches"]))
    talk = room.get("discussion") or {}
    notes = "\n".join([f"- {t['seat']} (on pitch {t['builds_on']}): {t['build']} Concern: {t['concern']}" for t in talk.get("talk") or []]
                      + [f"- Strongest idea (pitch {b['pitch']}): {b['idea']}" for b in talk.get("best") or []])
    steer = f"The agent chose pitch {pick}: build the campaign mostly from it." if pick else ""
    d = await _ask(llm, DIRECTOR, _user(facts, room, "Pitches:\n" + listed + ("\n\nThe room's discussion:\n" + notes if notes else "")
                                        + ("\n\n" + steer if steer else "")))
    chosen = pick or (int(d["chosen"]) if str(d.get("chosen") or "").isdigit() else 1)
    chosen = chosen if 1 <= chosen <= len(room["pitches"]) else 1
    pieces = _distinct(assemble(d.get("pieces"), room["pitches"], corpus))
    if len(pieces) < MIN_PIECES:   # the director's assembly did not hold: the chosen pitch as pitched
        by = room["pitches"][chosen - 1]["by"]
        pieces = _distinct([dict(x, source={"pitch": chosen, "by": by}) for x in room["pitches"][chosen - 1]["pieces"]])
    camp = {"name": d.get("name"), "idea": d.get("idea")}
    scored = {int(s.get("pitch") or 0): int(s.get("score") or 0) for s in d.get("scores") or []
              if isinstance(s, dict) and str(s.get("score") or "").isdigit() and str(s.get("pitch") or "").isdigit()}
    liked = [b["pitch"] for b in (room.get("discussion") or {}).get("best") or [] if b.get("pitch")]
    others = [n for n in dict.fromkeys(liked + sorted(scored, key=lambda n: -scored[n]) + list(range(1, len(room["pitches"]) + 1)))
              if n != chosen and 1 <= n <= len(room["pitches"])]
    terms = heroes(corpus, (c.project, c.locality))
    pieces = complete(_distinct(blend(pieces, room["pitches"], others)), room["pitches"], [chosen, *others], corpus)
    pieces = filmed(spread(pieces, terms, (room.get("brief") or {}).get("focus") or ""), corpus, (c.project, c.locality))
    if len(pieces) < MIN_PIECES:
        log.info("creative room: %d pieces after the director (%d assembled), too few", len(pieces), len(d.get("pieces") or []))
        return None
    reels = 0
    for p in pieces:   # the director's best few reels, in posting order
        if p.get("reel"):
            reels += 1
            if reels > MAX_REELS:
                p.pop("reel")
    room.update({"chosen": chosen, "why": _clean(d.get("why"), 60), "scores": [
        {"pitch": int(s.get("pitch") or 0), "score": int(s.get("score") or 0), "note": _clean(s.get("note"), 30)}
        for s in d.get("scores") or [] if isinstance(s, dict) and str(s.get("score") or "").isdigit()],
        "campaign": {"name": _clean(camp.get("name"), 8) or room["pitches"][chosen - 1]["name"],
                     "idea": _clean(camp.get("idea"), 30) or room["pitches"][chosen - 1]["idea"], "pieces": pieces}})
    room.pop("pictures", None)
    return room


REELS_WANTED = 3


def blend(pieces: List[Dict[str, Any]], pitches: List[Dict[str, Any]], order: Sequence[int]) -> List[Dict[str, Any]]:
    """What the director was told and did not do, done by code (the third live meeting: pitch 1 as pitched, one reel): with
    two or more pitches the campaign carries pieces from at least two (another pitch's piece with a job the campaign lacks,
    else its version of a job that comes with a reel), and pieces without a reel borrow the reel another pitch wrote for the
    same job, up to REELS_WANTED. `order`: the other pitches to borrow from, best first (the discussion, then the scores)."""
    out = [dict(p) for p in pieces]
    if len(pitches) > 1 and len({(p.get("source") or {}).get("pitch") for p in out}) < 2:
        for n in order:
            other = pitches[n - 1]
            src = {"pitch": n, "by": other["by"]}
            have = {p["role"] for p in out}
            new = next((x for x in other["pieces"] if x["role"] not in have), None)
            if new is not None and len(out) < MAX_PIECES:
                out.insert(len(out) - 1 if out and out[-1]["role"] in ("price", "visit") else len(out), dict(new, source=src))
                break
            swap = next(((i, x) for x in other["pieces"] if x.get("reel") for i, p in enumerate(out)
                         if p["role"] == x["role"] and not p.get("reel")), None)
            if swap is not None:
                out[swap[0]] = dict(swap[1], source=src)
                break
    for p in out:
        if sum(1 for x in out if x.get("reel")) >= REELS_WANTED:
            break
        if not p.get("reel"):
            reel = next((x["reel"] for q in pitches for x in q["pieces"] if x["role"] == p["role"] and x.get("reel")), None)
            if reel:
                p["reel"] = dict(reel)
    return out


WANT_PIECES = 5
STORY = ("teaser", "brand", "design", "homes", "lifestyle", "location", "trust", "why_us", "price", "visit", "story")   # posting order
METRO = re.compile(r"\bmetro\b", re.I)


def complete(pieces: List[Dict[str, Any]], pitches: List[Dict[str, Any]], order: Sequence[int], corpus: str) -> List[Dict[str, Any]]:
    """The campaign a sales team would post (the fifth live meeting: three pieces, no price, no metro, amenities first):
    topped up to WANT_PIECES from the pitches (the chosen one first) with jobs it lacks, always one piece that states the
    price, the metro line a pitch wrote carried into the location piece when the facts have a metro and no piece says it,
    and the pieces in story order (teaser, design, homes, lifestyle, location, price)."""
    out = [dict(p, lines=list(p["lines"])) for p in pieces]
    pool = [(n, x) for n in order if 1 <= n <= len(pitches) for x in pitches[n - 1]["pieces"]]
    src = lambda n: {"pitch": n, "by": pitches[n - 1]["by"]}   # noqa: E731

    def says_price(p: Dict[str, Any]) -> bool:
        return bool(PRICE.search(" ".join([p["headline"], *p["lines"]])))
    if PRICE.search(corpus) and not any(says_price(p) for p in out):
        hit = next(((n, x) for n, x in pool if says_price(x) and x["role"] in ("price", "homes")), None) or \
              next(((n, x) for n, x in pool if says_price(x)), None)
        if hit:
            out = [p for p in out if p["role"] != hit[1]["role"]] + [dict(hit[1], source=src(hit[0]))]
    for n, x in pool:
        if len(out) >= WANT_PIECES:
            break
        if x["role"] not in {p["role"] for p in out} and not (x["role"] == "location" and any(p["role"] == "location" for p in out)):
            out.append(dict(x, source=src(n)))
    if METRO.search(corpus) and not any(METRO.search(" ".join([p["headline"], *p["lines"]])) for p in out):
        line = next((l for _, x in pool for l in x["lines"] if METRO.search(l) and not overclaims(l, corpus)
                     and not problems_in(l, corpus)), "")
        spot = next((p for p in out if p["role"] == "location"), None) or next((p for p in out if p["role"] == "teaser"), None)
        if line and spot is not None:
            spot["lines"] = (spot["lines"] + [line])[-5:] if len(spot["lines"]) < 5 else spot["lines"][:4] + [line]
    if "Through Avasetu" in corpus and not any(p["role"] == "why_us" for p in out):   # our campaigns say why book with us
        hit = next(((n, x) for n, x in pool if x["role"] == "why_us"), None)
        out.append(dict(hit[1], source=src(hit[0])) if hit else
                   {"role": "why_us", "format": "checklist", "headline": WHY_US[0], "lines": list(WHY_US[1]), "visual": "text",
                    "facts": [], "ask": "What would you want us to check for you?", "source": {"pitch": 0, "by": "Room"}})
    return sorted(out, key=lambda p: STORY.index(p["role"]) if p["role"] in STORY else len(STORY))


FILM_ROLES = ("design", "lifestyle", "homes", "brand", "teaser", "location", "price", "trust", "why_us", "visit", "story")   # best on film first


HERO = re.compile(r"\b(?:[A-Z][a-zA-Z.&'-]+ ){1,4}[A-Z][a-zA-Z.&'-]+\b|\b[A-Z]{3,}\b")
COMMON = {"mahara", "maharera", "pune", "bhk", "info", "rera"}


def heroes(corpus: str, own: Sequence[str] = ()) -> List[str]:
    """The facts a reel can lead with, as words to look for: named people and places in the fact book ("Hafeez Contractor",
    "SHMA", "International Tech Park Pune"), the metro, the price; never the project's own name or its locality."""
    skip = {w.lower() for name in own for w in str(name or "").split()} | COMMON
    out = [t for t in dict.fromkeys(HERO.findall(corpus)) if not {w.lower() for w in t.split()} <= skip]
    return out + ["metro"] * bool(METRO.search(corpus)) + ["₹"] * bool(PRICE.search(corpus))


def _uses(line: str, terms: Sequence[str]) -> set:
    low = line.lower()
    return {t for t in terms if t.lower() in low}


def spread(pieces: List[Dict[str, Any]], terms: Sequence[str], focus: str = "") -> List[Dict[str, Any]]:
    """Each named fact in at most two pieces (three for the brief's focus), in posting order (owner, 2026-10-15: "not repeated
    much; the most important can be the focus, the team decides"): a later piece's line that brings a fact back once it has
    had its share is dropped; headlines stay, and a piece keeps at least one line."""
    focus_terms = _uses(focus, terms) if focus else set()
    seen: Dict[str, int] = {}
    out = []
    for p in pieces:
        p = dict(p, lines=list(p["lines"]))
        here = _uses(p["headline"], terms)
        lines = []
        for line in p["lines"]:
            over = {t for t in _uses(line, terms) - here if seen.get(t, 0) >= (3 if t in focus_terms else 2)}
            if not over or (not lines and line is p["lines"][-1]):
                lines.append(line)
                here |= _uses(line, terms)
        p["lines"] = lines or p["lines"][:1]
        for t in here:
            seen[t] = seen.get(t, 0) + 1
        out.append(p)
    return out


def filmed(pieces: List[Dict[str, Any]], corpus: str, own: Sequence[str] = ()) -> List[Dict[str, Any]]:
    """Up to REELS_WANTED reels, each leading with its own fact (the Camelot reels all said Hafeez Contractor): a reel whose
    hook repeats a fact an earlier reel used is dropped, and its beats that repeat one are swapped for the piece's other
    lines; then pieces with no reel, the ones film carries best first, get one made from their own words (hook = headline,
    beats = the lines, payoff = the price line once, else the piece's last line), kept only when it passes the reel checks."""
    out = [dict(p) for p in pieces]
    terms = heroes(corpus, own)
    used: set = set()

    def fresh(lines: Sequence[str]) -> List[str]:
        return [b for b in (_clean(str(l).rstrip("."), 9) for l in lines)
                if b and not (_uses(b, terms) & used) and not overclaims(b, corpus)]

    def ending(payoff: str, beats: List[str], p: Dict[str, Any]) -> str:
        """The reel's last line: its own when it passes and brings nothing back, else a spare line of the piece."""
        if payoff and not (_uses(payoff, terms) & used) and not overclaims(payoff, corpus):
            return payoff
        spare = [b for b in fresh(p["lines"]) if b not in beats]
        return spare[0] if spare else (beats.pop() if len(beats) > 2 else "")

    def keep(p: Dict[str, Any], s: ad_reel.Script) -> bool:
        ok = (len(s.beats) >= 2 and bool(s.payoff) and not ad_reel.check(s, corpus)
              and not any(overclaims(x, corpus) for x in s.lines()))
        if ok:
            p["reel"] = s.out()
            used.update(*(_uses(x, terms) for x in s.lines()))
        return ok

    for p in out:   # the room's own reels, in posting order
        r = p.pop("reel", None)
        if not r or _uses(r["hook"], terms) & used:
            continue
        beats = fresh(r["beats"])
        beats = (beats + [b for b in fresh(p["lines"]) if b not in beats])[:3] if len(beats) < 2 else beats
        payoff = ending(r["payoff"], beats, p)
        keep(p, ad_reel.Script("story", r["hook"], beats, payoff, r.get("cta") or ad_reel.CTA_TEXT, by="room"))
    price = next((p["headline"] for p in out if PRICE.search(p["headline"])), "")
    for p in sorted(out, key=lambda p: FILM_ROLES.index(p["role"]) if p["role"] in FILM_ROLES else 99):
        if sum(1 for x in out if x.get("reel")) >= REELS_WANTED:
            break
        if p.get("reel") or _uses(p["headline"], terms) & used:
            continue
        beats = fresh(p["lines"])[:3]
        payoff = ending(price if price != p["headline"] else "", beats, p)
        keep(p, ad_reel.Script("story", p["headline"], beats, payoff, ad_reel.CTA_TEXT, by="room"))
    return out


def discuss(raw: Dict[str, Any], pitches: int) -> Dict[str, Any]:
    """The discussion as kept on the run and shown in Studio: each seat's build and concern, the strongest ideas. Internal
    notes (never posted), so only trimmed and bounded, not fact-checked."""
    def pitch_no(x: Any) -> int:
        try:
            n = int(x)
        except (TypeError, ValueError):
            return 0
        return n if 1 <= n <= pitches else 0
    talk = [{"seat": _clean(t.get("seat"), 4) or "Room", "builds_on": pitch_no(t.get("builds_on")),
             "build": _clean(t.get("build"), 45), "concern": _clean(t.get("concern"), 40)}
            for t in (raw.get("talk") or [])[:6] if isinstance(t, dict)]
    best = [{"pitch": pitch_no(b.get("pitch")), "idea": _clean(b.get("idea"), 30)} for b in (raw.get("best") or [])[:3]
            if isinstance(b, dict)]
    return {"talk": [t for t in talk if t["build"] or t["concern"]], "best": [b for b in best if b["idea"]]}


# ---- the producer: pieces -> briefs and reel scripts ---------------------------------------------------------------------------
def angle_id(i: int, piece: Dict[str, Any]) -> str:
    return f"room{i + 1}_{piece['role']}"


def briefs(room: Dict[str, Any], c: Ctx, photos: Sequence[str] = (), images: Sequence[Dict[str, Any]] = ()) -> List[Tuple[str, Brief]]:
    """A Brief per piece for the design desk: the director's headline as the hook, its lines as the slides or the card text,
    the fact book as the only facts, a picture by the piece's visual (a render or plan from the confirmed brochure images,
    else the next of the property's photos)."""
    facts = [f["text"] for f in room.get("book") or []]
    camp = room.get("campaign") or {}
    renders = [i for i in images if i.get("kind") == "render"]
    plans = [i for i in images if i.get("kind") == "floor_plan"]
    out: List[Tuple[str, Brief]] = []
    k = 0
    for i, p in enumerate(camp.get("pieces") or []):
        kw: Dict[str, Any] = {"facts": facts, "topic": p["headline"], "short": p["role"],
                              "asks": {"en": p["ask"]} if p.get("ask") else {}}
        if p["format"] in ("carousel", "checklist") and len(p["lines"]) >= 3:
            kw.update(steps=p["lines"], prefer=p["format"])
        elif p["format"] == "stat" and stat_of(p["headline"]):
            kw.update(stat_value=stat_of(p["headline"]), stat_label=p["headline"], prefer="stat",
                      tip=" ".join(p["lines"])[:160])
        else:
            kw.update(tip=" ".join(p["lines"])[:160], prefer="single")
        b = c.brief(hook=p["headline"], angle="", **kw)
        visual = p.get("visual") or ""
        if "render" in visual and renders:
            b = replace(b, plan_image=renders[0]["path"], plan_label="Artist's impression", plan_fit="cover")
        elif "plan" in visual and plans:
            b = replace(b, plan_image=plans[0]["path"], plan_label="Floor plan", plan_fit="contain")
        elif photos and "text" not in visual:
            b = replace(b, photo=photos[k % len(photos)])
            k += 1
        b = replace(b, writer_note=(b.writer_note + f"\nThis is piece {i + 1} of the campaign \"{camp.get('name')}\" ({camp.get('idea')}). "
                                    f"Its job: {p['role']}. Keep the headline as written; the body says these lines in a "
                                    f"{(room.get('brief') or {}).get('tone') or 'calm, clear'} voice: " + " / ".join(p["lines"])))
        out.append((angle_id(i, p), b))
    return out


def scripts(room: Optional[Dict[str, Any]]) -> Dict[str, ad_reel.Script]:
    """{angle id: reel script} for the pieces the director gave a reel."""
    out = {}
    for i, p in enumerate(((room or {}).get("campaign") or {}).get("pieces") or []):
        r = p.get("reel")
        if r:
            out[angle_id(i, p)] = ad_reel.Script("story", r["hook"], list(r["beats"]), r["payoff"], r["cta"], by="room")
    return out
