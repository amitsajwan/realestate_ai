"""Write a draft from the extracted facts only (never the raw article), so the model has nothing to embellish.

The LLM returns short parts; code assembles the final text so the link, the 'as of' line, the hashtags and the disclaimer are
always there. Every draft still goes through `check` afterwards: this stage does not vouch for its own output.
"""
from app.core import brand
import re
import asyncio
from typing import List, Optional, Tuple

from .. import policy
from ..types import Draft, Facts, Llm, RawItem, Relevance, Research
from .research import readable_chars

BRAND = brand.TEAM
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

# used when the source gives only a headline: no room for 'why it matters', so the model is not asked for one
SYSTEM_HEADLINE = (
    f"You are the {BRAND}, writing for people in Pune who want to buy or rent a home. Write in friendly, plain English. "
    "The source gave only a headline, so you know just one fact. Use ONLY the facts you are given. Do not add any number, "
    "date, name, place or claim that is not in them, and do not explain what it means or what it may lead to. No hype, no "
    "phone numbers, no predictions about prices, no praise or criticism of any builder. If something is only approved or "
    "planned, say so. Reply with JSON only, with these keys: "
    '"title" (a short plain headline), "what" (ONE sentence in your own words: what happened), "check" (ONE practical '
    'sentence: what a buyer could verify, such as the official notice or the project page), "question" (one friendly '
    'question ending with ?).'
)
HEADLINE_CHECK = "Read the source and any official notice for the latest status before you decide."

# A full news article, written from researched facts (several reports when we found them) and our verified area guide.
SYSTEM_ARTICLE = (
    f"You are a reporter for the {BRAND}, writing a news article for people in Pune who want to buy or rent a home. Write in clear, "
    "plain English, like a good local newspaper: the news first, then the details, then context. Use ONLY the facts and background "
    "you are given. Do not add any number, date, name, place or claim that is not in them. Say where each important figure or claim "
    "comes from ('according to <source>', '<source> reported'); the source names are given with each fact. If two sources give "
    "different figures, say so and give both. Do not copy wording word for word; say it in your own words. No hype or superlatives, "
    "no phone numbers, no predictions about prices, no praise or criticism of any builder. If something is only approved or planned, "
    "say 'approved' or 'planned', never that it is running or open unless a fact says so. Reply with JSON only, with these keys: "
    '"title" (a plain, specific headline of 6 to 12 words, no hype), "standfirst" (one sentence: the news in brief), "body" (a list '
    "of 3 to 6 paragraphs, each 2 to 4 sentences: what happened, the key figures and dates, who decided or said what, what happens "
    'next as reported), "background" (1 to 2 sentences built only from the background lines, or "" when they do not help), "why" '
    "(2 to 3 sentences: why it may matter to someone buying or renting, hedged with may or could, concrete, no generic filler), "
    '"check" (a list of 1 to 3 practical things a buyer can verify, each one sentence), "question" (one friendly question ending with ?).'
)
ARTICLE_MIN_FACTS = 3  # fewer than this is a post, not an article
ARTICLE_MIN_CHARS = 800  # real article text the research must have read (full reports, not feed summaries)
# MahaRERA cards carry only a "Last Modified" date, so we cannot say when a project was registered or launched
MAHARERA_RULE = (f"This is a MahaRERA record. Say the project was '{policy.MAHARERA_PHRASE}'. Never say it was newly registered, "
                 "just registered, launched or a new launch.")
HEADLINE_MAX_WORDS = 25  # a source text shorter than this is treated as headline-only


def _clean(s) -> str:
    return re.sub(r"\s+", " ", URL.sub("", str(s or ""))).strip()


def is_maharera(item: RawItem) -> bool:
    return (item.source or "").strip().lower() == "maharera"


def headline_only(item: RawItem) -> bool:
    """True when the source gives no more than its headline (empty, same as the title, or a few words more)."""
    text = re.sub(r"\s+", " ", URL.sub("", item.text or "")).strip().lower()
    title = re.sub(r"\s+", " ", item.title or "").strip().lower()
    if not text or text == title or title.startswith(text):
        return True
    if text.startswith(title) and len(text.split()) - len(title.split()) <= 4:  # e.g. headline plus a publisher name
        return True
    return len(text.split()) < HEADLINE_MAX_WORDS


