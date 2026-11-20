"""New-project alerts on WhatsApp (whatsapp/alerts.py) and the project page's price-sheet ask (brain.page_ask)."""
from datetime import datetime, timedelta

import pytest

from app.modules.whatsapp import alerts

from .helpers import BUYER, NOW, PID, make, say

pytestmark = pytest.mark.asyncio

SEND_TIME = datetime(2026, 10, 8, 10, 0, 0)  # 15:30 in Pune, a week after NOW


async def conv_of(db):
    return await db.get_collection("whatsapp_conversations").find_one({"_id": f"{PID}:{BUYER}"})


def projects(*names):
    rows = [{"regno": f"P5210000000{i}", "name": n, "builder": "Gera", "homes": 120, "slug": n.lower().replace(" ", "-"),
             "registered_on": "2026-10-05"} for i, n in enumerate(names)]

    async def new_projects(db, place, since):
        new_projects.asked = (place, since)
        return rows
    return new_projects


@pytest.fixture(autouse=True)
def _reset():
    yield
    alerts.configure(new_projects=None)


async def test_alert_with_a_place_and_size_signs_the_chat_up_and_says_how_to_stop():
    svc, db, _, _ = make()
    r = await say(svc, "ALERT kharedi 2bhk")   # spelt by ear
    conv = await conv_of(db)
    assert conv["alert"]["place"] == "kharadi" and conv["alert"]["bhk"] == 2 and conv["alert"]["checked_at"] == NOW
    assert "Kharadi" in r["reply"] and "ALERT OFF" in r["reply"] and "/projects/area/kharadi/2-bhk" in r["reply"]
    assert conv["lead_id"]   # the buyer who asked is a lead like any other


async def test_alert_without_a_place_asks_for_one_and_signs_nothing_up():
    svc, db, _, _ = make()
    r = await say(svc, "alert")
    assert "ALERT Kharadi 2BHK" in r["reply"] and not (await conv_of(db)).get("alert")


async def test_alert_off_drops_the_alert():
    svc, db, _, _ = make()
    await say(svc, "ALERT Wagholi")
    r = await say(svc, "ALERT OFF")
    assert (await conv_of(db))["alert"] is None and "stopped" in r["reply"].lower()


async def test_a_due_alert_sends_the_new_projects_once_inside_the_window_as_plain_text():
    svc, db, _, clock = make()
    await say(svc, "ALERT Kharadi")
    clock["now"] = SEND_TIME
    await db.get_collection("whatsapp_conversations").update_one({"_id": f"{PID}:{BUYER}"}, {"$set": {"last_inbound_at": SEND_TIME - timedelta(hours=1)}})
    alerts.configure(new_projects=projects("Gera Island", "Kolte Sky"))
    assert await alerts.send_due(db, svc, SEND_TIME) == 1
    conv = await conv_of(db)
    last = conv["messages"][-1]
    assert last["sent_by"] == "alert" and "Gera Island by Gera, 120 homes" in last["text"] and "Kolte Sky" in last["text"]
    assert sorted(conv["alert"]["sent"]) == ["P52100000000", "P52100000001"]
    out = [m for m in await db.get_collection("whatsapp_messages").find({"direction": "out"}).to_list(50) if "Gera Island" in m["text"]]
    assert out[0]["type"] == "text"
    # the next week: the same projects are never sent again, and an empty week sends nothing
    nxt = SEND_TIME + timedelta(days=7)
    assert await alerts.send_due(db, svc, nxt) == 0


async def test_outside_the_window_the_alert_goes_as_the_marketing_template():
    svc, db, _, clock = make()
    await say(svc, "ALERT Kharadi")
    alerts.configure(new_projects=projects("Gera Island"))
    assert await alerts.send_due(db, svc, SEND_TIME) == 1
    rec = (await db.get_collection("whatsapp_messages").find({"type": "template"}).to_list(5))[0]
    assert rec["template"] == alerts.TEMPLATE and "Gera Island" in rec["text"] and "ALERT OFF" in rec["text"]


async def test_no_alert_before_its_week_at_night_or_after_stop():
    svc, db, _, _ = make()
    await say(svc, "ALERT Kharadi")
    alerts.configure(new_projects=projects("Gera Island"))
    assert await alerts.send_due(db, svc, NOW + timedelta(days=3)) == 0              # not a week yet
    assert await alerts.send_due(db, svc, datetime(2026, 10, 8, 18, 0)) == 0          # 23:30 in Pune
    await say(svc, "STOP")
    assert await alerts.send_due(db, svc, SEND_TIME) == 0


async def test_a_failing_chat_does_not_stop_the_others():
    svc, db, _, _ = make()
    await say(svc, "ALERT Kharadi")
    await db.get_collection("whatsapp_conversations").insert_one({"_id": f"{PID}:919000000000", "wa_id": "919000000000", "phone_number_id": PID,
                                                                  "alert": {"place": "wagholi", "name": "Wagholi", "checked_at": NOW}})
    calls = []

    async def new_projects(db, place, since):
        calls.append(place)
        if place == "wagholi":
            raise RuntimeError("register down")
        return [{"regno": "P1", "name": "Gera Island", "homes": None, "builder": None}]
    alerts.configure(new_projects=new_projects)
    assert await alerts.send_due(db, svc, SEND_TIME) == 1 and sorted(calls) == ["kharadi", "wagholi"]


# ---- the project page's WhatsApp ask -----------------------------------------------------------------------------------------
async def test_the_project_pages_whatsapp_message_is_a_price_sheet_ask_for_the_team():
    svc, db, _, _ = make()
    r = await say(svc, "Hi, please send today's price sheet and floor plans for Gera Island (page gera-island-kharadi)")
    assert "Gera Island" in r["reply"] and "price sheet" in r["reply"]
    conv = await conv_of(db)
    assert conv["needs_human"] and conv["context"]["slug"] == "gera-island-kharadi" and "project page" in conv["context"]["came_from"]
    assert any("Gera Island" in q for q in conv["data"]["questions"])
