"""The composition root: callbacks passed in at startup (docs/ARCHITECTURE.md §2), so that no module imports one above it
(the operator console, content from buyers or conversations). Called once by the route list (app/api/v1/router.py); safe to call again.
"""


def wire() -> None:
    from app.modules.calendar import library as calendar_library
    from app.modules.concierge.attribution import attribution_text, register_hub_item
    from app.modules.concierge.config import is_operator
    from app.modules.engage import service as engage_service
    from app.modules.interest import router as interest_routes
    from app.modules.knowledge import grounding
    from app.modules.marketing.facts import Facts
    from app.modules.photoquality import router as quality_routes
    from app.modules.showcase import samples
    from app.modules.social import router as social_routes

    # social posts carry the "Listed by" lines and register the Instagram post as a hub item
    social_routes.configure(attribution=attribution_text, on_instagram_published=register_hub_item)
    # the operator may review any agent's listing cards on the quality route
    quality_routes.configure(is_operator=is_operator)
    # the interest hub shows the labelled sample homes while nothing real is published
    interest_routes.configure(sample_entry=samples.catalogue_entry, sample_slugs=samples.catalogue_slugs)
    # grounded answers know the sample homes and the verified evergreen posts; comment replies show listing facts
    grounding.configure(sample_home=samples.get, icon_labels=samples.ICON_LABELS, evergreen_post=calendar_library.BY_SLUG.get)
    engage_service.configure(listing_facts=Facts.from_docs)
