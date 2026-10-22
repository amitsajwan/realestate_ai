"""The builder's claims as a listing keeps them (`brochure`, `file_claims`): short and plain, with no phone numbers, hype, sales
promises, the developer's company or the brochure's small print. Moved from propertyfacts.files so that listings.schemas can
clean claims on the way in without importing the app layer. Pure: no I/O."""
import re
from typing import List

from app.platform.guards import problems_in

from . import points

MAX_CLAIMS = 25        # a 4-page brochure: travel times alone fill a dozen
CLAIM_MAX_CHARS = 160
PHONE = re.compile(r"(?:\d[\s-]?){8,}")
SALES_PROBLEMS = ("hype word", "prediction", "promise", "claim not in facts")
INVEST = re.compile(r"\b(investment|returns?|appreciation|profit|earning)\b|गुंतवणूक|गुंतवणुकी|कमाई|परतावा|निवेश|मुनाफ", re.I)
# the developer's company, not this project (the reader is told to leave these out and still copied Lodha's Mumbai corporate
# address from the small print): its offices, portfolio, awards and company-wide figures
COMPANY = re.compile(r"\b(?:corporate|head|registered)\s+(?:office|address)\b|\bportfolio\b|\bawards?\b|\baward[- ]winning\b|"
                     r"\bother\s+projects?\b|\bmillion\s+sq|\bm(?:n|sf)\b|\bsbti\b|\bdjsi\b|science[- ]based\s+targets|"
                     r"dow\s+jones|\byears\s+of\s+(?:legacy|experience|excellence)\b|\bsince\s+(?:19|20)\d\d\b", re.I)
# a city that is not Pune: a claim naming one is about the developer's other work ("landmarks in Mumbai and London"), unless
# it is a road to it ("20 min to the Pune-Mumbai Expressway")
OTHER_CITY = re.compile(r"\b(?:mumbai|thane|london|dubai|bengaluru|bangalore|hyderabad|delhi|gurugram|gurgaon|chennai|"
                        r"kolkata)\b", re.I)
ROAD = re.compile(r"\b(?:expressway|highway|road|rd)\b|pune\s*-\s*\w+|\w+\s*-\s*pune", re.I)
# the small print of a legal page, read as claims once the page is sharp: not something the builder says about the project
DISCLAIMER = re.compile(r"\bindicative\b|\b(?:does|shall)\s+not\s+constitute\b|\bnot\s+an?\s+(?:offer|contract)\b|"
                        r"\breserves?\s+the\s+right\b|\bsubject\s+to\s+change\b|\bequivalent\s+or\s+better\b|\bvariance\b|"
                        r"\bpolyline\b|\bunfinished\s+(?:surfaces|dimensions)\b|\bat\s+an?\s+additional\s+(?:price|cost)\b|"
                        r"\bfinished\s+floor\s+level\b|\bartist'?s\s+impression\b|\bdisclaimer\b", re.I)


def clean_claims(raw) -> List[str]:
    """Short, plain claims only: no phone numbers, no hype (the post checks), no duplicates."""
    out: List[str] = []
    for c in raw or []:
        c = re.sub(r"\s+", " ", str(c or "")).strip().strip('"')
        if not c or len(c) > CLAIM_MAX_CHARS or PHONE.search(c) or INVEST.search(c) or points.PRELAUNCH.search(c):
            continue
        if COMPANY.search(c) or (OTHER_CITY.search(c) and not ROAD.search(c)):   # the developer's, not this project's
            continue
        if DISCLAIMER.search(c):
            continue
        # sales claims ("safe investment", "assured", "high returns") and hype are dropped; the builder's own numbers stay
        # (they are claims by definition, so the number check against our facts does not apply)
        if any(p.startswith(SALES_PROBLEMS) for p in problems_in(c, "")):
            continue
        if c.lower() not in (x.lower() for x in out):
            out.append(c)
        if len(out) >= MAX_CLAIMS:
            break
    return out
