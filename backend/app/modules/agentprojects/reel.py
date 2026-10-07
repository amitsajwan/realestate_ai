"""A short vertical reel (9:16) for one project, drawn with the reels compositor: area photo cover, prices, the MahaRERA check,
possession, and a closing ask in the agent's name. Same facts as the carousel; no phone number on screen (reels rule)."""
from pathlib import Path
from typing import List

from app.modules.reels.compose import Scene, TextLine, make_reel

from .cards import ASSETS, bhk_range, day, lakh, price_range


def scenes(p: dict, agent: dict) -> List[Scene]:
    r = p.get("rera") or {}
    media = next((m for m in p.get("media") or [] if m.get("kind", "image") == "image"), None)
    photo = ASSETS / Path(media["url"]).name if media else None
    out = [Scene(image=photo if photo and photo.is_file() else None, kicker=f"{p['locality'].upper()} · PUNE",
                 lines=[TextLine(p["name"], max_lines=3), f"*{price_range(p)}* · {bhk_range(p.get('bhk_options') or [])}"],
                 badge="AREA PHOTO, NOT THE PROJECT" if photo else None, layout="lower", seconds=3.6, seed=p["slug"] + "-1")]
    confs = (p.get("configurations") or [])[:3]
    out.append(Scene(kicker=f"PRICES AS QUOTED BY {agent['name'].upper()}",
                     lines=["Prices and sizes"] + [f"{c['label']} · {c['carpet_sqft']} sq ft · *{lakh(c['price_inr'])}*" for c in confs],
                     seconds=3.8, seed=p["slug"] + "-2"))
    if p.get("booked_pct") is not None:
        out.append(Scene(kicker="CHECKED ON MAHARERA",
                         lines=[f"*{p['booked_pct']}%* of {r.get('units_total')} homes booked",
                                f"Completion date filed: {day(r.get('completion_now'))}"], seconds=3.6, seed=p["slug"] + "-3"))
    if p.get("possession_target") and r.get("completion_now"):
        out.append(Scene(kicker="WHEN COULD YOU MOVE IN?",
                         lines=["Two dates", f"Builder's target: {day(p['possession_target'])}", f"MahaRERA date: *{day(r['completion_now'])}*",
                                "Plan around the MahaRERA date"], seconds=3.8, seed=p["slug"] + "-4"))
    out.append(Scene(kicker=agent["name"].upper(), lines=["Want prices for your floor?", "Comment *PRICE*"],
                     seconds=3.0, seed=p["slug"] + "-5"))
    return out


def render(p: dict, agent: dict, out: Path, music=None) -> Path:
    return make_reel(scenes(p, agent), out, music=music, end_card=False)
