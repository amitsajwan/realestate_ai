"""The composition root: callbacks passed in at startup (docs/ARCHITECTURE.md §2), so that lower modules never import
the operator console. Called once by the route list (app/api/v1/router.py); safe to call again.
"""


def wire() -> None:
    from app.modules.concierge.attribution import attribution_text, register_hub_item
    from app.modules.concierge.config import is_operator
    from app.modules.photoquality import router as quality_routes
    from app.modules.social import router as social_routes

    # social posts carry the "Listed by" lines and register the Instagram post as a hub item
    social_routes.configure(attribution=attribution_text, on_instagram_published=register_hub_item)
    # the operator may review any agent's listing cards on the quality route
    quality_routes.configure(is_operator=is_operator)
