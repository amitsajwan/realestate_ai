"""List the sample-home posts that are still out on our Facebook Page / Instagram, so they can be taken down. Deletes nothing.

  docker compose exec -T -e PYTHONPATH=. backend python scripts/list_sample_posts.py [--csv]

Reads content_calendar: published rows whose caption mentions "sample" (any case) or whose kind is "showcase" (the retired sample
homes). Prints slug, channel, permalink and external_id per row.
Facebook posts can be deleted through the Graph API with the Page token (DELETE /<external_id>); Instagram posts cannot be deleted
through the API, only by hand in the Instagram app (open the permalink, ... > Delete). After deleting, mark the row hidden_from_feed
so the website's posts feed stops showing it.
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path
from typing import List

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

SAMPLE = re.compile(r"sample", re.I)
QUERY = {"status": "published", "$or": [{"caption": {"$regex": "sample", "$options": "i"}}, {"kind": "showcase"}]}


def sample_rows(rows: List[dict]) -> List[dict]:
    """The published rows that show a sample home, oldest first. Pure (the same rule as QUERY)."""
    out = [r for r in rows if r.get("status") == "published" and (r.get("kind") == "showcase" or SAMPLE.search(r.get("caption") or ""))]
    return sorted(out, key=lambda r: (str(r.get("published_at") or ""), r.get("channel", ""), r.get("slug", "")))


def line(r: dict, sep: str = "  ") -> str:
    return sep.join(str(x or "") for x in (r.get("slug"), r.get("channel"), r.get("permalink"), r.get("external_id"),
                                          str(r.get("published_at") or "")[:16], "hidden" if r.get("hidden_from_feed") else ""))


async def run(db, csv: bool = False, say=print) -> List[dict]:
    rows = sample_rows(await db.get_collection("content_calendar").find(QUERY).to_list(None))
    sep = "," if csv else "  "
    say(sep.join(("slug", "channel", "permalink", "external_id", "published_at", "feed")))
    for r in rows:
        say(line(r, sep))
    fb = [r for r in rows if r.get("channel") == "facebook_page"]
    ig = [r for r in rows if r.get("channel") == "instagram"]
    if not csv:
        say(f"\n{len(rows)} published sample post(s): {len(fb)} on Facebook (deletable via Graph: DELETE /<external_id> with the Page "
            f"token), {len(ig)} on Instagram (delete by hand in the app).")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", action="store_true", help="comma-separated output")
    a = ap.parse_args()
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    asyncio.run(run(db, a.csv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
