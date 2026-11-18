"""Buyer mind: one thinking agent behind every lead and chat (docs/plan/buyer-mind.md). Today: the deep mind's Lead Brief and
the buyer profile, run by hand (BuyerMind.think); the background run, the chat's fast mind and Studio come next."""
from .service import BuyerMind, build

__all__ = ["BuyerMind", "build"]
