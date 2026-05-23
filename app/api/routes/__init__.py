from fastapi import APIRouter

from . import (
    ai_routes,
    auth_routes,
    exercise_routes,
    profile_routes,
    semantic_search_routes,
    training_log_routes,
    workout_routes,
)


api_router = APIRouter()

api_router.include_router(auth_routes.router)
api_router.include_router(profile_routes.router)
api_router.include_router(workout_routes.router)
api_router.include_router(training_log_routes.router)
api_router.include_router(exercise_routes.router)
api_router.include_router(semantic_search_routes.router)
api_router.include_router(ai_routes.router)