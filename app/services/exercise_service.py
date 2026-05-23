from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongo import get_database
from app.schemas.exercise_schema import (
    ExerciseCreateRequest,
    ExerciseResponse,
    ExerciseUpdateRequest,
)


def exercise_document_to_response(exercise: dict) -> ExerciseResponse:
    """
    Converts a MongoDB exercise document into an ExerciseResponse schema.
    """
    return ExerciseResponse(
        id=str(exercise["_id"]),
        name=exercise["name"],
        description=exercise["description"],
        muscle_groups=exercise.get("muscle_groups", []),
        equipment=exercise.get("equipment", []),
        difficulty=exercise["difficulty"],
        goal_tags=exercise.get("goal_tags", []),
        limitations=exercise.get("limitations", []),
        has_embedding=bool(exercise.get("embedding")),
        created_at=exercise["created_at"],
        updated_at=exercise["updated_at"],
    )


def build_exercise_text_for_embedding(exercise: dict) -> str:
    """
    Creates a rich text representation of an exercise.
    Later, this text will be converted into an embedding.
    """
    muscle_groups = ", ".join(exercise.get("muscle_groups", []))
    equipment = ", ".join(exercise.get("equipment", []))
    goal_tags = ", ".join(exercise.get("goal_tags", []))
    limitations = ", ".join(exercise.get("limitations", []))

    return (
        f"Exercise name: {exercise.get('name', '')}. "
        f"Description: {exercise.get('description', '')}. "
        f"Muscle groups: {muscle_groups}. "
        f"Equipment: {equipment}. "
        f"Difficulty: {exercise.get('difficulty', '')}. "
        f"Training goals: {goal_tags}. "
        f"Limitations or precautions: {limitations}."
    )


async def create_exercise(
    exercise_data: ExerciseCreateRequest,
) -> ExerciseResponse:
    """
    Creates an exercise in the exercise catalogue.
    The embedding will be generated later with OpenAI.
    """
    database = get_database()

    existing_exercise = await database["exercises"].find_one(
        {"name": {"$regex": f"^{exercise_data.name}$", "$options": "i"}}
    )

    if existing_exercise is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An exercise with this name already exists",
        )

    now = datetime.now(timezone.utc)

    exercise_document = {
        "name": exercise_data.name,
        "description": exercise_data.description,
        "muscle_groups": exercise_data.muscle_groups,
        "equipment": exercise_data.equipment,
        "difficulty": exercise_data.difficulty,
        "goal_tags": exercise_data.goal_tags,
        "limitations": exercise_data.limitations,
        "embedding": None,
        "created_at": now,
        "updated_at": now,
    }

    result = await database["exercises"].insert_one(exercise_document)

    created_exercise = await database["exercises"].find_one(
        {"_id": result.inserted_id}
    )

    if created_exercise is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Exercise could not be created",
        )

    return exercise_document_to_response(created_exercise)


async def list_exercises() -> List[ExerciseResponse]:
    """
    Returns all exercises from the catalogue.
    """
    database = get_database()

    cursor = database["exercises"].find().sort("name", 1)
    exercises = await cursor.to_list(length=200)

    return [
        exercise_document_to_response(exercise)
        for exercise in exercises
    ]


async def get_exercise_document_by_id(exercise_id: str) -> dict:
    """
    Finds an exercise by its MongoDB ID.
    """
    database = get_database()

    if not ObjectId.is_valid(exercise_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid exercise ID",
        )

    exercise = await database["exercises"].find_one(
        {"_id": ObjectId(exercise_id)}
    )

    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )

    return exercise


async def get_exercise(exercise_id: str) -> ExerciseResponse:
    """
    Returns one exercise from the catalogue.
    """
    exercise = await get_exercise_document_by_id(exercise_id)
    return exercise_document_to_response(exercise)


async def update_exercise(
    exercise_id: str,
    exercise_data: ExerciseUpdateRequest,
) -> ExerciseResponse:
    """
    Updates an exercise.
    If the text changes, the embedding is cleared so it can be regenerated later.
    """
    database = get_database()

    await get_exercise_document_by_id(exercise_id)

    update_data = exercise_data.model_dump(exclude_unset=True)

    fields_that_affect_embedding = {
        "name",
        "description",
        "muscle_groups",
        "equipment",
        "difficulty",
        "goal_tags",
        "limitations",
    }

    if any(field in update_data for field in fields_that_affect_embedding):
        update_data["embedding"] = None

    update_data["updated_at"] = datetime.now(timezone.utc)

    await database["exercises"].update_one(
        {"_id": ObjectId(exercise_id)},
        {"$set": update_data},
    )

    updated_exercise = await get_exercise_document_by_id(exercise_id)

    return exercise_document_to_response(updated_exercise)


async def delete_exercise(exercise_id: str) -> dict:
    """
    Deletes an exercise from the catalogue.
    """
    database = get_database()

    await get_exercise_document_by_id(exercise_id)

    await database["exercises"].delete_one(
        {"_id": ObjectId(exercise_id)}
    )

    return {
        "message": "Exercise deleted successfully"
    }