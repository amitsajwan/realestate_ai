"""What the To do tab says about projects on several pages, and the owner's word on them (seo/splits.py)."""
from datetime import datetime, timezone

import pytest

from app.modules.areastats import clusters
from app.modules.newsroom.store import Store
from app.modules.seo import splits

from ..fakes import FakeDb


def project(regno, name, slug=None, pincode="411045", promoter="", **kw):
    return {"_id": regno, "regno": regno, "name": name, "page_slug": slug or regno.lower(), "pincode": pincode, "promoter": promoter,
            "units_total": 100, "locality": "wagholi", **kw}


@pytest.fixture(autouse=True)
def homes_being_built(monkeypatch):
    monkeypatch.setattr(splits.pages, "homes", lambda d: True)
    monkeypatch.setattr(splits.pages, "is_old", lambda d: False)
    monkeypatch.setattr(splits.pages, "ready_for_search", lambda d: False)


def test_a_project_page_with_its_area_list_is_nothing_to_do():
    by_slug = {"rosewood-park-wagholi": project("P1", "Rosewood Park", "rosewood-park-wagholi")}
    c = splits.explain({"phrase": "rosewood park wagholi", "pages": ["/projects/area/wagholi", "/projects/rosewood-park-wagholi"]}, by_slug)
    assert c["kind"] == "project_and_list"
    assert [p["kind"] for p in c["pages"]] == ["area", "project"]


def test_two_list_pages_are_nothing_to_do():
    c = splits.explain({"phrase": "projects in baner", "pages": ["/projects/area/baner", "/projects/area/baner/new-launches"]}, {})
    assert c["kind"] == "lists"


def test_towers_of_one_project_shown_for_one_search_call_for_a_decision():
    by_slug = {"a": project("P1", "Aldea Annexo C2", "a"), "b": project("P2", "Aldea Annexo D", "b")}
    c = splits.explain({"phrase": "aldea annexo phase 4", "pages": ["/projects/a", "/projects/b"]}, by_slug)
    assert c["kind"] == "one_project" and c["regnos"] == ["P1", "P2"]


def test_a_builders_two_projects_are_not_one_project():
    by_slug = {"a": project("P1", "Suyog Rachana", "a", promoter="Suyog"), "b": project("P2", "Suyog Sweet Home", "b", promoter="Suyog")}
    assert splits.explain({"phrase": "suyog", "pages": ["/projects/a", "/projects/b"]}, by_slug)["kind"] == "different"


def test_alike_names_of_two_promoters_are_not_one_project():
    by_slug = {"a": project("P1", "Royal Park A", "a", promoter="One Ltd"), "b": project("P2", "Royal Park B", "b", promoter="Two Ltd")}
    assert splits.explain({"phrase": "royal park", "pages": ["/projects/a", "/projects/b"]}, by_slug)["kind"] == "different"


def test_towers_kept_apart_stop_asking():
    by_slug = {"a": project("P1", "Aldea Annexo C2", "a", split_apart="P1"), "b": project("P2", "Aldea Annexo D", "b", split_apart="P1")}
    assert splits.explain({"phrase": "aldea annexo", "pages": ["/projects/a", "/projects/b"]}, by_slug)["kind"] == "different"


def test_a_search_joins_its_project_as_evidence_and_comes_first():
    docs = [project("P1", "Nivaan Grandeur"), project("P2", "Nivaan Grandeur Phase-II"),
            project("Q1", "Aldea Annexo Tower 1", "q1"), project("Q2", "Aldea Annexo Tower 2", "q2")]
    conflict = {"phrase": "aldea annexo", "impressions": 6, "position": 7.7, "pages": ["/projects/q1", "/projects/q2"]}
    out = splits.view(docs, {}, [conflict])
    assert out["competing"] == []
    assert out["split"]["items"][0]["name"].startswith("Aldea Annexo")
    assert out["split"]["items"][0]["searches"] == [{"phrase": "aldea annexo", "impressions": 6, "position": 7.7}]


def test_a_row_says_whether_the_web_proved_it_or_the_numbers_wait(monkeypatch):
    docs = [project("P1", "Nivaan Grandeur"), project("P2", "Nivaan Grandeur Phase-II")]
    assert splits.view(docs, {}, [])["split"]["items"][0]["state"] == "waiting"
    assert splits.view(docs, {"P1": [], "P2": []}, [])["split"]["items"][0]["state"] == "no_proof"
    monkeypatch.setattr(splits.samegroup, "groups", lambda ds, results: [["P1", "P2"]])
    assert splits.view(docs, {}, [])["split"]["items"][0]["state"] == "proved"


def test_township_sectors_carry_a_warning():
    docs = [project("P1", "Life Republic Sector R34"), project("P2", "Life Republic Sector R35")]
    assert "township" in splits.view(docs, {}, [])["split"]["items"][0]["hint"].lower()


async def seeded(*docs):
    db = FakeDb()
    for d in docs:
        await db.get_collection("projects").insert_one(d)
    return Store(db), db


async def test_same_project_puts_the_pages_on_one_and_undo_takes_it_back():
    store, db = await seeded(project("P1", "Nivaan Grandeur"), project("P2", "Nivaan Grandeur Phase-II"))
    await splits.decide(store, ["P2", "P1"], "same")
    docs = await store.all_projects()
    assert {d["cluster_id"] for d in docs} == {"group:owner:P1"}
    assert sum(1 for d in docs if d["cluster_primary"]) == 1
    assert splits.decided(docs)[0]["decision"] == "same"
    await splits.decide(store, ["P1", "P2"], "undo")
    assert all(d.get("cluster_id") is None for d in await store.all_projects())


async def test_keep_separate_takes_a_project_off_the_list():
    store, db = await seeded(project("P1", "Nivaan Grandeur"), project("P2", "Nivaan Grandeur Phase-II"))
    await splits.decide(store, ["P1", "P2"], "apart")
    docs = await store.all_projects()
    assert splits.view(docs, {}, [])["split"]["total"] == 0
    assert splits.decided(docs)[0]["decision"] == "apart"


async def test_two_promoters_are_never_merged_even_when_asked():
    store, db = await seeded(project("P1", "Royal Park A", promoter="One Ltd"), project("P2", "Royal Park B", promoter="Two Ltd"))
    with pytest.raises(ValueError):
        await splits.decide(store, ["P1", "P2"], "same")


def test_a_project_records_group_keeps_its_registration():
    docs = [project("P1", "A", owner_group="P1"), project("P2", "B", owner_group="P1")]
    assert clusters.owner_groups(docs, {"group:X": ["P1"]}) == {"group:owner:P1": ["P2"]}
