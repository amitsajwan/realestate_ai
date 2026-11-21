"""Answers to post: questions buyers ask about our areas' projects, each with the answer our page already holds and its link, for
the owner to post by hand on Reddit and Quora (docs/plan/visibility-base.md step 1, "Reddit and Quora answers").

Google ranks Reddit and Quora threads at the top of "is <project> delayed" and "<project> possession" questions, where our young
site does not show yet; an honest answer there, disclosed as Avasetu, with the one page that holds the facts, brings buyers and
mentions without waiting for Google's trust. Nothing here is written by a model: the questions are Google's "People also ask"
(kept per project as `seo_faq` by the page doctor, seo.questions), and every answer is the code-written one from MahaRERA and the
checked web facts that the page itself shows. Nothing is posted from here (rule 6): the owner finds a thread with the search
links, edits the draft in their own words and posts it.

`to_post(projects, site, now)` -> up to MAX items, one per project, rotated week by week so the list changes every Monday.
"""
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

from app.core.areas import BY_KEY
from app.modules.areastats.pages import names, searchable

MAX = 10
# what people ask in threads, first: a delay or a builder's record starts a thread; a pincode does not
TOPIC_ORDER = ("possession", "oc", "booked", "builder", "rera", "size", "location")
DISCLOSE = "(I'm with Avasetu, which reads MahaRERA records for Pune projects.)"


def _shown(doc: dict) -> str:
    return doc.get("search_name") or doc.get("group_name") or names(doc)[0] or doc.get("name") or ""


def pick(doc: dict) -> Optional[dict]:
    """The project's question people most likely ask in a thread, by topic; None when its page answers none of them."""
    faq = [f for f in doc.get("seo_faq") or [] if f.get("q") and f.get("a") and f.get("topic") in TOPIC_ORDER]
    if not faq:
        return None
    return min(faq, key=lambda f: TOPIC_ORDER.index(f["topic"]))


def draft(answer: str, url: str) -> str:
    """The post: the answer as the page says it, the page for the rest, and who we are. The owner rewrites it to fit the thread."""
    return f"{answer}\n\nThe dates, homes booked and the MahaRERA record are on this page: {url}\n\n{DISCLOSE}"


def to_post(projects: List[dict], site: str, now: datetime, limit: int = MAX) -> List[Dict]:
    """Projects in our areas whose page is in search and answers a buyer's question, the most homes first (the ones most people
    are buying into), then this week's turn of that list, so the owner gets new ones each Monday and every project comes round."""
    site = site.rstrip("/")
    found = []
    for d in projects:
        area = BY_KEY.get(d.get("locality") or "")
        if not area or not d.get("page_slug") or not searchable(d, now):
            continue
        f = pick(d)
        if f is None:
            continue
        found.append((d, area, f))
    found.sort(key=lambda x: (-(x[0].get("units_total") or 0), x[0].get("page_slug")))
    if not found:
        return []
    start = (now.isocalendar()[1] * limit) % len(found)
    turn = (found[start:] + found[:start])[:limit]
    out = []
    for d, area, f in turn:
        shown = _shown(d)
        url = f"{site}/projects/{d['page_slug']}?src=answer"
        out.append({
            "project": shown, "area": area.name, "regno": d.get("regno") or d["_id"], "topic": f["topic"],
            "question": f["q"], "answer": f["a"], "source": f.get("source"), "page": url, "draft": draft(f["a"], url),
            # where to find a thread that asks it: Reddit's r/pune and Quora, searched for the project's name
            "find": {
                "reddit": f"https://www.reddit.com/r/pune/search/?q={quote_plus(shown)}",
                "quora": f"https://www.quora.com/search?q={quote_plus(shown + ' ' + area.name)}",
            },
        })
    return out
