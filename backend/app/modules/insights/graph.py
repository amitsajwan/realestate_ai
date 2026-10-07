"""Talking to the Graph API for insights, read-only. Pure apart from the `get` callable it is given (tests pass a fake).

`get(url, params) -> (status, json)`. The access token goes in `params`; it is cleaned out of every message we keep or show.
Meta renames and retires metric names, and one unknown name fails a whole request, so `probe` asks for each candidate alone and
`fetch` asks only for the names that worked last time.
"""
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

Get = Callable[[str, dict], Awaitable[Tuple[int, dict]]]

# target -> (endpoint under the published object, candidate metric names)
CANDIDATES: Dict[str, Tuple[str, List[str]]] = {
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
# Meta's error codes that mean "this token may not read this", not "this metric name is wrong": a person must fix them
PERMISSION_CODES = (10, 190, 200)


def clean(text: str, secrets: List[str]) -> str:
    for s in secrets:
        if s:
            text = text.replace(s, "[token]")
    return " ".join(str(text).split())[:160]


def target_of(row: dict) -> Optional[str]:
    """Which candidate list fits a calendar row. A carousel sent to Facebook as a Reel of its slides counts as a Facebook reel."""
    reel = row.get("kind") == "reel" or (row.get("tags") or {}).get("published_as") == "reel"
    if row.get("channel") == "instagram":
        return "instagram reel" if reel else "instagram post"
    if row.get("channel") == "facebook_page":
        return "facebook reel" if reel else "facebook post"
    return None


def values(body: dict) -> Dict[str, object]:
    """metric name -> value from an insights answer (Instagram: values[0].value or total_value.value)."""
    out: Dict[str, object] = {}
    for m in (body or {}).get("data") or []:
        if m.get("total_value") is not None:
            out[m.get("name")] = m["total_value"].get("value")
        elif m.get("values"):
            out[m.get("name")] = m["values"][0].get("value")
    return out


def _error(status: int, body: dict, token: str) -> Optional[dict]:
    err = (body or {}).get("error")
    if status < 400 and not err:
        return None
    err = err or {}
    return {"reason": clean(str(err.get("message") or f"HTTP {status}"), [token]),
            "permission": err.get("code") in PERMISSION_CODES or status in (401, 403)}


async def probe(get: Get, base: str, external_id: str, target: str, token: str) -> List[dict]:
    """One request per candidate metric. Each result: {metric, ok, value, reason, permission}."""
    endpoint, metrics = CANDIDATES[target]
    out = []
    for metric in metrics:
        try:
            status, body = await get(f"{base}/{external_id}/{endpoint}", {"metric": metric, "access_token": token})
        except Exception as e:  # network: report it, never the request (it holds the token)
            out.append({"metric": metric, "ok": False, "value": None, "reason": f"request failed ({type(e).__name__})", "permission": False})
            continue
        err = _error(status, body, token)
        if err:
            out.append({"metric": metric, "ok": False, "value": None, **err})
            continue
        got = values(body)
        out.append({"metric": metric, "ok": bool((body or {}).get("data")), "value": got.get(metric),
                    "reason": "" if (body or {}).get("data") else "no data returned", "permission": False})
    return out


async def fetch(get: Get, base: str, external_id: str, target: str, metrics: List[str], token: str) -> Tuple[Dict[str, object], Optional[dict]]:
    """(metric -> value, error or None) for the metrics known to work, in one request."""
    endpoint, _ = CANDIDATES[target]
    try:
        status, body = await get(f"{base}/{external_id}/{endpoint}", {"metric": ",".join(metrics), "access_token": token})
    except Exception as e:
        return {}, {"reason": f"request failed ({type(e).__name__})", "permission": False}
    err = _error(status, body, token)
    return ({}, err) if err else (values(body), None)


async def permissions(get: Get, base: str, token: str) -> List[str]:
    """The token's scopes as Meta reports them (debug_token), or [] when Meta does not say."""
    try:
        status, body = await get(f"{base}/debug_token", {"input_token": token, "access_token": token})
    except Exception:
        return []
    return sorted((body or {}).get("data", {}).get("scopes") or []) if status < 400 else []
