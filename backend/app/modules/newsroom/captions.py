"""The exact final captions of an approved item, one per channel, built from the stored draft and the item's facts. Pure functions.

Facebook: short summary, our view and 'what to check' when there is room, the fixed 'Worth checking' buyer line for the pillar
(presentation.buyer_line; English is the only caption language),'Source: X, as of D', a question, 'Read more: <our /news URL>'
(never the source link, which is often a long Google redirect), a few hashtags, the footer. Instagram: the same without any URL
(captions cannot hold links): 'Read more: link in our bio', up to 8 hashtags, the footer. The owner sees these strings before approving and
the publisher sends exactly them. `verify` runs the `check` stage over each final caption, so an edit or a template change can never slip a
number, a name or a link policy problem past the owner."""
from app.core import brand
import inspect
import re
from dataclasses import replace
from typing import Callable, Dict, List, Optional

from . import codec, policy
from . import presentation as pr

FB_MAX = policy.POST_MAX_CHARS  # strictly under, footer included
IG_MAX = policy.POST_MAX_CHARS
DIGEST_MAX = 1800
FB_TAGS, IG_TAGS = 5, 8
CHANNELS = ("facebook", "instagram")


def footer(channel: str) -> str:
    return f"{brand.NAME} · link in our bio" if channel == "instagram" else f"{brand.NAME} · {pr.site_url()}"


def _cut(text: str, room: int) -> str:
    if len(text) <= room:
        return text
    cut = text[:max(room - 1, 0)]
    stop = max(cut.rfind(". "), cut.rfind("? "))
    if stop > room * 0.5:
        return cut[:stop + 1].rstrip()
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > room * 0.5 else cut).rstrip(" ,;:-") + "…"


def _assemble(blocks: List[str], tags: List[str], channel: str, limit: int) -> Optional[str]:
    parts = [b for b in blocks if b] + ([" ".join(tags)] if tags else []) + [footer(channel)]
    text = "\n\n".join(parts)
    return text if len(text) < limit else None


def story(doc: dict, channel: str) -> str:
    p = pr.split_text((doc.get("draft") or {}).get("text", ""))
    name, when = pr.source_name(doc), pr.as_of_label(doc)
    if name:
        src = f"Source: {name}" + (f", as of {when}." if when else ".")
    else:
        src = f"As of {when}." if when else ""
    where = " or ".join(pr.area_names(doc)[:2]) or "Pune"
    q = p.question or f"Does this change how you look at homes in {where}? Tell us in the comments."
    link = f"Read more: {pr.news_url(doc['_id'])}" if channel == "facebook" else "Read more: link in our bio."
    limit = FB_MAX if channel == "facebook" else IG_MAX
    tags = pr.hashtags(doc, FB_TAGS if channel == "facebook" else IG_TAGS)
    view = f"Our view: {p.our_view}" if p.our_view else ""
    chk = f"What to check: {p.what_to_check}" if p.what_to_check else ""
    why = pr.buyer_line(doc)  # fixed house line, after the fact and before the source; kept longer than the draft's own extras
    for blocks in ([p.summary, view, chk, why, src, q, link], [p.summary, view, why, src, q, link], [p.summary, why, src, q, link],
                   [p.summary, src, q, link]):
        got = _assemble(blocks, tags, channel, limit)
        if got:
            return got
    room = limit - len("\n\n".join([src, q, link, " ".join(tags), footer(channel)])) - 10
    return (_assemble([_cut(p.summary, max(room - len(why) - 2, 80)), why, src, q, link], tags, channel, limit)
            or _assemble([_cut(p.summary, max(room, 80)), src, q, link], tags, channel, limit)
            or _assemble([_cut(p.summary, 60), src, q, link], [], channel, limit) or "")


def digest(doc: dict, channel: str) -> str:
    text = (doc.get("draft") or {}).get("text", "").strip()
    dg = doc.get("digest") or {}
    link = f"Read more: {dg.get('link') or pr.site_url() + '/news'}" if channel == "facebook" else "Read more: link in our bio."
    last = "#MahaRERA" if dg.get("kind") == "maharera" else "#PuneNews"
    tags = ["#Pune", brand.HASHTAG, "#Kharadi", "#Wagholi", last][:FB_TAGS if channel == "facebook" else IG_TAGS]
    return _assemble([text, link], tags, channel, DIGEST_MAX) or _assemble([text], [], channel, DIGEST_MAX) or ""


def build(doc: dict) -> Dict[str, str]:
    """{'facebook': text, 'instagram': text}: exactly what will be published."""
    fn = digest if (doc.get("draft") or {}).get("format") == "digest" else story
    return {ch: _no_phones(fn(doc, ch)) for ch in CHANNELS}


def _no_phones(text: str) -> str:
    """Strip anything shaped like a phone number, but never from inside a link (our site address has digits and hyphens)."""
    pieces = re.split(r"(https?://\S+)", text)
    return "".join(p if p.startswith("http") else pr.PHONE.sub("", p) for p in pieces)


async def verify(doc: dict, checker: Optional[Callable]) -> Dict[str, List[str]]:
    """Problems per channel from the check stage run over the final caption (empty lists when clean). No checker: no verdict."""
    out: Dict[str, List[str]] = {ch: [] for ch in CHANNELS}
    if checker is None or not doc.get("draft"):
        return out
    d, facts, raw = codec.draft(doc), codec.facts(doc), codec.raw_item(doc)
    for ch, text in build(doc).items():
        res = checker(replace(d, text=text, title=None), facts, raw)
        res = await res if inspect.isawaitable(res) else res
        out[ch] = [] if res.ok else (list(res.problems) or ["did not pass the checks"])
    return out
