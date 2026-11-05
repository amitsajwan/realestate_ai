"""Enrich the live main projects of some areas at once, several at a time, up to the newest writer (owner 2026-11-04: "multiple in
parallel, use ai no cap, get kharadi, upper kharadi, wagholi main projects done"). Safe to run again: a page on the newest writer
read by the newest steps is skipped, and one refused in the last day too. MahaRERA is not read here (`facts=False`): it stays one read at a time in the loop.

  sudo docker exec -e PYTHONPATH=. gcp-newsroom-1 python scripts/enrich_areas.py --areas kharadi upper_kharadi wagholi --parallel 8
  ... --places hinjawadi wakad baner balewadi tathawade --parallel 8 --limit 100
"""
import argparse
import asyncio
import logging
from datetime import datetime, timedelta, timezone

log = logging.getLogger("enrich_areas")


async def main(areas, places, parallel: int, limit: int, again: bool = False) -> None:
    from app.core.database import get_database, init_database
    from app.modules.areastats import budget, enrich, pages
    from app.modules.newsroom.store import Store
    from app.wiring import wire
    await init_database()
    wire()
    store, now = Store(get_database()), datetime.now(timezone.utc)

    def wanted(d: dict) -> bool:
        no = d.get("text_refused_at")
        return ((d.get("locality") in areas or d.get("pune_place") in places) and enrich.worth_model(d) and d.get("page_slug") and pages.indexable(d) and not pages.is_old(d)
                and (int(d.get("page_text_version") or 1) >= 6 if again
                     else int(d.get("page_text_version") or 1) < enrich.TEXT_VERSION or bool(enrich.outdated(d)))
                and not (isinstance(no, datetime) and now - enrich._aware(no) < timedelta(days=1)))

    # what is in search first; then what buyers are at: homes selling lately, Google's impressions, the newest
    docs = sorted((d for d in await store.all_projects() if wanted(d)),
                  key=lambda d: (not pages.searchable(d), -int(d.get("hot_score") or 0), -int(d.get("gsc_impressions") or 0), -pages.recency(d)))[:limit]
    print(f"{len(docs)} projects to do", flush=True)
    gate, done = asyncio.Semaphore(parallel), {"written": 0, "not": 0, "failed": 0}

    async def one(doc: dict) -> None:
        async with gate:
            started = datetime.now(timezone.utc)
            try:
                llm = await budget.reader(store.db, started)
                reread = not enrich.sources_fresh(doc, started) or bool(enrich.outdated(doc))
                out = await asyncio.wait_for(enrich.enrich_one(store, doc, llm, started, reread=reread, facts=False, rewrite=True), enrich.ROUND_SECONDS)
                done["written" if out["text"] else "not"] += 1
                print(doc.get("page_slug"), "written" if out["text"] else "no text", "|", "; ".join(out["notes"])[:160], flush=True)
            except Exception as e:
                done["failed"] += 1
                print(doc.get("page_slug"), "failed", type(e).__name__, flush=True)

    await asyncio.gather(*(one(d) for d in docs))
    print("finished", done, flush=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("--areas", nargs="*", default=[])
    parser.add_argument("--places", nargs="*", default=[], help="pune_place keys, for places outside our areas")
    parser.add_argument("--parallel", type=int, default=8)
    parser.add_argument("--again", action="store_true", help="every page that has points, for a new step that needs no site read again: sizes")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    asyncio.run(main(set(args.areas), set(args.places), args.parallel, args.limit, args.again))
