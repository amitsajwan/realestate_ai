"""Project pages and lists work out the whole register once per shared load, and read exactly as the scans they replace.

A crawl reading the area sitemaps held project pages past the site's 5 s wait and Google got 500s (2026-11-08): each list
walked all ~13k records again, and each project page several times."""
from datetime import datetime, timezone

from app.modules.areastats import pages
from app.modules.newsroom import store as shared

from ..fakes import FakeDb

READ = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)
BASE = {"completion_now": "2029-10-30", "completion_at_registration": "2028-12-31", "units_total": 400, "units_booked": 120,
        "details_checked_at": READ, "details_ok": True, "last_modified": "2026-09-28", "pincode": "412207", "news": []}


def register() -> list:
    """Towers grouped under a primary, a promoter with pages in two areas, a brand, a record with no page."""
    docs = []
    for i in range(30):
        regno = f"P5210000{i:04d}"
        d = {**BASE, "_id": regno, "regno": regno, "name": f"Project {i}", "locality": ("wagholi", "kharadi", "baner")[i % 3],
             "promoter": ("Rohan Builders Pvt Ltd", "Kolte Patil Developers Ltd", f"Small Builder {i}")[i % 3],
             "page_slug": f"project-{i}", "completion_now": f"20{27 + i % 5}-06-30"}
        if i % 4 == 0:
            d["cluster_id"], d["page_text"] = f"c{i % 8}", f"Text {i}"
        if i % 8 == 4:
            d["cluster_primary"] = f"P5210000{i - 4:04d}"
        if i == 29:
            d.pop("page_slug")
        docs.append(d)
    return docs


def test_the_load_index_answers_as_the_scans_did():
    docs = register()
    ix = pages.load_index(docs)
    for doc in docs:
        assert pages.track_record(doc, docs, ix) == pages.track_record(doc, docs)
        assert pages.same_promoter(doc, docs, ix) == pages.same_promoter(doc, docs)
        assert pages.towers(doc, docs, ix) == pages.towers(doc, docs)
        assert pages.group_primary(doc, docs, ix) is pages.group_primary(doc, docs)
        assert pages.primary_of(doc, docs, ix) is pages.primary_of(doc, docs)
        assert pages.cluster_updated(doc, docs, ix.stamps) == pages.cluster_updated(doc, docs)
        for field in ("locality", "pune_place"):   # a page's area: its peers, prices and comparison
            if doc.get(field):
                assert ix.by_area[(field, doc[field])] == [d for d in docs if d.get(field) == doc[field]]
    assert ix.hosted == {d["_id"] for d in docs if pages.can_host(d)}


def test_the_index_is_built_once_per_list_and_again_for_a_new_one():
    docs = register()
    assert pages.load_index(docs) is pages.load_index(docs)
    assert pages.load_index(list(docs)) is not pages.load_index(docs)


async def test_lists_are_worked_out_once_per_shared_load(monkeypatch):
    db = FakeDb()
    db.get_collection("projects").docs = register()
    shared._SHARED.clear()
    built = []
    real = pages._listing
    monkeypatch.setattr(pages, "_listing", lambda *a: built.append(a[1:]) or real(*a))
    first = await pages.listing(db, area="wagholi")
    assert await pages.listing(db, area="wagholi") == first and len(built) == 1   # the sitemap and the area page asking again
    await pages.listing(db, area="kharadi")
    assert len(built) == 2                                                        # another question is its own answer
    shared._SHARED.clear()                                                        # the next load (SHARED_SECONDS later)
    await pages.listing(db, area="wagholi")
    assert len(built) == 3
    shared._SHARED.clear()


async def test_a_caller_changing_its_list_leaves_the_kept_one_alone():
    db = FakeDb()
    db.get_collection("projects").docs = register()
    shared._SHARED.clear()
    rows = await pages.listing(db, area="wagholi")
    rows.clear()
    assert await pages.listing(db, area="wagholi")
    shared._SHARED.clear()


# ---- builder pages: the same work once per shared load (9 of them answered the crawl with 500s after the project fix) ----------

async def test_the_builder_grouping_and_list_are_worked_out_once_per_shared_load(monkeypatch):
    from app.modules.areastats import hubs
    db = FakeDb()
    db.get_collection("projects").docs = register()
    shared._SHARED.clear()
    grouped, listed = [], []
    real_group, real_list = hubs._group_by_builder, hubs._builders
    monkeypatch.setattr(hubs, "_group_by_builder", lambda docs: grouped.append(1) or real_group(docs))
    monkeypatch.setattr(hubs, "_builders", lambda docs, only: listed.append(only) or real_list(docs, only))
    slug = pages.builder_key({"promoter": "Rohan Builders Pvt Ltd", "name": "Project 0"})
    first = await hubs.builder_page(db, slug)
    assert await hubs.builder_page(db, slug) == first
    rows = await hubs.builders(db, only_indexable=False)
    assert await hubs.builders(db, only_indexable=False) == rows
    assert len(grouped) == 1 and listed == [False]
    shared._SHARED.clear()


async def test_a_builder_page_sorting_its_projects_leaves_the_shared_grouping_alone():
    from app.modules.areastats import hubs
    db = FakeDb()
    db.get_collection("projects").docs = register()
    shared._SHARED.clear()
    slug = pages.builder_key({"promoter": "Rohan Builders Pvt Ltd", "name": "Project 0"})
    docs = await shared.Store(db).shared_projects()
    before = [d["_id"] for d in hubs._by_builder(docs)[slug]]
    await hubs.builder_page(db, slug)
    assert [d["_id"] for d in hubs._by_builder(docs)[slug]] == before
    rows = await hubs.builders(db, only_indexable=False)
    rows[0]["name"] = "changed by a caller"
    assert (await hubs.builders(db, only_indexable=False))[0]["name"] != "changed by a caller"
    shared._SHARED.clear()
