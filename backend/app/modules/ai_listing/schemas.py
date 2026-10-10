"""AIDraft contract (docs/contracts/listing.md) and the internal Extraction container."""
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel, Field

TRANSACTIONS = ("sale", "rent")
PROPERTY_TYPES = ("apartment", "villa", "house", "plot", "commercial", "office", "shop")
FURNISHING = ("unfurnished", "semi", "furnished")

# fields the extractors may produce (draft keys except title/description which come from copy)
FACT_FIELDS = (
    "transaction", "property_type", "price_inr", "city", "locality", "project_name", "bhk", "carpet_sqft",
    "super_built_up_sqft", "floor", "total_floors", "furnishing", "possession", "rera_no", "amenities",
)
# publish-required per contract (photos are optional)
REQUIRED_TO_PUBLISH = ("title", "transaction", "property_type", "price_inr", "city", "locality", "description.en")


@dataclass
class Extraction:
    values: dict[str, Any] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)

    def set(self, key: str, value: Any, conf: float) -> None:
        if value is None or value == "" or value == []:
            return
        self.values[key] = value
        self.confidence[key] = conf


class Description(BaseModel):
    en: Optional[str] = None
    hi: Optional[str] = None
    mr: Optional[str] = None


class AIDraft(BaseModel):
    draft: dict[str, Any] = Field(default_factory=dict)
    confidence: dict[str, float] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)
    transcript: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    # where each draft field came from: "agent" (their words), "brochure" (the builder's brochure), "maharera" (our register)
    sources: dict[str, str] = Field(default_factory=dict)
    # register projects the agent can pick with one tap when the brochure's project was matched by name only
    rera_candidates: list[dict[str, Any]] = Field(default_factory=list)
    # what was read from the brochure: {claims: [...], rera_no, pages, error?}; None without one
    brochure: Optional[dict[str, Any]] = None
    # the register record matched by registration number: {regno, name, locality, taluka, pincode, promoter, completion_*}
    maharera: Optional[dict[str, Any]] = None
    # the brochure's selling points for the agent to confirm: [{key, text, text_local?, value, source: "brochure"}]
    # (propertyfacts/points.py); only points the agent saves on the listing with confirmed: true reach the posts
    selling_points: list[dict[str, Any]] = Field(default_factory=list)
