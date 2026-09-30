"""The check stage must reject every adversarial draft and pass a clean one (docs/NEWSROOM_PLAN.md sections 1 and 4)."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.newsroom.stages.check import check
from app.modules.newsroom.types import Draft, Fact, Facts, RawItem

NOW = datetime(2026, 9, 20, tzinfo=timezone.utc)
PUB = datetime(2026, 9, 12, tzinfo=timezone.utc)
URL = "https://example.com/metro-line-3"
SRC_TEXT = (
    "PMRDA said on 12 September that trial runs on Pune Metro Line 3 will begin next month. "
    "The project cost is Rs 8,313 crore and work is 85 percent complete. "
    "The stretch is approved but has not opened to passengers. "
    "A builder, Sunrise Developers, has registered a project near Kharadi with possession in December 2028. "
    "The authority will hold a public hearing on Kharadi road widening at Yerwada office."
)
ITEM = RawItem("i1", "metro_times", URL, "Metro Line 3 trial run plan announced", SRC_TEXT, PUB, PUB)
FACTS = Facts([Fact("Trial runs on Metro Line 3 start next month.", "trial runs on Pune Metro Line 3 will begin next month")], PUB)

CLEAN = (
    "PMRDA has said trial runs on Pune Metro Line 3 will begin next month, and work is 85 percent complete.\n\n"
    "Our view: This may matter if you are looking at Kharadi, but the line is approved and is not open to passengers yet.\n\n"
    "What to check: Check the latest status in the official notice.\n\n"
    f"Source: Metro Times, as of 12 Sep 2026. {URL}\n\n"
    "Does a planned metro change how you pick a home? Tell us in the comments.\n\n#Pune #PunePropertyHub #Kharadi"
)


def run(text=CLEAN, item=ITEM, facts=FACTS, **kw):
    d = Draft(**{"format": "post", "text": text, "link": URL, "source_names": ["Metro Times"], **kw})
    return check(d, facts, item, now=NOW)


def bad(res, needle):
    assert not res.ok, "draft should have been rejected"
    assert any(needle.lower() in p.lower() for p in res.problems), res.problems


def add(extra):  # slip one extra sentence into the clean draft
    return CLEAN.replace("Our view:", extra + " Our view:")


def test_clean_draft_passes():
    r = run()
    assert r.ok, r.problems


def test_invented_number():
    bad(run(CLEAN.replace("85 percent", "92 percent")), "92")


def test_invented_number_hidden_in_extra_sentence():
    bad(run(add("About 40,000 commuters will benefit.")), "40000")


def test_wrong_unit_on_real_number():
    bad(run(CLEAN.replace("85 percent", "85 crore")), "unit")


def test_changed_date():
    bad(run(CLEAN.replace("as of 12 Sep 2026", "as of 15 Sep 2026")), "date")


def test_changed_date_in_body():
    bad(run(CLEAN.replace("next month", "on 21 October")), "21")


def test_changed_year():
    bad(run(add("Possession in 2027.")), "2027")


def test_invented_place():
    bad(run(CLEAN.replace("Kharadi, but", "Hinjewadi, but")), "Hinjewadi")


def test_invented_name_at_sentence_start():
    bad(run(add("Hinjewadi sees more.")), "Hinjewadi")


def test_invented_acronym():
    bad(run(CLEAN.replace("PMRDA has", "MMRDA has")), "MMRDA")


def test_price_prediction_as_fact():
    bad(run(add("Prices in Kharadi are set to jump after this.")), "prediction")


def test_price_will_rise_banned():
    bad(run(add("Property rates will go up soon.")), "banned")


def test_expected_to_rise():
    bad(run(add("Rents are expected to rise near the line.")), "prediction")


def test_hedged_view_without_price_claim_is_fine():
    assert run(CLEAN.replace("may matter", "could be worth knowing about")).ok


def test_hype():
    bad(run(add("This is the perfect time.")), "hype")


def test_guarantee_is_banned():
    bad(run(add("Returns are guaranteed.")), "banned")


def test_phone_number():
    bad(run(CLEAN + "\nCall 9876543210"), "phone")


def test_copied_paragraph():
    copied = ("The project cost is Rs 8,313 crore and work is 85 percent complete. The stretch is approved but has not opened to "
              "passengers. A builder, Sunrise Developers, has registered a project near Kharadi with possession in December 2028.")
    bad(run(copied + "\n\nDoes this help? Tell us.\n\nSource: Metro Times, as of 12 Sep 2026 " + URL), "copies")


def test_copied_headline():
    bad(run(add("Metro Line 3 trial run plan announced.")), "headline")


def test_short_quote_is_allowed():
    assert run(add('PMRDA said "trial runs on Pune Metro Line 3 will begin next month".')).ok


def test_missing_link():
    bad(run(CLEAN.replace(URL, "").strip(), link=None), "link")


def test_link_in_text_is_enough():
    assert run(link=None).ok


def test_missing_source_name():
    bad(run(source_names=[]), "source name")


def test_builder_praise():
    bad(run(add("Sunrise Developers is a reliable builder.")), "builder")


def test_builder_criticism():
    bad(run(add("Avoid this builder.")), "builder")


def test_metro_opens_claim_not_in_source():
    bad(run(add("The metro line opens soon.")), "transport")


def test_metro_running_claim_when_source_only_approved():
    src = replace(ITEM, text="PMRDA approved Pune Metro Line 3 for Kharadi on 12 September. Work is 85 percent complete.")
    text = CLEAN.replace("trial runs on Pune Metro Line 3 will begin next month", "Pune Metro Line 3 is running in Kharadi")
    bad(run(text, item=src), "approved is not running")


def test_metro_open_claim_ok_when_source_says_so():
    src = replace(ITEM, text=ITEM.text + " The Pune Metro station will open to passengers in October.")
    assert run(add("The metro station will open in October."), item=src).ok


def test_stale_item():
    old = PUB - timedelta(days=30)
    bad(run(item=replace(ITEM, published_at=old), facts=Facts(FACTS.facts, old)), "days old")


def test_no_date_at_all():
    bad(run(item=replace(ITEM, published_at=None), facts=Facts(FACTS.facts, None)), "date")


def test_post_without_question():
    bad(run(CLEAN.replace("?", ".")), "question")


def test_question_mark_only_in_url_does_not_count():
    bad(run(CLEAN.replace("?", ".").replace(URL, URL + "?utm=1")), "question")


def test_post_too_long():
    bad(run(add("Filler words here. " * 60)), "characters")


def test_missing_as_of_line():
    bad(run(CLEAN.replace("as of 12 Sep 2026", "")), "as of")


def test_article_does_not_need_a_question():
    art = CLEAN.replace("Does a planned metro change how you pick a home? Tell us in the comments.\n\n", "")
    assert run(art, format="article", title="Metro Line 3 trial runs").ok


def test_invented_name_in_article_title():
    bad(run(format="article", title="Hinjewadi gets a station"), "Hinjewadi")


@pytest.mark.parametrize("text", ["", "   "])
def test_empty_text_never_passes(text):
    assert not run(text).ok
