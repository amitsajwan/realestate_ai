"""Starter posts for the PUNE Property Facebook Page.

  python scripts/brand_posts.py preview [--out DIR]     render the cards (no network) and print the captions
  python scripts/brand_posts.py replace                 delete the earlier copies of these posts, then publish the current ones
  python scripts/brand_posts.py instagram [--only slug ...]  publish the same cards to the Instagram account (links become "link in bio"; needs META_IG_BUSINESS_ID;
                                                        Instagram cannot delete posts through the API, so preview first)
  python scripts/brand_posts.py post [--only slug ...]  publish to the Facebook Page for real (needs META_PAGE_ID / META_PAGE_ACCESS_TOKEN,
                                                        PUBLIC_MEDIA_BASE_URL and the cards under <uploads>/brand/)
Posting ignores SOCIAL_DRY_RUN on purpose (agents' listing posts stay in test mode) and records nothing in the database.
Run on the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/brand_posts.py post
"""
import argparse
import asyncio
import os
import re
import sys
from dataclasses import replace
from pathlib import Path

import shutil

from app.modules.marketing.brand_posts import POSTS, STATIC_DIR, render_brand_post
from app.modules.marketing.images import save_jpeg


def render_all(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    for p in POSTS:
        static = STATIC_DIR / f"{p['slug']}.jpg"  # cards needing Devanagari shaping are pre-rendered in Chrome (see frontend/e2e/render-static-cards.js)
        if static.is_file():
            shutil.copyfile(static, out / f"{p['slug']}.jpg")
        else:
            save_jpeg(render_brand_post(p["kicker"], p["title"], p["points"]).img, out / f"{p['slug']}.jpg")
        print(f"rendered {p['slug']}.jpg")


async def delete_old():
    """Delete earlier copies of the starter posts (matched by their exact first caption line; nothing else is touched)."""
    import httpx

    from app.modules.social.config import load

    cfg = load()
    firsts = {p["caption"].split(chr(10))[0] for p in POSTS}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"https://graph.facebook.com/{cfg.graph_version}/{cfg.page_id}/posts",
                        params={"fields": "id,message", "limit": 50, "access_token": cfg.page_token})
        r.raise_for_status()
        for post in r.json().get("data", []):
            if (post.get("message") or "").split(chr(10))[0] in firsts:
                d = await c.delete(f"https://graph.facebook.com/{cfg.graph_version}/{post['id']}", params={"access_token": cfg.page_token})
                print("deleted", post["id"], d.status_code, d.json().get("success"))


IG_LAUNCH = ["welcome", "kharadi-choose", "five-checks", "carpet-area", "kharadi-site-visit", "rera", "kharadi-metro", "agents-problem"]


def ig_caption(caption: str) -> str:
    """Instagram does not make links clickable in captions: point to the bio link instead."""
    return re.sub(r"https?://\S+", "link in our bio", caption)


async def publish_instagram(only):
    from app.modules.social.config import load
    from app.modules.social.graph import GraphPublisher
    from app.modules.social.publisher import Post

    cfg = replace(load(), dry_run=False)
    if not (cfg.ig_id and cfg.page_token and cfg.media_url_ok):
        sys.exit("META_IG_BUSINESS_ID, META_PAGE_ACCESS_TOKEN and an https PUBLIC_MEDIA_BASE_URL are required")
    uploads = Path(os.environ.get("UPLOAD_DIRECTORY", "uploads"))
    render_all(uploads / "brand")
    pub = GraphPublisher(cfg)
    by = {p["slug"]: p for p in POSTS}
    for slug in (only or IG_LAUNCH):
        res = await pub.publish(Post("instagram", ig_caption(by[slug]["caption"]), [f"{cfg.media_base_url}/uploads/brand/{slug}.jpg"]))
        print(f"INSTAGRAM {slug}: {res.permalink or res.external_id}")
        await asyncio.sleep(5)


async def publish(only):
    from app.modules.social.config import load
    from app.modules.social.graph import GraphPublisher
    from app.modules.social.publisher import Post

    cfg = replace(load(), dry_run=False)
    if not (cfg.page_id and cfg.page_token and cfg.media_url_ok):
        sys.exit("META_PAGE_ID, META_PAGE_ACCESS_TOKEN and an https PUBLIC_MEDIA_BASE_URL are required")
    uploads = Path(os.environ.get("UPLOAD_DIRECTORY", "uploads"))
    render_all(uploads / "brand")
    pub = GraphPublisher(cfg)
    for p in POSTS:
        if only and p["slug"] not in only:
            continue
        res = await pub.publish(Post("facebook_page", p["caption"], [f"{cfg.media_base_url}/uploads/brand/{p['slug']}.jpg"]))
        print(f"POSTED {p['slug']}: {res.permalink or res.external_id}")
        await asyncio.sleep(3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preview", "post", "replace", "instagram"])
    ap.add_argument("--out", default="docs/brand/starter-posts")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    if a.mode == "preview":
        render_all(Path(a.out))
        for p in POSTS:
            print(f"\n----- {p['slug']} -----\n{p['caption']}")
    elif a.mode == "instagram":
        asyncio.run(publish_instagram(a.only))
    elif a.mode == "replace":
        asyncio.run(delete_old())
        asyncio.run(publish(a.only))
    else:
        asyncio.run(publish(a.only))
