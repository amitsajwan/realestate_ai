"""The radar's sources (docs/RADAR.md §4). Pasted posts (`manual`) come in through the router, not here.
Our own Page and Instagram comments are not a radar source: engage already reads, answers and records them as leads."""
from . import instagram, reddit, rss, youtube

ALL = {m.NAME: m for m in (youtube, reddit, rss, instagram)}
KINDS = {"youtube": ("query", "video"), "reddit": ("subreddit", "query"), "rss": ("feed",), "instagram": ("hashtag",)}
