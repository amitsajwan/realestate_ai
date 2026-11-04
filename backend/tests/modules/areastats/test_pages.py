"""Our own page for every register project: stable slugs, facts-only paragraph, noindex until the details are in, the lookup."""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.areastats import pages
from app.modules.areastats.cautions import cautions
from app.modules.areastats import router as ar
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

READ = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)
FULL = {"promoter": "Rohan Builders", "completion_now": "2029-10-30", "completion_at_registration": "2028-12-31", "units_total": 416,
        "units_booked": 244, "details_checked_at": READ, "details_ok": True, "last_modified": "2026-09-28",
        "source_url": "https://maharerait.maharashtra.gov.in/public/project/view/80076"}


async def seeded(*docs):
    db = FakeDb()
    store = Store(db)
    for regno, name, locality, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": name, "locality": locality, "pincode": "412207", "news": [], **extra})
    return db, store


async def test_slugs_are_readable_given_once_and_unique():
    db, store = await seeded(("P1", "Rohan Abhilasha 4", "wagholi", {}), ("P2", "Rohan Abhilasha 4", "wagholi", {}),
                             ("P3", "Wagholi Heights", "wagholi", {}), ("P4", "Far Away", None, {}))
    assert await pages.assign_all(store) == 3   # P4 is not ours and not watched: no page
    assert (await store.project("P1"))["page_slug"] == "rohan-abhilasha-4-wagholi"
    assert (await store.project("P2"))["page_slug"] == "rohan-abhilasha-4-wagholi-p2"   # clash: registration number's tail
    assert (await store.project("P3"))["page_slug"] == "wagholi-heights"               # the area word is not repeated
    await store.set_project("P1", name="Renamed Later")
    assert await pages.assign_all(store) == 0 and (await store.project("P1"))["page_slug"] == "rohan-abhilasha-4-wagholi"


async def test_the_paragraph_says_only_what_the_record_says():
    db, store = await seeded(("P52100080076", "Rohan Abhilasha 4", "wagholi", FULL))
    text = pages.paragraph(await store.project("P52100080076"))
    assert text.startswith("Rohan Abhilasha 4 is a project by Rohan Builders in Wagholi, Pune, registered with MahaRERA as P52100080076.")
    assert "filed completion date is 30 Oct 2029; at registration it was 31 Dec 2028" in text
    assert "244 of 416 homes were booked when we read the record on 3 Oct 2026" in text
    assert "₹" not in text and "lakh" not in text and "best" not in text.lower()
    thin = pages.paragraph({"_id": "P9", "name": "New One", "locality": "baner"})
    assert thin.startswith("New One is a project in Baner, Pune") and "booked" not in thin and "completion" not in thin


async def test_indexable_needs_a_date_and_a_promoter_or_pincode():
    assert pages.indexable(FULL)
    assert pages.indexable({**FULL, "units_total": None, "units_booked": None})   # bookings optional
    assert pages.indexable({**FULL, "completion_now": "2015-01-01"})               # finished projects stay in
    assert pages.indexable({**FULL, "promoter": None, "pincode": "412207"})
    assert not pages.indexable({**FULL, "completion_now": None})
    assert not pages.indexable({**FULL, "promoter": None, "pincode": None})


async def test_search_sees_only_pages_with_content_beyond_the_register():
    assert not pages.searchable(FULL)                                    # register facts alone: listed, kept out of search
    written = {**FULL, "page_text": "About the project."}
    assert not pages.searchable(written)                                 # a paragraph alone is thin (owner 2026-10-31)
    assert not pages.searchable({**FULL, "prices": {"rows": [{"bhk": 2}]}})   # a fact without written text is thin too
    assert pages.searchable({**written, "prices": {"rows": [{"bhk": 2}]}})
    assert pages.searchable({**written, "web_facts": {"facts": [{"key": "towers"}]}})
    assert pages.searchable({**written, "profile": {"highlights": ["Clubhouse"]}})
    assert pages.searchable({**written, "profile": {"highlights": [], "photos": [{"url": "x"}]}})
    assert not pages.searchable({**written, "profile": {"highlights": [], "photos": [], "plans": []}, "web_facts": {"facts": []}})
    assert not pages.searchable({**written, "prices": {"rows": [{"bhk": 2}]}, "completion_now": None})   # still needs what a listable page needs
    done = {**written, "prices": {"rows": [{"bhk": 2}]}, "completion_now": "2015-01-01"}
    assert not pages.searchable(done)                                    # finished: out of search (owner 2026-11-01)
    assert not pages.searchable({**done, "gsc_impressions": 4})          # even one Google already shows


