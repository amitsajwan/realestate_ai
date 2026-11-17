"""The pitch draft: a model's answer is used only when it passes the checks; any failure falls back to the same
fixed-structure template (CLAUDE.md rule 7)."""
from app.modules.press.config import Config
from app.modules.press.draft import draft_pitch, pick_facts, template_pitch

FACTS = [
    {"text": "Kharadi registered 4 new MahaRERA projects in October 2026, and 11 so far in 2026.", "area": "kharadi",
     "topic": "registrations", "source": "MahaRERA public records, read by Avasetu", "as_of": "2026-11-17"},
    {"text": "Builders moved the possession date of 6 of 20 homes projects still being built (30%).", "area": None,
     "topic": "date_moves", "source": "MahaRERA public records, read by Avasetu", "as_of": "2026-11-17"},
]
JOURNALIST = {"outlet": "Hindustan Times", "title": "Kharadi's new housing boom", "url": "https://hindustantimes.com/a",
              "date": "2 days ago", "name": None, "email": None, "contact_page": None}
CFG = Config(contact_email="hello@avasetu.in")


class FakeLLM:
    def __init__(self, out):
        self.out = out

    async def json(self, system, user, temperature=0):
        return self.out


def test_pick_facts_prefers_the_journalists_own_area():
    picked = pick_facts(JOURNALIST["title"], FACTS)
    assert picked[0]["area"] == "kharadi"


async def test_no_model_gives_the_template():
    out = await draft_pitch(None, JOURNALIST, FACTS, "November 2026", CFG)
    assert out["origin"] == "template"
    assert "Hindustan Times" in out["body"] and "Avasetu team" in out["body"] and "hello@avasetu.in" in out["body"]
    assert "pune-maharera-tracker" in out["body"]


async def test_a_model_draft_with_a_number_not_in_the_facts_falls_back_to_the_template():
    llm = FakeLLM({"subject": "Pune housing data", "body": "Kharadi registered 999 new projects this year."})
    out = await draft_pitch(llm, JOURNALIST, FACTS, "November 2026", CFG)
    assert out["origin"] == "template"


async def test_a_model_draft_with_a_sales_word_falls_back_to_the_template():
    llm = FakeLLM({"subject": "The best Pune housing data", "body": "Kharadi registered 4 new projects in October 2026."})
    out = await draft_pitch(llm, JOURNALIST, FACTS, "November 2026", CFG)
    assert out["origin"] == "template"


async def test_a_model_call_that_raises_falls_back_to_the_template():
    class Boom:
        async def json(self, system, user, temperature=0):
            raise RuntimeError("down")
    out = await draft_pitch(Boom(), JOURNALIST, FACTS, "November 2026", CFG)
    assert out["origin"] == "template"


async def test_a_clean_model_draft_is_used():
    llm = FakeLLM({"subject": "Pune MahaRERA data for your story", "body": "Kharadi registered 4 new projects in October 2026."})
    out = await draft_pitch(llm, JOURNALIST, FACTS, "November 2026", CFG)
    assert out["origin"] == "llm" and out["subject"] == "Pune MahaRERA data for your story"


def test_template_structure_has_every_fixed_part():
    draft = template_pitch(JOURNALIST, FACTS[:1], "November 2026", CFG)
    assert len(draft["subject"]) <= 70
    assert JOURNALIST["title"] in draft["body"]
    assert "pune-maharera-tracker" in draft["body"]
    assert "Avasetu team" in draft["body"] and "hello@avasetu.in" in draft["body"]
    assert "pictures" in draft["body"].lower()


def test_template_without_a_contact_email_has_no_email_line():
    draft = template_pitch(JOURNALIST, FACTS[:1], "November 2026", Config())
    assert "Avasetu team" in draft["body"] and "@" not in draft["body"].split("Avasetu team")[-1]
