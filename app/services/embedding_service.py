from typing import List

from fastapi import HTTPException, status
from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings


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


async def create_embedding(text: str) -> List[float]:
    """
    Creates an embedding vector from a text using OpenAI text-embedding-3-small.
    """
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text for embedding cannot be empty",
        )

    client = get_openai_client()

    try:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text,
        )

        return response.data[0].embedding

    except OpenAIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI embedding service error: {str(error)}",
        )