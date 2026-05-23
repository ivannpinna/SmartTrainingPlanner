from fastapi import APIRouter, Depends

from app.core.security import get_current_user_id
from app.schemas.auth_schema import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    get_current_user,
    login_user,
    register_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", response_model=TokenResponse)
async def register(register_data: UserRegisterRequest):
    """
    Creates a new user account and returns an access token.
    """
    return await register_user(register_data)


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLoginRequest):
    """
    Logs in an existing user and returns an access token.
    """
    return await login_user(login_data)


@router.get("/me", response_model=UserResponse)
async def read_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Returns the currently authenticated user.
    """
    return await get_current_user(user_id)