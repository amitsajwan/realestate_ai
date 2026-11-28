"""The official school lists the schools researcher reads (owner 2026-11-28: the boards' own lists only, never fees or ratings).
Plain fetch and parse, so each can be checked against a saved page (tests/modules/neighbourhood/fixtures).

CBSE, SARAS (saras.cbse.gov.in, the board's affiliation system; checked 2026-11-28 from this PC and the VM):
- GET  /saras/AffiliatedList/ListOfSchdirReport gives the search form with its anti-forgery token (and a cookie);
- POST the same address with MainRadioValue=State_wise, State=11 (Maharashtra), District=23 (Pune; from
  /saras/AffiliatedList/Dist_Bind?state_id=11) returns every affiliated school of Pune district in one HTML table (357 on
  2026-11-28): affiliation number, school code, status ("Senior Secondary Level", "Secondary Level", "Middle Class"), name,
  head's name (never kept), postal address and website. Only 47 of the 357 addresses carry a pincode, so
- GET /saras/AffiliatedList/AfflicationDetails/<affiliation> is read once per school for its pincode (and school type,
  foundation year, affiliation period, of which we keep the type).
saras.cbse.gov.in sends its certificate without the intermediate (Sectigo Public Server Authentication CA DV R36): browsers
fetch it, Python cannot, so it is bundled (data/schools_sectigo_dv_r36.pem, valid to 2036) as MahaRERA's is.

CISCE (ICSE, ISC), locate.cisce.org (the council's school locator, linked from cisce.org):
- GET / gives a Laravel `_token`; GET /result?_token=..&country=India&state=Maharashtra&page=N lists Maharashtra's schools ten
  a page (about 30 pages), each card with the school code ("MA001"), name, head's name (never kept), address ("..., Pune,
  Maharashtra, 411 001, India": the district is the second last part before the state), the ICSE / ISC badges and the school's
  website; the page's map script carries each school's own position (`const locations = {"schools": [{lat, lng, name}]}`).
  Its robots.txt allows every bot not named (AvasetuBot is not). It sits behind Cloudflare, which refused Python's own client
  from this PC on 2026-11-28 while curl was answered: when it refuses, the CISCE list is noted as not read and CBSE goes on.
Not used: IB (ibo.org find-a-school answered 403 to any reader), the State Board (UDISE+ needs a captcha), Cambridge (no public
list by city).
"""
import html
import json
import logging
import re
import ssl
from pathlib import Path
from typing import List, Optional, Tuple

import certifi
import httpx

log = logging.getLogger(__name__)

UA = "Mozilla/5.0 (compatible; AvasetuBot/1.0; +https://avasetu.in)"
# locate.cisce.org's Cloudflare turns away a bare bot name; a browser's words with ours after them are answered, and say who we are
CISCE_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36 "
            "AvasetuBot/1.0 (+https://avasetu.in)")
SARAS = "https://saras.cbse.gov.in/saras/AffiliatedList/ListOfSchdirReport"
SARAS_DETAILS = "https://saras.cbse.gov.in/saras/AffiliatedList/AfflicationDetails/{aff}"
SARAS_STATE, SARAS_DISTRICT = "11", "23"          # Maharashtra, Pune (Dist_Bind, 2026-11-28)
CISCE = "https://locate.cisce.org/"
CISCE_RESULT = "https://locate.cisce.org/result"
CISCE_MAX_PAGES = 60
CERT = Path(__file__).with_name("data") / "schools_sectigo_dv_r36.pem"
PINCODE = re.compile(r"\b4\s?1\s?\d\s?\d\s?\d\s?\d\b")      # Pune district pincodes are 41xxxx ("411 001" on CISCE)

LEVELS = {"senior secondary level": "Up to Class 12", "secondary level": "Up to Class 10", "middle class": "Up to Class 8"}


def cbse_tls() -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=certifi.where())
    if CERT.exists():
        ctx.load_verify_locations(cafile=str(CERT))
    return ctx


def cbse_client(timeout: float = 60.0) -> httpx.AsyncClient:
    """The client SARAS is read with (its missing intermediate added). Tests replace this function."""
    return httpx.AsyncClient(timeout=timeout, verify=cbse_tls(), follow_redirects=True,
                             headers={"User-Agent": UA, "Accept": "text/html", "Accept-Language": "en-IN,en"})


