"""MongoDB indexes for the v2 collections. Created at startup (idempotent); a failure to create one index is logged and
never stops the app (e.g. legacy duplicate data blocking a unique index)."""
import logging
from typing import Iterable, Tuple

logger = logging.getLogger(__name__)

ASC, DESC = 1, -1
# (collection, keys, options)
INDEXES: Iterable[Tuple[str, list, dict]] = [
    # listings: my listings, public reads, duplicate detection
    ("listings", [("agent_id", ASC), ("created_at", DESC)], {}),
    ("listings", [("agent_id", ASC), ("status", ASC), ("visibility", ASC), ("published_at", DESC)], {}),
    ("listings", [("fingerprint", ASC)], {"sparse": True}),
    # agent projects: one per (agent, slug); public site reads live ones in order
    ("agent_projects", [("agent_id", ASC), ("slug", ASC)], {"unique": True}),
    ("agent_projects", [("agent_id", ASC), ("status", ASC), ("order", ASC)], {}),
    # public agent sites: looked up by slug on every visit
    ("agent_public_profiles", [("slug", ASC)], {"unique": True, "sparse": True}),
    ("agent_public_profiles", [("agent_id", ASC)], {}),
    # tracking: events per visitor / per lead / per listing, leads per agent
    ("events", [("agent_id", ASC), ("anon_id", ASC), ("ts", DESC)], {}),
    ("events", [("agent_id", ASC), ("contact_id", ASC), ("ts", ASC)], {}),
    ("events", [("agent_id", ASC), ("type", ASC), ("listing_id", ASC)], {}),
    ("contacts", [("agent_id", ASC), ("phone", ASC)], {}),
    ("contacts", [("agent_id", ASC), ("last_activity_at", DESC)], {}),
    ("contacts", [("agent_id", ASC), ("anon_ids", ASC)], {}),
    # one-time codes: lookups by phone, and they clean themselves up after a day
    ("otp_codes", [("phone", ASC), ("created_at", DESC)], {}),
    ("otp_codes", [("created_at", ASC)], {"expireAfterSeconds": 86400}),
    # inquiry abuse limits: counted per (agent, phone) and per visitor over the last hour; rows expire after a day
    ("inquiry_log", [("agent_id", ASC), ("phone", ASC), ("ts", DESC)], {}),
    ("inquiry_log", [("anon_id", ASC), ("ts", DESC)], {}),
    ("inquiry_log", [("ts", ASC)], {"expireAfterSeconds": 86400}),
    # invite requests from the public page, and their rate-limit log (rows expire after a day)
    ("invite_requests", [("phone", ASC), ("created_at", DESC)], {}),
    ("invite_requests", [("status", ASC), ("created_at", ASC)], {}),
    ("invite_request_attempts", [("phone", ASC), ("at", DESC)], {}),
    ("invite_request_attempts", [("ip_hash", ASC), ("at", DESC)], {}),
    ("invite_request_attempts", [("at", ASC)], {"expireAfterSeconds": 86400}),
    # project register (newsroom): projects of an area, newest MahaRERA update first
    ("projects", [("locality", ASC), ("last_modified", DESC)], {}),
    # marketing + social
    ("marketing_packs", [("agent_id", ASC)], {}),
    ("publications", [("listing_id", ASC), ("channel", ASC), ("pack_version", ASC)], {}),
    ("publications", [("agent_id", ASC), ("created_at", DESC)], {}),
    # post results (modules/insights): one snapshot per post and age; read grouped by what the post was
    ("content_metrics", [("post_id", ASC), ("age_label", ASC)], {"unique": True}),
    ("content_metrics", [("tags.format", ASC), ("age_label", ASC), ("at", DESC)], {}),
]


async def ensure_indexes(db) -> dict:
    """Create every index; returns {"created": n, "failed": [descriptions]}."""
    created, failed = 0, []
    for collection, keys, options in INDEXES:
        try:
            await db[collection].create_index(keys, **options)
            created += 1
        except Exception as exc:  # keep starting up; the app works without an index, just slower
            desc = f"{collection}{[k for k, _ in keys]}: {type(exc).__name__}"
            failed.append(desc)
            logger.warning("index not created (%s): %s", desc, str(exc)[:200])
    logger.info("indexes ensured: %d created/present, %d failed", created, len(failed))
    return {"created": created, "failed": failed}
