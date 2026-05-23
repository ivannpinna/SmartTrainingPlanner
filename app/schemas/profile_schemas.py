from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProfileCreateRequest(BaseModel):
    age: int = Field(..., ge=12, le=100)
    weight_kg: float = Field(..., gt=0, le=300)
    height_cm: float = Field(..., gt=0, le=250)
    goal: str = Field(..., min_length=2, max_length=100)
    level: str = Field(..., min_length=2, max_length=50)
    available_days: int = Field(..., ge=1, le=7)
    equipment: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class ProfileUpdateRequest(BaseModel):
    age: Optional[int] = Field(default=None, ge=12, le=100)
    weight_kg: Optional[float] = Field(default=None, gt=0, le=300)
    height_cm: Optional[float] = Field(default=None, gt=0, le=250)
    goal: Optional[str] = Field(default=None, min_length=2, max_length=100)
    level: Optional[str] = Field(default=None, min_length=2, max_length=50)
    available_days: Optional[int] = Field(default=None, ge=1, le=7)
    equipment: Optional[List[str]] = None
    limitations: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    age: int
    weight_kg: float
    height_cm: float
    goal: str
    level: str
    available_days: int
    equipment: List[str]
    limitations: List[str]
    created_at: datetime
    updated_at: datetime