def test_a_finished_project_offers_the_projects_still_being_built_soonest_first():
    def doc(_id, done, **extra):
        return {"_id": _id, "name": _id, "locality": "wagholi", "page_slug": _id.lower(), "promoter": "R", "completion_now": done, **extra}
    old = doc("OLD", "2015-01-01")
    peers = [old, doc("LATE", "2031-06-30"), doc("SOON", "2027-03-31"), doc("ALSO_OLD", "2016-05-01")]
    assert [d["_id"] for d in pages._similar(old, peers)] == ["SOON", "LATE"]   # finished ones are never offered
    assert pages.view(old, [])["finished"] and not pages.view(old, [])["indexable"]
    assert not pages.view(peers[1], [])["finished"]


async def test_page_updated_is_our_own_change_never_maharera():
    # a full datetime, not a date: IndexNow must see the hour a page changed, or two edits the same day look identical
    assert pages.page_updated({"last_modified": "2026-09-28"}) is None
    assert pages.page_updated({**FULL, "page_text_at": datetime(2026, 10, 5, tzinfo=timezone.utc)}) == "2026-10-05T00:00:00+00:00"
    assert pages.page_updated(FULL) == "2026-10-03T09:00:00+00:00"
    # a round that found the same facts changed nothing a reader sees: the date stays
    assert pages.page_updated({**FULL, "enriched_at": datetime(2026, 10, 5, tzinfo=timezone.utc)}) == "2026-10-03T09:00:00+00:00"


async def test_an_ai_illustration_is_not_content_of_the_projects_own():
    drawn = {"photos": [{"path": "a.webp", "source": "ai"}]}
    written = {**FULL, "page_text": "About the project."}
    assert not pages.searchable({**written, "profile": drawn})
    assert pages.searchable({**written, "profile": {"photos": [{"path": "b.webp", "source": "builder"}]}})


async def test_a_page_in_search_shows_no_ai_illustrations():
    from app.modules.areastats import profile
    pics = {"photos": [{"path": "a.webp", "source": "ai"}, {"path": "b.webp", "source": "builder", "site": "x.com"}]}
    assert [p["source"] for p in profile.public(pics)["photos"]] == ["ai", "builder"]
    assert [p["source"] for p in profile.public(pics, drawn=False)["photos"]] == ["builder"]
    assert profile.public({"photos": [{"path": "a.webp", "source": "ai"}]}, drawn=False) is None


async def test_web_photos_do_not_make_a_page_searchable():
    copied = {"photos": [{"path": "a.webp", "source": "web", "site": "housiey.com"}],
              "plans": [{"path": "p.webp", "source": "web", "site": "magicbricks.com"}]}
    assert not pages.has_own_content({**FULL, "profile": copied})
    written = {**FULL, "page_text": "About the project."}
    assert not pages.searchable({**written, "profile": copied})
    # the builder's or the brochure's picture, or plan, still counts
    assert pages.searchable({**written, "profile": {"photos": [{"path": "b.webp", "source": "brochure"}]}})
    assert pages.searchable({**written, "profile": {"plans": [{"path": "p.webp", "source": "builder"}]}})
    assert pages.searchable({**written, "profile": {"photos": [{"path": "c.webp"}]}})   # saved before sources: the builder's


