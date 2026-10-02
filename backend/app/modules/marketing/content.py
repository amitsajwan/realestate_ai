"""Deterministic marketing copy built ONLY from listing facts. No network, no invented amenities/prices/claims."""
import re
import unicodedata
from typing import Dict, List, Optional

from .facts import SUPPORTED, T, Facts

HEADLINE_MAX = 90
CAPTION_MAX = 900
HASHTAGS_MAX = 12
FB_MAX = 2000
WA_MAX = 600
STATUS_MAX = 200

# language -> phrases that are not facts (calls to action, reel directions).
# No phone numbers anywhere: buyers comment INTERESTED, message, or use the listing link; the agent's tools answer them.
P = {
    "en": {
        "cta": "💬 Interested? Comment INTERESTED and {agent} will share the details and plan a site visit.",
        "cta_anon": "💬 Interested? Comment INTERESTED and we will share the details and plan a site visit.",
        "wa_hi": "Hi! ", "wa_link": "Details and photos: {url}", "wa_ask": "Reply here to plan a visit.",
        "status_cta": "Reply INTERESTED for details", "reel_cta": "Comment INTERESTED for a site visit",
        "v_hook": "Cover photo with the headline text", "v_prop": "Photo of the main room, text overlay",
        "v_loc": "Photo or map pin of the locality", "v_price": "Price on a plain card", "v_cta": "Agent name card",
        "am": "Amenities: {items}", "link": "🔗 Details and photos: {url}",
        "avail": "✅ Available as of {d}", "bio": "🔗 Full details and photos: link in bio",
        "where": " in {loc}", "guess": "Guess the price of this {what}{where}", "guess_rent": "Guess the rent of this {what}{where}",
        "live": "Would you live in this {what}{where}?", "reveal": "{price}. Did you guess right?",
    },
    "hi": {
        "cta": "💬 रुचि है? कमेंट में INTERESTED लिखें, {agent} विवरण भेजेंगे और साइट विज़िट तय करेंगे।",
        "cta_anon": "💬 रुचि है? कमेंट में INTERESTED लिखें, हम विवरण भेजेंगे और साइट विज़िट तय करेंगे।",
        "wa_hi": "नमस्ते! ", "wa_link": "विवरण और फोटो: {url}", "wa_ask": "साइट विज़िट के लिए यहीं जवाब दें।",
        "status_cta": "विवरण के लिए INTERESTED लिखकर जवाब दें",
        "reel_cta": "साइट विज़िट के लिए INTERESTED लिखें",
        "v_hook": "कवर फोटो और हेडलाइन टेक्स्ट", "v_prop": "मुख्य कमरे की फोटो, ऊपर टेक्स्ट",
        "v_loc": "इलाके की फोटो या मैप पिन", "v_price": "सादे कार्ड पर कीमत", "v_cta": "एजेंट के नाम का कार्ड",
        "am": "सुविधाएं: {items}", "link": "🔗 विवरण और फोटो: {url}",
        "avail": "✅ {d} तक उपलब्ध", "bio": "🔗 पूरा विवरण और फोटो: बायो में लिंक",
        "where": "{loc} में ", "guess": "{where}इस {what} की कीमत का अंदाज़ा लगाइए", "guess_rent": "{where}इस {what} के किराये का अंदाज़ा लगाइए",
        "live": "क्या आप {where}इस {what} में रहना चाहेंगे?", "reveal": "{price}. क्या आपका अंदाज़ा सही था?",
    },
    "mr": {
        "cta": "💬 आवड आहे? कमेंटमध्ये INTERESTED लिहा, {agent} तपशील पाठवतील आणि साइट व्हिजिट ठरवतील.",
        "cta_anon": "💬 आवड आहे? कमेंटमध्ये INTERESTED लिहा, आम्ही तपशील पाठवू आणि साइट व्हिजिट ठरवू.",
        "wa_hi": "नमस्कार! ", "wa_link": "तपशील आणि फोटो: {url}", "wa_ask": "साइट व्हिजिटसाठी इथेच उत्तर द्या.",
        "status_cta": "तपशिलासाठी INTERESTED लिहून उत्तर द्या",
        "reel_cta": "साइट व्हिजिटसाठी INTERESTED लिहा",
        "v_hook": "कव्हर फोटो आणि हेडलाइन मजकूर", "v_prop": "मुख्य खोलीचा फोटो, वर मजकूर",
        "v_loc": "परिसराचा फोटो किंवा मॅप पिन", "v_price": "साध्या कार्डवर किंमत", "v_cta": "एजंटच्या नावाचे कार्ड",
        "am": "सुविधा: {items}", "link": "🔗 तपशील आणि फोटो: {url}",
        "avail": "✅ {d} रोजी उपलब्ध", "bio": "🔗 संपूर्ण तपशील आणि फोटो: बायोमध्ये लिंक",
        "where": "{loc} येथील ", "guess": "अंदाज लावा: {where}या {what}ची किंमत किती?", "guess_rent": "अंदाज लावा: {where}या {what}चे भाडे किती?",
        "live": "{where}या {what}मध्ये राहायला आवडेल का?", "reveal": "{price}. तुमचा अंदाज बरोबर होता का?",
    },
}


