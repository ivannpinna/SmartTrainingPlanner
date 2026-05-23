from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class WorkoutExercise(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    sets: int = Field(..., ge=1, le=20)
    reps: str = Field(..., min_length=1, max_length=50)
    rest: str = Field(default="60 seconds", max_length=50)
    notes: Optional[str] = Field(default=None, max_length=300)


class WorkoutDay(BaseModel):
    day: str = Field(..., min_length=2, max_length=30)
    focus: str = Field(..., min_length=2, max_length=100)
    exercises: List[WorkoutExercise] = Field(default_factory=list)


class WorkoutPlanCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    goal: str = Field(..., min_length=2, max_length=100)
    days: List[WorkoutDay] = Field(..., min_length=1)


class WorkoutPlanUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=120)
    goal: Optional[str] = Field(default=None, min_length=2, max_length=100)
    days: Optional[List[WorkoutDay]] = None
    is_active: Optional[bool] = None


class WorkoutPlanResponse(BaseModel):
    id: str
    user_id: str
    title: str
    goal: str
    days: List[WorkoutDay]
    is_active: bool
    created_at: datetime
    updated_at: datetime