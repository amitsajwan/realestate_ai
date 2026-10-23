"""Every place in Pune district a MahaRERA project can be filed under, grouped the way buyers name them (Kharadi, Wakad, Undri),
for the all-Pune project register. Our 8 covered areas (app/core/areas.py) keep their own pages and facts; this list only groups
projects. Source of the pincode -> post offices facts: India Post (api.postalpincode.in, read 2026-10-09; 141 Pune district
pincodes). Area names and which pincode each belongs to are the market's names for those post offices.

How a project gets its place (`place_of`):
1. a place named in the project name, when that place is filed under the same pincode ("Wakad" in 411057, not Hinjawadi);
2. else the pincode's default place;
3. else, for a pincode we have no entry for, the taluka India Post gives (e.g. "Maval taluka").
A name alone never moves a project to another pincode's place: builders put famous names on far-off projects.
"""
import re
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class Place:
    key: str                         # stable id: "viman_nagar"
    name: str                        # "Viman Nagar"
    zone: str                        # for grouping lists: "East Pune", "PCMC", ...
    pincodes: Tuple[str, ...]        # pincodes this place is filed under (several places may share one)
    aliases: Tuple[str, ...] = ()    # other spellings in project names, lower case; the name itself is always matched

    @property
    def slug(self) -> str:
        return self.key.replace("_", "-")


Z_CENTRAL, Z_EAST, Z_SOUTH, Z_WEST, Z_PCMC = "Central Pune", "East Pune", "South Pune", "West Pune", "Pimpri-Chinchwad"
Z_NORTH, Z_OUT = "North Pune and Chakan", "Pune district"

