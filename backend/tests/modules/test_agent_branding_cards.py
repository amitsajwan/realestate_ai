import dataclasses
import re

import pytest

from app.modules.marketing.facts import Facts
from app.modules.marketing.images import render

from .marketing_helpers import facts


@pytest.mark.parametrize("kind", ["cover", "status", "cta"])
def test_agent_business_and_rera_line_on_cards_without_phone(kind):
    f = dataclasses.replace(facts(), agent_business="Deshmukh Realty", agent_rera_no="A52100012345")
    texts = " ".join(render(kind, f, None).texts)
    assert "Listed by Deshmukh Realty · RERA A52100012345" in texts
    assert not re.search(r"\d{8,}", re.sub(r"[AP]\d{11}", "", texts))


def test_cards_without_agent_branding_keep_the_team_line():
    assert "Listed by Avasetu team" in " ".join(render("cover", facts(), None).texts)


def test_facts_reads_business_name_and_rera_from_branding_data():
    prof = {"phone": "9876543210", "branding_data": {"business_name": "Deshmukh Realty", "rera_agent_no": "A52100012345"}}
    f = Facts.from_docs({"_id": "L1", "title": "2 BHK"}, prof, "https://x.test/l")
    assert (f.agent_business, f.agent_rera_no) == ("Deshmukh Realty", "A52100012345")
    assert Facts.from_docs({"_id": "L1"}, {}, "").agent_business == ""
