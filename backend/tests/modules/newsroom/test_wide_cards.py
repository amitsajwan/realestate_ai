"""The site's wide (1200x675) news card for stories that were drawn before it existed: a few per newsroom cycle, newest first,
the posted social cards untouched, and a card that cannot be drawn marked so it is not tried again."""
from datetime import timedelta
from pathlib import Path

from PIL import Image

from app.modules.newsroom import adapters, cards
from app.modules.newsroom.samples import AS_OF, SAMPLES
from app.modules.newsroom.store import Store

from ..fakes import FakeDb


async def put(store, doc, status, **extra):
    await store.items.insert_one({**doc, "status": status, "updated_at": AS_OF + timedelta(minutes=len(store.items.docs)), **extra})


def social(doc):
    return {"ig": f"news/{doc['_id']}-ig.jpg", "fb": f"news/{doc['_id']}-fb.jpg", "variant": "headline"}


async def test_public_items_without_a_wide_card_are_listed_newest_first_and_only_those():
    store = Store(FakeDb())
    await put(store, SAMPLES[0], "published", card=social(SAMPLES[0]))                                   # needs one
    await put(store, SAMPLES[1], "approved", card={**social(SAMPLES[1]), "web": "news/b-web.jpg"})       # has one
    await put(store, SAMPLES[2], "pending_review", card=social(SAMPLES[2]))                              # not public
    await put(store, SAMPLES[3], "published")                                                            # no cards at all: the publisher's job
    await put(store, SAMPLES[4], "published", card={**social(SAMPLES[4]), "web": ""})                    # tried, could not be drawn
    await put(store, SAMPLES[5], "scheduled", card=social(SAMPLES[5]))                                   # needs one, newer
    assert [d["_id"] for d in await store.public_without_wide(10)] == [SAMPLES[5]["_id"], SAMPLES[0]["_id"]]
    assert [d["_id"] for d in await store.public_without_wide(1)] == [SAMPLES[5]["_id"]]


async def test_wide_cards_step_draws_the_missing_ones_and_leaves_the_social_cards_alone(tmp_path):
    store = Store(FakeDb())
    for d in SAMPLES[:3]:
        await put(store, d, "published", card=social(d))
    before = [(d["_id"], d["updated_at"]) for d in await store.public(10)]
    assert await adapters.wide_cards(store, 2, uploads=tmp_path) == 2
    after = await store.public(10)
    assert [(d["_id"], d["updated_at"]) for d in after] == before  # the public order is by updated_at: an old story must not jump to the top
    done = [d for d in after if "web" in (d.get("card") or {})]
    assert [d["_id"] for d in done] == [SAMPLES[2]["_id"], SAMPLES[1]["_id"]]  # newest first, the limit kept
    for d in done:
        assert d["card"]["web"] == f"news/{d['_id']}-web.jpg" and d["card"]["fb"] == f"news/{d['_id']}-fb.jpg"
        assert Image.open(Path(tmp_path) / d["card"]["web"]).size == (1200, 675)
        assert not (Path(tmp_path) / d["card"]["fb"]).exists()  # the posted cards are not drawn again
    assert await adapters.wide_cards(store, 5, uploads=tmp_path) == 1  # the one left
    assert await adapters.wide_cards(store, 5, uploads=tmp_path) == 0


async def test_an_item_whose_wide_card_cannot_be_drawn_is_marked_and_not_tried_again(tmp_path, monkeypatch):
    store = Store(FakeDb())
    await put(store, SAMPLES[0], "published", card=social(SAMPLES[0]))

    def refuse(*a, **k):
        raise cards.CardError("does not fit")
    monkeypatch.setattr(cards, "_render_wide", refuse)
    assert await adapters.wide_cards(store, 5, uploads=tmp_path) == 0
    doc = await store.get(SAMPLES[0]["_id"])
    assert doc["card"]["web"] == "" and doc["card"]["fb"] == social(SAMPLES[0])["fb"]
    assert await store.public_without_wide(5) == []
