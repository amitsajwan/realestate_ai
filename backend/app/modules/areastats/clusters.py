"""Cluster detection for MahaRERA project pages: towers and phases of the same project share one primary page.

A cluster key = promoter_key + base_name + pincode.  base_name strips tower/wing/building/phase labels and their
identifiers (numbers, roman numerals, single letters) from the project name so "Lodha Camelot Tower 1" and
"Lodha Camelot Tower 2" map to the same key.

Two safety rules:
  - No promoter → no merge (Gulmohar Villas: 10 registrations, different promoters or none).
  - Different promoter_key values for the same base_name+pincode → never merged (140 such pairs on production).

Confirmed groups in agentprojects.groups override the name rule: a group document with a `registrations` list
(e.g. Lodha Camelot) is always kept together regardless of name.

Dry-run entry point:
    python -m app.modules.areastats.clusters --report
"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

from app.core.areas import BY_KEY

# ---------------------------------------------------------------------------
# Name normalisation helpers (promoter_key is imported from pages at call time
# to avoid a circular import; we re-implement the ASCII helper inline)
# ---------------------------------------------------------------------------

_WORDS = re.compile(r"[a-z0-9]+")

# Labels that introduce a tower / wing / phase identifier — stripped together
# with the identifier that follows (number, roman numeral, or single letter).
# IMPORTANT: require at least one whitespace OR a dash between the label word and the identifier;
# this prevents "towers" in a project name from being consumed as "tower" + "s" identifier.
_TOWER_LABEL = re.compile(
    r"\b(towers?|wings?|buildings?|phases?)(?:\s+|[-–]\s*)([0-9]+[a-z]?|[ivxlcdm]+|[a-z])\b",
    re.IGNORECASE,
)
# Reverse-order label: single-letter identifier BEFORE the label word, e.g. "H Building", "A Wing"
_REVERSE_LABEL = re.compile(
    r"\b([a-z])\s+(towers|tower|wings|wing|buildings|building)\b",
    re.IGNORECASE,
)
# A lone identifier at the end of the name: "Phase I", "Block C", "– II"
_TAIL_ROMAN = re.compile(r"\s+[-–]?\s*([ivxlcdm]+)\s*$", re.IGNORECASE)
_TAIL_LETTER = re.compile(r"\s+[-–]?\s*([a-z])\s*$", re.IGNORECASE)
# Separators left over after stripping tokens
_NOISE = re.compile(r"[\s\-–&,]+$")

# Legal-entity words dropped by promoter_key
_LEGAL = re.compile(r"\b(m s|private|pvt|limited|ltd|llp|the|and|co|company|corporation|corp)\b")


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()


def _promoter_key(name: Optional[str]) -> str:
    """'M/s. Rohan Builders Pvt. Ltd.' → 'rohan builders'."""
    words = " ".join(_WORDS.findall(_ascii(name or "")))
    return " ".join(_LEGAL.sub(" ", words).split())


def base_name(name: str) -> str:
    """Strip tower / wing / building / phase labels and their identifiers, then trailing roman / letter tokens.

    "Lodha Camelot Tower 1"         → "lodha camelot"
    "Venkatesh Vanaya Phase 1"      → "venkatesh vanaya"
    "Majestique Marbella II"        → "majestique marbella"
    "Manhattan H Building"          → "manhattan"        (label comes BEFORE the identifier)
    "Majestique Towers East Phase 1"→ "majestique towers east"   (mid-name 'towers' is preserved)
    """
    s = _ascii(name)
    # Strip "Tower 1", "Wing A", "Phase III", etc. (label + identifier)
    s = _TOWER_LABEL.sub(" ", s)
    # Strip reverse-order labels: "H Building", "A Wing" (identifier before label)
    s = _REVERSE_LABEL.sub(" ", s)
    # Strip a trailing roman numeral or single letter (the lone phase token)
    s = _TAIL_ROMAN.sub("", s)
    s = _TAIL_LETTER.sub("", s)
    # Clean up trailing noise characters and normalise internal spaces
    s = _NOISE.sub("", s).strip()
    s = re.sub(r"\s{2,}", " ", s)
    return s


def cluster_key(doc: dict) -> Optional[str]:
    """The cluster key for `doc`: promoter_key + base_name + pincode, or None when there is no promoter."""
    pk = _promoter_key(doc.get("promoter"))
    if not pk:
        return None
    bn = base_name(doc.get("name") or "")
    if not bn:
        return None
    pc = str(doc.get("pincode") or "").strip()
    return f"{pk}\t{bn}\t{pc}"


# ---------------------------------------------------------------------------
# Confirmed groups from agentprojects
# ---------------------------------------------------------------------------

AGENTPROJECTS = "agent_projects"


async def confirmed_groups(db) -> Dict[str, List[str]]:
    """Return {cluster_id: [regno, ...]} for every agentprojects document that has a `registrations` list.

    The cluster_id for a confirmed group is "group:<rera_no>" so it never collides with a name-based key.
    Only registration numbers are returned (no candidates).
    """
    col = db.get_collection(AGENTPROJECTS)
    docs = await col.find({"registrations.0": {"$exists": True}}).to_list(1000)
    out: Dict[str, List[str]] = {}
    for d in docs:
        regnos = [r["regno"] for r in (d.get("registrations") or []) if r.get("regno")]
        if len(regnos) < 2:
            continue
        key = f"group:{d.get('rera_no') or d['_id']}"
        out[key] = regnos
    return out


# ---------------------------------------------------------------------------
# Core clustering
# ---------------------------------------------------------------------------


def compute_clusters(docs: List[dict], confirmed: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Return {cluster_id: [regno, ...]} for docs, confirmed groups winning over name-based ones.

    Rules:
    - A doc already assigned by a confirmed group is not considered for name-based clustering.
    - No promoter → no name-based merge (key is None).
    - Different promoters for the same base_name+pincode → never merged.
    """
    by_id: Dict[str, dict] = {d.get("regno") or d["_id"]: d for d in docs}

    # ---- confirmed groups: assign members directly -------------------------
    assigned: Dict[str, str] = {}   # regno → cluster_id
    clusters: Dict[str, List[str]] = {}

    for cid, regnos in confirmed.items():
        members = [r for r in regnos if r in by_id]
        if len(members) < 2:
            # Single known member: still record it; may be useful later
            if members:
                assigned[members[0]] = cid
                clusters[cid] = members
            continue
        clusters[cid] = members
        for r in members:
            assigned[r] = cid

    # ---- name-based clustering for everything else -------------------------
    # The cluster key already includes the promoter_key, so two docs with different
    # promoters will never share a key: cross-promoter merges are structurally impossible.
    name_clusters: Dict[str, List[str]] = {}

    for regno, doc in by_id.items():
        if regno in assigned:
            continue
        ck = cluster_key(doc)
        if ck is None:
            continue
        name_clusters.setdefault(ck, []).append(regno)

    # Only keep name-based clusters with 2+ members
    for ck, members in name_clusters.items():
        if len(members) >= 2:
            clusters[ck] = members

    return clusters


