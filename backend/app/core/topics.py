"""Topics the platform must not answer or promote automatically, shared by the comment and chat bots and the /go hub."""
import os
import re


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def quiet_topic(*texts) -> bool:
    """A topic the bot must not answer (owner 2026-10-20: MHADA comments ask about payments, too risky for an automatic answer): comments
    on it wait for a person, DMs get only a safety line. ENGAGE_QUIET_WORDS (comma separated) replaces the default; "-" turns it off."""
    words = [w.strip() for w in _env("ENGAGE_QUIET_WORDS", "mhada,म्हाडा").split(",") if w.strip() and w.strip() != "-"]
    text = " ".join(t for t in texts if isinstance(t, str)).lower()
    return bool(words) and any(re.search(re.escape(w.lower()), text) for w in words)
