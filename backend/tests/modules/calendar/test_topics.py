"""The guide topic files (calendar/topics/*.json) as the page reads them: tables whose rows fit their columns, no row repeated
inside a section, and availability tags that match the booked share filed on MahaRERA."""
import re

from app.modules.calendar import topics


def _tables(section):
    return ([section["table"]] if section.get("table") else []) + list(section.get("tables") or [])


def _sections():
    for slug, t in topics.load().items():
        for s in t["sections"]:
            yield slug, s


def _section(slug, sid):
    return next(s for sl, s in _sections() if sl == slug and s["id"] == sid)


def test_every_table_row_has_one_cell_per_column():
    for slug, s in _sections():
        for tb in _tables(s):
            for r in tb["rows"]:
                assert len(r["cells"]) == len(tb["columns"]), (slug, s["id"], r["cells"][0])


def test_no_row_appears_twice_in_a_section():
    for slug, s in _sections():
        rows = [tuple(r["cells"]) for tb in _tables(s) for r in tb["rows"]]
        assert len(rows) == len(set(rows)), (slug, s["id"])


def test_upper_kharadi_prices_split_locality_averages_from_project_figures_with_no_booking_row():
    prices = _section("upper-kharadi", "prices")
    assert [tb["title"]["en"] for tb in prices["tables"]] == ["Locality averages", "Project specifics"]
    assert not any("World of Joy" in r["cells"][0] for tb in prices["tables"] for r in tb["rows"])


def test_availability_tags_follow_the_booked_share():
    tagged = 0
    for slug, s in _sections():
        for tb in _tables(s):
            for r in tb["rows"]:
                if "tag" in r:
                    pct = int(re.search(r"\((\d+)%\)", " ".join(r["cells"])).group(1))
                    assert r["tag"] == ("resale" if pct >= 95 else "open" if pct < 30 else "limited"), (slug, r["cells"][0])
                    tagged += 1
    assert tagged


def test_every_upper_kharadi_project_row_links_our_page_and_carries_a_tag():
    rows = _section("upper-kharadi", "projects")["table"]["rows"]
    assert all(r.get("href", "").startswith("/projects/") and r.get("tag") for r in rows)


def test_upper_kharadi_where_items_each_start_with_a_bold_lead_in():
    assert all(re.match(r"^\*\*[^*]+:\*\* \S", x) for x in _section("upper-kharadi", "where")["items"]["en"])


def test_a_cta_has_its_text_button_and_chat_question_and_mhada_has_none():
    for slug, s in _sections():
        if "cta" in s:
            assert slug != "mhada-pune-lottery"
            assert all(s["cta"][k]["en"].strip() for k in ("text", "button", "message")), slug
    assert "cta" in _section("upper-kharadi", "check")


def test_a_date_value_starts_as_a_sentence():
    for slug, t in topics.load().items():
        for d in t["dates"]:
            v = d["value"]["en"]
            assert v[0].isupper() or v[0].isdigit(), (slug, v)