def _primary_for(members: List[str], by_id: Dict[str, dict]) -> str:
    """The primary registration: oldest `registered_on` date, or alphabetically first regno."""
    def sort_key(regno: str) -> Tuple[str, str]:
        doc = by_id.get(regno, {})
        date = str(doc.get("registered_on") or "9999-99-99")[:10]
        return (date, regno)

    return min(members, key=sort_key)


# ---------------------------------------------------------------------------
# Cluster report
# ---------------------------------------------------------------------------

async def cluster_report(db) -> List[dict]:
    """Clusters in our areas (locality in BY_KEY), sorted by size desc.

    Each row: {cluster_id, primary, size, members: [{regno, name, slug, locality, promoter, pincode}]}
    """
    from app.modules.newsroom.store import Store
    store = Store(db)
    all_docs = await store.all_projects()

    conf = await confirmed_groups(db)
    clusters = compute_clusters(all_docs, conf)

    by_id = {d.get("regno") or d["_id"]: d for d in all_docs}

    # Filter to clusters where at least one member is in our areas
    rows = []
    for cid, members in clusters.items():
        in_area = [m for m in members if by_id.get(m, {}).get("locality") in BY_KEY]
        if not in_area:
            continue
        primary = _primary_for(members, by_id)
        member_rows = []
        for regno in sorted(members, key=lambda r: (r != primary, r)):
            doc = by_id.get(regno, {})
            member_rows.append({
                "regno": regno,
                "name": doc.get("name") or "",
                "slug": doc.get("page_slug") or "",
                "locality": doc.get("locality") or "",
                "promoter": doc.get("promoter") or "",
                "pincode": str(doc.get("pincode") or ""),
            })
        rows.append({
            "cluster_id": cid,
            "primary": primary,
            "size": len(members),
            "members": member_rows,
        })

    rows.sort(key=lambda r: (-r["size"], r["cluster_id"]))
    return rows


