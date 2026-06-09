from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (and a local .env).

    Per ADR 0006 the model strings are LiteLLM identifiers (e.g. "gemini/gemini-2.0-flash"
    or "anthropic/claude-..."), so the provider can be swapped without code changes.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://productintel:productintel@localhost:5432/productintel"

    # LiteLLM model identifiers.
    model: str = "gemini/gemini-2.5-flash"
    embed_model: str = "gemini/gemini-embedding-001"
    # Embedding dimension MUST match the embed_model output (we pass `dimensions`
    # explicitly; gemini-embedding-001 defaults to 3072 otherwise).
    # Changing this requires a new migration for the document_chunks.embedding column.
    embed_dim: int = 768

    cors_origins: str = "http://localhost:3000"
    app_name: str = "productintel"


settings = Settings()
