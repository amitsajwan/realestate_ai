"""The daily page check: a finished page against its record and sources (app/modules/seo/review.py)."""
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.modules.newsroom.store import Store
from app.modules.seo import report, review

from ..fakes import FakeDb

NOW = datetime(2026, 11, 3, 9, 0, tzinfo=timezone.utc)
WRITTEN = "Godrej Ivara has eleven buildings. " + "It sits close to the IT parks of Kharadi and the schools nearby. " * 6


def project(slug="godrej-ivara", **kw):
    return {"_id": "PR1260002502426", "regno": "PR1260002502426", "page_slug": slug, "name": "GODREJ IVARA", "locality": "kharadi",
            "promoter": "Manjari Housing", "pincode": "411014", "completion_now": "2032-12-16", "units_total": 2792, "units_booked": 489,
            "page_text": WRITTEN, "page_text_version": 4, "page_sections": [{"heading": "The project", "text": WRITTEN}],
            "prices": {"rows": [{"bhk": "2 BHK", "from_inr": 12000000}]}, "web_facts": {"facts": [{"key": "towers", "label": "Towers", "value": 11, "text": "11", "official": True, "sources": [{"site": "godrej.com", "url": "u", "quote": "11 towers"}]}]},
            "enriched_at": NOW - timedelta(days=3), **kw}


def page(doc=None, extra="", robots=""):
    doc = doc or project()
    return (f"<html><head><title>Godrej Ivara</title>{robots}<style>.a{{}}</style></head><body><h1>Godrej Ivara</h1><script>x=1</script>"
            f"<p>Kharadi, Pune PR1260002502426</p><p>16 Dec 2032</p><p>489 of 2,792 booked</p><p>{WRITTEN}</p>{extra}</body></html>")


class Asked:
    def __init__(self, answer):
        self.answer, self.calls = answer, 0

    async def json(self, system, user):
        self.calls += 1
        return self.answer


def http_with(*bodies, status=200):
    seen = []

    def handler(req):
        seen.append(req)
        return httpx.Response(status, text=bodies[min(len(seen) - 1, len(bodies) - 1)])
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client.seen = seen
    return client


async def check(body, doc=None, ask=None, others=()):
    return await review.check(FakeDb(), doc or project(), "https://avasetu.in/projects/godrej-ivara", list(others), http_with(body), ask or Asked({"problems": []}), 0)


async def test_a_page_that_matches_its_record_and_sources_is_clean_and_read_as_google():
    client = http_with(page())
    out = await review.check(FakeDb(), project(), "https://avasetu.in/projects/godrej-ivara", [], client, Asked({"problems": []}), 0)
    assert out == {"problems": [], "model": True}
    assert "-Google" in client.seen[0].headers["user-agent"]


@pytest.mark.parametrize("change, expected", [
    ({"units_booked": 500}, "500 of 2792"),
    ({"completion_now": "2031-01-31"}, "31 Jan 2031"),
    ({"regno": "PR9999"}, "PR9999"),
])
async def test_a_page_that_differs_from_its_record_is_reported(change, expected):
    out = await check(page(), project(**change))
    assert any(p["kind"] == "record" and expected in p["detail"] for p in out["problems"])


async def test_a_stale_copy_is_read_again_before_anything_is_reported():
    client = http_with(page().replace("489 of 2,792", "480 of 2,792"), page())
    out = await review.check(FakeDb(), project(), "https://avasetu.in/projects/godrej-ivara", [], client, Asked({"problems": []}), 0)
    assert len(client.seen) == 2 and out["problems"] == []


async def test_a_page_that_does_not_answer_or_says_noindex_is_reported():
    client = http_with("", status=500)
    out = await review.check(FakeDb(), project(), "https://avasetu.in/projects/godrej-ivara", [], client, Asked({"problems": []}), 0)
    assert out["problems"][0]["detail"] == "The page answered 500" and out["model"] is False
    out = await check(page(robots='<meta name="robots" content="noindex"/>'))
    assert [p["kind"] for p in out["problems"]] == ["not_in_search"]


