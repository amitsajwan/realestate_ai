"""The composition root: callbacks passed in at startup (docs/ARCHITECTURE.md §2), so that no module imports one above it
(the operator console, content from buyers or conversations). Called once by the route list (app/api/v1/router.py); safe to call again.
"""
import re


def wire() -> None:
    from app.modules.calendar import library as calendar_library
    from app.modules.calendar import quality as calendar_quality
    from app.modules.calendar import reach as calendar_reach
    from app.modules.calendar import runner as calendar_runner
    from app.modules.concierge.attribution import attribution_text, register_hub_item
    from app.modules.concierge.config import is_operator
    from app.modules.engage import service as engage_service
    from app.modules.inbox import service as inbox_service
    from app.modules.knowledge import grounding
    from app.modules.marketing.content import link_line
    from app.modules.marketing.facts import Facts
    from app.modules.newsroom import quality as news_quality
    from app.modules.photoquality import router as quality_routes
    from app.modules.propertyfacts import run_news
    from app.modules.propertyfacts.brochure_once import sweep as brochure_sweep
    from app.modules.reels import render_job
    from app.modules.showcase import samples
    from app.modules.social import service as social_service
    from app.modules.waitlist import router as waitlist_routes

    social_service.configure(link_line=link_line)  # the pack's link line, in marketing's words
    # a stuck marketing queue shows no error anywhere else; a brochure attached to a listing queues its one read
    render_job.configure(alert=_tell_owner_of_stuck_runs, sweep=brochure_sweep)
    # who hears about an agent's posts: the owner, and the agent on WhatsApp
    run_news.configure(owner=_owner_id, tell=_tell_agent)
    calendar_runner.configure(on_posted=run_news.posted, on_cycle=run_news.results_due)
    inbox_service.configure(ask_post=_ask_agent_about_post)
    # the quality route: the operator may review any agent's listing cards; calendar and news items are found by their owners
    quality_routes.configure(is_operator=is_operator,
                             resolvers={"calendar": calendar_quality.review_target, "news": news_quality.review_target})
    # grounded answers know the sample homes (comments on sample posts published before they were retired, and the demo
    # agent's listings) and the verified evergreen posts; comment replies show listing facts
    grounding.configure(sample_home=samples.get, icon_labels=samples.ICON_LABELS, evergreen_post=calendar_library.BY_SLUG.get)
    # the knowledge index cuts the guide topics and our published posts into passages, read the calendar's way
    from app.modules.calendar import public as calendar_public
    from app.modules.calendar import topics as calendar_topics
    from app.modules.knowledge import index as knowledge_index
    knowledge_index.configure(topics=calendar_topics.load, caption_text=calendar_public._text, caption_title=calendar_public._title)
    # newsroom research gives a story background from our verified area guide (conversations' knowledge)
    from app.modules.newsroom.stages import research as news_research
    news_research.configure(area_facts=_area_guide_facts)
    # comment replies know which posts are our agent promos (content's rule, calendar.reach)
    from app.modules.reels.agent_reels import source_tag as agent_reel_source
    engage_service.configure(listing_facts=Facts.from_docs, audience=calendar_reach.audience, reel_source=agent_reel_source)
    # the radar's review queue is the operator's (concierge owner) until signals are routed to agents
    from app.modules import radar
    radar.configure(is_operator=is_operator)
    # a website request to join shows as an alert in the owner's Studio (it waits in Studio > Admin)
    waitlist_routes.configure(on_new_request=_tell_owner_about_invite_request)

    # a signed-out agent gets a login code on WhatsApp (identity sits below conversations)
    from app.modules.onboarding import router as onboarding_routes
    onboarding_routes.configure(send_code=_send_login_code)

    # the MahaRERA register keeps every agent's builder project fresh, wherever it is (areastats.watch); add other sources here
    from app.modules.areastats import watch as register_watch
    register_watch.add_source("agent_projects", _agent_project_watch)
    # project pages are enriched slowly in the background with the property-facts gatherer (areastats.enrich, PROJECT_ENRICH_*)
    from app.modules.areastats import enrich as project_enrich
    from app.modules.areastats import spotlight
    # the banner picks are enriched first; spotlight sits above enrich (spotlight -> hubs -> enrich), so they come in here
    project_enrich.configure(gather=_gather_project, sheet=_project_sheet, pincode_centre=_pincode_centre, view=_project_view,
                             shown=spotlight.picked_slugs)
    register_watch.add_source("property_facts", _property_facts_watch)  # every project we gathered facts for to market it
    # area maps: pins found by the name a project is sold under (areastats.mappins), through propertyfacts' Google Places client
    from app.modules.areastats import mappins
    mappins.configure(search=_places_search)
    project_enrich.add_daily("map pins", mappins.refresh)
    # builder logos for project pages with no picture of their own (areastats.logos)
    from app.modules.areastats import logos
    project_enrich.add_daily("builder logos", logos.refresh)
    # a street map of where the project is, for pages with no picture (areastats.locmap)
    from app.modules.areastats import locmap
    project_enrich.add_daily("location maps", locmap.refresh)
    # areas by place: a pinned project belongs to the area it is in (areastats.placement, app/core/area_bounds.py)
    from app.modules.areastats import placement
    placement.configure(pin_address=_pin_address)
    project_enrich.add_daily("area placement", placement.refresh)
    # the place a page names must agree with what the sources say (areastats.placecheck, docs/plan/location-checks.md)
    from app.modules.areastats import placecheck
    placecheck.configure(pin_pincodes=_pin_pincodes, forget_place=_forget_place, search=_places_search, keep_pin=_keep_pin,
                         pin_address=_pin_address)
    project_enrich.add_daily("place check", placecheck.refresh)
    # a coming-soon project that has registered is the day we promised its waiting buyers (areastats.upcoming)
    from app.modules.areastats import upcoming
    upcoming.configure(tell=_tell_upcoming_registered)
    project_enrich.add_daily("coming-soon registered", upcoming.refresh)
    # how long each new launch took to be read, in search and indexed (areastats.launches); the index check sits above it
    from app.modules.areastats import launches
    from app.modules.seo import coverage as seo_coverage
    launches.configure(indexed=seo_coverage.indexed_paths)
    project_enrich.add_daily("launch clock", launches.refresh)
    # hot projects (areastats.hot): outside signals beyond MahaRERA, news and Search Console; YouTube is on with YOUTUBE_API_KEY
    from app.modules.areastats import hot as hot_projects
    hot_projects.add_signal("youtube", hot_projects.youtube_signal())
    from app.modules.areastats import websearch
    hot_projects.add_signal("google", websearch.signal())   # Google results through SERPER_API_KEY; off without it
    register_watch.add_source("web_discovered", _web_discovered_watch)   # projects found by number in Google results (areastats.discover)
    # the MahaRERA badge on the pack cards and the walkthrough reel prints only a project number propertyfacts trusts (AR-3)
    from app.modules.marketing import maharera as maharera_badge
    maharera_badge.configure(resolve=_project_registration)
    # deleting a listing (inventory) closes its marketing run and skips its posts not yet out; each owner writes its own
    from app.modules.calendar.store import skip_listing_posts
    from app.modules.listings import service as listing_service
    from app.modules.propertyfacts.jobs import listing_deleted as close_marketing_runs
    listing_service.configure(before_delete=(close_marketing_runs, skip_listing_posts))
    # Ask AI on a listing knows its property-facts sheet and its project page's web facts
    from app.modules.areastats.pages import web_facts_for
    from app.modules.listings import askai
    askai.configure(facts_sheet=_facts_sheet, web_facts=web_facts_for)
    # the AI listing draft matches its project in our MahaRERA register (the newsroom's projects, moving to inventory)
    from app.modules.ai_listing import router as ai_listing_routes
    from app.modules.newsroom.store import Store as NewsroomStore
    ai_listing_routes.configure(register=NewsroomStore, project_start=_project_start)
    # an enquiry on a project page is about the project's area (buyers' lead record reads inventory's project pages)
    from app.modules.tracking import service as tracking_service
    # ...and a new website form lead is told to its agent at once: the Studio badge and, where they turned it on, their phone
    tracking_service.configure(project_area=_project_area, on_new_lead=_new_lead_alert)