def _text(fragment: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", fragment or "", flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"[ \t\r\f\v]+", " ", html.unescape(t)).strip()


def pincode_in(text: str) -> str:
    found = PINCODE.findall(text or "")
    return re.sub(r"\s", "", found[-1]) if found else ""


def website(v: str) -> str:
    """A school's website as a link, or "" (the lists hold "NA", "www.x.in", "http://x.in/")."""
    v = (v or "").strip().strip(",;")
    if not v or v.lower() in ("na", "n/a", "nil", "none", "-", "0") or " " in v or "." not in v or "@" in v:
        return ""
    return v if re.match(r"(?i)https?://", v) else "http://" + v


# --- CBSE -------------------------------------------------------------------------------------------------------------------

def saras_token(page: str) -> str:
    m = re.search(r'name="__RequestVerificationToken" type="hidden" value="([^"]+)"', page or "")
    return m.group(1) if m else ""


def parse_saras_list(page: str) -> List[dict]:
    """The rows of SARAS's district list: [{affiliation, school_code, name, level, address, pincode, website}]. Heads' names
    are on the page and are never read into a row."""
    out: List[dict] = []
    body = page.split('id="myTable"', 1)[-1] if page else ""
    for row in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) < 6:
            continue
        ids, status, who, where = _text(cells[1]), _text(cells[3]), _text(cells[4]), _text(cells[5])
        aff = re.search(r"Aff\. No\. :\s*(\d+)", ids)
        if not aff:
            continue
        code = re.search(r"Sch\. Code:\s*(\d+)", ids)
        name = re.search(r"Name :\s*(.*?)\s*(?:\n|Head/Principal Name:|$)", who, re.S)
        addr = re.search(r"Address :\s*(.*?)\s*(?:\n\s*Website :|Website :|$)", where, re.S)
        site = re.search(r"Website :\s*(\S+)", where)
        address = " ".join((addr.group(1) if addr else "").split())
        out.append({"affiliation": aff.group(1), "school_code": code.group(1) if code else "",
                    "name": " ".join((name.group(1) if name else "").split()).strip(" ,"),
                    "level": LEVELS.get(status.strip().lower(), ""), "address": address, "pincode": pincode_in(address),
                    "website": website(site.group(1) if site else "")})
    return [r for r in out if r["name"]]


def parse_saras_details(page: str) -> dict:
    """{pincode, school_type} from a school's SARAS details page ("Pin Code | 412207", "School Type | INDEPENDENT")."""
    t = _text(re.sub(r"<script.*?</script>|<style.*?</style>", "", page or "", flags=re.S))
    pin = re.search(r"Pin Code\s+(\d[\d ]{5,7})", t)
    kind = re.search(r"School Type\s+([A-Z][A-Z .()/-]{2,40}?)\s+(?:Type of affiliation|Affiliation Period|$)", t)
    return {"pincode": re.sub(r"\s", "", pin.group(1))[:6] if pin else "", "school_type": kind.group(1).strip() if kind else ""}


async def read_cbse(client: httpx.AsyncClient) -> List[dict]:
    """Every CBSE school of Pune district from SARAS. Raises when SARAS does not answer or answers with no table."""
    form = await client.get(SARAS)
    form.raise_for_status()
    token = saras_token(form.text)
    if not token:
        raise RuntimeError("SARAS form had no token")
    r = await client.post(SARAS, data={"MainRadioValue": "State_wise", "State": SARAS_STATE, "District": SARAS_DISTRICT,
                                       "Region": "", "InstName_orAddress": "", "RegiAffNo": "0", "SchoolStatusWise": "0",
                                       "__RequestVerificationToken": token}, headers={"Referer": SARAS})
    r.raise_for_status()
    rows = parse_saras_list(r.text)
    if not rows:
        raise RuntimeError("SARAS answered with no schools")
    return rows


async def read_cbse_details(client: httpx.AsyncClient, affiliation: str) -> Optional[dict]:
    try:
        r = await client.get(SARAS_DETAILS.format(aff=affiliation))
    except httpx.HTTPError as e:
        log.info("schools: SARAS details %s not read (%s)", affiliation, type(e).__name__)
        return None
    if r.status_code != 200:
        return None
    got = parse_saras_details(r.text)
    return got if got["pincode"] or got["school_type"] else None


