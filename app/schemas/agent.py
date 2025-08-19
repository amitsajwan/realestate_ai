from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class AgentCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    phone: Optional[str] = None

class AgentOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    is_active: bool

class FacebookConfigUpdate(BaseModel):
    facebook_app_id: str = Field(..., example="1101030388754848")
    facebook_app_secret: str = Field(..., example="secret_string")
    facebook_page_id: Optional[str] = Field(None, example="699986296533656")
    access_token: Optional[str] = None
