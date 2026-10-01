"""Topic rules for the relevance filter: what is NOT useful to a Pune home buyer, and which places are not ours.

Policy-like constants kept next to the filter (policy.py is owned elsewhere). Plain data, no I/O.
"""
import re

# keywords in policy.AREA_KEYWORDS that are landmarks, not the locality itself
LANDMARKS = {"eon it park", "world trade center pune", "wtc pune", "magarpatta"}

# localities that are NOT ours; a landmark-only match next to one of these means the story is about that locality
OTHER_LOCALITIES = [
    "wakad", "tathawade", "hinjewadi", "baner", "balewadi", "aundh", "pashan", "kothrud", "hadapsar", "viman nagar",
    "koregaon park", "yerawada", "kalyani nagar", "mundhwa", "kondhwa", "undri", "wanowrie", "bavdhan", "pimple saudagar",
    "pimple nilakh", "ravet", "moshi", "chikhali", "talegaon", "chakan", "dhanori", "shivajinagar",
    "katraj", "warje", "sinhagad road", "nigdi", "akurdi", "pimpri", "chinchwad", "mumbai", "thane", "navi mumbai",
]

# (label, pattern). Checked against the title and the first sentence of the text.
DENY_TOPICS = [
    ("vehicle prices", re.compile(r"\b(on[- ]road price|ex[- ]showroom|car prices?|bike prices?|mileage|test drive)\b", re.I)),
    ("hotels and restaurants", re.compile(r"\b(hotels?|resorts?|restaurants?|cafes?|menu|buffet|brunch|dinner|lunch|breakfast|general manager|chef|cuisine|novotel|marriott|hyatt|radisson|hospitality)\b", re.I)),
    ("PG and rental ads", re.compile(r"\b(paying guests?|pg accommodation|pg in|co-?living|hostels?|rooms? for rent|flatmates?)\b", re.I)),
    ("festival or celebration", re.compile(
        r"\b(celebrat\w*|festivals?|utsav|ganeshotsav|ganpati|navratri|dandiya|diwali|dussehra|holi|eid|christmas|"
        r"visarjan|immersion|fervour|fervor|devotion|jayanti|mahotsav)\b", re.I)),
    ("sports", re.compile(r"\b(cricket|ipl|football|kabaddi|tournament|badminton|tennis|match(es)?|marathon|league|trophy)\b", re.I)),
    ("entertainment", re.compile(r"\b(movies?|films?|bollywood|actor|actress|web series|concert|box office|trailer|singer|album)\b", re.I)),
    ("weather", re.compile(r"\b(weather|imd|temperature|heat ?wave|cold wave|rainfall forecast|yellow alert|orange alert)\b", re.I)),
    ("unrelated government talk", re.compile(
        r"\b(maternal|nutrition|anganwadi|vaccination|immuni[sz]ation|blood donation|health camp|child health|"
        r"government priorit\w*|awareness (drive|campaign)|yoga day)\b", re.I)),
]
_PG = re.compile(r"\bPG\b")  # case-sensitive: 'pg' inside other words must not match

# one-day or few-day events are stale by nature, unless the text shows durable works
SHORT_LIVED = re.compile(
    r"\b(visarjan|immersion|procession|rally|today|tomorrow|tonight|this (weekend|evening|morning)|"
    r"(on|from|till|until) (mon|tues|wednes|thurs|fri|satur|sun)day|between \d{1,2}(:\d\d)?\s*(am|pm)|"
    r"traffic advisory|route advisory)\b", re.I)
_DIVERSION = re.compile(r"\b(diversions?|advisory|road closures?|closed for traffic)\b", re.I)
_DURABLE = re.compile(r"\b(girder|flyover|metro|construction|project|months?|weeks|permanent|long[- ]term|until further notice)\b", re.I)

# extra pillar evidence on top of policy.PILLAR_KEYWORDS (phrases, lowercase)
EXTRA_PILLAR_KEYWORDS = {
    "infrastructure": ["land acquisition", "acquisition", "drainage", "sewage", "waterlogging", "tender", "widening", "underpass", "interchange"],
    "new_supply": ["township", "housing project", "housing scheme", "affordable housing", "occupancy certificate"],
    "rules_money": ["property tax", "ready reckoner rate", "circle rate", "rera order", "tdr"],
    "locality_life": ["power cut", "electricity", "water tanker", "encroachment", "flooding"],
}
# education keywords; reported as locality_life until policy accepts 'education' in PILLAR_KEYWORDS (see handoff)
EDUCATION_KEYWORDS = ["school", "college", "university", "cbse", "icse", "admission", "campus"]

MIN_SCORE = 3  # buyer-relevance score below this is dropped


def short_lived(title: str, first: str) -> bool:
    t = f"{title} {first}"
    return bool(_DIVERSION.search(t) and SHORT_LIVED.search(t) and not _DURABLE.search(t))


def denied_topic(title: str, first: str) -> str:
    t = f"{title}\n{first}"
    for label, rx in DENY_TOPICS:
        if rx.search(t):
            return label
    if _PG.search(t):
        return "PG and rental ads"
    return ""
