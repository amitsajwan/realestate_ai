"""Which insights can our Meta token read? (docs/CONTENT_PLATFORM.md, X-1). Read-only: it never posts, edits or deletes anything.

For the most recent published calendar row of each kind (Instagram reel, Instagram post, Facebook reel, Facebook post) it asks the
Graph API for every candidate metric ONE AT A TIME (a single unknown or retired metric fails the whole request otherwise) and prints
a table: metric, available yes/no, the value or Meta's reason. It also prints the token's permissions when Meta shows them.

  docker compose exec -T -e PYTHONPATH=. backend python scripts/insights_check.py [--write]

--write also saves the table to docs/content/results/insights-check-<date>.md, to paste into docs/META_SETUP.md.
Instagram's 1/3/5 second hold (skip rate) is not in the API: read it in the Instagram app.
The access token is never printed: every message from Meta is cleaned of it before it is shown.
"""
import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# The candidates: names Meta has used for these numbers. Some are retired or renamed; finding out which is the point.
CANDIDATES: Dict[str, Tuple[str, List[str]]] = {
    # target: (endpoint under the object, metrics)
    "instagram reel": ("insights", ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions",
                                    "ig_reels_avg_watch_time", "ig_reels_video_view_total_time", "profile_visits", "follows", "plays"]),
    "instagram post": ("insights", ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions",
                                    "profile_visits", "follows", "impressions"]),
    "facebook reel": ("video_insights", ["blue_reels_play_count", "fb_reels_total_plays", "fb_reels_replay_count",
                                         "post_video_avg_time_watched", "post_video_view_time", "post_impressions_unique",
                                         "post_video_followers", "post_video_social_actions", "post_video_retention_graph",
                                         "total_video_views"]),
    "facebook post": ("insights", ["post_impressions_unique", "post_media_view", "post_clicks", "post_reactions_by_type_total",
                                   "post_activity_by_action_type", "post_impressions"]),
}
Get = Callable[[str, dict], Awaitable[Tuple[int, dict]]]


def clean(text: str, secrets: List[str]) -> str:
    for s in secrets:
        if s:
            text = text.replace(s, "[token]")
    return " ".join(text.split())[:160]


def target_of(row: dict) -> Optional[str]:
    """Which candidate list fits a calendar row. A carousel sent to Facebook as a Reel of its slides counts as a Facebook reel."""
    reel = row.get("kind") == "reel" or (row.get("tags") or {}).get("published_as") == "reel"
    if row.get("channel") == "instagram":
        return "instagram reel" if reel else "instagram post"
    if row.get("channel") == "facebook_page":
        return "facebook reel" if reel else "facebook post"
    return None


def _value(data: dict):
    """The number in one metric's answer (Instagram: values[0].value or total_value.value)."""
    for m in data.get("data") or []:
        if m.get("total_value") is not None:
            return m["total_value"].get("value")
        vals = m.get("values") or []
        if vals:
            return vals[0].get("value")
    return None


async def probe(get: Get, base: str, external_id: str, target: str, token: str) -> List[dict]:
    """One request per metric. Each result: {metric, ok, value, reason}."""
    endpoint, metrics = CANDIDATES[target]
    out = []
    for metric in metrics:
        try:
            status, body = await get(f"{base}/{external_id}/{endpoint}", {"metric": metric, "access_token": token})
        except Exception as e:  # network: report it, never the request (it holds the token)
            out.append({"metric": metric, "ok": False, "value": None, "reason": f"request failed ({type(e).__name__})"})
            continue
        err = (body or {}).get("error")
        if status >= 400 or err:
            out.append({"metric": metric, "ok": False, "value": None,
                        "reason": clean(str((err or {}).get("message") or f"HTTP {status}"), [token])})
            continue
        value = _value(body or {})
        out.append({"metric": metric, "ok": value is not None or bool((body or {}).get("data")), "value": value,
                    "reason": "" if (body or {}).get("data") else "no data returned"})
    return out


async def permissions(get: Get, base: str, token: str) -> List[str]:
    """The token's scopes as Meta reports them (debug_token), or [] when Meta does not say."""
    try:
        status, body = await get(f"{base}/debug_token", {"input_token": token, "access_token": token})
    except Exception:
        return []
    return sorted((body or {}).get("data", {}).get("scopes") or []) if status < 400 else []


def table(results: Dict[str, Tuple[dict, List[dict]]], scopes: List[str]) -> str:
    lines = [f"# Insights check, {date.today().isoformat()}", "",
             "Permissions on the token: " + (", ".join(scopes) if scopes else "not shown by Meta"), ""]
    for target in CANDIDATES:
        if target not in results:
            lines += [f"## {target}", "", "No published post of this kind in the calendar yet.", ""]
            continue
        row, res = results[target]
        lines += [f"## {target}: {row.get('slug')} ({row.get('published_at') or ''})", "", "| metric | available | value | reason |",
                  "|---|---|---|---|"]
        lines += [f"| {r['metric']} | {'yes' if r['ok'] else 'no'} | {'' if r['value'] is None else r['value']} | {r['reason']} |" for r in res]
        lines.append("")
    lines.append("Not in the API: Instagram's 1/3/5 second hold (skip rate). Read it in the Instagram app.")
    return "\n".join(lines) + "\n"


def latest_per_target(rows: List[dict]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for r in sorted(rows, key=lambda r: str(r.get("published_at") or ""), reverse=True):
        t = target_of(r)
        ext = str(r.get("external_id") or "")
        if t and t not in out and ext and not ext.startswith("dryrun_"):
            out[t] = r
    return out


async def run(write: bool) -> int:
    import httpx
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    from app.platform.meta_graph.config import load as load_social

    cfg = load_social()
    if not cfg.page_token:
        print("META_PAGE_ACCESS_TOKEN is not set: nothing to check")
        return 1
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    rows = await db.get_collection("content_calendar").find({"status": "published"}).to_list(5000)
    picks = latest_per_target(rows)
    base = f"https://graph.facebook.com/{cfg.graph_version}"
    async with httpx.AsyncClient(timeout=20) as c:
        async def get(url, params):
            r = await c.get(url, params=params)
            try:
                return r.status_code, r.json()
            except ValueError:
                return r.status_code, {}
        scopes = await permissions(get, base, cfg.page_token)
        results = {t: (row, await probe(get, base, row["external_id"], t, cfg.page_token)) for t, row in picks.items()}
    text = table(results, scopes)
    print(text)
    if write:
        out = BACKEND.parent / "docs" / "content" / "results" / f"insights-check-{date.today().isoformat()}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"saved {out}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true", help="also save the table under docs/content/results/")
    return asyncio.run(run(p.parse_args().write))


if __name__ == "__main__":
    sys.exit(main())
