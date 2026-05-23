from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongo import get_database
from app.schemas.workout_schema import (
    WorkoutPlanCreateRequest,
    WorkoutPlanResponse,
    WorkoutPlanUpdateRequest,
)


def workout_document_to_response(workout: dict) -> WorkoutPlanResponse:
    """
    Converts a MongoDB workout document into a WorkoutPlanResponse schema.
    """
    return WorkoutPlanResponse(
        id=str(workout["_id"]),
        user_id=workout["user_id"],
        title=workout["title"],
        goal=workout["goal"],
        days=workout.get("days", []),
        is_active=workout.get("is_active", False),
        created_at=workout["created_at"],
        updated_at=workout["updated_at"],
    )


async def create_workout_plan(
    user_id: str,
    workout_data: WorkoutPlanCreateRequest,
) -> WorkoutPlanResponse:
    """
    Creates a workout plan for the authenticated user.
    """
    database = get_database()
    now = datetime.now(timezone.utc)

    workout_document = {
        "user_id": user_id,
        "title": workout_data.title,
        "goal": workout_data.goal,
        "days": [day.model_dump() for day in workout_data.days],
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    result = await database["workout_plans"].insert_one(workout_document)

    created_workout = await database["workout_plans"].find_one(
        {"_id": result.inserted_id}
    )

    if created_workout is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workout plan could not be created",
        )

    return workout_document_to_response(created_workout)


async def list_my_workout_plans(user_id: str) -> List[WorkoutPlanResponse]:
    """
    Returns all workout plans created by the authenticated user.
    """
    database = get_database()

    cursor = database["workout_plans"].find(
        {"user_id": user_id}
    ).sort("created_at", -1)

    workouts = await cursor.to_list(length=100)

    return [
        workout_document_to_response(workout)
        for workout in workouts
    ]


async def get_workout_document_by_id(
    user_id: str,
    workout_id: str,
) -> dict:
    """
    Finds a workout plan by ID, ensuring it belongs to the authenticated user.
    """
    database = get_database()

    if not ObjectId.is_valid(workout_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workout plan ID",
        )

    workout = await database["workout_plans"].find_one(
        {
            "_id": ObjectId(workout_id),
            "user_id": user_id,
        }
    )

    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout plan not found",
        )

    return workout


async def get_my_workout_plan(
    user_id: str,
    workout_id: str,
) -> WorkoutPlanResponse:
    """
    Returns one workout plan from the authenticated user.
    """
    workout = await get_workout_document_by_id(user_id, workout_id)
    return workout_document_to_response(workout)


async def update_my_workout_plan(
    user_id: str,
    workout_id: str,
    workout_data: WorkoutPlanUpdateRequest,
) -> WorkoutPlanResponse:
    """
    Updates one workout plan from the authenticated user.
    """
    database = get_database()

    await get_workout_document_by_id(user_id, workout_id)

    update_data = workout_data.model_dump(exclude_unset=True)

    if "days" in update_data and update_data["days"] is not None:
        update_data["days"] = [
            day.model_dump() if hasattr(day, "model_dump") else day
            for day in workout_data.days
        ]

    update_data["updated_at"] = datetime.now(timezone.utc)

    await database["workout_plans"].update_one(
        {
            "_id": ObjectId(workout_id),
            "user_id": user_id,
        },
        {
            "$set": update_data
        },
    )

    updated_workout = await get_workout_document_by_id(user_id, workout_id)

    return workout_document_to_response(updated_workout)


async def delete_my_workout_plan(
    user_id: str,
    workout_id: str,
) -> dict:
    """
    Deletes one workout plan from the authenticated user.
    """
    database = get_database()

    await get_workout_document_by_id(user_id, workout_id)

    await database["workout_plans"].delete_one(
        {
            "_id": ObjectId(workout_id),
            "user_id": user_id,
        }
    )

    return {
        "message": "Workout plan deleted successfully"
    }