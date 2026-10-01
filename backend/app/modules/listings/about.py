"""`about`: project and area knowledge the agent adds at listing creation (docs/contracts/engagement.md, About).

Stored on the listing document exactly as this model dumps it (all fields optional). Free text only: no phone
numbers and no links (buyers reach the agent through the interest link, never a number pasted in a field), control
characters stripped, angle brackets removed so the text is safe wherever it is rendered.
"""
import re
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

MAX_TEXT = 300
NearbyType = Literal["school", "hospital", "transit", "office", "market", "park", "other"]

_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f​-‏  ]")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\s\-.()]*){10,}(?!\d)")
_URL = re.compile(r"(?:https?://|www\.|(?<![\w.])[a-z0-9-]+\.(?:com|in|co|org|net|io|app|me|ly|info)(?:/|\b))", re.I)


def clean_text(v: str, field: str = "text") -> str:
    v = _CTRL.sub(" ", v).replace("<", "").replace(">", "")
    v = re.sub(r"\s+", " ", v).strip()
    if len(v) > MAX_TEXT:
        raise ValueError(f"{field} must be at most {MAX_TEXT} characters")
    if _PHONE.search(v):
        raise ValueError(f"{field} must not contain a phone number; buyers contact you through your interest link")
    if _URL.search(v):
        raise ValueError(f"{field} must not contain a web link")
    return v


def _list(v, field: str, cap: int):
    if not isinstance(v, list):
        raise ValueError(f"{field} must be a list")
    if len(v) > cap:
        raise ValueError(f"{field} can have at most {cap} items")
    out = []
    for x in v:
        if not isinstance(x, str):
            raise ValueError(f"{field} items must be text")
        x = clean_text(x, field)
        if x:
            out.append(x)
    return out


class Nearby(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: NearbyType = "other"
    name: str = Field(..., max_length=MAX_TEXT)
    minutes: Optional[StrictInt] = Field(None, ge=0, le=240)

    @field_validator("name", mode="before")
    @classmethod
    def _name(cls, v):
        if not isinstance(v, str):
            raise ValueError("name must be text")
        v = clean_text(v, "nearby name")
        if not v:
            raise ValueError("nearby name must not be empty")
        return v


class Faq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    q: str = Field(..., max_length=MAX_TEXT)
    a: str = Field(..., max_length=MAX_TEXT)

    @field_validator("q", "a", mode="before")
    @classmethod
    def _qa(cls, v, info):
        if not isinstance(v, str):
            raise ValueError("faq question and answer must be text")
        v = clean_text(v, "faq " + info.field_name)
        if not v:
            raise ValueError("faq question and answer must not be empty")
        return v


_TEXT_FIELDS = ("project_name", "builder_known_as", "water", "power_backup", "maintenance", "society", "parking",
                "possession_note", "rera_note")


class _AboutPublicFields(BaseModel):
    project_name: Optional[str] = None
    builder_known_as: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    nearby: List[Nearby] = Field(default_factory=list)
    connectivity: List[str] = Field(default_factory=list)
    water: Optional[str] = None
    power_backup: Optional[str] = None
    maintenance: Optional[str] = None
    society: Optional[str] = None
    parking: Optional[str] = None
    possession_note: Optional[str] = None
    rera_note: Optional[str] = None


class About(_AboutPublicFields):
    model_config = ConfigDict(extra="forbid")
    faq: List[Faq] = Field(default_factory=list)

    @field_validator(*_TEXT_FIELDS, mode="before")
    @classmethod
    def _t(cls, v, info):
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError(f"{info.field_name} must be text")
        return clean_text(v, info.field_name) or None

    @field_validator("highlights", mode="before")
    @classmethod
    def _hl(cls, v):
        return _list(v, "highlights", 6)

    @field_validator("amenities", mode="before")
    @classmethod
    def _am(cls, v):
        return _list(v, "amenities", 20)

    @field_validator("connectivity", mode="before")
    @classmethod
    def _co(cls, v):
        return _list(v, "connectivity", 8)

    @field_validator("nearby")
    @classmethod
    def _nb(cls, v):
        if len(v) > 12:
            raise ValueError("nearby can have at most 12 items")
        return v

    @field_validator("faq")
    @classmethod
    def _fq(cls, v):
        if len(v) > 8:
            raise ValueError("faq can have at most 8 questions")
        return v


class PublicAbout(_AboutPublicFields):
    """What the public listing page may show. The faq (answers written for the assistant) stays on the agent side."""
    model_config = ConfigDict(extra="ignore")
