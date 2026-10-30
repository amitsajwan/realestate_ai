"""The finder link a chat reply carries (whatsapp/finder_link.py): the site's own address for what the buyer told us."""
from app.modules.whatsapp.finder_link import finder_line, finder_query

SITE = "https://avasetu.in"


def test_2_bhk_in_wagholi_under_a_crore_becomes_the_sites_finder_address():
    line = finder_line({"bhk": 2.0, "locality": "Wagholi", "budget_max": 9_500_000}, SITE)
    assert line == ("All 2 BHK in Wagholi under ₹1 Cr, with prices and MahaRERA checks: "
                    "https://avasetu.in/projects?area=wagholi&budget=75l-1cr&bhk=2&src=whatsapp#find")


def test_it_speaks_their_language_and_keeps_the_link():
    line = finder_line({"bhk": 3.0, "locality": "Upper Kharadi"}, SITE, "hinglish")
    assert line.startswith("Saare 3 BHK in Upper Kharadi") and line.endswith("/projects?area=upper-kharadi&bhk=3&src=whatsapp#find")


def test_nothing_known_renting_or_an_area_we_do_not_cover_gives_no_area():
    assert finder_line({}, SITE) is None
    assert finder_line({"bhk": 2.0, "tx": "rent"}, SITE) is None
    assert finder_query({"locality": "Nashik"}) is None
    assert finder_query({"locality": "Nashik", "bhk": 5.0}) == {"bhk": "4", "words": "4+ BHK"}
    assert finder_query({"budget_max": 40_000_000}) == {"budget": "above-2.5cr", "words": "new projects above ₹2.5 Cr"}
