# agent/

The ProductIntel agent service: Google ADK agents served over FastAPI (ADR 0002, 0003, 0005).

## Layout

```
app/
  config.py      Settings (env-driven; LiteLLM model strings)
  db.py          SQLAlchemy engine + session
  models.py      Document, DocumentChunk (pgvector embedding column)
  embeddings.py  Embed text via LiteLLM
  retrieval.py   Cosine-similarity search (the agent's tool backing)
  agent.py       The ADK LlmAgent + search_knowledge tool
  main.py        FastAPI app: /health and the SSE /chat endpoint
  ingest.py      Chunk + embed + store a Markdown corpus
alembic/         Migrations (source of truth for the schema, ADR 0008)
```

## Run locally

```bash
# From the repo root, start Postgres (+ optionally the agent) via Compose:
docker compose up -d db

# Then, in agent/:
uv venv && uv pip install -e .
cp ../.env.example ../.env   # set GOOGLE_API_KEY or ANTHROPIC_API_KEY
export $(grep -v '^#' ../.env | xargs)   # or use a dotenv loader
alembic upgrade head
uv run python -m app.ingest ../corpus
uv run uvicorn app.main:app --reload
```

Health check: `curl localhost:8000/health`

## ADK version note

This scaffold targets the stable ADK Python API. It has **not** been executed
end-to-end in the environment where it was generated, and some import paths or
method signatures (notably the `InMemorySessionService` async/sync surface and the
`google.adk.models.lite_llm.LiteLlm` path) may differ across ADK releases. Verify
against your installed version (e.g. ADK 3.x) and adjust if needed. Pin the exact
version in `pyproject.toml` once confirmed.
