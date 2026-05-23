from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ExerciseCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    muscle_groups: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    difficulty: str = Field(..., min_length=2, max_length=50)
    goal_tags: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class ExerciseUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, min_length=10, max_length=1000)
    muscle_groups: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    difficulty: Optional[str] = Field(default=None, min_length=2, max_length=50)
    goal_tags: Optional[List[str]] = None
    limitations: Optional[List[str]] = None


class ExerciseResponse(BaseModel):
    id: str
    name: str
    description: str
    muscle_groups: List[str]
    equipment: List[str]
    difficulty: str
    goal_tags: List[str]
    limitations: List[str]
    has_embedding: bool
    created_at: datetime
    updated_at: datetime