# --- CISCE ------------------------------------------------------------------------------------------------------------------

def cisce_token(page: str) -> str:
    m = re.search(r'name="_token" value="([^"]+)"', page or "")
    return m.group(1) if m else ""


def cisce_positions(page: str) -> dict:
    """{card name: (lat, lon)} from the result page's map script."""
    m = re.search(r"const locations = (\{.*?\});", page or "", re.S)
    if not m:
        return {}
    try:
        got = json.loads(m.group(1)).get("schools") or []
    except ValueError:
        return {}
    out = {}
    for s in got:
        if isinstance(s.get("lat"), (int, float)) and isinstance(s.get("lng"), (int, float)) and s.get("name"):
            out[" ".join(str(s["name"]).split())] = (float(s["lat"]), float(s["lng"]))
    return out


def parse_cisce_page(page: str) -> Tuple[List[dict], bool]:
    """(the schools on one result page, whether there is a next page). Each: {affiliation (the council's school code), name,
    address, district, pincode, website, icse, isc, lat, lon}; the head's name on the card is never read into a row."""
    pos = cisce_positions(page)
    out: List[dict] = []
    for card in re.split(r'<div class="school-card">', page or "")[1:]:
        title = re.search(r"<h6[^>]*>(.*?)</h6>", card, re.S)
        if not title:
            continue
        heading = " ".join(_text(title.group(1)).split())
        m = re.match(r"([A-Z]{2}\d{2,5})\s*-\s*(.+)", heading)
        if not m:
            continue
        para = re.search(r'<p class="mb-1">(.*?)</p>', card, re.S)
        lines = [ln.strip() for ln in _text(para.group(1) if para else "").split("\n") if ln.strip()]
        address = " ".join(" ".join(lines[1:]).split())   # the first line is the head's name, never kept
        parts = [p.strip() for p in address.split(",")]
        # "..., Pune, Maharashtra, 411 001, India": the district stands before the state
        district = ""
        for i, p in enumerate(parts):
            if p.lower() == "maharashtra" and i > 0:
                district = parts[i - 1]
        badges = [b.strip().upper() for b in re.findall(r'badge-outline-green[^"]*">\s*([^<]+?)\s*<', card)]
        link = re.search(r'<a href="([^"]+)"[^>]*visit-btn', card)
        lat, lon = pos.get(heading, (None, None))
        out.append({"affiliation": m.group(1), "name": m.group(2).strip(), "address": address, "district": district,
                    "pincode": pincode_in(address), "website": website(link.group(1) if link else ""),
                    "icse": "ICSE" in badges, "isc": "ISC" in badges, "lat": lat, "lon": lon})
    return out, bool(_next_pages(page))


def _next_pages(page: str) -> set:
    return {int(n) for n in re.findall(r"[?&](?:amp;)?page=(\d+)", page or "")}


async def read_cisce(client: httpx.AsyncClient, sleep=None, district: str = "Pune") -> List[dict]:
    """Every CISCE school of Pune district from the council's locator, page by page. Raises when the locator refuses (Cloudflare)
    or shows no school at all."""
    headers = {"User-Agent": CISCE_UA, "Accept": "text/html", "Accept-Language": "en-IN,en"}
    first = await client.get(CISCE, headers=headers)
    first.raise_for_status()
    token = cisce_token(first.text)
    if not token:
        raise RuntimeError("CISCE locator had no token (a challenge page?)")
    rows: List[dict] = []
    page_no, last = 1, 1
    while page_no <= min(last, CISCE_MAX_PAGES):
        r = await client.get(CISCE_RESULT, headers=headers,
                             params={"_token": token, "country": "India", "state": "Maharashtra", "page": page_no})
        r.raise_for_status()
        got, _ = parse_cisce_page(r.text)
        if not got:
            break
        rows += got
        last = max([last, *_next_pages(r.text)])
        page_no += 1
        if sleep and page_no <= last:
            await sleep()
    if not rows:
        raise RuntimeError("CISCE locator listed no schools")
    want = district.lower()
    return [r for r in rows if r["district"].lower() == want]