async def _send_login_code(phone: str, code: str) -> None:
    from app.modules.whatsapp import config as whatsapp_config
    from app.modules.whatsapp.graph import WhatsAppGraph
    cfg = whatsapp_config.load()
    if not cfg.enabled or cfg.dry_run or not cfg.can_send:  # outside production nothing goes to Meta; the personal code signs in
        raise RuntimeError("WhatsApp is not sending")
    await WhatsAppGraph(cfg).send_login_code(cfg.phone_number_id, phone.lstrip("+"), code)


async def _project_area(db, slug: str):
    from app.modules.areastats.pages import chat_brief

    return ((await chat_brief(db, slug)) or {}).get("area")


async def _new_lead_alert(db, lead: dict) -> None:
    """A new website form lead, told to its agent: what they wrote, never their number (the lead holds it)."""
    from app.modules.notifications.service import notify

    if not lead.get("agent_id") or not lead.get("_id"):
        return
    said = " ".join((lead.get("message") or "").split())
    text = f"{lead.get('name') or 'A buyer'} enquired on your website" + (f': "{said[:120]}"' if said else ".")
    await notify(db, lead["agent_id"], "new_lead", text, {"lead_id": lead["_id"], "screen": f"/studio/leads/{lead['_id']}"},
                 lead.get("created_at"))