def _source_name(item: RawItem) -> str:
    s = (item.source or "").replace("_", " ").strip()
    return s if any(c.isupper() for c in s) else s.title()  # "MahaRERA" stays as written; "times_of_india" -> "Times Of India"


def _as_of(facts: Facts, item: RawItem) -> str:
    d = facts.as_of or item.published_at
    return f"{d.day} {d.strftime('%b %Y')}" if d else ""


def _areas(rel: Relevance) -> List[str]:
    return [a for a in (rel.areas or []) if a in AREA_NAMES]


def _tags(rel: Relevance) -> str:
    return " ".join(["#Pune", brand.HASHTAG] + [AREA_TAGS[a] for a in _areas(rel)])


def _question(rel: Relevance) -> str:
    names = [AREA_NAMES[a] for a in _areas(rel)]
    where = " or ".join(names[:2]) if names else "Pune"
    return f"Does this change how you look at homes in {where}? Tell us in the comments."


def _safe_title(title, item: RawItem, facts: Facts) -> Optional[str]:
    """A headline for the website and the cards: the model's own title when it is short, is not the source headline and adds no
    capitalised word that the source or the facts lack; else None (the card then uses the first fact, already in our wording)."""
    t = _clean(title).rstrip(".")
    ws = t.split()
    if not t or len(ws) < 3 or len(ws) > 14:
        return None
    flat = lambda x: re.sub(r"\W+", " ", x or "").lower()  # noqa: E731
    src = " ".join(flat(x) for x in [item.title, item.text] + [f.text for f in facts.facts])
    if flat(t) == flat(item.title):
        return None
    for w in ws[1:]:
        core = re.sub(r"[^\w₹]", "", w)
        if core[:1].isupper() and not core.isupper() and core.lower() not in src:
            return None
    return t


def _sources(item: RawItem, facts: Facts, research: Optional[Research]) -> List[Tuple[str, str]]:
    """(name, link) of every report the draft draws on: the item's own source first, then each other report that gave a fact, then
    the publishers that also reported the story (no link: we could not read them)."""
    main = (_source_name(item), item.url or "")
    if research is None:
        return [main]
    used = {f.source for f in facts.facts if f.source}
    out = [main]
    for s in research.sources:
        if s.role != "main" and s.name in used and s.name not in [n for n, _ in out]:
            out.append((s.name, s.url))
    for n in research.also_reported:
        if n not in [x for x, _ in out]:
            out.append((n, ""))
    return out


def _readable(url: str) -> bool:
    return bool(url) and "news.google.com" not in url.lower()


def _source_line(sources: List[Tuple[str, str]], as_of: str) -> str:
    when = f", as of {as_of}" if as_of else ""
    if len(sources) == 1:
        name, url = sources[0]
        return f"Source: {name}{when}. Read it here: {url}"
    cited = [f"{n} ({u})" if u else n for n, u in sources]
    return f"Sources: {'; '.join(cited)}{when}."


def _article(item: RawItem, facts: Facts, rel: Relevance, parts: dict, research: Optional[Research]) -> Draft:
    """A full article: standfirst, body paragraphs, labelled background, our labelled view, what to check, every source with its
    link, the 'as of' date and the disclaimer. `split_text` takes the same text apart for the site and the captions."""
    sources = _sources(item, facts, research)
    body = [_clean(p) for p in (parts.get("body") or []) if isinstance(p, str) and _clean(p)]
    checks = parts.get("check")
    checks = [_clean(c) for c in (checks if isinstance(checks, list) else [checks]) if isinstance(c, str) and _clean(c)]
    bg, why = _clean(parts.get("background")), _clean(parts.get("why"))
    paras = [_clean(parts.get("standfirst"))] + body
    paras += [f"Background: {bg}"] if bg else []
    paras += [f"Why it may matter: {why} This is our view, not a fact from the source."] if why else []
    paras += [f"What to check: {' '.join(c if c.endswith(('.', '?')) else c + '.' for c in checks)}"] if checks else []
    paras += [_source_line(sources, _as_of(facts, item)), policy.DISCLAIMER]
    link = next((u for _, u in sources if _readable(u)), item.url)
    return Draft("article", "\n\n".join(p for p in paras if p), _safe_title(parts.get("title"), item, facts), link,
                 [n for n, _ in sources], [u for _, u in sources])


