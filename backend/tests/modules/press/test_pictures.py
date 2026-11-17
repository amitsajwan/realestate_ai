"""has_then_now tolerates areastats.pictures not existing, and reads it when it does."""
from app.modules.press import pictures

from ..fakes import FakeDb


async def test_none_when_the_module_does_not_exist():
    assert await pictures.has_then_now(FakeDb(), "kharadi") is None


async def test_reads_the_function_when_it_exists(monkeypatch):
    import sys
    import types

    mod = types.ModuleType("app.modules.areastats.pictures")

    async def then_and_now(db, area_key):
        return area_key == "kharadi"

    mod.then_and_now = then_and_now
    monkeypatch.setitem(sys.modules, "app.modules.areastats.pictures", mod)
    assert await pictures.has_then_now(FakeDb(), "kharadi") is True
    assert await pictures.has_then_now(FakeDb(), "wagholi") is False


async def test_none_when_the_function_itself_fails(monkeypatch):
    import sys
    import types

    mod = types.ModuleType("app.modules.areastats.pictures")

    async def then_and_now(db, area_key):
        raise RuntimeError("boom")

    mod.then_and_now = then_and_now
    monkeypatch.setitem(sys.modules, "app.modules.areastats.pictures", mod)
    assert await pictures.has_then_now(FakeDb(), "kharadi") is None
