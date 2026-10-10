"""Reach: each post's best few hashtags (5 on Instagram, 3 on Facebook) and a location tag.

Applied to every calendar row just before it is published. The caption's own hashtags are taken off and one line of tags
goes at the end, most specific first:
  1. the locality: one of our areas (app.core.areas, with its own tags) or any other locality the row names
     ("Gulmohar City, Ranjangaon." -> #Ranjangaon), so a plot in Ranjangaon is not tagged as only "Pune";
  2. the project, when the row is about a named one (#GulmoharCity), then the audience's own tag (segment_tag: #2BHKWagholi,
     #FlatsForRentPune, #NAPlotsPune, #AffordableHomesPune; on Facebook it takes the type tag's place);
  3. the property type when it is known (#PlotsInPune, #FlatsInPune, ...; not on Facebook when there is a project tag),
     then #<Locality>RealEstate (#WagholiRealEstate);
  4. the caption's own specific tags (the generator put them there on purpose: #StampDuty on a stamp-duty guide; a tag
     counts as specific when its words are in the caption), then #PuneProperty and #MahaRERA (when the row has a MahaRERA
     number or tag), then the area's second tag, the caption's other tags and fillers.
Duplicates are dropped whatever their case. Agent-recruitment posts get the agent tags. Areas live in app.core.areas only:
other localities are worked out here and never added there (that list drives area pages and the daily area reels).

Location tags need Facebook place ids from the environment: one per area (`Area.location_env`, e.g. IG_LOCATION_WAGHOLI),
one per other locality (IG_LOCATION_<NAME>, e.g. IG_LOCATION_RANJANGAON), else IG_LOCATION_PUNE; left out when unset. Instagram posts and reels carry it as `location_id`, Facebook Page
posts as `place` (Facebook Page reels go out without one).
"""
import os
import re
from typing import List, Optional, Tuple

from app.core import areas as pune_areas

_TAG = re.compile(r"(?<![\w&])#\w+")
_TAG_LINE = re.compile(r"^\s*(?:#\w+\s*)+$")
_RERA_NO = re.compile(r"\bP5\d{10}\b")
_WORD = r"[A-Z0-9][\w'&-]*"
# "Gulmohar City, Ranjangaon." (campaign intro) or "Goyal My Home, Upper Kharadi: ₹97 L" (agent project caption)
_PROJECT_LINE = re.compile(rf"^\s*({_WORD}(?:\s+{_WORD}){{0,5}}),\s+([A-Z][A-Za-z-]*(?:\s+[A-Z][A-Za-z-]*){{0,3}})(?:,\s*Pune)?\s*[.:](?:\s|$)")
_LINK_LINE = re.compile(r"Full details of ([^\n]+?), with its MahaRERA record", re.I)  # campaign.link_line_for

AGENT_TAGS = ["#PuneRealEstate", "#RealEstateAgentPune", "#PuneBrokers", "#ChannelPartner", "#PuneProperty"]
BUYER_TAGS = ["#PuneProperty", "#MahaRERA"]           # after the specific ones
FILLER_TAGS = ["#PuneRealEstate"]                      # only when nothing better is left
HOMES_TAG = "#PuneHomes"                               # a filler for anything but plots
AGENT_SOURCES = ("promo_agents", "promo_agents_v2", "agent_reels")
PROJECT_SOURCES = ("campaign", "agentprojects")
PER_CHANNEL = {"instagram": 5, "facebook_page": 3}
# The Pune-Nagar road corridor: a post from one town also reaches the next hub buyers search for (a Shirur plot is sold on
# Ranjangaon MIDC jobs). Locality (lower case, no spaces) -> the corridor tag that goes right after its own.
CORRIDOR = {"shirur": "#Ranjangaon", "malthan": "#Ranjangaon", "ranjangaon": "#Shirur", "karegaon": "#Ranjangaon",
            "shikrapur": "#Ranjangaon", "sanaswadi": "#Shikrapur", "koregaonbhima": "#Shikrapur", "lonikand": "#Wagholi",
            "wagholi": "#Kharadi"}
TYPE_TAGS = {"plot": "#PlotsInPune", "apartment": "#FlatsInPune", "flat": "#FlatsInPune", "villa": "#VillasInPune",
             "house": "#IndependentHousePune", "commercial": "#CommercialPropertyPune", "office": "#CommercialPropertyPune",
             "shop": "#CommercialPropertyPune"}
