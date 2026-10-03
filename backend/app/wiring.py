"""The composition root: callbacks passed in at startup (docs/ARCHITECTURE.md §2), so that no module imports one above it
(the operator console, or content from buyers). Called once by the route list (app/api/v1/router.py); safe to call again.
"""


def wire() -> None:
    from app.modules.concierge.attribution import attribution_text, register_hub_item
    from app.modules.concierge.config import is_operator
    from app.modules.interest import router as interest_routes
    from app.modules.photoquality import router as quality_routes
    from app.modules.showcase import samples
    from app.modules.social import router as social_routes

    # social posts carry the "Listed by" lines and register the Instagram post as a hub item
    social_routes.configure(attribution=attribution_text, on_instagram_published=register_hub_item)
    # the operator may review any agent's listing cards on the quality route
    quality_routes.configure(is_operator=is_operator)
    # the interest hub shows the labelled sample homes while nothing real is published
    interest_routes.configure(sample_entry=samples.catalogue_entry, sample_slugs=samples.catalogue_slugs)
