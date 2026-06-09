import litellm

from .config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via LiteLLM (ADR 0006)."""
    response = litellm.embedding(model=settings.embed_model, input=texts)
    return [item["embedding"] for item in response.data]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
