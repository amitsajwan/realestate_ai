"""The guide topic files (calendar/topics/*.json) as the page reads them: tables that line up, rows that are not repeated, and
availability tags that match the booked share filed on MahaRERA."""
import re

from app.modules.calendar import topics


def _tables(section):
    return ([section["table"]] if section.get("table") else []) + list(section.get("tables") or [])


def _sections():
    for slug, t in topics.load().items():
        for s in t["sections"]:
            yield slug, s


def test_every_table_row_has_one_cell_per_column():
    for slug, s in _sections():
        for tb in _tables(s):
            for r in tb["rows"]:
                assert len(r["cells"]) == len(tb["columns"]), (slug, s["id"], r["cells"][0])


def test_no_row_appears_twice_in_a_section():
    for slug, s in _sections():
        rows = [tuple(r["cells"]) for tb in _tables(s) for r in tb["rows"]]
        assert len(rows) == len(set(rows)), (slug, s["id"])


def test_a_project_row_from_another_table_does_not_leak_into_the_prices():
    prices = next(s for slug, s in _sections() if slug == "upper-kharadi" and s["id"] == "prices")
    assert [tb["title"]["en"] for tb in prices["tables"]] == ["Locality averages", "Project specifics"]
    assert not any("World of Joy" in r["cells"][0] for tb in prices["tables"] for r in tb["rows"])


def test_availability_tags_follow_the_booked_share():
    tagged = 0
    for slug, s in _sections():
        for tb in _tables(s):
            for r in tb["rows"]:
                if "tag" not in r:
                    continue
                pct = int(re.search(r"\((\d+)%\)", " ".join(r["cells"])).group(1))
                assert r["tag"] == ("resale" if pct >= 95 else "open" if pct < 30 else "limited"), (slug, r["cells"][0])
                tagged += 1
    assert tagged


def test_every_upper_kharadi_project_row_links_to_our_project_page():
    projects = next(s for slug, s in _sections() if slug == "upper-kharadi" and s["id"] == "projects")
    assert all(r.get("href", "").startswith("/projects/") and r.get("tag") for r in projects["table"]["rows"])


def test_the_upper_kharadi_where_section_bolds_each_lead_in():
    where = next(s for slug, s in _sections() if slug == "upper-kharadi" and s["id"] == "where")
    assert all(re.match(r"^\*\*[^*]+:\*\* \S", x) for x in where["items"]["en"])


def test_a_cta_has_text_a_button_and_the_chat_message():
    for slug, s in _sections():
        if "cta" in s:
            assert all(s["cta"][k]["en"].strip() for k in ("text", "button", "message")), slug


def test_a_date_value_starts_like_a_sentence():
    for slug, t in topics.load().items():
        for d in t["dates"]:
            v = d["value"]["en"]
            assert v[0].isupper() or v[0].isdigit(), (slug, v)
