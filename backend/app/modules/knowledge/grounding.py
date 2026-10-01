"""Grounding: the ONLY things a reply may say. `facts_for(ref, db)` turns a listing, a showcase sample home, a calendar item or an area into a
Grounding of plain sentences. Nothing is invented: every sentence comes from a stored field, the agent's `about` block, the sample dataset,
the item's own caption / library text, or the curated area facts. Agent-written text with a phone number, a link or hype is dropped.

Layout of a Grounding (all sentences are English; the reply layer handles language):
  facts       statements about THIS home / post (or, for an area grounding, about the area)
  area_facts  statements about the area the home is in (only used for area-type questions such as commute and metro)
  general     process statements that are true for any home (site visits, loans, how to check RERA)
  advice      'what to check' lines (never presented as facts)
  faq         agent-written or curated {q, a} pairs
Collections read: listings, content_calendar (the calendar's table, named here to stay loosely coupled).
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from app.modules.marketing.facts import money, sqft
from app.modules.marketing.polish import HYPE, PHONE

from .areas import AreaFacts, area_facts

CALENDAR_COLLECTION = "content_calendar"
URL = re.compile(r"https?://|www\.|\b\w+\.(?:com|in|org|gov\.in|net)\b", re.I)
INTEREST = "{interest_url}"

VISIT = "You can request a site visit and the agent will confirm a day and time."
LOAN = "Most buyers use a home loan; a bank will tell you your eligibility, so keep income proofs and ID ready."
RERA_GENERAL = "Every project above the RERA limits must be registered, and its RERA number, promised possession date and complaints can be looked up on the MahaRERA website."
GENERAL = [VISIT, LOAN, RERA_GENERAL]


@dataclass
class Ref:
    kind: str   # 'listing' | 'sample' | 'calendar' | 'area' | 'text'
    id: str     # listing id | sample slug | calendar item id | area key or name | the post text

    @staticmethod
    def listing(id: str) -> "Ref":
        return Ref("listing", id)

    @staticmethod
    def sample(slug: str) -> "Ref":
        return Ref("sample", slug)

    @staticmethod
    def calendar(id: str) -> "Ref":
        return Ref("calendar", id)

    @staticmethod
    def area(name: str) -> "Ref":
        return Ref("area", name)

    @staticmethod
    def text(message: str) -> "Ref":
        return Ref("text", message)


@dataclass
class Grounding:
    subject: str
    facts: List[str] = field(default_factory=list)
    faq: List[Dict[str, str]] = field(default_factory=list)       # agent-written (listing) or curated (area) question/answer pairs
    area_faq: List[Dict[str, str]] = field(default_factory=list)  # the area's curated pairs, for a listing or sample in that area
    links: Dict[str, str] = field(default_factory=lambda: {"interest": INTEREST, "page": ""})  # the caller fills the real URLs
    kind: str = "listing"          # listing | sample | post | area
    sample: bool = False
    area_facts: List[str] = field(default_factory=list)
    general: List[str] = field(default_factory=lambda: list(GENERAL))
    advice: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)   # audit only: where the statements come from
    locality: Optional[str] = None

    @property
    def noun(self) -> str:
        return {"area": "area", "post": "post"}.get(self.kind, "home")

    def corpus(self) -> str:
        """Everything a reply may quote (used to validate numbers and names)."""
        return " ".join(self.facts + self.area_facts + self.general + self.advice + [f"{x['q']} {x['a']}" for x in self.faq + self.area_faq] + [self.subject])


def _clean(s: Any) -> Optional[str]:
    """One tidy sentence, or None when it is empty or unsafe to repeat in public (phone, link, hype)."""
    t = " ".join(str(s or "").split()).strip()
    if not t or PHONE.search(t) or URL.search(t) or HYPE.search(t):
        return None
    return t if t[-1] in ".!?" else t + "."


def _add(out: List[str], *sentences: Any) -> None:
    for s in sentences:
        c = _clean(s)
        if c and c not in out:
            out.append(c)


def _join(items: List[str]) -> str:
    return ", ".join(i for i in (str(x).strip() for x in items) if i)


def _faq(items: Any, limit: int = 8) -> List[Dict[str, str]]:
    out = []
    for it in (items or [])[:limit]:
        q, a = _clean((it or {}).get("q")), _clean((it or {}).get("a"))
        if q and a:
            out.append({"q": q, "a": a})
    return out


def _area_part(g: Grounding, af: Optional[AreaFacts]) -> None:
    if not af:
        return
    g.locality = af.name
    for f in af.facts:
        (g.advice if f.startswith("Check:") else g.area_facts).append(f)
    pairs = [{"q": q, "a": a} for q, a in af.faq]
    if g.kind == "area":
        g.faq += pairs
    else:
        g.area_faq += pairs
    g.sources += list(af.sources)


# ---- listing --------------------------------------------------------------------------------------------------------
POSSESSION = {"ready": "It is ready to move.", "under_construction": "It is under construction."}
NEAR_LABEL = {"school": "school", "hospital": "hospital", "transit": "transit stop", "office": "office park", "market": "market", "park": "park", "other": "place"}


def listing_grounding(doc: dict) -> Grounding:
    about = doc.get("about") if isinstance(doc.get("about"), dict) else {}
    rent = (doc.get("transaction") or "sale") == "rent"
    loc = ", ".join(p for p in (doc.get("locality"), doc.get("city")) if p)
    bhk = doc.get("bhk")
    bhk_t = (f"{int(bhk)} BHK" if float(bhk).is_integer() else f"{bhk:g} BHK") if bhk else ""
    subject = (doc.get("title") or " ".join(x for x in (bhk_t, doc.get("property_type") or "home", ("in " + loc) if loc else "") if x)).strip()
    g = Grounding(subject=subject, kind="listing", sample=(doc.get("title") or "").strip().lower().startswith("sample"))
    f = g.facts
    _add(f, f"It is a {bhk_t} {doc.get('property_type') or 'home'} {'for rent' if rent else 'for sale'}{' in ' + loc if loc else ''}." if bhk_t or loc else None)
    if loc:
        _add(f, f"It is located in {loc}.")
    if doc.get("price_inr"):
        _add(f, f"The {'rent' if rent else 'price'} is {money(int(doc['price_inr']), rent)}.")
    if doc.get("carpet_sqft"):
        _add(f, f"The carpet area is {sqft(int(doc['carpet_sqft']))}.")
    if doc.get("super_built_up_sqft"):
        _add(f, f"The super built-up area is {sqft(int(doc['super_built_up_sqft']))}.")
    if doc.get("floor") is not None:
        _add(f, f"It is on floor {doc['floor']}{' of ' + str(doc['total_floors']) if doc.get('total_floors') else ''}.")
    if doc.get("furnishing"):
        _add(f, "It is " + {"semi": "semi-furnished", "unfurnished": "unfurnished", "furnished": "furnished"}.get(doc["furnishing"], str(doc["furnishing"])) + ".")
    p = doc.get("possession")
    if p:
        _add(f, POSSESSION.get(p, f"Possession is listed as {p}."))
    if doc.get("rera_no"):
        _add(f, f"The RERA number is {doc['rera_no']}.")
    if doc.get("project_name") or about.get("project_name"):
        _add(f, f"The project is {about.get('project_name') or doc.get('project_name')}.")
    amen = list(dict.fromkeys([str(a).strip() for a in (doc.get("amenities") or []) + (about.get("amenities") or []) if str(a).strip()]))
    if amen:
        _add(f, f"Amenities: {_join(amen)}.")
    status = doc.get("status")
    if status == "live":
        _add(f, "It is currently listed as available on our site.")
    elif status == "under_offer":
        _add(f, "It is currently under offer, so it may no longer be available.")
    # agent-supplied project and area knowledge (the `about` block); every key is optional
    if about.get("builder_known_as"):
        _add(f, f"The builder is known as {about['builder_known_as']}.")
    if about.get("highlights"):
        _add(f, f"Highlights: {_join(list(about['highlights'])[:6])}.")
    for n in (about.get("nearby") or [])[:12]:
        if isinstance(n, dict) and n.get("name"):
            mins = n.get("minutes")
            _add(f, f"Nearby {NEAR_LABEL.get(n.get('type'), 'place')}: {n['name']}{f', about {int(mins)} minutes away' if isinstance(mins, (int, float)) and mins > 0 else ''}.")
    for line in (about.get("connectivity") or [])[:6]:
        _add(f, f"Connectivity: {line}")
    for key, label in (("water", "Water supply"), ("power_backup", "Power backup"), ("maintenance", "Maintenance"), ("society", "Society"),
                       ("parking", "Parking"), ("possession_note", "Possession"), ("rera_note", "RERA")):
        if about.get(key):
            _add(f, f"{label}: {about[key]}")
    g.faq = _faq(about.get("faq"))
    g.sources.append("the agent's listing")
    _area_part(g, area_facts(doc.get("locality")))
    return g


# ---- sample home ----------------------------------------------------------------------------------------------------
def sample_grounding(slug: str) -> Grounding:
    from app.modules.showcase import samples as S  # data module; imported lazily so that a missing asset set cannot break area/listing replies
    h = S.get(slug)
    g = Grounding(subject=f"Sample home: {h.title}", kind="sample", sample=True, general=[LOAN, "A sample home has no RERA number; real listings show theirs, and every project can be looked up on the MahaRERA website."])
    f = g.facts
    _add(f, "This is a sample home shown for illustration, not available for sale.",
         "Because it is a sample, it cannot be visited or booked; tell us your budget and preferred area and we will look for a real match.",
         f"It is a {h.bhk} BHK in {h.locality}.", f"This sample home is located in {h.locality}, Pune.",f"The carpet area is {h.carpet_text}.", f"It is on floor {h.floor} of {h.total_floors}.",
         f"The sample price figure is {h.price_text}, a labelled sample figure and not a real offer.",
         f"It is {h.furnishing.lower()}.")
    _add(f, ("In this sample the home is ready to move." if h.ready else f"In this sample the home is {h.possession[0].lower() + h.possession[1:]}."))
    if h.facing:
        _add(f, f"It faces {h.facing.lower()}.")
    labels = [S.ICON_LABELS[a] for a in h.amenities if a in S.ICON_LABELS]
    if labels:
        _add(f, f"The sample society shows these amenities: {_join(labels)}.")
    _add(f, f"Highlights: {_join(list(h.highlights))}.")
    g.sources.append("showcase sample dataset (illustrative figures)")
    _area_part(g, area_facts(h.locality))
    return g


# ---- calendar item / evergreen post ---------------------------------------------------------------------------------
HASHTAG = re.compile(r"#\w+")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️]")


def sentences(body: str) -> List[str]:
    text = EMOJI.sub("", HASHTAG.sub("", body or ""))
    text = re.sub(r"https?://\S+", "", text)
    out: List[str] = []
    for chunk in re.split(r"\n+", text):
        for s in re.split(r"(?<=[.!?])\s+", chunk.strip()):
            s = s.strip()
            if len(s) > 12 and not s.endswith("?") and "link in our bio" not in s.lower() and "link in bio" not in s.lower():
                out.append(s)
    return out


def post_grounding(subject: str, body: str, review: str = "") -> Grounding:
    g = Grounding(subject=subject or "this post", kind="post")
    for s in sentences(body):
        _add(g.facts, s)
    if review:
        g.sources.append(review)
    return g


def calendar_grounding(doc: dict) -> Optional[Grounding]:
    if doc.get("kind") == "showcase":
        try:
            return sample_grounding(doc["slug"])
        except KeyError:
            return None
    body, subject, review = doc.get("caption") or "", doc.get("slug") or "", ""
    try:
        from app.modules.calendar.library import BY_SLUG  # data module: verified body and review note of the evergreen post
        e = BY_SLUG.get(doc.get("slug") or "")
    except Exception:
        e = None
    if e:
        body, subject, review = e.body, e.title, e.review
    g = post_grounding(subject, body, review)
    g.facts = g.facts or []
    return g if g.facts else None


# ---- entry point ----------------------------------------------------------------------------------------------------
def _ref(ref: Union[Ref, dict, tuple]) -> Ref:
    if isinstance(ref, Ref):
        return ref
    if isinstance(ref, tuple):
        return Ref(*ref)
    for k in ("listing", "sample", "calendar", "area", "text"):
        if ref.get(k) or ref.get(k + "_id"):
            return Ref(k, ref.get(k) or ref.get(k + "_id"))
    raise ValueError(f"unknown grounding reference {ref!r}")


async def facts_for(ref: Union[Ref, dict, tuple], db=None) -> Optional[Grounding]:
    """The Grounding for a listing id, a showcase sample slug, a calendar item id, an area, or a post's own text. None when it cannot be found."""
    r = _ref(ref)
    if r.kind == "area":
        af = area_facts(r.id)
        if not af:
            return None
        g = Grounding(subject=f"{af.name}, Pune", kind="area", locality=af.name)
        _area_part(g, af)
        g.facts, g.area_facts = [x for x in g.area_facts], []
        return g
    if r.kind == "sample":
        try:
            return sample_grounding(r.id)
        except KeyError:
            return None
    if r.kind == "text":
        g = post_grounding("this post", r.id)
        return g if g.facts else None
    if db is None:
        return None
    if r.kind == "listing":
        doc = await db.get_collection("listings").find_one({"_id": r.id})
        return listing_grounding(doc) if doc else None
    if r.kind == "calendar":
        doc = await db.get_collection(CALENDAR_COLLECTION).find_one({"_id": r.id})
        return calendar_grounding(doc) if doc else None
    return None
