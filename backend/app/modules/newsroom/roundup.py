"""The monthly MahaRERA post (docs/TASKS.md T1.3, "New on MahaRERA"): the register's projects listed or updated on MahaRERA in our areas in the last 30 days,
as an Instagram carousel (cover, one slide per project, what to check, a closing slide) and a Facebook post with the cover card.

Built on demand (one click in the review screen), as a normal `pending_review` item in the digest format, so the owner approves
it like any other and the existing carousel publishing path sends it. Facts only, all from the register: name, locality,
registration number and MahaRERA's 'Last Modified' date. Never 'new launch' or 'newly registered': we cannot know that. No
promoter opinions, no prices. The text passes the same `check` stage as a story."""
import inspect
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional

from app.core import brand
from app.core.areas import AREAS

from . import codec, policy
from . import presentation as pr
from .digest import _chunk
from .store import Store
from .types import Draft, Fact, Facts, RawItem

log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))
WINDOW_DAYS = 30
MAX_SLIDES = 7  # Instagram allows 10 images: the cover, up to 7 projects, what to check, the closing slide
KIND = "maharera"
TITLE = "Listed or updated on MahaRERA"  # never "new": the only date MahaRERA gives is Last Modified
AREA_NAMES = {a.key: a.name for a in AREAS}
CHECK = ("Open the project on the MahaRERA website and read its approvals, possession date and the promoter's quarterly "
         "updates.")  # the slide's label already says 'Before you decide'


class NothingToPost(Exception):
    """No project in the register was listed or updated on MahaRERA in the window."""


def _date(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=IST)
    except (TypeError, ValueError):
        return None


def _label(d: datetime) -> str:
    return f"{d.day} {pr.MONTHS[d.month - 1]} {d.year}"


def pick(projects: List[dict], now: datetime) -> List[dict]:
    """Projects in our areas whose MahaRERA record was modified in the last WINDOW_DAYS, newest first."""
    since = (now.astimezone(IST) - timedelta(days=WINDOW_DAYS)).date()
    ok = [p for p in projects if p.get("locality") in AREA_NAMES
          and _date(p.get("last_modified", "")) and _date(p["last_modified"]).date() >= since]
    return sorted(ok, key=lambda p: (p["last_modified"], p.get("name", "")), reverse=True)


