# Architecture Decision Records

Significant decisions for ProductIntel, in the format described by [ADR 0001](0001-record-architecture-decisions.md). One decision per file. Accepted ADRs are immutable; a later ADR supersedes an earlier one rather than editing it. New decisions use [`template.md`](template.md).

| # | Decision | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-polyglot-service-architecture.md) | Polyglot service architecture (web + agent + Postgres) | Accepted |
| [0003](0003-google-adk-agent-framework.md) | Google ADK as the agent framework | Accepted |
| [0004](0004-python-and-uv.md) | Python 3.12 and uv for the agent service | Accepted |
| [0005](0005-fastapi-api-layer.md) | FastAPI as the API layer | Accepted |
| [0006](0006-litellm-provider-agnostic-models.md) | LiteLLM for provider-agnostic model access | Accepted |
| [0007](0007-postgres-pgvector-datastore.md) | PostgreSQL and pgvector as the single datastore | Accepted |
| [0008](0008-sqlalchemy-alembic-data-layer.md) | SQLAlchemy 2.0 and Alembic for data access | Accepted |
| [0009](0009-reuse-nextjs-frontend.md) | Reuse Next.js for the frontend | Accepted |
| [0010](0010-sse-streaming-transport.md) | Server-Sent Events for streaming agent output | Accepted |
| [0011](0011-monorepo-layout.md) | Monorepo layout | Accepted |
| [0012](0012-docker-compose-packaging.md) | Docker and Compose for packaging and local development | Accepted |
| [0013](0013-observability-otel-langfuse.md) | OpenTelemetry and Langfuse via ADK callbacks | Accepted |
| [0014](0014-defer-auth-jwt-bearer.md) | Defer authentication for v0; JWT bearer when introduced | Accepted |
| [0015](0015-knowledge-first-vertical-slice.md) | Knowledge as the first vertical slice | Accepted |
