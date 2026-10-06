"""X-1 (docs/CONTENT_PLATFORM.md): which insights the Graph API returns for our posts with the current Page token. Read-only.

Run on the VM inside the backend container: `python scripts/insights_probe.py`. Prints the token's permissions, then for the
latest Instagram reel, Instagram post, Facebook post and Facebook reel each metric as OK (value) or NO (Meta's reason).
Each metric is asked alone, so one unsupported metric does not hide the others. The token is never printed.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

from app.platform.meta_graph.config import load

cfg = load()
BASE = f"https://graph.facebook.com/{cfg.graph_version}"

IG_REEL = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions", "ig_reels_avg_watch_time",
           "ig_reels_video_view_total_time", "plays", "profile_visits", "follows"]
IG_POST = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions", "profile_visits", "follows"]
FB_POST = ["post_impressions_unique", "post_impressions", "post_media_view", "post_clicks", "post_reactions_by_type_total",
           "post_engaged_users"]
FB_REEL = ["blue_reels_play_count", "fb_reels_total_plays", "post_impressions_unique", "post_video_avg_time_watched",
           "post_video_view_time", "post_video_retention_graph", "post_video_social_actions", "post_video_followers"]


def get(path, **params):
    params["access_token"] = cfg.page_token
    try:
        with urllib.request.urlopen(f"{BASE}/{path}?{urllib.parse.urlencode(params)}", timeout=30) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        try:
            return None, json.load(e).get("error", {}).get("message", str(e))[:140]
        except Exception:
            return None, str(e)


def probe(label, obj_id, path, metrics):
    print(f"\n== {label} {obj_id}")
    for m in metrics:
        data, err = get(f"{obj_id}/{path}", metric=m)
        if err:
            print(f"  NO  {m}: {err}")
            continue
        vals = (data or {}).get("data") or []
        v = vals[0].get("values", [{}])[0].get("value") if vals and vals[0].get("values") else (vals[0].get("total_value") if vals else None)
        print(f"  OK  {m}: {json.dumps(v)[:120] if vals else '(empty)'}")


def main():
    if not cfg.page_token:
        print("META_PAGE_ACCESS_TOKEN is not set")
        return
    dbg, err = get("debug_token", input_token=cfg.page_token)
    d = (dbg or {}).get("data", {})
    print("token:", err or f"type={d.get('type')} valid={d.get('is_valid')} scopes={','.join(d.get('scopes') or [])}")

    if cfg.ig_id:
        media, err = get(f"{cfg.ig_id}/media", fields="id,media_type,media_product_type,timestamp", limit=25)
        items = (media or {}).get("data", [])
        reel = next((x for x in items if x.get("media_product_type") == "REELS"), None)
        post = next((x for x in items if x.get("media_product_type") == "FEED"), None)
        if err:
            print("IG media list:", err)
        if reel:
            probe(f"IG reel {reel['timestamp']}", reel["id"], "insights", IG_REEL)
        if post:
            probe(f"IG post {post['timestamp']}", post["id"], "insights", IG_POST)
    if cfg.page_id:
        posts, err = get(f"{cfg.page_id}/posts", fields="id,created_time", limit=5)
        p = ((posts or {}).get("data") or [None])[0]
        if err:
            print("FB posts list:", err)
        if p:
            probe(f"FB post {p['created_time']}", p["id"], "insights", FB_POST)
        reels, err = get(f"{cfg.page_id}/video_reels", fields="id,created_time", limit=5)
        r = ((reels or {}).get("data") or [None])[0]
        if err:
            print("FB reels list:", err)
        if r:
            probe(f"FB reel {r.get('created_time')}", r["id"], "video_insights", FB_REEL)


if __name__ == "__main__":
    main()