def resolve_language(requested: str) -> str:
    """Language actually used (unsupported requests fall back to English)."""
    return requested if requested in SUPPORTED else "en"


def clip(text: str, n: int) -> str:
    """Hard length limit on a word boundary (last resort; builders already drop optional parts first)."""
    if len(text) <= n:
        return text
    cut = text[: n - 1].rsplit(" ", 1)[0].rstrip(" ,.;:|-")
    return cut + "…"


def sanitize_hashtag(raw: str) -> str:
    """Letters/digits only (Devanagari marks kept), each word capitalised: 'pimple saurabh' -> 'PimpleSaurabh'."""
    words = re.split(r"[\s_\-/]+", raw.strip())
    out = ""
    for w in words:
        w = "".join(c for c in w if c.isalnum() or unicodedata.category(c).startswith("M"))
        out += w[:1].upper() + w[1:]
    return out[:30]


def hashtags(f: Facts) -> List[str]:
    """City / locality / BHK / type / transaction tags, sanitised, de-duplicated, max 12."""
    raw = [f.locality, f.city, f.bhk_text, f.type_text("en"), "for sale" if not f.rent else "for rent",
           f"{f.locality} property" if f.locality else None, f"{f.city} real estate" if f.city else None,
           f"{f.city} property" if f.city else None, f.project, "real estate", "property"]
    seen, out = set(), []
    for r in raw:
        if not r:
            continue
        tag = sanitize_hashtag(r)
        if len(tag) < 2 or tag.lower() in seen:
            continue
        seen.add(tag.lower())
        out.append("#" + tag)
    return out[:HASHTAGS_MAX]


def _summary_line(f: Facts, lang: str) -> str:
    bits = [f.price_text, f.area_text, f.possession_text(lang)]
    return " · ".join(b for b in bits if b)


def headline(f: Facts, lang: str) -> str:
    price = f" | {f.price_text}" if f.price_text else ""
    for title in (f.title_line(lang), f.title_line(lang).replace(f", {f.city}", "") if f.city else "",
                  f"{f.bhk_text or f.type_text(lang)} {f.locality or f.city or ''}".strip()):
        if title and len(title + price) <= HEADLINE_MAX:
            return title + price
    return clip(f.title_line(lang) + price, HEADLINE_MAX)


def _amen(f: Facts, lang: str, n: int) -> Optional[str]:
    return P[lang]["am"].format(items=", ".join(f.amenities[:n])) if f.amenities else None


def _cta(f: Facts, lang: str, key: str = "cta") -> str:
    p = P[lang]
    return p[key].format(agent=f.agent_name) if f.agent_name else p[key + "_anon"]


SAMPLE_LINE = "SAMPLE LISTING (an illustration of how a listing looks on PUNE Property, not available for sale)"


def instagram_caption(f: Facts, lang: str) -> str:
    """Short and visual, one emoji, ends with the call to action."""
    head = f"\U0001F3E1 {f.title_line(lang)}"
    must = ([SAMPLE_LINE] if f.sample else []) + [head, _summary_line(f, lang)]
    if f.rera:
        must.append(f"RERA: {f.rera}")
    optional = [_amen(f, lang, 4), f.project]
    cta = _cta(f, lang)
    if f.share_url:  # Instagram captions are not clickable: point to the link in bio (the agent's site)
        cta = P[lang]["bio"] + "\n" + cta
    lines = [x for x in must if x]
    for extra in optional:
        if extra and len("\n".join(lines + [extra]) + "\n\n" + cta) <= CAPTION_MAX:
            lines.append(extra)
    text = "\n".join(lines) + "\n\n" + cta
    return text if len(text) <= CAPTION_MAX else head + "\n\n" + cta


def facebook_post(f: Facts, lang: str) -> str:
    """More detail, short paragraphs."""
    t = T[lang]
    p1 = (SAMPLE_LINE + "\n\n" if f.sample else "") + f"\U0001F3E1 {f.title_line(lang)}" + (f"\n{f.price_text}" if f.price_text else "")
    if f.project:
        p1 += f"\n{f.project}"
    details = []
    if f.area_text:
        kind = f" ({f.area_kind})" if lang == "en" and f.area_kind else ""
        details.append(f"\U0001F4D0 {t['area']}: {f.area_text}{kind}")
    for extra in (f.floor_text(lang), t["furn"].get(f.furnishing or "")):
        if extra:
            details.append(f"▪ {extra}")
    if f.possession_text(lang):
        details.append(f"✅ {t['possession']}: {f.possession_text(lang)}")
    if f.rera:
        details.append(f"▪ RERA: {f.rera}")
    paras = [p1]
    if details:
        paras.append("\n".join(details))
    if f.amenities:
        paras.append(_amen(f, lang, 10))
    cta = _cta(f, lang)
    if f.share_url:  # Facebook links are clickable; src=facebook shows up as the channel in leads
        cta = P[lang]["link"].format(url=f.share_url.replace("src=whatsapp", "src=facebook")) + "\n\n" + cta
    paras.append(cta)
    return clip("\n\n".join(paras[:-1]), FB_MAX - len(cta) - 2) + "\n\n" + cta


