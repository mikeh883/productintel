# ADR 0016: Callback seam for enforced guardrails and tracing

**Status:** Accepted
**Date:** 2026-06-09

## Context

The original ProductIntel's agent framework expressed guardrails as Markdown injected
into prompts: advisory, not enforced. It also logged every LLM call's tokens, a
discipline worth carrying forward. ADK provides callbacks (`before_model`,
`after_model`, `before_tool`, `after_tool`) that run in code around every model and
tool call and can short-circuit them.

## Decision

All agents route their model and tool calls through a single callback seam
(`agent/app/seam.py`). The seam does three things:

1. **Tracing.** Every model call (tokens, latency, finish reason) and tool call
   (latency, result size) is persisted to a `trace_events` table.
2. **Enforced budget.** A per-session token budget is accounted in session state and
   enforced in `before_model`: once exhausted, further model calls are short-circuited
   with an explanatory response rather than reaching the provider.
3. **Tool-result cap.** `after_tool` truncates oversized tool results before they reach
   the model — the descendant of the original framework's summaries-plus-pointers
   cost pattern.

OpenTelemetry/Langfuse export (ADR 0013) will attach to this same seam later; the DB
table is the v0 trace sink.

## Alternatives considered

- **Prompt-text guardrails only.** What the original did; a model can ignore them, and
  a budget stated in prose cannot stop a call.
- **Enforcement in the FastAPI layer.** Could cap requests, but has no visibility into
  per-call token usage or the tool loop inside an ADK invocation; the callback layer is
  the only place with both the data and the power to block.
- **Full Langfuse wiring now.** Deferred (ADR 0013) to keep v0 small; the seam is
  designed so the exporter is an additive handler, not a rework.

## Consequences

- Guardrails are now code that executes, testable and configurable
  (`SESSION_TOKEN_BUDGET`, `MAX_TOOL_RESULT_CHARS`).
- Every call is auditable in SQL; cost questions become queries.
- The seam adds a small latency overhead per call (one threaded DB write), accepted
  at this scale.
