# ProductIntel (v2)

## What This Is
An AI-native operations platform rebuilt from the ground up on Google's Agent Development Kit (ADK). The forward-looking line of ProductIntel; the original prototype (`productbrain`, separate repo) remains as the v1 learning project with its own bespoke agent framework (AgentWeave). This rebuild deliberately uses a translatable, industry-standard stack with every decision recorded as an ADR.

## Architecture
Polyglot, service-oriented (ADR 0002). ADK is a Python agent runtime, not a web framework:
- `web/` — Next.js 16 + React 19 + TypeScript + Tailwind v4 chat UI. Proxies chat via `app/api/chat/route.ts` to the agent service; streams SSE back to the browser. Never imports agent code.
- `agent/` — Python 3.12 + ADK + FastAPI. Agents: `app/agent.py` (knowledge_agent + the root `coordinator` with `sub_agents` delegation), `app/work.py` (work_agent: story filing/triage tools). FastAPI surface (`/health`, SSE `/chat`) in `app/main.py` serves the coordinator.
- PostgreSQL + pgvector — single store for relational data and embeddings (ADR 0007). Schema source of truth is Alembic (`agent/alembic/`).

## Key Decisions (docs/adr/ — 18 ADRs, immutable; supersede, never edit)
- ADR 0003: ADK over the home-grown framework. Code-first agents, deliberate reversal of v1's data-first registry rows.
- ADR 0006: ALL model access through LiteLLM. Models are config strings (`MODEL`, `EMBED_MODEL` in `.env`), never hardcoded. This paid off day one: Google retired both original default models; fix was two config lines.
- ADR 0010: REST + SSE for streaming. Note: ADK currently emits the post-tool-loop answer as ONE SSE event; token-level streaming is a planned refinement (ADK run_config streaming mode).
- ADR 0016: the callback seam (`agent/app/seam.py`). ALL model/tool calls route through it: trace persistence (`trace_events` table), ENFORCED per-session token budget (blocks in `before_model`), tool-result truncation cap. New cross-cutting policy belongs here, not in prompts. Langfuse/OTel (ADR 0013) attaches here later.
- ADR 0017: coordinator with LLM-driven delegation (`sub_agents` transfer, not AgentTool). ADK injects `transfer_to_agent`; after a transfer the specialist owns the turn, and follow-up turns resume with it (sticky). New specialists: give them a `description` (routing reads it), wire the seam, add to `sub_agents`.
- ADR 0018: ADK's native OTel spans own the Langfuse trace structure (constructing the Langfuse client registers the global provider that turns them on). The seam does NOT build its own observations; it stamps `session.id`/trace name and emits guardrail events. ADK 2.2 double-emits model spans (`call_llm` + semconv `generate_content`); `generate_content` is filtered at export or tokens double-count.
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
- `make seed` — seed 6 demo untriaged stories (idempotent: skips if stories exist).
- `make web` — Next.js dev server on :3000 (foreground).
- `make logs` / `make down`.
- Non-Docker path: see README "Option B" (local venv via uv, local Postgres works too).
- Quick verify: `curl localhost:8000/health`; chat: `curl -N -X POST localhost:8000/chat -H 'Content-Type: application/json' -d '{"message":"...","session_id":"..."}'`.
- Traces: `psql -h localhost -p 5433 -U productintel -d productintel` (password `productintel`) → `trace_events` table.

## Environment
- `.env` at repo root (gitignored; `.env.example` documents all knobs). Free Google AI Studio key covers the default Gemini Flash models.
- Current models: `gemini/gemini-2.5-flash` chat, `gemini/gemini-embedding-001` embeddings. Lesson learned: model IDs are perishable — if a 404 NOT_FOUND appears, list available models via the API and update `.env`, not code.
- Seam knobs: `SESSION_TOKEN_BUDGET` (default 100k, enforced), `MAX_TOOL_RESULT_CHARS` (default 8k).
- Langfuse (optional): `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` (the SDK's own env name; `LANGFUSE_HOST` aliased). Exporter is a no-op without keys. Mike's project is on the US cloud free tier.
- ADK version verified against: google-adk 2.2.0 (public line). Langfuse SDK pinned `>=4.7.0` (v4 dropped v3's `update_trace`; verify SDK surfaces by introspection, same as ADK).

## Current State (2026-06-09)
- v0 Knowledge slice: SHIPPED and verified live end to end (ingest → agent → pgvector retrieval → cited answers → out-of-KB refusal → web proxy chain).
- Callback seam: SHIPPED and verified (traces, budget block, truncation all tested with real traffic).
- v1 Work slice: SHIPPED and verified live (coordinator routes knowledge questions and backlog requests via `transfer_to_agent`; work_agent filed + triaged stories with rationales persisted; traces show the multi-agent flow per agent).
- Langfuse export (ADR 0013 + 0018): SHIPPED and verified live (one nested trace per turn from ADK's native OTel spans, sessions grouped, tokens counted once; `generate_content` duplicates filtered at export — tool spans render at trace root until ADK finishes its semconv migration).
- Rebuild write-up: drafted at `docs/why-i-rebuilt-on-adk.md`, pending author edit.
- Sessions are in-memory (`InMemorySessionService`) — restart loses conversations; `DatabaseSessionService` is the upgrade path. No auth (ADR 0014). No dedupe on ingest.

## Next
- Token-level SSE streaming via ADK streaming run config.
- Auth (ADR 0014) when multi-user.
- Durable sessions (`DatabaseSessionService`); ingest dedupe.
