"""Buyer mind: one thinking agent behind every lead and chat (docs/plan/buyer-mind.md). Owns `lead_briefs` and `buyer_profiles`.
Today: the deep mind's Lead Brief and the buyer profile, run in the background by inbox.followups (through app.wiring, with
BUYER_MIND on) and by hand from Studio's lead page (router.py). The chat's fast mind comes next."""
from .service import BuyerMind, TooSoon, build

__all__ = ["BuyerMind", "TooSoon", "build"]
