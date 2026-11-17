"""Pune Metro's stations: where each one is and whether trains stop there yet (docs/plan/area-pictures.md, step 1).

One hand-checked table that every page reads, like `work_hubs.py`. A station is here only when both its position and its status
were confirmed; the ones we could not confirm are left out rather than guessed (the list is in the plan).

How each row was checked, on 2026-11-17:
- Position: the station's OpenStreetMap object, looked up by id on Nominatim (nominatim.openstreetmap.org/lookup) the same day.
  Most ids are in our own copy (propertyfacts/data/pune_places.json.gz, category "railway"), where the names are mixed: one stop
  can be "Civil Court", "District Court" and "District Court Metro Station", and Line 3's stations still carry their old
  working names there ("Wipro", "Pall India", "IISER"). The id is what ties a row to the map, never the name.
- Lines 1 and 2: Maha-Metro's own lists on punemetrorail.org (route map, "Know your stations", the journey planner): 30 stations,
  29 running. Range Hill is the one built but not open (the planner leaves it out; OpenStreetMap marks it under construction).
  "R.T.O. Pune" is the station OpenStreetMap and older maps call Mangalwar Peth; "Kasba Peth" was Budhwar Peth.
- Line 1's extension from PCMC to Nigdi: Maha-Metro's Line 1 A page (4 elevated stations, under construction); the four are in
  OpenStreetMap as under construction, opening 2029.
- Line 3 (PMRDA's, Hinjawadi to Shivajinagar): opened on 4 November 2026 with 17 of its 23 stations (Hindustan Times, 3 November
  2026: "services will be available at 17 stations"; The Times of India, 27 October 2026, "17 of 23 stations cleared by CMRS").
  Which six are still closed (both Balewadi stations, both Baner stations, Bhosalenagar RBI and Shivajinagar) is OpenStreetMap's
  construction tag on each and the stations list on Wikipedia's Line 3 article, read the same day; the Times names the same ones by
  their nearby chowks. Our tracker (/news/track/pune-metro-line-3) follows the rest.

Status is only ever `running` or `being built`: a page says which in words, and never calls a station running before it opens.
"""
from dataclasses import dataclass
from typing import Dict, Tuple

# the day every row was last checked: pages say "as of" this, so a status is never read as newer than it is
CHECKED_ON = "2026-11-17"

RUNNING = "running"
BEING_BUILT = "being built"

# line -> how a page names it; the colours are Maha-Metro's and PMRDA's own names for the lines
LINES: Dict[str, str] = {"1": "Line 1 (Purple Line, PCMC to Swargate)", "2": "Line 2 (Aqua Line, Vanaz to Ramwadi)",
                         "3": "Line 3 (Pink Line, Hinjawadi to Shivajinagar)"}
SHORT: Dict[str, str] = {"1": "Purple Line", "2": "Aqua Line", "3": "Pink Line (Line 3)"}
# where a line's unfinished part is followed on the site (newsroom trackers); a line with none links its source only
TRACKERS: Dict[str, str] = {"3": "/news/track/pune-metro-line-3"}

MAHA_METRO = "Maha-Metro station list (punemetrorail.org)"
LINE_1A = "Maha-Metro, Line 1 A Extension (PCMC to Nigdi, under construction)"
LINE_3 = "Line 3 opened 4 Nov 2026 with 17 stations (Hindustan Times, 3 Nov 2026)"
LINE_3_LATER = "Line 3: one of the 6 stations not open yet (The Times of India, 27 Oct 2026; OpenStreetMap)"


@dataclass(frozen=True)
class Station:
    name: str
    line: str                      # "1", "2" or "3" (LINES)
    status: str                    # RUNNING or BEING_BUILT
    lat: float
    lon: float
    osm: str                       # the OpenStreetMap object the position is from: "node/11699340657"
    source: str                    # where the name and the status are from

    @property
    def line_name(self) -> str:
        return LINES[self.line]

    @property
    def running(self) -> bool:
        return self.status == RUNNING


