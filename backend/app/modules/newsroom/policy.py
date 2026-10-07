"""Editorial policy as data (docs/NEWSROOM_PLAN.md section 1). Plain constants, no I/O."""
from app.core import brand
import re

MAX_AGE_DAYS = 14  # news older than this is dropped (evergreen education items are exempt)
DAILY_CAP = 2  # posts a day at most
MAX_QUOTE_WORDS = 15  # longest run of words we may repeat from a source
POST_MAX_CHARS = 900

# NEWS scope: area key (app.core.areas) -> lowercase phrases that show a news item is about it. Narrower than the 8 areas on
# purpose: Hinjawadi, Wakad and Baner news is still "another locality" for the news filter (stages/topics.OTHER_LOCALITIES)
# until the owner widens the news scope. The project register below covers all 8 areas.
AREA_KEYWORDS = {
    "kharadi": ["kharadi", "eon it park", "world trade center pune", "wtc pune", "magarpatta"],
    "upper_kharadi": ["upper kharadi"],
    "wagholi": ["wagholi", "bakori", "kesnand"],
    "lohegaon": ["lohegaon", "lohgaon"],
}
# Which MahaRERA project is in which area. MahaRERA gives the taluka ("Haveli"), not the locality, so the pincode decides,
# with the project name where one pincode covers more than one place. Verified 2026-10-04 against the MahaRERA search
# (project_location=<pincode> lists a pincode's projects; project_name=<word> lists projects by name):
# - 411014: 325 projects; Kharadi-named ones (Mantra Kharadi, Palladio Kharadi Central, VJ IndiLife Kharadi) are here. Upper
#   Kharadi (Thite Nagar) shares it (2026-10-02).
# - 412207: 380 projects; Wagholi-named ones are here, and so are many named Kharadi ("Kharadi Pune P1", "Kharadi New Project",
#   "Menlo Homes Kharadi Next"): the pincode says Wagholi, so they stay Wagholi; "MY HOME UPPER KHARADI" is 412207 too, so
#   a name saying Upper Kharadi wins here as in 411014. Kesnand and Bakori share it (2026-10-02).
# - 411047: 196 projects (Belmont Skyone, Goodwill Metropolis East, Hollyhock City, NESTERRA): Lohegaon's pincode. It used to map
#   to Wagholi, which put Lohegaon projects under Wagholi. No project names Lohegaon; Dhanori-named ones are 411015. One is named
#   for Viman Nagar ("Solitaire Business Hub Viman Nagar"), so a name that says another locality keeps a project out.
# - 411057: 645 projects, shared: Hinjawadi (31 of the 33 Hinjewadi/Hinjawadi-named ones read are here, the other 2 are 410506)
#   and Wakad (all 9 Wakad-named ones), plus Maan, Marunji and others; most names say neither, so the name must say which.
# - 411036: 243 projects, shared with Mundhwa (5 Mundhwa-named here). No MahaRERA project names Keshav Nagar (2026-10-04), so
#   Keshav Nagar has projects only once one is named for it.
# - 411045: 714 projects, shared: Baner (18 of 19 Baner-named here) and Balewadi (all 7 Balewadi-named here), Mhalunge.
# The detail API's address (getProjectLegalLandAddressDetails) needs a login (401), so names and pincodes are all we can use.
AREA_PINCODES = {"411014": "kharadi", "412207": "wagholi", "411047": "lohegaon"}  # pincode -> its area
SHARED_PINCODES = {"411057": ("hinjawadi", "wakad"), "411036": ("keshav_nagar",), "411045": ("baner",)}  # name decides
# Upper Kharadi has no pincode of its own: within these, a name that says Upper Kharadi is the finer answer
UPPER_KHARADI_PINCODES = ("411014", "412207")
# a project named for an area but filed under none of these pincodes counts only near Pune city: "Xrbia Hinjewadi Road" is
# 410506 (the Talegaon side), not Hinjawadi; "Pune Baner Project-Tower 4 and 5" (411038) is Baner (its Tower 3 is 411045)
NAME_ONLY_PINCODE_PREFIXES = ("411", "412")
# newest 150 Pune district projects per run: enough for new registrations (Pune grew from 12920 to 12949 projects in two days,
# 2026-10-02 to 2026-10-04; a run is every 3 hours), whatever the number of areas, because the pincode filter picks ours from
# the whole district. Older projects in our areas come from the area sweep (areastats.refresh), not from here.
MAHARERA_PAGES = 15
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
