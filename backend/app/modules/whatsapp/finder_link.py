"""The home finder's link for what a buyer told us in a chat (owner 2026-10-30: "2 BHK Wagholi" gets the list, not one card).

The site's finder (frontend lib/site/finder.ts) reads area, bhk and budget from the address; this writes the same address from
the chat's data, so the reply carries every project that fits, agent-listed first, as a link the buyer can open and send on.
The budget is the band the buyer's top figure falls in, the same five bands the site offers.
"""
from typing import Optional
from urllib.parse import urlencode

from app.core.areas import AREAS

# (band key, the band's top in rupees, how it reads): the site's BUDGETS
BANDS = (("under-75l", 7_500_000, "under ₹75 L"), ("75l-1cr", 10_000_000, "under ₹1 Cr"), ("1-1.5cr", 15_000_000, "under ₹1.5 Cr"),
         ("1.5-2.5cr", 25_000_000, "under ₹2.5 Cr"), ("above-2.5cr", None, "above ₹2.5 Cr"))

LINE = {
    "en": "All {what}, with prices and MahaRERA checks: {url}",
    "hinglish": "Saare {what}, prices aur MahaRERA check ke saath: {url}",
    "hi": "सभी {what}, कीमत और MahaRERA जाँच के साथ: {url}",
    "mr_latn": "Saglya {what}, kimat ani MahaRERA check sobat: {url}",
    "mr": "सगळे {what}, किंमत आणि MahaRERA तपासणीसह: {url}",
}


def _area(locality: Optional[str]):
    want = (locality or "").strip().lower()
    return next((a for a in AREAS if a.name.lower() == want or a.slug == want.replace(" ", "-")), None) if want else None


def finder_query(data: dict) -> Optional[dict]:
    """{area, bhk, budget, words} from the chat's data; None when it knows nothing the finder asks, or they want to rent."""
    if (data.get("tx") or "sale") != "sale":
        return None
    q, words = {}, []
    bhk = data.get("bhk")
    if isinstance(bhk, (int, float)) and bhk >= 1:
        q["bhk"] = "4" if bhk >= 4 else str(int(bhk))
        words.append("4+ BHK" if bhk >= 4 else f"{int(bhk)} BHK")
    else:
        words.append("new projects")
    area = _area(data.get("locality"))
    if area:
        q["area"] = area.slug
        words.append(f"in {area.name}")
    top = data.get("budget_max")
    if isinstance(top, (int, float)) and top > 0:
        key, _, said = next(b for b in BANDS if b[1] is None or top <= b[1])
        q["budget"] = key
        words.append(said)
    return {**q, "words": " ".join(words)} if ("area" in q or "bhk" in q or "budget" in q) else None


def finder_line(data: dict, site: str, lang: str = "en") -> Optional[str]:
    """One line with the finder's link for what the buyer asked, or None; `site` is the public origin."""
    q = finder_query(data)
    if not q or not site:
        return None
    params = {k: q[k] for k in ("area", "budget", "bhk") if k in q}
    url = f"{site.rstrip('/')}/projects?{urlencode({**params, 'src': 'whatsapp'})}#find"
    return LINE.get(lang, LINE["en"]).format(what=q["words"], url=url)
