"""Floor plans a target project lacks, collected from the pages that rank for it (owner 2026-10-31: "lets find floor plans";
"its fine if we know floor plan from other site is correct ... if we generate our own").

The profile step (areastats.profile) takes pictures from the builder's own project page only, and stopped reading other sites'
pictures on 2026-10-29 because no page showed them. These are read again here, plans only, for the projects areastats.plans3d
draws (`plans3d.target`) and only when the project has no plan stored: from the project's stored Google results (one search when
it has none), each page checked to be about the project (webfacts.about_project), its pictures named or addressed as a floor
plan (profile.kind_of), downloaded, sized and deduplicated as the profile does. Kept as WebP under
uploads/project_media/<regno>-src/ and on the record as `plan_sources` = {at, plans: [...], read: [{site, url, ok, why}]}; the
`source` is "builder" for the builder's own site, else "web". Never shown as they are: they are what plans3d reads and checks,
and a plan that fails its checks is never drawn. A project with no plan found gets no drawing.
"""
import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import pages, profile, webfacts, websearch

log = logging.getLogger(__name__)

MAX_PAGES = 5                          # pages read for plans
MAX_PLANS = 8                          # plan pictures kept per project
MAX_TRIED = 24                         # pictures downloaded per project, at most


async def collect(store, doc: dict, now: datetime, fetch: Optional[webfacts.Fetch] = None,
                  image: Optional[profile.FetchBytes] = None, search: Optional[websearch.Search] = None,
                  uploads: Path = Path("uploads")) -> dict:
    """{"plan_sources": {...}} for one project record (a group's primary)."""
    fetch = fetch or webfacts.fetch_page
    image = image or profile.fetch_bytes
    name = pages.names(doc)[0]
    regno = str(doc.get("regno") or doc["_id"])
    results = await webfacts.results_for(store, doc, name, search if search is not None else websearch.provider(), now)
    sources = webfacts.sources_for(doc, results, name, limit=webfacts.MAX_TRIES)
    folder = uploads / "project_media" / (re.sub(r"[^A-Za-z0-9]", "", regno).lower() + "-src")
    plans, read, hashes, tried = [], [], [], 0
    for src in sources:
        if sum(1 for r in read if r["why"] != "page not read") >= MAX_PAGES or len(plans) >= MAX_PLANS:
            break
        raw = await fetch(src["url"])
        if not raw:
            read.append({"site": src["site"], "url": src["url"], "ok": False, "why": "page not read"})
            continue
        ok, not_ok = webfacts.about_project(doc, name, webfacts.page_text(raw), src)
        if not ok:
            read.append({"site": src["site"], "url": src["url"], "ok": False, "why": not_ok})
            continue
        found = 0
        for c in profile.candidates(raw, src["url"]):
            if profile.kind_of(c) != "plan" or tried >= MAX_TRIED or len(plans) >= MAX_PLANS:
                continue
            tried += 1
            body = await image(c["url"])
            got = profile.picture(body, "plan") if body else None
            if got is None:
                continue
            im, h = got
            if any(bin(h ^ x).count("1") < profile.NEAR for x in hashes):
                continue
            hashes.append(h)
            folder.mkdir(parents=True, exist_ok=True)
            file = folder / f"{h:016x}.webp"
            await asyncio.to_thread(im.save, file, "WEBP", quality=86, method=4)
            plans.append({"path": file.relative_to(uploads).as_posix(), "width": im.size[0], "height": im.size[1],
                          "alt": f"{name}, from {src['site']}", "image_url": c["url"], "page_url": src["url"], "site": src["site"],
                          "source": "builder" if src["official"] else "web"})
            found += 1
        read.append({"site": src["site"], "url": src["url"], "ok": bool(found), "why": f"{found} plans" if found else "no plan pictures"})
    log.info("planfind: %s %d plans from %d pages", regno, len(plans), len(read))
    return {"plan_sources": {"at": now, "plans": plans, "read": read}}
