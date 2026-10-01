import importlib.util
from datetime import date
from pathlib import Path

import pytest

from app.modules.calendar.store import Store

from ..fakes import FakeDb

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "calendar_admin.py"
START = date(2026, 10, 12)


@pytest.fixture
def admin():
    spec = importlib.util.spec_from_file_location("calendar_admin", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_dry_check_passes_on_the_library(admin, capsys):
    assert admin.main(["--dry-check"]) == 0
    assert "39 posts checked, 0 problem(s)" in capsys.readouterr().out


def test_dry_check_fails_on_a_bad_caption(admin, monkeypatch, capsys):
    from app.modules.calendar import library

    bad = library.Entry("bad", "myth", "K", "T", ("p",), "The best flat, call 9876543210\nNo prompt.", ("#a",), "review")
    monkeypatch.setattr(library, "ENTRIES", [bad])
    assert admin.dry_check() == 1 and "FAIL bad" in capsys.readouterr().out


async def test_plan_preview_approve_skip_flow(admin, tmp_path, capsys):
    store = Store(FakeDb())
    made = await admin.plan(store, START, 2, False, False, False, tmp_path / "uploads")
    rows = await store.all()
    assert len(made) == len(rows) == 20 and {r["status"] for r in rows} == {"planned"}
    assert "nothing posts until you approve" in capsys.readouterr().out

    paths = await admin.preview_plan(store, tmp_path / "review", None, tmp_path / "uploads")
    assert sorted(paths) == [1, 2]
    for p in paths.values():
        assert p.is_file() and p.stat().st_size < 1_000_000
    text = (tmp_path / "review" / "week-1-captions.txt").read_text(encoding="utf8")
    assert "instagram" in text and "id=" in text and "Sample listing" in text

    assert await admin.approve(store, None, 1, False) == 10  # --week 1
    assert {r["status"] for r in await store.all() if r["week"] == 1} == {"approved"}
    assert {r["status"] for r in await store.all() if r["week"] == 2} == {"planned"}
    target = next(r for r in await store.all() if r["week"] == 2)
    assert await admin.approve(store, target["_id"], None, False) == 1  # a single id
    assert await admin.approve(store, None, None, True) == 9  # --all takes the rest
    victim = (await store.all())[0]["_id"]
    await admin.skip(store, victim)
    assert (await store.get(victim))["status"] == "skipped"
    await admin.list_rows(store, "approved")
    out = capsys.readouterr().out
    assert "approved" in out and victim not in out
    assert await admin.plan(store, START, 2, False, False, False, tmp_path / "uploads") == []  # idempotent
