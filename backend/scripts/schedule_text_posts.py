"""Publish or schedule the text-first posts on the Facebook Page.

  python scripts/schedule_text_posts.py preview
  python scripts/schedule_text_posts.py now  --only pick-your-area
  python scripts/schedule_text_posts.py schedule --first 2026-10-01T10:00:00+05:30 [--every-days 1] [--only slug ...]

Scheduled posts show up in Facebook's Publishing tools -> Scheduled posts, where they can be edited or deleted. Facebook needs them 10 minutes to 30 days ahead.
Run on the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/schedule_text_posts.py schedule --first ...
"""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone

import httpx

from app.modules.marketing.text_posts import TEXT_POSTS
from app.modules.social.config import load
from app.modules.social.publisher import sanitize


def body(p: dict) -> dict:
    text = p["text"].format(link=p["link"]) if p["link"] else p["text"]
    out = {"message": text}
    if p["link"]:
        out["link"] = p["link"]
    return out


async def send(cfg, p: dict, when: datetime = None) -> str:
    data = {**body(p), "access_token": cfg.page_token}
    if when is not None:
        data.update(published="false", scheduled_publish_time=str(int(when.timestamp())))
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"https://graph.facebook.com/{cfg.graph_version}/{cfg.page_id}/feed", data=data)
    j = r.json()
    if r.status_code >= 400 or "error" in j:
        raise SystemExit("Facebook said: " + sanitize((j.get("error") or {}).get("message", str(r.status_code)), [cfg.page_token]))
    return j.get("id", "")


async def main(a) -> None:
    posts = [p for p in TEXT_POSTS if not a.only or p["slug"] in a.only]
    if a.mode == "preview":
        for p in posts:
            print(f"----- {p['slug']} -----\n{body(p)['message']}\n")
        return
    cfg = load()
    cfg = type(cfg)(**{**cfg.__dict__}) if False else cfg
    if a.mode == "now":
        for p in posts:
            print("POSTED", p["slug"], await send(cfg, p))
        return
    first = datetime.fromisoformat(a.first)
    for i, p in enumerate(posts):
        when = first + timedelta(days=i * a.every_days)
        print("SCHEDULED", p["slug"], when.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), await send(cfg, p, when))
        await asyncio.sleep(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preview", "now", "schedule"])
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--first", default="")
    ap.add_argument("--every-days", type=int, default=1)
    asyncio.run(main(ap.parse_args()))
