"""Where the platform operates. For the pilot it is Pune only: set ALLOWED_CITIES (comma separated words) to widen it, or to '*' for anywhere."""
import os

DEFAULT = "pune,pimpri,chinchwad,pcmc"
MESSAGE = "PUNE Property lists homes in Pune for now. Please use a Pune city or locality."


def allowed_words() -> list:
    raw = (os.environ.get("ALLOWED_CITIES") or DEFAULT).strip().lower()
    return [w.strip() for w in raw.split(",") if w.strip()]


def check_city(value):
    """Return the city unchanged when it is inside the pilot region (empty stays empty); raise ValueError with a friendly message otherwise."""
    if not value or not isinstance(value, str):
        return value
    words = allowed_words()
    if "*" in words or any(w in value.lower() for w in words):
        return value
    raise ValueError(MESSAGE)