async def test_photos_copied_from_other_sites_are_never_shown_but_stay_on_the_record():
    from app.modules.areastats import profile
    stored = {"highlights": [], "photos": [{"path": "a.webp", "source": "web", "site": "housiey.com"},
                                           {"path": "b.webp", "source": "builder", "site": "lodhagroup.com"}],
              "plans": [{"path": "p.webp", "source": "web", "site": "magicbricks.com"}, {"path": "q.webp", "source": "brochure"}]}
    for drawn in (True, False):
        shown = profile.public(stored, drawn=drawn)
        assert [p["url"] for p in shown["photos"]] == ["/uploads/b.webp"]
        assert [p["url"] for p in shown["plans"]] == ["/uploads/q.webp"]
    assert len(stored["photos"]) == 2 and len(stored["plans"]) == 2   # the reading is kept, only not shown
    # nothing else to show: no profile at all, so the page shows its no-picture fallback
    assert profile.public({"highlights": [], "photos": [{"path": "a.webp", "source": "web"}], "plans": []}) is None


async def test_marketed_name_and_aliases():
    doc = {"name": "Geras World of Joy M", "promoter": "Gera Developments Pvt. Ltd."}
    marketed, aliases = pages.names(doc)
    assert marketed == "Gera World of Joy M"
    assert aliases == ["Gera World of Joy M", "Gera World of Joy", "Gera's World of Joy M", "Gera's World of Joy",
                       "Geras World of Joy M"]
    # conservative: no promoter match, no stripping
    assert pages.names({"name": "Kumars Park II", "promoter": "Rohan Builders"}) == ("Kumars Park II", ["Kumars Park II", "Kumars Park"])
    assert pages.names({"name": "Rohan Abhilasha 4", "promoter": "Rohan Builders"})[1] == ["Rohan Abhilasha 4"]
    assert pages.names({**doc, "marketed_name_override": "World of Joy"})[0] == "World of Joy"


async def test_search_ranking_and_same_promoter():
    pages.clear_search_cache()
    gera = {**FULL, "promoter": "Gera Developments"}
    db, store = await seeded(("P52100012345", "Geras World of Joy M", "wagholi", gera),
                             ("P52100099999", "Joy Homes", "wagholi", FULL),
                             ("P52100055555", "Geras Island of Joy", "wagholi", gera))
    await pages.assign_all(store)
    app = FastAPI()
    app.include_router(ar.public_router, prefix="/public")
    app.dependency_overrides[ar.get_db] = lambda: db
    c = TestClient(app)
    get = lambda q: [r["regno"] for r in c.get("/public/register/search", params={"q": q}).json()]
    assert get("P52100012345") == ["P52100012345"]
    assert get("12345")[0] == "P52100012345"
    assert get("gera world")[0] == "P52100012345"                    # alias startswith
    assert get("joy") == ["P52100099999", "P52100055555", "P52100012345"]   # startswith 60 beats contains 50
    assert get("joy gera")[:2] and set(get("joy gera")) == {"P52100012345", "P52100055555"}   # all words
    assert get("j") == [] and get("  ") == []
    row = c.get("/public/register/search", params={"q": "World of Joy"}).json()[0]
    assert set(row) == {"slug", "name", "marketed_name", "regno", "promoter", "area", "place_name", "completion_now",
                        "units_total", "units_booked", "checked", "checks_total", "active", "months_later"}
    assert row["marketed_name"] == "Gera World of Joy M" and row["area"] == "wagholi"
    page = c.get(f"/public/register/projects/{row['slug']}").json()
    assert [s["name"] for s in page["same_promoter"]] == ["Geras Island of Joy"] and "Gera's World of Joy" in page["aliases"]
    item = c.get("/public/register/projects").json()[0]
    assert {"marketed_name", "units_total", "units_booked", "page_updated"} <= set(item)
    pages.clear_search_cache()


