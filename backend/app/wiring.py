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
    from app.modules.interest import router as interest_routes
    from app.modules.knowledge import grounding
    from app.modules.marketing.content import link_line
    from app.modules.marketing.facts import Facts
    from app.modules.newsroom import quality as news_quality
    from app.modules.photoquality import router as quality_routes
    from app.modules.showcase import samples
    from app.modules.social import router as social_routes
    from app.modules.social import service as social_service
    from app.modules.waitlist import router as waitlist_routes

    # social posts carry the "Listed by" lines and register the Instagram post as a hub item
    social_routes.configure(attribution=attribution_text, on_instagram_published=register_hub_item)
    social_service.configure(link_line=link_line)  # the pack's link line, in marketing's words
    # the quality route: the operator may review any agent's listing cards; calendar and news items are found by their owners
    quality_routes.configure(is_operator=is_operator,
                             resolvers={"calendar": calendar_quality.review_target, "news": news_quality.review_target})
    # the interest hub shows the labelled sample homes while nothing real is published
    interest_routes.configure(sample_entry=samples.catalogue_entry, sample_slugs=samples.catalogue_slugs)
    # grounded answers know the sample homes and the verified evergreen posts; comment replies show listing facts
    grounding.configure(sample_home=samples.get, icon_labels=samples.ICON_LABELS, evergreen_post=calendar_library.BY_SLUG.get)
    # comment replies know which posts are our agent promos (content's rule, calendar.reach)
    engage_service.configure(listing_facts=Facts.from_docs, audience=calendar_reach.audience)
    # a website request to join shows as an alert in the owner's Studio (it waits in Studio > Admin)
    waitlist_routes.configure(on_new_request=_tell_owner_about_invite_request)


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
