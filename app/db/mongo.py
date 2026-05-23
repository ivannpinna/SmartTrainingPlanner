from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


class MongoConnection:
    client: AsyncIOMotorClient | None = None
    database: AsyncIOMotorDatabase | None = None


mongo_connection = MongoConnection()


async def connect_to_mongo() -> None:
    """
    Creates the MongoDB connection when the FastAPI app starts.
    """
    mongo_connection.client = AsyncIOMotorClient(settings.MONGO_URI)
    mongo_connection.database = mongo_connection.client[settings.MONGO_DB_NAME]

    # Checks that MongoDB is reachable
    await mongo_connection.client.admin.command("ping")

    print("Connected to MongoDB")


async def close_mongo_connection() -> None:
    """
    Closes the MongoDB connection when the FastAPI app stops.
    """
    if mongo_connection.client is not None:
        mongo_connection.client.close()
        mongo_connection.client = None
        mongo_connection.database = None

        print("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Returns the active MongoDB database.
    """
    if mongo_connection.database is None:
        raise RuntimeError("MongoDB database is not connected")

    return mongo_connection.database