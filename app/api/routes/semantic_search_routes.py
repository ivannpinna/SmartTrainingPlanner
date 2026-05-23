from fastapi import APIRouter, Depends

from app.core.security import get_current_user_id
from app.schemas.semantic_search_schema import (
    GenerateEmbeddingsResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.services.semantic_search_service import (
    generate_missing_exercise_embeddings,
    semantic_search_exercises,
)


router = APIRouter(
    prefix="/semantic-search",
    tags=["Semantic Search"],
)


@router.post(
    "/generate-exercise-embeddings",
    response_model=GenerateEmbeddingsResponse,
)
async def generate_exercise_embeddings(
    user_id: str = Depends(get_current_user_id),
):
    """
    Generates embeddings for all exercises that do not have embeddings yet.

    This endpoint should be called after creating the exercise catalogue.
    """
    return await generate_missing_exercise_embeddings()


@router.post(
    "/exercises",
    response_model=SemanticSearchResponse,
)
async def search_similar_exercises(
    search_data: SemanticSearchRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Searches for exercises using semantic similarity.

    Example query:
    "I need an easier alternative to squats because my knees hurt"
    """
    results = await semantic_search_exercises(
        query=search_data.query,
        limit=search_data.limit,
    )

    return SemanticSearchResponse(
        query=search_data.query,
        results=results,
    )