"""Manage pilot invite codes (JOIN_MODE=invite).

  python scripts/invite.py issue 98765 43210 --label "Rahul, Baner"   # prints the code to WhatsApp to the agent
  python scripts/invite.py revoke 9876543210

Run from backend/ with PYTHONPATH=. so `app` imports resolve. Uses the same MONGODB_URL/DATABASE_NAME as the app.
"""
import argparse
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.modules.onboarding.invites import InviteService
from app.modules.onboarding.phone import normalize_indian_mobile


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["issue", "revoke"])
    ap.add_argument("phone", nargs="+", help="Indian mobile number (spaces allowed)")
    ap.add_argument("--label", default="")
    args = ap.parse_args()
    phone = normalize_indian_mobile("".join(args.phone))
    svc = InviteService(AsyncIOMotorClient(settings.mongodb_url)[settings.database_name], settings.jwt_secret_key)
    if args.action == "issue":
        code = await svc.issue(phone, args.label)
        print(f"Invite for {phone}: code {code}\n\nMessage to send:\n"
              f"Welcome! Open {settings.public_site_url.rstrip('/')}/join, enter {phone[3:]} and your personal code {code}. "
              f"Please don't share it.")
    else:
        print("revoked" if await svc.revoke(phone) else "no invite found for that number")


if __name__ == "__main__":
    asyncio.run(main())
