"""Unit tests for areastats.sellers – classification logic only (no MongoDB required)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.areastats.sellers import (
    PORTALS,
    OWN_SITE,
    classify,
    sellers,
    _to_row,
)


# ---------------------------------------------------------------------------
# classify() – pure function, no I/O
# ---------------------------------------------------------------------------

class TestClassify:
    def test_portal_99acres(self):
        assert classify("https://www.99acres.com/search/property/buy/pune", "", "") == "portals"

    def test_portal_housing(self):
        assert classify("https://housing.com/in/buy/pune", "", "") == "portals"

    def test_portal_nobroker(self):
        assert classify("https://www.nobroker.in/property/pune", "", "") == "portals"

    def test_portal_housiey(self):
        assert classify("https://housiey.com/projects/pune/some-project", "", "") == "portals"

    def test_own_site_excluded(self):
        assert classify(f"https://{OWN_SITE}/agent/ravi", "", "") is None

    def test_maharera_excluded(self):
        assert classify("https://maharashtra.gov.in/site", "", "") is None

    def test_youtube_excluded(self):
        assert classify("https://www.youtube.com/watch?v=abc", "", "") is None

    def test_builder_by_promoter_key(self):
        # Promoter "Puranik Builders Pvt Ltd" -> key "puranik builders"
        # Microsite domain: "puranikbuilders.com" -> host_slug = "puranikbuilderscom"
        # "puranik" in host_slug and "builders" in host_slug -> builder
        result = classify("https://www.puranikbuilders.com/projects", "", "Puranik Builders Pvt Ltd")
        assert result == "builder"

    def test_builder_by_project_name(self):
        # Project name "Neoworld" in "sparkleneoworld.com"
        result = classify("https://sparkleneoworld.com/neoworld-project", "Neoworld", "")
        assert result == "builder"

    def test_builder_31palma(self):
        # Project "31 Palma Drive Phase 2", promoter not known -> agents if no match
        # "31palma-drive.com" -> host_slug="31palmadrivecm" ... hmm
        # "31palmadrive-kharadi.in" -> words "31", "palmadrive", "kharadi"
        # project name "31 Palma Drive" -> parts ["31","palma","drive"]; "palma" in "31palmadrivekharadiin" ✓ "drive" ✓ "31" ✓
        result = classify("https://31palmadrive-kharadi.in/project", "31 Palma Drive", "")
        assert result == "builder"

    def test_channel_partner(self):
        # bhandariassociates.co.in is an agent microsite
        result = classify("https://bhandariassociates.co.in/projects/31-palma-drive", "31 Palma Drive", "Some Developer")
        assert result == "agents"

    def test_jllhomes(self):
        result = classify("https://www.jllhomes.co.in/", "", "")
        assert result == "agents"

    def test_empty_link(self):
        assert classify("", "", "") is None

    def test_link_with_no_host(self):
        assert classify("not-a-url", "", "") is None

    def test_all_portals_classified(self):
        """Every portal domain in the fixed list is classified as 'portals'."""
        for domain in PORTALS:
            link = f"https://{domain}/some/path"
            result = classify(link, "", "")
            assert result == "portals", f"{domain} was classified as {result!r}, expected 'portals'"


# ---------------------------------------------------------------------------
# _to_row() – shape check
# ---------------------------------------------------------------------------

class TestToRow:
    def test_organic_result(self):
        raw = {"title": "Foo", "link": "https://99acres.com/foo", "position": 3, "ad": False}
        row = _to_row(raw)
        assert row["site"] == "99acres.com"
        assert row["title"] == "Foo"
        assert row["position"] == 3
        assert row["ad"] is False

    def test_ad_result(self):
        raw = {"title": "Bar Ad", "link": "https://squareyards.com/ad", "position": 0, "ad": True}
        row = _to_row(raw)
        assert row["ad"] is True

    def test_missing_fields_tolerated(self):
        row = _to_row({})
        assert row["site"] == ""
        assert row["title"] == ""
        assert row["link"] == ""
        assert row["position"] is None
        assert row["ad"] is False


# ---------------------------------------------------------------------------
# sellers() – async, with mocked MongoDB
# ---------------------------------------------------------------------------

def _make_db(
    project=None,
    search_results=None,
    listings=None,
    profiles=None,
):
    """Build a minimal mock database that sellers() can iterate over."""
    db = MagicMock()

    def _coll(name):
        coll = MagicMock()

        if name == "projects":
            coll.find_one = AsyncMock(return_value=project)
        elif name == "web_search_results":
            docs = search_results or []

            async def _iter(*args, **kwargs):
                for d in docs:
                    yield d

            cursor = MagicMock()
            cursor.__aiter__ = _iter
            cursor.sort = MagicMock(return_value=cursor)
            cursor.limit = MagicMock(return_value=cursor)
            coll.find = MagicMock(return_value=cursor)
        elif name == "listings":
            docs = listings or []

            async def _iter2(*args, **kwargs):
                for d in docs:
                    yield d

            cursor2 = MagicMock()
            cursor2.__aiter__ = _iter2
            coll.find = MagicMock(return_value=cursor2)
        elif name == "agent_public_profiles":
            profile_map = {p["agent_id"]: p for p in (profiles or [])}

            async def _find_one(flt):
                aid = flt.get("agent_id")
                return profile_map.get(aid)

            coll.find_one = AsyncMock(side_effect=_find_one)

        return coll

    db.get_collection = MagicMock(side_effect=_coll)
    return db


@pytest.mark.asyncio
async def test_sellers_empty_when_no_results():
    db = _make_db()
    result = await sellers(db, "P52000000001")
    assert result["searched_at"] is None
    assert result["query"] is None
    assert result["groups"]["agents"] == []
    assert result["groups"]["portals"] == []


@pytest.mark.asyncio
async def test_sellers_classifies_portals():
    from datetime import datetime
    search_doc = {
        "_id": "Neoworld Lohegaon Pune",
        "kind": "project",
        "regno": "P52000000001",
        "at": datetime(2026, 10, 13),
        "results": [
            {"title": "Neoworld on 99acres", "link": "https://99acres.com/neoworld", "position": 2, "ad": False, "type": "organic"},
            {"title": "Neoworld on Housing", "link": "https://housing.com/neoworld", "position": 4, "ad": False, "type": "organic"},
        ],
    }
    db = _make_db(
        project={"_id": "P52000000001", "name": "Neoworld", "promoter": "Sparkling Builders Pvt Ltd"},
        search_results=[search_doc],
    )
    result = await sellers(db, "P52000000001")
    assert len(result["groups"]["portals"]) == 2
    assert result["groups"]["agents"] == []
    assert result["searched_at"] == datetime(2026, 10, 13)


@pytest.mark.asyncio
async def test_sellers_classifies_builder():
    from datetime import datetime
    search_doc = {
        "_id": "Neoworld Lohegaon Pune",
        "kind": "project",
        "regno": "P52000000002",
        "at": datetime(2026, 10, 13),
        "results": [
            {"title": "Sparkling Neoworld official site",
             "link": "https://sparkleneoworld.com/neoworld", "position": 1, "ad": False, "type": "organic"},
        ],
    }
    db = _make_db(
        project={"_id": "P52000000002", "name": "Neoworld", "promoter": "Sparkling Builders Pvt Ltd"},
        search_results=[search_doc],
    )
    result = await sellers(db, "P52000000002")
    assert len(result["groups"]["builder"]) == 1
    assert result["groups"]["builder"][0]["site"] == "sparkleneoworld.com"


@pytest.mark.asyncio
async def test_sellers_excludes_not_marketers():
    from datetime import datetime
    search_doc = {
        "_id": "Some Project Pune",
        "kind": "project",
        "regno": "P52000000003",
        "at": datetime(2026, 10, 13),
        "results": [
            {"title": "YouTube video", "link": "https://www.youtube.com/watch?v=xyz",
             "position": 5, "ad": False, "type": "organic"},
            {"title": "Our own page", "link": f"https://{OWN_SITE}/agent/ravi",
             "position": 6, "ad": False, "type": "organic"},
        ],
    }
    db = _make_db(search_results=[search_doc])
    result = await sellers(db, "P52000000003")
    # Both excluded
    total = sum(len(v) for v in result["groups"].values())
    assert total == 0


@pytest.mark.asyncio
async def test_sellers_skips_related_questions():
    from datetime import datetime
    search_doc = {
        "_id": "Prasun Elara Lohegaon Pune",
        "kind": "project",
        "regno": "P52000000004",
        "at": datetime(2026, 10, 13),
        "results": [
            {"title": "Related search", "link": "", "position": 0, "ad": False, "type": "related"},
            {"title": "People also ask", "link": "https://somesite.com/q", "position": 0, "ad": False, "type": "question"},
            {"title": "Actual portal", "link": "https://99acres.com/prasun-elara", "position": 2, "ad": False, "type": "organic"},
        ],
    }
    db = _make_db(search_results=[search_doc])
    result = await sellers(db, "P52000000004")
    assert len(result["groups"]["portals"]) == 1


@pytest.mark.asyncio
async def test_sellers_platform_agents():
    from datetime import datetime
    db = _make_db(
        listings=[
            {"_id": "lst1", "rera_no": "P52000000005", "agent_id": "agent1", "status": "live"},
        ],
        profiles=[
            {"agent_id": "agent1", "slug": "ravi-sharma-pune", "display_name": "Ravi Sharma"},
        ],
    )
    result = await sellers(db, "P52000000005")
    platform = result["groups"]["platform"]
    assert len(platform) == 1
    assert platform[0]["title"] == "Ravi Sharma"
    assert "ravi-sharma-pune" in platform[0]["link"]
    assert platform[0]["ad"] is False
    # No phone numbers
    for row in platform:
        assert "phone" not in row
