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
# publish-required per contract (media handled separately from image_count)
REQUIRED_TO_PUBLISH = ("title", "transaction", "property_type", "price_inr", "city", "locality", "media",
                       "description.en")


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
