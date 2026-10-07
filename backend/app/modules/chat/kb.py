"""Vetted answers. Only stable, checkable statements: no prices per sq ft, no predictions, no invented distances, and transport is 'approved is not running'."""
from app.core import brand
import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Entry:
    id: str
    keywords: Tuple[str, ...]   # lower-case words/phrases; the more that match, the better
    answer: str


MAHARERA = "the MahaRERA website (maharera.maharashtra.gov.in)"

ENTRIES: List[Entry] = [
    Entry("rera", ("rera", "maharera", "is it registered", "approved project"),
          f"Every project above the RERA limits must be registered. You can look up a project's RERA number, its promised possession date and its complaints on {MAHARERA}. If an ad shows no RERA number, ask for it before you pay anything."),
    Entry("carpet", ("carpet", "built-up", "built up", "super built", "sq ft", "sqft", "square feet"),
          "Carpet area is the floor space you actually use, wall to wall. Built-up adds the walls and balcony, and super built-up adds your share of common areas. To compare flats fairly, compare the price per sq ft of carpet area."),
    Entry("ready_vs_uc", ("ready to move", "ready possession", "under construction", "possession", "rtm", "new launch"),
          "Ready-to-move means you see exactly what you buy. Under construction can cost less to enter, but you wait and rely on the builder keeping the date, so check the possession date on the RERA page and visit a finished project by the same builder."),
    Entry("metro", ("metro", "station", "train", "line 4", "corridor"),
          "Two metro projects on the east side have been approved by the Union Cabinet: Corridor 2B (Ramwadi to Wagholi/Vitthalwadi) and Line 4 (Kharadi to Khadakwasla). Approved is not the same as running, so please do not pay extra for a station that does not exist yet, and check the latest status on the Maha-Metro website."),
    Entry("kharadi", ("kharadi",),
          "Kharadi is one of east Pune's main office areas, with large campuses such as EON IT Park and World Trade Center Pune. It is established and usually the busiest and priciest of the three areas we cover (Kharadi, Upper Kharadi, Wagholi). Full guide: /localities/kharadi"),
    Entry("upper_kharadi", ("upper kharadi",),
          "Upper Kharadi is on the same eastern corridor, with newer projects and more open space than Kharadi. Check the builder, the RERA possession date and the road access at rush hour. Full guide: /localities/upper-kharadi"),
    Entry("wagholi", ("wagholi",),
          "Wagholi is further out on the eastern corridor. Buyers often find more space for the budget there, in exchange for a longer commute. Try the trip yourself at 9 am and 6:30 pm on a weekday. Full guide: /localities/wagholi"),
    Entry("commute", ("commute", "distance", "how far", "travel time", "office", "traffic"),
          "We do not quote travel times because they change a lot by route and hour. The reliable test is to make the trip yourself at 9:00 am and 6:30 pm on a weekday before you decide."),
    Entry("costs", ("stamp duty", "registration charges", "gst", "hidden charges", "maintenance", "total cost", "cost sheet"),
          "Ask for the full cost sheet, not just the headline price: stamp duty, registration, GST where applicable, parking, and the maintenance deposit. Rates change, so we do not quote them here. Our team can help you compare cost sheets."),
    Entry("loan", ("loan", "emi", "bank", "finance", "mortgage", "down payment"),
          "Most buyers use a home loan. A bank will tell you your eligibility, and it helps to have income proofs and ID ready. We can note whether you need a loan so the agent can guide you."),
    Entry("documents", ("document", "title", "agreement", "sale deed", "ownership", "paperwork", "lawyer"),
          "Before you book, have a lawyer check the title and approvals, and compare the agreement's carpet area and possession date with the RERA page. Never pay a large booking amount before you have seen the documents."),
    Entry("site_visit", ("site visit", "visit the flat", "see the flat", "see the property", "appointment"),
          "Our team can arrange a site visit at a time that suits you. Share your area, budget and a mobile number and someone will get back to you to fix a time."),
    Entry("fees", ("brokerage", "commission", "is it free", "any fee", "service charge"),
          "Browsing and asking questions here is free. Any brokerage is agreed between you and the agent, so please ask about it and get it in writing before you agree."),
    Entry("sample", ("sample", "not available", "is it available", "still available", "availability"),
          "Listings marked SAMPLE are illustrations of how a listing looks. For real availability, tell us what you are looking for and our team will confirm current options."),
    Entry("negotiation", ("negotiable", "negotiate", "discount", "reduce price", "best price", "final price"),
          "Whether a price can move depends on the seller. Our team can find out for the homes you like. Tell us your area, BHK and budget to start."),
    Entry("agent", ("i am an agent", "list my property", "join the pilot", "free trial", "become an agent", "sell my"),
          "If you are an agent in Pune, claim your free trial: your first 3 properties are marketed free, no card. Start at /trial."),
    Entry("who", ("who are you", "what is avasetu", "what is pune property", "what do you do"),
          brand.NAME + " helps people understand and find homes in Pune: clear guides, honest listings and a team that answers your questions. Tell me what you are looking for and I will help."),
]


def _words(text: str) -> str:
    return " " + re.sub(r"[^a-z0-9ऀ-ॿ ]+", " ", text.lower()) + " "


def search(question: str, limit: int = 3) -> List[Tuple[int, Entry]]:
    """Entries ranked by how many of their keywords appear in the question (multi-word keywords count double)."""
    q = _words(question)
    scored = []
    for e in ENTRIES:
        score = sum(2 if " " in k.strip() else 1 for k in e.keywords if _words(k).strip() and (" " + _words(k).strip() + " ") in q)
        if score:
            scored.append((score, e))
    return sorted(scored, key=lambda t: -t[0])[:limit]


def best(question: str, min_score: int = 1):
    hits = search(question, 1)
    return hits[0][1] if hits and hits[0][0] >= min_score else None
