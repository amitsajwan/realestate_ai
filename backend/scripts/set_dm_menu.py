"""Set the Page's DM starter buttons (ice breakers) on Messenger and Instagram (docs/plan/project-check.md).

A tapped button arrives as a postback whose title is what the person "said" (whatsapp/dms.parse), so each title is worded for the
brain: the first starts the project check (whatsapp/check_flow.starts).

  python -m scripts.set_dm_menu            # show what is set now
  python -m scripts.set_dm_menu --apply    # set the buttons on both

Uses META_PAGE_ACCESS_TOKEN (the Page token, in the Authorization header) and the Graph version from the DM config.
"""
import argparse
import asyncio
import json

import httpx

from app.modules.whatsapp.dm_config import load
from app.modules.whatsapp.dm_graph import GRAPH_HOST

BUTTONS = [
    ("🔍 Check my project's MahaRERA status", "CHECK_PROJECT"),
    ("🏠 I'm looking for a home in Pune", "HOMES"),
    ("💼 I'm a real estate agent", "AGENT"),
]
FIELDS = "ice_breakers"


def body() -> dict:
    return {"ice_breakers": [{"locale": "default", "call_to_actions": [{"question": q, "payload": p} for q, p in BUTTONS]}]}


async def main(apply: bool) -> None:
    cfg = load()
    if not cfg.page_token:
        raise SystemExit("META_PAGE_ACCESS_TOKEN is not set")
    url = f"{GRAPH_HOST}/{cfg.graph_version}/me/messenger_profile"
    headers = {"Authorization": f"Bearer {cfg.page_token}"}
    async with httpx.AsyncClient(timeout=20) as client:
        for platform in ("messenger", "instagram"):
            params = {"fields": FIELDS} | ({"platform": "instagram"} if platform == "instagram" else {})
            now = (await client.get(url, params=params, headers=headers)).json()
            print(f"{platform} now: {json.dumps(now, ensure_ascii=False)}")
            if apply:
                extra = {"platform": "instagram"} if platform == "instagram" else {}
                res = (await client.post(url, params=extra, json=body(), headers=headers)).json()
                print(f"{platform} set: {json.dumps(res, ensure_ascii=False)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    asyncio.run(main(ap.parse_args().apply))