async def test_text_naming_another_project_a_far_place_or_a_wild_rate_is_reported():
    text = WRITTEN + " Next to Kolte Patil Life Republic, 40 km away."
    doc = project(page_text=text, page_sections=[{"text": text}])
    body = page().replace(WRITTEN, text) .replace("</body>", "<p>₹500/sq ft</p></body>")
    kinds = {p["kind"] for p in (await check(body, doc, others=["Kolte Patil Life Republic"]))["problems"]}
    assert kinds == {"wrong_project", "location", "number"}


async def test_the_projects_own_longer_name_is_not_another_project():
    text = WRITTEN + " Godrej Ivara Phase 2 is planned."
    doc = project(page_text=text, page_sections=[{"text": text}])
    body = page().replace(WRITTEN, text)
    assert (await check(body, doc, others=["Godrej Ivara Phase 2"]))["problems"] == []


async def test_a_thin_page_is_reported():
    doc = project(web_facts={}, page_text="Short.", page_sections=[{"text": "Short."}])
    out = await check(page().replace(WRITTEN, "Short."), doc)
    assert [p["kind"] for p in out["problems"]] == ["thin"]


async def test_short_text_beside_two_kinds_of_facts_is_not_thin():
    doc = project(page_text="Short.", page_sections=[{"text": "Short."}])
    assert (await check(page().replace(WRITTEN, "Short."), doc))["problems"] == []


async def test_old_text_no_page_shows_is_not_looked_for_or_given_to_the_model():
    doc = project(page_text="Old words from before sections.", page_sections=[], web_facts={})
    asked = Asked({"problems": []})
    out = await check(page().replace(WRITTEN, ""), doc, asked)
    assert [p["kind"] for p in out["problems"]] == ["thin"] and asked.calls == 0


async def test_the_model_counts_only_with_a_quote_really_on_the_page():
    answer = {"problems": [
        {"kind": "wrong_project", "quote": "eleven buildings", "why": "Another project has eleven.", "source": "none"},
        {"kind": "wrong_project", "quote": "twelve lakes nearby", "why": "Invented quote."},
        {"kind": "style", "quote": "eleven buildings", "why": "Not a kind we ask for."},
    ]}
    out = await check(page(), ask=Asked(answer))
    assert [(p["kind"], p["quote"], p["by"]) for p in out["problems"]] == [("wrong_project", "eleven buildings", "model")]


def test_a_number_the_sources_hold_is_not_called_wrong():
    answer = {"problems": [{"kind": "number", "quote": "2,792 booked", "why": "Wrong."}, {"kind": "number", "quote": "489 of", "why": "Wrong."}]}
    got = review.checked_answer(answer, "489 of 2,792 booked", "MahaRERA shows 2,792 homes")
    assert [p["quote"] for p in got] == ["489 of"]


async def test_with_no_model_the_rules_stand_and_the_page_stays_due():
    out = await review.check(FakeDb(), project(), "https://avasetu.in/x", [], http_with(page()), None, 0)
    assert out == {"problems": [], "model": False}
    assert await review.check(FakeDb(), project(), "https://avasetu.in/x", [], http_with(page()), Asked(None), 0) == out


def test_pick_takes_new_pages_first_then_unread_by_the_model_then_rewritten_then_old():
    new, unread, rewritten, old, done = (project(s, _id=s, enriched_at=NOW - timedelta(days=90)) for s in ("new", "unread", "rewritten", "old", "done"))
    rewritten["page_text_at"] = NOW - timedelta(days=1)
    latest = {"unread": {"at": NOW - timedelta(days=1), "model": False}, "rewritten": {"at": NOW - timedelta(days=2), "model": True},
              "old": {"at": NOW - review.AGAIN, "model": True}, "done": {"at": NOW - timedelta(days=2), "model": True}}
    got = review.pick([done, old, rewritten, unread, new], latest, NOW)
    assert [d["page_slug"] for d in got] == ["new", "unread", "rewritten", "old"]


