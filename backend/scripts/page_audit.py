"""Page-by-page SEO audit: every page Google knows of ours, its clicks, rank, index state, top search and one action (seo.pageaudit).
Read-only: it reads Search Console with the same restricted key the loops use and the stored index checks, and changes nothing.

  sudo docker exec gcp-newsroom-1 sh -c "PYTHONPATH=. python scripts/page_audit.py"                       # summary + top 20
  sudo docker exec gcp-newsroom-1 sh -c "PYTHONPATH=. python scripts/page_audit.py --csv /tmp/audit.csv"  # every page
  sudo docker exec gcp-newsroom-1 sh -c "PYTHONPATH=. python scripts/page_audit.py --bucket seen_far --kind project"

Buckets, in the order to work them: low_ctr, earning, near_page_one, seen_far, too_few, outside_sitemap, indexed_silent,
not_indexed, unchecked. Copy the CSV off the VM with `sudo docker cp` and `gcloud compute scp`.
"""
import argparse
import asyncio
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

COLUMNS = ("path", "kind", "bucket", "clicks", "impressions", "ctr", "position", "impressions_before", "trend", "index_state",
           "in_sitemap", "top_search", "top_search_impressions", "action")


async def _store():
    from app.core.database import get_database, init_database
    from app.modules.newsroom.store import Store
    try:
        return Store(get_database())
    except RuntimeError:  # scripts run outside the app lifespan: connect first
        await init_database()
        return Store(get_database())


def line(r: dict) -> str:
    pos = f"{r['position']:.1f}" if r.get("position") is not None else "-"
    return (f"{r['clicks']:>6} {r['impressions']:>7} {pos:>6}  {r['trend']:<8} {r['bucket']:<16} {r['kind']:<9} {r['path']}"
            + (f"  <- \"{r['top_search']}\"" if r.get("top_search") else ""))


async def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--csv", help="write every row to this file")
    p.add_argument("--bucket")
    p.add_argument("--kind")
    p.add_argument("--limit", type=int, default=20)
    a = p.parse_args(argv)
    from app.modules.seo import pageaudit
    rows = await pageaudit.read(await _store(), datetime.now(timezone.utc))
    if rows is None:
        print("No Search Console key (GSC_SA_KEY_B64) in this container: run it where the newsroom worker runs.")
        return 1
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"{len(rows)} pages written to {a.csv}")
    picked = [r for r in rows if (not a.bucket or r["bucket"] == a.bucket) and (not a.kind or r["kind"] == a.kind)]
    s = pageaudit.summary(picked, a.limit)
    print(f"{s['pages']} pages")
    print("By bucket: " + ", ".join(f"{b} {n}" for b, n in s["by_bucket"].items() if n))
    print("By kind (clicks / impressions / pages per bucket):")
    for kind, c in s["by_kind"].items():
        rest = ", ".join(f"{b} {c[b]}" for b in pageaudit.BUCKETS if c.get(b))
        print(f"  {kind:<10} {c.get('clicks', 0):>6} / {c.get('impressions', 0):>7}   {rest}")
    print(f"\nMost seen {len(s['top'])}:\n{'clicks':>6} {'impr':>7} {'pos':>6}  trend    bucket           kind      path")
    for r in s["top"]:
        print(line(r))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
