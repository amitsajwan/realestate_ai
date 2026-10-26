"""Leads from AI answers are named by their assistant (app/modules/tracking/origin.py; docs/plan/seo-system.md 8a, step 3)."""
from datetime import datetime, timedelta, timezone

from app.modules.inbox.handover import source_text
from app.modules.seo import aivisits
from app.modules.tracking import origin

from .fakes import FakeDb

NOW = datetime(2026, 10, 26, 9, 0, tzinfo=timezone.utc)


def test_a_visit_from_gemini_is_gemini_not_google_search():
    assert origin.referrer_source("https://gemini.google.com/app/abc") == "gemini"
    assert origin.referrer_source("https://www.google.co.in/") == "google"


def test_every_assistant_the_ai_visit_log_knows_is_a_lead_source():
    for host, name in aivisits.REFERRERS:
        key = origin.referrer_source(f"https://{host}/")
        assert key in origin.AI_SOURCES and origin.AI_NAMES[key] == name


def test_copilot_and_claude_referrers_are_named():
    assert origin.referrer_source("https://copilot.microsoft.com/chats/1") == "copilot"
    assert origin.referrer_source("https://claude.ai/chat/1") == "claude"


def test_chatgpts_utm_source_names_the_lead_when_its_app_sends_no_referrer():
    assert origin.source_key(None, None, {"utm_source": "chatgpt.com"}) == "chatgpt"
    assert origin.source_key("fb_reel", None, {"utm_source": "chatgpt.com"}) == "fb_reel"      # a tagged link still wins
    assert origin.source_key(None, "https://www.google.com/", {"utm_source": "newsletter"}) == "google"


def test_the_agent_sees_the_assistant_a_lead_came_from():
    lead = {"source": None, "utm": {"utm_source": "perplexity"}, "first_touch": {"referrer": None}}
    assert source_text(lead) == "Perplexity"
    assert source_text({"source": "gemini", "first_touch": {}}) == "Gemini"


async def test_leads_from_ai_answers_are_counted_per_assistant_for_the_week():
    contacts = FakeDb().get_collection("contacts")
    for i, (source, ref, utm, days) in enumerate([
            ("chatgpt", None, {}, 1), (None, "https://gemini.google.com/", {}, 2), (None, None, {"utm_source": "chatgpt.com"}, 3),
            ("google", "https://www.google.com/", {}, 1), ("chatgpt", None, {}, 9)]):
        await contacts.insert_one({"_id": str(i), "source": source, "utm": utm, "first_touch": {"referrer": ref},
                                   "created_at": NOW - timedelta(days=days)})
    assert await origin.leads_from_ai(contacts, NOW - timedelta(days=7)) == {"ChatGPT": 2, "Gemini": 1}
