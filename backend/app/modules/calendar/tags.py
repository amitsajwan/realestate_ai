"""Tags on every calendar row, so a post's results can be grouped by what it was (docs/CONTENT_PLATFORM.md, X-3).

Derived, never typed in: `derive(row)` reads what the row already holds (kind, slug, caption, creative notes, area) and returns a small
dict with a fixed vocabulary. Store.add puts it on every new row, whoever writes it (the plan builders, the campaign scheduler, the
scripts); `Store.backfill_tags` adds it to older rows. A value it cannot tell is "unknown", never a guess.

  schema       TAGS_SCHEMA (bump when a meaning changes, so old and new rows are not compared blindly)
  audience     buyers | agents
  kind         post | showcase | reel
  format       reels: tip | tour | pitch | area | project | trend | agent_ad | listing | slides;
               posts: carousel | single | checklist | myth-vs-fact | poll | stat | before-after | showcase | unknown
  pillar       the plan's role for the slot (myth, explainer, checklist, local, poll, agent, showcase, listing, ...) or unknown
  hook_type    price_reveal | question | number | myth | mistake | statement | unknown
  hook         the opening line, at most 120 characters
  cta          the comment keyword asked for (INTERESTED, AGENT, PRICE, ...), save_share, or none
  area         an area key from app.core.areas, or unknown
  language     en | hi | mr
  experiment, variant, engine, price_band   passed through when the writer set them (trend reels do)
  duration_s, render                        reels only, set when the video is rendered (Store.set_video)
"""
import re
from typing import Dict, Optional

from . import reach

TAGS_SCHEMA = 1
UNKNOWN = "unknown"
REEL_FORMATS = {"tip": "tip", "tour": "tour", "pitch": "pitch", "area": "area", "project": "project", "agent": "agent_ad"}
POST_FORMATS = ("carousel", "single", "checklist", "myth-vs-fact", "poll", "stat", "before-after")
PASS_THROUGH = ("experiment", "variant", "engine", "price_band")
CTA_WORD = re.compile(r"\bcomment\s+\*?([A-Z]{3,})\*?", re.I)
SAVE_SHARE = re.compile(r"\b(save|share|send)\b", re.I)
GUESS = re.compile(r"\bguess\b|\bwait for the price\b", re.I)
MYTH = re.compile(r"\bmyth\b", re.I)
MISTAKE = re.compile(r"\bmistake|\bdon'?t\b|\bstop\b", re.I)
DIGIT = re.compile(r"\d")


def _hook(row: dict) -> str:
    c = row.get("creative") or {}
    text = c.get("hook") or next((l for l in (row.get("caption") or "").splitlines() if l.strip()), "")
    return re.sub(r"\s+", " ", str(text)).strip()[:120]


def hook_type(hook: str, given: Optional[str] = None) -> str:
    """The writer's own label when it set one (trend reels), else read from the words. Order matters: a price guess is also a question."""
    if given:
        return str(given)
    if not hook:
        return UNKNOWN
    if GUESS.search(hook):
        return "price_reveal"
    if MYTH.search(hook):
        return "myth"
    if MISTAKE.search(hook):
        return "mistake"
    if "?" in hook:
        return "question"
    if DIGIT.search(hook):
        return "number"
    return "statement"


def _format(row: dict) -> str:
    c = row.get("creative") or {}
    src = str(c.get("source") or "")
    if row.get("kind") == "reel":
        if src == "trend_reels":
            return "trend"
        if src == "campaign":
            return "listing"
        if c.get("slides_reel"):
            return "slides"
        return REEL_FORMATS.get(str(c.get("template") or ""), UNKNOWN)
    if row.get("kind") == "showcase" or c.get("layout") == "showcase":
        return "showcase"
    fmt = str(c.get("format") or "")
    if fmt in POST_FORMATS:
        return fmt
    slides = c.get("slides")
    if isinstance(slides, int):
        return "carousel" if slides > 1 else "single"
    return UNKNOWN


def _cta(row: dict) -> str:
    c = row.get("creative") or {}
    text = " ".join([str(row.get("caption") or "")] + [str(s) for s in (c.get("script") or []) if isinstance(s, str)])
    for m in CTA_WORD.finditer(text):   # the keyword is written in capitals ('Comment INTERESTED'); 'comment becomes ...' is not one
        if m.group(1).isupper():
            return m.group(1)
    return "save_share" if SAVE_SHARE.search(text) else "none"


def derive(row: dict) -> Dict:
    """The tags for one calendar row (pure: no I/O, no clock). See the module docstring for the vocabulary."""
    c = row.get("creative") or {}
    hook = _hook(row)
    a = reach.area({**row, "area": row.get("area") or c.get("area") or c.get("locality") or ""})
    tags = {
        "schema": TAGS_SCHEMA,
        "audience": reach.audience(row),
        "kind": row.get("kind") or "post",
        "format": _format(row),
        "pillar": str(c.get("role") or UNKNOWN),
        "hook_type": hook_type(hook, c.get("hook_type") or ("myth" if _format(row) == "myth-vs-fact" else None)),
        "hook": hook,
        "cta": _cta(row),
        "area": a.key if a else UNKNOWN,
        "language": str(c.get("language") or row.get("language") or "en"),
    }
    for k in PASS_THROUGH:
        if c.get(k):
            tags[k] = c[k]
    for k in ("duration_s", "render"):
        if (row.get("tags") or {}).get(k) is not None:   # set at render time: kept when the tags are derived again
            tags[k] = row["tags"][k]
    return tags
