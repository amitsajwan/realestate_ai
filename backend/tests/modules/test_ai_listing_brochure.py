"""AI draft from a builder's brochure: brochure facts, register match, sources, timeouts, and claims carried to marketing."""
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.ai_listing import brochure as bro
from app.modules.ai_listing import router as r
from app.modules.ai_listing.service import AIListingService
from app.modules.ai_listing.extractor import extract
from app.modules.listings.schemas import ListingCreate
from app.modules.propertyfacts import files

TEXT = "GULMOHAR CITY  N.A. Bungalow Plots  Gat No. 245, Malthan, Tal. Shirur, Dist. Pune  Plot sizes 1000 sq.ft to 2500 sq.ft"
CLAIMS = ["Gulmohar City is at Malthan, 10 minutes from Shikrapur.", "Plots from 1000 sq ft to 2500 sq ft.",
          "Internal roads of 30 ft.", "24x7 water supply."]


class FakeLLM:
    def __init__(self, out=None):
        self.out, self.texts = out, []

    async def extract(self, text, city_hint=None):
        self.texts.append(text)
        return self.out

    async def translate(self, facts, en):
        return None

    async def json(self, s, u):
        return None


class FakeRegister:
    def __init__(self, docs):
        self.docs = docs

    async def project(self, regno):
        return next((d for d in self.docs if d["_id"] == regno), None)

    async def all_projects(self, limit=20000):
        return list(self.docs)


REC = {"_id": "P52100012345", "regno": "P52100012345", "name": "Gulmohar City", "taluka": "Shirur", "pincode": "412208",
       "pune_place_name": "Malthan", "promoter": "Gulmohar Developers", "completion_now": "2027-12-31"}


@pytest.fixture
def uploads(tmp_path, monkeypatch):
    (tmp_path / "documents").mkdir()
    (tmp_path / "documents" / "abc.pdf").write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(files, "pdf_text", lambda pdf, max_pages=10: TEXT)

    async def read_brochure(pdf, out_dir):
        assert Path(out_dir).parent.name == "drafts"
        return {"pages": ["p0.jpg", "p1.jpg"], "claims": CLAIMS, "rera_no": None, "rera_missing": True}
    monkeypatch.setattr(files, "read_brochure", read_brochure)
    return tmp_path


URL = "/uploads/documents/abc.pdf"


def run(coro):
    return asyncio.run(coro)


def test_resolve_only_inside_documents(uploads):
    assert bro.resolve(URL, uploads) == (uploads / "documents" / "abc.pdf").resolve()
    assert bro.resolve("https://avasetu.in/uploads/documents/abc.pdf", uploads) is not None
    for bad in ("/uploads/documents/../x.pdf", "/uploads/images/abc.pdf", "/uploads/documents/none.pdf", "", None):
        assert bro.resolve(bad, uploads) is None


def test_brochure_fills_the_draft(uploads):
    llm = FakeLLM({"project_name": "Gulmohar City", "locality": "Gulmohar City", "property_type": "plot", "rera_no": "245"})
    d = run(AIListingService(llm=llm).create_draft(text="", brochure_url=URL, uploads_dir=uploads))
    f = d.draft
    assert f["project_name"] == "Gulmohar City"
    assert f.get("locality") != "Gulmohar City"           # the project's name is never its locality
    assert f["property_type"] == "plot" and f["transaction"] == "sale" and f["listing_scope"] == "layout"
    assert f["city"] == "Pune"
    assert (f["size_min_sqft"], f["size_max_sqft"]) == (1000, 2500)
    assert "rera_no" not in f                               # a gat number is not a registration
    assert "price_inr" not in f                             # none printed
    assert "builder's brochure mentions" in f["description"]["en"]
    assert f["about"]["highlights"][0] == CLAIMS[0]
    assert d.sources["property_type"] == "brochure" and d.sources["transaction"] == "brochure"
    assert d.brochure == {"claims": CLAIMS, "rera_no": None, "pages": 2}
    assert "brochure" in llm.texts[0] and CLAIMS[0] in llm.texts[0]


def test_agent_words_are_sourced_agent(uploads):
    d = run(AIListingService().create_draft(text="Plots in Gulmohar City 25 lakh", brochure_url=URL, uploads_dir=uploads))
    assert d.draft["price_inr"] == 2500000 and d.sources["price_inr"] == "agent"
    assert d.sources["listing_scope"] == "brochure"


def test_register_match_by_number_fills_rera_and_locality(uploads, monkeypatch):
    monkeypatch.setattr(files, "pdf_text", lambda pdf, max_pages=10: TEXT + " MahaRERA No. P52100012345")
    d = run(AIListingService().create_draft(text="", brochure_url=URL, uploads_dir=uploads, register=FakeRegister([REC])))
    assert d.draft["rera_no"] == "P52100012345" and d.sources["rera_no"] == "maharera"
    assert d.draft["locality"] == "Malthan" and d.sources["locality"] == "maharera"
    assert d.maharera["taluka"] == "Shirur" and d.maharera["promoter"] == "Gulmohar Developers"
    assert d.brochure["rera_no"] == "P52100012345" and d.rera_candidates == []