R, B = RUNNING, BEING_BUILT
STATIONS: Tuple[Station, ...] = (
    # Line 1, north to south
    Station("PCMC", "1", R, 18.629319, 73.803286, "node/10214268972", MAHA_METRO),
    Station("Sant Tukaram Nagar", "1", R, 18.614525, 73.815746, "node/7944597690", MAHA_METRO),
    Station("Nashik Phata (Bhosari)", "1", R, 18.609303, 73.820097, "node/7944597706", MAHA_METRO),
    Station("Kasarwadi", "1", R, 18.599620, 73.827264, "node/7944597699", MAHA_METRO),
    Station("Phugewadi", "1", R, 18.591106, 73.831147, "node/7944584963", MAHA_METRO),
    Station("Dapodi", "1", R, 18.583765, 73.833766, "node/7944584975", MAHA_METRO),
    Station("Bopodi", "1", R, 18.569661, 73.838103, "node/7944597711", MAHA_METRO),
    Station("Khadki", "1", R, 18.562262, 73.842083, "node/13644302877", MAHA_METRO),
    Station("Range Hill", "1", B, 18.550287, 73.845807, "node/7944584969", MAHA_METRO + ": 30 stations, 29 running"),
    Station("Shivaji Nagar", "1", R, 18.532172, 73.849660, "node/11097510271", MAHA_METRO),
    Station("District Court", "1", R, 18.526786, 73.856899, "node/11097510274", MAHA_METRO),
    Station("Kasba Peth", "1", R, 18.521375, 73.859623, "node/12211880200", MAHA_METRO),
    Station("Mahatma Phule Mandai", "1", R, 18.512354, 73.857033, "way/1503654104", MAHA_METRO),
    Station("Swargate", "1", R, 18.499745, 73.857460, "node/7944597710", MAHA_METRO),
    # Line 1's extension north of PCMC
    Station("Chinchwad", "1", B, 18.639173, 73.794931, "node/13647412355", LINE_1A),
    Station("Akurdi", "1", B, 18.651160, 73.784747, "node/13647412354", LINE_1A),
    Station("Nigdi", "1", B, 18.658399, 73.778398, "node/13647412352", LINE_1A),
    Station("Bhakti Shakti", "1", B, 18.662561, 73.774574, "node/13647412351", LINE_1A),
    # Line 2, west to east
    Station("Vanaz", "2", R, 18.507185, 73.805195, "node/9599243853", MAHA_METRO),
    Station("Anand Nagar", "2", R, 18.509572, 73.814075, "node/9599243854", MAHA_METRO),
    Station("Paud Phata", "2", R, 18.508885, 73.822144, "node/9599243855", MAHA_METRO),
    Station("SNDT College", "2", R, 18.507357, 73.828782, "node/9599243856", MAHA_METRO),
    Station("Garware College", "2", R, 18.511989, 73.838050, "node/9599243857", MAHA_METRO),
    Station("Deccan Gymkhana", "2", R, 18.516448, 73.844446, "node/11097527725", MAHA_METRO),
    Station("Chhatrapati Sambhaji Udyan", "2", R, 18.520081, 73.847383, "node/11097527718", MAHA_METRO),
    Station("PMC", "2", R, 18.522744, 73.853350, "node/7944584980", MAHA_METRO),
    Station("District Court", "2", R, 18.526720, 73.857748, "node/7944597685", MAHA_METRO),
    Station("R.T.O. Pune", "2", R, 18.530076, 73.865103, "way/1532296305", MAHA_METRO),
    Station("Pune Railway Station", "2", R, 18.529759, 73.872409, "way/1494691943", MAHA_METRO),
    Station("Ruby Hall Clinic", "2", R, 18.532718, 73.877749, "node/7944584984", MAHA_METRO),
    Station("Bund Garden", "2", R, 18.540593, 73.883439, "node/11699340649", MAHA_METRO),
    Station("Yerawada", "2", R, 18.545303, 73.886621, "node/11699340652", MAHA_METRO),
    Station("Kalyani Nagar", "2", R, 18.544481, 73.905698, "node/11699340655", MAHA_METRO),
    Station("Ramwadi", "2", R, 18.557028, 73.908563, "node/11699340657", MAHA_METRO),
    # Line 3, Hinjawadi (west) to District Court; the names are the opened line's (OpenStreetMap and Wikipedia agree)
    Station("Maan", "3", R, 18.579213, 73.688016, "node/7944584973", LINE_3),
    Station("Maan MIDC Circle Phase 2", "3", R, 18.584019, 73.694818, "node/7944597688", LINE_3),
    Station("Maan Bus Depot", "3", R, 18.588102, 73.702895, "node/7944584965", LINE_3),
    Station("Hinjawadi Phase 2 Circle 2", "3", R, 18.594195, 73.709223, "node/7944584983", LINE_3),
    Station("Hinjawadi Phase 2 Circle 1", "3", R, 18.596590, 73.717161, "node/7944597696", LINE_3),
    Station("Padmabhushan Chowk", "3", R, 18.594487, 73.727826, "node/14334230170", LINE_3),
    Station("Shivaji Chowk, Hinjawadi", "3", R, 18.592395, 73.737357, "node/13647113374", LINE_3),
    Station("Hinjawadi Phase 1", "3", R, 18.590967, 73.746300, "node/13647113373", LINE_3),
    Station("Wakad Chowk", "3", R, 18.590299, 73.757559, "node/7944597702", LINE_3),
    Station("Sports Complex Mahalunge (Balewadi Stadium)", "3", R, 18.579709, 73.761542, "node/7944584964", LINE_3),
    Station("Mitcon Balewadi", "3", R, 18.575034, 73.766062, "node/13647113369", LINE_3),
    Station("R K Laxman Museum Balewadi", "3", R, 18.574343, 73.771849, "node/14334230175", LINE_3),
    Station("Balewadi High Street", "3", B, 18.570512, 73.774838, "node/13647113368", LINE_3_LATER),
    Station("Balewadi Phata", "3", B, 18.564186, 73.779766, "node/13647113367", LINE_3_LATER),
    Station("Baner Gaon", "3", B, 18.559196, 73.790598, "node/13647113366", LINE_3_LATER),
    Station("Baner Pashan Link Road", "3", B, 18.554955, 73.797667, "node/13647113365", LINE_3_LATER),
    Station("Aundh", "3", R, 18.550306, 73.808257, "node/13647113364", LINE_3),
    Station("Sakal Nagar", "3", R, 18.546325, 73.819665, "node/13647113363", LINE_3),
    Station("Savitribai Phule Pune University", "3", R, 18.542347, 73.827173, "node/13647113362", LINE_3),
    Station("Bhosalenagar RBI", "3", B, 18.536371, 73.836692, "node/7944597700", LINE_3_LATER),
    Station("Agriculture College", "3", R, 18.533006, 73.841487, "node/7944597695", LINE_3),
    Station("Shivajinagar", "3", B, 18.530430, 73.848715, "node/7944584959", LINE_3_LATER),
    Station("District Court", "3", R, 18.528395, 73.856012, "node/13570390374", LINE_3),
)