def can_be_article(item: RawItem, facts: Facts, research: Optional[Research]) -> bool:
    """An article needs real reporting to stand on: enough facts, and full article text that the research actually read. A headline
    and a line make a post, however important the story."""
    return len(facts.facts) >= ARTICLE_MIN_FACTS and readable_chars(research) >= ARTICLE_MIN_CHARS


def template_article(item: RawItem, facts: Facts, rel: Relevance, research: Optional[Research]) -> Optional[Draft]:
    """Deterministic article straight from the facts, grouped by the report they come from. Used when the LLM is unavailable."""
    texts = [(f.source or _source_name(item), _clean(f.text)) for f in facts.facts if _clean(f.text)]
    if not texts:
        return None
    dot = lambda t: t if t.endswith(".") else t + "."  # noqa: E731
    groups: dict = {}
    for name, t in texts[1:]:
        groups.setdefault(name, []).append(dot(t))
    body = [f"{' '.join(ts)} (Reported by {name}.)" for name, ts in groups.items()]
    bg = " ".join(research.background[:2]) if research and research.background else ""
    parts = {"title": texts[0][1].rstrip(".")[:90], "standfirst": dot(texts[0][1]), "body": body, "background": bg, "why": "",
             "check": [HEADLINE_CHECK]}
    return _article(item, facts, rel, parts, research)


def _assemble(item: RawItem, facts: Facts, rel: Relevance, fmt: str, parts: dict) -> Draft:
    name, as_of = _source_name(item), _as_of(facts, item)
    src = f"Source: {name}" + (f", as of {as_of}" if as_of else "")
    what, why, chk = _clean(parts.get("what")), _clean(parts.get("why")), _clean(parts.get("check"))
    q = _clean(parts.get("question"))
    if not q.endswith("?"):
        q = _question(rel)
    if fmt == "article":
        body = [what, f"Why it may matter: {why} This is our view, not a fact from the source." if why else "", f"What to check: {chk}",
                f"{src}. Read it here: {item.url}", policy.DISCLAIMER]
        text = "\n\n".join(p for p in body if p)
        return Draft("article", text, _clean(parts.get("title")) or None, item.url, [name])

    def post(with_check: bool) -> str:
        lines = [what] + ([f"Our view: {why}"] if why else []) + ([f"What to check: {chk}"] if with_check and chk else [])
        lines += [f"{src}. {item.url}", q, _tags(rel)]
        return "\n\n".join(x for x in lines if x)

    text = post(True)
    if len(text) > policy.POST_MAX_CHARS:
        text = post(False)  # shortest honest version: the check line goes first
    return Draft("post", text, _safe_title(parts.get("title"), item, facts), item.url, [name])


def template_draft(item: RawItem, facts: Facts, rel: Relevance, fmt: str = "post") -> Optional[Draft]:
    """Deterministic, plain draft straight from the facts. Used when no LLM is available."""
    texts = [_clean(f.text) for f in facts.facts if _clean(f.text)]
    if not texts:
        return None
    if headline_only(item) and len(facts.facts) == 1:  # the headline itself is the only statement: quote it and credit the publisher
        what = f"{_source_name(item)} reports: “{texts[0].rstrip('.')}”"
    else:
        what = " ".join(t if t.endswith(".") else t + "." for t in texts[:2])
    parts = {
        "title": texts[0].rstrip(".")[:90],
        "what": what,
        "why": "",  # nothing specific to say, so say nothing: generic filler is worse than silence
        "check": "Read the source and any official notice for the latest status before you decide.",
        "question": _question(rel),
    }
    return _assemble(item, facts, rel, "article" if fmt == "article" else "post", parts)


