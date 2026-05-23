from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TrainingLogCreateRequest(BaseModel):
    workout_plan_id: Optional[str] = Field(default=None)
    training_date: str = Field(..., description="Date in YYYY-MM-DD format")
    completed: bool = Field(default=False)
    fatigue_level: int = Field(..., ge=1, le=10)
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=300)
    pain_notes: Optional[str] = Field(default=None, max_length=300)
    notes: Optional[str] = Field(default=None, max_length=500)


class TrainingLogUpdateRequest(BaseModel):
    workout_plan_id: Optional[str] = None
    training_date: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD format")
    completed: Optional[bool] = None
    fatigue_level: Optional[int] = Field(default=None, ge=1, le=10)
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=300)
    pain_notes: Optional[str] = Field(default=None, max_length=300)
    notes: Optional[str] = Field(default=None, max_length=500)


class TrainingLogResponse(BaseModel):
    id: str
    user_id: str
    workout_plan_id: Optional[str]
    training_date: str
    completed: bool
    fatigue_level: int
    duration_minutes: Optional[int]
    pain_notes: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime