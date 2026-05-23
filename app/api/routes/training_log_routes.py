from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongo import get_database
from app.schemas.training_log_schema import (
    TrainingLogCreateRequest,
    TrainingLogResponse,
    TrainingLogUpdateRequest,
)


def training_log_document_to_response(training_log: dict) -> TrainingLogResponse:
    """
    Converts a MongoDB training log document into a TrainingLogResponse schema.
    """
    return TrainingLogResponse(
        id=str(training_log["_id"]),
        user_id=training_log["user_id"],
        workout_plan_id=training_log.get("workout_plan_id"),
        training_date=training_log["training_date"],
        completed=training_log["completed"],
        fatigue_level=training_log["fatigue_level"],
        duration_minutes=training_log.get("duration_minutes"),
        pain_notes=training_log.get("pain_notes"),
        notes=training_log.get("notes"),
        created_at=training_log["created_at"],
        updated_at=training_log["updated_at"],
    )


async def validate_workout_plan_belongs_to_user(
    user_id: str,
    workout_plan_id: str | None,
) -> None:
    """
    Checks that the workout plan exists and belongs to the authenticated user.
    If workout_plan_id is None, it does nothing.
    """
    if workout_plan_id is None:
        return

    if not ObjectId.is_valid(workout_plan_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workout plan ID",
        )

    database = get_database()

    workout_plan = await database["workout_plans"].find_one(
        {
            "_id": ObjectId(workout_plan_id),
            "user_id": user_id,
        }
    )

    if workout_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout plan not found",
        )


async def create_training_log(
    user_id: str,
    training_log_data: TrainingLogCreateRequest,
) -> TrainingLogResponse:
    """
    Creates a daily training log for the authenticated user.
    """
    database = get_database()

    await validate_workout_plan_belongs_to_user(
        user_id=user_id,
        workout_plan_id=training_log_data.workout_plan_id,
    )

    now = datetime.now(timezone.utc)

    training_log_document = {
        "user_id": user_id,
        "workout_plan_id": training_log_data.workout_plan_id,
        "training_date": training_log_data.training_date,
        "completed": training_log_data.completed,
        "fatigue_level": training_log_data.fatigue_level,
        "duration_minutes": training_log_data.duration_minutes,
        "pain_notes": training_log_data.pain_notes,
        "notes": training_log_data.notes,
        "created_at": now,
        "updated_at": now,
    }

    result = await database["training_logs"].insert_one(training_log_document)

    created_training_log = await database["training_logs"].find_one(
        {"_id": result.inserted_id}
    )

    if created_training_log is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Training log could not be created",
        )

    return training_log_document_to_response(created_training_log)


async def list_my_training_logs(user_id: str) -> List[TrainingLogResponse]:
    """
    Returns all training logs created by the authenticated user.
    """
    database = get_database()

    cursor = database["training_logs"].find(
        {"user_id": user_id}
    ).sort("training_date", -1)

    training_logs = await cursor.to_list(length=100)

    return [
        training_log_document_to_response(training_log)
        for training_log in training_logs
    ]


async def get_training_log_document_by_id(
    user_id: str,
    training_log_id: str,
) -> dict:
    """
    Finds a training log by ID, ensuring it belongs to the authenticated user.
    """
    database = get_database()

    if not ObjectId.is_valid(training_log_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid training log ID",
        )

    training_log = await database["training_logs"].find_one(
        {
            "_id": ObjectId(training_log_id),
            "user_id": user_id,
        }
    )

    if training_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training log not found",
        )

    return training_log


async def get_my_training_log(
    user_id: str,
    training_log_id: str,
) -> TrainingLogResponse:
    """
    Returns one training log from the authenticated user.
    """
    training_log = await get_training_log_document_by_id(
        user_id=user_id,
        training_log_id=training_log_id,
    )

    return training_log_document_to_response(training_log)


async def update_my_training_log(
    user_id: str,
    training_log_id: str,
    training_log_data: TrainingLogUpdateRequest,
) -> TrainingLogResponse:
    """
    Updates one training log from the authenticated user.
    """
    database = get_database()

    await get_training_log_document_by_id(
        user_id=user_id,
        training_log_id=training_log_id,
    )

    update_data = training_log_data.model_dump(exclude_unset=True)

    if "workout_plan_id" in update_data:
        await validate_workout_plan_belongs_to_user(
            user_id=user_id,
            workout_plan_id=update_data["workout_plan_id"],
        )

    update_data["updated_at"] = datetime.now(timezone.utc)

    await database["training_logs"].update_one(
        {
            "_id": ObjectId(training_log_id),
            "user_id": user_id,
        },
        {
            "$set": update_data
        },
    )

    updated_training_log = await get_training_log_document_by_id(
        user_id=user_id,
        training_log_id=training_log_id,
    )

    return training_log_document_to_response(updated_training_log)


async def delete_my_training_log(
    user_id: str,
    training_log_id: str,
) -> dict:
    """
    Deletes one training log from the authenticated user.
    """
    database = get_database()

    await get_training_log_document_by_id(
        user_id=user_id,
        training_log_id=training_log_id,
    )

    await database["training_logs"].delete_one(
        {
            "_id": ObjectId(training_log_id),
            "user_id": user_id,
        }
    )

    return {
        "message": "Training log deleted successfully"
    }