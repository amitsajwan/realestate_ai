"""A listing starts from the project's page, and a published listing is on that page at once (owner, 2026-11-06, docs/plan/listing-flow.md)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.ai_listing.service import PAGE_PRICES, AIListingService
from app.modules.areastats import pagestart
from app.modules.listings import projectlive
from app.modules.newsroom.store import Store
from app.modules.propertyfacts.router import with_sheet
from app.modules.tracking.service import TrackingService  # noqa: F401  (the fakes' module set)

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio
NOW = datetime(2026, 11, 6, 12, 0, 0, tzinfo=timezone.utc)
REGNO = "P52100000001"


def priced(*rows):
    return {"at": NOW, "rows": [{"bhk": b, "from_inr": p, "sources": [{"site": "a.test", "quote": f"{b} from {p}"}]} for b, p in rows]}


def project(**kw):
    return {"_id": REGNO, "regno": REGNO, "name": "GODREJ IVARA", "promoter": "Godrej Properties Limited", "locality": "kharadi",
            "page_slug": "godrej-ivara-kharadi", "completion_now": "2029-10-30", "completion_at_registration": "2029-10-30",
            "units_total": 400, "units_booked": 100, **kw}


def listing(lid, agent="A1", **kw):
    return {"_id": lid, "agent_id": agent, "rera_no": REGNO, "status": "live", "price_inr": 8_000_000, "bhk": 2, "transaction": "sale",
            "property_type": "apartment", "media": [], "updated_at": datetime(2026, 11, 1), **kw}


async def db_with(*docs):
    db = FakeDb()
    for d in docs:
        await Store(db).projects.insert_one(dict(d))
    return db


class Register:
    def __init__(self, doc):
        self.doc = doc

    async def project(self, regno):
        return self.doc if regno == self.doc["regno"] else None

    async def all_projects(self):
        return [self.doc]


# ---- what the page offers ------------------------------------------------------------------------------------------------
async def test_the_page_gives_its_sizes_at_their_lowest_published_price_smallest_first():
    db = await db_with(project(prices=priced(("3 BHK", 15_000_000), ("2 BHK", 9_000_000), ("All homes", 8_000_000))))
    start = await pagestart.listing_start(db, REGNO, NOW)
    assert start["homes"] == [{"bhk": 2.0, "price_inr": 9_000_000}, {"bhk": 3.0, "price_inr": 15_000_000}]
    assert start["slug"] == "godrej-ivara-kharadi" and start["name"] == "Godrej Ivara" and start["property_type"] == "apartment"


async def test_a_page_with_no_published_price_offers_no_sizes():
    start = await pagestart.listing_start(await db_with(project()), REGNO, NOW)
    assert start["homes"] == [] and start["photos"] == []


async def test_only_pictures_the_page_may_show_are_offered():
    photos = [{"path": "images/own.jpg", "alt": "Tower", "source": "builder"}, {"url": "https://portal.test/x.jpg", "source": "portal"}]
    start = await pagestart.listing_start(await db_with(project(profile={"photos": photos})), REGNO, NOW)
    assert start["photos"] == [{"url": "/uploads/images/own.jpg", "alt": "Tower"}]


async def test_a_number_with_no_page_gives_nothing():
    assert await pagestart.listing_start(await db_with(project()), "P52100009999", NOW) is None


# ---- the draft -------------------------------------------------------------------------------------------------------------
PAGE = {"slug": "godrej-ivara-kharadi", "name": "Godrej Ivara", "photos": [], "property_type": "apartment", "mine": None, "others": 0,
        "homes": [{"bhk": 2.0, "price_inr": 9_000_000}, {"bhk": 3.0, "price_inr": 15_000_000}]}


async def test_the_draft_holds_mahareras_facts_and_the_pages_sizes_ready_to_publish():
    d = await AIListingService().draft_from_project(REGNO, Register(project()), PAGE)
    assert d.missing == [] and d.draft["configurations"] == PAGE["homes"] and d.page == PAGE
    assert d.draft["title"].startswith("Godrej Ivara") and "2 BHK and up from" in d.draft["title"]
    assert (d.draft["price_inr"], d.draft["bhk"], d.draft["rera_no"]) == (9_000_000, 2.0, REGNO)
    assert d.draft["listing_scope"] == "layout" and d.draft["transaction"] == "sale"


async def test_prices_from_the_page_are_marked_for_the_agent_to_check():
    d = await AIListingService().draft_from_project(REGNO, Register(project()), PAGE)
    assert d.sources["price_inr"] == "page" and d.confidence["price_inr"] < 0.7 and PAGE_PRICES in d.warnings
    assert d.confidence["property_type"] >= 0.7 and d.confidence["bhk"] >= 0.7   # nothing else nags them


async def test_with_no_published_prices_the_agent_is_asked_for_a_price_and_told_nothing_false():
    d = await AIListingService().draft_from_project(REGNO, Register(project()), {**PAGE, "homes": []})
    assert "price_inr" in d.missing and PAGE_PRICES not in d.warnings and "configurations" not in d.draft


# ---- two agents, one project -------------------------------------------------------------------------------------------------
def test_the_most_complete_listing_leads_not_the_last_edited():
    rich = listing("rich", configurations=[{"bhk": 2, "price_inr": 1}, {"bhk": 3, "price_inr": 2}], updated_at=datetime(2026, 10, 1))
    fresh = listing("fresh", media=[{"url": "/a.jpg"}] * 5, updated_at=datetime(2026, 11, 5))
    assert projectlive.best([fresh, rich])["_id"] == "rich"


def test_photos_decide_next_and_the_newest_breaks_a_tie():
    old, new = listing("old", updated_at=datetime(2026, 10, 1)), listing("new", updated_at=datetime(2026, 11, 1))
    assert projectlive.best([old, new])["_id"] == "new"
    assert projectlive.best([new, listing("pics", media=[{"url": "/a.jpg"}], updated_at=datetime(2026, 9, 1))])["_id"] == "pics"
    assert projectlive.best([]) is None


# ---- the page, straight after publishing -----------------------------------------------------------------------------------
async def test_a_published_listing_is_on_the_project_page_with_no_facts_gathered():
    db = FakeDb()
    db.get_collection("listings").docs.append(listing("L1", configurations=[{"bhk": 2, "price_inr": 8_000_000}, {"bhk": 3, "price_inr": 12_000_000}]))
    out = await with_sheet(db, None, regno=REGNO)
    assert out["offer"]["price_inr"] == 8_000_000 and out["offer"]["source"] == "the agent's listing" and len(out["offer"]["homes"]) == 2


async def test_a_draft_or_withdrawn_listing_is_not_on_the_page():
    db = FakeDb()
    db.get_collection("listings").docs.append(listing("L1", status="draft"))
    assert await with_sheet(db, None, regno=REGNO) is None


async def test_gathered_facts_keep_their_offer_and_gain_the_sheet():
    db = FakeDb()
    db.get_collection("listings").docs.append(listing("L1"))
    out = await with_sheet(db, {"maharera": {"rera_no": REGNO}, "offer": {"price_inr": 7_000_000, "source": "post"}})
    assert out["offer"]["price_inr"] == 7_000_000


async def test_an_old_listing_day_is_read_from_its_update():
    db = FakeDb()
    db.get_collection("listings").docs.append(listing("L1", updated_at=NOW - timedelta(days=1)))
    assert (await with_sheet(db, None, regno=REGNO))["offer"]["read_at"] == "2026-11-05"