async def _tell_upcoming_registered(db, upcoming: dict, project: dict, now) -> None:
    """The owner decides whether it is the same project and what the waiting buyers hear: this sends buyers nothing."""
    import logging
    import re

    from app.modules.concierge.config import owner_ids
    from app.modules.notifications.service import notify

    owners = owner_ids()
    if not owners:
        logging.getLogger(__name__).warning("coming-soon: no CONCIERGE_OWNER_IDS set, so nobody hears that %s registered", upcoming["slug"])
    waiting = await db.get_collection("contacts").count_documents({"message": {"$regex": re.escape(upcoming["name"])}})
    regno = project.get("regno") or project["_id"]
    text = (f"{upcoming['name']} may be registered: {project.get('name')} ({regno}), by {project.get('promoter') or 'an unnamed promoter'}. "
            f"{waiting} waiting on its page. If it is the same project, hide the coming-soon card.")
    for owner in owners:
        await notify(db, owner, "upcoming_registered", text, {"screen": "/studio/leads"}, now=now)


async def _tell_owner_about_invite_request(name: str, city: str) -> None:
    import logging

    from app.core.database import get_database
    from app.modules.concierge.config import owner_ids
    from app.modules.notifications.service import notify

    owners = owner_ids()
    if not owners:
        logging.getLogger(__name__).warning("invite request: no CONCIERGE_OWNER_IDS set, so nobody gets an alert (it waits in Studio > Admin)")
    for owner in owners:
        await notify(get_database(), owner, "invite_request", f"{name} ({city}) asked to join on the website",
                     {"screen": "/studio/admin"})


async def _property_facts_watch():
    """Every project a listing campaign gathered facts for (propertyfacts), for the register's watch list."""
    from app.core.database import get_database
    from app.modules.areastats.watch import WatchItem
    from app.modules.propertyfacts.store import FactsStore

    docs = await FactsStore(get_database()).watched()
    return [WatchItem(d["rera_no"], d.get("maharera_id"), d.get("project_name") or "") for d in docs if d.get("rera_no")]


async def _web_discovered_watch():
    """Every project number seen in Google results and found on MahaRERA (areastats.discover), for the register's watch list."""
    from app.core.database import get_database
    from app.modules.areastats import discover

    return await discover.watch_items(get_database())


async def _agent_project_watch():
    """Every builder project an agent has added (with MahaRERA's id), for the register's watch list: each of the registrations
    a marketed project is sold under (agentprojects.groups), never its unconfirmed candidates."""
    from app.core.database import get_database
    from app.modules.areastats.watch import WatchItem

    docs = await get_database().get_collection("agent_projects").find(
        {"rera_no": {"$exists": True}}, {"rera_no": 1, "maharera_id": 1, "name": 1, "registrations": 1}).to_list(2000)
    out = [WatchItem(d["rera_no"], d.get("maharera_id"), d.get("name", "")) for d in docs if d.get("rera_no")]
    out += [WatchItem(r["regno"], r.get("maharera_id"), f"{d.get('name', '')} {r.get('tower', '')}".strip())
            for d in docs for r in d.get("registrations") or [] if r.get("regno") and r["regno"] != d.get("rera_no")]
    return out


async def _project_registration(db, listing):
    """propertyfacts.advert.for_listing, imported lazily (propertyfacts sits above marketing and reels)."""
    from app.modules.propertyfacts.advert import for_listing

    return await for_listing(db, listing)


async def _project_start(db, regno, agent_id):
    """What a project's page holds for an agent listing it, and whether it is already listed: theirs to open, or by others."""
    from app.modules.areastats import pagestart
    from app.modules.listings import projectlive
    page = await pagestart.listing_start(db, regno)
    if page is None:
        return None
    live = await projectlive.live_for_project(db, regno)
    return {**page, "mine": next((x["_id"] for x in live if x.get("agent_id") == agent_id), None),
            "others": sum(1 for x in live if x.get("agent_id") != agent_id)}