# ---------------------------------------------------------------------------
# Assign cluster_id and cluster_primary to store docs
# ---------------------------------------------------------------------------

async def assign_clusters(store, docs: List[dict]) -> int:
    """Compute clusters for all docs and store cluster_id / cluster_primary on each record.

    Returns the number of records updated.  Call after assign_all slugs.
    cluster_primary is None for the primary record in a cluster (it IS the primary).
    cluster_id is None for records not in any cluster.
    """
    conf = await confirmed_groups(store.db)
    clusters = compute_clusters(docs, conf)

    by_id = {d.get("regno") or d["_id"]: d for d in docs}

    # Build assignment map: regno → (cluster_id, primary_regno)
    assignment: Dict[str, Tuple[str, str]] = {}
    for cid, members in clusters.items():
        primary = _primary_for(members, by_id)
        for regno in members:
            assignment[regno] = (cid, primary)

    n = 0
    for doc in docs:
        regno = doc.get("regno") or doc["_id"]
        info = assignment.get(regno)
        if info:
            cid, primary = info
            cluster_primary = None if regno == primary else primary
            # Only update if changed
            if doc.get("cluster_id") != cid or doc.get("cluster_primary") != cluster_primary:
                await store.set_project(regno, cluster_id=cid, cluster_primary=cluster_primary)
                n += 1
        else:
            # Clear stale cluster fields if they exist
            if doc.get("cluster_id") is not None:
                await store.set_project(regno, cluster_id=None, cluster_primary=None)
                n += 1
    return n


# ---------------------------------------------------------------------------
# __main__: python -m app.modules.areastats.clusters --report
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio
    import os
    import sys

    from motor.motor_asyncio import AsyncIOMotorClient

    async def _run():
        mongo_url = os.environ.get("MONGODB_URL") or os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.environ.get("DATABASE_NAME") or os.environ.get("DB_NAME", "propertyai")
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        try:
            rows = await cluster_report(db)
        finally:
            client.close()

        total_pages = sum(r["size"] for r in rows)
        print(f"Cluster report — {len(rows)} clusters, {total_pages} pages in our areas\n")
        for r in rows:
            promoter = r["members"][0]["promoter"] if r["members"] else ""
            pincode = r["members"][0]["pincode"] if r["members"] else ""
            pline = f" | {promoter}" if promoter else " | (no promoter)"
            print(f"[{r['size']}] {r['cluster_id']}  primary={r['primary']}{pline}  pin={pincode}")
            for m in r["members"]:
                flag = "*" if m["regno"] == r["primary"] else " "
                print(f"  {flag} {m['regno']:30s} {m['name']}")
            print()

    if "--report" not in sys.argv:
        print("Usage: python -m app.modules.areastats.clusters --report")
        sys.exit(1)

    asyncio.run(_run())
