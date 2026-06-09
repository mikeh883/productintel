import litellm

from .config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via LiteLLM (ADR 0006).

    `dimensions` pins the output to the schema's vector size — gemini-embedding-001
    defaults to 3072, which would not fit the vector(EMBED_DIM) column.
    """
    response = litellm.embedding(
        model=settings.embed_model, input=texts, dimensions=settings.embed_dim
    )
    return [item["embedding"] for item in response.data]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