_TYPE_WORDS = (("plot", re.compile(r"\b(?:na )?plots?\b", re.I)), ("apartment", re.compile(r"\b(?:\d\s?bhk|flats?|apartments?)\b", re.I)))
# tags that say nothing about this post in particular: never ahead of the specific ones
_GENERIC = {t.lower() for t in BUYER_TAGS + FILLER_TAGS + AGENT_TAGS + [HOMES_TAG] + list(TYPE_TAGS.values())
            + ["#Pune", "#Avasetu", "#PuneNews", "#NewProjects", "#RealEstate", "#India", "#NAPlots"]}
_BROAD = {"#pune", "#avasetu", "#realestate", "#india"}  # kept only when there is room left over


def audience(doc: dict) -> str:
    """'agents' for our recruitment posts, 'buyers' for everything else (projects, homes, news, guides)."""
    src = str((doc.get("creative") or {}).get("source") or "")
    return "agents" if src in AGENT_SOURCES or str(doc.get("slug", "")).startswith("promo") else "buyers"


def area(doc: dict) -> Optional[pune_areas.Area]:
    """The row's area: its explicit `area` key (set by the daily-reel rows) when known, else the most specific area the
    caption names; None when it names none of ours."""
    explicit = pune_areas.get(str(doc.get("area") or ""))
    if explicit:
        return explicit
    named = pune_areas.named_in(doc.get("caption") or "")
    return named[0] if named else None


def _creative(doc: dict) -> dict:
    return doc.get("creative") or {}


def _project_dict(doc: dict) -> dict:
    p = _creative(doc).get("project")
    return p if isinstance(p, dict) else {}


def _project_like(doc: dict) -> bool:
    c = _creative(doc)
    return (str(c.get("source") or "") in PROJECT_SOURCES or str(doc.get("slug", "")).startswith("campaign-")
            or c.get("role") in ("listing", "project") or bool(_project_dict(doc)))


def project_and_locality(doc: dict) -> Tuple[str, str]:
    """(project name, locality) the row is about, each "" when unknown. Fields first (`project`/`locality` on the row or its
    creative, the agent project dict of a daily project reel), then the caption: the campaign's link line, then a
    "Project, Locality." line (any line of a project row; only the first line of other rows, and only when it names an area)."""
    c, p = _creative(doc), _project_dict(doc)
    proj = str(doc.get("project_name") or c.get("project_name") or p.get("name") or "").strip()
    if isinstance(c.get("project"), str):
        proj = proj or c["project"].strip()
    loc = str(doc.get("locality") or c.get("locality") or p.get("locality") or c.get("area") or "").strip()
    if proj and loc:
        return proj, loc
    caption = doc.get("caption") or ""
    m = _LINK_LINE.search(caption)
    if m and "," in m.group(1):
        a, b = (s.strip() for s in m.group(1).split(",", 1))
        return proj or a, loc or re.sub(r",\s*Pune$", "", b, flags=re.I)
    lines = [ln for ln in caption.splitlines() if ln.strip()]
    project_row = _project_like(doc)
    for ln in (lines if project_row else lines[:1]):
        m = _PROJECT_LINE.match(ln)
        if m and (project_row or pune_areas.get(m.group(2)) or pune_areas.named_in(m.group(2))):
            return proj or m.group(1).strip(), loc or m.group(2).strip()
    return proj, loc


def locality(doc: dict) -> Tuple[str, Optional[pune_areas.Area]]:
    """(locality name, its area or None). The explicit area key wins, then the locality the row is about (even one outside
    our areas, e.g. Ranjangaon), then the most specific area the caption names; ("", None) when none."""
    explicit = pune_areas.get(str(doc.get("area") or ""))
    if explicit:
        return explicit.name, explicit
    _, loc = project_and_locality(doc)
    if loc:
        a = pune_areas.get(loc) or next(iter(pune_areas.named_in(loc)), None)
        return (a.name, a) if a else (loc, None)
    a = area(doc)
    return (a.name, a) if a else ("", None)


def camel_tag(name: str) -> str:
    """'Gulmohar City' -> '#GulmoharCity', 'shirur pune' -> '#ShirurPune'; '' when nothing is left."""
    words = re.findall(r"[A-Za-z0-9]+", name or "")
    tag = "".join(w if w[:1].isupper() or w.isupper() else w.capitalize() for w in words)
    return f"#{tag}" if tag and len(tag) <= 30 and not tag.isdigit() else ""


