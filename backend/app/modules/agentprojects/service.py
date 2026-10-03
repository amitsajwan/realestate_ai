"""Project storage, MahaRERA checks and public reads.

Owner scoping: projects are written by the platform owner for an agent (white-glove), keyed by (agent_id, slug).
Public reads show only `live` projects of public agent profiles, never the internal issue list.
"""
import uuid
from datetime import datetime
from typing import Callable, List, Optional

from . import maharera
from .schemas import CatalogProject, OwnerProject, ProjectAgent, ProjectIn, PublicProject, Rera

COLLECTION = "agent_projects"
MAX_PER_AGENT = 200
MAX_CATALOG = 2000  # live project records read to build the shared /projects pages


def indexable(profile: dict) -> bool:
    """A public agent site that is neither the fictional demo nor a preview the agent has not agreed to publish."""
    b = profile.get("branding_data") or {}
    return bool(profile.get("is_public")) and not (b.get("demo") or b.get("preview")) and bool(profile.get("agent_id"))


def _agent_name(profile: dict) -> str:
    b = profile.get("branding_data") or {}
    return (b.get("business_name") or profile.get("agent_name") or profile.get("slug") or "").strip()


class ProjectError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _months(a: Optional[str], b: Optional[str]) -> Optional[int]:
    """Whole months from date a to date b (YYYY-MM-DD); None when either is missing."""
    if not a or not b:
        return None
    ya, ma = int(a[:4]), int(a[5:7])
    yb, mb = int(b[:4]), int(b[5:7])
    return (yb - ya) * 12 + (mb - ma)


def public_view(doc: dict) -> dict:
    confs = []
    for c in doc.get("configurations") or []:
        confs.append({**c, "price_per_sqft": int(round(c["price_inr"] / c["carpet_sqft"]))})
    prices = [c["price_inr"] for c in confs]
    rera = doc.get("rera") or None
    booked = None
    if rera and rera.get("units_total"):
        booked = int(round(100 * (rera.get("units_booked") or 0) / rera["units_total"]))
    moved = _months(rera.get("completion_at_registration"), rera.get("completion_now")) if rera else None
    updated = doc.get("updated_at")
    return {
        "id": doc["_id"], "slug": doc["slug"], "name": doc["name"], "builder": doc["builder"],
        "locality": doc["locality"], "address": doc.get("address", ""), "pincode": doc.get("pincode", ""),
        "rera_no": doc["rera_no"], "scope_note": doc.get("scope_note", ""), "configurations": confs,
        "price_min": min(prices) if prices else None, "price_max": max(prices) if prices else None,
        "bhk_options": sorted({c["bhk"] for c in confs}), "possession_target": doc.get("possession_target"),
        "positioning": doc.get("positioning", ""), "who_it_suits": doc.get("who_it_suits") or [],
        "highlights": doc.get("highlights") or [], "amenities": doc.get("amenities") or [],
        "specs": doc.get("specs") or {}, "provenance": doc.get("provenance") or {}, "nearby": doc.get("nearby") or [],
        "place": doc.get("place"), "maps_query": doc.get("maps_query", ""), "media": doc.get("media") or [],
        "rera": rera, "booked_pct": booked, "completion_moved_months": moved,
        "updated_at": updated.isoformat() if isinstance(updated, datetime) else updated,
    }


