import json
from typing import Any, Dict, List

from fastapi import HTTPException, status
from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from app.core.config import settings
from app.db.mongo import get_database
from app.schemas.ai_schema import (
    AIWorkoutAdaptationRequest,
    AIWorkoutAdaptationResponse,
    AIWorkoutGenerationResponse,
)
from app.schemas.workout_schema import WorkoutPlanCreateRequest
from app.services.profile_service import get_profile_by_user_id
from app.services.workout_service import (
    create_workout_plan,
    get_workout_document_by_id,
)


WORKOUT_PLAN_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string"
        },
        "goal": {
            "type": "string"
        },
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "string"
                    },
                    "focus": {
                        "type": "string"
                    },
                    "exercises": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string"
                                },
                                "sets": {
                                    "type": "integer"
                                },
                                "reps": {
                                    "type": "string"
                                },
                                "rest": {
                                    "type": "string"
                                },
                                "notes": {
                                    "type": "string"
                                },
                            },
                            "required": [
                                "name",
                                "sets",
                                "reps",
                                "rest",
                                "notes",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "day",
                    "focus",
                    "exercises",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "title",
        "goal",
        "days",
    ],
    "additionalProperties": False,
}


WORKOUT_ADAPTATION_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "recommendation": {
            "type": "string"
        },
        "adapted_day": {
            "type": "object",
            "properties": {
                "day": {
                    "type": "string"
                },
                "focus": {
                    "type": "string"
                },
                "exercises": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "sets": {
                                "type": "integer"
                            },
                            "reps": {
                                "type": "string"
                            },
                            "rest": {
                                "type": "string"
                            },
                            "notes": {
                                "type": "string"
                            },
                        },
                        "required": [
                            "name",
                            "sets",
                            "reps",
                            "rest",
                            "notes",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": [
                "day",
                "focus",
                "exercises",
            ],
            "additionalProperties": False,
        },
        "explanation": {
            "type": "string"
        },
    },
    "required": [
        "recommendation",
        "adapted_day",
        "explanation",
    ],
    "additionalProperties": False,
}


