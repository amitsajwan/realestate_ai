from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId


class SmartPropertyDocument(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    property_id: str
    user_id: str
    smart_features: Dict[str, Any] = Field(default_factory=dict)
    ai_insights: Dict[str, Any] = Field(default_factory=dict)
    market_analysis: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    automation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


class SmartPropertyCreate(BaseModel):
    property_id: str
    smart_features: Optional[Dict[str, Any]] = None
    ai_insights: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    automation_rules: Optional[List[Dict[str, Any]]] = None
    # Additional fields for API compatibility
    address: Optional[str] = None
    price: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    features: Optional[str] = None
    template: Optional[str] = "just_listed"
    language: Optional[str] = "en"
    ai_generate: Optional[bool] = True
    ai_content: Optional[str] = None


class SmartPropertyUpdate(BaseModel):
    smart_features: Optional[Dict[str, Any]] = None
    ai_insights: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    automation_rules: Optional[List[Dict[str, Any]]] = None


class SmartPropertyResponse(BaseModel):
    id: str
    property_id: str
    user_id: str
    smart_features: Dict[str, Any]
    ai_insights: Dict[str, Any]
    market_analysis: Dict[str, Any]
    recommendations: List[str]
    automation_rules: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {ObjectId: str}
