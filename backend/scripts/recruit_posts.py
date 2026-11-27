"""Recruiting posts for the agent network on the Avasetu Facebook Page and Instagram (docs/plan/agent-network.md, "Recruiting posts").

  python scripts/recruit_posts.py agents-01                 dry run: prints each platform's caption and image url, posts nothing
  python scripts/recruit_posts.py agents-01 --live          posts for real, once per platform (ledger key recruit:agents-01:<platform>)

Every post goes through social.distribution.send (CLAUDE.md rule 6): a key that is already out is never posted again, and the
owner's posting pause stops it. The image is copied to <uploads>/recruit/ so Meta can fetch it from PUBLIC_MEDIA_BASE_URL.
Run live on the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/recruit_posts.py agents-01 --live
"""
import argparse
import asyncio
import os
import shutil
import sys
from dataclasses import replace
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.social.distribution import send  # noqa: E402
from app.platform.meta_graph.config import load  # noqa: E402
from app.platform.meta_graph.graph import GraphPublisher  # noqa: E402
from app.platform.meta_graph.publisher import DryRunPublisher, Post  # noqa: E402

IMAGES = Path(__file__).resolve().parent / "recruit"

# The audience comes first (agents, not buyers). Only what is live today is claimed; the board is "being built".
POSTS = {
    "agents-01": {
        "image": "agents-01.jpg",
        "alt": "Avasetu agent network: Pune agents buyers can check.One lead board, ask for the buyers that fit you. "
               "Nobody can pay for a higher place. Joining is free.",
        "caption": (
            "For property agents in Pune: most portals sell the top spot. The Avasetu network is the opposite, agents buyers can check.\n\n"
            "What an agent gets today:\n"
            "• Your own page with your name, photo and MahaRERA agent number, checked against the register\n"
            "• Type a project's MahaRERA number and your listing fills itself\n"
            "• Posts and a short video for each listing, sent only after you approve\n"
            "• Our research on the projects you sell\n\n"
            "Being built with our first agents: a lead board of Pune buyers where you ask for the ones that fit you. "
            "Nobody can pay for a higher place.\n\n"
            "Joining is free, any area of Pune. Comment \"Pune\" or message us.\n"
            "avasetu.in/for-agents\n\n"
            "— The Avasetu team\n\n"
            "#Pune #PuneRealEstate #MahaRERA"
        ),
    },
}

CHANNELS = {"facebook": "facebook_page", "instagram": "instagram"}


def ledger_key(slug: str, platform: str) -> str:
    return f"recruit:{slug}:{platform}"


def _db():
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    return AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]


async def run(slug: str, live: bool, platforms) -> None:
    spec = POSTS[slug]
    cfg = replace(load(), dry_run=not live)
    uploads = Path(os.environ.get("UPLOAD_DIRECTORY", "uploads"))
    base = cfg.media_base_url or "https://<PUBLIC_MEDIA_BASE_URL>"
    url = f"{base}/uploads/recruit/{spec['image']}"
    if live:
        if not (cfg.page_id and cfg.ig_id and cfg.page_token and cfg.media_url_ok):
            sys.exit("META_PAGE_ID, META_IG_BUSINESS_ID, META_PAGE_ACCESS_TOKEN and an https PUBLIC_MEDIA_BASE_URL are required")
        (uploads / "recruit").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(IMAGES / spec["image"], uploads / "recruit" / spec["image"])
    publisher = GraphPublisher(cfg) if live else DryRunPublisher()
    db = _db() if live else None
    for platform in platforms:
        post = Post(CHANNELS[platform], spec["caption"], [url], alt_text=spec["alt"] if platform == "instagram" else None)
        key = ledger_key(slug, platform)
        res = await send(db, key, lambda p=post: publisher.publish(p), dry_run=not live,
                         paused_flag="posting_paused" if live else None)
        print(f"{'LIVE' if live else 'DRY RUN'} {key}: {res.permalink or res.external_id}")
        print(f"  image: {url}\n  caption:\n" + "\n".join("    " + line for line in post.text.splitlines()))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("slug", choices=sorted(POSTS))
    ap.add_argument("--live", action="store_true", help="post for real (default: dry run)")
    ap.add_argument("--only", choices=sorted(CHANNELS), nargs="*")
    a = ap.parse_args()
    asyncio.run(run(a.slug, a.live, a.only or ["facebook", "instagram"]))


if __name__ == "__main__":
    main()
