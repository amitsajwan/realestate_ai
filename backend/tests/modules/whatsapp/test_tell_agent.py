"""What we send an agent stays in their Inbox thread, and a tap on a button says which listing it answers."""
from datetime import timedelta

from app.modules.inbox.service import InboxService

from .helpers import NOW, cfg, epoch, make, value

WA = "919967464952"


def tap(text, about_id, ts=None):
    return {"from": WA, "id": f"wamid.tap{text}", "timestamp": epoch(ts or NOW), "type": "button",
            "button": {"text": text, "payload": text}, "context": {"id": about_id}}


async def test_a_message_to_an_agent_is_kept_in_their_thread():
    svc, db, rec, _ = make()
    out = await svc.tell_agent(WA, "Kausar Patanwala", "agent_post_live_v1", ["Kausar", "UBC", "a", "b"], "Namaste Kausar ji", "UBC", NOW)
    conv = await db.get_collection("whatsapp_conversations").find_one({"wa_id": WA})
    assert conv["role"] == "agent" and conv["agent_id"] == cfg().owner_agent_id
    assert conv["messages"][-1]["text"] == "Namaste Kausar ji"
    kept = await db.get_collection("whatsapp_messages").find_one({"_id": out["_id"]})
    assert kept["template"] == "agent_post_live_v1" and kept["sent_by"] == "auto" and kept["about"] == "UBC"


async def test_a_second_message_joins_the_same_thread():
    svc, db, _, _ = make()
    await svc.tell_agent(WA, "Kausar", "t", [], "one", "UBC", NOW)
    await svc.tell_agent(WA, "Kausar", "t", [], "two", "UBC", NOW)
    assert await db.get_collection("whatsapp_conversations").count_documents({"wa_id": WA}) == 1
    assert [m["text"] for m in (await db.get_collection("whatsapp_conversations").find_one({"wa_id": WA}))["messages"]] == ["one", "two"]


async def test_a_tap_says_which_listing_it_answers_and_opens_the_window():
    svc, db, _, clock = make()
    out = await svc.tell_agent(WA, "Kausar", "agent_post_results_v1", [], "after 2 days", "KP Supernova", NOW)
    m = tap("Boost", out["_id"])
    v = value([m], wa=WA)
    assert await svc.claim(m, v)
    await svc.handle(m, v)
    conv = await db.get_collection("whatsapp_conversations").find_one({"wa_id": WA})
    assert any(x.get("text") == "Boost (KP Supernova)" for x in conv["messages"])
    assert conv["last_inbound_at"] and conv["last_inbound_at"] > NOW - timedelta(minutes=1)
