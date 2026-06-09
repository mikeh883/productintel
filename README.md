# ProductIntel

> An AI-native operations platform, reimagined on Google's Agent Development Kit (ADK).

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Status: early](https://img.shields.io/badge/status-early%20%2F%20WIP-orange)
![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB)
![Next.js](https://img.shields.io/badge/Next.js-16-black)

ProductIntel is a workspace where product, knowledge, and support work share one
foundation, and AI assistance shows up at every decision point. This repository is a
ground-up rebuild of an earlier prototype (`productbrain`) on an industry-standard agent
stack: the bespoke agent framework is replaced by Google ADK, and the choices are
deliberately the kind any team would recognize.

It is developed in the open as a portfolio and learning project.

## Status

Early, and intentionally so. Two vertical slices are built: **Knowledge**, a
retrieval-augmented chat over a document corpus, and **Work**, a story backlog
managed by a triage agent behind the project's first multi-agent coordinator.
Tracing and enforced guardrails run through a callback seam on every call. This is
not production software. Authentication and external observability export are
decided but not yet built (see the ADRs). Every architecture decision is recorded
under [`docs/adr/`](docs/adr/) as it is made.

## What it does today

Ask a question in the chat UI. A coordinator agent routes it to the right specialist:

- **Knowledge questions** go to the knowledge agent, which searches the knowledge base
  for the most relevant document chunks, answers using only what it finds, and cites
  the documents it used. If the knowledge base does not contain the answer, it says so
  rather than guessing.
- **Backlog requests** go to the work agent. Paste a raw bug report or feature request
  and it files a story; ask it to triage the backlog and it classifies each story
  (bug, feature, or chore), assigns a priority (P0 to P3), and records its rationale.

The routing itself is model-driven, using ADK's agent transfer
([ADR 0017](docs/adr/0017-coordinator-llm-delegation.md)), and every model and tool
call from every agent is traced and budget-checked by the callback seam
([ADR 0016](docs/adr/0016-callback-seam-guardrails-tracing.md)).

## Architecture

ADK is a Python agent runtime, not a web framework, so ProductIntel is a small polyglot
system rather than a monolith:

```
   ┌───────────────┐     HTTP + SSE      ┌────────────────────────┐
   │   web/        │ ──────────────────▶ │   agent/               │
   │   Next.js UI  │ ◀────────────────── │   Google ADK + FastAPI │
   └───────────────┘   streamed tokens   └───────────┬────────────┘
                                                      │ SQLAlchemy
                                                      ▼
                                          ┌────────────────────────┐
                                          │  PostgreSQL + pgvector  │
                                          └────────────────────────┘
```

- **`web/`** renders the UI and proxies chat to the agent service; it never imports
  agent code.
- **`agent/`** hosts the ADK agent and its retrieval tool behind a small FastAPI surface
  (`/health`, `/chat`).
- **PostgreSQL + pgvector** stores documents, chunks, and embeddings in one place.

The seam between the frontend and the agent service (streaming, and the ADK callback
layer where observability and guardrails plug in) is where most of the engineering
interest lives.

## Stack

| Layer | Choice | Decision |
|---|---|---|
| Agent runtime | Google ADK | [ADR 0003](docs/adr/0003-google-adk-agent-framework.md) |
| Language / deps | Python 3.12 + uv | [ADR 0004](docs/adr/0004-python-and-uv.md) |
| API layer | FastAPI | [ADR 0005](docs/adr/0005-fastapi-api-layer.md) |
| Model access | LiteLLM (Gemini or Claude) | [ADR 0006](docs/adr/0006-litellm-provider-agnostic-models.md) |
| Data layer | SQLAlchemy 2.0 + Alembic | [ADR 0008](docs/adr/0008-sqlalchemy-alembic-data-layer.md) |
| Database | PostgreSQL + pgvector | [ADR 0007](docs/adr/0007-postgres-pgvector-datastore.md) |
| Frontend | Next.js + React + TypeScript + Tailwind | [ADR 0009](docs/adr/0009-reuse-nextjs-frontend.md) |
| Transport | REST + Server-Sent Events | [ADR 0010](docs/adr/0010-sse-streaming-transport.md) |
| Packaging | Docker + Compose | [ADR 0012](docs/adr/0012-docker-compose-packaging.md) |

## Getting started

Both options need a model provider API key in `.env`. **The default setup runs for
free:** the scaffold uses Google's Gemini Flash models, which have a permanent free
tier on [Google AI Studio](https://aistudio.google.com/apikey), generous enough for
local development and the sample corpus, with no billing setup. Create a free key, then:

```bash
cp .env.example .env    # then set GOOGLE_API_KEY=...
```

> **Want Claude or another provider instead?** Change `MODEL`/`EMBED_MODEL` in `.env` to
> LiteLLM identifiers (e.g. `anthropic/claude-haiku-4-5`) and set that provider's key.
> Two things to know: chat subscriptions (Claude Pro/Max, Gemini Advanced) do **not**
> grant API access: programmatic usage is billed per token, separately from any
> subscription. And Anthropic has no embeddings API, so an all-Claude setup still needs a
> separate embeddings provider; the all-Gemini default avoids that.

### Option A: Docker (recommended, fully reproducible)

```bash
make up        # build + start Postgres and the agent service (applies migrations)
make ingest    # embed the sample corpus/ into the knowledge base
make seed      # seed a demo backlog of untriaged stories for the work agent
make web       # run the Next.js chat UI at http://localhost:3000
```

### Option B: local Postgres, no Docker

Requires a local PostgreSQL with the `pgvector` extension available, plus `uv` and Node.

```bash
createdb productintel

cd agent
uv venv --python 3.12 && uv pip install -e .
export DATABASE_URL=postgresql+psycopg://localhost:5432/productintel
uv run alembic upgrade head            # creates the vector extension + tables
uv run python -m app.ingest ../corpus  # needs a model key for embeddings
uv run uvicorn app.main:app --reload   # agent service on :8000

cd ../web && npm install && npm run dev # UI on :3000
```

Then open http://localhost:3000.

## Project layout

```
web/        Next.js + React + TypeScript chat UI
agent/      Python ADK agents over FastAPI; SQLAlchemy + Alembic; LiteLLM
corpus/     Sample Markdown documents to ingest
docs/adr/   Architecture Decision Records (the reasoning behind every choice)
```

## Architecture decisions

The reasoning behind every stack and architecture choice lives in
[`docs/adr/`](docs/adr/) as numbered, immutable records. Good entry points:
[ADR 0002](docs/adr/0002-polyglot-service-architecture.md) (why a polyglot service
split) and [ADR 0003](docs/adr/0003-google-adk-agent-framework.md) (why ADK over the
original framework).

For the narrative version, read
[**Why I rebuilt ProductIntel on Google's ADK**](docs/why-i-rebuilt-on-adk.md):
the data-first vs code-first fork, what the original framework taught that this
rebuild keeps, and why enforced guardrails in the callback layer were the upgrade
that mattered most.

## Roadmap

- **Token-level streaming**: ADK currently emits the final answer as one SSE event;
  true incremental streaming uses ADK's streaming run config.
- **Observability export**: OpenTelemetry + Langfuse attached to the existing callback
  seam ([ADR 0013](docs/adr/0013-observability-otel-langfuse.md)).
- **Durable sessions**: conversations currently live in memory; a database-backed
  session service survives restarts.
- **Authentication**: JWT bearer when the product grows past a single user
  ([ADR 0014](docs/adr/0014-defer-auth-jwt-bearer.md)).

## Relationship to `productbrain`

`productbrain` is the original learning project and MVP, a full Next.js application with
a home-grown agent framework. ProductIntel is the forward-looking line on a standard
stack. The two are intentionally separate codebases.

## License

MIT. See [LICENSE](LICENSE).
