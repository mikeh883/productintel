# ProductIntel (v2)

## What This Is
An AI-native operations platform rebuilt from the ground up on Google's Agent Development Kit (ADK). The forward-looking line of ProductIntel; the original prototype (`productbrain`, separate repo) remains as the v1 learning project with its own bespoke agent framework (AgentWeave). This rebuild deliberately uses a translatable, industry-standard stack with every decision recorded as an ADR.

## Architecture
Polyglot, service-oriented (ADR 0002). ADK is a Python agent runtime, not a web framework:
- `web/` — Next.js 16 + React 19 + TypeScript + Tailwind v4 chat UI. Proxies chat via `app/api/chat/route.ts` to the agent service; streams SSE back to the browser. Never imports agent code.
- `agent/` — Python 3.12 + ADK + FastAPI. The ADK `LlmAgent` lives in `app/agent.py`; FastAPI surface (`/health`, SSE `/chat`) in `app/main.py`.
- PostgreSQL + pgvector — single store for relational data and embeddings (ADR 0007). Schema source of truth is Alembic (`agent/alembic/`).

## Key Decisions (docs/adr/ — 16 ADRs, immutable; supersede, never edit)
- ADR 0003: ADK over the home-grown framework. Code-first agents, deliberate reversal of v1's data-first registry rows.
- ADR 0006: ALL model access through LiteLLM. Models are config strings (`MODEL`, `EMBED_MODEL` in `.env`), never hardcoded. This paid off day one: Google retired both original default models; fix was two config lines.
- ADR 0010: REST + SSE for streaming. Note: ADK currently emits the post-tool-loop answer as ONE SSE event; token-level streaming is a planned refinement (ADK run_config streaming mode).
- ADR 0016: the callback seam (`agent/app/seam.py`). ALL model/tool calls route through it: trace persistence (`trace_events` table), ENFORCED per-session token budget (blocks in `before_model`), tool-result truncation cap. New cross-cutting policy belongs here, not in prompts. Langfuse/OTel (ADR 0013) attaches here later.
- Narrative version of all decisions: `docs/why-i-rebuilt-on-adk.md`.

## Conventions
- Python: SQLAlchemy 2.0 typed mappings, pydantic-settings config (`app/config.py`), migrations via Alembic (numbered `000N_*.py`). Embedding dimension is pinned (`EMBED_DIM=768`, passed explicitly as `dimensions=` — gemini-embedding-001 defaults to 3072).
- Agents: tools are plain functions with docstrings (ADK builds schemas from them). Wire all agents through the seam callbacks. Verify ADK API surfaces by introspecting the installed version before writing against them; pin versions once confirmed.
- Significant decisions get a new ADR (Nygard format, `docs/adr/template.md`); update the index table in `docs/adr/README.md`.
- Public-facing prose (README, docs/): no em-dashes; use commas, colons, or periods.
- Commit each capability separately; small focused commits in imperative mood.

## Commands
- `make up` — build + start Postgres (pgvector, host port 5433) and the agent service via Docker Compose; applies migrations on boot.
- `make ingest` — chunk + embed + store `corpus/` (re-running duplicates; no dedupe yet).
- `make web` — Next.js dev server on :3000 (foreground).
- `make logs` / `make down`.
- Non-Docker path: see README "Option B" (local venv via uv, local Postgres works too).
- Quick verify: `curl localhost:8000/health`; chat: `curl -N -X POST localhost:8000/chat -H 'Content-Type: application/json' -d '{"message":"...","session_id":"..."}'`.
- Traces: `psql -h localhost -p 5433 -U productintel -d productintel` (password `productintel`) → `trace_events` table.

## Environment
- `.env` at repo root (gitignored; `.env.example` documents all knobs). Free Google AI Studio key covers the default Gemini Flash models.
- Current models: `gemini/gemini-2.5-flash` chat, `gemini/gemini-embedding-001` embeddings. Lesson learned: model IDs are perishable — if a 404 NOT_FOUND appears, list available models via the API and update `.env`, not code.
- Seam knobs: `SESSION_TOKEN_BUDGET` (default 100k, enforced), `MAX_TOOL_RESULT_CHARS` (default 8k).
- ADK version verified against: google-adk 2.2.0 (public line).

## Current State (2026-06-09)
- v0 Knowledge slice: SHIPPED and verified live end to end (ingest → agent → pgvector retrieval → cited answers → out-of-KB refusal → web proxy chain).
- Callback seam: SHIPPED and verified (traces, budget block, truncation all tested with real traffic).
- Rebuild write-up: drafted at `docs/why-i-rebuilt-on-adk.md`, pending author edit.
- Sessions are in-memory (`InMemorySessionService`) — restart loses conversations; `DatabaseSessionService` is the upgrade path. No auth (ADR 0014). No dedupe on ingest.

## Next
- v1 Work slice: a story-triage agent and the first multi-agent coordination (a coordinator routing between knowledge Q&A and work actions — ADK delegation / `sub_agents`, new primitives for this codebase).
- Token-level SSE streaming via ADK streaming run config.
- Langfuse/OTel exporter on the seam (ADR 0013); auth (ADR 0014) when multi-user.