class ProjectService:
    def __init__(self, db, now: Callable[[], datetime] = datetime.utcnow, fetch: Optional[maharera.Fetch] = None):
        self.col = db.get_collection(COLLECTION)
        self.profiles = db.get_collection("agent_public_profiles")
        self.now = now
        self.fetch = fetch or maharera.make_fetch()

    # ---- owner side -----------------------------------------------------------------------------------------
    async def upsert(self, agent_id: str, slug: str, body: ProjectIn) -> OwnerProject:
        """Create or replace the agent's project `slug`. A MahaRERA reading already stored is kept unless the
        registration number changed (then it is dropped until the next check)."""
        data = body.model_dump(mode="json")
        now = self.now()
        doc = await self.col.find_one({"agent_id": agent_id, "slug": slug})
        if doc:
            sets = {**data, "updated_at": now}
            if doc.get("rera_no") != data["rera_no"] or doc.get("maharera_id") != data["maharera_id"]:
                sets["rera"] = None
            elif doc.get("rera"):
                sets["rera"] = {**doc["rera"], "promoter": data["promoter"] or doc["rera"].get("promoter", "")}
            await self.col.update_one({"_id": doc["_id"]}, {"$set": sets})
        else:
            if await self.col.count_documents({"agent_id": agent_id}) >= MAX_PER_AGENT:
                raise ProjectError("Too many projects for one agent", 409)
            await self.col.insert_one({"_id": uuid.uuid4().hex, "agent_id": agent_id, "slug": slug, **data,
                                       "rera": None, "created_at": now, "updated_at": now})
        return await self._owner(agent_id, slug)

    async def _owner(self, agent_id: str, slug: str) -> OwnerProject:
        doc = await self.col.find_one({"agent_id": agent_id, "slug": slug})
        if not doc:
            raise ProjectError("Project not found", 404)
        return OwnerProject(**public_view(doc), agent_id=agent_id, status=doc.get("status", "draft"),
                            issues=doc.get("issues") or [])

    async def list_for_owner(self, agent_id: str) -> List[OwnerProject]:
        docs = await self.col.find({"agent_id": agent_id}).sort("order", 1).to_list(MAX_PER_AGENT)
        return [OwnerProject(**public_view(d), agent_id=agent_id, status=d.get("status", "draft"),
                             issues=d.get("issues") or []) for d in docs]

    async def check_maharera(self, agent_id: str, slug: str) -> OwnerProject:
        """Re-read the project's MahaRERA record and store it with today's date. Fails loudly, never guesses."""
        doc = await self.col.find_one({"agent_id": agent_id, "slug": slug})
        if not doc:
            raise ProjectError("Project not found", 404)
        if not doc.get("maharera_id"):
            raise ProjectError("This project has no MahaRERA id yet", 422)
        body = await self.fetch(doc["maharera_id"])
        if body is None:
            raise ProjectError("MahaRERA did not answer, try again later", 503)
        try:
            rera = maharera.parse_general(body, doc["rera_no"], doc["maharera_id"])
        except maharera.MahaReraError as e:
            raise ProjectError(str(e), 422)
        now = self.now()
        rera.update(promoter=doc.get("promoter", ""), checked_at=now.strftime("%Y-%m-%d"))
        await self.col.update_one({"_id": doc["_id"]}, {"$set": {"rera": Rera(**rera).model_dump(), "rera_checked": now}})
        return await self._owner(agent_id, slug)

    # ---- public side ----------------------------------------------------------------------------------------
    async def _agent_id(self, agent_slug: str) -> Optional[str]:
        profile = await self.profiles.find_one({"slug": agent_slug, "is_public": True})
        return profile.get("agent_id") if profile else None

    async def public_list(self, agent_slug: str) -> List[PublicProject]:
        agent_id = await self._agent_id(agent_slug)
        if not agent_id:
            raise ProjectError("Agent not found", 404)
        docs = await self.col.find({"agent_id": agent_id, "status": "live"}).sort("order", 1).to_list(MAX_PER_AGENT)
        return [PublicProject(**public_view(d)) for d in docs]

    async def sitemap_entries(self) -> List[dict]:
        """Live projects on public agent sites that are neither the fictional demo nor an unpublished preview,
        as {agent_slug, slug, updated_at}."""
        out = []
        for profile in await self.profiles.find({"is_public": True}).to_list(None):
            if not indexable(profile):
                continue
            docs = await self.col.find({"agent_id": profile["agent_id"], "status": "live"}).sort("order", 1).to_list(MAX_PER_AGENT)
            out += [{"agent_slug": profile["slug"], "slug": d["slug"], "updated_at": d.get("updated_at")} for d in docs]
        return out

    # ---- Avasetu's shared project pages --------------------------------------------------------------------------
    async def catalog(self, locality: Optional[str] = None) -> List[CatalogProject]:
        """One entry per MahaRERA registration that some indexable agent has live and that at least one record has checked.
        Two agents with the same project give one page: its facts come from the most recently checked record, and both
        agents are listed for enquiries. Sorted by locality, then name."""
        profiles = {p["agent_id"]: p for p in await self.profiles.find({"is_public": True}).to_list(None) if indexable(p)}
        if not profiles:
            return []
        docs = await self.col.find({"status": "live", "agent_id": {"$in": list(profiles)}}).to_list(MAX_CATALOG)
        groups: dict = {}
        for d in docs:
            groups.setdefault(d["rera_no"], []).append(d)
        want = (locality or "").strip().lower()
        out = []
        for recs in groups.values():
            def fresh(d):
                u = d.get("updated_at")
                return ((d.get("rera") or {}).get("checked_at") or "", u.isoformat() if isinstance(u, datetime) else str(u or ""))
            checked = sorted((d for d in recs if d.get("rera")), key=fresh, reverse=True)
            if not checked:  # nobody's copy has been read on MahaRERA yet: no shared page
                continue
            main = checked[0]
            if want and main["locality"].strip().lower() != want:
                continue
            agents = []
            for d in sorted(recs, key=lambda d: _agent_name(profiles[d["agent_id"]]).lower()):
                pr = profiles[d["agent_id"]]
                agents.append(ProjectAgent(slug=pr["slug"], name=_agent_name(pr), phone=pr.get("phone"), photo=pr.get("photo"),
                                           project_slug=d["slug"]))
            out.append(CatalogProject(**public_view(main), catalog_slug=main["slug"], agents=agents))
        out.sort(key=lambda p: (p.locality.lower(), p.name.lower()))
        return out

    async def catalog_get(self, slug: str) -> CatalogProject:
        """The shared page for `slug`. An agent's own slug for the same project also finds it (catalog_slug then says
        which address is the real one, so the page can redirect)."""
        for p in await self.catalog():
            if p.slug == slug or any(a.project_slug == slug for a in p.agents):
                return p
        raise ProjectError("Project not found", 404)

    async def public_get(self, agent_slug: str, slug: str) -> PublicProject:
        agent_id = await self._agent_id(agent_slug)
        doc = await self.col.find_one({"agent_id": agent_id, "slug": slug, "status": "live"}) if agent_id else None
        if not doc:
            raise ProjectError("Project not found", 404)
        shared = next((p.slug for p in await self.catalog() if p.rera_no == doc["rera_no"]
                       and any(a.slug == agent_slug for a in p.agents)), None)
        return PublicProject(**public_view(doc), catalog_slug=shared)
