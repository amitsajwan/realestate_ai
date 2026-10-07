"""Which insights can our Meta token read? (docs/CONTENT_PLATFORM.md, X-1). Read-only: it never posts, edits or deletes anything.

Optional: the worker's insights collector (app/modules/insights) finds this out by itself and tells the owners when a permission is
missing. This script is for looking at the same answer by hand, on demand.

For the most recent published calendar row of each kind (Instagram reel, Instagram post, Facebook reel, Facebook post) it asks the
Graph API for every candidate metric ONE AT A TIME (a single unknown or retired metric fails the whole request otherwise) and prints
a table: metric, available yes/no, the value or Meta's reason. It also prints the token's permissions when Meta shows them.

  docker compose exec -T -e PYTHONPATH=. backend python scripts/insights_check.py [--write]

--write also saves the table to docs/content/results/insights-check-<date>.md, to paste into docs/META_SETUP.md.
Instagram's 1/3/5 second hold (skip rate) is not in the API: read it in the Instagram app.
The access token is never printed: every message from Meta is cleaned of it before it is shown.
"""
import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.insights.graph import CANDIDATES, permissions, probe, target_of  # noqa: E402  (one copy: the collector's)


def table(results: Dict[str, Tuple[dict, List[dict]]], scopes: List[str]) -> str:
    lines = [f"# Insights check, {date.today().isoformat()}", "",
             "Permissions on the token: " + (", ".join(scopes) if scopes else "not shown by Meta"), ""]
    for target in CANDIDATES:
        if target not in results:
            lines += [f"## {target}", "", "No published post of this kind in the calendar yet.", ""]
            continue
        row, res = results[target]
        lines += [f"## {target}: {row.get('slug')} ({row.get('published_at') or ''})", "", "| metric | available | value | reason |",
                  "|---|---|---|---|"]
        lines += [f"| {r['metric']} | {'yes' if r['ok'] else 'no'} | {'' if r['value'] is None else r['value']} | {r['reason']} |" for r in res]
        lines.append("")
    lines.append("Not in the API: Instagram's 1/3/5 second hold (skip rate). Read it in the Instagram app.")
    return "\n".join(lines) + "\n"


def latest_per_target(rows: List[dict]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for r in sorted(rows, key=lambda r: str(r.get("published_at") or ""), reverse=True):
        t = target_of(r)
        ext = str(r.get("external_id") or "")
        if t and t not in out and ext and not ext.startswith("dryrun_"):
            out[t] = r
    return out


async def run(write: bool) -> int:
    import httpx
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    from app.platform.meta_graph.config import load as load_social

    cfg = load_social()
    if not cfg.page_token:
        print("META_PAGE_ACCESS_TOKEN is not set: nothing to check")
        return 1
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    rows = await db.get_collection("content_calendar").find({"status": "published"}).to_list(5000)
    picks = latest_per_target(rows)
    base = f"https://graph.facebook.com/{cfg.graph_version}"
    async with httpx.AsyncClient(timeout=20) as c:
        async def get(url, params):
            r = await c.get(url, params=params)
            try:
                return r.status_code, r.json()
            except ValueError:
                return r.status_code, {}
        scopes = await permissions(get, base, cfg.page_token)
        results = {t: (row, await probe(get, base, row["external_id"], t, cfg.page_token)) for t, row in picks.items()}
    text = table(results, scopes)
    print(text)
    if write:
        out = BACKEND.parent / "docs" / "content" / "results" / f"insights-check-{date.today().isoformat()}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"saved {out}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true", help="also save the table under docs/content/results/")
    return asyncio.run(run(p.parse_args().write))


if __name__ == "__main__":
    sys.exit(main())
