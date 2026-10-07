"""Readable, permanent news addresses: a story's public id is `<headline words>-<6 chars of its stored id>`, the same every time;
`/public/news/{id}` answers for that slug and for every older address (the stored id that already-posted captions link to, an
older slug after a headline edit) and always replies with the current slug; digests keep their ids; `area=` filters the list."""
import re
from datetime import datetime, timedelta, timezone

from app.modules.newsroom import digest, roundup
from app.modules.newsroom import public as pub
from app.modules.newsroom.samples import AS_OF, SAMPLES, make_doc

from .test_n3_public import put, setup

HASH = "f5ddeef0763d0726992a04d8a388e7823addd6c2"  # a real story id is the sha1 of its link
NOW = datetime(2026, 10, 3, 5, 7, 29, tzinfo=timezone.utc)
ROUNDUP_PROJECTS = [{"_id": "P52100012345", "name": "Sky Homes", "locality": "lohegaon", "pincode": "411047", "last_modified": "2026-10-01",
                     "source_url": "https://maharera.maharashtra.gov.in/x"}]
SHAPE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def story(id=HASH, title="Lohegaon hospital OPD awaiting approval", areas=("lohegaon",), pillar="locality_life"):
    return make_doc(id, title, ["The Lohegaon hospital OPD is awaiting state approval."], pillar, ["kharadi"], "Pune Mirror") \
        | {"relevance": {"keep": True, "pillar": pillar, "areas": list(areas), "reason": "test"}}


def test_slug_shape_headline_words_then_six_id_chars():
    s = pub.slug(story())
    assert s == "lohegaon-hospital-opd-awaiting-approval-f5ddee" and SHAPE.match(s)
    # 8 words at most, and never ending on a word like "of" or "the" that reads cut off
    assert pub.slug(story(title="Lohegaon hospital OPD still awaiting approval of the state health department")) ==         "lohegaon-hospital-opd-still-awaiting-approval-f5ddee"
    for d in SAMPLES:
        s = pub.slug(d)
        words = s.split("-")
        assert SHAPE.match(s) and words[-1] == d["_id"][:6] and len(words) - 1 <= 8 and len(s) <= 60 + 7
    assert pub.slug(SAMPLES[0]) == "pune-ring-road-10502-crore-approved-a1b2c3"  # "₹10,502" is one number, no symbol


def test_slug_is_ascii_for_accents_and_falls_back_for_hindi_or_marathi_headlines():
    assert pub.slug(story(title="Café near Kharadi’s new road")) == "cafe-near-kharadis-new-road-f5ddee"
    s = pub.slug(story(title="लोहगाव रुग्णालयाला मंजुरी", areas=("lohegaon", "wagholi"), pillar="infrastructure"))
    assert s == "lohegaon-wagholi-infrastructure-news-f5ddee"
    assert pub.slug(story(title="पुणे बातमी", areas=(), pillar="locality_life")) == "pune-locality-life-news-f5ddee"


def test_slug_is_stable_when_nothing_about_the_story_changes():
    d = story()
    first = pub.slug(d)
    later = {**d, "status": "published", "updated_at": AS_OF + timedelta(days=9), "published_at": AS_OF + timedelta(days=9),
             "publish": {"platform_id": "1", "channels": {"facebook": {"ok": True, "permalink": "https://www.facebook.com/1"}}}}
    assert pub.slug(later) == first == pub.slug(story())


def test_digest_and_roundup_ids_are_unchanged():
    dg = digest.sample_digest(SAMPLES)
    assert pub.slug(dg) == dg["_id"] and dg["_id"].startswith("digest-")
    rp = roundup.compose(ROUNDUP_PROJECTS, NOW, "maharera-20261003-103729")
    assert rp and pub.slug(rp) == "maharera-20261003-103729"


async def test_list_and_detail_carry_the_slug_and_both_addresses_work():
    c, store = setup()
    await put(store, story(), "published")
    listed = c.get("/public/news").json()
    assert [r["id"] for r in listed] == ["lohegaon-hospital-opd-awaiting-approval-f5ddee"]
    by_slug = c.get("/public/news/lohegaon-hospital-opd-awaiting-approval-f5ddee")
    by_old = c.get(f"/public/news/{HASH}")  # what captions already posted on Facebook and Instagram link to
    assert by_slug.status_code == by_old.status_code == 200
    assert by_slug.json() == by_old.json() and by_old.json()["id"] == listed[0]["id"]
    assert by_old.json()["areas"] == [{"key": "lohegaon", "slug": "lohegaon", "name": "Lohegaon"}]  # every area, not only the first three


