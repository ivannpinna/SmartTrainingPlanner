from bson import ObjectId
from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.db.mongo import get_database
from app.schemas.auth_schema import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


def user_document_to_response(user: dict) -> UserResponse:
    """
    Converts a MongoDB user document into a UserResponse schema.
    """
    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
    )


async def get_user_by_email(email: str) -> dict | None:
    """
    Finds a user by email.
    """
    database = get_database()
    return await database["users"].find_one({"email": email})


async def get_user_by_id(user_id: str) -> dict | None:
    """
    Finds a user by MongoDB ObjectId.
    """
    database = get_database()

    if not ObjectId.is_valid(user_id):
        return None

    return await database["users"].find_one({"_id": ObjectId(user_id)})


async def register_user(register_data: UserRegisterRequest) -> TokenResponse:
    """
    Registers a new user and returns a JWT token.
    """
    database = get_database()

    existing_user = await get_user_by_email(register_data.email)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    user_document = {
        "name": register_data.name,
        "email": register_data.email,
        "password_hash": hash_password(register_data.password),
    }

    result = await database["users"].insert_one(user_document)

    created_user = await database["users"].find_one({"_id": result.inserted_id})

    if created_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User could not be created",
        )

    access_token = create_access_token(subject=str(created_user["_id"]))

    return TokenResponse(
        access_token=access_token,
        user=user_document_to_response(created_user),
    )


async def login_user(login_data: UserLoginRequest) -> TokenResponse:
    """
    Authenticates a user and returns a JWT token.
    """
    user = await get_user_by_email(login_data.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    password_is_valid = verify_password(
        plain_password=login_data.password,
        hashed_password=user["password_hash"],
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(subject=str(user["_id"]))

    return TokenResponse(
        access_token=access_token,
        user=user_document_to_response(user),
    )


async def get_current_user(user_id: str) -> UserResponse:
    """
    Returns the authenticated user's public data.
    """
    user = await get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user_document_to_response(user)