# Order matters within a pincode: the FIRST place listing a pincode is that pincode's default.
PLACES: Tuple[Place, ...] = (
    # ---- East
    Place("kharadi", "Kharadi", Z_EAST, ("411014",), ("kharadi",)),
    Place("upper_kharadi", "Upper Kharadi", Z_EAST, ("411014", "412207", "412307"), ("upper kharadi", "upper-kharadi")),
    Place("viman_nagar", "Viman Nagar", Z_EAST, ("411014", "411032"), ("viman nagar", "vimannagar")),
    Place("vadgaon_sheri", "Vadgaon Sheri", Z_EAST, ("411014",), ("vadgaon sheri", "wadgaon sheri", "wadgaonsheri")),
    Place("kalyani_nagar", "Kalyani Nagar", Z_EAST, ("411006",), ("kalyani nagar", "kalyaninagar")),
    Place("yerwada", "Yerwada", Z_EAST, ("411006",), ("yerwada", "yerawada")),
    Place("wagholi", "Wagholi", Z_EAST, ("412207",), ("wagholi", "vagholi")),
    Place("kesnand", "Kesnand", Z_EAST, ("412207",), ("kesnand",)),
    Place("lohegaon", "Lohegaon", Z_EAST, ("411047",), ("lohegaon", "lohgaon", "lohogaon")),
    Place("dhanori", "Dhanori", Z_EAST, ("411015",), ("dhanori",)),
    Place("vishrantwadi", "Vishrantwadi", Z_EAST, ("411015",), ("vishrantwadi", "tingre nagar")),
    Place("airport_road", "Airport Road", Z_EAST, ("411032",), ("airport road", "vidyanagar")),
    Place("keshav_nagar", "Keshav Nagar", Z_EAST, ("411036",), ("keshav nagar", "keshavnagar")),
    Place("mundhwa", "Mundhwa", Z_EAST, ("411036",), ("mundhwa", "mundhva")),
    Place("manjari", "Manjari", Z_EAST, ("412307",), ("manjari",)),
    Place("hadapsar", "Hadapsar", Z_EAST, ("411028", "411013"), ("hadapsar",)),
    Place("magarpatta", "Magarpatta", Z_EAST, ("411028", "411013"), ("magarpatta", "amanora")),
    Place("mohammadwadi", "Mohammadwadi", Z_EAST, ("411060",), ("mohammadwadi", "mohamadwadi")),
    Place("undri", "Undri", Z_EAST, ("411060",), ("undri",)),
    Place("phursungi", "Phursungi", Z_EAST, ("412308",), ("phursungi", "fursungi", "uruli devachi")),
    Place("wanowrie", "Wanowrie", Z_EAST, ("411040", "411022"), ("wanowrie", "wanwadi", "wanowarie")),
    Place("kondhwa", "Kondhwa", Z_EAST, ("411048",), ("kondhwa",)),
    Place("nibm", "NIBM", Z_EAST, ("411048",), ("nibm",)),
    Place("lonikand", "Lonikand", Z_EAST, ("412216",), ("lonikand", "koregaon bhima")),
    Place("loni_kalbhor", "Loni Kalbhor", Z_EAST, ("412201",), ("loni kalbhor", "kunjirwadi")),
    Place("theur", "Theur", Z_EAST, ("412110",), ("theur",)),
    Place("uruli_kanchan", "Uruli Kanchan", Z_EAST, ("412202",), ("uruli kanchan", "urulikanchan")),
    # ---- Central
    Place("camp", "Camp", Z_CENTRAL, ("411001",), ("camp", "pune cantonment")),
    Place("peth_areas", "Peth areas", Z_CENTRAL, ("411002", "411011", "411030", "411042"), ("peth", "swargate")),
    Place("deccan", "Deccan", Z_CENTRAL, ("411004",), ("deccan", "prabhat road", "erandwane")),
    Place("shivajinagar", "Shivajinagar", Z_CENTRAL, ("411005", "411016"), ("shivajinagar", "model colony", "gokhalenagar")),
    Place("parvati", "Parvati", Z_CENTRAL, ("411009",), ("parvati",)),
    Place("bibwewadi", "Bibwewadi", Z_CENTRAL, ("411037",), ("bibwewadi", "bibvewadi", "market yard", "salisbury park")),
    Place("khadki", "Khadki", Z_CENTRAL, ("411003", "411020"), ("khadki",)),
    # ---- South
    Place("katraj", "Katraj", Z_SOUTH, ("411046",), ("katraj",)),
    Place("ambegaon", "Ambegaon", Z_SOUTH, ("411046",), ("ambegaon",)),
    Place("dhankawadi", "Dhankawadi", Z_SOUTH, ("411043",), ("dhankawadi",)),
    Place("dhayari", "Dhayari", Z_SOUTH, ("411041",), ("dhayari", "dhayri")),
    Place("narhe", "Narhe", Z_SOUTH, ("411041",), ("narhe",)),
    Place("vadgaon_budruk", "Vadgaon Budruk", Z_SOUTH, ("411041",), ("vadgaon budruk", "vadgaon bk", "wadgaon budruk")),
    Place("nanded_city", "Nanded City", Z_SOUTH, ("411041",), ("nanded city", "nanded")),
    Place("sinhagad_road", "Sinhagad Road", Z_SOUTH, ("411051",), ("sinhagad road", "anand nagar")),
    Place("kirkatwadi", "Kirkatwadi and Khadakwasla", Z_SOUTH, ("411024", "411025"), ("kirkatwadi", "khadakwasla", "nanded phata")),
    Place("shivane", "Shivane and NDA Road", Z_SOUTH, ("411023",), ("shivane", "nda road", "uttam nagar", "uttamnagar")),
    Place("karve_nagar", "Karve Nagar", Z_SOUTH, ("411052",), ("karve nagar", "karvenagar")),
    Place("warje", "Warje", Z_SOUTH, ("411058",), ("warje",)),
    Place("kothrud", "Kothrud", Z_SOUTH, ("411038",), ("kothrud",)),
    Place("bavdhan", "Bavdhan", Z_WEST, ("411021",), ("bavdhan", "bavdhan budruk")),
    Place("sus", "Sus", Z_WEST, ("411021",), ("sus gaon", "susgaon", " sus ")),
    # ---- West
    Place("baner", "Baner", Z_WEST, ("411045",), ("baner",)),
    Place("balewadi", "Balewadi", Z_WEST, ("411045",), ("balewadi",)),
    Place("mahalunge", "Mahalunge", Z_WEST, ("411045",), ("mahalunge",)),
    Place("pashan", "Pashan", Z_WEST, ("411008",), ("pashan", "sutarwadi")),
    Place("aundh", "Aundh", Z_WEST, ("411007",), ("aundh",)),
    Place("hinjawadi", "Hinjawadi", Z_WEST, ("411057",), ("hinjawadi", "hinjewadi")),
    Place("wakad", "Wakad", Z_WEST, ("411057",), ("wakad",)),
    Place("marunji", "Marunji", Z_WEST, ("411057",), ("marunji", "maan", "man gaon")),
    Place("tathawade", "Tathawade", Z_WEST, ("411033",), ("tathawade", "thathawade")),
    Place("punawale", "Punawale", Z_WEST, ("411033",), ("punawale",)),
    Place("thergaon", "Thergaon", Z_PCMC, ("411033",), ("thergaon",)),
    Place("pirangut", "Pirangut", Z_WEST, ("412115",), ("pirangut", "bhugaon", "bhukum", "lavale")),
    Place("paud", "Paud and Mulshi", Z_WEST, ("412108",), ("paud", "mulshi")),
    Place("lavasa", "Lavasa", Z_WEST, ("412112",), ("lavasa",)),
    # ---- Pimpri-Chinchwad
    Place("pimple_saudagar", "Pimple Saudagar", Z_PCMC, ("411027",), ("pimple saudagar",)),
    Place("sangvi", "Sangvi", Z_PCMC, ("411027",), ("sangvi", "sangavi")),
    Place("pimple_nilakh", "Pimple Nilakh", Z_PCMC, ("411027",), ("pimple nilakh",)),
    Place("pimple_gurav", "Pimple Gurav", Z_PCMC, ("411061",), ("pimple gurav",)),
    Place("pimpri", "Pimpri", Z_PCMC, ("411017", "411018"), ("pimpri", "kalewadi", "rahatani")),
    Place("chinchwad", "Chinchwad", Z_PCMC, ("411019", "411033"), ("chinchwad",)),
    Place("akurdi", "Akurdi", Z_PCMC, ("411035",), ("akurdi",)),
    Place("nigdi", "Nigdi", Z_PCMC, ("411044",), ("nigdi", "pradhikaran")),
    Place("bhosari", "Bhosari", Z_PCMC, ("411026", "411039"), ("bhosari",)),
    Place("kasarwadi", "Kasarwadi", Z_PCMC, ("411034",), ("kasarwadi",)),
    Place("dapodi", "Dapodi", Z_PCMC, ("411012", "411031"), ("dapodi",)),
    Place("chikhali", "Chikhali", Z_PCMC, ("411062",), ("chikhali", "talawade", "talwade")),
    Place("moshi", "Moshi", Z_PCMC, ("412105",), ("moshi",)),
    Place("charholi", "Charholi", Z_PCMC, ("412105",), ("charholi", "charoli", "dudulgaon")),
    Place("alandi", "Alandi", Z_PCMC, ("412105",), ("alandi",)),
    Place("ravet", "Ravet", Z_PCMC, ("412101",), ("ravet",)),
    Place("kiwale", "Kiwale", Z_PCMC, ("412101",), ("kiwale", "dehu road", "dehuroad")),
    Place("dehu", "Dehu", Z_PCMC, ("412109",), ("dehu",)),
    # ---- North and Chakan
    Place("chakan", "Chakan", Z_NORTH, ("410501",), ("chakan", "mahalunge ingale", "kuruli", "nighoje")),
    Place("talegaon", "Talegaon", Z_NORTH, ("410506", "410507"), ("talegaon", "induri", "varale")),
    Place("shikrapur", "Shikrapur", Z_NORTH, ("412208",), ("shikrapur", "sanaswadi")),
    Place("ranjangaon", "Ranjangaon", Z_NORTH, ("412220", "412209"), ("ranjangaon", "karegaon")),
    # ---- District towns
    Place("lonavala", "Lonavala and Khandala", Z_OUT, ("410401", "410402", "410403", "410301", "410302"), ("lonavala", "lonavla", "khandala")),
    Place("kamshet", "Kamshet", Z_OUT, ("410405",), ("kamshet",)),
    Place("shirur", "Shirur", Z_OUT, ("412210",), ("shirur",)),
    Place("saswad", "Saswad", Z_OUT, ("412301",), ("saswad",)),
    Place("jejuri", "Jejuri", Z_OUT, ("412303",), ("jejuri",)),
    Place("yavat", "Yavat", Z_OUT, ("412214",), ("yavat",)),
    Place("narayangaon", "Narayangaon", Z_OUT, ("410504",), ("narayangaon",)),
    Place("manchar", "Manchar", Z_OUT, ("410503",), ("manchar",)),
    Place("junnar", "Junnar", Z_OUT, ("410502",), ("junnar",)),
    Place("rajgurunagar", "Rajgurunagar (Khed)", Z_OUT, ("410505",), ("rajgurunagar",)),
    Place("bhor", "Bhor", Z_OUT, ("412206",), ("bhor",)),
    Place("baramati", "Baramati", Z_OUT, ("413102", "413133", "413110", "413115", "413116"), ("baramati",)),
    Place("indapur", "Indapur", Z_OUT, ("413106", "413103", "413104", "413105", "413114", "413120", "413130", "413132"), ("indapur", "bhigwan")),
    Place("daund", "Daund", Z_OUT, ("413801", "413802"), ("daund", "kurkumbh")),
)

