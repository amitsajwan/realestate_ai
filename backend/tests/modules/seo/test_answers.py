"""Answers to post on Reddit and Quora: the page's own fact-written answers, one per project, rotated weekly (seo/answers.py)."""
from datetime import datetime, timezone

from app.modules.seo import answers

NOW = datetime(2026, 11, 23, 9, 0, tzinfo=timezone.utc)
FAQ_PINCODE = {"q": "What is the pincode of Godrej Ivara?", "a": "412207.", "source": "MahaRERA", "topic": "location"}
FAQ_DATE = {"q": "When is Godrej Ivara possession?", "a": "The completion date Godrej Ivara filed with MahaRERA is 31 December 2030.",
            "source": "MahaRERA", "topic": "possession"}


def project(regno: str, units: int, locality: str = "upper_kharadi", faq=None, slug=None) -> dict:
    return {"_id": regno, "regno": regno, "name": f"PROJECT {regno}", "search_name": f"Project {regno}", "locality": locality,
            "page_slug": slug or f"project-{regno.lower()}", "units_total": units, "seo_faq": faq if faq is not None else [FAQ_PINCODE, FAQ_DATE]}


def test_a_projects_possession_question_comes_before_its_pincode(monkeypatch):
    monkeypatch.setattr(answers, "searchable", lambda d, now=None: True)
    [item] = answers.to_post([project("P1", 400)], "https://avasetu.in/", NOW)
    assert item["question"] == FAQ_DATE["q"] and item["answer"] == FAQ_DATE["a"]
    assert item["page"] == "https://avasetu.in/projects/project-p1?src=answer"
    assert item["draft"].startswith(FAQ_DATE["a"]) and item["page"] in item["draft"] and answers.DISCLOSE in item["draft"]
    assert item["find"]["reddit"] == "https://www.reddit.com/r/pune/search/?q=Project+P1"
    assert item["area"] == "Upper Kharadi"


def test_only_our_areas_pages_in_search_with_an_answer_are_offered(monkeypatch):
    monkeypatch.setattr(answers, "searchable", lambda d, now=None: d["_id"] != "OUT")
    docs = [project("OUT", 900), project("RAVET", 800, locality="ravet"), project("NOFAQ", 700, faq=[]),
            project("PRICE", 600, faq=[{"q": "Price?", "a": "x", "topic": "price"}]), project("OK", 100)]
    assert [i["regno"] for i in answers.to_post(docs, "https://avasetu.in", NOW)] == ["OK"]


def test_the_list_turns_each_week_and_every_project_comes_round(monkeypatch):
    monkeypatch.setattr(answers, "searchable", lambda d, now=None: True)
    docs = [project(f"P{i:02d}", 1000 - i) for i in range(25)]
    seen = set()
    for week in range(5):
        day = datetime(2026, 11, 2 + 7 * week, tzinfo=timezone.utc)
        got = [i["regno"] for i in answers.to_post(docs, "https://avasetu.in", day)]
        assert len(got) == answers.MAX and len(set(got)) == answers.MAX
        seen.update(got)
    assert len(seen) == 25
