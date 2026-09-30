"""Dry run of the newsroom on LIVE sources: fetch, filter, extract, draft, check, and print what would reach the review queue.
Writes nothing (no database, no Facebook). Run on the server:
  docker compose exec -T -e PYTHONPATH=. backend python scripts/newsroom_dryrun.py [--max 6]
"""
import argparse
import asyncio
from datetime import datetime, timezone

from app.modules.newsroom import adapters, policy
from app.modules.newsroom.config import load
from app.modules.newsroom.sources import build_sources
from app.modules.newsroom.stages.check import check
from app.modules.newsroom.stages.draft import draft
from app.modules.newsroom.stages.extract import extract
from app.modules.newsroom.stages.filter import assess, same_story
from app.modules.newsroom.stages.read import RobotsCache, polite_get, read


async def main(a) -> None:
    now, llm = datetime.now(timezone.utc), adapters.default_llm()
    get = adapters.make_fetcher()
    rget, robots = polite_get(get, 2.0), RobotsCache()
    items = []
    for src in build_sources(list(load().sources)):
        got = await src.fetch(get)
        print(f"source {src.name}: {len(got)} items")
        items += got
    kept, titles, why = [], [], {}
    for it in items:
        rel = assess(it, now)
        if not rel.keep:
            why[rel.reason] = why.get(rel.reason, 0) + 1
        elif any(same_story(it.title, t) for t in titles):
            why["same story"] = why.get("same story", 0) + 1
        else:
            kept.append((it, rel))
            titles.append(it.title)
    print(f"\n{len(items)} fetched, {len(kept)} relevant. Dropped because: {why}\n")
    shown = 0
    for it, rel in kept:
        if shown >= a.max:
            break
        it = await read(it, rget, robots)  # fetch the article text when the source only gave a headline
        facts = await extract(it, llm)
        if not facts:
            print(f"- {it.title[:80]}: no verifiable facts (headline only)\n")
            continue
        fmt = policy.FORMATS_BY_PILLAR.get(rel.pillar or "", ["post"])[0]
        d = await draft(it, facts, rel, fmt, llm)
        res = check(d, facts, it) if d else None
        shown += 1
        print(f"=== {rel.pillar} / {rel.areas} / {it.source}\n{it.title}\n{it.url}")
        print("CHECK:", "OK" if res and res.ok else (res.problems if res else "no draft"))
        print((d.text if d else "") + "\n")


p = argparse.ArgumentParser()
p.add_argument("--max", type=int, default=6)
asyncio.run(main(p.parse_args()))