# a shared pincode's default place where it is not the first place listing it
PIN_DEFAULTS: Dict[str, str] = {"412207": "wagholi", "411036": "mundhwa", "412307": "manjari", "411032": "airport_road", "411033": "tathawade"}
# projects whose name does not say where they are, placed by hand after checking (registration number -> place key)
VERIFIED: Dict[str, str] = {
    "PR1261012500289": "upper_kharadi",  # Geras Avive Towers Phase I, 412307: sold as Upper Kharadi (owner, 2026-10-09)
    # Lodha Camelot, 412207 ("Kharadi New Project - Tower N" on MahaRERA): the 5 registrations its brochure (Nov 2025) lists,
    # sold as Upper Kharadi. Towers 5, 6 and 9 (same promoter and naming) are not in the brochure and are not placed here.
    "PR1260002501386": "upper_kharadi",  # Tower 1
    "PR1260002501413": "upper_kharadi",  # Tower 2
    "PR1260002501399": "upper_kharadi",  # Tower 3
    "PR1260002501398": "upper_kharadi",  # Tower 4
    "PR1260002501449": "upper_kharadi",  # Tower 11
    # Godrej Ivara: MahaRERA's card shows the promoter's Mumbai PIN (400079); portals and the builder sell it on Upper Kharadi
    # Main Road, Wagholi side (2026-10-19)
    "PR1260002502426": "upper_kharadi",
    # 412207 projects the builder, or two or more listings, place in Upper Kharadi (Upper Kharadi Main Road, Ubale Nagar,
    # Vitthal Nagar), read 2026-10-23 from our stored Google results and portal pages; a group's phases move together.
    # Left in Wagholi with only housing.com's area tag or a hashtag: Prime Angan, SB Sai Sanskruti, Springshire, Ganga Pavitra.
    "PR1260002501224": "upper_kharadi",  # 31 Palma Drive Phase 1: builder's site, housiey, punepropertyinvestor
    "PR1261012601574": "upper_kharadi",  # 31 Palma Drive Phase 2
    "P52100080905": "upper_kharadi",     # Saina Serenity: builder's site "located in Upper Kharadi", housing.com
    "P52100023185": "upper_kharadi",     # Menlo Business Hub: builder's address "Nagar Road, Upper Kharadi"
    "P52100078861": "upper_kharadi",     # iLIFE Business Zone: its own Instagram and video, "Upper Kharadi"
    # Lodha Kharadi Pune (sold as Giardino / Estilo): JLL, HomeBazaar, PropHunt "Upper Kharadi Main Rd", Camelot's land
    "P52100047587": "upper_kharadi",     # Phase I Tower 1 to 4
    "P52100048326": "upper_kharadi",     # Phase I Tower 5
    "P52100051552": "upper_kharadi",     # Phase II Tower 6
    "P52100050123": "upper_kharadi",     # Phase II Tower 7
    "P52100079422": "upper_kharadi",     # Phase II Tower 8
    "P52100078396": "upper_kharadi",     # P1
    "P52100052703": "upper_kharadi",     # P2
    "P52100054436": "upper_kharadi",     # P3
    # Kharadi New Project Towers 5, 6, 9: Camelot's site, so Upper Kharadi; still NOT part of Camelot (owner, 2026-10-13)
    "PR1260002502039": "upper_kharadi",  # Tower 5
    "PR1260002602176": "upper_kharadi",  # Tower 6
    "PR1260002602168": "upper_kharadi",  # Tower 9
    # VJ Yashwin Enchante and UK1321 (same promoter and land): JLL, HomeBazaar "Upper Kharadi Main Road"
    "P52100046510": "upper_kharadi",     # Yashwin Enchante Phase 1
    "P52100077455": "upper_kharadi",     # Yashwin Enchante Phase 2
    "P52100049638": "upper_kharadi",     # UK1321 Inclusive Housing
    # Majestique Towers East: most listings "Upper Kharadi Main Road, Vitthal Nagar", the builder's own video
    "P52100015020": "upper_kharadi",     # Phase 1
    "P52100015183": "upper_kharadi",     # Phase 2
    "P52100028815": "upper_kharadi",     # Phase 3
    "P52100046709": "upper_kharadi",     # Phase 5
    "P52100053786": "upper_kharadi",     # Phase 6
    "P52100078306": "upper_kharadi",     # Phase 7
    "PR1260002600313": "upper_kharadi",  # Phase 8
    "PR1260002503000": "upper_kharadi",  # Phase 9
    # Pristine O2 World: listings "Upper Kharadi Main Road, Ubale Nagar, Wagholi"
    "P52100054937": "upper_kharadi",     # Part 1
    "P52100066545": "upper_kharadi",     # Part 2
    "P52100079026": "upper_kharadi",     # Part 3
    "P52100079395": "upper_kharadi",     # Part 4
}

