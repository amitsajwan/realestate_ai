"""Blank promoters filled from MahaRERA's cards: a firm is written, a person never, a record that has one is left alone."""
from app.modules.areastats import refresh
from app.modules.newsroom.store import PROJECTS, Store
from app.modules.newsroom.types import MahaReraProject

from ..fakes import FakeDb


def card(regno, promoter):
    return MahaReraProject(regno=regno, name=regno, promoter=promoter, location="", district="", pincode="", last_modified="", url="")


async def _store(*records):
    db = FakeDb()
    for r in records:
        await db.get_collection(PROJECTS).insert_one(r)
    return Store(db)


async def _filled(monkeypatch, store, cards, **kw):
    async def by_name(get, name):
        return cards

    monkeypatch.setattr(refresh.search, "search_by_name", by_name)
    return await refresh.fill_promoters(store, None, pause=0, **kw)


async def test_a_firm_on_the_card_fills_only_a_blank_promoter(monkeypatch):
    store = await _store({"_id": "P1", "name": "A", "locality": "wagholi", "promoter": ""},
                         {"_id": "P2", "name": "B", "locality": "wagholi", "promoter": "Kept Developers"},
                         {"_id": "P3", "name": "C", "locality": None, "promoter": ""})
    out = await _filled(monkeypatch, store, [card("P1", "Krishna Buildcon"), card("P2", "Other Developers"), card("P3", "Other Homes")])
    assert out["read"] == 1 and out["filled"] == 1
    assert (await store.project("P1"))["promoter"] == "Krishna Buildcon"
    assert (await store.project("P2"))["promoter"] == "Kept Developers"
    assert (await store.project("P3"))["promoter"] == ""


async def test_a_card_with_a_person_or_no_card_leaves_it_blank(monkeypatch):
    store = await _store({"_id": "P1", "name": "A", "locality": "kharadi", "promoter": ""},
                         {"_id": "P2", "name": "B", "locality": "kharadi", "promoter": None})
    out = await _filled(monkeypatch, store, [card("P1", "")])   # the parser has already blanked the person
    assert out["filled"] == 0 and out["no_card"] == 1
    assert (await store.project("P1"))["promoter"] == ""


async def test_a_dry_run_names_what_it_would_write_and_writes_nothing(monkeypatch):
    store = await _store({"_id": "P1", "name": "A", "locality": "wagholi", "promoter": ""})
    out = await _filled(monkeypatch, store, [card("P1", "Krishna Buildcon")], dry_run=True)
    assert out["names"] == [("P1", "Krishna Buildcon")]
    assert (await store.project("P1"))["promoter"] == ""
