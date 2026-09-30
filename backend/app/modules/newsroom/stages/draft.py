"""Write a draft from the extracted facts only (never the raw article), so the model has nothing to embellish.

The LLM returns short parts; code assembles the final text so the link, the 'as of' line, the hashtags and the disclaimer are
always there. Every draft still goes through `check` afterwards: this stage does not vouch for its own output.
"""
import re
from typing import List, Optional

from .. import policy
from ..types import Draft, Facts, Llm, RawItem, Relevance

BRAND = "PUNE Property team"
AREA_NAMES = {"kharadi": "Kharadi", "upper_kharadi": "Upper Kharadi", "wagholi": "Wagholi"}
AREA_TAGS = {"kharadi": "#Kharadi", "upper_kharadi": "#UpperKharadi", "wagholi": "#Wagholi"}
URL = re.compile(r"https?://\S+", re.I)

SYSTEM = (
    f"You are the {BRAND}, writing for people in Pune who want to buy or rent a home. Write in friendly, plain English. "
    "Use ONLY the facts you are given. Do not add any number, date, name, place or claim that is not in them. Do not copy "
    "wording word for word; say it in your own words. No hype or superlatives (best, perfect, dream), no phone numbers, "
    "no predictions about prices, no praise or criticism of any builder. If something is only approved or planned, say "
    "'approved' or 'planned', never that it is running or open unless a fact says so. Hedge your view with words like "
    "'may' or 'could'. Reply with JSON only, with these keys: "
    '"title" (a short plain headline, no hype), "what" (1 to 2 sentences: what happened), "why" (1 to 2 sentences: why it may '
    'matter to someone buying or renting in the area, hedged), "check" (one sentence: what a buyer should verify), '
    '"question" (one friendly question that invites comments, ending with ?).'
)


def _clean(s) -> str:
    return re.sub(r"\s+", " ", URL.sub("", str(s or ""))).strip()


def _source_name(item: RawItem) -> str:
    return item.source.replace("_", " ").strip().title() if item.source else ""


def _as_of(facts: Facts, item: RawItem) -> str:
    d = facts.as_of or item.published_at
    return f"{d.day} {d.strftime('%b %Y')}" if d else ""


def _areas(rel: Relevance) -> List[str]:
    return [a for a in (rel.areas or []) if a in AREA_NAMES]


def _tags(rel: Relevance) -> str:
    return " ".join(["#Pune", "#PunePropertyHub"] + [AREA_TAGS[a] for a in _areas(rel)])


def _question(rel: Relevance) -> str:
    names = [AREA_NAMES[a] for a in _areas(rel)]
    where = " or ".join(names[:2]) if names else "Pune"
    return f"Does this change how you look at homes in {where}? Tell us in the comments."


def _assemble(item: RawItem, facts: Facts, rel: Relevance, fmt: str, parts: dict) -> Draft:
    name, as_of = _source_name(item), _as_of(facts, item)
    src = f"Source: {name}" + (f", as of {as_of}" if as_of else "")
    what, why, chk = _clean(parts.get("what")), _clean(parts.get("why")), _clean(parts.get("check"))
    q = _clean(parts.get("question"))
    if not q.endswith("?"):
        q = _question(rel)
    if fmt == "article":
        body = [what, f"Why it may matter: {why} This is our view, not a fact from the source.", f"What to check: {chk}",
                f"{src}. Read it here: {item.url}", policy.DISCLAIMER]
        text = "\n\n".join(p for p in body if p)
        return Draft("article", text, _clean(parts.get("title")) or None, item.url, [name])

    def post(with_check: bool) -> str:
        lines = [what, f"Our view: {why}"] + ([f"What to check: {chk}"] if with_check and chk else [])
        lines += [f"{src}. {item.url}", q, _tags(rel)]
        return "\n\n".join(x for x in lines if x)

    text = post(True)
    if len(text) > policy.POST_MAX_CHARS:
        text = post(False)  # shortest honest version: the check line goes first
    return Draft("post", text, None, item.url, [name])


def template_draft(item: RawItem, facts: Facts, rel: Relevance, fmt: str = "post") -> Optional[Draft]:
    """Deterministic, plain draft straight from the facts. Used when no LLM is available."""
    texts = [_clean(f.text) for f in facts.facts if _clean(f.text)]
    if not texts:
        return None
    names = [AREA_NAMES[a] for a in _areas(rel)]
    where = " and ".join(names) if names else "Pune"
    parts = {
        "title": texts[0].rstrip(".")[:90],
        "what": " ".join(t if t.endswith(".") else t + "." for t in texts[:2]),
        "why": f"If you are buying or renting in {where}, this may be worth knowing about.",
        "check": "Read the source and any official notice for the latest status before you decide.",
        "question": _question(rel),
    }
    return _assemble(item, facts, rel, "article" if fmt == "article" else "post", parts)


async def draft(item: RawItem, facts: Facts, relevance: Relevance, fmt: str, llm: Optional[Llm]) -> Optional[Draft]:
    if not facts.facts:
        return None
    if llm is None:
        return template_draft(item, facts, relevance, fmt)
    where = ", ".join(AREA_NAMES[a] for a in _areas(relevance)) or "Pune"
    user = (f"Format: {fmt}\nArea: {where}\nPillar: {relevance.pillar or 'general'}\nAs of: {_as_of(facts, item) or 'unknown'}\n"
            "Facts:\n" + "\n".join(f"- {_clean(f.text)}" for f in facts.facts))
    try:
        parts = await llm.json(SYSTEM, user)
    except Exception:  # an LLM outage must never crash the pipeline
        return None
    if not isinstance(parts, dict) or not _clean(parts.get("what")) or not _clean(parts.get("why")):
        return None
    return _assemble(item, facts, relevance, "article" if fmt == "article" else "post", parts)
