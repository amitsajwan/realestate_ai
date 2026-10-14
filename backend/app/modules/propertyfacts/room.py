"""The creative room: a campaign is pitched and chosen before anything is drawn (owner, 2026-10-14: "not randomly a reel or a
post; a team that brainstorms concepts, thinks from different angles and pitches, like a good agency").

    room = await convene(ctx, listing, llm, photos=4, images=kit_images)
    planned = briefs(room, ctx, photos, images)      # [(angle id, Brief)] for campaign.make
    reels = scripts(room)                            # {angle id: ad_reel.Script} for the ad reels

Who is in the room (each one an LLM call with its own brief; JSON in, JSON out):

  strategist          the facts in, the brief out: what this property is (premium brand, family, first home, plot), who buys it
                      and why, the one idea to own, the tone, what to avoid
  copywriter          \
  art director         } one campaign pitch each, from its own lens (words, pictures, film), in parallel
  film director       /
  creative director   scores the pitches against the brief and the facts, picks one, borrows the best of the others, and
                      writes the campaign: 4-6 pieces, each with a different job in the story, in posting order

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
ROLES = ("teaser", "brand", "design", "homes", "lifestyle", "location", "price", "trust", "visit")
FORMATS = ("carousel", "stat", "single", "checklist")
# a brochure or agent line that goes stale or promises stock: never a fact a post may state
STALE = re.compile(r"\bavailab|\bbooking|\boffer\b|\bdiscount|\blimited\b|\blast few\b|\bhurry|\bany (?:tower|floor)", re.I)
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
}
# where each one starts, so the three pitches differ (the first live room: three pitches named after the brief's own line)
LEAD = {
    "copywriter": "Start from one of the brief's buyers: the life this home gives them, told as a story across the posts.",
    "art_director": "Start from the place itself: its design, architecture, landscape and spaces, shown before price or distance.",
    "film_director": "Start from a moment: a morning, a commute, an arrival home; the campaign plays like short scenes.",
}
# what the checker cuts whatever the prompt said: registration sold as approval, puffery, a walk to somewhere a car is needed
OVERCLAIM = re.compile(r"\b(?:approved|trusted|certified|endorsed)\b[^.]{0,30}\b(?:rera|maharera|regulator)|\b(?:rera|maharera|regulator)s?\b"
                       r"[^.]{0,20}\b(?:approved|trusted|certified)\b|\b(?:renowned|world[\s-]*class|iconic|unmatched|unparalleled)\b", re.I)
WALK = re.compile(r"\bwalk(?:ing|able)?\b", re.I)
KM = re.compile(r"(\d+(?:\.\d+)?)\s*km\b", re.I)


def overclaims(text: str) -> bool:
    """A registration sold as an approval, puffery, or a walk to a place 1 km or more away (or with no distance at all)."""
    if OVERCLAIM.search(text):
        return True
    if WALK.search(text):
        kms = [float(x) for x in KM.findall(text)]
        return not kms or max(kms) >= 1
    return False


# ---- the fact book: every claim a piece may make, numbered --------------------------------------------------------------------
def book(c: Ctx, listing: dict) -> List[Dict[str, str]]:
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
         "buyer speaks.")

STRATEGIST = (
    "You are the marketing strategist of a Pune property agency. From the numbered facts, write the campaign brief. Decide what "
    "this property is (premium brand / mid-range family / first home / plot / rental), who really buys it (2-3 buyer types, "
    "each with why), the single-minded idea to own, the tone, and what would cheapen it. " + RULES +
    " Reply JSON only: {\"positioning\": \"...\", \"tier\": \"premium|family|first_home|plot|rental\", \"buyers\": [{\"who\": \"...\", "
    "\"why\": \"...\"}], \"idea\": \"...\", \"tone\": \"...\", \"avoid\": [\"...\"]}")


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
DIRECTOR = (
    "You are the creative director. You have the brief, the facts and the pitches, each piece numbered. Score each pitch 1-10 "
    "for fit with the brief, freshness, and how well it is backed by the facts. Pick the best, then assemble the final "
    "campaign from the pitches' pieces: 4-6 pieces in posting order, borrowing the strongest from any pitch, each with a "
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
            piece = dict(pitches[i - 1]["pieces"][j - 1])
        except (TypeError, ValueError, IndexError, AttributeError, KeyError):
            continue
        head = _clean(r.get("headline"), 10)
        if head and not problems_in(head, corpus) and not overclaims(head):
            piece["headline"] = head
        ask = _clean(r.get("ask"), 16)
        if ask and not problems_in(ask, corpus) and not overclaims(ask):
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


async def _ask(llm: Any, system: str, user: str) -> Dict[str, Any]:
    try:
        r = await llm.json(system, user)
        return r if isinstance(r, dict) else {}
    except Exception:
        log.info("creative room: a call failed", exc_info=True)
        return {}


# ---- the fact checker --------------------------------------------------------------------------------------------------------
def _clean(s: Any, words: int) -> str:
    s = " ".join(str(s or "").replace("*", "").split()).strip()
    return s if s and len(s.split()) <= words else ""


def check(piece: Dict[str, Any], corpus: str) -> Optional[Dict[str, Any]]:
    """The piece with only lines the facts back (guards.problems_in against the whole fact book), or None when its headline
    fails or a post is left with nothing to say."""
    head = _clean(piece.get("headline"), 10)
    if not head or problems_in(head, corpus) or overclaims(head):
        return None
    lines = [x for x in (_clean(l, 14) for l in (piece.get("lines") or [])[:5]) if x and not problems_in(x, corpus) and not overclaims(x)]
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
                           _clean(reel.get("payoff"), 10), f"Comment {ad_reel.CTA_WORD} for the details", by="room")
        if s.hook and s.payoff and not ad_reel.check(s, corpus) and not any(overclaims(x) for x in s.lines()):
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
async def convene(c: Ctx, listing: dict, llm: Any, photos: int = 0, images: Sequence[Dict[str, Any]] = (),
                  pick: Optional[int] = None, earlier: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """The room's work: {book, brief, pitches, chosen, why, scores, campaign}, or None when there is no model or too little
    survives the fact check. `pick` (1-based) with `earlier` (a previous room): the agent chose that pitch; the director
    writes the campaign from it, the brief and pitches stay as they were."""
    if llm is None:
        return None
    facts = book(c, listing)
    if len(facts) < 4:
        return None
    corpus = "\n".join(f["text"] for f in facts)   # what the checker reads: the facts without their ids (F12 is not a 12)
    kinds = [str(i.get("kind") or "") for i in images]
    room: Dict[str, Any] = {"book": facts, "pictures": ", ".join(x for x in (
        f"{photos} photos of the property" if photos else "", f"{kinds.count('render')} builder render(s)" if "render" in kinds else "",
        f"{kinds.count('floor_plan')} floor plan(s)" if "floor_plan" in kinds else "") if x) or "text cards only"}
    if earlier and pick:
        room.update({k: earlier.get(k) for k in ("brief", "pitches")})
    else:
        brief = await _ask(llm, STRATEGIST, _user(facts, room))
        if not brief.get("idea"):
            return None
        room["brief"] = {k: brief.get(k) for k in ("positioning", "tier", "buyers", "idea", "tone", "avoid")}
        raws = await asyncio.gather(*(_ask(llm, _creative(lens), _user(facts, room)) for lens in LENSES))
        room["pitches"] = [p for p in (_pitch(r, corpus, LENSES[lens][0]) for lens, r in zip(LENSES, raws)) if p]
    if not room.get("pitches"):
        return None
    listed = "\n\n".join(f"Pitch {i + 1} ({p['by']}): {p['name']}. {p['idea']}\n" + "\n".join(
        f"- piece {j + 1}, {x['role']} / {x['format']}: {x['headline']} | {' / '.join(x['lines'])}" + (" | reel" if x.get("reel") else "")
        for j, x in enumerate(p["pieces"])) for i, p in enumerate(room["pitches"]))
    steer = f"The agent chose pitch {pick}: assemble the campaign mostly from it." if pick else ""
    d = await _ask(llm, DIRECTOR, _user(facts, room, "Pitches:\n" + listed + ("\n\n" + steer if steer else "")))
    chosen = pick or (int(d["chosen"]) if str(d.get("chosen") or "").isdigit() else 1)
    chosen = chosen if 1 <= chosen <= len(room["pitches"]) else 1
    pieces = _distinct(assemble(d.get("pieces"), room["pitches"], corpus))
    if len(pieces) < MIN_PIECES:   # the director's assembly did not hold: the chosen pitch as pitched
        pieces = _distinct(room["pitches"][chosen - 1]["pieces"])
    camp = {"name": d.get("name"), "idea": d.get("idea")}
    if len(pieces) < MIN_PIECES:
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
