from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.db.mongo import get_database
from app.schemas.profile_schema import (
    ProfileCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)


def profile_document_to_response(profile: dict) -> ProfileResponse:
    """
    Converts a MongoDB profile document into a ProfileResponse schema.
    """
    return ProfileResponse(
        id=str(profile["_id"]),
        user_id=profile["user_id"],
        age=profile["age"],
        weight_kg=profile["weight_kg"],
        height_cm=profile["height_cm"],
        goal=profile["goal"],
        level=profile["level"],
        available_days=profile["available_days"],
        equipment=profile.get("equipment", []),
        limitations=profile.get("limitations", []),
        created_at=profile["created_at"],
        updated_at=profile["updated_at"],
    )


async def get_profile_by_user_id(user_id: str) -> dict | None:
    """
    Finds the fitness profile associated with a user.
    """
    database = get_database()
    return await database["profiles"].find_one({"user_id": user_id})


async def create_profile(
    user_id: str,
    profile_data: ProfileCreateRequest,
) -> ProfileResponse:
    """
    Creates a fitness profile for the authenticated user.
    Each user can only have one profile.
    """
    database = get_database()

    existing_profile = await get_profile_by_user_id(user_id)

    if existing_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user already has a fitness profile",
        )

    now = datetime.now(timezone.utc)

    profile_document = {
        "user_id": user_id,
        "age": profile_data.age,
        "weight_kg": profile_data.weight_kg,
        "height_cm": profile_data.height_cm,
        "goal": profile_data.goal,
        "level": profile_data.level,
        "available_days": profile_data.available_days,
        "equipment": profile_data.equipment,
        "limitations": profile_data.limitations,
        "created_at": now,
        "updated_at": now,
    }

    result = await database["profiles"].insert_one(profile_document)

    created_profile = await database["profiles"].find_one(
        {"_id": result.inserted_id}
    )

    if created_profile is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile could not be created",
        )

    return profile_document_to_response(created_profile)


async def get_my_profile(user_id: str) -> ProfileResponse:
    """
    Returns the authenticated user's fitness profile.
    """
    profile = await get_profile_by_user_id(user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fitness profile not found",
        )

    return profile_document_to_response(profile)


async def update_my_profile(
    user_id: str,
    profile_data: ProfileUpdateRequest,
) -> ProfileResponse:
    """
    Updates the authenticated user's fitness profile.
    """
    database = get_database()

    existing_profile = await get_profile_by_user_id(user_id)

    if existing_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fitness profile not found",
        )

    update_data = profile_data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)

    await database["profiles"].update_one(
        {"user_id": user_id},
        {"$set": update_data},
    )

    updated_profile = await get_profile_by_user_id(user_id)

    if updated_profile is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile could not be updated",
        )

    return profile_document_to_response(updated_profile)


async def delete_my_profile(user_id: str) -> dict:
    """
    Deletes the authenticated user's fitness profile.
    """
    database = get_database()

    existing_profile = await get_profile_by_user_id(user_id)

    if existing_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fitness profile not found",
        )

    await database["profiles"].delete_one({"user_id": user_id})

    return {
        "message": "Fitness profile deleted successfully"
    }