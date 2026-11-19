"""The rows of Studio's Admin -> Health, gathered in one place: the Health screen shows them and the system watch (below) tells
the owner when one goes wrong, so the screen and the alarm never disagree."""
from datetime import datetime, timezone
from typing import Callable, List, Optional

from . import health
from .service import AdminService


async def health_rows(svc: AdminService, ai_ping: Callable = health.default_ai_ping, ctl: Optional[dict] = None) -> List[dict]:
    """Every Health row, as /admin/overview returns them."""
    from app.modules.calendar.config import load as load_calendar
    from app.modules.engage.config import load as load_engage
    from app.modules.newsroom.config import load as load_newsroom
    from app.platform.meta_graph.config import load as load_social
    from app.modules.whatsapp.config import load as load_wa
    from app.modules.whatsapp.dm_config import load as load_dm
    ctl = ctl if ctl is not None else await svc.controls()
    cal_run, news_run = await svc.run_status("calendar_status"), await svc.run_status("newsroom_status")
    rows = health.build_health(social=load_social(), wa=load_wa(), engage=load_engage(), calendar=load_calendar(), newsroom=load_newsroom(),
                               meta=await svc.meta_status(), cal_run=cal_run, news_run=news_run, controls=ctl,
                               ai=await health.ai_status(ai_ping), dm=load_dm())
    rows += await _seo_rows(svc)
    from app.modules.areastats.websearch import credits, provider
    rows.append(health.search_row(provider() is not None, await credits()))
    rows.append(await _press_row(svc))
    return rows


async def _seo_rows(svc: AdminService) -> list:
    from app.modules.areastats.enrich import POLL_SECONDS as ENRICH_POLL_S
    from app.modules.areastats.enrich import load as enrich_cfg
    from app.modules.areastats.searchconsole import key as gsc_key
    from app.modules.seo import freshness, review
    from app.modules.seo.indexnow import key as indexnow_key
    from app.modules.seo.runner import INTERVAL_S as SEO_INTERVAL_S
    from app.modules.seo.runner import enabled as seo_on
    from app.platform import heartbeats
    names = ["indexnow", "gsc_coverage", "gsc_pages", freshness.MARK, review.MARK]
    marks = {d["_id"]: d for d in await svc.c("newsroom_status").find({"_id": {"$in": names}}).to_list(len(names))}
    beats, now = await heartbeats.read_all(svc.db), datetime.now(timezone.utc)
    from app.modules.areaphotos.config import load as photo_scout_cfg
    from app.modules.areaphotos.runner import INTERVAL_S as PHOTO_SCOUT_INTERVAL_S
    loops = [health.loop_row("seo", "SEO loop", beats.get("seo"), float(SEO_INTERVAL_S) if seo_on() else None, now, "",
                             "rankings, coverage and IndexNow are not being updated"),
             health.loop_row("enrich", "Project page refresh", beats.get("project_enrich"),
                             float(ENRICH_POLL_S) if enrich_cfg().enabled else None, now,
                             "Set PROJECT_ENRICH_ENABLED=true in the server settings",
                             "project pages are not re-read, so their dates and facts go old"),
             health.loop_row("photo_scout", "Photo scout", beats.get("area_photo_scout"),
                             float(PHOTO_SCOUT_INTERVAL_S) if photo_scout_cfg().enabled else None, now,
                             "Set AREA_PHOTO_SCOUT=true in the server settings",
                             "no new Commons photos are suggested for the area guides")]
    from app.modules.communities.discover import COLLECTION as COMMUNITIES
    from app.modules.communities.runner import enabled as articles_on
    hoods = await svc.c(COMMUNITIES).find({}).to_list(None)
    held = sorted((d for d in hoods if not d.get("published") and d.get("write_notes")), key=lambda d: d.get("written_at"), reverse=True)
    articles = {"found": len(hoods), "published": sum(1 for d in hoods if d.get("published")),
                "last_note": f"{held[0]['name']}: {held[0]['write_notes'][0]}" if held else None}
    from app.modules.areastats.pictures import AreaPictures
    from app.modules.areastats.picturesloop import enabled as pictures_on
    pictures_summary = await AreaPictures(svc.db).health_summary()
    return health.seo_rows(indexnow_on=indexnow_key() is not None, gsc_on=gsc_key() is not None, indexnow=marks.get("indexnow"),
                           coverage=marks.get("gsc_coverage"), pages=marks.get("gsc_pages"), articles_on=articles_on(),
                           articles=articles) + [r for r in loops if r] + [
        health.freshness_row(marks.get(freshness.MARK), freshness.WINDOW.days), health.page_check_row(marks.get(review.MARK), now),
        health.pictures_row(pictures_on(), pictures_summary)]


async def _press_row(svc: AdminService) -> dict:
    from app.modules.press.config import load as press_cfg
    from app.modules.press.runner import INTERVAL_S as PRESS_INTERVAL_S
    from app.modules.press.store import Store as PressStore
    from app.platform import heartbeats
    cfg, now = press_cfg(), datetime.now(timezone.utc)
    month = now.strftime("%Y-%m")
    story = await PressStore(svc.db).story(month) if cfg.enabled else None
    beat = (await heartbeats.read_all(svc.db)).get("press") if cfg.enabled else None
    return health.press_row(cfg.enabled, story is not None, beat, PRESS_INTERVAL_S if cfg.enabled else None, now, month)