BY_KEY: Dict[str, Place] = {p.key: p for p in PLACES}
BY_SLUG: Dict[str, Place] = {p.slug: p for p in PLACES}
DEFAULT_BY_PIN: Dict[str, Place] = {}
for _p in PLACES:
    for _pin in _p.pincodes:
        DEFAULT_BY_PIN.setdefault(_pin, _p)
DEFAULT_BY_PIN.update({pin: BY_KEY[k] for pin, k in PIN_DEFAULTS.items()})

# Every Pune district pincode and its taluka (India Post "Block", read 2026-10-09): the register sweeps all of them, and a
# pincode with no place above is grouped by its taluka
TALUKA_BY_PIN: Dict[str, str] = {
    "410301": "Maval",
    "410302": "Maval",
    "410401": "Maval",
    "410402": "Maval",
    "410403": "Maval",
    "410405": "Maval",
    "410406": "Maval",
    "410501": "Khed",
    "410502": "Junnar",
    "410503": "Ambegaon",
    "410504": "Junnar",
    "410505": "Khed",
    "410506": "Maval",
    "410507": "Maval",
    "410508": "Ambegaon",
    "410509": "Ambegaon",
    "410510": "Ambegaon",
    "410511": "Junnar",
    "410512": "Khed",
    "410513": "Khed",
    "410515": "Ambegaon",
    "410516": "Ambegaon",
    "411001": "Pune City",
    "411002": "Pune City",
    "411003": "Pune City",
    "411004": "Pune City",
    "411005": "Pune City",
    "411006": "Pune City",
    "411007": "Haveli",
    "411008": "Pune City",
    "411009": "Pune City",
    "411011": "Pune City",
    "411012": "Pune City",
    "411013": "Pune City",
    "411014": "Pune City",
    "411015": "Pune City",
    "411016": "Haveli",
    "411017": "Pune City",
    "411018": "Pune City",
    "411019": "Pune City",
    "411020": "Pune City",
    "411021": "Pune City",
    "411022": "Pune City",
    "411023": "Haveli",
    "411024": "Pune City",
    "411025": "Haveli",
    "411026": "Pune City",
    "411027": "NA",
    "411028": "Pune",
    "411030": "Pune City",
    "411031": "Pune City",
    "411032": "Pune City",
    "411033": "Pune City",
    "411034": "Pune City",
    "411035": "Pune City",
    "411036": "Pune City",
    "411037": "Pune City",
    "411038": "Pune City",
    "411039": "Pune City",
    "411040": "Pune City",
    "411041": "Haveli",
    "411042": "Pune City",
    "411043": "Pune City",
    "411044": "Pune City",
    "411045": "Haveli",
    "411046": "Haveli",
    "411047": "Pune City",
    "411048": "Pune City",
    "411051": "Pune City",
    "411052": "Pune City",
    "411057": "Haveli",
    "411058": "Pune City",
    "411060": "Pune City",
    "411061": "Haveli",
    "411062": "Haveli",
    "412101": "Haveli",
    "412102": "Purandar",
    "412103": "Baramati",
    "412104": "Purandar",
    "412105": "Khed",
    "412106": "Maval",
    "412107": "Velhe",
    "412108": "Mulshi",
    "412109": "Haveli",
    "412110": "Haveli",
    "412112": "Mulshi",
    "412115": "Mulshi",
    "412201": "Haveli",
    "412202": "Daund",
    "412203": "Daund",
    "412204": "Baramati",
    "412205": "Bhor",
    "412206": "Bhor",
    "412207": "Haveli",
    "412208": "Shirur",
    "412209": "Shirur",
    "412210": "Shirur",
    "412211": "Shirur",
    "412212": "Velhe",
    "412213": "Bhor",
    "412214": "Daund",
    "412215": "Daund",
    "412216": "Haveli",
    "412218": "Shirur",
    "412219": "Daund",
    "412220": "Shirur",
    "412301": "Purandar",
    "412303": "Purandar",
    "412304": "Baramati",
    "412305": "Purandar",
    "412306": "Baramati",
    "412307": "Haveli",
    "412308": "Haveli",
    "412311": "Purandar",
    "412312": "Purandar",
    "412401": "Junnar",
    "412402": "Khed",
    "412403": "Shirur",
    "412404": "Khed",
    "412405": "Ambegaon",
    "412406": "Ambegaon",
    "412408": "Ambegaon",
    "412409": "Junnar",
    "412410": "Junnar",
    "412411": "Junnar",
    "412412": "Junnar",
    "413102": "Baramati",
    "413103": "Indapur",
    "413104": "Indapur",
    "413105": "Indapur",
    "413106": "Indapur",
    "413110": "Baramati",
    "413114": "Indapur",
    "413115": "Baramati",
    "413116": "Baramati",
    "413120": "Indapur",
    "413130": "Indapur",
    "413132": "Indapur",
    "413133": "Baramati",
    "413801": "Daund",
    "413802": "Daund"
}
ALL_PINCODES: Tuple[str, ...] = tuple(sorted(TALUKA_BY_PIN))


