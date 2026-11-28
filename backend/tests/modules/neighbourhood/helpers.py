"""Register records for the neighbourhood tests, shaped as newsroom's `projects` collection holds them."""
from datetime import datetime, timezone

from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 28, 9, 0, tzinfo=timezone.utc)
KHARADI = (18.5510, 73.9400)


def project(regno: str, place: str = "kharadi", pin=None, completion: str = "2029-06-30", homes: int = 100, **more) -> dict:
    d = {"_id": regno, "regno": regno, "name": f"Project {regno}", "promoter": "Builder", "pincode": "411014",
         "pune_place": place, "pune_place_name": place.replace("_", " ").title(), "page_slug": f"project-{regno.lower()}",
         "completion_now": completion, "units_total": homes, "building_totals": {"units_residential": homes}}
    if pin:
        d["geo"] = {"lat": pin[0], "lon": pin[1], "located_from": "google"}
        d["enrichment"] = {"steps": {"places": {"ok": True}}}
    d.update(more)
    return d


async def db_with(*docs) -> FakeDb:
    db = FakeDb()
    for d in docs:
        await db.projects.insert_one(d)
    return db
