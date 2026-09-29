"""Pydantic models for the frozen marketing-pack contract (section 1)."""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict

Language = Literal["en", "hi", "mr"]
ImageKind = Literal["cover", "facts", "amenities", "cta", "status"]


class GenerateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Language = "en"


class ImageAsset(BaseModel):
    kind: ImageKind
    url: str
    width: int
    height: int


class Instagram(BaseModel):
    caption: str
    hashtags: List[str]
    images: List[ImageAsset]


class Facebook(BaseModel):
    post: str


class WhatsApp(BaseModel):
    message: str
    status_text: str
    status_image: Optional[ImageAsset] = None


class ReelBeat(BaseModel):
    seconds: str
    text: str
    visual: str


class Reel(BaseModel):
    hook: str
    beats: List[ReelBeat]
    cta: str
    duration_s: int


class MarketingPack(BaseModel):
    listing_id: str
    language: Language
    version: int
    generated_at: str
    angle: str
    headline: str
    instagram: Instagram
    facebook: Facebook
    whatsapp: WhatsApp
    reel: Reel
    share_url: str