def _norm(s: str) -> str:
    return " " + re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip() + " "


def _named(place: Place, text: str) -> int:
    """Length of the longest of the place's names found as whole words in text (0 when none)."""
    best = 0
    for al in (place.name.lower(),) + place.aliases:
        a = _norm(al)
        if len(a) > 2 and a in text:
            best = max(best, len(a))
    return best


def place_of(name: str, pincode: str, regno: str = "") -> Optional[Place]:
    """The place of a project from its name and pincode; None outside Pune district or when the pincode is unknown."""
    if regno and regno.strip().upper() in VERIFIED:
        return BY_KEY[VERIFIED[regno.strip().upper()]]
    pin = (pincode or "").strip()
    here = [p for p in PLACES if pin in p.pincodes]
    if not here:
        return None
    text = _norm(name)
    scored = sorted(((_named(p, text), i, p) for i, p in enumerate(here)), key=lambda t: (-t[0], t[1]))
    return scored[0][2] if scored[0][0] else DEFAULT_BY_PIN[pin]


def place_name(name: str, pincode: str, taluka: str = "", regno: str = "") -> Optional[str]:
    """A display name for a project's place: a Place's name, else "<Taluka> taluka" from the record or the pincode."""
    p = place_of(name, pincode, regno)
    if p:
        return p.name
    t = TALUKA_BY_PIN.get((pincode or "").strip()) or (taluka or "").strip().title()
    if t and t.lower() not in ("haveli", "pune city", "pune", "na"):
        return f"{t} taluka"
    return None


