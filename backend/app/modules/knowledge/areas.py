"""Curated, stable facts about the areas we cover (the list in app/core/areas.py). Source of truth for what replies may say about an area.

Rules (same as the site pages): no prices, no predictions, no invented distances or school names. Every statement here restates
something already published on our own pages, frontend/lib/marketing/localities.ts and insights.ts, which cite official sources
(PIB press releases for Pune Metro Phase-2, Corridor 2B and Line 4; PMRDA pages and press notes for Metro Line 3; the Airports
Authority of India for Pune airport at Lohegaon; PCMC town planning for Wakad; MahaRERA). A test (tests/modules/knowledge/test_areas.py) parses
those two files and fails if this file says anything they do not (numbers, metro wording, price words).
Anything we cannot source is left out on purpose: the reply then says honestly that it does not have it (schools, hospitals, malls
and exact distances are NOT listed for any area).
Facts starting with 'Check:' are advice on what to ask or look at on a visit, not statements about the area.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from app.core import areas as _registry

# every spelling app/core/areas.py knows (key, slug, display name, aliases) -> area key
AREA_ALIASES: Dict[str, str] = {
    " ".join(spelling.lower().split()): a.key
    for a in _registry.AREAS for spelling in (a.key, a.slug, a.name, *a.aliases)
}


@dataclass(frozen=True)
class AreaFacts:
    key: str                              # an area key from app/core/areas.py
    name: str
    slug: str                             # site path slug: /localities/<slug>
    facts: Tuple[str, ...]                # plain sentences
    faq: Tuple[Tuple[str, str], ...]      # (question, answer)
    sources: Tuple[str, ...] = ()

    @property
    def page(self) -> str:
        return f"/localities/{self.slug}"


_CHECK_COMMUTE = "Check: try the commute yourself at 9:00 am and 6:30 pm on a weekday before you decide."
_CHECK_RERA = "Check: look up the project's RERA number and its possession date on the MahaRERA website and compare with the agreement."
_CHECK_COST = "Check: ask for the full cost sheet (stamp duty, registration, GST where applicable, parking and maintenance deposit) and compare on carpet area."
_CHECK_UTIL = "Check: ask where the water comes from (municipal supply, tanker or borewell), how much storage the building has, and what the power backup covers."
_METRO_NOTE = "Check the current status on the official Maha-Metro website."
_CHECK_RERA_EACH = "Check: look up each project on the MahaRERA website before you book, and visit a finished project by the same builder."
# Pune Metro Line 3 (PMRDA): one wording everywhere, as on the locality pages
_L3_STATUS = ("In September 2026 PMRDA said the Commissioner of Metro Railway Safety had approved the 13.20 km Maan to Balewadi section of "
              "Line 3, but approved is not the same as running.")
_BROCHURE = ("Check: if a brochure mentions a new metro line or road, ask which official approval it refers to; approved is not the same "
             "as running.")

AREAS: Dict[str, AreaFacts] = {
    "kharadi": AreaFacts(
        "kharadi", "Kharadi", "kharadi",
        ("Kharadi is one of east Pune's main office areas, home to large campuses such as EON IT Park and World Trade Center Pune.",
         "It is an established neighbourhood, so it is usually the busiest and most expensive of the three areas on this corridor (Kharadi, Upper Kharadi and Wagholi).",
         "Living here can mean a short trip to work for people employed at the nearby campuses.",
         "Roads around the office campuses are busy at rush hour.",
         "Metro Line 4 (Kharadi to Khadakwasla) has been approved by the Union Cabinet, but approved is not the same as running.",
         _METRO_NOTE, _CHECK_COMMUTE, _CHECK_RERA, _CHECK_COST, _CHECK_UTIL),
        (("Is the metro running in Kharadi?", "Not yet. Line 4 (Kharadi to Khadakwasla) is approved, which is different from running. Check the latest status on the official Maha-Metro website."),
         ("Should I buy ready-to-move or under construction?", "Ready-to-move lets you see exactly what you buy. Under construction can cost less to enter but you wait and rely on the builder keeping the date, so check the RERA possession date and visit a finished project by the same builder.")),
        ("PIB: Pune Metro Phase-2, Line 4 (Kharadi to Khadakwasla)", "MahaRERA (official portal)", "site pages /localities/kharadi and /insights/kharadi-upper-kharadi-wagholi")),
    "upper_kharadi": AreaFacts(
        "upper_kharadi", "Upper Kharadi", "upper-kharadi",
        ("Upper Kharadi sits on the same eastern corridor as Kharadi and Wagholi.",
         "Many projects here are newer or still being built, so the builder and the accuracy of the possession date matter.",
         "It tends to have newer projects and more open space than Kharadi, and the Kharadi offices are a short drive away.",
         "Two metro projects have been approved for this corridor, Line 4 from Kharadi and Corridor 2B towards Wagholi, but approved is not the same as running.",
         _METRO_NOTE,
         "Check: test the road access at rush hour, not on a Sunday, because the approaches to the main roads decide your daily commute.",
         _CHECK_RERA, _CHECK_COST, _CHECK_UTIL),
        (("What is the difference between Kharadi and Upper Kharadi?", "Kharadi is closest to the office campuses and more established; Upper Kharadi tends to have newer projects and more open space. Visit both at rush hour before you choose."),
         ("How do I check an under-construction project?", "Look up its RERA registration and stated possession date on MahaRERA, ask for the approved plan, and visit a finished project by the same builder.")),
        ("PIB: Pune Metro Phase-2, Line 4 and Corridor 2B", "MahaRERA (official portal)", "site pages /localities/upper-kharadi and /insights/kharadi-upper-kharadi-wagholi")),
    "wagholi": AreaFacts(
        "wagholi", "Wagholi", "wagholi",
        ("Wagholi is further out on the eastern corridor than Kharadi and Upper Kharadi.",
         "Buyers often find more space for their budget and many newer towers here, in exchange for a longer commute that depends on the road and the time of day.",
         "Corridor 2B of Pune Metro Phase-2 (Ramwadi to Wagholi/Vitthalwadi, about 11.6 km with 11 stations) has been approved by the Union Cabinet, but approved is not the same as running.",
         _METRO_NOTE, _CHECK_COMMUTE, _CHECK_RERA, _CHECK_COST, _CHECK_UTIL),
        (("Is there a metro to Wagholi?", "Corridor 2B (Ramwadi to Wagholi/Vitthalwadi) is approved. It is not running yet, so do not pay extra for it today and check the latest status with Maha-Metro."),
         ("How far is Wagholi from the Kharadi offices?", "It depends on the route and the time. We do not quote times here: try the trip yourself at rush hour before you decide.")),
        ("PIB: Pune Metro Phase-2, Corridor 2B (Ramwadi to Wagholi/Vitthalwadi)", "MahaRERA (official portal)", "site pages /localities/wagholi and /insights/metro-kharadi-wagholi-approved-not-running")),
    "lohegaon": AreaFacts(
        "lohegaon", "Lohegaon", "lohegaon",
        ("Lohegaon, in north-east Pune, is where Pune airport is.",
         "The Airports Authority of India runs the civil terminal as a civil enclave, and air traffic control is with the Indian Air Force.",
         "Many buyers here are looking for a first home, so the builder, the possession date and the full cost matter more than the brochure.",
         _CHECK_COMMUTE, _BROCHURE,
         "Check: visit the flat in the morning, the evening and once at night to judge aircraft noise for yourself.",
         "Check: ask whether the project needed a height clearance because of the airport, and ask for a copy.",
         _CHECK_RERA, _CHECK_COST, _CHECK_UTIL),
        (("Is Pune airport in Lohegaon?", "Yes. The Airports Authority of India lists its civil enclave as Pune Airport, Lohegaon. Air traffic control there is with the Indian Air Force."),
         ("How do I check an under-construction project?", "Look up its RERA registration and stated possession date on MahaRERA, ask for the approved plan, and visit a finished project by the same builder.")),
        ("Airports Authority of India: Pune Airport, Lohegaon", "MahaRERA (official portal)", "site page /localities/lohegaon")),
    "keshav_nagar": AreaFacts(
        "keshav_nagar", "Keshav Nagar", "keshav-nagar",
        ("Keshav Nagar is a residential area in east Pune, in the Mundhwa area.",
         "We have not yet found official sources about its roads and transport that we can cite.",
         _CHECK_COMMUTE, _BROCHURE, _CHECK_RERA_EACH, _CHECK_RERA, _CHECK_COST, _CHECK_UTIL),
        (("Is Keshav Nagar the same as Mundhwa?", "Keshav Nagar is in the Mundhwa area, and the two names are often used together in addresses. Check the exact address and survey number in the agreement and on the MahaRERA page of the project."),
         ("How far is Keshav Nagar from the Kharadi offices?", "It depends on the route and the time. We do not quote times here: try the trip yourself at rush hour before you decide.")),
        ("MahaRERA (official portal)", "site page /localities/keshav-nagar")),
    "hinjawadi": AreaFacts(
        "hinjawadi", "Hinjawadi", "hinjawadi",
        ("Hinjawadi, on Pune's western edge, is home to the Rajiv Gandhi IT Park.",
         "Living here can mean a short trip to work for people employed in the Rajiv Gandhi IT Park.",
         "PMRDA is building Pune Metro Line 3 (Maan-Hinjawadi to Shivajinagar), an elevated line of about 23.2 km with 23 stations, as a public-private partnership; check the current status on the PMRDA website.",
         _L3_STATUS,
         "PMRDA itself names traffic congestion in the Maan-Hinjawadi area as the reason to finish Line 3.",
         "Before the 2026 monsoon, PMRDA, MIDC and the local gram panchayats inspected the Hinjawadi IT Park to clear choke points and prevent waterlogging.",
         _CHECK_COMMUTE,
         "Check: drive the approach roads after heavy rain before you book.",
         _CHECK_RERA, _CHECK_COST, _CHECK_UTIL),
        (("Is the metro running in Hinjawadi?", "Check the current status on the PMRDA website. In September 2026 PMRDA said the Maan to Balewadi section of Line 3 had its safety approval; approved is not the same as running, so do not pay extra for a station until trains are carrying passengers."),
         ("How far is Hinjawadi from the rest of Pune?", "It depends on the route and the time. We do not quote times here: try the trip yourself at rush hour before you decide.")),
        ("PMRDA: Pune Metro Line 3", "PMRDA press notes, June and September 2026", "MahaRERA (official portal)", "site page /localities/hinjawadi")),
    "wakad": AreaFacts(
        "wakad", "Wakad", "wakad",
        ("Wakad lies between Hinjawadi and Balewadi and comes under the Pimpri Chinchwad Municipal Corporation (PCMC).",
         "On PMRDA's route map, Pune Metro Line 3 has a station at Wakad Chowk, between the Hinjawadi stations and Balewadi; check the current status on the PMRDA website.",
         _L3_STATUS, _CHECK_COMMUTE,
         "Check: look up the plot on PCMC's development plan maps for planned roads and reservations next to the building.",
         _CHECK_RERA, _CHECK_COST, _CHECK_UTIL),
        (("Is there a metro station in Wakad?", "PMRDA's route map for Line 3 shows a station at Wakad Chowk. In September 2026 PMRDA said the Maan to Balewadi section had its safety approval; approved is not the same as running, so check the current status on the PMRDA website."),
         ("Which civic body looks after Wakad?", "Wakad comes under the Pimpri Chinchwad Municipal Corporation (PCMC). Its town planning page has the development plan maps for Wakad.")),
        ("PMRDA: Pune Metro Line 3 route map", "PCMC town planning", "MahaRERA (official portal)", "site page /localities/wakad")),
    "baner": AreaFacts(
        "baner", "Baner", "baner",
        ("Baner is in west Pune, on the route of Pune Metro Line 3 from Maan-Hinjawadi to Shivajinagar, which has stations named Baner Gaon and Baner on PMRDA's route map; check the current status on the PMRDA website.",
         "The safety approval PMRDA announced in September 2026 was for the Maan to Balewadi section of Line 3, and approved is not the same as running.",
         "The Baner ramp of PMRDA's double-decker flyover at Pune University opened to traffic on 8 March 2026.",
         _CHECK_COMMUTE, _CHECK_RERA, _CHECK_COST, _CHECK_UTIL),
        (("Is the metro running in Baner?", "The safety approval PMRDA announced in September 2026 was for the Maan to Balewadi section of Line 3; approved is not the same as running. Check the current status of the Baner stations on the PMRDA website."),
         ("How far is Baner from the Hinjawadi IT park?", "It depends on the route and the time. We do not quote times here: try the trip yourself at rush hour before you decide.")),
        ("PMRDA: Pune Metro Line 3", "PMRDA press note, September 2026", "MahaRERA (official portal)", "site page /localities/baner")),
}


def normalise(locality: Optional[str]) -> Optional[str]:
    """'Upper Kharadi' / 'upper-kharadi' -> 'upper_kharadi'; None for an area we do not cover."""
    return AREA_ALIASES.get(" ".join((locality or "").strip().lower().split()))


def area_facts(locality: Optional[str]) -> Optional[AreaFacts]:
    key = normalise(locality)
    return AREAS.get(key) if key else None