async def test_an_older_slug_still_finds_the_story_after_a_headline_edit():
    c, store = setup()
    await put(store, story(), "published")
    old = pub.slug(story())
    store.items.docs[0]["draft"]["title"] = "Lohegaon hospital OPD gets state approval"
    r = c.get(f"/public/news/{old}")
    assert r.status_code == 200 and r.json()["id"] == "lohegaon-hospital-opd-gets-state-approval-f5ddee"


async def test_two_stories_sharing_six_id_chars_each_keep_their_own_address():
    c, store = setup()
    await put(store, story(HASH, "Lohegaon hospital OPD awaiting approval"), "published")
    await put(store, story(HASH[:6] + "00" * 17, "Wagholi water line tender opens", ("wagholi",)), "published")
    assert c.get("/public/news/lohegaon-hospital-opd-awaiting-approval-f5ddee").json()["headline"].startswith("Lohegaon")
    assert c.get("/public/news/wagholi-water-line-tender-opens-f5ddee").json()["headline"].startswith("Wagholi")


async def test_unknown_or_hidden_addresses_are_404():
    c, store = setup()
    await put(store, story(), "pending_review")
    await put(store, {**SAMPLES[0], "_id": "abcdef0000"}, "published")
    for bad in ("missing", "lohegaon-hospital-opd-awaiting-approval-f5ddee", HASH, "no-such-story-000000", "pune-ring-road-abcdeg",
                "pune-ring-road-abcdef0", "-", "x-"):
        assert c.get(f"/public/news/{bad}").status_code == 404, bad
    assert c.get("/public/news/any-words-abcdef").json()["id"] == "pune-ring-road-10502-crore-approved-abcdef"


async def test_digest_is_found_by_its_id_and_lists_its_stories_by_slug():
    c, store = setup()
    for d in SAMPLES:
        await put(store, d, "published")
    dg = digest.sample_digest(SAMPLES)
    await put(store, dg, "approved")
    r = c.get(f"/public/news/{dg['_id']}").json()
    assert r["id"] == dg["_id"] and r["kind"] == "digest"
    by_id = {d["_id"]: pub.slug(d) for d in SAMPLES}
    assert r["items"] and all(i["linked"] and i["id"] in by_id.values() for i in r["items"])
    for i in r["items"]:  # each link opens its story
        assert c.get(f"/public/news/{i['id']}").json()["id"] == i["id"]


async def test_roundup_projects_are_not_linked_as_stories():
    c, store = setup()
    rp = roundup.compose(ROUNDUP_PROJECTS, NOW, "maharera-20261003-103729")
    await put(store, rp, "published")
    r = c.get("/public/news/maharera-20261003-103729").json()
    assert r["id"] == "maharera-20261003-103729" and [i["linked"] for i in r["items"]] == [False]


async def test_area_filter_keeps_that_areas_stories():
    c, store = setup()
    await put(store, story(), "published")
    for d in SAMPLES:
        await put(store, d, "published")
    await put(store, digest.sample_digest(SAMPLES), "approved")
    await put(store, roundup.compose(ROUNDUP_PROJECTS, NOW, "maharera-20261003-103729"), "published")
    lohegaon = c.get("/public/news?area=lohegaon").json()
    assert [r["id"] for r in lohegaon] == ["maharera-20261003-103729", "lohegaon-hospital-opd-awaiting-approval-f5ddee"]
    wagholi = c.get("/public/news?area=wagholi&limit=50").json()
    expected = [pub.slug(d) for d in reversed(SAMPLES) if "wagholi" in d["relevance"]["areas"]]
    assert [r["id"] for r in wagholi] == expected  # newest first, the weekly digest (all areas) left out
    assert all("wagholi" in [a["key"] for a in r["areas"]] for r in wagholi)
    assert [r["id"] for r in c.get("/public/news?area=wagholi&limit=2").json()] == expected[:2]
    upper = [r["id"] for r in c.get("/public/news?area=upper_kharadi").json()]
    assert upper == [pub.slug(SAMPLES[-1])] and [r["id"] for r in c.get("/public/news?area=upper-kharadi").json()] == upper  # or its slug
    assert c.get("/public/news?area=hinjawadi").json() == [] and c.get("/public/news?area=nowhere").json() == []
    assert len(c.get("/public/news").json()) == len(SAMPLES) + 3  # no area: everything, as before