def group_post(f: Facts, lang: str) -> str:
    """Short, photo-first text for WhatsApp / Facebook groups. The agent adds their own contact line in the app; nothing personal is generated here.
    Groups punish stale posts, so the 'available as of' date is part of it. Enquiries from it are tracked as source 'fbgroup'."""
    p = P[lang]
    lines = [SAMPLE_LINE] if f.sample else []
    lines.append(f"\U0001F3E1 {f.title_line(lang)}")
    facts_line = _summary_line(f, lang)
    if facts_line:
        lines.append(facts_line)
    if f.loc:
        lines.append(f"\U0001F4CD {f.loc}")
    if f.rera:
        lines.append(f"RERA: {f.rera}")
    if f.amenities:
        lines.append(_amen(f, lang, 5))
    if f.as_of:
        lines.append(p["avail"].format(d=f.as_of))
    if f.share_url:
        lines.append(p["link"].format(url=f.share_url.replace("src=whatsapp", "src=fbgroup")))
    return "\n".join(x for x in lines if x)


def whatsapp_message(f: Facts, lang: str) -> str:
    """2-3 short conversational lines including the listing link."""
    p = P[lang]
    line1 = ("SAMPLE LISTING (not available). " if f.sample else "") + p["wa_hi"] + f.title_line(lang) + (f" - {f.price_text}" if f.price_text else "")
    extra = ", ".join(x for x in (f.area_text, f.possession_text(lang)) if x)
    if extra:
        line1 += f" ({extra})"
    if f.rera:
        line1 += f". RERA: {f.rera}"
    return clip(line1, WA_MAX - len(p["wa_link"]) - len(f.share_url) - 4) + "\n" + \
        p["wa_link"].format(url=f.share_url) + "\n" + p["wa_ask"]


def status_text(f: Facts, lang: str) -> str:
    bits = [f.bhk_text or f.type_text(lang), f.locality or f.city, f.price_text]
    return clip(" | ".join(b for b in bits if b) + "\n" + P[lang]["status_cta"], STATUS_MAX)


def reel_hook(f: Facts, lang: str) -> str:
    """Opening line that stops the scroll, built from the listing facts only. With a price: 'guess the price', revealed near the end
    (people watch to the reveal and comment their guess). Without one: a question that invites comments."""
    p = P[lang]
    what = f"{f.bhk_text} {f.type_text(lang)}" if f.bhk_text else f.type_text(lang)
    where = p["where"].format(loc=f.locality or f.city) if (f.locality or f.city) else ""
    key = ("guess_rent" if f.rent else "guess") if f.price_text else "live"
    return p[key].format(what=what, where=where).replace("  ", " ").strip()


def reel(f: Facts, lang: str) -> Dict:
    """Script only: hook -> property -> location -> price reveal -> call to action, ~15 s."""
    p = P[lang]
    prop = " · ".join(x for x in (f"{f.bhk_text} {f.type_text(lang)}" if f.bhk_text else f.type_text(lang),
                                  f.area_text, f.possession_text(lang)) if x)
    hook = reel_hook(f, lang)
    cta = P[lang]["reel_cta"]
    beats = [
        {"seconds": "0-3s", "text": hook, "visual": p["v_hook"]},
        {"seconds": "3-6s", "text": prop, "visual": p["v_prop"]},
        {"seconds": "6-9s", "text": f.loc or "", "visual": p["v_loc"]},
        {"seconds": "9-12s", "text": p["reveal"].format(price=f.price_text) if f.price_text else "", "visual": p["v_price"]},
        {"seconds": "12-15s", "text": cta, "visual": p["v_cta"]},
    ]
    return {"hook": hook, "beats": [b for b in beats if b["text"]], "cta": cta, "duration_s": 15}


def build_content(f: Facts, language: str) -> Dict:
    """All copy for one language. Returns plain dict (service turns it into the pack)."""
    lang = resolve_language(language)
    return {
        "language": lang, "angle": f.angle(), "headline": headline(f, lang),
        "instagram": {"caption": instagram_caption(f, lang), "hashtags": hashtags(f)},
        "facebook": {"post": facebook_post(f, lang)},
        "whatsapp": {"message": whatsapp_message(f, lang), "status_text": status_text(f, lang)},
        "group": {"post": group_post(f, lang)},
        "reel": reel(f, lang),
    }
