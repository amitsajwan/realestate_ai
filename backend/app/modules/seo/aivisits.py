"""Who reads our pages for AI search, and who comes to us from an AI answer (docs/plan/seo-system.md, "AI search").

Search Console shows Google's clicks only. AI answers (ChatGPT, Perplexity, Copilot, Gemini, Claude) leave two traces we can see:
1. their fetchers in our request log, by user agent (`AGENTS`), in three groups:
   - "answer":   a page read live because someone asked the assistant a question (ChatGPT-User, Perplexity-User, Claude-User):
                 the nearest thing to "we were used in an answer" without paying for their APIs;
   - "search":   crawlers that build the AI search indexes (OAI-SearchBot, PerplexityBot, Claude-SearchBot) and the classic
                 engines they lean on (Bingbot for ChatGPT and Copilot, Googlebot for AI Overviews, Applebot);
   - "training": crawlers that collect text for model training (GPTBot, ClaudeBot, CCBot ...).
2. people who click a link in an AI answer: the referring site (`REFERRERS`) or the utm_source the assistant adds
   (ChatGPT adds utm_source=chatgpt.com).
The frontend proxy (frontend/proxy.ts) forwards page requests that may be one of these to POST /internal/seo/visit, a path the
public site never routes to the backend (deploy/gcp/Caddyfile sends only /api, /docs, /openapi.json and /uploads). We count by
day; for answer fetches and AI referrals we keep the pages too (which pages AI answers use). User agents are taken as sent:
no reverse-DNS check, so a spoofed name counts; the numbers are for trends, not proof.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse

COLLECTION = "seo_ai_visits"         # {_id: "<day>|<group>|<agent>", day, group, agent, count, kinds: {page kind: n}, paths: {...}}
KEEP_PATHS = ("answer", "referral")  # groups whose pages we keep
MAX_PATH = 200

# (user agent token, name, group): first match wins, so the specific "-User" fetchers come before their crawlers
AGENTS = (
    ("chatgpt-user", "ChatGPT", "answer"), ("perplexity-user", "Perplexity", "answer"), ("claude-user", "Claude", "answer"),
    ("mistralai-user", "Mistral", "answer"), ("duckassistbot", "DuckDuckGo Assist", "answer"),
    ("oai-searchbot", "ChatGPT search", "search"), ("perplexitybot", "Perplexity", "search"),
    ("claude-searchbot", "Claude search", "search"), ("bingbot", "Bing", "search"), ("googlebot", "Google", "search"),
    ("applebot", "Apple", "search"), ("youbot", "You.com", "search"),
    ("gptbot", "OpenAI training", "training"), ("claudebot", "Anthropic training", "training"), ("ccbot", "Common Crawl", "training"),
    ("google-extended", "Google training", "training"), ("bytespider", "ByteDance", "training"),
    ("meta-externalagent", "Meta", "training"), ("amazonbot", "Amazon", "training"), ("cohere-ai", "Cohere", "training"),
)
# referring host (or a parent domain of it) -> assistant
REFERRERS = (
    ("chatgpt.com", "ChatGPT"), ("chat.openai.com", "ChatGPT"), ("perplexity.ai", "Perplexity"),
    ("copilot.microsoft.com", "Copilot"), ("gemini.google.com", "Gemini"), ("bard.google.com", "Gemini"), ("claude.ai", "Claude"),
    ("you.com", "You.com"), ("phind.com", "Phind"), ("meta.ai", "Meta AI"), ("grok.com", "Grok"), ("chat.deepseek.com", "DeepSeek"),
)
# utm_source values assistants add to their links
UTM = {"chatgpt.com": "ChatGPT", "chatgpt": "ChatGPT", "openai": "ChatGPT", "perplexity": "Perplexity", "perplexity.ai": "Perplexity",
       "copilot": "Copilot", "copilot.com": "Copilot", "gemini": "Gemini", "claude": "Claude", "claude.ai": "Claude"}


def classify(ua: Optional[str], referer: Optional[str], utm_source: Optional[str]) -> Optional[dict]:
    """{group, agent} for a request we count, else None (an ordinary visitor or a bot we do not track)."""
    low = (ua or "").lower()
    if "avasetuseoaudit" in low:
        return None   # our own weekly audit reading pages as the AI fetchers (seo/audit.py)
    for token, name, group in AGENTS:
        if token in low:
            return {"group": group, "agent": name}
    src = UTM.get((utm_source or "").strip().lower())
    if src:
        return {"group": "referral", "agent": src}
    host = (urlparse(referer or "").hostname or "").lower()
    for h, name in REFERRERS:
        if host == h or host.endswith("." + h):
            return {"group": "referral", "agent": name}
    return None


def page_kind(path: str) -> str:
    """Which of our page types a path is, for the counts (never the path itself for crawlers)."""
    p = path or "/"
    for prefix, kind in (("/projects/area/", "area list"), ("/projects/", "project"), ("/localities/", "area guide"),
                         ("/builders/", "builder"), ("/guides/", "guide"), ("/news", "news"), ("/insights", "insight"),
                         ("/2-bhk/", "size"), ("/3-bhk/", "size"), ("/price/", "budget"), ("/agent/", "agent site")):
        if p.startswith(prefix):
            return kind
    return "home" if p == "/" else "other"


def _key(s: str) -> str:
    """A Mongo field name for a path: no dots or dollar signs."""
    return s.replace("%", "%25").replace(".", "%2E").replace("$", "%24")


def _unkey(s: str) -> str:
    return s.replace("%2E", ".").replace("%24", "$").replace("%25", "%")


_PATH = re.compile(r"^/[A-Za-z0-9/_\-.%]*$")


async def record(db, ua: Optional[str], referer: Optional[str], path: Optional[str], utm_source: Optional[str],
                 now: Optional[datetime] = None) -> Optional[dict]:
    """Count one request when it is an AI fetcher or an AI referral; None (nothing stored) otherwise."""
    hit = classify(ua, referer, utm_source)
    path = (path or "/").split("?")[0][:MAX_PATH]
    if hit is None or not _PATH.match(path):
        return None
    now = now or datetime.now(timezone.utc)
    day = now.date().isoformat()
    inc = {"count": 1, f"kinds.{_key(page_kind(path))}": 1}
    if hit["group"] in KEEP_PATHS:
        inc[f"paths.{_key(path)}"] = 1
    await db.get_collection(COLLECTION).update_one(
        {"_id": f"{day}|{hit['group']}|{hit['agent']}"},
        {"$inc": inc, "$set": {"day": day, "group": hit["group"], "agent": hit["agent"], "last_at": now}}, upsert=True)
    return hit


async def summary(db, now: Optional[datetime] = None, days: int = 28, top: int = 10) -> dict:
    """Studio → Insights → Rankings, "AI search": per group and agent, visits in the last 7 and `days` days; the pages AI answers
    read and the pages people reached from AI answers, most first."""
    now = now or datetime.now(timezone.utc)
    since = (now.date() - timedelta(days=days - 1)).isoformat()
    week = (now.date() - timedelta(days=6)).isoformat()
    rows = await db.get_collection(COLLECTION).find({"day": {"$gte": since}}).to_list(None)
    agents: Dict[tuple, dict] = {}
    pages: Dict[str, Dict[str, int]] = {g: {} for g in KEEP_PATHS}
    for r in rows:
        a = agents.setdefault((r["group"], r["agent"]), {"group": r["group"], "agent": r["agent"], "week": 0, "total": 0, "kinds": {}})
        a["total"] += int(r.get("count") or 0)
        if r["day"] >= week:
            a["week"] += int(r.get("count") or 0)
        for k, n in (r.get("kinds") or {}).items():
            a["kinds"][_unkey(k)] = a["kinds"].get(_unkey(k), 0) + int(n)
        for p, n in (r.get("paths") or {}).items():
            if r["group"] in pages:
                pages[r["group"]][_unkey(p)] = pages[r["group"]].get(_unkey(p), 0) + int(n)
    order = {"answer": 0, "referral": 1, "search": 2, "training": 3}
    out = sorted(agents.values(), key=lambda a: (order.get(a["group"], 9), -a["total"]))
    best = lambda d: [{"path": p, "count": n} for p, n in sorted(d.items(), key=lambda x: (-x[1], x[0]))[:top]]  # noqa: E731
    return {"days": days, "since": since, "agents": out, "answer_pages": best(pages["answer"]),
            "referral_pages": best(pages["referral"]),
            "totals": {g: sum(a["week"] for a in out if a["group"] == g) for g in order}}


def week_line(s: dict) -> str:
    """One line for the weekly note: AI answers that read us and visits from AI answers in the last 7 days."""
    t = s.get("totals") or {}
    return (f"AI search, 7 days: {t.get('answer', 0):,} pages read for AI answers, {t.get('referral', 0):,} visits from AI answers, "
            f"{t.get('search', 0):,} search-crawler reads.")

