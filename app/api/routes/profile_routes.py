from fastapi import APIRouter, Depends

from app.core.security import get_current_user_id
from app.schemas.profile_schema import (
    ProfileCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.services.profile_service import (
    create_profile,
    delete_my_profile,
    get_my_profile,
    update_my_profile,
)


router = APIRouter(
    prefix="/profile",
    tags=["Fitness Profile"],
)


@router.post("", response_model=ProfileResponse)
async def create_my_fitness_profile(
    profile_data: ProfileCreateRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Creates a fitness profile for the authenticated user.
    """
    return await create_profile(user_id, profile_data)


@router.get("/me", response_model=ProfileResponse)
async def read_my_fitness_profile(
    user_id: str = Depends(get_current_user_id),
):
    """
    Returns the authenticated user's fitness profile.
    """
    return await get_my_profile(user_id)


@router.put("/me", response_model=ProfileResponse)
async def update_my_fitness_profile(
    profile_data: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Updates the authenticated user's fitness profile.
    """
    return await update_my_profile(user_id, profile_data)


@router.delete("/me")
async def delete_my_fitness_profile(
    user_id: str = Depends(get_current_user_id),
):
    """
    Deletes the authenticated user's fitness profile.
    """
    return await delete_my_profile(user_id)