async def _gather_project(db, regno, name, locality, city="Pune", now=None):
    """propertyfacts.enrich.gather_project, imported lazily (propertyfacts sits above areastats)."""
    from app.modules.propertyfacts.enrich import gather_project

    return await gather_project(db, regno, name, locality, city=city, now=now)


def _area_guide_facts(key):
    """An area's fact sentences from our verified guide (knowledge.areas), or none for an area it does not cover."""
    from app.modules.knowledge.areas import AREAS
    return getattr(AREAS.get(key), "facts", ()) or ()


async def _facts_sheet(db, rera_no, project, locality):
    """A listing's property-facts sheet, by MahaRERA number else project + locality (Ask AI's first source)."""
    from app.modules.propertyfacts.store import FactsStore
    return await FactsStore(db).find(rera_no, project, locality)


async def _project_sheet(db, regno):
    """The kept property-facts sheet for a registration number (raw document), for the enrichment's place fill and checks."""
    from app.modules.propertyfacts.store import FactsStore

    return await FactsStore(db).find(regno)


async def _project_view(db, regno):
    """The public view of a project's kept property-facts sheet, for a reading round that does not gather again (areastats.enrich)."""
    from app.modules.propertyfacts.public import view
    from app.modules.propertyfacts.store import FactsStore

    return view(await FactsStore(db).find(regno))


async def _places_search(db, query, centre):
    """Google Places Text Search candidates near a centre, unjudged (propertyfacts.pin.Pins.search); None without a key."""
    from app.core.config import settings
    from app.modules.propertyfacts.pin import Pins

    return await Pins(db, settings.google_maps_api_key).search(query, centre)


async def _pin_address(db, regno):
    """The address Google gave for a project's own pin (propertyfacts keeps the pins), or None."""
    from app.modules.propertyfacts.pin import COLLECTION

    doc = await db.get_collection(COLLECTION).find_one({"_id": regno}) or {}
    return doc.get("address") or None


async def _pin_pincodes(db, regno):
    """Pincodes of Google's place for a project: its pin's address, and a best match refused only for its pincode
    ("not found on Google Maps (pincode 412105, MahaRERA says 411014)")."""
    from app.modules.propertyfacts.pin import COLLECTION

    doc = await db.get_collection(COLLECTION).find_one({"_id": regno}) or {}
    found = re.findall(r"\b(4\d{5})\b", doc.get("address") or "")
    refused = re.findall(r"pincode (\d{6}), MahaRERA says", doc.get("checked") or "")
    return sorted(set(found + refused))


async def _keep_pin(db, regno, place, now):
    """The place the place check found becomes the project's own pin (propertyfacts keeps the pins)."""
    from app.core.config import settings
    from app.modules.propertyfacts.pin import Pins

    await Pins(db, settings.google_maps_api_key).keep(regno, place, now)


async def _forget_place(db, regno):
    """Drop a project's gathered fact sheet (propertyfacts): it was gathered for the old place (its nearby list, its centre)."""
    from app.modules.propertyfacts.store import COLLECTION

    await db.get_collection(COLLECTION).delete_one({"_id": regno})


def _owner_id() -> str:
    from app.modules.engage.config import load

    return load().owner_agent_id or ""


async def _tell_agent(db, wa_id: str, name: str, template: str, params: list, text: str, about: str) -> None:
    from datetime import datetime

    from app.modules.whatsapp.router import build_service

    await build_service(db=db).tell_agent(wa_id, name, template, params, text, about, datetime.utcnow())


async def _ask_agent_about_post(db, wa_id: str) -> bool:
    from app.modules.calendar.store import Store
    from app.modules.propertyfacts import run_news

    return await run_news.ask_by_hand(Store(db), wa_id)


async def _tell_owner_of_stuck_runs(db, summary: str) -> None:
    from app.modules.engage.config import load
    from app.modules.notifications.service import notify

    await notify(db, load().owner_agent_id, "marketing_stuck", summary, {"screen": "/studio"})


async def _pincode_centre(db, pincode):
    """(lat, lon) of an Indian pincode from Nominatim, through the gatherer's shared polite client (1 request a second, cached)."""
    from app.modules.propertyfacts import place
    from app.modules.propertyfacts.enrich import _shared_clients

    rows = await _shared_clients(db).get_json(place.NOMINATIM, {"postalcode": pincode, "country": "India", "format": "jsonv2", "limit": 1})
    try:
        return (float(rows[0]["lat"]), float(rows[0]["lon"])) if rows else None
    except (KeyError, TypeError, ValueError, IndexError):
        return None
