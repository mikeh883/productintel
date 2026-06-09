# ADR 0018: ADK's native OpenTelemetry spans own the Langfuse trace structure

**Status:** Accepted
**Date:** 2026-06-09

## Context

Wiring Langfuse (ADR 0013) surfaced something the docs do not advertise: ADK 2.2
ships its own OpenTelemetry instrumentation (scope `gcp.vertex.agent`). The moment
the Langfuse SDK registers a global tracer provider, ADK exports a fully nested
trace per invocation on its own: invocation, invoke_agent per agent, a model span
per LLM call with token usage, and tool spans. The seam's hand-built observations
(the first implementation) produced a second, flatter trace of the same turn, and
token usage landed in Langfuse analytics twice.

A second duplication exists inside ADK itself: during its migration to the GenAI
semantic conventions it emits each model call as both a legacy `call_llm` span and
a semconv `generate_content` span carrying the same usage.

## Decision

ADK's native spans own the trace structure. The seam stops emitting its own
generations and tool observations for Langfuse and instead contributes only what
the runtime cannot know: it stamps the chat session id and trace name onto the
active span (so traces group into Langfuse sessions) and emits guardrail events
such as token-budget blocks. The duplicate `generate_content` spans are filtered
at export (`should_export_span`); `call_llm` is the one kept because it parents
under `invoke_agent`, preserving the per-agent hierarchy in the waterfall.

The local `trace_events` table is unchanged and remains the always-on record.

## Alternatives considered

- **Seam-built observations own the trace** (the first implementation). Full
  control of naming and payloads, and the purest reading of ADR 0016. Rejected:
  it duplicates what the runtime already exports, the hand-built trace was flatter
  than the native one, and every future agent feature would need matching export
  code. Suppressing the native spans to fix the double-count means maintaining a
  parallel copy of instrumentation ADK gives away.
- **Keep both pipelines.** Two traces per turn and double-counted cost analytics.
- **Filter `call_llm` instead of `generate_content`.** Tested live: the semconv
  spans parent under `call_llm`, so dropping `call_llm` orphans every generation
  and the per-agent grouping collapses.

## Consequences

- One trace per turn, nested by agent, tokens counted once. Tool spans render at
  the trace root because their parent is the filtered `generate_content` span; a
  cosmetic trade-off accepted until ADK completes its semconv migration, at which
  point the filter and this quirk should be revisited.
- The seam's Langfuse code shrinks to a session stamp and guardrail events. The
  exporter rides on industry-standard instrumentation rather than custom code.
- ADK puts prompt and response text in spans by default
  (`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS`), which is what a demo wants; disable it
  if trace content ever becomes sensitive.
