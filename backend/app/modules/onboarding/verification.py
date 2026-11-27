"""MahaRERA agent check (docs/plan/agent-network.md, step 1): is the agent's MahaRERA agent number real and theirs.

The owner checks each number by hand on the MahaRERA register for now (later code reads the register). The result lives on the
agent's profile in `rera_check` (onboarding owns `agent_public_profiles`, so only this module writes it):

    {status: verified | rejected, number, by, at, register_url, note}

A profile with no check, or a check of another number than the one on the profile now, is `pending`: changing the number undoes
the check by itself, so a badge never stands for a number nobody looked at.

Only a verified agent sees the lead board and can ask for a buyer. The public agent page shows a "MahaRERA verified" badge from
`branding_data.rera_verified_no` (the number that was checked), which the page already receives with the rest of the branding;
who checked it and the note stay private.
"""
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

COLLECTION = "agent_public_profiles"
STATUSES = ("pending", "verified", "rejected")
# the register's addresses (the public search moved between these hosts). The search on maharera.maharashtra.gov.in links
# each agent to their page on maharerait.maharashtra.gov.in/agent/view/<id>: that page is the one to paste.
REGISTER_HOSTS = ("maharera.maharashtra.gov.in", "maharera.mahaonline.gov.in", "maharerait.maharashtra.gov.in")
MAX_NOTE = 300


class VerificationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def number_of(profile: dict) -> Optional[str]:
    return ((profile.get("branding_data") or {}).get("rera_agent_no") or "").strip() or None


def status_of(profile: dict) -> str:
    """pending, verified or rejected, for the number on the profile now."""
    chk = profile.get("rera_check") or {}
    no = number_of(profile)
    if no and chk.get("status") in ("verified", "rejected") and chk.get("number") == no:
        return chk["status"]
    return "pending"


def is_verified(profile: Optional[dict]) -> bool:
    return bool(profile) and status_of(profile) == "verified"


def is_register_url(url: str) -> bool:
    try:
        u = urlparse(url)
    except ValueError:
        return False
    host = (u.hostname or "").lower()
    return u.scheme == "https" and any(host == h or host.endswith("." + h) for h in REGISTER_HOSTS)


def view(profile: dict) -> dict:
    """The check as the owner sees it in Studio."""
    chk = profile.get("rera_check") or {}
    status = status_of(profile)
    b = profile.get("branding_data") or {}
    return {"agent_id": str(profile.get("agent_id") or profile.get("_id")), "slug": profile.get("slug"),
            "name": (b.get("business_name") or profile.get("agent_name") or profile.get("slug") or "Agent").strip(),
            "rera_agent_no": number_of(profile), "status": status,
            "checked_at": chk.get("at") if status != "pending" else None,
            "register_url": chk.get("register_url") if status != "pending" else None,
            "note": chk.get("note") if status != "pending" else None,
            # a check of an older number: say so, so the owner knows why it is pending again
            "number_changed": bool(chk.get("number")) and chk.get("number") != number_of(profile)}


async def checks(db) -> List[dict]:
    """Every agent profile with its check, the ones waiting first (those with a number before those without)."""
    rows = [view(p) for p in await db.get_collection(COLLECTION).find({}).to_list(5000)]
    order = {"pending": 0, "rejected": 1, "verified": 2}
    return sorted(rows, key=lambda r: (order[r["status"]], r["rera_agent_no"] is None, r["name"].lower()))


async def set_status(db, owner_id: str, agent_id: str, status: str, register_url: Optional[str] = None,
                     note: Optional[str] = None, now: Optional[datetime] = None) -> dict:
    """The owner records what the register says about this agent's number. `pending` clears the check."""
    if status not in STATUSES:
        raise VerificationError("Unknown status", 422)
    col = db.get_collection(COLLECTION)
    prof = await col.find_one({"agent_id": agent_id})
    if not prof:
        raise VerificationError("Agent not found", 404)
    no = number_of(prof)
    url = (register_url or "").strip() or None
    if status != "pending" and not no:
        raise VerificationError("This agent has not given a MahaRERA agent number yet", 409)
    if status == "verified" and not (url and is_register_url(url)):
        raise VerificationError("Paste the agent's page on the MahaRERA register (an https maharera address)", 422)
    if url and not is_register_url(url):
        raise VerificationError("The register page must be an https maharera address", 422)
    branding = dict(prof.get("branding_data") or {})
    if status == "verified":
        branding["rera_verified_no"] = no
    else:
        branding.pop("rera_verified_no", None)
    sets = {"branding_data": branding, "updated_at": now or datetime.utcnow()}
    update = {"$set": sets}
    if status == "pending":
        update["$unset"] = {"rera_check": ""}
    else:
        sets["rera_check"] = {"status": status, "number": no, "by": owner_id, "at": now or datetime.utcnow(),
                              "register_url": url, "note": (note or "").strip()[:MAX_NOTE] or None}
    await col.update_one({"agent_id": agent_id}, update)
    return view({**prof, **sets} if status != "pending" else {**{k: v for k, v in prof.items() if k != "rera_check"}, **sets})
