"""T1.1: new projects reach the newsroom. MahaRERA gives the taluka ("Haveli"), so its items are matched by pincode and by
project name; new-project news may name the area only after the first sentence; plurals in 'es' count; and nothing we write
claims a MahaRERA project is newly registered (the only date we have is 'Last Modified')."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.modules.newsroom.sources.maharera import MahaReraSource, parse_page
from app.modules.newsroom.stages import draft as draft_stage
from app.modules.newsroom.stages.check import check
from app.modules.newsroom.stages.filter import _phrase, assess
from app.modules.newsroom.types import Draft, Fact, Facts, RawItem, Relevance

NOW = datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc)
FIX = Path(__file__).parent / "fixtures" / "sources"
FIRST = (FIX / "maharera_pune_first.html").read_text(encoding="utf-8")
LAST = (FIX / "maharera_pune_last.html").read_text(encoding="utf-8")

# the real last page, with three cards moved into our area: two by pincode, one by its project name
IN_AREA = (LAST.replace("412202", "412207", 1)  # AARAMBH PHASE 1 -> Wagholi / Kesnand / Bakori
           .replace("411016", "411014", 1)  # VIKRAM MARQUEE -> Kharadi
           .replace("Satvam Hills C5", "Satvam Kharadi Heights", 1))


def fresh(items):  # the fixture dates span September; the age rule is not what these tests are about
    return [replace(i, published_at=NOW) for i in items]


def item(title, text, source="t"):
    return RawItem(id="x", source=source, url="https://e.test/x", title=title, text=text, published_at=NOW, fetched_at=NOW)


def test_real_last_page_has_no_project_of_ours():
    for it in fresh(parse_page(LAST)):
        r = assess(it, NOW)
        assert not r.keep and r.reason.startswith("off-topic"), (it.title, r.reason)


def test_in_area_projects_are_kept_and_the_rest_dropped():
    kept = {}
    for it in fresh(parse_page(IN_AREA)):
        r = assess(it, NOW)
        if r.keep:
            kept[it.title.split(": ", 1)[1].split(",")[0]] = (r.areas, r.pillar)
        else:
            assert r.reason.startswith("off-topic"), (it.title, r.reason)
    assert kept == {
        "AARAMBH PHASE 1": (["wagholi"], "new_supply"),
        "VIKRAM MARQUEE": (["kharadi"], "new_supply"),
        "Satvam Kharadi Heights": (["kharadi"], "new_supply"),
    }


def test_maharera_items_say_listed_or_updated():
    for it in parse_page(LAST):
        assert it.title.startswith("Listed or updated on MahaRERA: ")
        assert "listed or updated on MahaRERA" in it.text
        assert "newly" not in (it.title + it.text).lower()


@pytest.mark.asyncio
async def test_reads_more_pages_by_default():
    urls = []

    async def get(url):
        urls.append(url)
        return FIRST if "page=0&" in url else LAST

    await MahaReraSource().fetch(get)
    assert len(urls) == 1 + 15  # the count page, then the newest 15 pages


def test_area_in_second_sentence_of_new_project_story():
    r = assess(item("Developer launches project in Pune",
                    "The developer has announced a residential tower with 200 homes. The site is in Kharadi, off Nagar Road."), NOW)
    assert r.keep, r.reason
    assert r.pillar == "new_supply" and r.areas == ["kharadi"]


def test_area_in_second_sentence_of_other_story_is_still_a_passing_mention():
    r = assess(item("Pune civic body plans new water tanks",
                    "The civic body will build 12 tanks across the city. One will come up near Kharadi."), NOW)
    assert not r.keep


def test_new_project_in_another_locality_is_not_ours():
    r = assess(item("Developer launches project in Hinjewadi",
                    "The developer has announced a residential tower with 200 homes. Kharadi is about an hour away."), NOW)
    assert not r.keep


def test_landmark_alone_deep_in_new_project_story_does_not_count():
    r = assess(item("Developer launches project in Pune",
                    "The developer has announced a residential tower with 200 homes. It is a short drive from EON IT Park."), NOW)
    assert not r.keep


def test_pincode_counts_in_any_item():
    r = assess(item("New project registered in Haveli",
                    "A residential project has been registered. Its address is Gat 1203, Haveli, Pune 412207."), NOW)
    assert r.keep and r.areas == ["wagholi"]
    assert not assess(item("New project registered in Haveli",
                           "A residential project has been registered at Gat 1203, Haveli, Pune 412202."), NOW).keep
    assert not assess(item("New project registered", "Survey number 4120071 in Haveli."), NOW).keep


@pytest.mark.parametrize("word, text", [
    ("launch", "two launches this week"), ("launch", "one launch"), ("launch", "three launchs"), ("bus", "more buses"),
])
def test_plurals_in_es_count(word, text):
    assert _phrase(word, plural=True).search(text)


def test_plural_does_not_swallow_longer_words():
    assert not _phrase("launch", plural=True).search("launcher")
    assert not _phrase("bus", plural=True).search("business")


MAHA = item("Listed or updated on MahaRERA: VIKRAM MARQUEE, Pune City",
            "Project VIKRAM MARQUEE (MahaRERA registration number PM1260002602035) was listed or updated on MahaRERA. "
            "Location: Pune City, Pune district, pincode 411014. MahaRERA record last modified 2026-09-24.", source="MahaRERA")
MAHA_FACTS = Facts([Fact("VIKRAM MARQUEE was listed or updated on MahaRERA.", "was listed or updated on MahaRERA")], NOW)


def _draft(what):
    text = (f"{what}\n\nSource: MahaRERA, as of 30 Sep 2026. {MAHA.url}\n\nAre you looking at homes in Kharadi?\n\n#Pune #Kharadi")
    return Draft("post", text, None, MAHA.url, ["MahaRERA"])


@pytest.mark.parametrize("what", [
    "VIKRAM MARQUEE in Kharadi is newly registered on MahaRERA.",
    "VIKRAM MARQUEE is a new launch in Kharadi.",
    "VIKRAM MARQUEE launched in Kharadi.",
])
def test_check_rejects_new_claims_for_maharera(what):
    res = check(_draft(what), MAHA_FACTS, MAHA, NOW)
    assert any("Last Modified" in p for p in res.problems), res.problems


def test_check_accepts_listed_or_updated():
    res = check(_draft("VIKRAM MARQUEE in Kharadi was listed or updated on MahaRERA."), MAHA_FACTS, MAHA, NOW)
    assert not any("Last Modified" in p for p in res.problems), res.problems


def test_check_leaves_other_sources_alone():
    other = replace(MAHA, source="Times of India")
    res = check(_draft("VIKRAM MARQUEE launched in Kharadi."), MAHA_FACTS, other, NOW)
    assert not any("Last Modified" in p for p in res.problems)


@pytest.mark.asyncio
async def test_llm_is_told_the_maharera_wording(monkeypatch):
    monkeypatch.setattr(draft_stage, "RETRY_DELAY", 0)
    seen = []

    class Llm:
        async def json(self, system, user):
            seen.append(user)
            return None

        async def text(self, system, user, timeout=None):
            return None

    rel = Relevance(keep=True, pillar="new_supply", areas=["kharadi"])
    await draft_stage.draft(MAHA, MAHA_FACTS, rel, "post", Llm())
    assert seen and "listed or updated on MahaRERA" in seen[0] and "Never say" in seen[0]
    seen.clear()
    await draft_stage.draft(replace(MAHA, source="Times of India"), MAHA_FACTS, rel, "post", Llm())
    assert "Never say" not in seen[0]


def test_source_name_keeps_its_capitals():
    assert draft_stage._source_name(MAHA) == "MahaRERA"
    assert draft_stage._source_name(replace(MAHA, source="times_of_india")) == "Times Of India"


def test_a_question_starting_with_has_is_not_a_name():
    res = check(_draft("VIKRAM MARQUEE in Kharadi was listed or updated on MahaRERA.\n\nHas anyone visited the site?"),
                MAHA_FACTS, MAHA, NOW)
    assert not any("Names not in the source" in p for p in res.problems), res.problems
