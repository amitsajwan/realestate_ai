"""Pydantic models for the frozen social contract."""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Channel = Literal["facebook_page", "instagram"]
Status = Literal["queued", "published", "failed", "dry_run"]


class PublishIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channels: List[Channel] = Field(min_length=1)
    approve: bool = False
    consent: bool = False
    force: bool = False


class Consent(BaseModel):
    given_at: str
    text: str


class Payload(BaseModel):
    text: str
    image_urls: List[str]


class Publication(BaseModel):
    id: str
    listing_id: str
    agent_id: str
    channel: Channel
    pack_version: int
    status: Status
    external_id: Optional[str] = None
    permalink: Optional[str] = None
    error: Optional[str] = None
    consent: Consent
    approved_at: str
    created_at: str
    updated_at: str
    attempts: int
    payload: Payload


class PublishOut(BaseModel):
    publications: List[Publication]


class ListOut(BaseModel):
    items: List[Publication]


class StatusOut(BaseModel):
    dry_run: bool
    channels: Dict[str, bool]
    brand: str
    media_url_ok: bool
