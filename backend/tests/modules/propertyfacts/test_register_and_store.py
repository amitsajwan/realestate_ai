"""Our MahaRERA register is asked before MahaRERA, and every gathered sheet is kept."""
from datetime import datetime, timedelta, timezone

from app.modules.propertyfacts import gather as gather_mod
from app.modules.propertyfacts import registration
from app.modules.propertyfacts.store import FactsStore, key_of

from .test_registration import LISTING, NOW, Fakes

CHECKED = datetime(2026, 10, 1, tzinfo=timezone.utc)
RECORD = {"_id": "P52100076768", "regno": "P52100076768", "name": "Gulmohar City", "promoter": "", "taluka": "Shirur",
          "district": "Pune", "pincode": "412209", "source_url": "https://maharerait.maharashtra.gov.in/public/project/view/46398",
          "project_type": "Plotted", "registered_on": "2024-06-28", "completion_at_registration": "2028-12-31",
          "completion_now": "2029-04-30", "units_total": 123, "units_booked": 0, "details_ok": True, "details_checked_at": CHECKED}
OTHER = {**RECORD, "_id": "P52100077275", "regno": "P52100077275", "name": "GULMOHAR CITY", "taluka": "Khed", "pincode": "410501"}


class Register:
    def __init__(self, *docs):
        self.docs = {d["_id"]: d for d in docs}

    async def project(self, regno):
        return self.docs.get(regno)

    async def all_projects(self, limit=20000):
        return list(self.docs.values())


class Col:
    def __init__(self):
        self.docs = {}

    async def update_one(self, flt, update, upsert=False):
        self.docs.setdefault(flt["_id"], {"_id": flt["_id"]}).update(update["$set"])

    async def find_one(self, flt):
        if "_id" in flt:
            return self.docs.get(flt["_id"])
        return next((d for d in self.docs.values() if all(d.get(k) == v for k, v in flt.items())), None)


class Db:
    def __init__(self):
        self.col = Col()

    def get_collection(self, name):
        return self.col


class WithRegister(Fakes):
    def __init__(self, register, **kw):
        super().__init__(**kw)
        self.register = register
        self.facts_store = FactsStore(Db())


async def test_a_fresh_register_record_answers_without_asking_maharera():
    f = WithRegister(Register(RECORD, OTHER))
    s = await gather_mod.gather(LISTING, f, NOW)
    assert not any(isinstance(c, int) or "maharera" in str(c) for c in f.calls)  # no MahaRERA search, no project API
    assert s.match.how == "name and taluka (Shirur) (our register)"
    assert s.facts["possession_now"].value == "2029-04-30" and s.facts["possession_now"].readings[-1].fetched_at == CHECKED


async def test_a_rera_number_alone_is_enough_with_the_register():
    f = WithRegister(Register(RECORD))
    s = await gather_mod.gather({"locality": "Ranjangaon", "rera_no": "P52100076768", "property_type": "plot"}, f, NOW)
    assert s.facts["units_total"].value == 123 and s.facts["project_name"].value == "Gulmohar City"


async def test_stale_or_missing_register_details_go_to_maharera():
    stale = {**RECORD, "details_checked_at": NOW.replace(tzinfo=timezone.utc) - timedelta(days=90)}
    f = WithRegister(Register(stale))
    s = await gather_mod.gather(LISTING, f, NOW)
    assert 46398 in f.calls and "our register" not in s.match.how
    f = WithRegister(Register())
    await gather_mod.gather(LISTING, f, NOW)
    assert 46398 in f.calls


async def test_the_sheet_is_kept():
    f = WithRegister(Register(RECORD))
    await gather_mod.gather(LISTING, f, NOW)
    doc = await f.facts_store.get("P52100076768")
    facts = {x["key"]: x for x in doc["facts"]}
    assert facts["possession_now"]["level"] == "official" and facts["possession_now"]["readings"][0]["source"] == "maharera"
    assert facts["nearby.hospital"]["usable"] and doc["gathered_at"] == NOW


def test_key_without_a_registration():
    assert key_of({"project_name": "Sample Heights", "locality": "Kharadi"}) == "sample-heights-kharadi"


def test_fresh_needs_ok_details_and_a_recent_check():
    assert registration.fresh(RECORD, NOW)
    assert not registration.fresh({**RECORD, "details_ok": False}, NOW)
    assert not registration.fresh({**RECORD, "details_checked_at": None}, NOW)


async def test_public_view_shows_usable_facts_with_sources_and_is_found_by_alias():
    from app.modules.propertyfacts.public import view
    f = WithRegister(Register(RECORD))
    await gather_mod.gather({**LISTING, "price_inr": 3230000, "carpet_sqft": 1927}, f, NOW)
    doc = await f.facts_store.find(project="Gulmohar City", locality="Ranjangaon")   # no RERA on the listing
    assert doc and doc["_id"] == "P52100076768"
    v = view(doc)
    assert v["maharera"]["completion_now"] == "2029-04-30" and v["maharera"]["moved_months"] == 4
    assert v["maharera"]["url"].endswith("/46398") and v["maharera"]["read_at"].startswith("2026-10-01")
    assert v["nearby"] == [{"label": "Hospital", "name": "Narwade Hospital", "km": 0.3},
                           {"label": "Industrial area", "name": "IndoSpace", "km": 2.4}]
    assert v["numbers"]["price_per_sqft"] == 1676 and v["numbers"]["emi"]["emi"] == 22425
    assert await f.facts_store.find(project="Other", locality="Ranjangaon") is None


def test_public_view_hides_held_back_facts_and_empty_sheets():
    from app.modules.propertyfacts.public import view
    held = {"facts": [{"key": "price_per_sqft", "value": 1800, "level": "single", "usable": False, "readings": []}]}
    assert view(held) is None and view(None) is None