def _and(names: List[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _snapshot(p: dict) -> dict:
    where = AREA_NAMES.get(p.get("locality", ""), "")
    return {"id": p["_id"], "headline": p["name"], "hook": p["name"],
            "line": f"{where}, pincode {p.get('pincode', '')}. MahaRERA registration number {p['_id']}.",
            "source": "MahaRERA", "as_of": _date(p["last_modified"]), "pillar": "new_supply", "areas": [p.get("locality", "")],
            "url": p.get("source_url", "")}


def compose(projects: List[dict], now: datetime, item_id: str) -> Optional[dict]:
    """The roundup item document (status pending_review, not yet checked), or None when no project qualifies."""
    chosen = pick(projects, now)
    if not chosen:
        return None
    ist = now.astimezone(IST)
    when = _label(ist)
    shown = [_snapshot(p) for p in chosen[:MAX_SLIDES]]
    areas = list(dict.fromkeys(p.get("locality", "") for p in chosen if p.get("locality") in AREA_NAMES))
    where = _and([name for k, name in AREA_NAMES.items() if k in areas])  # in AREAS order
    lines = "\n".join(f"• {p['name']}, {AREA_NAMES.get(p.get('locality', ''), '')} (MahaRERA {p['_id']}), "
                      f"last updated {_label(_date(p['last_modified']))}" for p in chosen)
    n = len(chosen)
    intro = (f"{n} project{'s' if n != 1 else ''} in {where} {'were' if n != 1 else 'was'} "
             f"{policy.MAHARERA_PHRASE} in the last {WINDOW_DAYS} days.")
    question = "Which of these would you like us to look into?"
    text = "\n\n".join([intro, lines, f"What to check: {CHECK}", f"Source: MahaRERA, as of {when}.", question])
    site = pr.site_url()
    link = "/localities"  # a path: captions add the site address when they are built
    # the source text the check compares against: what the register holds for each project, as stated by MahaRERA
    basis = [f"Projects {policy.MAHARERA_PHRASE} in the last {WINDOW_DAYS} days in {where}: {n}."]
    for p in chosen:
        lm = _date(p["last_modified"])
        basis.append(f"{p['name']} ({p['_id']}) in {AREA_NAMES.get(p.get('locality', ''), '')}, pincode {p.get('pincode', '')}, "
                     f"was {policy.MAHARERA_PHRASE}; record last modified {_label(lm)}.")
    basis.append(_chunk(f"What to check: {CHECK}"))  # our own sentence: chunked so it is not read as copied
    raw = RawItem(id=item_id, source="MahaRERA", url=site + link, title="Project register: MahaRERA records in our areas", text="\n".join(basis), published_at=ist, fetched_at=ist)
    facts = Facts([Fact(text=f"{p['name']} was {policy.MAHARERA_PHRASE}.", quote=p["name"]) for p in chosen], as_of=ist)
    draft = Draft("digest", text, TITLE, site + link, ["MahaRERA"])
    more = n - len(shown)
    return {"_id": item_id, "status": "pending_review", "raw": codec.to_doc(raw),
            "relevance": {"keep": True, "pillar": "new_supply", "areas": areas, "reason": f"New on MahaRERA, last {WINDOW_DAYS} days"},
            "facts": codec.to_doc(facts), "draft": codec.to_doc(draft), "check": None,
            "digest": {"kind": KIND, "title": TITLE, "as_of": ist, "tip": CHECK, "items": shown, "link": link,
                       "kicker": f"MAHARERA · LAST {WINDOW_DAYS} DAYS",
                       "meta": f"Facts from MahaRERA · Last {WINDOW_DAYS} days · As of {when}",
                       "cover_line": f"{n} project{'s' if n != 1 else ''}, with {'their' if n != 1 else 'its'} registration number{'s' if n != 1 else ''}"
                                     + (f" (first {len(shown)} here)" if more else ""),
                       "closing_title": "Every project, with its MahaRERA link, on our site",
                       "closing_line": "Tap the link in our bio and open Localities."}}


def _item_id(now: datetime) -> str:
    return f"maharera-{now.astimezone(IST):%Y%m%d-%H%M%S}"


async def _open_roundup(store: Store) -> Optional[dict]:
    for d in await store.queue(100):
        if (d.get("digest") or {}).get("kind") == KIND:
            return d
    return None


async def build(store: Store, now: datetime, checker: Optional[Callable] = None, render: Optional[Callable] = None) -> dict:
    """Make the roundup for the last WINDOW_DAYS. Returns {"doc", "created"}: one still waiting for review is returned as it
    is (a second click never makes a second post). Raises NothingToPost, or ValueError when the text fails its check."""
    waiting = await _open_roundup(store)
    if waiting is not None:
        return {"doc": waiting, "created": False}
    doc = compose(await store.projects.find({}).to_list(None), now, _item_id(now))
    if doc is None:
        raise NothingToPost(f"No project in our areas was {policy.MAHARERA_PHRASE} in the last {WINDOW_DAYS} days")
    if checker is None:
        from .stages.check import check as checker
    res = checker(codec.draft(doc), codec.facts(doc), codec.raw_item(doc))
    res = await res if inspect.isawaitable(res) else res
    if not res.ok:
        log.warning("newsroom: MahaRERA roundup failed its check: %s", "; ".join(res.problems)[:300])
        raise ValueError("The post did not pass the checks: " + "; ".join(res.problems))
    doc["check"] = codec.to_doc(res)
    if render is not None:
        try:
            out = render(doc)
            doc["card"] = await out if inspect.isawaitable(out) else out
        except Exception:  # no card yet: the review screen draws it on demand
            log.warning("newsroom: MahaRERA roundup cards failed", exc_info=True)
    doc["history"] = [{"at": now, "status": "pending_review", "note": f"New on MahaRERA, by {brand.TEAM} owner"}]
    doc["created_at"] = doc["updated_at"] = now
    await store.insert_item(doc)
    return {"doc": doc, "created": True}
