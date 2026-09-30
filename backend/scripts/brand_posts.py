"""Starter posts for the PUNE Property Facebook Page.

  python scripts/brand_posts.py preview [--out DIR]     render the cards (no network) and print the captions
  python scripts/brand_posts.py post [--only slug ...]  publish to the Facebook Page for real (needs META_PAGE_ID / META_PAGE_ACCESS_TOKEN,
                                                        PUBLIC_MEDIA_BASE_URL and the cards under <uploads>/brand/)
Posting ignores SOCIAL_DRY_RUN on purpose (agents' listing posts stay in test mode) and records nothing in the database.
Run on the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/brand_posts.py post
"""
import argparse
import asyncio
import os
import sys
from dataclasses import replace
from pathlib import Path

from app.modules.marketing.brand_posts import POSTS, render_brand_post
from app.modules.marketing.images import save_jpeg


def render_all(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    for p in POSTS:
        save_jpeg(render_brand_post(p["kicker"], p["title"], p["points"]).img, out / f"{p['slug']}.jpg")
        print(f"rendered {p['slug']}.jpg")


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
    ap.add_argument("mode", choices=["preview", "post"])
    ap.add_argument("--out", default="docs/brand/starter-posts")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    if a.mode == "preview":
        render_all(Path(a.out))
        for p in POSTS:
            print(f"\n----- {p['slug']} -----\n{p['caption']}")
    else:
        asyncio.run(publish(a.only))
