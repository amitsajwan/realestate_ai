"""What people search around our areas and projects, and where our site ranks for it (areastats.demand). Read-only.

  sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/demand_report.py                 # top 30 phrases
  sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/demand_report.py --rising        # only rising ones
  sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/demand_report.py --area kharadi --kind project
  sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/demand_report.py --missing       # numbers not found on MahaRERA

Columns: impressions in 28 days (and the 28 days before), Google position from Search Console, our place in the results of the
searches we run (- = not in the top 10), the phrase's kind and area or project, and where it came from.
"""
import argparse
import asyncio
import sys


async def _store():
    from app.core.database import get_database, init_database
    from app.modules.newsroom.store import Store
    try:
        return Store(get_database())
    except RuntimeError:  # scripts run outside the app lifespan: connect first
        await init_database()
        return Store(get_database())


def line(t: dict) -> str:
    g = t.get("gsc") or {}
    imp = f"{g.get('impressions', 0)}" + (f" ({t['gsc_prev']})" if t.get("gsc_prev") is not None else "")
    pos = f"{g['position']:.1f}" if g.get("position") else "-"
    rank = (t.get("rank") or {}).get("position")
    where = t.get("regno") or t.get("area") or ""
    up = " RISING" if t.get("rising") else ""
    return f"{imp:>12}  {pos:>5}  {rank if rank else '-':>4}  {t['kind']:<7} {where:<16} {t['phrase']}  [{', '.join(t.get('sources') or [])}]{up}"


async def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--rising", action="store_true")
    p.add_argument("--area")
    p.add_argument("--kind", choices=["project", "area", "topic"])
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--missing", action="store_true", help="project numbers seen in Google results that MahaRERA search did not find")
    a = p.parse_args(argv)
    from app.modules.areastats import demand, discover
    store = await _store()
    if a.missing:
        rows = await discover.pending(store)
        for r in rows:
            print(f"{r['regno']}: tried {', '.join(r['tried_names'] or [])}; seen in: {'; '.join(s.get('title', '') for s in r['seen'])}")
        print(f"{len(rows)} number(s) need a person: find the project on MahaRERA and add it with areastats.watch")
        return 0
    rows = await demand.top(store, kind=a.kind, area=a.area, rising_only=a.rising, limit=a.limit)
    print(f"{'impr (prev)':>12}  {'gpos':>5}  {'rank':>4}  kind    area/project     phrase  [sources]")
    for t in rows:
        print(line(t))
    print(f"{len(rows)} phrase(s)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
