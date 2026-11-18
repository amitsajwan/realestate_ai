"""Buyer mind settings (docs/plan/buyer-mind.md). Off by default: each brief is several model calls."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    enabled: bool          # BUYER_MIND: think about new leads and buyer replies in the background
    effort: str            # BUYER_MIND_EFFORT: how hard a reasoning model thinks (low / medium / high)
    max_rounds: int        # BUYER_MIND_ROUNDS: rounds of lookups before it must answer


def load() -> Settings:
    effort = (os.environ.get("BUYER_MIND_EFFORT") or "medium").strip().lower()
    try:
        rounds = max(1, min(10, int(os.environ.get("BUYER_MIND_ROUNDS") or 6)))
    except ValueError:
        rounds = 6
    return Settings(enabled=(os.environ.get("BUYER_MIND") or "").strip().lower() in ("1", "true", "on", "yes"),
                    effort=effort if effort in ("low", "medium", "high") else "medium", max_rounds=rounds)
