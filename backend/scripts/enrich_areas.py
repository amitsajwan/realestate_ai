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


def worth_a_buyer(d: dict, now: datetime) -> float:
    """How much a project is what Pune's buyers look for (owner 2026-11-05: "best projects in pune first, that are getting searched,
    possession not near, new launches"): searched for on Google, hot, newly registered, a known brand, a real size."""
    from app.modules.areastats import brands, pages
    registered = pages._day(d.get("registered_on")) or ""
    new = registered >= (now - timedelta(days=365)).date().isoformat()
    return (min(int(d.get("gsc_impressions") or 0), 200) + 2 * int(d.get("hot_score") or 0) + (60 if new else 0)
            + (50 if brands.of(d) else 0) + min(int(d.get("units_total") or 0) / 10, 40))


async def reads_only(parallel: int, limit: int) -> None:
    """Avasetu's read for pages in search that have none; pages with too little to read are passed over."""
    from app.core.database import get_database, init_database
    from app.modules.areastats import budget, enrich, pages
    from app.modules.newsroom.store import Store
    from app.wiring import wire
    await init_database()
    wire()
    store, gate, done = Store(get_database()), asyncio.Semaphore(parallel), {"written": 0, "none": 0}
    docs = [d for d in await store.all_projects() if pages.searchable(d) and enrich.worth_model(d) and not d.get("page_read")
            and sum(1 for f in enrich.read_lines(d, (d.get("fact_sheet") or {}).get("facts") or []) if f["key"] in enrich.READ_SIGNALS) >= enrich.READ_MIN_SIGNALS][:limit]
    print(f"{len(docs)} projects to do", flush=True)

    async def one(doc: dict) -> None:
        async with gate:
            now = datetime.now(timezone.utc)
            llm = await budget.reader(store.db, now)
            read = await enrich.buyer_read(store, doc, enrich._ask(llm, enrich.tier_of(doc), "text"), now)
            done["written" if read else "none"] += 1
    await asyncio.gather(*(one(d) for d in docs))
    print("finished", done, flush=True)


async def facts_only(limit: int) -> None:
    """The code's steps for pages in search that a batch took past them: `main` leaves MahaRERA to the loop, and the loop never
    reaches a place outside our areas, so 336 pages had no place check and no nearby places (2026-11-05). One at a time, because
    MahaRERA is read here, and no model. Safe to run again: a page with the step done is skipped."""
    from app.core.database import get_database, init_database
    from app.modules.areastats import enrich, pages
    from app.modules.newsroom.store import Store
    from app.wiring import wire
    await init_database()
    wire()
    store = Store(get_database())
    docs = [d for d in await store.all_projects() if pages.searchable(d) and not d.get("cluster_primary")
            and not ((d.get("enrichment") or {}).get("steps") or {}).get("places")]
    docs.sort(key=lambda d: -worth_a_buyer(d, datetime.now(timezone.utc)))
    print(f"{len(docs)} projects to do", flush=True)
    done = {"read": 0, "failed": 0}
    for doc in docs[:limit]:
        try:
            await asyncio.wait_for(enrich.enrich_one(store, doc, None, datetime.now(timezone.utc), reread=False), enrich.ROUND_SECONDS)
            await store.set_project(doc["_id"], reading_due=False)   # nothing was put off: this round wanted no model
            done["read"] += 1
            print(doc.get("page_slug"), "read", flush=True)
        except Exception as e:
            done["failed"] += 1
            print(doc.get("page_slug"), "failed", type(e).__name__, flush=True)
    print("finished", done, flush=True)


async def main(areas, places, parallel: int, limit: int, again: bool = False, pune: bool = False, possession_from: str = "", preview: bool = False) -> None:
    from app.core.database import get_database, init_database
    from app.modules.areastats import budget, enrich, pages
    from app.modules.newsroom.store import Store
    from app.wiring import wire
    await init_database()
    wire()
    store, now = Store(get_database()), datetime.now(timezone.utc)

    def wanted(d: dict) -> bool:
        no = d.get("text_refused_at")
        return ((pune or d.get("locality") in areas or d.get("pune_place") in places) and enrich.worth_model(d)
                and str(d.get("completion_now") or "") >= possession_from and not pages.sold_out(d) and d.get("page_slug") and pages.indexable(d) and not pages.is_old(d)
                and (int(d.get("page_text_version") or 1) >= 6 if again
                     else int(d.get("page_text_version") or 1) < enrich.TEXT_VERSION or bool(enrich.outdated(d)))
                and not (isinstance(no, datetime) and now - enrich._aware(no) < timedelta(days=1)))

    # what is in search first; then what buyers are at: homes selling lately, Google's impressions, the newest
    docs = sorted((d for d in await store.all_projects() if wanted(d)),
                  key=lambda d: -worth_a_buyer(d, now) if pune else (not pages.searchable(d), -int(d.get("hot_score") or 0), -int(d.get("gsc_impressions") or 0), -pages.recency(d)))[:limit]
    if preview:
        for d in docs:
            print(round(worth_a_buyer(d, now)), d.get("pune_place") or d.get("locality"), str(d.get("completion_now"))[:7], d.get("units_total"), d.get("gsc_impressions") or 0, d.get("page_slug"))
        return
    print(f"{len(docs)} projects to do", flush=True)
    gate, done = asyncio.Semaphore(parallel), {"written": 0, "not": 0, "failed": 0}

    async def one(doc: dict) -> None:
        async with gate:
            started = datetime.now(timezone.utc)
            try:
                llm = await budget.reader(store.db, started)
                # a page with no fact of its own is read again however lately: a round without search credits found nothing (2026-11-05)
                reread = not enrich.sources_fresh(doc, started) or bool(enrich.outdated(doc)) or not pages.own_facts(doc)
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
    parser.add_argument("--read", action="store_true", help="Avasetu's read for pages in search that have none")
    parser.add_argument("--facts", action="store_true", help="only the code's steps, one at a time, for pages in search that lack them")
    parser.add_argument("--pune", action="store_true", help="all of Pune, what buyers look for first (worth_a_buyer)")
    parser.add_argument("--possession-from", default="", help="filed completion date from this day, 2028-01-01")
    parser.add_argument("--preview", action="store_true", help="list the projects and stop")
    parser.add_argument("--again", action="store_true", help="every page that has points, for a new step that needs no site read again: sizes")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    if args.read:
        asyncio.run(reads_only(args.parallel, args.limit))
    elif args.facts:
        asyncio.run(facts_only(args.limit))
    else:
        asyncio.run(main(set(args.areas), set(args.places), args.parallel, args.limit, args.again, args.pune, args.possession_from, args.preview))
