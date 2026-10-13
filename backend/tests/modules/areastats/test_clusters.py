"""Tests for areastats.clusters: name matching, no-promoter rule, cross-promoter safety, confirmed groups."""
import pytest

from app.modules.areastats.clusters import (
    assign_clusters,
    base_name,
    cluster_key,
    compute_clusters,
    confirmed_groups,
)
from app.modules.areastats.pages import assign_all
from app.modules.newsroom.store import Store

from ..fakes import FakeDb


# ---------------------------------------------------------------------------
# base_name and cluster_key
# ---------------------------------------------------------------------------

def test_base_name_strips_tower_label_and_number():
    assert base_name("Lodha Camelot Tower 1") == "lodha camelot"
    assert base_name("Lodha Camelot Tower 2") == "lodha camelot"
    assert base_name("Kharadi New Project - Tower 1") == "kharadi new project"
    assert base_name("Kharadi New Project - Tower 8") == "kharadi new project"


def test_base_name_strips_wing_label():
    assert base_name("Venkatesh Vanaya Phase 1 Wing A") == "venkatesh vanaya"
    assert base_name("Venkatesh Vanaya Wing B") == "venkatesh vanaya"


def test_base_name_strips_phase_label_with_number_or_roman():
    assert base_name("Majestique Marbella Phase I") == "majestique marbella"
    assert base_name("Majestique Marbella Phase IV") == "majestique marbella"
    assert base_name("Joyville Hinjawadi Phase 3") == "joyville hinjawadi"
    assert base_name("Majestique Towers East phase 1") == "majestique towers east"


def test_base_name_strips_trailing_roman_numeral():
    assert base_name("Majestique Marbella II") == "majestique marbella"
    assert base_name("Majestique Marbella I") == "majestique marbella"


def test_base_name_preserves_mid_name_towers_word():
    """'Towers' in the middle of a project name must not be stripped."""
    assert base_name("Majestique Towers East Phase 1") == "majestique towers east"


def test_base_name_strips_building_label():
    assert base_name("Manhattan H Building") == "manhattan"
    assert base_name("Manhattan Building C") == "manhattan"


def test_base_name_same_after_strip_gives_cluster():
    assert base_name("Lodha Camelot Tower 1") == base_name("Lodha Camelot Tower 2")
    assert base_name("Venkatesh Vanaya Phase 1") == base_name("Venkatesh Vanaya Phase 8")


def test_cluster_key_requires_promoter():
    doc_with = {"name": "Prasun Elara Tower 1", "promoter": "Prasun Developers", "pincode": "411062"}
    doc_without = {"name": "Gulmohar Villas Phase 1", "promoter": None, "pincode": "411062"}
    assert cluster_key(doc_with) is not None
    assert cluster_key(doc_without) is None


def test_cluster_key_same_for_same_project_different_towers():
    doc1 = {"name": "Prasun Elara Tower 1", "promoter": "Prasun Developers Pvt Ltd", "pincode": "411062"}
    doc2 = {"name": "Prasun Elara Tower 2", "promoter": "Prasun Developers Pvt Ltd", "pincode": "411062"}
    assert cluster_key(doc1) == cluster_key(doc2)


def test_cluster_key_differs_by_promoter():
    d1 = {"name": "Sunrise Tower 1", "promoter": "Alpha Builders", "pincode": "411062"}
    d2 = {"name": "Sunrise Tower 1", "promoter": "Beta Builders", "pincode": "411062"}
    assert cluster_key(d1) != cluster_key(d2)


def test_cluster_key_differs_by_pincode():
    d1 = {"name": "Sunrise Tower 1", "promoter": "Alpha Builders", "pincode": "411062"}
    d2 = {"name": "Sunrise Tower 1", "promoter": "Alpha Builders", "pincode": "411001"}
    assert cluster_key(d1) != cluster_key(d2)


# ---------------------------------------------------------------------------
# compute_clusters
# ---------------------------------------------------------------------------

def _doc(regno, name, promoter, pincode):
    return {"_id": regno, "regno": regno, "name": name, "promoter": promoter, "pincode": pincode}


def test_compute_clusters_groups_same_project():
    docs = [
        _doc("T1", "Lodha Camelot Tower 1", "Lodha Builders Pvt Ltd", "411014"),
        _doc("T2", "Lodha Camelot Tower 2", "Lodha Builders Pvt Ltd", "411014"),
        _doc("T3", "Lodha Camelot Tower 3", "Lodha Builders Pvt Ltd", "411014"),
        _doc("U1", "Unrelated Project", "Other Developer", "411014"),
    ]
    clusters = compute_clusters(docs, {})
    # T1/T2/T3 must be in one cluster
    found = [c for c in clusters.values() if "T1" in c and "T2" in c and "T3" in c]
    assert len(found) == 1 and "U1" not in found[0]


def test_compute_clusters_no_merge_without_promoter():
    docs = [
        _doc("G1", "Gulmohar Villas Phase 1", None, "411014"),
        _doc("G2", "Gulmohar Villas Phase 2", None, "411014"),
        _doc("G3", "Gulmohar Villas Phase 3", None, "411014"),
    ]
    clusters = compute_clusters(docs, {})
    # No promoter → no cluster
    for members in clusters.values():
        assert not any(r in members for r in ["G1", "G2", "G3"]), \
            "Records without a promoter must never be merged"