def place_key(name: str, pincode: str, regno: str = "") -> Optional[str]:
    """A stable grouping key: the Place's key, else "taluka_<name>" for a Pune district pincode, else None."""
    p = place_of(name, pincode, regno)
    if p:
        return p.key
    t = TALUKA_BY_PIN.get((pincode or "").strip())
    return f"taluka_{t.lower().replace(' ', '_')}" if t and t.lower() not in ("haveli", "pune city", "pune", "na") else None


# ---- a place in a buyer's search, however it is spelt -------------------------------------------------------------------------
# People type place names by ear: "lohegoan", "lohgaon", "vagholi", "hinjawadi", "kharedi". A search names a place when one of
# its names is in it as whole words; else when a run of 1 to 3 words sounds like one name (`sound`: no vowels, h, or doubled
# letters, a leading vowel kept as "a"; w=v, f=p, z=j, q/c=k). A sound shared by two places, or shorter than MIN_SOUND, is never used: we never guess.
# Only for searches (seo, demand): a project's place still comes from its pincode and exact names (`place_of`).
MIN_SOUND = 3
SPELT_LIKE = 0.75


def sound(s: str) -> str:
    t = re.sub(r"[^a-z]", "", (s or "").lower())
    t = t.translate(str.maketrans("wfzqc", "vpjkk")).replace("h", "")
    t = ("a" if t[:1] in "aeiou" and t else "") + re.sub(r"[aeiou]", "", t)
    return re.sub(r"(.)\1+", r"\1", t)