async def test_page_for_and_the_public_api():
    written = {**FULL, "page_text": "About the project.", "page_text_version": 4,   # text and a fact of its own: search sees it
               "prices": {"rows": [{"bhk": 2}]}}
    db, store = await seeded(("P52100080076", "Rohan Abhilasha 4", "wagholi", written), ("P2", "Kesnand Greens", "wagholi", {**FULL, "completion_now": "2029-03-31"}),
                             ("P3", "Thin One", "wagholi", {}), ("GULM", "Gulmohar City", None, {"watched_by": ["agent_projects"]}),
                             ("NOTOURS", "Somewhere", None, {}))
    hit = await pages.page_for(db, "p52100080076")
    assert hit == {"slug": "rohan-abhilasha-4-wagholi", "path": "/projects/rohan-abhilasha-4-wagholi",
                   "url": hit["url"], "indexable": True} and hit["url"].endswith("/projects/rohan-abhilasha-4-wagholi")
    assert (await pages.page_for(db, "GULM"))["slug"] == "gulmohar-city-pune" and await pages.page_for(db, "NOTOURS") is None
    await pages.assign_all(store)

    app = FastAPI()
    app.include_router(ar.public_router, prefix="/public")
    app.dependency_overrides[ar.get_db] = lambda: db
    c = TestClient(app)
    page = c.get("/public/register/projects/rohan-abhilasha-4-wagholi").json()
    assert page["area"] == {"key": "wagholi", "slug": "wagholi", "name": "Wagholi"} and page["units_booked"] == 244
    assert page["details_read_at"] == "2026-10-03" and page["indexable"] and page["maharera_url"].endswith("/80076")
    assert [s["slug"] for s in page["same_area"]] == ["kesnand-greens-wagholi"]   # thin pages are not suggested
    assert c.get("/public/register/projects/thin-one-wagholi").json()["indexable"] is False
    assert c.get("/public/register/projects/nope").status_code == 404
    assert c.get("/public/register/by-regno/GULM").json() == {"slug": "gulmohar-city-pune", "path": "/projects/gulmohar-city-pune", "indexable": False}
    assert c.get("/public/register/by-regno/NOTOURS").status_code == 404
    assert [p["slug"] for p in c.get("/public/register/projects?area=wagholi").json()] == ["kesnand-greens-wagholi", "rohan-abhilasha-4-wagholi"] or \
        sorted(p["slug"] for p in c.get("/public/register/projects?area=wagholi").json()) == ["kesnand-greens-wagholi", "rohan-abhilasha-4-wagholi"]
    assert len(c.get("/public/register/projects?all=true").json()) == 4


async def test_zero_booked_after_completion_means_not_reported_and_the_page_says_the_date_passed():
    past = {**FULL, "completion_now": "2023-12-29", "completion_at_registration": "2022-12-30", "units_total": 1185, "units_booked": 0}
    assert pages.booked(past) is None and pages.indexable(past)
    text = pages.paragraph({**past, "_id": "P1", "name": "Ivy Estate-Nia", "locality": "wagholi", "regno": "P1"})
    assert "0 of 1185" not in text and "bookings were not reported" in text and "occupancy certificate (OC)" in text
    future_new = {**FULL, "units_booked": 0}   # a new project with nothing sold yet: 0 is a real number
    assert pages.booked(future_new) == 0 and pages.indexable(future_new)


def test_a_page_is_dated_by_its_last_change():
    from datetime import datetime, timezone
    doc = {"last_modified": "2026-09-01", "details_checked_at": datetime(2026, 10, 3, tzinfo=timezone.utc), "details_ok": True}
    assert pages.page_updated(doc) == "2026-10-03T00:00:00+00:00"
    assert pages.page_updated({**doc, "page_text_at": datetime(2026, 10, 12, tzinfo=timezone.utc)}) == "2026-10-12T00:00:00+00:00"
    assert pages.page_updated({**doc, "details_ok": False}) is None          # a failed read changed nothing; MahaRERA's own date never counts
    assert pages.page_updated({}) is None


async def test_a_place_counts_its_current_projects_apart_from_every_registration():
    db, store = await seeded(("P1", "New One", "wagholi", {**FULL, "pune_place": "wagholi"}),
                             ("P2", "Old One", "wagholi", {**FULL, "pune_place": "wagholi", "completion_now": "2019-03-31"}))
    await pages.assign_all(store)
    got = {p["key"]: p for p in await pages.places(db)}["wagholi"]
    assert (got["projects"], got["current"]) == (2, 1)   # the old one stays on the page, not in "being built or just finished"


