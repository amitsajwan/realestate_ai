"""Reach: each post's best few hashtags (5 on Instagram, 3 on Facebook) and an Instagram location tag.

Applied to every calendar row just before it is published. The caption's own hashtags are taken off and one line of tags
goes at the end, most specific first:
  1. the locality: one of our areas (app.core.areas, with its own tags) or any other locality the row names
     ("Gulmohar City, Ranjangaon." -> #Ranjangaon), so a plot in Ranjangaon is not tagged as only "Pune";
  2. the project, when the row is about a named one (#GulmoharCity);
  3. the property type when it is known (#PlotsInPune, #FlatsInPune, ...);
  4. the caption's own specific tags (the generator put them there on purpose: #StampDuty on a stamp-duty guide; a tag
     counts as specific when its words are in the caption), then #PuneProperty and #MahaRERA (when the row has a MahaRERA
     number or tag), then the area's second tag, the caption's other tags and fillers.
Duplicates are dropped whatever their case. Agent-recruitment posts get the agent tags. Areas live in app.core.areas only:
other localities are worked out here and never added there (that list drives area pages and the daily area reels).

Location tags need Facebook place ids from the environment: one per area (`Area.location_env`, e.g. IG_LOCATION_WAGHOLI),
one per other locality (IG_LOCATION_<NAME>, e.g. IG_LOCATION_RANJANGAON), else IG_LOCATION_PUNE; left out when unset.
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
    tags = (loc_tags[:1] + [camel_tag(proj) if proj and _squash(proj) != _squash(loc) else ""] + [TYPE_TAGS.get(kind, "")]
            + own_specific + ["#PuneProperty"] + ["#MahaRERA"] * rera + loc_tags[1:] + own_local + own_topical + own_generic
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
    if doc.get("channel") != "instagram":
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
