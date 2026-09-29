"""Work through the public "request an invite" queue.

  python scripts/invite_requests.py list                      # new requests, oldest first
  python scripts/invite_requests.py mark-invited 98765 43210  # after you issued an invite with scripts/invite.py

Run from backend/ with PYTHONPATH=. so `app` imports resolve. Uses the same MONGODB_URL/DATABASE_NAME as the app.
"""
import argparse
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.modules.onboarding.phone import normalize_indian_mobile
from app.modules.waitlist.service import WaitlistService


def format_request(r: dict) -> str:
    when = r["created_at"].strftime("%Y-%m-%d %H:%M UTC") if r.get("created_at") else "?"
    lines = [f"{r['phone']}  {r['name']}  ({r.get('city') or '-'})  {when}"]
    if r.get("message"):
        lines.append(f"    \"{r['message']}\"")
    return "\n".join(lines)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["list", "mark-invited"])
    ap.add_argument("phone", nargs="*", help="Indian mobile number (spaces allowed), for mark-invited")
    args = ap.parse_args()
    svc = WaitlistService(AsyncIOMotorClient(settings.mongodb_url)[settings.database_name], settings.jwt_secret_key)
    if args.action == "list":
        rows = await svc.list_new()
        print("\n".join(format_request(r) for r in rows) if rows else "no new requests")
        return
    if not args.phone:
        ap.error("mark-invited needs a phone number")
    phone = normalize_indian_mobile("".join(args.phone))
    print("marked invited" if await svc.mark_invited(phone) else "no new request found for that number")


if __name__ == "__main__":
    asyncio.run(main())
