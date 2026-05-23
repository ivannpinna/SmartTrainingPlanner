from typing import List

from fastapi import APIRouter, Depends

from app.core.security import get_current_user_id
from app.schemas.workout_schema import (
    WorkoutPlanCreateRequest,
    WorkoutPlanResponse,
    WorkoutPlanUpdateRequest,
)
from app.services.workout_service import (
    create_workout_plan,
    delete_my_workout_plan,
    get_my_workout_plan,
    list_my_workout_plans,
    update_my_workout_plan,
)


router = APIRouter(
    prefix="/workouts",
    tags=["Workout Plans"],
)


@router.post("", response_model=WorkoutPlanResponse)
async def create_my_workout_plan(
    workout_data: WorkoutPlanCreateRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Creates a new workout plan for the authenticated user.
    """
    return await create_workout_plan(user_id, workout_data)


@router.get("", response_model=List[WorkoutPlanResponse])
async def read_my_workout_plans(
    user_id: str = Depends(get_current_user_id),
):
    """
    Returns all workout plans created by the authenticated user.
    """
    return await list_my_workout_plans(user_id)


@router.get("/{workout_id}", response_model=WorkoutPlanResponse)
async def read_my_workout_plan(
    workout_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Returns a specific workout plan by ID.
    """
    return await get_my_workout_plan(user_id, workout_id)


@router.put("/{workout_id}", response_model=WorkoutPlanResponse)
async def update_workout_plan(
    workout_id: str,
    workout_data: WorkoutPlanUpdateRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Updates a specific workout plan.
    """
    return await update_my_workout_plan(user_id, workout_id, workout_data)


@router.delete("/{workout_id}")
async def delete_workout_plan(
    workout_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Deletes a specific workout plan.
    """
    return await delete_my_workout_plan(user_id, workout_id)