def property_type(doc: dict) -> str:
    """'plot', 'apartment', 'villa', ... when the row says; '' when it does not (or the caption names both plots and flats)."""
    c, p = _creative(doc), _project_dict(doc)
    t = str(doc.get("property_type") or c.get("property_type") or p.get("property_type") or "").lower()
    if t in TYPE_TAGS:
        return t
    if p.get("bhk_options"):
        return "apartment"
    caption = doc.get("caption") or ""
    own = {x.lower() for x in _TAG.findall(caption)}
    for k in ("plot", "apartment", "villa", "house", "commercial"):
        if TYPE_TAGS[k].lower() in own:
            return k
    if "#naplots" in own:
        return "plot"
    found = [k for k, rx in _TYPE_WORDS if rx.search(_TAG.sub(" ", caption))]
    return found[0] if len(found) == 1 else ""


def _body(caption: str) -> str:
    """The caption without its tags-only lines, inline tags kept as words."""
    lines = [ln for ln in (caption or "").splitlines() if not _TAG_LINE.match(ln)]
    return "\n".join(_TAG.sub(lambda m: m.group(0)[1:], ln).rstrip() for ln in lines).rstrip()


def _squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


# ---- who a buyer post is for: one function feeds both the hashtags and the tags, so what we target and what we measure agree ----
SEGMENTS = ("renter", "plot", "first_home", "family_home", "premium", "unknown")
SEGMENT_TAGS = {"renter": "#FlatsForRentPune", "plot": "#NAPlotsPune", "first_home": "#AffordableHomesPune"}
# (upper bound in rupees, label); a starting price counts as its band
PRICE_BANDS = ((30_00_000, "under_30L"), (50_00_000, "30-50L"), (75_00_000, "50-75L"), (1_00_00_000, "75L-1Cr"),
               (1_50_00_000, "1-1.5Cr"), (None, "1.5Cr+"))


def _num(v) -> Optional[float]:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def listing_facts(doc: dict) -> dict:
    """{transaction, price_inr, bhk} the row carries (campaign rows from the listing, agent project reels from the project),
    each None when the row does not say."""
    c, p = _creative(doc), _project_dict(doc)
    price = _num(doc.get("price_inr") or c.get("price_inr") or p.get("price_min") or p.get("price_inr"))
    bhk = _num(doc.get("bhk") or c.get("bhk"))
    opts = p.get("bhk_options")
    if bhk is None and isinstance(opts, list) and len(opts) == 1:
        bhk = _num(opts[0])
    tx = str(doc.get("transaction") or c.get("transaction") or "").lower()
    return {"transaction": tx if tx in ("sale", "rent") else None, "price_inr": price, "bhk": bhk}


def price_band(doc: dict) -> str:
    f = listing_facts(doc)
    if f["transaction"] == "rent" or f["price_inr"] is None:
        return "unknown"
    return next(label for top, label in PRICE_BANDS if top is None or f["price_inr"] < top)


def segment(doc: dict) -> str:
    """The buyer a post is for: renter | plot | first_home | family_home | premium, or unknown when the row does not say enough.
    Rules, first match: a rental; a plot; under ₹50 lakh or a 1 BHK (first home); ₹1.5 crore and up or 4+ BHK (premium);
    a known price or a 2-3 BHK (family home). Recruitment posts and news have no segment."""
    if audience(doc) == "agents":
        return "unknown"
    f, kind = listing_facts(doc), property_type(doc)
    if f["transaction"] == "rent":
        return "renter"
    if kind == "plot":
        return "plot"
    price, bhk = f["price_inr"], f["bhk"]
    if (price and price < 50_00_000) or (bhk and bhk < 2):
        return "first_home"
    if (price and price >= 1_50_00_000) or (bhk and bhk >= 4):
        return "premium"
    if price or bhk:
        return "family_home"
    return "unknown"


def segment_tag(doc: dict, loc: str) -> str:
    """The audience's own hashtag: '#2BHKWagholi' when a flat's BHK is known (what buyers type), else the segment's tag."""
    seg = segment(doc)
    bhk = listing_facts(doc)["bhk"]
    if seg in ("renter", "plot") or not bhk or not float(bhk).is_integer() or property_type(doc) not in ("", "apartment", "flat"):
        return SEGMENT_TAGS.get(seg, "")
    return camel_tag(f"{int(bhk)}BHK {loc or 'Pune'}")