def _sounds() -> Dict[str, Tuple[str, str]]:
    seen: Dict[str, set] = {}
    for p in PLACES:
        for al in (p.name.lower(),) + p.aliases:
            k = sound(al)
            if len(k) >= MIN_SOUND:
                seen.setdefault(k, set()).add((p.key, al.replace(" ", "")))
    return {k: next(iter(v)) for k, v in seen.items() if len({key for key, _ in v}) == 1}


SOUNDS: Dict[str, Tuple[str, str]] = _sounds()   # sound -> (place key, the name it came from, spaces dropped)


def spellings(place: Place) -> Tuple[str, ...]:
    """Other spellings of the place's name ("Lohgaon", "Lohogaon" for Lohegaon), for the page to say and its structured data;
    aliases that are another name (Amanora for Magarpatta) are not spellings."""
    own = place.name.lower().replace(" ", "")
    out = []
    for al in place.aliases:
        if al.replace(" ", "").replace("-", "") != own and SequenceMatcher(None, al.replace(" ", ""), own).ratio() >= SPELT_LIKE \
                and "-" not in al:
            t = " ".join(w.capitalize() for w in al.split())
            if t not in out:
                out.append(t)
    return tuple(out)


def in_search(text: str) -> Optional[Tuple[Place, str]]:
    """(place, the words that named it) for a search phrase, or None. The longest exact name wins; else the run of words that
    sounds like one place's name and is spelt closest to it (SPELT_LIKE: "possession" sounds like Pashan but is not spelt
    like it)."""
    t = _norm(text)
    best: Optional[Tuple[Place, str]] = None
    for p in PLACES:
        for al in (p.name.lower(),) + p.aliases:
            a = _norm(al)
            if len(a) > 2 and a in t and (best is None or len(a) > len(best[1])):
                best = (p, a)
    if best:
        return best[0], best[1].strip()
    words, near = t.split(), None
    for n in (1, 2, 3):
        for i in range(len(words) - n + 1):
            run = words[i:i + n]
            joined = "".join(run)
            if len(joined) < 5 or any(w.isdigit() for w in run):
                continue
            hit = SOUNDS.get(sound(joined))
            if not hit:
                continue
            ratio = SequenceMatcher(None, joined, hit[1]).ratio()
            if ratio >= SPELT_LIKE and (near is None or ratio > near[0]):
                near = (ratio, hit[0], " ".join(run))
    return (BY_KEY[near[1]], near[2]) if near else None
