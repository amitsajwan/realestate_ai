"""One project under several MahaRERA registrations, proved from the pages Google returns for their numbers, and named the way
two sites name it (areastats.samegroup; docs/plan/rival-housiey-ravet.md). Sonigara The Unicorn, Ravet: three registrations,
no promoter, three pages."""
from app.modules.areastats import samegroup
from app.modules.areastats.clusters import assign_clusters
from app.modules.areastats.websearch import RESULTS
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

C, A, D = "P52100052724", "PR1262022600338", "PM1260002601012"


def reg(regno, name, **kw):
    return {"_id": regno, "regno": regno, "name": name, "promoter": "", "pincode": "412101", "locality": None,
            "pune_place_name": "Ravet", **kw}


UNICORN = [reg(C, "The Unicorn Building C Wing C1 & C2"), reg(A, "The Unicorn Building A Wing A1 & A2"), reg(D, "The Unicorn Building D")]


def page(link, title, snippet=""):
    return {"type": "organic", "link": link, "title": title, "snippet": snippet}


RESULTS_SEEN = {
    C: [page("https://housiey.com/projects/sonigara-the-unicorn", "Sonigara The Unicorn Ravet - Brochure, Pros&Cons, PriceSheet",
             f"MahaRERA {C}, {A} ... 3 towers"),
        page("https://www.sonigara.com/the-unicorn", "Sonigara The Unicorn | Ravet, Pune", f"RERA No. {C} | {D}"),
        page("https://maharera.maharashtra.gov.in/x", f"Sonigara The Unicorn {C} {A} {D}")],
    A: [page("https://www.squareyards.com/pune/sonigara-the-unicorn", "Sonigara The Unicorn in Ravet, Pune: Price", f"RERA {A}")],
}


def test_a_page_printing_two_numbers_links_them_and_links_join_into_one_group():
    assert set(samegroup.linked([C, A, D], RESULTS_SEEN)) == {(C, A), (C, D)}
    assert samegroup.groups(UNICORN, RESULTS_SEEN) == [sorted([A, C, D])]


def test_a_list_of_projects_maharera_itself_or_far_apart_pins_prove_nothing():
    many = " ".join(f"P5210000{n:04d}" for n in range(9))
    lists = {C: [page("https://portal.example/ravet", "Projects in Ravet", f"{C} {A} {many}")]}
    assert samegroup.groups(UNICORN, lists) == []
    official = {C: [RESULTS_SEEN[C][2]]}
    assert samegroup.groups(UNICORN, official) == []
    pinned = {"enrichment": {"steps": {"places": {"ok": True}}}}
    far = [reg(C, "The Unicorn C", geo={"lat": 18.64, "lon": 73.74, "located_from": "google"}, **pinned),
           reg(A, "The Unicorn A", geo={"lat": 18.70, "lon": 73.80, "located_from": "google"}, **pinned)]
    assert samegroup.groups(far, {C: [RESULTS_SEEN[C][0]]}) == []


def test_the_name_two_sites_give_it_without_the_place_or_a_portals_tail():
    assert samegroup.web_name(UNICORN, RESULTS_SEEN, "The Unicorn", ["Ravet"]) == "Sonigara The Unicorn"
    one_site = {C: [RESULTS_SEEN[C][0]]}
    assert samegroup.web_name(UNICORN, one_site, "The Unicorn", ["Ravet"]) is None
    assert samegroup.web_name(UNICORN, RESULTS_SEEN, "Blue Ridge", ["Ravet"]) is None   # a title without the shared name


async def test_the_merge_step_puts_the_proved_towers_on_one_page_under_the_webs_name():
    store = Store(FakeDb())
    for d in UNICORN + [reg("P52100099999", "Unrelated Heights")]:
        await store.projects.insert_one(d)
    for regno, results in RESULTS_SEEN.items():
        await store.db.get_collection(RESULTS).insert_one({"_id": regno, "kind": "regno", "results": results})
    await assign_clusters(store, await store.all_projects())
    got = {r: await store.project(r) for r in (C, A, D)}
    assert len({g["cluster_id"] for g in got.values()}) == 1 and got[C]["cluster_id"].startswith("web:")
    primary = next(g for g in got.values() if not g.get("cluster_primary"))
    assert primary["group_name"] == "Sonigara The Unicorn"
    assert (await store.project("P52100099999")).get("cluster_id") is None


async def test_without_stored_pages_nothing_merges():
    store = Store(FakeDb())
    for d in UNICORN:
        await store.projects.insert_one(d)
    await assign_clusters(store, await store.all_projects())
    assert [(await store.project(r)).get("cluster_id") for r in (C, A, D)] == [None, None, None]
