"""Who reads our pages for AI search, and who comes to us from an AI answer (docs/plan/seo-system.md, "AI search"); since
2026-11-18 every other robot too, by name (`ROBOTS`, then any user agent that calls itself a bot, crawler or spider), so the owner
can see whether Google or something else is reading the site.

Search Console shows Google's clicks only. AI answers (ChatGPT, Perplexity, Copilot, Gemini, Claude) leave two traces we can see:
1. their fetchers in our request log, by user agent (`AGENTS`), in three groups:
   - "answer":   a page read live because someone asked the assistant a question (ChatGPT-User, Perplexity-User, Claude-User):
                 the nearest thing to "we were used in an answer" without paying for their APIs;
   - "search":   crawlers that build the AI search indexes (OAI-SearchBot, PerplexityBot, Claude-SearchBot) and the classic
                 engines they lean on (Bingbot for ChatGPT and Copilot, Googlebot for AI Overviews, Applebot);
   - "training": crawlers that collect text for model training (GPTBot, ClaudeBot, CCBot ...);
   - other robots: "engine" (Yandex, Baidu, DuckDuckGo ...), "seo" (Ahrefs, Semrush ...), "preview" (WhatsApp, Facebook link
     previews), "script" (headless browsers, Lighthouse, python, curl) and "other" (anything else that calls itself a bot).
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

from app.modules.tracking import origin

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
# Every other robot, by name, so we can see who reads the site (owner, 2026-11-18: "we need such visits to understand if google
# crawler or something else is reading our site"). Visitor counts still leave them out (tracking.service drops bots and headless
# browsers); this log is where they show. Google's other readers come first: the URL Inspection tool is Search Console's
# "Test live URL" and "Request indexing".
ROBOTS = (
    ("google-inspectiontool", "Google URL inspection", "search"), ("googleother", "Google (other)", "search"),
    ("storebot-google", "Google Shopping", "search"), ("adsbot-google", "Google Ads", "search"),
    ("yandex", "Yandex", "engine"), ("baiduspider", "Baidu", "engine"), ("duckduckbot", "DuckDuckGo", "engine"),
    ("slurp", "Yahoo", "engine"), ("petalbot", "Petal (Huawei)", "engine"), ("seznambot", "Seznam", "engine"),
    ("ahrefs", "Ahrefs", "seo"), ("semrush", "Semrush", "seo"), ("mj12bot", "Majestic", "seo"), ("dotbot", "Moz", "seo"),
    ("rogerbot", "Moz", "seo"), ("dataforseo", "DataForSEO", "seo"), ("screaming frog", "Screaming Frog", "seo"),
    ("serpstatbot", "Serpstat", "seo"), ("barkrowler", "Babbar", "seo"),
    ("facebookexternalhit", "Facebook / Instagram preview", "preview"), ("whatsapp", "WhatsApp preview", "preview"),
    ("twitterbot", "X preview", "preview"), ("linkedinbot", "LinkedIn preview", "preview"), ("telegrambot", "Telegram preview", "preview"),
    ("slackbot", "Slack preview", "preview"), ("discordbot", "Discord preview", "preview"), ("pinterestbot", "Pinterest preview", "preview"),
    ("chrome-lighthouse", "Lighthouse / PageSpeed", "script"), ("headlesschrome", "Headless browser", "script"),
    ("python", "Python script", "script"), ("curl/", "curl", "script"), ("wget", "wget", "script"), ("scrapy", "Scrapy", "script"),
    ("go-http-client", "Go script", "script"), ("okhttp", "OkHttp script", "script"), ("axios", "Node script", "script"),
    ("node-fetch", "Node script", "script"), ("java/", "Java script", "script"),
)
# an unknown robot that says so ("FooBot/2.1", "some-crawler"): counted under the word it uses
UNKNOWN_ROBOT = re.compile(r"[a-z0-9_.\-]*(?:bot|crawler|spider)[a-z0-9_.\-]*")
MAX_ROBOT_NAME = 30
# referring host (or a parent domain of it) -> assistant, and the utm_source values assistants add to their links: the lead
# sources' list (tracking.origin), so a visit and a lead from one assistant carry the same name
REFERRERS = tuple((host, name) for host, name, _ in origin.AI_REFERRERS)
UTM = {value: origin.AI_NAMES[key] for value, key in origin.AI_UTM.items()}


def classify(ua: Optional[str], referer: Optional[str], utm_source: Optional[str]) -> Optional[dict]:
    """{group, agent} for a request we count, else None (an ordinary visitor)."""
    low = (ua or "").lower()
    if "avasetuseoaudit" in low:
        return None   # our own weekly audit reading pages as the AI fetchers (seo/audit.py)
    for token, name, group in AGENTS + ROBOTS:
        if token in low:
            return {"group": group, "agent": name}
    m = UNKNOWN_ROBOT.search(low)
    if m and not m.group(0).startswith(("cubot", "robotics")):   # a phone model or a word, not a robot
        return {"group": "other", "agent": m.group(0).split("/")[0].strip(".-_")[:MAX_ROBOT_NAME] or "robot"}
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
        {"$inc": inc, "$set": {"day": day, "group": hit["group"], "agent": hit["agent"], "last_at": now,
                               **({"last_path": path} if hit["group"] != "referral" else {})}}, upsert=True)
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
    order = {"answer": 0, "referral": 1, "search": 2, "training": 3, "engine": 4, "seo": 5, "preview": 6, "script": 7, "other": 8}
    out = sorted(agents.values(), key=lambda a: (order.get(a["group"], 9), -a["total"]))
    best = lambda d: [{"path": p, "count": n} for p, n in sorted(d.items(), key=lambda x: (-x[1], x[0]))[:top]]  # noqa: E731
    return {"days": days, "since": since, "agents": out, "answer_pages": best(pages["answer"]),
            "referral_pages": best(pages["referral"]),
            "totals": {g: sum(a["week"] for a in out if a["group"] == g) for g in order}}


ROBOT_GROUPS = ("answer", "search", "training", "engine", "seo", "preview", "script", "other")   # every group but people (referral)
MAX_ROBOTS = 40


async def robots_today(db, now: Optional[datetime] = None) -> dict:
    """Studio → Results, under the visitors (owner, 2026-11-18: "if we see in visitor it will be good"): every robot that read the
    site today (the log's day, UTC, which starts at 5:30 IST), most recent first, with its reads, when it last came and the last
    page it read. People who came from an AI answer are visitors, not robots, so they are not here."""
    now = now or datetime.now(timezone.utc)
    day = now.date().isoformat()
    rows = await db.get_collection(COLLECTION).find({"day": day, "group": {"$in": list(ROBOT_GROUPS)}}).to_list(None)
    def at(r: dict) -> datetime:
        t = r.get("last_at") or datetime.min.replace(tzinfo=timezone.utc)
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    rows.sort(key=at, reverse=True)
    out = [{"agent": r["agent"], "group": r["group"], "reads": int(r.get("count") or 0),
            "last_at": at(r).isoformat().replace("+00:00", "Z"), "last_path": r.get("last_path")} for r in rows[:MAX_ROBOTS]]
    return {"day": day, "reads": sum(int(r.get("count") or 0) for r in rows), "robots": out}


def week_line(s: dict, leads: Optional[Dict[str, int]] = None) -> str:
    """One line for the weekly note: AI answers that read us, visits from AI answers and the leads they brought, last 7 days."""
    t = s.get("totals") or {}
    by = ", ".join(f"{name} {n}" for name, n in sorted((leads or {}).items(), key=lambda x: (-x[1], x[0]))[:3])   # fits the note
    return (f"AI search, 7 days: {t.get('answer', 0):,} pages read for AI answers, {t.get('referral', 0):,} visits and "
            f"{sum((leads or {}).values()):,} enquiries from AI answers{f' ({by})' if by else ''}, "
            f"{t.get('search', 0):,} search-crawler reads.")

