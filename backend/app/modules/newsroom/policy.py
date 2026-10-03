"""Editorial policy as data (docs/NEWSROOM_PLAN.md section 1). Plain constants, no I/O."""
from app.core import brand
import re

MAX_AGE_DAYS = 14  # news older than this is dropped (evergreen education items are exempt)
DAILY_CAP = 2  # posts a day at most
MAX_QUOTE_WORDS = 15  # longest run of words we may repeat from a source
POST_MAX_CHARS = 900

# area name (as used in `AREAS`) -> lowercase phrases that show an item is about it
AREA_KEYWORDS = {
    "kharadi": ["kharadi", "eon it park", "world trade center pune", "wtc pune", "magarpatta"],
    "upper_kharadi": ["upper kharadi"],
    "wagholi": ["wagholi", "lohegaon", "bakori", "kesnand"],
}
# pincode -> area. MahaRERA gives the taluka ("Haveli"), not the locality, so the pincode is how its items find us.
# 411014 also covers Upper Kharadi (Thite Nagar); 412207 also covers Kesnand and Bakori (verified 2026-10-02)
AREA_PINCODES = {"411014": "kharadi", "412207": "wagholi", "411047": "wagholi"}
MAHARERA_PAGES = 15  # newest 150 Pune district projects per run; the pincode filter keeps only ours
# the only honest wording for a MahaRERA item: the date we have is "Last Modified", not the registration date
MAHARERA_PHRASE = "listed or updated on MahaRERA"
# corridor topics that affect our areas even when no area is named (matched together with a Pune hint)
CORRIDOR_KEYWORDS = [
    "pune ring road", "nagar road", "ramwadi", "wagholi metro", "kharadi metro", "pune-ahmednagar", "shirur road",
    "pune airport", "purandar airport", "ring road pune", "kharadi bypass", "hadapsar-kharadi",
]
PUNE_HINT = ("pune", "pimpri", "pmc", "pmrda", "maharera")

# pillar -> phrases that suggest it
PILLAR_KEYWORDS = {
    "infrastructure": ["metro", "flyover", "bridge", "road", "airport", "ring road", "pmrda", "pmc", "corridor", "bus", "brts"],
    "new_supply": ["maharera", "rera registration", "registered project", "new project", "launch", "possession"],
    "rules_money": ["stamp duty", "registration fee", "rera", "home loan", "repo rate", "interest rate", "gst", "ready reckoner"],
    "locality_life": ["school", "hospital", "it park", "office", "water supply", "traffic", "garbage", "mall"],
}

# pillar -> formats we may draft for it (first is the default)
FORMATS_BY_PILLAR = {
    "infrastructure": ["post", "article"],
    "new_supply": ["post"],
    "rules_money": ["post", "article"],
    "locality_life": ["post"],
    "education": ["post", "article"],
    "digest": ["digest"],
}

# statements we never publish, whatever the source says
BANNED = re.compile(
    r"\b(will (rise|increase|double|appreciate|go up)|guarantee[ds]?|assured returns?|invest now|best (builder|project)|"
    r"don'?t miss|hurry|limited (period|time|units)|once in a lifetime|sure[- ]?shot)\b", re.I)

DISCLAIMER = ("Approvals and project status change, so check the sources before you decide. "
              "This is general information, not investment or legal advice.")
SITE = brand.SITE

# 'Why it matters' for a buyer: one fixed house line per pillar and sub-type, chosen by code (presentation.buyer_line), never written by
# the LLM. Practical things to verify only: no prediction, no 'will', no price, date or investment talk. These exact strings are the
# only text the check stage reads as ours rather than the source's (check._without_house_lines); an edited copy is checked like any
# other text.
BUYER_LINES = {
    ("infrastructure", "transport"): "Worth checking: how far your shortlisted project is from this road or line.",
    ("infrastructure", "other"): "Worth checking: how close your shortlisted project is to this work.",
    ("new_supply", "maharera"): "Worth checking: before a visit, open the project's MahaRERA page and match the possession date.",
    ("new_supply", "other"): "Worth checking: before a visit, ask for the project's MahaRERA number and look it up on the MahaRERA website.",
    ("rules_money", "loan"): "Worth checking: ask your bank how this applies to your loan before you decide.",
    ("rules_money", "cost"): "Worth checking: ask the seller or your lawyer how this changes your total cost before you decide.",
    ("rules_money", "other"): "Worth checking: ask your lawyer how this applies to your purchase before you decide.",
    ("locality_life", ""): "Worth checking on a weekday visit: traffic and water at the times you would use them.",
}  # education items are already a tip and the digest carries its own: neither gets a line
# pillar -> [(sub-type, words that select it)], first match wins; no match falls back to the pillar's "other" line
BUYER_SUBTYPES = {
    "infrastructure": [("transport", ("metro", "road", "roads", "flyover", "bridge", "rail", "railway", "station", "corridor", "highway",
                                      "bus", "brts", "line", "bypass", "underpass", "tunnel"))],
    "new_supply": [("maharera", ("maharera",))],
    "rules_money": [("loan", ("home loan", "home-loan", "repo", "interest rate", "emi", "bank", "banks", "lending rate")),
                    ("cost", ("stamp duty", "registration fee", "ready reckoner", "gst", "circle rate", "property tax"))],
}