def test_pick_leaves_out_towers_pages_not_in_search_and_pages_just_changed():
    docs = [project("tower", cluster_primary="X"), project("noslug", page_slug=None), project("empty", page_text=None),
            project("just", details_checked_at=NOW - timedelta(minutes=30)), project("ok", _id="OK")]
    assert [d["page_slug"] for d in review.pick(docs, {}, NOW)] == ["ok"]


def test_pick_prefers_our_areas_and_hot_pages_and_stops_at_the_days_number():
    docs = [project(f"p{i}", _id=f"P{i}") for i in range(30)] + [project("hot", _id="H", hot_score=9), project("far", _id="F", locality="talegaon")]
    got = review.pick(docs, {}, NOW)
    assert len(got) == review.PER_DAY and got[0]["page_slug"] == "hot" and "far" not in [d["page_slug"] for d in got]


async def store_with(*docs):
    store = Store(FakeDb())
    for d in docs:
        await store.projects.insert_one(d)
    return store


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://avasetu.in")
    monkeypatch.delenv("SEO_PAGE_REVIEW", raising=False)

    async def no_reader(db, now):
        return None
    monkeypatch.setattr(review.budget, "reader", no_reader)


async def test_a_round_reports_once_a_day_and_changes_no_project_record(live):
    doc = project()
    store = await store_with(doc)
    before = dict(await store.projects.find_one({"_id": doc["_id"]}))
    got = await review.run_once(store, NOW, http=http_with(page()), wait_s=0)
    assert got == {"read": 1, "flagged": 0, "model": 0, "unread": 0}
    assert await review.run_once(store, NOW + timedelta(hours=3), http=http_with(page()), wait_s=0) is None
    assert await store.projects.find_one({"_id": doc["_id"]}) == before
    assert (await store.get_mark(review.MARK))["read"] == 1


async def test_one_page_that_cannot_be_read_does_not_stop_the_others(live):
    store = await store_with(project("bad", _id="B"), project("good", _id="G"))

    def handler(req):
        if req.url.path.endswith("bad"):
            raise httpx.ConnectError("down")
        return httpx.Response(200, text=page())
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    got = await review.run_once(store, NOW, http=client, wait_s=0)
    assert (got["read"], got["unread"]) == (1, 1)
    rows = await store.db.get_collection(review.COLLECTION).find({}).to_list(None)
    assert [r["page_slug"] for r in rows] == ["good"]


async def test_it_is_off_by_its_setting_and_where_there_is_no_live_site(monkeypatch):
    store = await store_with(project())
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://avasetu.in")
    monkeypatch.setenv("SEO_PAGE_REVIEW", "off")
    assert await review.run_once(store, NOW) is None
    monkeypatch.delenv("SEO_PAGE_REVIEW")
    monkeypatch.setenv("PUBLIC_SITE_URL", "http://localhost:3000")
    assert await review.run_once(store, NOW) is None


async def test_rankings_show_a_pages_latest_read_only_while_it_has_problems():
    store = Store(FakeDb())
    rows = store.db.get_collection(review.COLLECTION)
    bad = [{"kind": "thin", "detail": "Thin"}]
    await rows.insert_one({"_id": "a:1", "page_slug": "a", "name": "A", "url": "u", "at": NOW - timedelta(days=2), "problems": bad, "model": True})
    await rows.insert_one({"_id": "a:2", "page_slug": "a", "name": "A", "url": "u", "at": NOW - timedelta(days=1), "problems": [], "model": True})
    await rows.insert_one({"_id": "b:1", "page_slug": "b", "name": "B", "url": "u", "at": NOW - timedelta(days=1), "problems": bad, "model": True})
    await rows.insert_one({"_id": "c:1", "page_slug": "c", "name": "C", "url": "u", "at": NOW - timedelta(days=20), "problems": bad, "model": True})
    got = await review.summary(store, NOW)
    assert [i["slug"] for i in got["items"]] == ["b"]
    assert (got["week"], got["week_flagged"]) == (3, 2)
    assert "3 pages" in review.week_line(got)
    assert review.week_line({"week": 0}) == ""
    assert report.review is review