def test_compute_clusters_no_cross_promoter_merge():
    """The cluster key includes the promoter, so two docs with different promoters can never
    share a key — cross-promoter merges are structurally impossible.  B1 has a different
    promoter from A1+A2 so it goes to a different key and is never merged with them."""
    docs = [
        _doc("A1", "Palm Spring Tower 1", "Alpha Developers Pvt Ltd", "411045"),
        _doc("A2", "Palm Spring Tower 2", "Alpha Developers Pvt Ltd", "411045"),
        _doc("B1", "Palm Spring Tower 1", "Beta Realtors Pvt Ltd", "411045"),
    ]
    clusters = compute_clusters(docs, {})
    # A1+A2 share promoter + base_name + pincode → one cluster
    a_cluster = [c for c in clusters.values() if "A1" in c and "A2" in c]
    assert len(a_cluster) == 1
    assert "B1" not in a_cluster[0], "B1 (different promoter) must not be in the A cluster"
    # B1 is alone → no cluster for it (need 2+ members)
    b_clusters = [c for c in clusters.values() if "B1" in c]
    assert len(b_clusters) == 0, "B1 alone with its key must not form a cluster"


def test_compute_clusters_confirmed_group_wins():
    docs = [
        _doc("C1", "Lodha Project Tower 1", "Lodha Builders Pvt Ltd", "411014"),
        _doc("C2", "Lodha Project Tower 2", "Lodha Builders Pvt Ltd", "411014"),
        _doc("C3", "Lodha Project Tower 3", "Lodha Builders Pvt Ltd", "411014"),
    ]
    confirmed = {"group:CAMELOT": ["C1", "C2", "C3"]}
    clusters = compute_clusters(docs, confirmed)
    assert "group:CAMELOT" in clusters
    assert set(clusters["group:CAMELOT"]) == {"C1", "C2", "C3"}


def test_compute_clusters_confirmed_excludes_from_name_rule():
    """A member in a confirmed group must not also appear in a name-based cluster."""
    docs = [
        _doc("C1", "Lodha Project Tower 1", "Lodha Builders Pvt Ltd", "411014"),
        _doc("C2", "Lodha Project Tower 2", "Lodha Builders Pvt Ltd", "411014"),
    ]
    confirmed = {"group:CAMELOT": ["C1", "C2"]}
    clusters = compute_clusters(docs, confirmed)
    # Only the confirmed cluster, not a duplicate name-based one
    assert len(clusters) == 1
    assert "group:CAMELOT" in clusters


# ---------------------------------------------------------------------------
# assign_clusters (integration with FakeDb)
# ---------------------------------------------------------------------------

async def _seeded_db(*triples):
    """triples: (regno, name, locality, promoter, pincode)"""
    db = FakeDb()
    store = Store(db)
    for regno, name, locality, promoter, pincode in triples:
        await store.projects.insert_one({
            "_id": regno, "regno": regno, "name": name,
            "locality": locality, "promoter": promoter, "pincode": pincode,
        })
    return db, store


async def test_assign_clusters_sets_fields():
    db, store = await _seeded_db(
        ("P1", "Sunrise Phase 1", "wagholi", "Sunrise Developers Pvt Ltd", "412207"),
        ("P2", "Sunrise Phase 2", "wagholi", "Sunrise Developers Pvt Ltd", "412207"),
        ("P3", "Standalone Project", "wagholi", "Other Builder", "412207"),
    )
    docs = await store.all_projects()
    n = await assign_clusters(store, docs)
    assert n > 0
    p1 = await store.project("P1")
    p2 = await store.project("P2")
    # Both share the same cluster_id
    assert p1["cluster_id"] is not None
    assert p1["cluster_id"] == p2["cluster_id"]
    # Exactly one of them is the primary (the other has cluster_primary set)
    primaries = [p1.get("cluster_primary"), p2.get("cluster_primary")]
    assert primaries.count(None) == 1, "Exactly one member is the primary (cluster_primary is None on it)"
    # Standalone project has no cluster
    p3 = await store.project("P3")
    assert p3.get("cluster_id") is None


async def test_assign_clusters_no_promoter_no_cluster():
    db, store = await _seeded_db(
        ("G1", "Gulmohar Villas Phase 1", "wagholi", None, "412207"),
        ("G2", "Gulmohar Villas Phase 2", "wagholi", None, "412207"),
    )
    docs = await store.all_projects()
    await assign_clusters(store, docs)
    for regno in ("G1", "G2"):
        doc = await store.project(regno)
        assert doc.get("cluster_id") is None, f"{regno} without a promoter must not be clustered"


async def test_assign_all_also_runs_clusters():
    """assign_all now also calls assign_clusters; cluster fields must be set after it."""
    db, store = await _seeded_db(
        ("R1", "Rohan Abhilasha Phase 1", "wagholi", "Rohan Builders Pvt Ltd", "412207"),
        ("R2", "Rohan Abhilasha Phase 2", "wagholi", "Rohan Builders Pvt Ltd", "412207"),
    )
    await assign_all(store)
    r1 = await store.project("R1")
    r2 = await store.project("R2")
    assert r1.get("cluster_id") is not None and r1["cluster_id"] == r2.get("cluster_id")
