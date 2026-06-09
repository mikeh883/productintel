# ProductIntel

An AI-native operations platform, rebuilt from the ground up on **Google's Agent Development Kit (ADK)**.

This is the production-oriented reimagining of [ProductIntel](https://productintel.io). The original codebase (`productbrain`) was a learning project and MVP that grew a bespoke agent framework (AgentWeave) alongside a full Next.js product. This repo keeps the *spirit* of that work (knowledge as the context engine, AI assistance at every decision point, a unified artifact model) but starts fresh on an industry-standard agent stack, with deliberate, documented architecture decisions.

## Why a rebuild

The original taught the hard parts: agent orchestration, retrieval, the product itself. This version trades the home-grown framework for the tooling enterprises actually run, so the architecture is translatable across companies and the decisions are ones anyone in the field would recognize.

## Architecture

A polyglot, service-oriented system, because ADK is an agent runtime rather than a web framework:

- **`web/`** — Next.js + React + TypeScript + Tailwind frontend
- **`agent/`** — Python ADK agents served over FastAPI
- **PostgreSQL + pgvector** — relational data and embeddings in one store

The interesting engineering lives in the seam between the frontend and the agent service: streaming agent events to the UI, and the ADK callback layer where observability, guardrails, and cost control plug in.

## Stack

| Layer | Choice |
|---|---|
| Agent runtime | Google ADK |
| Language / deps | Python 3.12 + uv |
| API layer | FastAPI |
| Model access | LiteLLM (provider-agnostic: Gemini or Claude) |
| Data layer | SQLAlchemy 2.0 + Alembic |
| Database | PostgreSQL + pgvector |
| Frontend | Next.js + React + TypeScript + Tailwind |
| Transport | REST + Server-Sent Events (streaming) |
| Packaging | Docker + Compose |
| Observability | OpenTelemetry + Langfuse (via ADK callbacks) |

Each choice is recorded as an Architecture Decision Record under [`docs/adr/`](docs/adr/).

## Getting started

Prerequisites: Docker, Node 20+, and a model provider API key (Google or Anthropic).

```bash
cp .env.example .env          # add GOOGLE_API_KEY or ANTHROPIC_API_KEY
make up                       # build + start Postgres and the agent service (runs migrations)
make ingest                   # embed the sample corpus/ into the knowledge base
make web                      # run the Next.js chat UI at http://localhost:3000
```

The agent service listens on `http://localhost:8000` (`/health`, `/chat`). The web app
proxies chat to it and streams the response. See `agent/README.md` for running the
backend without Docker, and a note on ADK version differences.

## Layout

```
web/      Next.js + React + TypeScript chat UI (ADR 0009)
agent/    Python ADK agents over FastAPI, SQLAlchemy + Alembic (ADR 0002-0008)
corpus/   Sample Markdown documents to ingest
docs/adr/ Architecture Decision Records
```

## Status

Early. The first slice is **Knowledge**: retrieval-augmented chat over a document corpus, built as a single ADK agent with a pgvector retrieval tool. Work (story triage) follows, and is where the first multi-agent coordination appears.

## Relationship to `productbrain`

`productbrain` remains as the original learning project and MVP. This repo is the forward-looking line. The two are intentionally separate codebases.
