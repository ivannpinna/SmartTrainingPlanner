from typing import List

import numpy as np
from fastapi import HTTPException, status

from app.db.mongo import get_database
from app.services.embedding_service import create_embedding
from app.services.exercise_service import build_exercise_text_for_embedding


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """
    Calculates cosine similarity between two vectors.
    The result is between -1 and 1.
    Higher values mean more semantic similarity.
    """
    a = np.array(vector_a, dtype=float)
    b = np.array(vector_b, dtype=float)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


async def generate_missing_exercise_embeddings() -> dict:
    """
    Generates embeddings for all exercises that do not have one yet.
    This will be useful before using semantic search.
    """
    database = get_database()

    cursor = database["exercises"].find(
        {
            "$or": [
                {"embedding": None},
                {"embedding": {"$exists": False}},
            ]
        }
    )

    exercises_without_embedding = await cursor.to_list(length=500)

    updated_count = 0

    for exercise in exercises_without_embedding:
        text_for_embedding = build_exercise_text_for_embedding(exercise)
        embedding = await create_embedding(text_for_embedding)

        await database["exercises"].update_one(
            {"_id": exercise["_id"]},
            {
                "$set": {
                    "embedding": embedding,
                }
            },
        )

        updated_count += 1

    return {
        "message": "Exercise embeddings generated successfully",
        "updated_count": updated_count,
    }


async def semantic_search_exercises(
    query: str,
    limit: int = 5,
) -> List[dict]:
    """
    Searches for exercises semantically similar to the user's query.
    """
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty",
        )

    database = get_database()

    query_embedding = await create_embedding(query)

    cursor = database["exercises"].find(
        {
            "embedding": {
                "$exists": True,
                "$ne": None,
            }
        }
    )

    exercises = await cursor.to_list(length=500)

    if not exercises:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No exercises with embeddings found. Generate embeddings first.",
        )

    scored_results = []

    for exercise in exercises:
        exercise_embedding = exercise.get("embedding")

        if not exercise_embedding:
            continue

        similarity = cosine_similarity(query_embedding, exercise_embedding)

        scored_results.append(
            {
                "id": str(exercise["_id"]),
                "name": exercise["name"],
                "description": exercise["description"],
                "muscle_groups": exercise.get("muscle_groups", []),
                "equipment": exercise.get("equipment", []),
                "difficulty": exercise.get("difficulty", ""),
                "goal_tags": exercise.get("goal_tags", []),
                "limitations": exercise.get("limitations", []),
                "similarity": round(similarity, 4),
            }
        )

    scored_results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return scored_results[:limit]