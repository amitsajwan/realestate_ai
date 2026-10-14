"""AI draft: the project matched in our MahaRERA register from the agent's words (brochures are stored, never read), and
brochure claims kept on older listings."""
import asyncio
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.ai_listing import router as r
from app.modules.ai_listing.extractor import extract
from app.modules.ai_listing.service import AIListingService
from app.modules.listings.schemas import ListingCreate
from app.modules.propertyfacts import files

CLAIMS = ["Gulmohar City is at Malthan, 10 minutes from Shikrapur.", "Plots from 1000 sq ft to 2500 sq ft."]
URL = "/uploads/documents/abc.pdf"


class FakeLLM:
    def __init__(self, out=None):
        self.out = out

    async def extract(self, text, city_hint=None):
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


def run(coro):
    return asyncio.run(coro)


def test_register_match_by_number_fills_rera_and_locality():
    d = run(AIListingService().create_draft(text="Plots in Gulmohar City 25 lakh, MahaRERA P52100012345",
                                            register=FakeRegister([REC])))
    assert d.draft["rera_no"] == "P52100012345" and d.sources["rera_no"] == "maharera"
    assert d.draft["locality"] == "Malthan" and d.sources["locality"] == "maharera"
    assert d.maharera["taluka"] == "Shirur" and d.maharera["promoter"] == "Gulmohar Developers"
    assert d.draft["price_inr"] == 2500000 and d.sources["price_inr"] == "agent"


def test_register_by_name_gives_candidates_only():
    other = {**REC, "_id": "P52100099999", "regno": "P52100099999", "name": "Gulmohar City Phase II", "taluka": "Haveli"}
    llm = FakeLLM({"project_name": "Gulmohar City Plots", "rera_no": "245"})
    d = run(AIListingService(llm=llm).create_draft(text="plots in gulmohar city", register=FakeRegister([REC, other])))
    assert "rera_no" not in d.draft and d.maharera is None      # a gat number is not a registration
    assert {c["regno"] for c in d.rera_candidates} == {"P52100012345", "P52100099999"}
    assert d.rera_candidates[0] == {"regno": "P52100012345", "name": "Gulmohar City", "taluka": "Shirur"}


def test_project_name_not_locality_without_llm():
    v = extract("Plots for sale in Gulmohar City, Shikrapur road 25 lakh")[0].values
    assert v.get("project_name") == "Gulmohar City" and v.get("locality") != "Gulmohar City"
    assert extract("2 bhk in Pune City 50 lakh")[0].values.get("project_name") is None


def test_router_draft_from_words_only():
    app = FastAPI()
    app.include_router(r.router, prefix="/api/v1/listings")
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="u1")
    app.dependency_overrides[r.get_llm] = lambda: None
    app.dependency_overrides[r.get_transcriber] = lambda: None
    app.dependency_overrides[r.get_register] = lambda: FakeRegister([REC])
    j = TestClient(app).post("/api/v1/listings/ai/draft", data={"text": "2 bhk Baner 85 lakh"}).json()
    assert j["sources"]["locality"] == "agent" and "brochure" not in j and "selling_points" not in j


def test_listing_create_carries_claims():
    media = [{"url": URL, "kind": "document"}]
    body = ListingCreate(media=media, file_claims={"brochure": CLAIMS + ["Call 98765 43210 now"], "rera_on_brochure": "Gat 245"})
    d = body.model_dump()
    assert d["file_claims"]["brochure"] == CLAIMS and d["file_claims"]["rera_on_brochure"] is None
    assert d["file_claims"]["brochure_url"] == URL
    assert "file_claims" not in ListingCreate().model_dump()
    assert "file_claims" not in ListingCreate(file_claims={"brochure": CLAIMS}).model_dump()  # no brochure on the listing


def test_marketing_reuses_claims_for_the_same_file(tmp_path):
    pdf = Path(tmp_path) / "abc.pdf"
    listing = {"media": [{"url": URL, "kind": "document"}],
               "file_claims": {"brochure": CLAIMS, "rera_on_brochure": "P52100012345", "brochure_url": URL}}
    kept = files.claims_for(listing, pdf)
    assert kept["claims"] == CLAIMS and kept["rera_no"] == "P52100012345" and not kept["rera_missing"]
    assert files.claims_for({**listing, "file_claims": {**listing["file_claims"], "brochure_url": "/uploads/documents/old.pdf"}},
                            pdf) is None
