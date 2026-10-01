"""Curated, stable facts about the three areas we cover. Source of truth for what replies may say about an area.

Rules (same as the site pages): no prices, no predictions, no invented distances or school names. Every statement here restates
something already published on our own pages, frontend/lib/marketing/localities.ts and insights.ts, which cite official sources
(PIB press releases for Pune Metro Phase-2, Corridor 2B and Line 4; MahaRERA). A test (tests/modules/knowledge/test_areas.py) parses
those two files and fails if this file says anything they do not (numbers, metro wording, price words).
Anything we cannot source is left out on purpose: the reply then says honestly that it does not have it (schools, hospitals, malls
and exact distances are NOT listed for any area).
Facts starting with 'Check:' are advice on what to ask or look at on a visit, not statements about the area.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

AREA_ALIASES = {"kharadi": "kharadi", "upper kharadi": "upper_kharadi", "upper-kharadi": "upper_kharadi", "upper_kharadi": "upper_kharadi",
                "wagholi": "wagholi"}


@dataclass(frozen=True)
class AreaFacts:
    key: str                              # kharadi | upper_kharadi | wagholi
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
}


def normalise(locality: Optional[str]) -> Optional[str]:
    """'Upper Kharadi' / 'upper-kharadi' -> 'upper_kharadi'; None for an area we do not cover."""
    return AREA_ALIASES.get(" ".join((locality or "").strip().lower().split()))


def area_facts(locality: Optional[str]) -> Optional[AreaFacts]:
    key = normalise(locality)
    return AREAS.get(key) if key else None
