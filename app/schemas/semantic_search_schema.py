from typing import List

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


class SemanticExerciseResult(BaseModel):
    id: str
    name: str
    description: str
    muscle_groups: List[str]
    equipment: List[str]
    difficulty: str
    goal_tags: List[str]
    limitations: List[str]
    similarity: float


class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SemanticExerciseResult]


class GenerateEmbeddingsResponse(BaseModel):
    message: str
    updated_count: int