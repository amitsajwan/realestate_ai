"""Settings for the photo scout (docs/plan/area-pictures.md step 4), read from the environment in one place per rule 5 of
CLAUDE.md. Off until the owner sets AREA_PHOTO_SCOUT=true: it spends Gemini budget and downloads from Wikimedia Commons."""
import os
from dataclasses import dataclass

TRUE = ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    enabled: bool = False
    max_judged_per_area: int = 30     # candidates judged per area per round
    max_judged_per_day: int = 120     # across every area, one worker cycle
    max_suggested_per_area: int = 8   # kept suggestions per area; the guide itself shows up to PUBLIC_MAX (service.py)
    round_days: int = 7               # how often one area gets a fresh round
    min_live_and_suggested: int = 4   # fewer than this live+suggested and the area gets a gap nudge
    gap_notify_days: int = 30         # at most one nudge per area this often
    flag_uploads_per_cycle: int = 10  # agent uploads vision-checked (flagged, never rejected) per cycle


def load() -> Config:
    return Config(enabled=(os.environ.get("AREA_PHOTO_SCOUT") or "").strip().lower() in TRUE)
