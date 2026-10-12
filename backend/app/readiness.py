"""What the marketing pipeline can do on this server, logged once at start (API and worker), one line per dependency:

    pipeline=startup ref=- step=voice outcome=skipped reason="GOOGLE_TTS_API_KEY is not set" effect="reels are music only"

So "why did my reel have no voice-over?" is answered by the first lines of the log, before any job runs. Settings are read,
never logged: each check says only whether the setting is there."""
import logging
import os
from typing import List, Tuple

from app.platform import trace

log = logging.getLogger("app.readiness")

Check = Tuple[str, str, str, str]   # (step, outcome, reason, effect when not ok)


def checks() -> List[Check]:
    from app.modules.calendar.config import load as load_calendar
    from app.modules.reels import ffmpeg, voice
    from app.platform.llm import groq_api_key
    from app.platform.meta_graph.config import load as load_social

    out: List[Check] = []
    out.append(("ffmpeg", trace.OK, "", "") if ffmpeg.available() else
               ("ffmpeg", trace.FAILED, "ffmpeg did not start (imageio-ffmpeg)", "no reel can be made"))
    out.append(("voice", trace.OK, "GOOGLE_TTS_API_KEY is set", "") if voice.available() else
               ("voice", trace.SKIPPED, "GOOGLE_TTS_API_KEY is not set", "reels are music only, no voice-over"))
    out.append(("llm", trace.OK, "LLM key is set", "") if groq_api_key() else
               ("llm", trace.SKIPPED, "AI_LLM_API_KEY / GROQ_API_KEY is not set", "scripts and captions come from the rules"))
    music_on = os.environ.get("REEL_BRAND_MUSIC", "on").strip().lower() != "off"
    out.append(("music", trace.OK, "", "") if music_on else
               ("music", trace.SKIPPED, "REEL_BRAND_MUSIC=off", "voiceless reels are silent"))
    social = load_social()
    if social.dry_run:
        out.append(("social", trace.SKIPPED, "SOCIAL_DRY_RUN is on", "posts are marked published but nothing is sent"))
    else:
        missing = [name for name, ok in (("META_PAGE_ID + META_PAGE_ACCESS_TOKEN", social.configured("facebook_page")),
                                         ("META_IG_BUSINESS_ID", social.configured("instagram")),
                                         ("PUBLIC_MEDIA_BASE_URL (https)", social.media_url_ok)) if not ok]
        out.append(("social", trace.OK, "live", "") if not missing else
                   ("social", trace.FAILED, "missing " + ", ".join(missing), "posts on those channels fail"))
    out.append(("calendar", trace.OK, "", "") if load_calendar().enabled else
               ("calendar", trace.SKIPPED, "CALENDAR_ENABLED is off", "approved posts are not sent"))
    return out


def log_readiness(where: str) -> None:
    """One line per check. Never raises: a broken check is logged and the process starts anyway."""
    try:
        for step, outcome, reason, effect in checks():
            trace.event(log, "startup", where, step, outcome, reason=reason or None, effect=effect or None)
    except Exception:
        log.exception("readiness checks failed")