def get_openai_client() -> AsyncOpenAI:
    """
    Creates an async OpenAI client.
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key is not configured",
        )

    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def parse_json_response(content: str) -> Dict[str, Any]:
    """
    Parses the JSON returned by the AI model.
    """
    try:
        return json.loads(content)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI response was not valid JSON",
        )


async def get_exercise_catalog_text() -> str:
    """
    Reads the exercise catalogue from MongoDB and converts it into text.
    This helps the AI generate plans using exercises from our database.
    """
    database = get_database()

    cursor = database["exercises"].find(
        {},
        {
            "embedding": 0,
        },
    ).sort("name", 1)

    exercises = await cursor.to_list(length=100)

    if not exercises:
        return "No exercise catalogue is available."

    exercise_lines: List[str] = []

    for exercise in exercises:
        exercise_lines.append(
            "- "
            f"Name: {exercise.get('name', '')}; "
            f"Description: {exercise.get('description', '')}; "
            f"Muscle groups: {', '.join(exercise.get('muscle_groups', []))}; "
            f"Equipment: {', '.join(exercise.get('equipment', []))}; "
            f"Difficulty: {exercise.get('difficulty', '')}; "
            f"Goals: {', '.join(exercise.get('goal_tags', []))}; "
            f"Limitations: {', '.join(exercise.get('limitations', []))}."
        )

    return "\n".join(exercise_lines)


async def get_recent_training_logs_text(user_id: str) -> str:
    """
    Reads recent training logs to help the AI adapt future workouts.
    """
    database = get_database()

    cursor = database["training_logs"].find(
        {
            "user_id": user_id
        }
    ).sort("training_date", -1).limit(5)

    logs = await cursor.to_list(length=5)

    if not logs:
        return "No recent training logs available."

    log_lines: List[str] = []

    for log in logs:
        log_lines.append(
            "- "
            f"Date: {log.get('training_date')}; "
            f"Completed: {log.get('completed')}; "
            f"Fatigue: {log.get('fatigue_level')}/10; "
            f"Duration: {log.get('duration_minutes')} minutes; "
            f"Pain notes: {log.get('pain_notes')}; "
            f"Notes: {log.get('notes')}."
        )

    return "\n".join(log_lines)


async def generate_ai_workout_plan(
    user_id: str,
) -> AIWorkoutGenerationResponse:
    """
    Generates a personalized workout plan using GPT-4o mini and saves it in MongoDB.
    """
    profile = await get_profile_by_user_id(user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You must create a fitness profile before generating a workout plan",
        )

    exercise_catalog = await get_exercise_catalog_text()

    system_prompt = """
    You are an AI fitness coach inside a student full-stack project.

    Your task is to generate safe, realistic and personalized workout plans.

    Important rules:
    - Return only the JSON object required by the schema.
    - Do not include markdown.
    - Do not include medical diagnosis.
    - Respect the user's limitations.
    - Use the available equipment whenever possible.
    - Prefer exercises from the provided catalogue.
    - The number of training days must match the user's available_days.
    - Each day should contain between 3 and 6 exercises.
    - Keep the plan realistic for the user's level.
    """

    user_prompt = f"""
    Generate a personalized weekly workout plan for this user.

    User fitness profile:
    - Age: {profile["age"]}
    - Weight kg: {profile["weight_kg"]}
    - Height cm: {profile["height_cm"]}
    - Goal: {profile["goal"]}
    - Level: {profile["level"]}
    - Available training days per week: {profile["available_days"]}
    - Equipment: {", ".join(profile.get("equipment", []))}
    - Limitations: {", ".join(profile.get("limitations", []))}

    Exercise catalogue:
    {exercise_catalog}
    """

    client = get_openai_client()

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "workout_plan",
                    "schema": WORKOUT_PLAN_JSON_SCHEMA,
                    "strict": True,
                },
            },
            temperature=0.4,
        )

    except OpenAIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI workout generation error: {str(error)}",
        )

    content = response.choices[0].message.content

    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an empty response",
        )

    generated_data = parse_json_response(content)

    try:
        workout_request = WorkoutPlanCreateRequest(**generated_data)

    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI workout plan did not match the expected structure: {error}",
        )

    saved_workout = await create_workout_plan(
        user_id=user_id,
        workout_data=workout_request,
    )

    return AIWorkoutGenerationResponse(
        message="Workout plan generated and saved successfully",
        workout_plan=saved_workout,
    )


async def adapt_workout_with_ai(
    user_id: str,
    adaptation_data: AIWorkoutAdaptationRequest,
) -> AIWorkoutAdaptationResponse:
    """
    Adapts a workout day based on fatigue, time available, pain notes and recent logs.
    This does not overwrite the saved workout plan. It returns a daily recommendation.
    """
    profile = await get_profile_by_user_id(user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You must create a fitness profile before adapting a workout",
        )

    workout = await get_workout_document_by_id(
        user_id=user_id,
        workout_id=adaptation_data.workout_plan_id,
    )

    recent_logs = await get_recent_training_logs_text(user_id)

    system_prompt = """
    You are an AI fitness coach inside a student full-stack project.

    Your task is to adapt one workout day based on the user's current situation.

    Important rules:
    - Return only the JSON object required by the schema.
    - Do not include markdown.
    - Do not include medical diagnosis.
    - If the user reports pain, reduce risk and suggest safer alternatives.
    - If fatigue is high, reduce volume or intensity.
    - If available time is short, reduce the workout to the most important exercises.
    - Keep the recommendation practical and easy to understand.
    """

    user_prompt = f"""
    Adapt a workout for this user.

    User fitness profile:
    - Age: {profile["age"]}
    - Weight kg: {profile["weight_kg"]}
    - Height cm: {profile["height_cm"]}
    - Goal: {profile["goal"]}
    - Level: {profile["level"]}
    - Available days: {profile["available_days"]}
    - Equipment: {", ".join(profile.get("equipment", []))}
    - Limitations: {", ".join(profile.get("limitations", []))}

    Current workout plan:
    {json.dumps({
        "title": workout.get("title"),
        "goal": workout.get("goal"),
        "days": workout.get("days", []),
    }, ensure_ascii=False)}

    Current situation:
    - Target day: {adaptation_data.target_day or "Not specified"}
    - Fatigue level: {adaptation_data.fatigue_level}/10
    - Available time: {adaptation_data.available_time_minutes} minutes
    - Pain notes: {adaptation_data.pain_notes or "None"}
    - User notes: {adaptation_data.user_notes or "None"}

    Recent training logs:
    {recent_logs}
    """

    client = get_openai_client()

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "workout_adaptation",
                    "schema": WORKOUT_ADAPTATION_JSON_SCHEMA,
                    "strict": True,
                },
            },
            temperature=0.3,
        )

    except OpenAIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI workout adaptation error: {str(error)}",
        )

    content = response.choices[0].message.content

    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an empty response",
        )

    generated_data = parse_json_response(content)

    try:
        return AIWorkoutAdaptationResponse(**generated_data)

    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI workout adaptation did not match the expected structure: {error}",
        )