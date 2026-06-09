from pydantic import AliasChoices, Field
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

    # Callback seam (ADR 0016). The budget is ENFORCED: once a session's
    # cumulative LLM tokens cross it, further model calls are short-circuited.
    session_token_budget: int = 100_000
    # Tool results larger than this are truncated before reaching the model —
    # the descendant of AgentWeave's pointer/lazy-load cost pattern.
    max_tool_result_chars: int = 8_000

    # Langfuse export (ADR 0013). Off unless both keys are set; when on, ADK's
    # native OpenTelemetry spans flow to the Langfuse project, one trace per
    # agent invocation, grouped into one Langfuse session per chat session.
    # LANGFUSE_BASE_URL is the SDK's own variable name; LANGFUSE_HOST also works.
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = Field(
        "https://us.cloud.langfuse.com",
        validation_alias=AliasChoices("LANGFUSE_BASE_URL", "LANGFUSE_HOST"),
    )


settings = Settings()