def test_register_by_name_gives_candidates_only(uploads):
    other = {**REC, "_id": "P52100099999", "regno": "P52100099999", "name": "Gulmohar City Phase II", "taluka": "Haveli"}
    llm = FakeLLM({"project_name": "Gulmohar City Plots"})
    d = run(AIListingService(llm=llm).create_draft(text="", brochure_url=URL, uploads_dir=uploads,
                                                   register=FakeRegister([REC, other])))
    assert "rera_no" not in d.draft and d.maharera is None
    assert {c["regno"] for c in d.rera_candidates} == {"P52100012345", "P52100099999"}
    assert d.rera_candidates[0] == {"regno": "P52100012345", "name": "Gulmohar City", "taluka": "Shirur"}


def test_slow_or_broken_brochure_never_fails(uploads, monkeypatch):
    async def slow(pdf, out_dir):
        await asyncio.sleep(5)
    monkeypatch.setattr(files, "read_brochure", slow)
    b = run(bro.read(URL, uploads, timeout=0.05))
    assert b["error"] and b["claims"] == [] and "Gat No" in b["text"]

    async def boom(pdf, out_dir):
        raise RuntimeError("x")
    monkeypatch.setattr(files, "read_brochure", boom)
    d = run(AIListingService().create_draft(text="2 bhk Baner 85 lakh", brochure_url=URL, uploads_dir=uploads))
    assert d.brochure["error"] and d.draft["price_inr"] == 8500000
    d = run(AIListingService().create_draft(text="2 bhk Baner 85 lakh", brochure_url="/uploads/documents/gone.pdf",
                                            uploads_dir=uploads))
    assert d.brochure["error"] and d.draft["locality"] == "Baner"


def test_project_name_not_locality_without_llm():
    v = extract("Plots for sale in Gulmohar City, Shikrapur road 25 lakh")[0].values
    assert v.get("project_name") == "Gulmohar City" and v.get("locality") != "Gulmohar City"
    assert extract("2 bhk in Pune City 50 lakh")[0].values.get("project_name") is None


def test_router_brochure_field(uploads):
    app = FastAPI()
    app.include_router(r.router, prefix="/api/v1/listings")
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="u1")
    app.dependency_overrides[r.get_llm] = lambda: None
    app.dependency_overrides[r.get_transcriber] = lambda: None
    app.dependency_overrides[r.get_register] = lambda: FakeRegister([REC])
    app.dependency_overrides[r.get_uploads_dir] = lambda: uploads
    res = TestClient(app).post("/api/v1/listings/ai/draft", data={"text": "", "brochure_url": URL})
    assert res.status_code == 200, res.text
    j = res.json()
    assert j["brochure"]["pages"] == 2 and j["draft"]["listing_scope"] == "layout"
    assert j["sources"]["listing_scope"] == "brochure" and isinstance(j["rera_candidates"], list)
    plain = TestClient(app).post("/api/v1/listings/ai/draft", data={"text": "2 bhk Baner 85 lakh"}).json()
    assert plain["brochure"] is None and plain["sources"]["locality"] == "agent"


def test_listing_create_carries_claims():
    media = [{"url": URL, "kind": "document"}]
    body = ListingCreate(media=media, file_claims={"brochure": CLAIMS + ["Call 98765 43210 now"], "rera_on_brochure": "Gat 245"})
    d = body.model_dump()
    assert d["file_claims"]["brochure"] == CLAIMS and d["file_claims"]["rera_on_brochure"] is None
    assert d["file_claims"]["brochure_url"] == URL
    assert "file_claims" not in ListingCreate().model_dump()
    assert "file_claims" not in ListingCreate(file_claims={"brochure": CLAIMS}).model_dump()  # no brochure on the listing


def test_marketing_reuses_claims_for_the_same_file(tmp_path):
    pdf = tmp_path / "abc.pdf"
    listing = {"media": [{"url": URL, "kind": "document"}],
               "file_claims": {"brochure": CLAIMS, "rera_on_brochure": "P52100012345", "brochure_url": URL}}
    kept = files.claims_for(listing, pdf)
    assert kept["claims"] == CLAIMS and kept["rera_no"] == "P52100012345" and not kept["rera_missing"]
    assert files.claims_for({**listing, "file_claims": {**listing["file_claims"], "brochure_url": "/uploads/documents/old.pdf"}},
                            pdf) is None
    assert files.brochure_url(listing, pdf) == URL