LLM_TRIES = 3
RETRY_DELAY = 2.0  # seconds; tests set it to 0


def _facts_block(facts: Facts) -> str:
    return "\n".join(f"- {_clean(f.text)}" + (f" [source: {f.source}]" if f.source else "") for f in facts.facts)


async def _ask(llm: Llm, system: str, user: str, ok) -> Optional[dict]:
    parts = None
    for attempt in range(LLM_TRIES):  # free models are flaky under a burst of calls: try again before giving up
        try:
            parts = await llm.json(system, user)
        except Exception:  # an LLM outage must never crash the pipeline
            parts = None
        if isinstance(parts, dict) and ok(parts):
            return parts
        if attempt < LLM_TRIES - 1:
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    return None


async def write_article(item: RawItem, facts: Facts, relevance: Relevance, llm: Optional[Llm], research: Optional[Research]) -> Optional[Draft]:
    """The researched article (see SYSTEM_ARTICLE); the deterministic one when the model fails or returns too little."""
    if llm is None:
        return template_article(item, facts, relevance, research)
    where = ", ".join(AREA_NAMES[a] for a in _areas(relevance)) or "Pune"
    bg = research.background if research else []
    user = (f"Area: {where}\nTopic: {relevance.pillar or 'general'}\nAs of: {_as_of(facts, item) or 'unknown'}\n"
            f"Sources read: {', '.join(n for n, _ in _sources(item, facts, research))}\n"
            + "Facts (each with its source):\n" + _facts_block(facts)
            + ("\nBackground (our own verified area guide; context only, never news):\n" + "\n".join(f"- {b}" for b in bg) if bg else ""))
    body_ok = lambda p: isinstance(p.get("body"), list) and sum(1 for x in p["body"] if isinstance(x, str) and _clean(x)) >= 2  # noqa: E731
    parts = await _ask(llm, SYSTEM_ARTICLE, user, lambda p: bool(_clean(p.get("standfirst"))) and body_ok(p) and bool(_clean(p.get("why"))))
    if parts is None:
        return template_article(item, facts, relevance, research)
    return _article(item, facts, relevance, parts, research)


async def draft(item: RawItem, facts: Facts, relevance: Relevance, fmt: str, llm: Optional[Llm],
                research: Optional[Research] = None) -> Optional[Draft]:
    if not facts.facts:
        return None
    if fmt == "article" and can_be_article(item, facts, research):
        return await write_article(item, facts, relevance, llm, research)
    if fmt == "article":
        fmt = "post"  # too little reporting behind it for an honest article
    if llm is None:
        return template_draft(item, facts, relevance, fmt)
    where = ", ".join(AREA_NAMES[a] for a in _areas(relevance)) or "Pune"
    thin = headline_only(item)
    if thin:
        fmt = "post"  # a headline alone never supports an article
    user = (f"Format: {fmt}\nArea: {where}\nPillar: {relevance.pillar or 'general'}\nAs of: {_as_of(facts, item) or 'unknown'}\n"
            + (MAHARERA_RULE + "\n" if is_maharera(item) else "")
            + "Facts:\n" + "\n".join(f"- {_clean(f.text)}" for f in facts.facts))
    parts = None
    for attempt in range(LLM_TRIES):  # free models are flaky under a burst of calls: try again before giving up
        try:
            parts = await llm.json(SYSTEM_HEADLINE if thin else SYSTEM, user)
        except Exception:  # an LLM outage must never crash the pipeline
            parts = None
        if isinstance(parts, dict) and _clean(parts.get("what")):
            break
        if attempt < LLM_TRIES - 1:
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    if not isinstance(parts, dict) or not _clean(parts.get("what")):
        return template_draft(item, facts, relevance, fmt)
    if thin:
        parts = {**parts, "why": "", "check": parts.get("check") or HEADLINE_CHECK}
    elif not _clean(parts.get("why")):
        return template_draft(item, facts, relevance, fmt)
    return _assemble(item, facts, relevance, "article" if fmt == "article" else "post", parts)
