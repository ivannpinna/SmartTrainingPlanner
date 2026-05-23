from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.workout_schema import WorkoutPlanResponse


class AIWorkoutGenerationResponse(BaseModel):
    message: str
    workout_plan: WorkoutPlanResponse


class AIWorkoutAdaptationRequest(BaseModel):
    workout_plan_id: str = Field(..., min_length=1)
    target_day: Optional[str] = Field(default=None, max_length=30)
    fatigue_level: int = Field(..., ge=1, le=10)
    available_time_minutes: int = Field(..., ge=10, le=180)
    pain_notes: Optional[str] = Field(default=None, max_length=300)
    user_notes: Optional[str] = Field(default=None, max_length=500)


class AdaptedWorkoutExercise(BaseModel):
    name: str
    sets: int
    reps: str
    rest: str
    notes: str


class AdaptedWorkoutDay(BaseModel):
    day: str
    focus: str
    exercises: List[AdaptedWorkoutExercise]


class AIWorkoutAdaptationResponse(BaseModel):
    recommendation: str
    adapted_day: AdaptedWorkoutDay
    explanation: str