def test_health_warns_when_the_check_stops_or_the_model_read_nothing():
    from app.modules.admin import health
    assert health.page_check_row(None, NOW)["status"] == health.OK
    assert health.page_check_row({"at": NOW - timedelta(days=1), "read": 20, "model": 20}, NOW)["status"] == health.OK
    assert health.page_check_row({"at": NOW - timedelta(days=1), "read": 20, "model": 0}, NOW)["status"] == health.WARN
    assert health.page_check_row({"at": NOW - timedelta(days=4), "read": 20, "model": 20}, NOW)["status"] == health.WARN


# a page that stands for several registrations (pages.project_scope): Venkatesh Vanaya's main registration holds 168 of 745 homes
VANAYA = {"_id": "PR1261012601206", "regno": "PR1261012601206", "units_total": 168, "units_booked": 7}
SCOPE = {"registrations": 7, "regnos": ["PR1261012601206"], "units_total": 745, "units_counted": 6, "units_booked": 40,
         "booked_of": 745, "booked_counted": 6, "completion_first": "2030-08-31", "completion_last": "2033-01-31", "completion_passed": False}


def test_a_page_saying_one_registration_s_count_as_the_project_s_is_reported():
    wrong = "<html><body><h1>Venkatesh Vanaya</h1><p>How many flats are there? MahaRERA lists 168 units.</p></body></html>"
    found = review.scope_problems(VANAYA, review.plain(wrong), SCOPE)
    assert [p["kind"] for p in found] == ["scope"] and "168" in found[0]["detail"]
    right = ("<html><body><p>MahaRERA lists 745 units across 6 of its 7 MahaRERA registrations; PR1261012601206 has 168.</p>"
             "<table><tr><td>PR1261012601206</td><td>30 Apr 2031</td><td>7 of 168</td></tr></table></body></html>")
    assert review.scope_problems(VANAYA, review.plain(right), SCOPE) == []
    assert review.scope_problems(VANAYA, review.plain(wrong), None) == []   # a page of one registration: its count is the project's


def test_the_head_search_quotes_is_read_too_but_not_the_page_s_data_payload():
    head = ('<html><head><title>Venkatesh Vanaya</title><meta name="description" content="Possession Apr 2031, 7 of 168 homes booked.">'
            '</head><body><p>40 of 745 homes booked across 6 of its 7 MahaRERA registrations.</p>'
            '<script>self.__next_f.push([1,"{\\"units_total\\":168}"])</script></body></html>')
    assert [p["kind"] for p in review.rule_problems(VANAYA, head, [], SCOPE) if p["kind"] == "scope"] == ["scope"]
    payload_only = head.replace("7 of 168 homes booked", "40 of 745 homes booked")
    assert [p for p in review.rule_problems(VANAYA, payload_only, [], SCOPE) if p["kind"] == "scope"] == []


def test_a_page_of_several_registrations_must_show_the_whole_project_s_bookings():
    text = "PR1261012601206 40 of 745 homes booked across 6 of its 7 MahaRERA registrations"
    assert [p for p in review.against_record(VANAYA, text, SCOPE) if "booked" in p["detail"]] == []
    assert [p["detail"] for p in review.against_record(VANAYA, "PR1261012601206 7 of 168 booked", SCOPE)
            if "booked" in p["detail"]] == ["40 of 745 homes booked is not on the page"]
