"""Website slug generation: <slug>.domain or /agent/<slug>."""
import re
import unicodedata

RESERVED = {
    "www", "app", "api", "admin", "dashboard", "login", "register", "join",
    "agent", "agents", "static", "assets", "mail", "support", "help", "blog",
    "properties", "property", "listing", "listings", "market", "marketplace",
    "about", "contact", "pricing", "terms", "privacy", "test", "demo",
}
MAX_LEN = 40


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:MAX_LEN].strip("-")


async def unique_slug(collection, *candidates: str) -> str:
    """First free slug from the candidates, then numeric suffixes on the first."""
    bases = [slugify(c) for c in candidates if slugify(c)] or ["agent"]
    for base in bases:
        if len(base) >= 3 and base not in RESERVED and not await collection.find_one({"slug": base}):
            return base
    base = bases[0] if len(bases[0]) >= 3 and bases[0] not in RESERVED else f"agent-{bases[0]}"
    n = 2
    while await collection.find_one({"slug": f"{base}-{n}"}):
        n += 1
    return f"{base}-{n}"
