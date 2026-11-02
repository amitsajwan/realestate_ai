"""How many towers a registration has, from MahaRERA's list of buildings (app/modules/agentprojects/maharera.py)."""
from app.modules.agentprojects.maharera import building_totals


def row(name="Prestigia", wing=None, floors=9, units=10):
    return {"name": name, "wing": wing, "floors": floors, "units_total": units}


def test_every_wing_filed_under_the_projects_name_counts_as_a_tower():
    rows = [row(wing=w, floors=f) for w, f in (("A", 3), ("B", 9), ("C", 3))]
    assert building_totals(rows)["towers"] == 3


def test_rows_with_no_wing_and_different_sizes_are_different_towers():
    assert building_totals([row(floors=13), row(floors=9)])["towers"] == 2


def test_an_identical_row_counts_once_and_no_rows_say_nothing():
    assert building_totals([row(wing="A"), row(wing="A")])["towers"] == 1
    assert building_totals([])["towers"] is None
