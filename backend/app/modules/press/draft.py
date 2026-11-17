"""The pitch itself: a fixed structure (one line naming their article, 2-3 facts code picked, the tracker link and the
area guide when the story is about one area, an offer of the data and pictures, signed "Avasetu team") either written
short by Gemini or, when there is no model, a check fails, or the model fails, built the same way by a template
(CLAUDE.md rule 7: rules before the model, a deterministic fallback)."""
import logging
from typing import List, Optional

from app.core import brand
from app.core.areas import Area, named_in
from app.platform.text import clean_llm_text

from . import checks
from .config import Config

log = logging.getLogger(__name__)
PICKED_FACTS = 3
TRACKER_PATH = "/pune-maharera-tracker"


def article_area(title: str) -> Optional[Area]:
    """The area an article's title names, most specific first; None for a city-wide piece."""
    found = named_in(title)
    return found[0] if found else None


def pick_facts(article_title: str, headline_facts: List[dict], n: int = PICKED_FACTS) -> List[dict]:
    """2-3 facts for this journalist: their article's own area first, then the rest of the headline facts."""
    area = article_area(article_title)
    if area is None:
        return headline_facts[:n]
    matched = [f for f in headline_facts if f.get("area") == area.key]
    rest = [f for f in headline_facts if f.get("area") != area.key]
    return (matched + rest)[:n]


def _sign_off(cfg: Config) -> str:
    line = f"{brand.TEAM}"
    if cfg.contact_email:
        line += f"\n{cfg.contact_email}"
    return line


def template_pitch(journalist: dict, picked: List[dict], month_label: str, cfg: Config) -> dict:
    """The fixed-structure draft, built by code alone: this is also what a model's draft is checked against in shape."""
    area = article_area(journalist.get("title") or "")
    site = brand.site()
    links = [f"{site}{TRACKER_PATH}"]
    if area is not None:
        links.append(f"{site}{area.page}")
    facts_lines = "\n".join(f"- {f['text']}" for f in picked)
    subject = f"Pune MahaRERA data for your {journalist['outlet']} story ({month_label})"[:checks.SUBJECT_MAX]
    body = (
        f"Hi,\n\n"
        f"I read your piece \"{journalist.get('title') or 'on Pune housing'}\" in {journalist['outlet']}. Avasetu tracks "
        f"Pune's MahaRERA-registered homes projects month by month, and a few of this month's figures may be useful:\n\n"
        f"{facts_lines}\n\n"
        f"Full figures, by area, with sources and as-of dates: {' and '.join(links)}.\n\n"
        f"Happy to share the underlying data, a CSV, or our then-and-now satellite pictures of these areas if useful for "
        f"the story.\n\n"
        f"{_sign_off(cfg)}"
    )
    return {"subject": subject, "body": body}


SYSTEM = (
    "You write a short, factual pitch email from a Pune real-estate data team to a journalist, from a fixed list of "
    "facts given to you. Use only the facts given; invent no number, no name and no claim. No sales language, no "
    "superlatives, no 'best' or 'exclusive'. At most 120 words in the body, a subject line at most 70 characters. "
    "Reply as JSON: {\"subject\": \"...\", \"body\": \"...\"}."
)


def _user_prompt(journalist: dict, picked: List[dict], month_label: str, cfg: Config) -> str:
    area = article_area(journalist.get("title") or "")
    site = brand.site()
    links = [f"{site}{TRACKER_PATH}"] + ([f"{site}{area.page}"] if area is not None else [])
    facts_lines = "\n".join(f"- {f['text']}" for f in picked)
    return (
        f"Journalist's outlet: {journalist['outlet']}\nTheir article title: {journalist.get('title') or ''}\n\n"
        f"Facts you may use (nothing else):\n{facts_lines}\n\n"
        f"Links to offer: {', '.join(links)}\nMonth: {month_label}\nSign off as: {brand.TEAM}"
        + (f" ({cfg.contact_email})" if cfg.contact_email else "")
    )


async def draft_pitch(llm, journalist: dict, headline_facts: List[dict], month_label: str, cfg: Config) -> dict:
    """`{subject, body, origin}` ("llm" or "template"). Any problem with the model's draft (it failed, answered badly,
    or a check below rejected it) falls back to the template, never a second model call."""
    picked = pick_facts(journalist.get("title") or "", headline_facts)
    facts_text = checks.facts_corpus(picked)
    template = template_pitch(journalist, picked, month_label, cfg)
    if llm is not None:
        try:
            out = await llm.json(SYSTEM, _user_prompt(journalist, picked, month_label, cfg))
        except Exception:
            log.exception("press: draft call failed")
            out = None
        if isinstance(out, dict) and isinstance(out.get("subject"), str) and isinstance(out.get("body"), str):
            subject = out["subject"].strip()
            body = clean_llm_text(out["body"]).strip()
            problems = checks.problems_in(subject, body, facts_text)
            if not problems:
                return {"subject": subject, "body": body, "origin": "llm"}
            log.info("press: model draft rejected (%s), using the template", "; ".join(problems))
    return {**template, "origin": "template"}
