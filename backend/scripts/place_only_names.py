"""Registrations named only after their place, in every Pune place: the ones the top lists, prices and web facts cannot join
into one project, because no site prints the name (areastats.pages.place_only_name). Read-only.

  sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/place_only_names.py                 # every place, ours first
  sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/place_only_names.py --place kharadi
  sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/place_only_names.py --all           # sold out and finished too

Lodha files its Kharadi projects as "Kharadi Pune", "Kharadi Pune P1" and "Kharadi Pune P3", and Lodha Camelot's towers as
"Kharadi New Project - Tower N". Each group printed here wants one marketed name (or a confirmed group) set by hand, from the
builder's brochure or site, never guessed. By default only homes a buyer can still buy are listed, as the top lists take them.
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.areas import AREAS  # noqa: E402
from app.modules.areastats import pages  # noqa: E402
from app.modules.areastats.service import _count  # noqa: E402


async def _store():
    from app.core.database import get_database, init_database
    from app.modules.newsroom.store import Store
    try:
        return Store(get_database())
    except RuntimeError:  # scripts run outside the app lifespan: connect first
        await init_database()
        return Store(get_database())


def groups(docs, now: datetime, place=None, every: bool = False) -> dict:
    """{(place, builder): [record, ...]} of the place-only names, each group's records in MahaRERA number order."""
    out: dict = {}
    for d in docs:
        if place and d.get("pune_place") != place:
            continue
        if not d.get("page_slug") or not pages.homes(d) or not pages.place_only_name(d):
            continue
        if not every and not pages.buyable(d, now.date()):
            continue
        key = (d.get("pune_place") or "", pages.builder_key(d) or str(d.get("promoter") or "no promoter"))
        out.setdefault(key, []).append(d)
    order = [a.key for a in AREAS]
    return {k: sorted(v, key=lambda d: d.get("regno") or d["_id"])
            for k, v in sorted(out.items(), key=lambda kv: (kv[0][0] not in order, order.index(kv[0][0]) if kv[0][0] in order else 0, kv[0]))}


async def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--place", help="a Pune place key, e.g. kharadi, upper_kharadi")
    p.add_argument("--all", action="store_true", help="sold out and finished projects too")
    a = p.parse_args(argv)
    store = await _store()
    found = groups(await store.all_projects(), datetime.now(timezone.utc), a.place, a.all)
    if not found:
        print("No registration is named only after its place.")
        return 0
    for (place, builder), docs in found.items():
        homes = sum(_count(d.get("units_total")) or 0 for d in docs)
        print(f"\n{place} · {builder} · {len(docs)} registration{'s' if len(docs) > 1 else ''}, {homes} homes")
        for d in docs:
            print(f"  {d.get('regno') or d['_id']:<18} {d.get('name', '')!s:<45} /projects/{d['page_slug']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
