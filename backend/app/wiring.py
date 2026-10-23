"""The composition root: callbacks passed in at startup (docs/ARCHITECTURE.md §2), so that no module imports one above it
(the operator console, content from buyers or conversations). Called once by the route list (app/api/v1/router.py); safe to call again.
"""


def wire() -> None:
    from app.modules.calendar import library as calendar_library
    from app.modules.calendar import quality as calendar_quality
    from app.modules.calendar import reach as calendar_reach
    from app.modules.concierge.attribution import attribution_text, register_hub_item
    from app.modules.concierge.config import is_operator
    from app.modules.engage import service as engage_service
    from app.modules.knowledge import grounding
    from app.modules.marketing.content import link_line
    from app.modules.marketing.facts import Facts
    from app.modules.newsroom import quality as news_quality
    from app.modules.photoquality import router as quality_routes
    from app.modules.showcase import samples
    from app.modules.social import service as social_service
    from app.modules.waitlist import router as waitlist_routes

    social_service.configure(link_line=link_line)  # the pack's link line, in marketing's words
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

    # the MahaRERA register keeps every agent's builder project fresh, wherever it is (areastats.watch); add other sources here
    from app.modules.areastats import watch as register_watch
    register_watch.add_source("agent_projects", _agent_project_watch)
    # project pages are enriched slowly in the background with the property-facts gatherer (areastats.enrich, PROJECT_ENRICH_*)
    from app.modules.areastats import enrich as project_enrich
    project_enrich.configure(gather=_gather_project, sheet=_project_sheet, pincode_centre=_pincode_centre)
    register_watch.add_source("property_facts", _property_facts_watch)  # every project we gathered facts for to market it
    # area maps: pins found by the name a project is sold under (areastats.mappins), through propertyfacts' Google Places client
    from app.modules.areastats import mappins
    mappins.configure(search=_places_search)
    project_enrich.add_daily("map pins", mappins.refresh)
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
    ai_listing_routes.configure(register=NewsroomStore)


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


async def _places_search(db, query, centre):
    """Google Places Text Search candidates near a centre, unjudged (propertyfacts.pin.Pins.search); None without a key."""
    from app.core.config import settings
    from app.modules.propertyfacts.pin import Pins

    return await Pins(db, settings.google_maps_api_key).search(query, centre)


async def _pincode_centre(db, pincode):
    """(lat, lon) of an Indian pincode from Nominatim, through the gatherer's shared polite client (1 request a second, cached)."""
    from app.modules.propertyfacts import place
    from app.modules.propertyfacts.enrich import _shared_clients

    rows = await _shared_clients(db).get_json(place.NOMINATIM, {"postalcode": pincode, "country": "India", "format": "jsonv2", "limit": 1})
    try:
        return (float(rows[0]["lat"]), float(rows[0]["lon"])) if rows else None
    except (KeyError, TypeError, ValueError, IndexError):
        return None
