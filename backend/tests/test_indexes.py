import pytest

from app.core.indexes import INDEXES, ensure_indexes

pytestmark = pytest.mark.asyncio


class FakeColl:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    async def create_index(self, keys, **opts):
        if self.fail:
            raise RuntimeError("E11000 duplicate key")
        self.calls.append((keys, opts))


class FakeDb(dict):
    def __missing__(self, name):
        self[name] = FakeColl()
        return self[name]


async def test_every_index_is_requested_and_ttl_and_unique_are_set():
    db = FakeDb()
    out = await ensure_indexes(db)
    assert out == {"created": len(INDEXES), "failed": []}
    assert {"unique": True, "sparse": True} in [o for _, o in db["agent_public_profiles"].calls]
    assert {"expireAfterSeconds": 86400} in [o for _, o in db["otp_codes"].calls]


async def test_one_failing_index_never_stops_startup():
    db = FakeDb()
    db["contacts"] = FakeColl(fail=True)
    out = await ensure_indexes(db)
    assert len(out["failed"]) == 3 and out["created"] == len(INDEXES) - 3


async def test_a_project_page_is_found_by_its_address_without_a_scan():
    db = FakeDb()
    await ensure_indexes(db)
    keys = [k for k, _ in db["projects"].calls]
    assert [("page_slug", 1)] in keys and [("old_slugs", 1)] in keys