async def test_a_place_is_in_search_only_with_a_project_page_in_search():
    async def wagholi(first: dict) -> dict:
        db, store = await seeded(("P1", "New One", "wagholi", {**FULL, "pune_place": "wagholi", **first}),
                                 ("P2", "Other One", "wagholi", {**FULL, "pune_place": "wagholi"}))
        await pages.assign_all(store)
        return {p["key"]: p for p in await pages.places(db)}["wagholi"]
    got = await wagholi({})
    assert (got["projects"], got["indexable"]) == (2, 0)    # register-only pages: the place page stays out of search
    assert (await wagholi({"page_text": "Written from the record."}))["indexable"] == 0   # a paragraph alone is thin
    assert (await wagholi({"page_text": "Written from the record.", "prices": {"rows": [{"bhk": 2}]}}))["indexable"] == 1


async def test_a_word_of_the_name_ranks_before_letters_inside_another_word():
    pages.clear_search_cache()
    db, store = await seeded(("P52100011111", "Bhide Nivara", "wagholi", FULL), ("P52100022222", "Godrej Ivara", "kharadi", FULL))
    await pages.assign_all(store)
    assert [r["regno"] for r in await pages.search(db, "ivara")] == ["P52100022222", "P52100011111"]


# ---- offices and shops (2026-11-03: 24 of 174 project pages in search in Kharadi, Upper Kharadi and Wagholi) ----------------

OFFICES = {"building_totals": {"units_residential": 0, "units_other": 104}}


def test_a_project_with_no_homes_is_offices_whatever_its_type_says():
    assert not pages.homes({**FULL, "project_type": "Commercial"})
    assert not pages.homes({**FULL, "project_type": "Others", **OFFICES})                     # AP4 Tech Park
    assert not pages.homes({**FULL, "regno": "PC1260002602605"})                              # Ganga Altus Building G
    assert pages.homes({**FULL, "project_type": "Mixed", "building_totals": {"units_residential": 60, "units_other": 16}})
    assert pages.homes({**FULL, "project_type": "Residential / Group Housing"})


def test_offices_and_shops_are_never_in_search_however_full_the_page():
    full = {**FULL, "page_text": "About the project.", "profile": {"photos": [{"path": "b.webp", "source": "builder"}]}}
    assert pages.searchable(full)
    assert not pages.searchable({**full, "project_type": "Commercial"})
    assert not pages.searchable({**full, "project_type": "Others", **OFFICES})


async def test_an_offices_page_shows_no_flat_prices_and_says_it_has_no_homes():
    read = datetime(2026, 11, 1, tzinfo=timezone.utc)
    flats = {"at": read, "rows": [{"bhk": "2 BHK", "from_inr": 8_500_000, "official": True, "sources": []}]}
    db, _ = await seeded(("P1", "Aastha Business Bay", "kharadi", {**FULL, "project_type": "Commercial", "page_slug": "aastha-business-bay-kharadi",
                                                                  "prices": flats, **OFFICES}))
    page = await pages.project_page(db, "aastha-business-bay-kharadi", now=read)
    assert page["homes"] is False and page["indexable"] is False
    assert page["prices"] is None and page["price_idea"] is None and page["area_rate"] is None and page["area_compare"] is None


def test_the_shops_caution_is_for_homes_beside_shops_not_for_an_office_building():
    mixed = {**FULL, "building_totals": {"units_residential": 108, "units_other": 34}}
    assert "shops" in [c["key"] for c in cautions(mixed)]
    assert "shops" not in [c["key"] for c in cautions({**FULL, **OFFICES})]


def test_content_counts_say_what_the_pages_in_search_hold():
    base = {"completion_now": "2031-01-01", "promoter": "Rose LLP", "project_type": "Residential", "page_text": "x" * 300}
    full = {**base, "prices": {"rows": [{}]}, "web_facts": {"facts": [{}]},
            "profile": {"highlights": ["Clubhouse"], "photos": [{"source": "builder"}], "plans": [{"source": "brochure"}]}}
    thin = {**base, "prices": {"rows": [{}]}, "profile": {"photos": [{"source": "ai"}, {"source": "web"}]}}
    out = pages.content_counts([full, thin, {**base}, {**full, "cluster_primary": "P9"}])
    assert (out["pages"], out["prices"], out["photos"], out["plans"], out["full"], out["median_text"]) == (2, 2, 1, 1, 1, 300)


def test_content_counts_with_no_pages():
    assert pages.content_counts([])["median_text"] == 0
