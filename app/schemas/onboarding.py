from pydantic import BaseModel, Field
from typing import Optional

class OnboardingStep(BaseModel):
    step_number: int = Field(..., description="Current step number in the onboarding process")
    data: dict = Field(..., description="Data associated with the current step")

class OnboardingComplete(BaseModel):
    user_id: str = Field(..., description="User ID of the completed onboarding")
    message: str = Field(..., description="Completion message")