"""What Avasetu says about itself and about buying in Pune: one vetted set of answers for the website chat and for replies to post comments.

The agent answers follow the landing page and /trial copy (frontend/lib/marketing/strings.ts); change both together. Only stable, checkable
statements: no price after the free trial, no prices per sq ft, no predictions, no invented distances, and transport is 'approved is not
running'. `answer()` uses a keyword hit when there is one, else lets the LLM answer from these entries only (checked: no new numbers, no links).
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.core import brand


@dataclass(frozen=True)
class Entry:
    id: str
    keywords: Tuple[str, ...]   # lower-case words/phrases; the more that match, the better
    answer: str
    audience: str = "buyer"     # buyer | agent | any ('agent' and 'any' are about Avasetu itself)
    cta: str = ""               # the next step with its site path; the chat adds it, a comment reply uses its own link instead


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
          "Kharadi is one of east Pune's main office areas, with large campuses such as EON IT Park and World Trade Center Pune. It is established and usually busier and pricier than Upper Kharadi and Wagholi. Full guide: /localities/kharadi"),
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
    Entry("who", ("who are you", "what is avasetu", "what is this", "what is this site", "what is this website", "what you do", "what do you do",
                  "what does avasetu do", "about you", "about avasetu", "how does it work", "how it works", "what is pune property",
                  "aap kya karte", "kya karte ho", "kya karte hai", "avasetu kya hai", "ye kya hai", "तुम्ही काय करता", "आप क्या करते"),
          f"{brand.NAME} (आवास + सेतु: home + bridge) helps real estate agents in Pune market their properties: your own website, posts and reels "
          "for Facebook and Instagram, and every buyer enquiry as a lead card. Buyers can ask us about homes and areas in Pune, and we pass "
          "their requirement to the agent.", "any", "Agents: claim your free trial at /trial. Looking for a home? Tell me the area, BHK and budget."),
    Entry("agent", ("i am an agent", "i'm an agent", "im an agent", "i am a broker", "i am broker", "real estate agent", "list my property",
                    "join the pilot", "free trial", "become an agent", "sell my", "agent hoon", "broker hoon", "main agent hoon", "मैं एजेंट हूँ", "मी एजंट आहे",
                    "mi agent aahe"),
          "If you are a real estate agent in Pune: we make your website, posts and reels, and every buyer enquiry becomes a lead card with "
          "budget, area, timing and how warm the buyer is. Your first 3 properties are marketed free, no card.", "agent", "Start at /trial."),
    Entry("agent_cost", ("price for agents", "cost for agents", "how much for agents", "pricing", "plans", "monthly fee", "subscription",
                         "charges for agents", "really free", "after trial", "after the trial", "kitna lagega", "kitne paise"),
          "Your first 3 properties are free, no card. After that there is a small monthly fee, and you see the price first, then decide.",
          "agent", "Start at /trial."),
    Entry("agent_start", ("how do i start", "how to start", "how to join", "sign up", "signup", "sign-up code", "trial code"),
          "Tap Claim your free trial and leave your number. Your sign-up code comes on WhatsApp, usually the same day; sign in and add your "
          "first property. You can add a project by its MahaRERA number and we fill in the rest.", "agent", "Start at /trial."),
    Entry("agent_posts", ("post on my", "my facebook", "my instagram", "reels", "posts for me", "social media", "marketing"),
          "We make posts and reels for each property. They go on your own Facebook and Instagram after you approve each post.", "agent",
          "Start at /trial."),
    Entry("agent_leads", ("who sees my leads", "my leads", "lead card", "buyer details"),
          "Only you see your buyer leads. Buyers agree to be contacted, and we never sell or share their details. Call or WhatsApp a buyer "
          "straight from the lead card.", "agent"),
    Entry("agent_app", ("an app", "the app", "install", "download", "play store"),
          "No app to install. It works in your phone's browser, with your own WhatsApp.", "agent"),
    Entry("languages", ("language", "languages", "in hindi", "in marathi"),
          "Posts and replies work in English, Hindi and Marathi.", "any"),
    Entry("areas", ("which areas", "which cities", "which city", "where do you work", "only pune", "other cities", "areas you cover"),
          f"{brand.NAME} works in Pune: agents across Pune can join, and our area guides cover the main localities.", "any"),
    Entry("contact", ("contact you", "call me", "call back", "callback", "talk to someone", "customer care"),
          "Leave your name and mobile and we call you back. Buyers can also share their requirement here and our team gets back to them.",
          "any", "Agents: /request-invite."),
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


def text(e: Entry) -> str:
    """The chat's wording: the answer and its next step."""
    return f"{e.answer} {e.cta}".strip()


LLM_SYSTEM = (
    f"You answer a question for {brand.NAME} (a service for real estate agents in Pune, and a helper for home buyers), using ONLY the KNOWLEDGE "
    'below. Reply with one JSON object: {"answerable": true or false, "answer": "..."}. The answer is at most 3 short sentences, in the '
    "asker's language, friendly and plain. If KNOWLEDGE does not contain the answer, set answerable=false and answer=''. Never invent prices, "
    "fees, distances, dates, amenities, approvals or availability. Never include phone numbers or links. Never use words like best, perfect, "
    "guaranteed, dream."
)


async def answer(question: str, llm) -> Optional[Entry]:
    """The vetted entry for a question: a keyword hit, else the LLM's answer from all entries (an Entry with id 'llm'), else None."""
    hit = best(question, min_score=1)
    if hit:
        return hit
    if llm is None or not hasattr(llm, "json"):
        return None
    from app.modules.engage.brain import valid_reply  # engage imports knowledge, so not at module level
    context = "\n".join(f"- {e.answer}" for e in ENTRIES)
    raw = await llm.json(LLM_SYSTEM, f"KNOWLEDGE:\n{context}\n\nQUESTION:\n{question[:400]}")
    if isinstance(raw, dict) and raw.get("answerable") is True:
        draft = (raw.get("answer") or "").strip()
        if valid_reply(draft, context, ""):
            return Entry("llm", (), draft, "any")
    return None