def hashtags(doc: dict) -> List[str]:
    n = PER_CHANNEL.get(doc.get("channel", ""), 3)
    if audience(doc) == "agents":
        return AGENT_TAGS[:n]
    caption = doc.get("caption") or ""
    proj, _ = project_and_locality(doc)
    loc, a = locality(doc)
    kind = property_type(doc)
    loc_tags = list(a.hashtags) if a else [camel_tag(loc)]
    body = _squash(_body(caption))
    own = list(dict.fromkeys(_TAG.findall(caption)))
    other_areas = {x.key for x in pune_areas.AREAS} - {a.key if a else ""}

    def named(t: str) -> set:
        return {x.key for x in pune_areas.named_in(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", t[1:]))}

    def names_other_area(t: str) -> bool:  # a default "#Wagholi" on a post about something else
        return bool(named(t) & other_areas)

    own_specific = [t for t in own if t.lower() not in _GENERIC and _squash(t) in body and not names_other_area(t)]
    own_local = [t for t in own_specific if a and a.key in named(t)]  # "#Wagholi" next to "#WagholiPune": one is enough up front
    own_specific = [t for t in own_specific if t not in own_local]
    own_topical = [t for t in own if t.lower() not in _GENERIC and t not in own_specific and not names_other_area(t)]
    own_generic = [t for t in own if t.lower() in _GENERIC and t.lower() not in _BROAD]
    rera = bool(_RERA_NO.search(caption)) or "#maharera" in {t.lower() for t in own}
    proj_tag = camel_tag(proj) if proj and _squash(proj) != _squash(loc) else ""
    # Facebook's 3 tags: locality and project say more than the type when the row names a project
    type_tag = "" if proj_tag and doc.get("channel") == "facebook_page" else TYPE_TAGS.get(kind, "")
    local_tag = camel_tag(f"{loc} Real Estate") if loc else ""  # #WagholiRealEstate: narrower than #PuneProperty
    corridor = CORRIDOR.get(_squash(loc), "") if loc else ""
    if corridor and corridor.lower() in {t.lower() for t in loc_tags}:
        corridor = ""
    seg_tag = segment_tag(doc, loc)
    # 3 tags on Facebook: place, project, audience; and a plot's or rental's audience tag already says the type
    if seg_tag and (doc.get("channel") == "facebook_page" or segment(doc) in ("plot", "renter")):
        type_tag = ""
    # with a corridor tag the narrow #<Locality>RealEstate waits until after #PuneProperty
    tags = (loc_tags[:1] + [corridor, proj_tag, seg_tag, type_tag] + ([] if corridor else [local_tag])
            + own_specific + ["#PuneProperty"] + ([local_tag] if corridor else []) + ["#MahaRERA"] * rera + loc_tags[1:] + own_local + own_topical + own_generic
            + ([] if kind == "plot" else [HOMES_TAG]) + FILLER_TAGS + [t for t in own if t.lower() in _BROAD])
    out, seen = [], set()
    for t in tags:
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out[:n]


def with_hashtags(caption: str, tags: List[str]) -> str:
    """The caption without its own hashtags (lines of only tags dropped, inline tags removed), plus one line of `tags`."""
    body = re.sub(r"\n{3,}", "\n\n", _body(caption))  # "#Wagholi" -> "Wagholi"
    return f"{body}\n\n{' '.join(tags)}" if tags else body


def location_env(name: str) -> str:
    """IG_LOCATION_<NAME> for a locality outside our areas: 'Ranjangaon' -> IG_LOCATION_RANJANGAON."""
    return "IG_LOCATION_" + "_".join(re.findall(r"[A-Za-z0-9]+", name)).upper()


def location_id(doc: dict) -> Optional[str]:
    """The Facebook place id for the row's locality (area or not), else Pune; None when not configured (the post goes out
    without one)."""
    if doc.get("channel") not in ("instagram", "facebook_page"):
        return None
    loc, a = locality(doc)
    envs = [a.location_env] if a else ([location_env(loc)] if loc else [])
    for env in envs + ["IG_LOCATION_PUNE"]:
        v = (os.environ.get(env) or "").strip()
        if v.isdigit():
            return v
    return None


def apply(doc: dict) -> dict:
    return {**doc, "caption": with_hashtags(doc.get("caption", ""), hashtags(doc))}
