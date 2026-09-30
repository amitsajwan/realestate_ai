import importlib.util
from datetime import date
from pathlib import Path

import pytest

from app.modules.calendar.store import Store

from ..fakes import FakeDb

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "calendar_admin.py"


@pytest.fixture
def admin():
    spec = importlib.util.spec_from_file_location("calendar_admin", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_dry_check_passes_on_the_library(admin, capsys):
    assert admin.main(["--dry-check"]) == 0
    assert "40 posts checked, 0 problem(s)" in capsys.readouterr().out


def test_dry_check_fails_on_a_bad_caption(admin, monkeypatch, capsys):
    from app.modules.calendar import library

    bad = library.Entry("bad", "myth", "K", "T", ("p",), "The best flat, call 9876543210\nNo prompt.", ("#a",), "review")
    monkeypatch.setattr(library, "ENTRIES", [bad])
    assert admin.dry_check() == 1 and "FAIL bad" in capsys.readouterr().out


async def test_seed_is_idempotent_and_skips_used_slugs(admin, monkeypatch):
    store = Store(FakeDb())

    async def fake_store():
        return store

    monkeypatch.setattr(admin, "_store", fake_store)
    await admin.seed(date(2026, 10, 6), 8)
    rows = await store.all()
    assert len(rows) > 40 and all(r["status"] == "scheduled" for r in rows)
    assert all(r["image_path"].startswith("calendar/ig/") for r in rows if r["channel"] == "instagram")
    assert all("http" not in r["caption"] for r in rows if r["channel"] == "instagram")
    await admin.seed(date(2026, 10, 6), 8)  # second run adds nothing
    assert len(await store.all()) == len(rows)
    for ch in ("facebook_page", "instagram"):
        slugs = [r["slug"] for r in rows if r["channel"] == ch]
        assert len(slugs) == len(set(slugs))


def test_preview_renders_cards_and_prints_the_schedule(admin, tmp_path, capsys):
    assert admin.main(["preview", "--out", str(tmp_path), "--start", "2026-10-06", "--weeks", "1"]) == 0
    out = capsys.readouterr().out
    assert "rendered 80 cards" in out and "IST" in out
    assert (tmp_path / "ig" / "red-flags-in-ads.jpg").is_file() and (tmp_path / "red-flags-in-ads.jpg").is_file()
