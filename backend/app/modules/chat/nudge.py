"""The website chat speaks first (owner, 2026-11-06: "when a person is doing analysis, like home plan, comparing projects, checking multiple
for a few minutes, what if our bot starts communicating?"; docs/plan/chat-reach.md).

Three weeks of visits to 2026-11-06: 610 visits, 14 chats, 1 lead, while 28 visitors read two or more projects for over 90 seconds and
nobody spoke to them. The widget asks POST /chat/nudge after a while on the site, and this picks the one line that fits what they read:
a small note beside the chat button that never opens by itself. Code picks and our fixed sentences speak; no model is asked.

WhatsApp has no such thing: Meta lets us write first only with a paid template, so there the bot answers when they write."""
from datetime import timedelta
from typing import Optional

from app.core import areas as area_registry

from . import engine, plan
from .phrases import quick, quick_for, say

PLAN_WAIT = 20       # seconds on the site: a finished plan is worth a word at once
COMPARE_WAIT = 90    # two or more projects read
AREA_WAIT = 120      # one area or project
ANY_WAIT = 180       # anything else they stay on
GAP = timedelta(hours=24)            # one note a day, however many visits
CHAT_QUIET = timedelta(days=7)       # someone we are already talking to is left alone


def pick(d: dict, seconds: int) -> Optional[dict]:
    """{key, text, quick, link} or None: nothing to say yet, or nobody to say it to (agents, an agent's own site, a buyer who gave a number)."""
    page = d.get("page") or {}
    if d.get("audience") != "buyer" or page.get("site") != "house" or d.get("lead_done") or d.get("phone"):
        return None
    lang = engine._lang(d)
    done = d.get("plan")
    if done and done.get("east") and seconds >= PLAN_WAIT:
        return {"key": "plan", "text": say("seen_plan", lang, want=done["want"]), "quick": [quick("plan_prices", lang)], "link": None}
    offer = plan.link(d, lang) if plan.can_offer(d, "web") else None
    here = [page["name"]] if page.get("kind") == "project" and page.get("name") else []
    read = here + engine.read_projects(d, limit=3)
    if len(read) >= 2 and seconds >= COMPARE_WAIT:
        return {"key": "compare", "text": say("nudge_compare", lang, a=read[0], b=read[1]), "quick": [quick("compare", lang)], "link": offer}
    area = d.get("locality") or page.get("locality")
    if area and seconds >= AREA_WAIT and area_registry.named_in(area):
        return {"key": "hot", "text": say("nudge_hot", lang, area=area), "quick": [quick_for("hot_in", lang, area)], "link": offer}
    if offer and seconds >= ANY_WAIT:
        return {"key": "try_plan", "text": say("try_plan", lang), "quick": [], "link": offer}
    return None
