"""End-to-end check of the comment assistant against the LIVE Page (run on the server), leaving nothing behind.

It plays the outsider: it posts test comments on one of the Page's own posts through the Graph API, tells the assistant to treat the Page as
someone else for this run (so the comments are not ignored as "own comments"), runs one real cycle, checks what happened on Facebook and in the
database, then deletes every comment, reply and record it created.

  docker compose exec -T -e PYTHONPATH=. backend python scripts/verify_engage_live.py
"""
import asyncio
import sys
from dataclasses import replace

import httpx

from app.core import database as dbmod
from app.modules.ai_listing.llm import default_llm
from app.modules.engage.config import load
from app.modules.engage.graph import EngageGraph
from app.modules.engage.service import EngageService

G = "https://graph.facebook.com/v23.0"
CASES = [("hello you there", "greeting", True), ("INTERESTED", "interested", True), ("Which school is nearby?", "question", True), ("Earn money from home click here www.spam.example", "spam", False)]
ok_all = True


def check(label: str, ok: bool, extra: str = "") -> None:
    global ok_all
    ok_all &= ok
    print(("PASS " if ok else "FAIL ") + label + (f"  {extra}" if extra else ""))


async def main() -> None:
    await dbmod.init_database()
    db = dbmod.get_database()
    cfg = load()
    if not (cfg.page_id and cfg.page_token):
        sys.exit("Meta page settings are missing")
    test_cfg = replace(cfg, page_id="__someone_else__", dry_run=False)  # the Page's own comments now count as an outsider's
    graph = EngageGraph(cfg)  # real Page id and token for every Graph call
    coll = db.get_collection("engage_comments")
    created, reply_ids = [], []
    await coll.delete_many({"from_id": cfg.page_id})  # earlier verification runs must not eat today's per-person cap
    async with httpx.AsyncClient(timeout=30) as c:
        posts = await graph.recent_posts_with_comments()
        post = posts[-1]
        print("using post", post["id"][-8:], "|", (post.get("message") or "")[:40].replace("\n", " "))
        for text, _, _ in CASES:
            r = await c.post(f"{G}/{post['id']}/comments", data={"message": text, "access_token": cfg.page_token})
            check(f"created test comment {text[:22]!r}", r.status_code == 200, str(r.status_code))
            created.append(r.json().get("id"))
        for cid in created:  # the background loop may have seen them first and marked them 'ignored' (own comment): reset so this run decides
            await coll.delete_many({"_id": cid}) if hasattr(coll, "delete_many") else None
        svc = EngageService(db, graph, default_llm(), test_cfg)  # only the 'who is an outsider' rule uses the fake id
        counts = await svc.run_once()
        print("cycle result:", counts)
        docs = {d["_id"]: d for d in await coll.find({"_id": {"$in": created}}).to_list(10)}
        for (text, intent, replied), cid in zip(CASES, created):
            d = docs.get(cid)
            check(f"recorded {text[:22]!r} as {intent}", bool(d) and d["intent"] == intent, f"got {d and d['intent']} / {d and d['status']}")
            if replied:
                check(f"  replied publicly to {text[:22]!r}", bool(d) and d["status"] == "replied" and bool(d["reply_id"]), f"status={d and d['status']} reply={(d or {}).get('reply', '')[:70]!r}")
                if d and d.get("reply_id"):
                    reply_ids.append(d["reply_id"])
                    rr = await c.get(f"{G}/{d['reply_id']}", params={"fields": "message,parent{id}", "access_token": cfg.page_token})
                    check("  the reply exists on Facebook under that comment", rr.status_code == 200 and (rr.json().get("parent") or {}).get("id") == cid)
                    check("  the reply has our link (if it should) and no phone number", (intent == "greeting" or "sslip.io" in d["reply"]) and not __import__("re").search(r"\d{10}", d["reply"]))
            else:
                check(f"  spam was NOT answered", bool(d) and d["status"] == "ignored" and not d.get("reply_id"))
            if intent == "question" and d:
                check("  the question is queued for a person", d["needs_human"] is True, d["reason"])
        again = await svc.run_once()
        check("running again does not reply twice", again in ({}, {"ignored": 0}) or not again.get("replied"), str(again))
        owner = cfg.owner_agent_id
        recent = await svc.recent(owner) if owner else []
        check("the owner's Interest feed can see these", any(d["_id"] in created for d in recent), f"{len(recent)} rows")
        # cleanup: everything this script created
        for rid in reply_ids + created:
            await c.delete(f"{G}/{rid}", params={"access_token": cfg.page_token})
        left = await graph.recent_posts_with_comments()
        remaining = [x for p in left for x in (p.get("comments") or {}).get("data", []) if x["id"] in created + reply_ids]
        check("cleaned up: no test comments remain on the Page", not remaining)
        await coll.delete_many({"_id": {"$in": created}}) if hasattr(coll, "delete_many") else None
    print("\nALL PASSED" if ok_all else "\nSOME FAILED")
    sys.exit(0 if ok_all else 1)


asyncio.run(main())
