import asyncio
from datetime import datetime, timezone

from app.db.mongo import close_mongo_connection, connect_to_mongo, get_database


INITIAL_EXERCISES = [
    {
        "name": "Squat",
        "description": "A compound lower-body exercise that mainly targets the quadriceps, glutes and core. It is useful for strength and muscle gain.",
        "muscle_groups": ["quadriceps", "glutes", "core"],
        "equipment": ["barbell"],
        "difficulty": "intermediate",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["not ideal for knee pain"],
    },
    {
        "name": "Glute Bridge",
        "description": "A lower-body exercise focused on glutes and hamstrings. It is low impact and can be suitable for users with knee discomfort.",
        "muscle_groups": ["glutes", "hamstrings"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "goal_tags": ["strength", "muscle gain", "rehabilitation"],
        "limitations": ["suitable for knee pain"],
    },
    {
        "name": "Hip Thrust",
        "description": "A glute-focused strength exercise that targets the posterior chain with less knee stress than squats or lunges.",
        "muscle_groups": ["glutes", "hamstrings"],
        "equipment": ["barbell", "bench"],
        "difficulty": "intermediate",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["suitable for knee pain"],
    },
    {
        "name": "Leg Press",
        "description": "A machine-based lower-body exercise that targets quadriceps and glutes. The range of motion can be controlled to reduce discomfort.",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        "equipment": ["machine"],
        "difficulty": "beginner",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["use controlled range for knee pain"],
    },
    {
        "name": "Lunge",
        "description": "A unilateral lower-body exercise that works quadriceps, glutes and balance. It can be challenging for users with knee pain.",
        "muscle_groups": ["quadriceps", "glutes", "core"],
        "equipment": ["bodyweight", "dumbbells"],
        "difficulty": "intermediate",
        "goal_tags": ["strength", "balance", "muscle gain"],
        "limitations": ["not ideal for knee pain"],
    },
    {
        "name": "Bench Press",
        "description": "A compound upper-body exercise that mainly targets chest, shoulders and triceps. It is commonly used for strength and muscle gain.",
        "muscle_groups": ["chest", "shoulders", "triceps"],
        "equipment": ["barbell", "bench"],
        "difficulty": "intermediate",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["not ideal for shoulder pain"],
    },
    {
        "name": "Push-up",
        "description": "A bodyweight upper-body exercise that targets chest, shoulders, triceps and core. It is useful for general fitness and endurance.",
        "muscle_groups": ["chest", "shoulders", "triceps", "core"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "goal_tags": ["strength", "endurance", "general fitness"],
        "limitations": ["may affect shoulder pain or wrist pain"],
    },
    {
        "name": "Incline Dumbbell Press",
        "description": "An upper-body exercise that targets the upper chest, shoulders and triceps using dumbbells on an incline bench.",
        "muscle_groups": ["chest", "shoulders", "triceps"],
        "equipment": ["dumbbells", "bench"],
        "difficulty": "intermediate",
        "goal_tags": ["muscle gain", "strength"],
        "limitations": ["use light weight for shoulder pain"],
    },
    {
        "name": "Seated Chest Press",
        "description": "A machine-based chest exercise that targets chest, shoulders and triceps with more stability than free weights.",
        "muscle_groups": ["chest", "shoulders", "triceps"],
        "equipment": ["machine"],
        "difficulty": "beginner",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["controlled option for beginners"],
    },
    {
        "name": "Pull-up",
        "description": "A bodyweight upper-body pulling exercise that targets the back, biceps and core. It is effective for strength development.",
        "muscle_groups": ["back", "biceps", "core"],
        "equipment": ["pull-up bar"],
        "difficulty": "advanced",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["difficult for beginners"],
    },
    {
        "name": "Lat Pulldown",
        "description": "A machine-based pulling exercise that targets the lats, upper back and biceps. It is a good alternative to pull-ups.",
        "muscle_groups": ["back", "biceps"],
        "equipment": ["machine"],
        "difficulty": "beginner",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["suitable alternative to pull-ups"],
    },
    {
        "name": "Barbell Row",
        "description": "A compound pulling exercise for the back, biceps and posterior chain. It requires good posture and core control.",
        "muscle_groups": ["back", "biceps", "hamstrings", "core"],
        "equipment": ["barbell"],
        "difficulty": "intermediate",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["not ideal for lower back pain"],
    },
    {
        "name": "Seated Cable Row",
        "description": "A machine or cable-based back exercise that targets the lats, mid-back and biceps with stable positioning.",
        "muscle_groups": ["back", "biceps"],
        "equipment": ["cable machine"],
        "difficulty": "beginner",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["controlled option for lower back discomfort"],
    },
    {
        "name": "Deadlift",
        "description": "A heavy compound exercise that targets the posterior chain, including hamstrings, glutes, back and core.",
        "muscle_groups": ["hamstrings", "glutes", "back", "core"],
        "equipment": ["barbell"],
        "difficulty": "advanced",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["not ideal for lower back pain"],
    },
    {
        "name": "Romanian Deadlift",
        "description": "A hip-hinge exercise that targets hamstrings, glutes and lower back with controlled movement.",
        "muscle_groups": ["hamstrings", "glutes", "back"],
        "equipment": ["barbell", "dumbbells"],
        "difficulty": "intermediate",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["use caution with lower back pain"],
    },
    {
        "name": "Leg Curl",
        "description": "A machine-based isolation exercise that targets the hamstrings with minimal stress on the lower back.",
        "muscle_groups": ["hamstrings"],
        "equipment": ["machine"],
        "difficulty": "beginner",
        "goal_tags": ["muscle gain", "strength"],
        "limitations": ["controlled option for lower body training"],
    },
    {
        "name": "Shoulder Press",
        "description": "An overhead pressing exercise that targets shoulders and triceps. It can be performed with dumbbells or a barbell.",
        "muscle_groups": ["shoulders", "triceps"],
        "equipment": ["dumbbells", "barbell"],
        "difficulty": "intermediate",
        "goal_tags": ["strength", "muscle gain"],
        "limitations": ["not ideal for shoulder pain"],
    },
    {
        "name": "Lateral Raise",
        "description": "An isolation exercise that targets the side deltoids and helps improve shoulder width and stability.",
        "muscle_groups": ["shoulders"],
        "equipment": ["dumbbells"],
        "difficulty": "beginner",
        "goal_tags": ["muscle gain", "general fitness"],
        "limitations": ["use light weight for shoulder pain"],
    },
    {
        "name": "Face Pull",
        "description": "A cable exercise that targets rear delts, upper back and shoulder stabilizers. It is useful for posture and shoulder health.",
        "muscle_groups": ["shoulders", "upper back"],
        "equipment": ["cable machine"],
        "difficulty": "beginner",
        "goal_tags": ["posture", "rehabilitation", "general fitness"],
        "limitations": ["suitable for shoulder stability"],
    },
    {
        "name": "Plank",
        "description": "An isometric core exercise that improves trunk stability, posture and endurance.",
        "muscle_groups": ["core"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "goal_tags": ["core strength", "endurance", "general fitness"],
        "limitations": ["may be difficult with shoulder pain"],
    },
    {
        "name": "Dead Bug",
        "description": "A low-impact core stability exercise performed lying down. It is useful for beginners and users with lower back concerns.",
        "muscle_groups": ["core"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "goal_tags": ["core strength", "rehabilitation"],
        "limitations": ["suitable for lower back pain"],
    },
    {
        "name": "Mountain Climbers",
        "description": "A dynamic bodyweight exercise that trains core, shoulders and cardiovascular endurance.",
        "muscle_groups": ["core", "shoulders", "legs"],
        "equipment": ["bodyweight"],
        "difficulty": "intermediate",
        "goal_tags": ["fat loss", "endurance", "general fitness"],
        "limitations": ["not ideal for wrist pain or shoulder pain"],
    },
    {
        "name": "Cycling",
        "description": "A low-impact cardiovascular exercise that improves endurance and can be easier on the joints than running.",
        "muscle_groups": ["legs", "cardio"],
        "equipment": ["bike"],
        "difficulty": "beginner",
        "goal_tags": ["fat loss", "endurance", "general fitness"],
        "limitations": ["low impact option"],
    },
    {
        "name": "Treadmill Running",
        "description": "A cardiovascular exercise focused on endurance and fat loss. It can be high impact for knees and ankles.",
        "muscle_groups": ["legs", "cardio"],
        "equipment": ["treadmill"],
        "difficulty": "intermediate",
        "goal_tags": ["fat loss", "endurance"],
        "limitations": ["not ideal for knee pain"],
    },
    {
        "name": "Elliptical Trainer",
        "description": "A low-impact cardio machine that trains endurance while reducing stress on knees compared with running.",
        "muscle_groups": ["legs", "cardio"],
        "equipment": ["machine"],
        "difficulty": "beginner",
        "goal_tags": ["fat loss", "endurance", "general fitness"],
        "limitations": ["suitable for knee pain"],
    },
]


async def seed_exercises() -> None:
    """
    Inserts or updates the initial exercise catalogue.

    Existing exercises are updated by name.
    Embeddings are not overwritten if they already exist.
    """
    database = get_database()
    now = datetime.now(timezone.utc)

    inserted_count = 0
    updated_count = 0

    for exercise in INITIAL_EXERCISES:
        existing_exercise = await database["exercises"].find_one(
            {"name": {"$regex": f"^{exercise['name']}$", "$options": "i"}}
        )

        exercise_data = {
            **exercise,
            "updated_at": now,
        }

        if existing_exercise is None:
            exercise_data["embedding"] = None
            exercise_data["created_at"] = now

            await database["exercises"].insert_one(exercise_data)
            inserted_count += 1

        else:
            await database["exercises"].update_one(
                {"_id": existing_exercise["_id"]},
                {
                    "$set": exercise_data
                },
            )
            updated_count += 1

    print("Exercise seed completed")
    print(f"Inserted exercises: {inserted_count}")
    print(f"Updated exercises: {updated_count}")


async def main() -> None:
    await connect_to_mongo()

    try:
        await seed_exercises()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())