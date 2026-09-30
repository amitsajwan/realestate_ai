"""Source plugins and the registry that maps NEWSROOM_SOURCES names to instances."""
from typing import Dict, List, Optional, Sequence, Tuple

from app.modules.newsroom.sources.google_news import GoogleNewsSource
from app.modules.newsroom.sources.maharera import MahaReraSource
from app.modules.newsroom.sources.publishers import PublishersSource
from app.modules.newsroom.sources.rss import RssSource
from app.modules.newsroom.types import Source


def build_sources(names: List[str], rss_feeds: Optional[Sequence[Tuple[str, str]]] = None) -> List[Source]:
    """Instances for the known names (google_news, maharera, publishers, rss), in the order given, each once.
    Unknown names are ignored. `rss` fetches nothing unless given (name, url) pairs via `rss_feeds`."""
    factories: Dict[str, object] = {
        "google_news": lambda: GoogleNewsSource(),
        "maharera": lambda: MahaReraSource(),
        "publishers": lambda: PublishersSource(),
        "rss": lambda: RssSource(rss_feeds or ()),
    }
    out: List[Source] = []
    seen = set()
    for raw in names or []:
        name = (raw or "").strip().lower()
        if name in seen or name not in factories:
            continue
        seen.add(name)
        out.append(factories[name]())
    return out
